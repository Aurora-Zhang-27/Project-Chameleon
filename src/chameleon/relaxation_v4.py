"""Diagnostics for the MFE v4 charge/discharge relaxation gate."""

from __future__ import annotations

from dataclasses import dataclass, replace
import time
from typing import Sequence

from .truth_model import (
    ExtensiveFormResult,
    ScenarioDecision,
    SolverConfig,
    V2System,
    solve_extensive_form,
)


@dataclass(frozen=True)
class SimultaneousOperationReport:
    max_base_simultaneous_mw: float
    max_up_branch_simultaneous_mw: float
    max_down_branch_simultaneous_mw: float
    max_mode_fractionality: float

    @property
    def max_simultaneous_mw(self) -> float:
        return max(
            self.max_base_simultaneous_mw,
            self.max_up_branch_simultaneous_mw,
            self.max_down_branch_simultaneous_mw,
        )


@dataclass(frozen=True)
class AdaptiveIteration:
    iteration: int
    binary_count: int
    solve_seconds: float
    objective: float | None
    max_simultaneous_mw: float
    added_base_hours: tuple[int, ...]
    added_up_hours: tuple[int, ...]
    added_down_hours: tuple[int, ...]


@dataclass(frozen=True)
class AdaptiveRelaxationResult:
    result: ExtensiveFormResult
    certified_contract_exact: bool
    iterations: tuple[AdaptiveIteration, ...]
    integer_base_hours: tuple[int, ...]
    integer_up_hours: tuple[int, ...]
    integer_down_hours: tuple[int, ...]


def diagnose_simultaneous_operation(
    decision: ScenarioDecision,
) -> SimultaneousOperationReport:
    """Measure physical cycling and fractional mode use in all three branches."""

    base = []
    up = []
    down = []
    for t, (charge, discharge) in enumerate(
        zip(decision.charge_mw, decision.discharge_mw)
    ):
        base.append(min(max(0.0, charge), max(0.0, discharge)))
        up_charge = charge - decision.up_charge_reduction_mw[t]
        up_discharge = discharge + decision.up_discharge_increase_mw[t]
        down_charge = charge + decision.down_charge_increase_mw[t]
        down_discharge = discharge - decision.down_discharge_reduction_mw[t]
        up.append(min(max(0.0, up_charge), max(0.0, up_discharge)))
        down.append(min(max(0.0, down_charge), max(0.0, down_discharge)))

    modes = (
        decision.mode_discharge
        + decision.up_mode_discharge
        + decision.down_mode_discharge
    )
    fractionality = [
        min(abs(value), abs(1.0 - value))
        for value in modes
    ]
    return SimultaneousOperationReport(
        max_base_simultaneous_mw=max(base, default=0.0),
        max_up_branch_simultaneous_mw=max(up, default=0.0),
        max_down_branch_simultaneous_mw=max(down, default=0.0),
        max_mode_fractionality=max(fractionality, default=0.0),
    )


def recover_modes_if_complementary(
    decision: ScenarioDecision,
    *,
    tolerance: float = 1e-6,
) -> ScenarioDecision | None:
    """Recover binary modes when relaxed power actions are already physical.

    This function intentionally changes only the three mode vectors. It does
    not repair simultaneous charge/discharge, SOC, reserve allocation, or any
    stage-1 field. Returning ``None`` therefore certifies that this cheapest
    contract-preserving recovery is unavailable.
    """

    def mode(charge: float, discharge: float) -> float | None:
        if charge > tolerance and discharge > tolerance:
            return None
        return 1.0 if discharge > tolerance else 0.0

    base_modes = []
    up_modes = []
    down_modes = []
    for t, (charge, discharge) in enumerate(
        zip(decision.charge_mw, decision.discharge_mw)
    ):
        base_mode = mode(charge, discharge)
        up_mode = mode(
            charge - decision.up_charge_reduction_mw[t],
            discharge + decision.up_discharge_increase_mw[t],
        )
        down_mode = mode(
            charge + decision.down_charge_increase_mw[t],
            discharge - decision.down_discharge_reduction_mw[t],
        )
        if base_mode is None or up_mode is None or down_mode is None:
            return None
        base_modes.append(base_mode)
        up_modes.append(up_mode)
        down_modes.append(down_mode)

    return replace(
        decision,
        mode_discharge=tuple(base_modes),
        up_mode_discharge=tuple(up_modes),
        down_mode_discharge=tuple(down_modes),
    )


