"""MFE v2 lossy bidirectional physical truth model.

The module implements the common scenario-recouse MILP registered in
the frozen v2/v3 truth-model semantics summarized in the final research
reports. It keeps
solver construction separate from ``replay_v2`` so replay can reconstruct
all physics and cost without reading solver internals.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Mapping, Sequence, Tuple

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

from .mfe_harness import ThermalUnit, load_frozen_deterministic_case


TOLERANCE = 1e-6


@dataclass(frozen=True)
class PenaltyTable:
    load_shedding_per_mwh: float = 10_000.0
    reserve_shortfall_per_mwh: float = 5_000.0
    imbalance_per_mwh: float = 1_000.0
    emergency_spill_per_mwh: float = 1_000.0
    pv_curtailment_per_mwh: float = 10.0
    battery_throughput_per_mwh: float = 2.0
    thermal_reserve_per_mw: float = 5.0
    hybrid_reserve_per_mw: float = 0.0


PENALTIES = PenaltyTable()


@dataclass(frozen=True)
class SolverConfig:
    mip_rel_gap: float = 1e-4
    time_limit_seconds: float = 900.0
    presolve: bool = True
    replay_tolerance: float = TOLERANCE
    relax_base_modes: bool = False
    relax_up_activation_modes: bool = False
    relax_down_activation_modes: bool = False
    integer_base_mode_hours: Tuple[int, ...] = field(default_factory=tuple)
    integer_up_activation_hours: Tuple[int, ...] = field(default_factory=tuple)
    integer_down_activation_hours: Tuple[int, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class V2BatterySpec:
    energy_capacity_mwh: float
    initial_energy_mwh: float
    charge_max_mw: float = 50.0
    discharge_max_mw: float = 50.0
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.95
    interval_hours: float = 1.0
    reserve_duration_hours: float = 0.5
    terminal_fraction: float = 0.25

    @property
    def terminal_energy_mwh(self) -> float:
        return self.terminal_fraction * self.energy_capacity_mwh


@dataclass(frozen=True)
class V2System:
    load_mw: Tuple[float, ...]
    forecast_pv_mw: Tuple[float, ...]
    thermal_units: Tuple[ThermalUnit, ...]
    battery: V2BatterySpec
    reserve_fraction: float
    penalties: PenaltyTable = PENALTIES

    @property
    def horizon(self) -> int:
        return len(self.load_mw)

    @property
    def reserve_requirement_mw(self) -> Tuple[float, ...]:
        return tuple(self.reserve_fraction * value for value in self.load_mw)


@dataclass(frozen=True)
class Stage1Decision:
    thermal_dispatch_mw: Tuple[Tuple[float, ...], ...]
    hybrid_injection_mw: Tuple[float, ...]
    thermal_up_reserve_mw: Tuple[Tuple[float, ...], ...]
    thermal_down_reserve_mw: Tuple[Tuple[float, ...], ...]
    hybrid_up_reserve_mw: Tuple[float, ...]
    hybrid_down_reserve_mw: Tuple[float, ...]
    day_ahead_load_shedding_mw: Tuple[float, ...] = field(default_factory=tuple)
    day_ahead_spill_mw: Tuple[float, ...] = field(default_factory=tuple)
    declared_soc_mwh: Tuple[float, ...] = field(default_factory=tuple)
    declared_charge_mw: Tuple[float, ...] = field(default_factory=tuple)
    declared_discharge_mw: Tuple[float, ...] = field(default_factory=tuple)
    declared_pv_curtailment_mw: Tuple[float, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ScenarioDecision:
    thermal_segment_mw: Tuple[Tuple[Tuple[float, ...], ...], ...]
    charge_mw: Tuple[float, ...]
    discharge_mw: Tuple[float, ...]
    mode_discharge: Tuple[float, ...]
    soc_mwh: Tuple[float, ...]
    pv_curtailment_mw: Tuple[float, ...]
    imbalance_positive_mw: Tuple[float, ...]
    imbalance_negative_mw: Tuple[float, ...]
    reserve_shortfall_up_mw: Tuple[float, ...]
    reserve_shortfall_down_mw: Tuple[float, ...]
    load_shedding_mw: Tuple[float, ...]
    emergency_spill_mw: Tuple[float, ...]
    up_pv_release_mw: Tuple[float, ...]
    up_charge_reduction_mw: Tuple[float, ...]
    up_discharge_increase_mw: Tuple[float, ...]
    down_pv_curtailment_mw: Tuple[float, ...]
    down_charge_increase_mw: Tuple[float, ...]
    down_discharge_reduction_mw: Tuple[float, ...]
    up_mode_discharge: Tuple[float, ...]
    down_mode_discharge: Tuple[float, ...]
    serialized_primal_cost: float

    def thermal_dispatch(self, system: V2System) -> Tuple[Tuple[float, ...], ...]:
        rows = []
        for unit, unit_segments in zip(system.thermal_units, self.thermal_segment_mw):
            rows.append(
                tuple(
                    unit.power_min_mw
                    + sum(segment[t] for segment in unit_segments)
                    for t in range(system.horizon)
                )
            )
        return tuple(rows)


@dataclass(frozen=True)
class SolveDiagnostics:
    status: int
    termination: str
    success: bool
    solver_unresolved: bool
    incumbent_objective: float | None
    best_bound: float | None
    relative_gap: float | None
    node_count: int | None
    variable_count: int
    constraint_count: int
    binary_count: int
    solve_seconds: float


@dataclass(frozen=True)
class Stage2SolveResult:
    decision: ScenarioDecision | None
    diagnostics: SolveDiagnostics


@dataclass(frozen=True)
class ExtensiveFormResult:
    stage1: Stage1Decision | None
    scenarios: Tuple[ScenarioDecision, ...]
    objective: float | None
    diagnostics: SolveDiagnostics


@dataclass(frozen=True)
class MultiStratumResult:
    stage1_by_stratum: Tuple[Stage1Decision, ...]
    scenarios_by_stratum: Tuple[Tuple[ScenarioDecision, ...], ...]
    objective: float | None
    diagnostics: SolveDiagnostics


def load_v2_system(
    repository_root: Path,
    *,
    duration_hours: int,
    initial_soc_fraction: float,
    reserve_fraction: float,
) -> V2System:
    """Load the frozen four-unit day with the v2 uniform load scale."""

    if duration_hours not in {1, 2, 4}:
        raise ValueError("duration_hours must be 1, 2, or 4")
    if initial_soc_fraction not in {0.25, 0.5, 0.75}:
        raise ValueError("initial_soc_fraction must be 0.25, 0.5, or 0.75")
    if reserve_fraction not in {0.05, 0.20}:
        raise ValueError("reserve_fraction must be 0.05 or 0.20")

    v1 = load_frozen_deterministic_case(repository_root)
    scale_ratio = 0.12973491536034124 / 0.15
    load = tuple(scale_ratio * value for value in v1.load_mw)
    capacity = 50.0 * duration_hours
    return V2System(
        load_mw=load,
        forecast_pv_mw=v1.must_take_pv_mw,
        thermal_units=v1.thermal_units,
        battery=V2BatterySpec(
            energy_capacity_mwh=capacity,
            initial_energy_mwh=initial_soc_fraction * capacity,
        ),
        reserve_fraction=reserve_fraction,
    )


def validate_stage1(system: V2System, decision: Stage1Decision) -> None:
    """Validate dimensions and registered day-ahead physical constraints."""

    t_count = system.horizon
    g_count = len(system.thermal_units)
    vectors = (
        decision.hybrid_injection_mw,
        decision.hybrid_up_reserve_mw,
        decision.hybrid_down_reserve_mw,
    )
    if any(len(vector) != t_count for vector in vectors):
        raise ValueError("stage-1 hybrid vector has the wrong horizon")
    matrices = (
        decision.thermal_dispatch_mw,
        decision.thermal_up_reserve_mw,
        decision.thermal_down_reserve_mw,
    )
    if any(len(matrix) != g_count for matrix in matrices):
        raise ValueError("stage-1 thermal matrix has the wrong unit count")
    if any(len(row) != t_count for matrix in matrices for row in matrix):
        raise ValueError("stage-1 thermal row has the wrong horizon")

    da_shed = _stage1_optional_vector(
        decision.day_ahead_load_shedding_mw, t_count
    )
    da_spill = _stage1_optional_vector(decision.day_ahead_spill_mw, t_count)
    tol = TOLERANCE
    requirement = system.reserve_requirement_mw
    for t in range(t_count):
        balance = sum(row[t] for row in decision.thermal_dispatch_mw)
        balance += decision.hybrid_injection_mw[t]
        balance += da_shed[t] - da_spill[t]
        if abs(balance - system.load_mw[t]) > tol:
            raise ValueError(f"stage-1 balance fails at hour {t + 1}")
        if da_shed[t] < -tol or da_spill[t] < -tol:
            raise ValueError("negative stage-1 economic slack")
        up = sum(row[t] for row in decision.thermal_up_reserve_mw)
        up += decision.hybrid_up_reserve_mw[t]
        down = sum(row[t] for row in decision.thermal_down_reserve_mw)
        down += decision.hybrid_down_reserve_mw[t]
        if up + tol < requirement[t] or down + tol < requirement[t]:
            raise ValueError(f"stage-1 reserve requirement fails at hour {t + 1}")
        if decision.hybrid_up_reserve_mw[t] < -tol:
            raise ValueError("negative hybrid upward reserve")
        if decision.hybrid_down_reserve_mw[t] < -tol:
            raise ValueError("negative hybrid downward reserve")
        for g, unit in enumerate(system.thermal_units):
            p = decision.thermal_dispatch_mw[g][t]
            rup = decision.thermal_up_reserve_mw[g][t]
            rdn = decision.thermal_down_reserve_mw[g][t]
            if rup < -tol or rdn < -tol:
                raise ValueError("negative thermal reserve")
            if p + rup > unit.power_max_mw + tol:
                raise ValueError("thermal upward headroom fails")
            if p - rdn < unit.power_min_mw - tol:
                raise ValueError("thermal downward footroom fails")
            ramp_call = unit.ramp_mw_per_hour * system.battery.reserve_duration_hours
            if rup > ramp_call + tol or rdn > ramp_call + tol:
                raise ValueError("thermal reserve ramp deliverability fails")
            if t and abs(p - decision.thermal_dispatch_mw[g][t - 1]) > (
                unit.ramp_mw_per_hour + tol
            ):
                raise ValueError("stage-1 thermal ramp fails")
    if decision.declared_soc_mwh:
        validate_assoc_declaration(system, decision)


def validate_assoc_declaration(
    system: V2System,
    decision: Stage1Decision,
) -> None:
    """Independently validate the frozen C_ASSOC market-proxy declaration."""

    h = system.horizon
    b = system.battery
    tol = TOLERANCE
    if len(decision.declared_soc_mwh) != h + 1:
        raise ValueError("C_ASSOC SOC declaration has the wrong horizon")
    for vector in (
        decision.declared_charge_mw,
        decision.declared_discharge_mw,
        decision.declared_pv_curtailment_mw,
    ):
        if len(vector) != h:
            raise ValueError("C_ASSOC power declaration has the wrong horizon")
    if abs(decision.declared_soc_mwh[0] - b.initial_energy_mwh) > tol:
        raise ValueError("C_ASSOC initial SOC mismatch")
    if decision.declared_soc_mwh[-1] < b.terminal_energy_mwh - tol:
        raise ValueError("C_ASSOC terminal SOC fails")

    for t in range(h):
        energy = decision.declared_soc_mwh[t]
        next_energy = decision.declared_soc_mwh[t + 1]
        charge = decision.declared_charge_mw[t]
        discharge = decision.declared_discharge_mw[t]
        curtail = decision.declared_pv_curtailment_mw[t]
        up = decision.hybrid_up_reserve_mw[t]
        down = decision.hybrid_down_reserve_mw[t]
        if energy < -tol or energy > b.energy_capacity_mwh + tol:
            raise ValueError(f"C_ASSOC SOC bound fails at hour {t + 1}")
        if charge < -tol or charge > b.charge_max_mw + tol:
            raise ValueError(f"C_ASSOC charge bound fails at hour {t + 1}")
        if discharge < -tol or discharge > b.discharge_max_mw + tol:
            raise ValueError(f"C_ASSOC discharge bound fails at hour {t + 1}")
        if charge > tol and discharge > tol:
            raise ValueError(f"C_ASSOC mode exclusivity fails at hour {t + 1}")
        if (
            curtail < -tol
            or curtail > system.forecast_pv_mw[t] + tol
        ):
            raise ValueError(f"C_ASSOC curtailment bound fails at hour {t + 1}")
        expected_hybrid = (
            system.forecast_pv_mw[t] - curtail + discharge - charge
        )
        if abs(expected_hybrid - decision.hybrid_injection_mw[t]) > tol:
            raise ValueError(f"C_ASSOC injection identity fails at hour {t + 1}")
        expected_next = (
            energy
            + b.charge_efficiency * charge * b.interval_hours
            - discharge * b.interval_hours / b.discharge_efficiency
        )
        if abs(expected_next - next_energy) > tol:
            raise ValueError(f"C_ASSOC SOC identity fails at hour {t + 1}")
        if discharge + up > b.discharge_max_mw + tol:
            raise ValueError(f"C_ASSOC upward power fails at hour {t + 1}")
        if charge + down > b.charge_max_mw + tol:
            raise ValueError(f"C_ASSOC downward power fails at hour {t + 1}")
        if (
            up * b.reserve_duration_hours / b.discharge_efficiency
            > energy + tol
        ):
            raise ValueError(f"C_ASSOC upward energy fails at hour {t + 1}")
        if (
            energy
            + b.charge_efficiency * down * b.reserve_duration_hours
            > b.energy_capacity_mwh + tol
        ):
            raise ValueError(f"C_ASSOC downward energy fails at hour {t + 1}")


class _MILP:
    def __init__(self) -> None:
        self.lower: list[float] = []
        self.upper: list[float] = []
        self.integrality: list[int] = []
        self.objective: list[float] = []
        self.row_i: list[int] = []
        self.col_i: list[int] = []
        self.data: list[float] = []
        self.row_lower: list[float] = []
        self.row_upper: list[float] = []

    def variable(
        self,
        *,
        lower: float = 0.0,
        upper: float = math.inf,
        objective: float = 0.0,
        binary: bool = False,
    ) -> int:
        index = len(self.lower)
        self.lower.append(lower)
        self.upper.append(1.0 if binary else upper)
        self.integrality.append(1 if binary else 0)
        self.objective.append(objective)
        return index

    def row(
        self,
        coefficients: Mapping[int, float],
        *,
        lower: float = -math.inf,
        upper: float = math.inf,
    ) -> None:
        row = len(self.row_lower)
        for column, value in coefficients.items():
            if abs(value) > 0:
                self.row_i.append(row)
                self.col_i.append(column)
                self.data.append(float(value))
        self.row_lower.append(lower)
        self.row_upper.append(upper)

    def equality(self, coefficients: Mapping[int, float], rhs: float) -> None:
        self.row(coefficients, lower=rhs, upper=rhs)

    def solve(self, config: SolverConfig):
        import time

        matrix = coo_matrix(
            (self.data, (self.row_i, self.col_i)),
            shape=(len(self.row_lower), len(self.lower)),
        ).tocsc()
        start = time.perf_counter()
        result = milp(
            np.asarray(self.objective),
            integrality=np.asarray(self.integrality),
            bounds=Bounds(np.asarray(self.lower), np.asarray(self.upper)),
            constraints=LinearConstraint(
                matrix,
                np.asarray(self.row_lower),
                np.asarray(self.row_upper),
            ),
            options={
                "presolve": config.presolve,
                "mip_rel_gap": config.mip_rel_gap,
                "time_limit": config.time_limit_seconds,
            },
        )
        elapsed = time.perf_counter() - start
        gap = _optional_float(getattr(result, "mip_gap", None))
        has_incumbent = getattr(result, "x", None) is not None
        has_integer_variables = any(self.integrality)
        unresolved = not has_incumbent or int(result.status) not in {0}
        if has_integer_variables:
            unresolved = (
                unresolved
                or gap is None
                or gap > config.mip_rel_gap + 1e-12
            )
        diagnostics = SolveDiagnostics(
            status=int(result.status),
            termination=str(result.message),
            success=bool(result.success),
            solver_unresolved=unresolved,
            incumbent_objective=_optional_float(getattr(result, "fun", None)),
            best_bound=_optional_float(getattr(result, "mip_dual_bound", None)),
            relative_gap=gap,
            node_count=_optional_int(getattr(result, "mip_node_count", None)),
            variable_count=len(self.lower),
            constraint_count=len(self.row_lower),
            binary_count=sum(self.integrality),
            solve_seconds=elapsed,
        )
        return result, diagnostics


@dataclass(frozen=True)
class _Stage2Layout:
    thermal_segments: Tuple[Tuple[Tuple[int, ...], ...], ...]
    charge: Tuple[int, ...]
    discharge: Tuple[int, ...]
    mode: Tuple[int, ...]
    up_mode: Tuple[int, ...]
    down_mode: Tuple[int, ...]
    soc: Tuple[int, ...]
    curtail: Tuple[int, ...]
    imbalance_pos: Tuple[int, ...]
    imbalance_neg: Tuple[int, ...]
    short_up: Tuple[int, ...]
    short_down: Tuple[int, ...]
    shed: Tuple[int, ...]
    spill: Tuple[int, ...]
    up_pv: Tuple[int, ...]
    up_charge: Tuple[int, ...]
    up_discharge: Tuple[int, ...]
    down_pv: Tuple[int, ...]
    down_charge: Tuple[int, ...]
    down_discharge: Tuple[int, ...]


@dataclass(frozen=True)
class _Stage1Layout:
    thermal_segments: Tuple[Tuple[Tuple[int, ...], ...], ...]
    hybrid: Tuple[int, ...]
    thermal_up: Tuple[Tuple[int, ...], ...]
    thermal_down: Tuple[Tuple[int, ...], ...]
    hybrid_up: Tuple[int, ...]
    hybrid_down: Tuple[int, ...]
    shed: Tuple[int, ...]
    spill: Tuple[int, ...]
    declared_soc: Tuple[int, ...] = field(default_factory=tuple)
    declared_charge: Tuple[int, ...] = field(default_factory=tuple)
    declared_discharge: Tuple[int, ...] = field(default_factory=tuple)
    declared_curtail: Tuple[int, ...] = field(default_factory=tuple)


def solve_stage2(
    system: V2System,
    stage1: Stage1Decision,
    realized_pv_mw: Sequence[float],
    *,
    config: SolverConfig = SolverConfig(),
) -> Stage2SolveResult:
    """Solve the registered common scenario recourse for frozen stage 1."""

    validate_stage1(system, stage1)
    pv = tuple(float(value) for value in realized_pv_mw)
    if len(pv) != system.horizon:
        raise ValueError("realized PV path has the wrong horizon")
    if any(value < -TOLERANCE or value > 200.0 + TOLERANCE for value in pv):
        raise ValueError("realized PV lies outside [0, 200] MW")

    model = _MILP()
    layout, constant_cost = _build_stage2_block(
        model,
        system,
        stage1,
        pv,
        relax_base_modes=config.relax_base_modes,
        relax_up_activation_modes=config.relax_up_activation_modes,
        relax_down_activation_modes=config.relax_down_activation_modes,
        integer_base_mode_hours=config.integer_base_mode_hours,
        integer_up_activation_hours=config.integer_up_activation_hours,
        integer_down_activation_hours=config.integer_down_activation_hours,
    )
    raw, diagnostics = model.solve(config)
    if raw.x is None:
        return Stage2SolveResult(None, diagnostics)
    variable_cost = float(np.dot(np.asarray(model.objective), raw.x))
    decision = _extract_stage2(
        system,
        layout,
        raw.x,
        serialized_primal_cost=constant_cost + variable_cost,
        round_modes=not (
            config.relax_base_modes
            or config.relax_up_activation_modes
            or config.relax_down_activation_modes
        ),
    )
    return Stage2SolveResult(decision, diagnostics)


def solve_extensive_form(
    system: V2System,
    pv_scenarios_mw: Sequence[Sequence[float]],
    contract: str,
    *,
    c0_parameters=None,
    c1_band=None,
    force_hybrid_reserve_zero: bool = False,
    config: SolverConfig = SolverConfig(),
) -> ExtensiveFormResult:
    """Solve one nonanticipative stage-1 schedule with scenario recourse.

    ``contract`` must be ``"c0"``, ``"c1"``, ``"c1_v3"``,
    ``"c_assoc"``, or ``"c_full"``. The physical recourse block, objective,
    solver, and tolerances are identical; only the registered stage-1
    contract constraints differ.
    """

    if contract not in {"c0", "c1", "c1_v3", "c_assoc", "c_full"}:
        raise ValueError(
            "contract must be c0, c1, c1_v3, c_assoc, or c_full"
        )
    if contract == "c0" and c0_parameters is None:
        raise ValueError("c0 requires parameters")
    if contract in {"c1", "c1_v3"} and c1_band is None:
        raise ValueError("c1 requires a PV band")
    scenarios = np.asarray(pv_scenarios_mw, dtype=float)
    if (
        scenarios.ndim != 2
        or scenarios.shape[0] < 1
        or scenarios.shape[1] != system.horizon
    ):
        raise ValueError("PV scenarios must have shape (n, horizon)")
    if np.any(scenarios < -TOLERANCE) or np.any(scenarios > 200.0 + TOLERANCE):
        raise ValueError("PV scenarios lie outside [0, 200] MW")

    model = _MILP()
    stage1_layout = _build_stage1(
        model, system, contract, c0_parameters, c1_band
    )
    if force_hybrid_reserve_zero:
        for up, down in zip(
            stage1_layout.hybrid_up, stage1_layout.hybrid_down
        ):
            model.equality({up: 1.0}, 0.0)
            model.equality({down: 1.0}, 0.0)
    scenario_layouts = []
    weight = 1.0 / len(scenarios)
    constant_cost = 0.0
    for path in scenarios:
        layout, block_constant = _build_linked_stage2_block(
            model,
            system,
            stage1_layout,
            tuple(float(value) for value in path),
            objective_weight=weight,
            relax_base_modes=config.relax_base_modes,
            relax_up_activation_modes=config.relax_up_activation_modes,
            relax_down_activation_modes=config.relax_down_activation_modes,
            integer_base_mode_hours=config.integer_base_mode_hours,
            integer_up_activation_hours=config.integer_up_activation_hours,
            integer_down_activation_hours=config.integer_down_activation_hours,
        )
        scenario_layouts.append(layout)
        constant_cost += block_constant
    raw, diagnostics = model.solve(config)
    if raw.x is None:
        return ExtensiveFormResult(None, tuple(), None, diagnostics)
    stage1 = _extract_stage1(system, stage1_layout, raw.x)
    extracted = []
    for layout in scenario_layouts:
        provisional = _extract_stage2(
            system,
            layout,
            raw.x,
            serialized_primal_cost=0.0,
            round_modes=not (
                config.relax_base_modes
                or config.relax_up_activation_modes
                or config.relax_down_activation_modes
            ),
        )
        serialized = evaluate_serialized_primal_cost(system, stage1, provisional)
        extracted.append(
            ScenarioDecision(
                **{
                    **provisional.__dict__,
                    "serialized_primal_cost": serialized,
                }
            )
        )
    objective = constant_cost + float(np.dot(np.asarray(model.objective), raw.x))
    return ExtensiveFormResult(
        stage1=stage1,
        scenarios=tuple(extracted),
        objective=objective,
        diagnostics=diagnostics,
    )


def solve_multistratum_c0(
    systems: Sequence[V2System],
    pv_scenarios_by_stratum: Sequence[Sequence[Sequence[float]]],
    c0_parameters,
    *,
    config: SolverConfig = SolverConfig(),
) -> MultiStratumResult:
    """Solve Amendment-5's one block-diagonal 384-record C0 fit."""

    if len(systems) != 6 or len(pv_scenarios_by_stratum) != 6:
        raise ValueError("C0 fitting requires exactly six registered strata")
    counts = [len(paths) for paths in pv_scenarios_by_stratum]
    if counts != [64] * 6:
        raise ValueError("each C0 fitting stratum must contain exactly 64 paths")
    total = sum(counts)
    model = _MILP()
    stage1_layouts = []
    scenario_layouts_by_stratum = []
    constant_cost = 0.0
    for system, paths in zip(systems, pv_scenarios_by_stratum):
        stage1_layout = _build_stage1(
            model,
            system,
            "c0",
            c0_parameters,
            None,
            objective_weight=len(paths) / total,
        )
        stage1_layouts.append(stage1_layout)
        layouts = []
        for path in paths:
            layout, block_constant = _build_linked_stage2_block(
                model,
                system,
                stage1_layout,
                tuple(float(value) for value in path),
                objective_weight=1.0 / total,
                relax_base_modes=config.relax_base_modes,
                relax_up_activation_modes=config.relax_up_activation_modes,
                relax_down_activation_modes=config.relax_down_activation_modes,
                integer_base_mode_hours=config.integer_base_mode_hours,
                integer_up_activation_hours=config.integer_up_activation_hours,
                integer_down_activation_hours=config.integer_down_activation_hours,
            )
            layouts.append(layout)
            constant_cost += block_constant
        scenario_layouts_by_stratum.append(tuple(layouts))
    raw, diagnostics = model.solve(config)
    if raw.x is None:
        return MultiStratumResult(tuple(), tuple(), None, diagnostics)
    stages = tuple(
        _extract_stage1(system, layout, raw.x)
        for system, layout in zip(systems, stage1_layouts)
    )
    grouped = []
    for system, stage1, layouts in zip(
        systems, stages, scenario_layouts_by_stratum
    ):
        decisions = []
        for layout in layouts:
            provisional = _extract_stage2(
                system,
                layout,
                raw.x,
                serialized_primal_cost=0.0,
                round_modes=not (
                    config.relax_base_modes
                    or config.relax_up_activation_modes
                    or config.relax_down_activation_modes
                ),
            )
            serialized = evaluate_serialized_primal_cost(
                system, stage1, provisional
            )
            decisions.append(
                ScenarioDecision(
                    **{
                        **provisional.__dict__,
                        "serialized_primal_cost": serialized,
                    }
                )
            )
        grouped.append(tuple(decisions))
    objective = constant_cost + float(np.dot(np.asarray(model.objective), raw.x))
    return MultiStratumResult(
        stage1_by_stratum=stages,
        scenarios_by_stratum=tuple(grouped),
        objective=objective,
        diagnostics=diagnostics,
    )


