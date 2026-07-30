"""Reduced-semantics MFE pilot and frontier primitives.

The model is deliberately the stochastic extension of the proved Phase-I
contract: common hybrid schedule and reserve awards, scenario-specific
must-take-PV translation, lossless discharge-only storage, and isolated
upward reserve.  It contains no charging, curtailment, or mode variables.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, Sequence, Tuple

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

from .contracts import ContractKind
from .mfe_harness import DeterministicMFECase


@dataclass(frozen=True)
class StaticContractParameters:
    power_cap_mw: float
    reserve_cap_mw: float
    ramp_cap_mw_per_hour: float


@dataclass(frozen=True)
class MFECell:
    duration_hours: int
    initial_soc_fraction: float
    pv_shortfall_sigma: float
    reserve_fraction: float

    @property
    def energy_capacity_mwh(self) -> float:
        return 50.0 * self.duration_hours

    @property
    def initial_energy_mwh(self) -> float:
        return self.initial_soc_fraction * self.energy_capacity_mwh


@dataclass(frozen=True)
class FrontierSchedule:
    contract: str
    objective: float
    hybrid_injection_mw: Tuple[float, ...]
    hybrid_upward_reserve_mw: Tuple[float, ...]
    thermal_dispatch_mw: Tuple[Tuple[float, ...], ...]
    thermal_upward_reserve_mw: Tuple[Tuple[float, ...], ...]
    solver_message: str


@dataclass(frozen=True)
class ScenarioReplaySummary:
    scenario_feasible: Tuple[bool, ...]
    base_violation_mwh: Tuple[float, ...]
    reserve_shortfall_mwh: Tuple[float, ...]
    sequential_shortfall_mwh: Tuple[float, ...]

    @property
    def non_delivery_rate(self) -> float:
        if not self.scenario_feasible:
            return 0.0
        return 1.0 - sum(self.scenario_feasible) / len(self.scenario_feasible)


@dataclass(frozen=True)
class _Layout:
    horizon: int
    segment_counts: Tuple[int, ...]
    scenario_count: int
    include_soc: bool

    @property
    def hybrid(self) -> slice:
        return slice(0, self.horizon)

    @property
    def hybrid_reserve(self) -> slice:
        return slice(self.horizon, 2 * self.horizon)

    @property
    def segment_start(self) -> int:
        return 2 * self.horizon

    @property
    def total_segments(self) -> int:
        return sum(self.segment_counts)

    @property
    def thermal_reserve_start(self) -> int:
        return self.segment_start + self.total_segments * self.horizon

    @property
    def soc_start(self) -> int:
        return self.thermal_reserve_start + len(self.segment_counts) * self.horizon

    @property
    def size(self) -> int:
        soc_count = self.scenario_count * (self.horizon + 1) if self.include_soc else 0
        return self.soc_start + soc_count

    def segment(self, unit: int, segment: int, period: int) -> int:
        flat = sum(self.segment_counts[:unit]) + segment
        return self.segment_start + flat * self.horizon + period

    def thermal_reserve(self, unit: int, period: int) -> int:
        return self.thermal_reserve_start + unit * self.horizon + period

    def soc(self, scenario: int, period: int) -> int:
        if not self.include_soc:
            raise ValueError("SOC variables are absent")
        return self.soc_start + scenario * (self.horizon + 1) + period


class _Rows:
    def __init__(self, width: int) -> None:
        self.width = width
        self.row_indices: list[int] = []
        self.column_indices: list[int] = []
        self.values: list[float] = []
        self.rhs: list[float] = []

    def add(self, coefficients: Mapping[int, float], rhs: float) -> None:
        row = len(self.rhs)
        for column, value in coefficients.items():
            if abs(value) > 0:
                self.row_indices.append(row)
                self.column_indices.append(column)
                self.values.append(value)
        self.rhs.append(rhs)

    def matrix(self) -> coo_matrix:
        return coo_matrix(
            (self.values, (self.row_indices, self.column_indices)),
            shape=(len(self.rhs), self.width),
        )


def generate_pv_shortfall_scenarios(
    forecast_pv_mw: Sequence[float],
    sigma: float,
    count: int,
    seed: int,
) -> np.ndarray:
    """Generate the frozen correlated one-sided shortfall paths."""

    if sigma not in {0.03, 0.08, 0.15}:
        raise ValueError("sigma must be one of the three frozen levels")
    if count < 1:
        raise ValueError("scenario count must be positive")
    forecast = np.asarray(forecast_pv_mw, dtype=float)
    generator = np.random.default_rng(seed)
    innovations = generator.standard_normal((count, len(forecast)))
    latent = np.empty_like(innovations)
    latent[:, 0] = innovations[:, 0]
    scale = np.sqrt(1.0 - 0.8**2)
    for period in range(1, len(forecast)):
        latent[:, period] = (
            0.8 * latent[:, period - 1] + scale * innovations[:, period]
        )
    fractional_shortfall = np.minimum(0.25, sigma * np.abs(latent))
    return forecast[None, :] * (1.0 - fractional_shortfall)


def solve_frontier_schedule(
    base_case: DeterministicMFECase,
    cell: MFECell,
    pv_scenarios_mw: np.ndarray,
    contract: ContractKind | str,
    *,
    c0_parameters: StaticContractParameters | None = None,
    force_zero_hybrid_reserve: bool = False,
) -> FrontierSchedule:
    """Solve one common schedule against a finite scenario set."""

    contract_name = (
        contract.value if isinstance(contract, ContractKind) else str(contract)
    )
    supported = {
        "c0_market",
        ContractKind.C1_PREFIX.value,
        ContractKind.C_FULL_DET.value,
    }
    if contract_name not in supported:
        raise ValueError(f"unsupported frontier contract: {contract_name}")
    if contract_name == "c0_market" and c0_parameters is None:
        raise ValueError("c0_market requires static parameters")

    scenarios = np.asarray(pv_scenarios_mw, dtype=float)
    horizon = base_case.battery.horizon
    if scenarios.ndim != 2 or scenarios.shape[1] != horizon:
        raise ValueError("PV scenarios must have shape (n, horizon)")

    include_soc = contract_name == ContractKind.C_FULL_DET.value
    layout = _Layout(
        horizon=horizon,
        segment_counts=tuple(
            len(unit.segment_widths_mw) for unit in base_case.thermal_units
        ),
        scenario_count=len(scenarios),
        include_soc=include_soc,
    )
    objective = np.zeros(layout.size)
    bounds: list[Tuple[float | None, float | None]] = [
        (0.0, None)
    ] * layout.size
    bounds[layout.hybrid] = [(0.0, None)] * horizon
    reserve_bound = 0.0 if force_zero_hybrid_reserve else 50.0
    bounds[layout.hybrid_reserve] = [(0.0, reserve_bound)] * horizon

    for unit_index, unit in enumerate(base_case.thermal_units):
        for segment_index, (width, cost) in enumerate(
            zip(unit.segment_widths_mw, unit.segment_costs_per_mwh)
        ):
            for period in range(horizon):
                index = layout.segment(unit_index, segment_index, period)
                objective[index] = cost
                bounds[index] = (0.0, width)
        for period in range(horizon):
            index = layout.thermal_reserve(unit_index, period)
            objective[index] = unit.reserve_cost_per_mw
            bounds[index] = (0.0, None)

    if include_soc:
        for scenario in range(len(scenarios)):
            for period in range(horizon + 1):
                bounds[layout.soc(scenario, period)] = (
                    0.0,
                    cell.energy_capacity_mwh,
                )

    equalities = _Rows(layout.size)
    inequalities = _Rows(layout.size)
    thermal_minimum = sum(unit.power_min_mw for unit in base_case.thermal_units)

    for period in range(horizon):
        balance: Dict[int, float] = {layout.hybrid.start + period: 1.0}
        for unit_index, unit in enumerate(base_case.thermal_units):
            for segment_index in range(len(unit.segment_widths_mw)):
                balance[layout.segment(unit_index, segment_index, period)] = 1.0
        equalities.add(balance, base_case.load_mw[period] - thermal_minimum)

        reserve: Dict[int, float] = {
            layout.hybrid_reserve.start + period: -1.0
        }
        for unit_index in range(len(base_case.thermal_units)):
            reserve[layout.thermal_reserve(unit_index, period)] = -1.0
        inequalities.add(
            reserve, -cell.reserve_fraction * base_case.load_mw[period]
        )

        for unit_index, unit in enumerate(base_case.thermal_units):
            headroom: Dict[int, float] = {
                layout.thermal_reserve(unit_index, period): 1.0
            }
            for segment_index in range(len(unit.segment_widths_mw)):
                headroom[layout.segment(unit_index, segment_index, period)] = 1.0
            inequalities.add(headroom, unit.power_max_mw - unit.power_min_mw)

    for period in range(1, horizon):
        for unit_index, unit in enumerate(base_case.thermal_units):
            ramp: Dict[int, float] = {}
            for segment_index in range(len(unit.segment_widths_mw)):
                ramp[layout.segment(unit_index, segment_index, period)] = 1.0
                ramp[layout.segment(unit_index, segment_index, period - 1)] = -1.0
            inequalities.add(ramp, unit.ramp_mw_per_hour)
            inequalities.add(
                {index: -value for index, value in ramp.items()},
                unit.ramp_mw_per_hour,
            )

    dt = 1.0
    tau = 0.5
    for scenario_index, pv in enumerate(scenarios):
        for period in range(horizon):
            hybrid_index = layout.hybrid.start + period
            reserve_index = layout.hybrid_reserve.start + period

            # b_t = h_t - w_t must be nonnegative.
            inequalities.add({hybrid_index: -1.0}, -float(pv[period]))
            # b_t + r_t <= 50 MW.
            inequalities.add(
                {hybrid_index: 1.0, reserve_index: 1.0},
                float(pv[period]) + 50.0,
            )

            if contract_name == "c0_market":
                assert c0_parameters is not None
                inequalities.add(
                    {hybrid_index: 1.0},
                    float(pv[period]) + c0_parameters.power_cap_mw,
                )
                inequalities.add(
                    {reserve_index: 1.0},
                    c0_parameters.reserve_cap_mw,
                )
                if period > 0:
                    current_minus_previous = {
                        hybrid_index: 1.0,
                        layout.hybrid.start + period - 1: -1.0,
                    }
                    pv_difference = float(pv[period] - pv[period - 1])
                    inequalities.add(
                        current_minus_previous,
                        c0_parameters.ramp_cap_mw_per_hour + pv_difference,
                    )
                    inequalities.add(
                        {
                            index: -value
                            for index, value in current_minus_previous.items()
                        },
                        c0_parameters.ramp_cap_mw_per_hour - pv_difference,
                    )
            elif contract_name == ContractKind.C1_PREFIX.value:
                prefix = {
                    layout.hybrid.start + prior: dt
                    for prior in range(period + 1)
                }
                prefix[reserve_index] = tau
                pv_prefix = float(np.sum(pv[: period + 1]))
                inequalities.add(
                    prefix, cell.initial_energy_mwh + pv_prefix
                )

        if include_soc:
            equalities.add(
                {layout.soc(scenario_index, 0): 1.0},
                cell.initial_energy_mwh,
            )
            for period in range(horizon):
                equalities.add(
                    {
                        layout.soc(scenario_index, period + 1): 1.0,
                        layout.soc(scenario_index, period): -1.0,
                        layout.hybrid.start + period: dt,
                    },
                    float(pv[period]) * dt,
                )
                inequalities.add(
                    {
                        layout.hybrid_reserve.start + period: tau,
                        layout.soc(scenario_index, period + 1): -1.0,
                    },
                    0.0,
                )

    result = linprog(
        objective,
        A_ub=inequalities.matrix().tocsr(),
        b_ub=np.asarray(inequalities.rhs),
        A_eq=equalities.matrix().tocsr(),
        b_eq=np.asarray(equalities.rhs),
        bounds=bounds,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"frontier schedule solve failed: {result.message}")

    values = result.x
    thermal_dispatch: list[Tuple[float, ...]] = []
    thermal_reserve: list[Tuple[float, ...]] = []
    for unit_index, unit in enumerate(base_case.thermal_units):
        dispatch = []
        reserve = []
        for period in range(horizon):
            dispatch.append(
                unit.power_min_mw
                + sum(
                    values[layout.segment(unit_index, segment_index, period)]
                    for segment_index in range(len(unit.segment_widths_mw))
                )
            )
            reserve.append(values[layout.thermal_reserve(unit_index, period)])
        thermal_dispatch.append(tuple(float(value) for value in dispatch))
        thermal_reserve.append(tuple(float(value) for value in reserve))

    return FrontierSchedule(
        contract=contract_name,
        objective=float(result.fun),
        hybrid_injection_mw=tuple(float(value) for value in values[layout.hybrid]),
        hybrid_upward_reserve_mw=tuple(
            float(value) for value in values[layout.hybrid_reserve]
        ),
        thermal_dispatch_mw=tuple(thermal_dispatch),
        thermal_upward_reserve_mw=tuple(thermal_reserve),
        solver_message=result.message,
    )


def replay_frontier_schedule(
    schedule: FrontierSchedule,
    cell: MFECell,
    pv_scenarios_mw: np.ndarray,
    *,
    tolerance: float = 1e-7,
) -> ScenarioReplaySummary:
    """Independently replay held-out scenarios and the fixed two-call stress."""

    scenarios = np.asarray(pv_scenarios_mw, dtype=float)
    base_violations: list[float] = []
    reserve_shortfalls: list[float] = []
    sequential_shortfalls: list[float] = []
    feasible: list[bool] = []
    tau = 0.5

    for pv in scenarios:
        energy = cell.initial_energy_mwh
        total_base_violation = 0.0
        total_reserve_shortfall = 0.0
        base_energies = []
        battery_power = []

        for hybrid, reserve, pv_t in zip(
            schedule.hybrid_injection_mw,
            schedule.hybrid_upward_reserve_mw,
            pv,
        ):
            discharge = hybrid - float(pv_t)
            battery_power.append(discharge)
            negative_violation = max(0.0, -discharge)
            power_violation = max(0.0, discharge - 50.0)
            available = max(0.0, energy)
            energy_violation = max(0.0, discharge - available)
            total_base_violation += (
                negative_violation + power_violation + energy_violation
            )
            energy = max(0.0, energy - max(0.0, discharge))
            base_energies.append(energy)

            power_headroom = max(0.0, 50.0 - max(0.0, discharge))
            energy_headroom = max(0.0, energy / tau)
            deliverable = min(reserve, power_headroom, energy_headroom)
            total_reserve_shortfall += max(0.0, reserve - deliverable) * tau

        sequential_energy = cell.initial_energy_mwh
        sequential_shortfall = 0.0
        for period, discharge in enumerate(battery_power):
            sequential_energy = max(
                0.0, sequential_energy - max(0.0, discharge)
            )
            if period in {17, 18}:
                reserve = schedule.hybrid_upward_reserve_mw[period]
                power_headroom = max(0.0, 50.0 - max(0.0, discharge))
                deliverable = min(
                    reserve,
                    power_headroom,
                    max(0.0, sequential_energy / tau),
                )
                shortfall = max(0.0, reserve - deliverable)
                sequential_shortfall += shortfall * tau
                sequential_energy = max(
                    0.0, sequential_energy - deliverable * tau
                )

        base_violations.append(total_base_violation)
        reserve_shortfalls.append(total_reserve_shortfall)
        sequential_shortfalls.append(sequential_shortfall)
        feasible.append(
            total_base_violation <= tolerance
            and total_reserve_shortfall <= tolerance
        )

    return ScenarioReplaySummary(
        scenario_feasible=tuple(feasible),
        base_violation_mwh=tuple(base_violations),
        reserve_shortfall_mwh=tuple(reserve_shortfalls),
        sequential_shortfall_mwh=tuple(sequential_shortfalls),
    )


def static_parameter_grid() -> Tuple[StaticContractParameters, ...]:
    values = tuple(float(value) for value in range(0, 51, 5))
    ramps = tuple(float(value) for value in range(5, 51, 5))
    return tuple(
        StaticContractParameters(power, reserve, ramp)
        for power in values
        for reserve in values
        if power + reserve <= 50.0
        for ramp in ramps
    )