def solve_adaptive_extensive_form(
    system: V2System,
    pv_scenarios_mw: Sequence[Sequence[float]],
    contract: str,
    *,
    c0_parameters=None,
    c1_band=None,
    force_hybrid_reserve_zero: bool = False,
    config: SolverConfig = SolverConfig(),
    simultaneous_tolerance_mw: float = 1e-6,
    max_iterations: int = 73,
    total_time_limit_seconds: float | None = None,
) -> AdaptiveRelaxationResult:
    """Add integrality only at branch-hours exhibiting simultaneous operation.

    Hour masks are shared across scenarios. Once an optimal partial relaxation
    has no simultaneous charge/discharge, mode-only recovery makes that
    solution feasible for the full MILP at the same objective. Since the
    partial problem is a relaxation of the full MILP, this is a sandwich
    certificate of contract exactness within the configured solver tolerance.
    """

    base_hours = set(config.integer_base_mode_hours)
    up_hours = set(config.integer_up_activation_hours)
    down_hours = set(config.integer_down_activation_hours)
    history: list[AdaptiveIteration] = []
    latest: ExtensiveFormResult | None = None
    started = time.perf_counter()

    for iteration in range(max_iterations):
        elapsed = time.perf_counter() - started
        if total_time_limit_seconds is not None:
            remaining = total_time_limit_seconds - elapsed
            if remaining <= 0.0:
                break
            iteration_limit = min(config.time_limit_seconds, remaining)
        else:
            iteration_limit = config.time_limit_seconds
        iteration_config = replace(
            config,
            time_limit_seconds=iteration_limit,
            relax_base_modes=True,
            relax_up_activation_modes=True,
            relax_down_activation_modes=True,
            integer_base_mode_hours=tuple(sorted(base_hours)),
            integer_up_activation_hours=tuple(sorted(up_hours)),
            integer_down_activation_hours=tuple(sorted(down_hours)),
        )
        latest = solve_extensive_form(
            system,
            pv_scenarios_mw,
            contract,
            c0_parameters=c0_parameters,
            c1_band=c1_band,
            force_hybrid_reserve_zero=force_hybrid_reserve_zero,
            config=iteration_config,
        )
        if (
            latest.stage1 is None
            or not latest.scenarios
            or latest.diagnostics.solver_unresolved
        ):
            return AdaptiveRelaxationResult(
                result=latest,
                certified_contract_exact=False,
                iterations=tuple(history),
                integer_base_hours=tuple(sorted(base_hours)),
                integer_up_hours=tuple(sorted(up_hours)),
                integer_down_hours=tuple(sorted(down_hours)),
            )

        found_base: set[int] = set()
        found_up: set[int] = set()
        found_down: set[int] = set()
        max_simultaneous = 0.0
        for decision in latest.scenarios:
            for t, (charge, discharge) in enumerate(
                zip(decision.charge_mw, decision.discharge_mw)
            ):
                branch_values = (
                    (
                        "base",
                        min(max(0.0, charge), max(0.0, discharge)),
                    ),
                    (
                        "up",
                        min(
                            max(
                                0.0,
                                charge
                                - decision.up_charge_reduction_mw[t],
                            ),
                            max(
                                0.0,
                                discharge
                                + decision.up_discharge_increase_mw[t],
                            ),
                        ),
                    ),
                    (
                        "down",
                        min(
                            max(
                                0.0,
                                charge
                                + decision.down_charge_increase_mw[t],
                            ),
                            max(
                                0.0,
                                discharge
                                - decision.down_discharge_reduction_mw[t],
                            ),
                        ),
                    ),
                )
                for branch, value in branch_values:
                    max_simultaneous = max(max_simultaneous, value)
                    if value <= simultaneous_tolerance_mw:
                        continue
                    if branch == "base":
                        found_base.add(t)
                    elif branch == "up":
                        found_up.add(t)
                    else:
                        found_down.add(t)

        add_base = found_base - base_hours
        add_up = found_up - up_hours
        add_down = found_down - down_hours
        history.append(
            AdaptiveIteration(
                iteration=iteration,
                binary_count=latest.diagnostics.binary_count,
                solve_seconds=latest.diagnostics.solve_seconds,
                objective=latest.objective,
                max_simultaneous_mw=max_simultaneous,
                added_base_hours=tuple(sorted(add_base)),
                added_up_hours=tuple(sorted(add_up)),
                added_down_hours=tuple(sorted(add_down)),
            )
        )

        if not add_base and not add_up and not add_down:
            recovered = tuple(
                recover_modes_if_complementary(
                    decision,
                    tolerance=simultaneous_tolerance_mw,
                )
                for decision in latest.scenarios
            )
            if any(decision is None for decision in recovered):
                break
            recovered_result = replace(
                latest,
                scenarios=tuple(
                    decision
                    for decision in recovered
                    if decision is not None
                ),
            )
            return AdaptiveRelaxationResult(
                result=recovered_result,
                certified_contract_exact=True,
                iterations=tuple(history),
                integer_base_hours=tuple(sorted(base_hours)),
                integer_up_hours=tuple(sorted(up_hours)),
                integer_down_hours=tuple(sorted(down_hours)),
            )

        base_hours.update(add_base)
        up_hours.update(add_up)
        down_hours.update(add_down)

    if latest is None:
        latest = solve_extensive_form(
            system,
            pv_scenarios_mw,
            contract,
            c0_parameters=c0_parameters,
            c1_band=c1_band,
            force_hybrid_reserve_zero=force_hybrid_reserve_zero,
            config=replace(config, time_limit_seconds=0.001),
        )
    return AdaptiveRelaxationResult(
        result=latest,
        certified_contract_exact=False,
        iterations=tuple(history),
        integer_base_hours=tuple(sorted(base_hours)),
        integer_up_hours=tuple(sorted(up_hours)),
        integer_down_hours=tuple(sorted(down_hours)),
    )