def solve_wait_and_see(
    system: V2System,
    realized_pv_mw: Sequence[float],
    *,
    config: SolverConfig = SolverConfig(),
) -> ExtensiveFormResult:
    """Solve the registered path-revealed C_WS benchmark."""

    return solve_extensive_form(
        system,
        (tuple(realized_pv_mw),),
        "c_full",
        config=config,
    )


def _build_stage1(
    model: _MILP,
    system: V2System,
    contract: str,
    c0_parameters,
    c1_band,
    *,
    objective_weight: float = 1.0,
) -> _Stage1Layout:
    h = system.horizon
    p = system.penalties
    b = system.battery
    thermal_segments = []
    for unit in system.thermal_units:
        unit_segments = []
        for width in unit.segment_widths_mw:
            unit_segments.append(
                tuple(model.variable(upper=width) for _ in range(h))
            )
        thermal_segments.append(tuple(unit_segments))
    hybrid = tuple(model.variable(lower=-50.0, upper=250.0) for _ in range(h))
    thermal_up = tuple(
        tuple(
            model.variable(
                upper=unit.ramp_mw_per_hour * b.reserve_duration_hours,
                objective=objective_weight * p.thermal_reserve_per_mw,
            )
            for _ in range(h)
        )
        for unit in system.thermal_units
    )
    thermal_down = tuple(
        tuple(
            model.variable(
                upper=unit.ramp_mw_per_hour * b.reserve_duration_hours,
                objective=objective_weight * p.thermal_reserve_per_mw,
            )
            for _ in range(h)
        )
        for unit in system.thermal_units
    )
    hybrid_up = tuple(
        model.variable(
            upper=50.0,
            objective=objective_weight * p.hybrid_reserve_per_mw,
        )
        for _ in range(h)
    )
    hybrid_down = tuple(
        model.variable(
            upper=50.0,
            objective=objective_weight * p.hybrid_reserve_per_mw,
        )
        for _ in range(h)
    )
    shed = tuple(
        model.variable(
            objective=objective_weight * p.load_shedding_per_mwh * b.interval_hours
        )
        for _ in range(h)
    )
    spill = tuple(
        model.variable(
            objective=objective_weight
            * p.emergency_spill_per_mwh
            * b.interval_hours
        )
        for _ in range(h)
    )
    declared_soc: Tuple[int, ...] = ()
    declared_charge: Tuple[int, ...] = ()
    declared_discharge: Tuple[int, ...] = ()
    declared_curtail: Tuple[int, ...] = ()
    requirement = system.reserve_requirement_mw
    for t in range(h):
        balance: Dict[int, float] = {
            hybrid[t]: 1.0,
            shed[t]: 1.0,
            spill[t]: -1.0,
        }
        thermal_min = 0.0
        for g, unit in enumerate(system.thermal_units):
            thermal_min += unit.power_min_mw
            for segment in thermal_segments[g]:
                balance[segment[t]] = 1.0
        model.equality(balance, system.load_mw[t] - thermal_min)
        up_row: Dict[int, float] = {hybrid_up[t]: 1.0}
        down_row: Dict[int, float] = {hybrid_down[t]: 1.0}
        for g, unit in enumerate(system.thermal_units):
            up_row[thermal_up[g][t]] = 1.0
            down_row[thermal_down[g][t]] = 1.0
            above = {segment[t]: 1.0 for segment in thermal_segments[g]}
            model.row(
                {**above, thermal_up[g][t]: 1.0},
                upper=unit.power_max_mw - unit.power_min_mw,
            )
            foot = dict(above)
            foot[thermal_down[g][t]] = -1.0
            model.row(foot, lower=0.0)
        model.row(up_row, lower=requirement[t])
        model.row(down_row, lower=requirement[t])
    for t in range(1, h):
        for g, unit in enumerate(system.thermal_units):
            ramp: Dict[int, float] = {}
            for segment in thermal_segments[g]:
                ramp[segment[t]] = 1.0
                ramp[segment[t - 1]] = -1.0
            model.row(
                ramp,
                lower=-unit.ramp_mw_per_hour * b.interval_hours,
                upper=unit.ramp_mw_per_hour * b.interval_hours,
            )

    if contract == "c0":
        theta = c0_parameters
        for t in range(h):
            model.row(
                {hybrid[t]: 1.0},
                lower=system.forecast_pv_mw[t] - theta.power_cap_mw,
                upper=system.forecast_pv_mw[t] + theta.power_cap_mw,
            )
            model.row({hybrid_up[t]: 1.0}, upper=theta.up_reserve_cap_mw)
            model.row({hybrid_down[t]: 1.0}, upper=theta.down_reserve_cap_mw)
            if t:
                model.row(
                    {hybrid[t]: 1.0, hybrid[t - 1]: -1.0},
                    lower=(
                        system.forecast_pv_mw[t]
                        - system.forecast_pv_mw[t - 1]
                        - theta.ramp_cap_mw_per_hour
                    ),
                    upper=(
                        system.forecast_pv_mw[t]
                        - system.forecast_pv_mw[t - 1]
                        + theta.ramp_cap_mw_per_hour
                    ),
                )
    elif contract == "c1":
        band = c1_band
        if len(band.lower_mw) != h:
            raise ValueError("C1 band has the wrong horizon")
        x_dis = tuple(model.variable() for _ in range(h))
        x_ch = tuple(model.variable() for _ in range(h))
        for t in range(h):
            model.row(
                {x_dis[t]: 1.0, hybrid[t]: -1.0},
                lower=-band.lower_mw[t],
            )
            model.row(
                {x_ch[t]: 1.0, hybrid[t]: 1.0},
                lower=band.upper_mw[t],
            )
            upper_prefix: Dict[int, float] = {
                hybrid_up[t]: b.reserve_duration_hours / b.discharge_efficiency
            }
            lower_prefix: Dict[int, float] = {
                hybrid_down[t]: b.charge_efficiency * b.reserve_duration_hours
            }
            for prior in range(t + 1):
                upper_prefix[x_dis[prior]] = (
                    b.interval_hours / b.discharge_efficiency
                )
                lower_prefix[x_ch[prior]] = (
                    b.charge_efficiency * b.interval_hours
                )
            model.row(upper_prefix, upper=b.initial_energy_mwh)
            model.row(
                lower_prefix,
                upper=b.energy_capacity_mwh - b.initial_energy_mwh,
            )
        terminal = {
            x_dis[t]: b.interval_hours / b.discharge_efficiency
            for t in range(h)
        }
        model.row(
            terminal,
            upper=b.initial_energy_mwh - b.terminal_energy_mwh,
        )
    elif contract == "c1_v3":
        band = c1_band
        if len(band.lower_mw) != h:
            raise ValueError("C1 band has the wrong horizon")

        # Exact epigraph x_dis[t] = max(h[t] - lower[t], 0).  The binary is
        # necessary: a loose epigraph could otherwise inflate x_dis and create
        # artificial downward-reserve capability.
        big_m = 250.0
        x_dis = tuple(model.variable(upper=big_m) for _ in range(h))
        x_positive = tuple(model.variable(binary=True) for _ in range(h))
        for t in range(h):
            lower_pv = float(band.lower_mw[t])
            model.row({hybrid[t]: 1.0}, lower=0.0)
            model.row(
                {x_dis[t]: 1.0, hybrid[t]: -1.0},
                lower=-lower_pv,
            )
            model.row(
                {
                    x_dis[t]: 1.0,
                    hybrid[t]: -1.0,
                    x_positive[t]: big_m,
                },
                upper=big_m - lower_pv,
            )
            model.row(
                {x_dis[t]: 1.0, x_positive[t]: -big_m},
                upper=0.0,
            )

            discharge_prefix: Dict[int, float] = {
                hybrid_up[t]: b.reserve_duration_hours
                / b.discharge_efficiency
            }
            for prior in range(t + 1):
                discharge_prefix[x_dis[prior]] = (
                    b.interval_hours / b.discharge_efficiency
                )
            model.row(discharge_prefix, upper=b.initial_energy_mwh)

            # At the lower-PV boundary, downward response is supplied in the
            # registered order: reduce discharge, charge, then curtail PV.
            model.row(
                {hybrid_down[t]: 1.0, x_dis[t]: -1.0},
                upper=b.charge_max_mw + lower_pv,
            )
            charge_headroom = (
                b.energy_capacity_mwh - b.initial_energy_mwh
            )
            full_charge_energy = (
                b.charge_efficiency
                * b.charge_max_mw
                * b.reserve_duration_hours
            )
            if charge_headroom < full_charge_energy - TOLERANCE:
                model.row(
                    {hybrid_down[t]: 1.0, x_dis[t]: -1.0},
                    upper=charge_headroom
                    / (b.charge_efficiency * b.reserve_duration_hours),
                )

        terminal = {
            x_dis[t]: b.interval_hours / b.discharge_efficiency
            for t in range(h)
        }
        model.row(
            terminal,
            upper=b.initial_energy_mwh - b.terminal_energy_mwh,
        )
    elif contract == "c_assoc":
        declared_charge = tuple(
            model.variable(upper=b.charge_max_mw) for _ in range(h)
        )
        declared_discharge = tuple(
            model.variable(upper=b.discharge_max_mw) for _ in range(h)
        )
        declared_mode = tuple(model.variable(binary=True) for _ in range(h))
        declared_soc = tuple(
            model.variable(upper=b.energy_capacity_mwh)
            for _ in range(h + 1)
        )
        declared_curtail = tuple(
            model.variable(upper=float(system.forecast_pv_mw[t]))
            for t in range(h)
        )
        model.equality({declared_soc[0]: 1.0}, b.initial_energy_mwh)
        model.row(
            {declared_soc[h]: 1.0},
            lower=b.terminal_energy_mwh,
        )
        for t in range(h):
            model.equality(
                {
                    declared_soc[t + 1]: 1.0,
                    declared_soc[t]: -1.0,
                    declared_charge[t]: -b.charge_efficiency
                    * b.interval_hours,
                    declared_discharge[t]: b.interval_hours
                    / b.discharge_efficiency,
                },
                0.0,
            )
            model.equality(
                {
                    hybrid[t]: 1.0,
                    declared_curtail[t]: 1.0,
                    declared_discharge[t]: -1.0,
                    declared_charge[t]: 1.0,
                },
                float(system.forecast_pv_mw[t]),
            )
            model.row(
                {
                    declared_charge[t]: 1.0,
                    declared_mode[t]: b.charge_max_mw,
                },
                upper=b.charge_max_mw,
            )
            model.row(
                {
                    declared_discharge[t]: 1.0,
                    declared_mode[t]: -b.discharge_max_mw,
                },
                upper=0.0,
            )

            # Conservative CAISO-style market proxy: every aggregate hybrid
            # reserve MW is treated as battery-backed. Renewable curtailment
            # headroom is intentionally not credited.
            model.row(
                {
                    declared_discharge[t]: 1.0,
                    hybrid_up[t]: 1.0,
                },
                upper=b.discharge_max_mw,
            )
            model.row(
                {
                    declared_charge[t]: 1.0,
                    hybrid_down[t]: 1.0,
                },
                upper=b.charge_max_mw,
            )
            model.row(
                {
                    declared_soc[t]: 1.0,
                    hybrid_up[t]: -b.reserve_duration_hours
                    / b.discharge_efficiency,
                },
                lower=0.0,
            )
            model.row(
                {
                    declared_soc[t]: 1.0,
                    hybrid_down[t]: b.charge_efficiency
                    * b.reserve_duration_hours,
                },
                upper=b.energy_capacity_mwh,
            )

    layout = _Stage1Layout(
        thermal_segments=tuple(thermal_segments),
        hybrid=hybrid,
        thermal_up=thermal_up,
        thermal_down=thermal_down,
        hybrid_up=hybrid_up,
        hybrid_down=hybrid_down,
        shed=shed,
        spill=spill,
        declared_soc=declared_soc,
        declared_charge=declared_charge,
        declared_discharge=declared_discharge,
        declared_curtail=declared_curtail,
    )
    return layout


def _build_linked_stage2_block(
    model: _MILP,
    system: V2System,
    stage1: _Stage1Layout,
    pv: Sequence[float],
    *,
    objective_weight: float,
    relax_base_modes: bool = False,
    relax_up_activation_modes: bool = False,
    relax_down_activation_modes: bool = False,
    integer_base_mode_hours: Sequence[int] = (),
    integer_up_activation_hours: Sequence[int] = (),
    integer_down_activation_hours: Sequence[int] = (),
) -> Tuple[_Stage2Layout, float]:
    """Add one recourse block linked to variable stage-1 decisions."""

    h = system.horizon
    battery = system.battery
    dt = battery.interval_hours
    tau = battery.reserve_duration_hours
    eta_c = battery.charge_efficiency
    eta_d = battery.discharge_efficiency
    penalties = system.penalties
    thermal_segments = []
    constant_cost = 0.0
    for unit in system.thermal_units:
        constant_cost += objective_weight * h * (
            unit.power_min_mw * unit.segment_costs_per_mwh[0] * dt
        )
        unit_rows = []
        for width, cost in zip(unit.segment_widths_mw, unit.segment_costs_per_mwh):
            unit_rows.append(
                tuple(
                    model.variable(
                        upper=width,
                        objective=objective_weight * cost * dt,
                    )
                    for _ in range(h)
                )
            )
        thermal_segments.append(tuple(unit_rows))

    def vec(*, upper=math.inf, objective=0.0, binary=False):
        return tuple(
            model.variable(upper=upper, objective=objective, binary=binary)
            for _ in range(h)
        )

    charge = vec(
        upper=battery.charge_max_mw,
        objective=objective_weight * penalties.battery_throughput_per_mwh * dt,
    )
    discharge = vec(
        upper=battery.discharge_max_mw,
        objective=objective_weight * penalties.battery_throughput_per_mwh * dt,
    )
    base_integer = set(integer_base_mode_hours)
    up_integer = set(integer_up_activation_hours)
    down_integer = set(integer_down_activation_hours)
    mode = tuple(
        model.variable(
            upper=1.0,
            binary=(not relax_base_modes or t in base_integer),
        )
        for t in range(h)
    )
    up_mode = tuple(
        model.variable(
            upper=1.0,
            binary=(not relax_up_activation_modes or t in up_integer),
        )
        for t in range(h)
    )
    down_mode = tuple(
        model.variable(
            upper=1.0,
            binary=(not relax_down_activation_modes or t in down_integer),
        )
        for t in range(h)
    )
    soc = tuple(
        model.variable(upper=battery.energy_capacity_mwh) for _ in range(h + 1)
    )
    curtail = tuple(
        model.variable(
            upper=float(pv[t]),
            objective=objective_weight * penalties.pv_curtailment_per_mwh * dt,
        )
        for t in range(h)
    )
    imbalance_pos = vec(
        objective=objective_weight * penalties.imbalance_per_mwh * dt
    )
    imbalance_neg = vec(
        objective=objective_weight * penalties.imbalance_per_mwh * dt
    )
    short_up = vec(
        objective=objective_weight
        * penalties.reserve_shortfall_per_mwh
        * tau
    )
    short_down = vec(
        objective=objective_weight
        * penalties.reserve_shortfall_per_mwh
        * tau
    )
    shed = vec(
        objective=objective_weight * penalties.load_shedding_per_mwh * dt
    )
    spill = vec(
        objective=objective_weight * penalties.emergency_spill_per_mwh * dt
    )
    up_pv = vec(upper=200.0)
    up_charge = vec(upper=battery.charge_max_mw)
    up_discharge = vec(upper=battery.discharge_max_mw)
    down_pv = vec(upper=200.0)
    down_charge = vec(upper=battery.charge_max_mw)
    down_discharge = vec(upper=battery.discharge_max_mw)
    layout = _Stage2Layout(
        thermal_segments=tuple(thermal_segments),
        charge=charge,
        discharge=discharge,
        mode=mode,
        up_mode=up_mode,
        down_mode=down_mode,
        soc=soc,
        curtail=curtail,
        imbalance_pos=imbalance_pos,
        imbalance_neg=imbalance_neg,
        short_up=short_up,
        short_down=short_down,
        shed=shed,
        spill=spill,
        up_pv=up_pv,
        up_charge=up_charge,
        up_discharge=up_discharge,
        down_pv=down_pv,
        down_charge=down_charge,
        down_discharge=down_discharge,
    )
    model.equality({soc[0]: 1.0}, battery.initial_energy_mwh)
    model.row({soc[h]: 1.0}, lower=battery.terminal_energy_mwh)
    for t in range(h):
        model.equality(
            {
                soc[t + 1]: 1.0,
                soc[t]: -1.0,
                charge[t]: -eta_c * dt,
                discharge[t]: dt / eta_d,
            },
            0.0,
        )
        model.row(
            {charge[t]: 1.0, mode[t]: battery.charge_max_mw},
            upper=battery.charge_max_mw,
        )
        model.row(
            {discharge[t]: 1.0, mode[t]: -battery.discharge_max_mw},
            upper=0.0,
        )
        balance: Dict[int, float] = {
            discharge[t]: 1.0,
            charge[t]: -1.0,
            curtail[t]: -1.0,
            shed[t]: 1.0,
            spill[t]: -1.0,
        }
        thermal_min = 0.0
        for g, unit in enumerate(system.thermal_units):
            thermal_min += unit.power_min_mw
            for segment in thermal_segments[g]:
                balance[segment[t]] = 1.0
        model.equality(
            balance,
            system.load_mw[t] - float(pv[t]) - thermal_min,
        )
        model.equality(
            {
                discharge[t]: 1.0,
                charge[t]: -1.0,
                curtail[t]: -1.0,
                imbalance_pos[t]: -1.0,
                imbalance_neg[t]: 1.0,
                stage1.hybrid[t]: -1.0,
            },
            -float(pv[t]),
        )
        model.equality(
            {
                up_pv[t]: 1.0,
                up_charge[t]: 1.0,
                up_discharge[t]: 1.0,
                short_up[t]: 1.0,
                stage1.hybrid_up[t]: -1.0,
            },
            0.0,
        )
        model.equality(
            {
                down_pv[t]: 1.0,
                down_charge[t]: 1.0,
                down_discharge[t]: 1.0,
                short_down[t]: 1.0,
                stage1.hybrid_down[t]: -1.0,
            },
            0.0,
        )
        model.row({up_pv[t]: 1.0, curtail[t]: -1.0}, upper=0.0)
        model.row({up_charge[t]: 1.0, charge[t]: -1.0}, upper=0.0)
        model.row(
            {
                charge[t]: 1.0,
                up_charge[t]: -1.0,
                up_mode[t]: battery.charge_max_mw,
            },
            upper=battery.charge_max_mw,
        )
        model.row(
            {
                discharge[t]: 1.0,
                up_discharge[t]: 1.0,
                up_mode[t]: -battery.discharge_max_mw,
            },
            upper=0.0,
        )
        model.row({down_pv[t]: 1.0, curtail[t]: 1.0}, upper=float(pv[t]))
        model.row(
            {
                charge[t]: 1.0,
                down_charge[t]: 1.0,
                down_mode[t]: battery.charge_max_mw,
            },
            upper=battery.charge_max_mw,
        )
        model.row(
            {down_discharge[t]: 1.0, discharge[t]: -1.0},
            upper=0.0,
        )
        model.row(
            {
                discharge[t]: 1.0,
                down_discharge[t]: -1.0,
                down_mode[t]: -battery.discharge_max_mw,
            },
            upper=0.0,
        )
        model.row(
            {
                soc[t]: 1.0,
                charge[t]: eta_c * tau,
                up_charge[t]: -eta_c * tau,
                discharge[t]: -tau / eta_d,
                up_discharge[t]: -tau / eta_d,
            },
            lower=0.0,
            upper=battery.energy_capacity_mwh,
        )
        model.row(
            {
                soc[t + 1]: 1.0,
                up_charge[t]: -eta_c * tau,
                up_discharge[t]: -tau / eta_d,
            },
            lower=0.0,
            upper=battery.energy_capacity_mwh,
        )
        model.row(
            {
                soc[t]: 1.0,
                charge[t]: eta_c * tau,
                down_charge[t]: eta_c * tau,
                discharge[t]: -tau / eta_d,
                down_discharge[t]: tau / eta_d,
            },
            lower=0.0,
            upper=battery.energy_capacity_mwh,
        )
        model.row(
            {
                soc[t + 1]: 1.0,
                down_charge[t]: eta_c * tau,
                down_discharge[t]: tau / eta_d,
            },
            lower=0.0,
            upper=battery.energy_capacity_mwh,
        )
        for g, unit in enumerate(system.thermal_units):
            above_rt = {segment[t]: 1.0 for segment in thermal_segments[g]}
            redispatch = dict(above_rt)
            for segment in stage1.thermal_segments[g]:
                redispatch[segment[t]] = -1.0
            model.row(
                redispatch,
                lower=-unit.ramp_mw_per_hour * dt,
                upper=unit.ramp_mw_per_hour * dt,
            )
            up_headroom = dict(above_rt)
            up_headroom[stage1.thermal_up[g][t]] = 1.0
            model.row(
                up_headroom,
                upper=unit.power_max_mw - unit.power_min_mw,
            )
            foot = dict(above_rt)
            foot[stage1.thermal_down[g][t]] = -1.0
            model.row(foot, lower=0.0)
    for t in range(1, h):
        for g, unit in enumerate(system.thermal_units):
            ramp: Dict[int, float] = {}
            for segment in thermal_segments[g]:
                ramp[segment[t]] = 1.0
                ramp[segment[t - 1]] = -1.0
            model.row(
                ramp,
                lower=-unit.ramp_mw_per_hour * dt,
                upper=unit.ramp_mw_per_hour * dt,
            )
    return layout, constant_cost


def _extract_stage1(
    system: V2System,
    layout: _Stage1Layout,
    values: np.ndarray,
) -> Stage1Decision:
    thermal = []
    for g, unit in enumerate(system.thermal_units):
        thermal.append(
            tuple(
                unit.power_min_mw
                + sum(values[segment[t]] for segment in layout.thermal_segments[g])
                for t in range(system.horizon)
            )
        )

    def vector(indices: Sequence[int]) -> Tuple[float, ...]:
        return tuple(float(values[index]) for index in indices)

    return Stage1Decision(
        thermal_dispatch_mw=tuple(thermal),
        hybrid_injection_mw=vector(layout.hybrid),
        thermal_up_reserve_mw=tuple(vector(row) for row in layout.thermal_up),
        thermal_down_reserve_mw=tuple(vector(row) for row in layout.thermal_down),
        hybrid_up_reserve_mw=vector(layout.hybrid_up),
        hybrid_down_reserve_mw=vector(layout.hybrid_down),
        day_ahead_load_shedding_mw=vector(layout.shed),
        day_ahead_spill_mw=vector(layout.spill),
        declared_soc_mwh=vector(layout.declared_soc),
        declared_charge_mw=vector(layout.declared_charge),
        declared_discharge_mw=vector(layout.declared_discharge),
        declared_pv_curtailment_mw=vector(layout.declared_curtail),
    )


def evaluate_serialized_primal_cost(
    system: V2System,
    stage1: Stage1Decision,
    decision: ScenarioDecision,
) -> float:
    """Solver-side primal cost serialization, independent of replay code."""

    p = system.penalties
    dt = system.battery.interval_hours
    tau = system.battery.reserve_duration_hours
    total = sum(
        thermal_cost(unit, segments, interval_hours=dt)
        for unit, segments in zip(system.thermal_units, decision.thermal_segment_mw)
    )
    total += p.thermal_reserve_per_mw * sum(
        sum(row)
        for matrix in (
            stage1.thermal_up_reserve_mw,
            stage1.thermal_down_reserve_mw,
        )
        for row in matrix
    )
    total += p.hybrid_reserve_per_mw * (
        sum(stage1.hybrid_up_reserve_mw)
        + sum(stage1.hybrid_down_reserve_mw)
    )
    total += p.load_shedding_per_mwh * dt * sum(
        _stage1_optional_vector(
            stage1.day_ahead_load_shedding_mw, system.horizon
        )
    )
    total += p.emergency_spill_per_mwh * dt * sum(
        _stage1_optional_vector(stage1.day_ahead_spill_mw, system.horizon)
    )
    total += p.load_shedding_per_mwh * dt * sum(decision.load_shedding_mw)
    total += p.reserve_shortfall_per_mwh * tau * (
        sum(decision.reserve_shortfall_up_mw)
        + sum(decision.reserve_shortfall_down_mw)
    )
    total += p.imbalance_per_mwh * dt * (
        sum(decision.imbalance_positive_mw)
        + sum(decision.imbalance_negative_mw)
    )
    total += p.emergency_spill_per_mwh * dt * sum(decision.emergency_spill_mw)
    total += p.pv_curtailment_per_mwh * dt * sum(decision.pv_curtailment_mw)
    total += p.battery_throughput_per_mwh * dt * (
        sum(decision.charge_mw) + sum(decision.discharge_mw)
    )
    return total


def _build_stage2_block(
    model: _MILP,
    system: V2System,
    stage1: Stage1Decision,
    pv: Sequence[float],
    *,
    objective_weight: float = 1.0,
    relax_base_modes: bool = False,
    relax_up_activation_modes: bool = False,
    relax_down_activation_modes: bool = False,
    integer_base_mode_hours: Sequence[int] = (),
    integer_up_activation_hours: Sequence[int] = (),
    integer_down_activation_hours: Sequence[int] = (),
) -> Tuple[_Stage2Layout, float]:
    h = system.horizon
    battery = system.battery
    dt = battery.interval_hours
    tau = battery.reserve_duration_hours
    eta_c = battery.charge_efficiency
    eta_d = battery.discharge_efficiency
    p = system.penalties

    thermal_segments = []
    constant_cost = p.thermal_reserve_per_mw * sum(
        sum(row)
        for matrix in (
            stage1.thermal_up_reserve_mw,
            stage1.thermal_down_reserve_mw,
        )
        for row in matrix
    )
    constant_cost += p.hybrid_reserve_per_mw * (
        sum(stage1.hybrid_up_reserve_mw)
        + sum(stage1.hybrid_down_reserve_mw)
    )
    constant_cost += p.load_shedding_per_mwh * dt * sum(
        _stage1_optional_vector(
            stage1.day_ahead_load_shedding_mw, system.horizon
        )
    )
    constant_cost += p.emergency_spill_per_mwh * dt * sum(
        _stage1_optional_vector(stage1.day_ahead_spill_mw, system.horizon)
    )
    for unit in system.thermal_units:
        constant_cost += objective_weight * h * (
            unit.power_min_mw * unit.segment_costs_per_mwh[0] * dt
        )
        unit_rows = []
        for width, cost in zip(unit.segment_widths_mw, unit.segment_costs_per_mwh):
            unit_rows.append(
                tuple(
                    model.variable(
                        upper=width,
                        objective=objective_weight * cost * dt,
                    )
                    for _ in range(h)
                )
            )
        thermal_segments.append(tuple(unit_rows))

    charge = tuple(
        model.variable(
            upper=battery.charge_max_mw,
            objective=objective_weight * p.battery_throughput_per_mwh * dt,
        )
        for _ in range(h)
    )
    discharge = tuple(
        model.variable(
            upper=battery.discharge_max_mw,
            objective=objective_weight * p.battery_throughput_per_mwh * dt,
        )
        for _ in range(h)
    )
    base_integer = set(integer_base_mode_hours)
    up_integer = set(integer_up_activation_hours)
    down_integer = set(integer_down_activation_hours)
    mode = tuple(
        model.variable(
            upper=1.0,
            binary=(not relax_base_modes or t in base_integer),
        )
        for t in range(h)
    )
    up_mode = tuple(
        model.variable(
            upper=1.0,
            binary=(not relax_up_activation_modes or t in up_integer),
        )
        for t in range(h)
    )
    down_mode = tuple(
        model.variable(
            upper=1.0,
            binary=(not relax_down_activation_modes or t in down_integer),
        )
        for t in range(h)
    )
    soc = tuple(
        model.variable(upper=battery.energy_capacity_mwh) for _ in range(h + 1)
    )
    curtail = tuple(
        model.variable(
            upper=max(0.0, pv[t]),
            objective=objective_weight * p.pv_curtailment_per_mwh * dt,
        )
        for t in range(h)
    )
    imbalance_pos = tuple(
        model.variable(objective=objective_weight * p.imbalance_per_mwh * dt)
        for _ in range(h)
    )
    imbalance_neg = tuple(
        model.variable(objective=objective_weight * p.imbalance_per_mwh * dt)
        for _ in range(h)
    )
    short_up = tuple(
        model.variable(
            objective=objective_weight * p.reserve_shortfall_per_mwh * tau
        )
        for _ in range(h)
    )
    short_down = tuple(
        model.variable(
            objective=objective_weight * p.reserve_shortfall_per_mwh * tau
        )
        for _ in range(h)
    )
    shed = tuple(
        model.variable(objective=objective_weight * p.load_shedding_per_mwh * dt)
        for _ in range(h)
    )
    spill = tuple(
        model.variable(objective=objective_weight * p.emergency_spill_per_mwh * dt)
        for _ in range(h)
    )
    up_pv = tuple(model.variable(upper=200.0) for _ in range(h))
    up_charge = tuple(model.variable(upper=battery.charge_max_mw) for _ in range(h))
    up_discharge = tuple(
        model.variable(upper=battery.discharge_max_mw) for _ in range(h)
    )
    down_pv = tuple(model.variable(upper=200.0) for _ in range(h))
    down_charge = tuple(
        model.variable(upper=battery.charge_max_mw) for _ in range(h)
    )
    down_discharge = tuple(
        model.variable(upper=battery.discharge_max_mw) for _ in range(h)
    )
    layout = _Stage2Layout(
        thermal_segments=tuple(thermal_segments),
        charge=charge,
        discharge=discharge,
        mode=mode,
        up_mode=up_mode,
        down_mode=down_mode,
        soc=soc,
        curtail=curtail,
        imbalance_pos=imbalance_pos,
        imbalance_neg=imbalance_neg,
        short_up=short_up,
        short_down=short_down,
        shed=shed,
        spill=spill,
        up_pv=up_pv,
        up_charge=up_charge,
        up_discharge=up_discharge,
        down_pv=down_pv,
        down_charge=down_charge,
        down_discharge=down_discharge,
    )

    model.equality({soc[0]: 1.0}, battery.initial_energy_mwh)
    model.row(
        {soc[h]: 1.0},
        lower=battery.terminal_energy_mwh,
    )
    for t in range(h):
        model.equality(
            {
                soc[t + 1]: 1.0,
                soc[t]: -1.0,
                charge[t]: -eta_c * dt,
                discharge[t]: dt / eta_d,
            },
            0.0,
        )
        model.row(
            {charge[t]: 1.0, mode[t]: battery.charge_max_mw},
            upper=battery.charge_max_mw,
        )
        model.row(
            {discharge[t]: 1.0, mode[t]: -battery.discharge_max_mw},
            upper=0.0,
        )

        # Real-time balance and hybrid imbalance.
        balance: Dict[int, float] = {
            discharge[t]: 1.0,
            charge[t]: -1.0,
            curtail[t]: -1.0,
            shed[t]: 1.0,
            spill[t]: -1.0,
        }
        thermal_min = 0.0
        for g, unit in enumerate(system.thermal_units):
            thermal_min += unit.power_min_mw
            for segment in layout.thermal_segments[g]:
                balance[segment[t]] = 1.0
        model.equality(
            balance,
            system.load_mw[t] - float(pv[t]) - thermal_min,
        )
        model.equality(
            {
                discharge[t]: 1.0,
                charge[t]: -1.0,
                curtail[t]: -1.0,
                imbalance_pos[t]: -1.0,
                imbalance_neg[t]: 1.0,
            },
            stage1.hybrid_injection_mw[t] - float(pv[t]),
        )

        # Reserve source identities and limits.
        model.equality(
            {
                up_pv[t]: 1.0,
                up_charge[t]: 1.0,
                up_discharge[t]: 1.0,
                short_up[t]: 1.0,
            },
            stage1.hybrid_up_reserve_mw[t],
        )
        model.equality(
            {
                down_pv[t]: 1.0,
                down_charge[t]: 1.0,
                down_discharge[t]: 1.0,
                short_down[t]: 1.0,
            },
            stage1.hybrid_down_reserve_mw[t],
        )
        model.row({up_pv[t]: 1.0, curtail[t]: -1.0}, upper=0.0)
        model.row({up_charge[t]: 1.0, charge[t]: -1.0}, upper=0.0)
        model.row(
            {
                charge[t]: 1.0,
                up_charge[t]: -1.0,
                up_mode[t]: battery.charge_max_mw,
            },
            upper=battery.charge_max_mw,
        )
        model.row(
            {
                discharge[t]: 1.0,
                up_discharge[t]: 1.0,
                up_mode[t]: -battery.discharge_max_mw,
            },
            upper=0.0,
        )
        model.row(
            {down_pv[t]: 1.0, curtail[t]: 1.0},
            upper=float(pv[t]),
        )
        model.row(
            {
                charge[t]: 1.0,
                down_charge[t]: 1.0,
                down_mode[t]: battery.charge_max_mw,
            },
            upper=battery.charge_max_mw,
        )
        model.row(
            {down_discharge[t]: 1.0, discharge[t]: -1.0},
            upper=0.0,
        )
        model.row(
            {
                discharge[t]: 1.0,
                down_discharge[t]: -1.0,
                down_mode[t]: -battery.discharge_max_mw,
            },
            upper=0.0,
        )

        # SOC at the end of the start-of-hour call segment and hour.
        up_mid = {
            soc[t]: 1.0,
            charge[t]: eta_c * tau,
            up_charge[t]: -eta_c * tau,
            discharge[t]: -tau / eta_d,
            up_discharge[t]: -tau / eta_d,
        }
        model.row(up_mid, lower=0.0, upper=battery.energy_capacity_mwh)
        up_end = {
            soc[t + 1]: 1.0,
            up_charge[t]: -eta_c * tau,
            up_discharge[t]: -tau / eta_d,
        }
        model.row(up_end, lower=0.0, upper=battery.energy_capacity_mwh)
        down_mid = {
            soc[t]: 1.0,
            charge[t]: eta_c * tau,
            down_charge[t]: eta_c * tau,
            discharge[t]: -tau / eta_d,
            down_discharge[t]: tau / eta_d,
        }
        model.row(down_mid, lower=0.0, upper=battery.energy_capacity_mwh)
        down_end = {
            soc[t + 1]: 1.0,
            down_charge[t]: eta_c * tau,
            down_discharge[t]: tau / eta_d,
        }
        model.row(down_end, lower=0.0, upper=battery.energy_capacity_mwh)

        # Thermal recourse link, reserve headroom, and call ramp.
        for g, unit in enumerate(system.thermal_units):
            above = {segment[t]: 1.0 for segment in layout.thermal_segments[g]}
            p_da = stage1.thermal_dispatch_mw[g][t]
            model.row(
                above,
                lower=p_da - unit.power_min_mw - unit.ramp_mw_per_hour * dt,
                upper=p_da - unit.power_min_mw + unit.ramp_mw_per_hour * dt,
            )
            model.row(
                above,
                upper=unit.power_max_mw
                - unit.power_min_mw
                - stage1.thermal_up_reserve_mw[g][t],
            )
            model.row(
                above,
                lower=stage1.thermal_down_reserve_mw[g][t],
            )

    for t in range(1, h):
        for g, unit in enumerate(system.thermal_units):
            ramp: Dict[int, float] = {}
            for segment in layout.thermal_segments[g]:
                ramp[segment[t]] = 1.0
                ramp[segment[t - 1]] = -1.0
            model.row(
                ramp,
                lower=-unit.ramp_mw_per_hour * dt,
                upper=unit.ramp_mw_per_hour * dt,
            )
    return layout, constant_cost


def _extract_stage2(
    system: V2System,
    layout: _Stage2Layout,
    values: np.ndarray,
    *,
    serialized_primal_cost: float,
    round_modes: bool = True,
) -> ScenarioDecision:
    def vector(indices: Sequence[int]) -> Tuple[float, ...]:
        return tuple(float(values[index]) for index in indices)

    segments = tuple(
        tuple(vector(segment) for segment in unit)
        for unit in layout.thermal_segments
    )
    def modes(indices: Sequence[int]) -> Tuple[float, ...]:
        if round_modes:
            return tuple(float(round(values[index])) for index in indices)
        return vector(indices)

    return ScenarioDecision(
        thermal_segment_mw=segments,
        charge_mw=vector(layout.charge),
        discharge_mw=vector(layout.discharge),
        mode_discharge=modes(layout.mode),
        soc_mwh=vector(layout.soc),
        pv_curtailment_mw=vector(layout.curtail),
        imbalance_positive_mw=vector(layout.imbalance_pos),
        imbalance_negative_mw=vector(layout.imbalance_neg),
        reserve_shortfall_up_mw=vector(layout.short_up),
        reserve_shortfall_down_mw=vector(layout.short_down),
        load_shedding_mw=vector(layout.shed),
        emergency_spill_mw=vector(layout.spill),
        up_pv_release_mw=vector(layout.up_pv),
        up_charge_reduction_mw=vector(layout.up_charge),
        up_discharge_increase_mw=vector(layout.up_discharge),
        down_pv_curtailment_mw=vector(layout.down_pv),
        down_charge_increase_mw=vector(layout.down_charge),
        down_discharge_reduction_mw=vector(layout.down_discharge),
        up_mode_discharge=modes(layout.up_mode),
        down_mode_discharge=modes(layout.down_mode),
        serialized_primal_cost=serialized_primal_cost,
    )


def thermal_cost(
    unit: ThermalUnit,
    segment_dispatch_mw: Sequence[Sequence[float]],
    *,
    interval_hours: float = 1.0,
) -> float:
    """Independently evaluate the registered piecewise-linear unit cost."""

    horizon = len(segment_dispatch_mw[0]) if segment_dispatch_mw else 0
    total = horizon * unit.power_min_mw * unit.segment_costs_per_mwh[0]
    for cost, segment in zip(unit.segment_costs_per_mwh, segment_dispatch_mw):
        total += cost * sum(segment)
    return total * interval_hours


def _optional_float(value) -> float | None:
    if value is None:
        return None
    try:
        converted = float(value)
    except (TypeError, ValueError):
        return None
    return converted if math.isfinite(converted) else None


def _optional_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _stage1_optional_vector(
    values: Sequence[float],
    horizon: int,
) -> Tuple[float, ...]:
    if len(values) == 0:
        return (0.0,) * horizon
    if len(values) != horizon:
        raise ValueError("stage-1 slack vector has the wrong horizon")
    return tuple(float(value) for value in values)
