"""Independent physical and cost replay for MFE v2.

This module intentionally does not import or inspect MILP matrices, result
objects, duals, bounds, or solver objectives.  It consumes only immutable
source data plus serialized stage-1/stage-2 primal decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence, Tuple

from .truth_model import (
    ScenarioDecision,
    Stage1Decision,
    TOLERANCE,
    V2System,
    thermal_cost,
)


@dataclass(frozen=True)
class ActivationReplay:
    deliverable_up_mw: Tuple[float, ...]
    shortfall_up_mw: Tuple[float, ...]
    deliverable_down_mw: Tuple[float, ...]
    shortfall_down_mw: Tuple[float, ...]
    up_mid_soc_mwh: Tuple[float, ...]
    up_end_soc_mwh: Tuple[float, ...]
    down_mid_soc_mwh: Tuple[float, ...]
    down_end_soc_mwh: Tuple[float, ...]


@dataclass(frozen=True)
class SequentialReplay:
    actual_soc_mwh: Tuple[float, ...]
    call_mid_soc_mwh: Tuple[float, float]
    delivered_up_mw: Tuple[float, float]
    shortfall_up_mw: Tuple[float, float]
    physical_violation_mwh: float


@dataclass(frozen=True)
class V2ReplayResult:
    reconstructed_soc_mwh: Tuple[float, ...]
    thermal_dispatch_mw: Tuple[Tuple[float, ...], ...]
    hybrid_injection_mw: Tuple[float, ...]
    system_balance_residual_mw: Tuple[float, ...]
    imbalance_identity_residual_mw: Tuple[float, ...]
    soc_identity_residual_mwh: Tuple[float, ...]
    physical_violations: Tuple[str, ...]
    activation: ActivationReplay
    sequential: SequentialReplay
    cost_components: Tuple[Tuple[str, float], ...]
    replay_cost: float
    serialized_primal_cost: float
    cost_residual: float
    cost_reconciled: bool

    @property
    def physically_valid(self) -> bool:
        return not self.physical_violations


def replay_v2(
    system: V2System,
    stage1: Stage1Decision,
    decision: ScenarioDecision,
    realized_pv_mw: Sequence[float],
    *,
    tolerance: float = TOLERANCE,
) -> V2ReplayResult:
    """Replay one frozen scenario decision under the registered semantics."""

    pv = tuple(float(value) for value in realized_pv_mw)
    if len(pv) != system.horizon:
        raise ValueError("realized PV path has the wrong horizon")
    h = system.horizon
    b = system.battery
    dt = b.interval_hours
    tau = b.reserve_duration_hours
    eta_c = b.charge_efficiency
    eta_d = b.discharge_efficiency
    violations: list[str] = []
    da_shed = (
        decision_zeros(h)
        if len(stage1.day_ahead_load_shedding_mw) == 0
        else stage1.day_ahead_load_shedding_mw
    )
    da_spill = (
        decision_zeros(h)
        if len(stage1.day_ahead_spill_mw) == 0
        else stage1.day_ahead_spill_mw
    )
    if len(da_shed) != h or len(da_spill) != h:
        raise ValueError("stage-1 slack vector has the wrong horizon")

    thermal = decision.thermal_dispatch(system)
    hybrid = tuple(
        pv[t]
        - decision.pv_curtailment_mw[t]
        + decision.discharge_mw[t]
        - decision.charge_mw[t]
        for t in range(h)
    )

    reconstructed = [b.initial_energy_mwh]
    soc_residual = []
    balance_residual = []
    imbalance_residual = []

    for t in range(h):
        c = decision.charge_mw[t]
        d = decision.discharge_mw[t]
        z = decision.mode_discharge[t]
        expected_next = reconstructed[-1] + eta_c * c * dt - d * dt / eta_d
        reconstructed.append(expected_next)
        soc_residual.append(expected_next - decision.soc_mwh[t + 1])
        balance_residual.append(
            sum(row[t] for row in thermal)
            + hybrid[t]
            + decision.load_shedding_mw[t]
            - decision.emergency_spill_mw[t]
            - system.load_mw[t]
        )
        imbalance_residual.append(
            hybrid[t]
            - stage1.hybrid_injection_mw[t]
            - decision.imbalance_positive_mw[t]
            + decision.imbalance_negative_mw[t]
        )
        da_balance = (
            sum(row[t] for row in stage1.thermal_dispatch_mw)
            + stage1.hybrid_injection_mw[t]
            + da_shed[t]
            - da_spill[t]
            - system.load_mw[t]
        )
        if abs(da_balance) > tolerance:
            violations.append(f"stage-1 balance mismatch at hour {t + 1}")
        if da_shed[t] < -tolerance or da_spill[t] < -tolerance:
            violations.append(f"negative stage-1 slack at hour {t + 1}")

        _bound(violations, f"charge[{t + 1}]", c, 0.0, b.charge_max_mw, tolerance)
        _bound(
            violations,
            f"discharge[{t + 1}]",
            d,
            0.0,
            b.discharge_max_mw,
            tolerance,
        )
        if z not in {0, 1}:
            violations.append(f"mode[{t + 1}] is not binary")
        if c > tolerance and d > tolerance:
            violations.append(f"simultaneous charge/discharge at hour {t + 1}")
        if z == 1 and c > tolerance:
            violations.append(f"charge violates discharge mode at hour {t + 1}")
        if z == 0 and d > tolerance:
            violations.append(f"discharge violates charge mode at hour {t + 1}")
        _bound(
            violations,
            f"curtailment[{t + 1}]",
            decision.pv_curtailment_mw[t],
            0.0,
            pv[t],
            tolerance,
        )
        _bound(
            violations,
            f"SOC[{t + 2}]",
            expected_next,
            0.0,
            b.energy_capacity_mwh,
            tolerance,
        )
        if abs(soc_residual[-1]) > tolerance:
            violations.append(f"serialized SOC mismatch at hour {t + 1}")
        if abs(balance_residual[-1]) > tolerance:
            violations.append(f"system balance mismatch at hour {t + 1}")
        if abs(imbalance_residual[-1]) > tolerance:
            violations.append(f"imbalance identity mismatch at hour {t + 1}")

        for name, value in (
            ("imbalance_positive", decision.imbalance_positive_mw[t]),
            ("imbalance_negative", decision.imbalance_negative_mw[t]),
            ("reserve_shortfall_up", decision.reserve_shortfall_up_mw[t]),
            ("reserve_shortfall_down", decision.reserve_shortfall_down_mw[t]),
            ("load_shedding", decision.load_shedding_mw[t]),
            ("emergency_spill", decision.emergency_spill_mw[t]),
        ):
            if value < -tolerance:
                violations.append(f"negative {name} at hour {t + 1}")

        for g, unit in enumerate(system.thermal_units):
            value = thermal[g][t]
            _bound(
                violations,
                f"thermal[{g},{t + 1}]",
                value,
                unit.power_min_mw,
                unit.power_max_mw,
                tolerance,
            )
            if value + stage1.thermal_up_reserve_mw[g][t] > (
                unit.power_max_mw + tolerance
            ):
                violations.append(f"thermal upward headroom at unit {g}, hour {t + 1}")
            if value - stage1.thermal_down_reserve_mw[g][t] < (
                unit.power_min_mw - tolerance
            ):
                violations.append(
                    f"thermal downward footroom at unit {g}, hour {t + 1}"
                )
            if abs(value - stage1.thermal_dispatch_mw[g][t]) > (
                unit.ramp_mw_per_hour * dt + tolerance
            ):
                violations.append(f"thermal redispatch link at unit {g}, hour {t + 1}")
            if t and abs(value - thermal[g][t - 1]) > (
                unit.ramp_mw_per_hour * dt + tolerance
            ):
                violations.append(f"thermal RT ramp at unit {g}, hour {t + 1}")

    if abs(decision.soc_mwh[0] - b.initial_energy_mwh) > tolerance:
        violations.append("serialized initial SOC mismatch")
    if reconstructed[-1] < b.terminal_energy_mwh - tolerance:
        violations.append("terminal SOC requirement")

    activation = _replay_isolated(
        system,
        stage1,
        decision,
        reconstructed,
        tolerance,
        violations,
    )
    sequential = _replay_sequential(
        system,
        stage1,
        decision,
        tolerance,
    )

    components = _cost_components(system, stage1, decision)
    replay_cost = sum(value for _, value in components)
    residual = replay_cost - decision.serialized_primal_cost
    cost_tolerance = tolerance * max(
        1.0, abs(replay_cost), abs(decision.serialized_primal_cost)
    )
    return V2ReplayResult(
        reconstructed_soc_mwh=tuple(reconstructed),
        thermal_dispatch_mw=thermal,
        hybrid_injection_mw=hybrid,
        system_balance_residual_mw=tuple(balance_residual),
        imbalance_identity_residual_mw=tuple(imbalance_residual),
        soc_identity_residual_mwh=tuple(soc_residual),
        physical_violations=tuple(violations),
        activation=activation,
        sequential=sequential,
        cost_components=tuple(components),
        replay_cost=replay_cost,
        serialized_primal_cost=decision.serialized_primal_cost,
        cost_residual=residual,
        cost_reconciled=abs(residual) <= cost_tolerance,
    )


def _replay_isolated(
    system: V2System,
    stage1: Stage1Decision,
    decision: ScenarioDecision,
    base_soc: Sequence[float],
    tolerance: float,
    violations: list[str],
) -> ActivationReplay:
    b = system.battery
    tau = b.reserve_duration_hours
    eta_c = b.charge_efficiency
    eta_d = b.discharge_efficiency
    up_delivered = []
    up_short = []
    down_delivered = []
    down_short = []
    up_mid = []
    up_end = []
    down_mid = []
    down_end = []
    for t in range(system.horizon):
        c = decision.charge_mw[t]
        d = decision.discharge_mw[t]
        up_mode = decision.up_mode_discharge[t]
        down_mode = decision.down_mode_discharge[t]
        up_charge = c - decision.up_charge_reduction_mw[t]
        up_discharge = d + decision.up_discharge_increase_mw[t]
        down_charge = c + decision.down_charge_increase_mw[t]
        down_discharge = d - decision.down_discharge_reduction_mw[t]
        up = (
            decision.up_pv_release_mw[t]
            + decision.up_charge_reduction_mw[t]
            + decision.up_discharge_increase_mw[t]
        )
        down = (
            decision.down_pv_curtailment_mw[t]
            + decision.down_charge_increase_mw[t]
            + decision.down_discharge_reduction_mw[t]
        )
        up_delivered.append(up)
        down_delivered.append(down)
        up_short.append(max(0.0, stage1.hybrid_up_reserve_mw[t] - up))
        down_short.append(max(0.0, stage1.hybrid_down_reserve_mw[t] - down))
        up_mid_t = base_soc[t] + tau * (
            eta_c * (c - decision.up_charge_reduction_mw[t])
            - (d + decision.up_discharge_increase_mw[t]) / eta_d
        )
        up_end_t = up_mid_t + (b.interval_hours - tau) * (
            eta_c * c - d / eta_d
        )
        down_mid_t = base_soc[t] + tau * (
            eta_c * (c + decision.down_charge_increase_mw[t])
            - (d - decision.down_discharge_reduction_mw[t]) / eta_d
        )
        down_end_t = down_mid_t + (b.interval_hours - tau) * (
            eta_c * c - d / eta_d
        )
        up_mid.append(up_mid_t)
        up_end.append(up_end_t)
        down_mid.append(down_mid_t)
        down_end.append(down_end_t)
        for label, value, upper in (
            ("up-branch charge", up_charge, b.charge_max_mw),
            ("up-branch discharge", up_discharge, b.discharge_max_mw),
            ("down-branch charge", down_charge, b.charge_max_mw),
            ("down-branch discharge", down_discharge, b.discharge_max_mw),
        ):
            _bound(
                violations,
                f"{label}[{t + 1}]",
                value,
                0.0,
                upper,
                tolerance,
            )
        for label, branch_mode, branch_charge, branch_discharge in (
            ("up", up_mode, up_charge, up_discharge),
            ("down", down_mode, down_charge, down_discharge),
        ):
            if branch_mode not in {0, 1}:
                violations.append(
                    f"{label}-branch mode[{t + 1}] is not binary"
                )
            if branch_charge > tolerance and branch_discharge > tolerance:
                violations.append(
                    f"simultaneous {label}-branch charge/discharge "
                    f"at hour {t + 1}"
                )
            if branch_mode == 1 and branch_charge > tolerance:
                violations.append(
                    f"{label}-branch charge violates discharge mode "
                    f"at hour {t + 1}"
                )
            if branch_mode == 0 and branch_discharge > tolerance:
                violations.append(
                    f"{label}-branch discharge violates charge mode "
                    f"at hour {t + 1}"
                )
        for label, value in (
            ("up-mid", up_mid_t),
            ("up-end", up_end_t),
            ("down-mid", down_mid_t),
            ("down-end", down_end_t),
        ):
            if value < -tolerance or value > b.energy_capacity_mwh + tolerance:
                violations.append(f"{label} SOC bound at hour {t + 1}")
        if abs(
            up + decision.reserve_shortfall_up_mw[t]
            - stage1.hybrid_up_reserve_mw[t]
        ) > tolerance:
            violations.append(f"upward reserve identity at hour {t + 1}")
        if abs(
            down
            + decision.reserve_shortfall_down_mw[t]
            - stage1.hybrid_down_reserve_mw[t]
        ) > tolerance:
            violations.append(f"downward reserve identity at hour {t + 1}")

    return ActivationReplay(
        deliverable_up_mw=tuple(up_delivered),
        shortfall_up_mw=tuple(up_short),
        deliverable_down_mw=tuple(down_delivered),
        shortfall_down_mw=tuple(down_short),
        up_mid_soc_mwh=tuple(up_mid),
        up_end_soc_mwh=tuple(up_end),
        down_mid_soc_mwh=tuple(down_mid),
        down_end_soc_mwh=tuple(down_end),
    )


def _replay_sequential(
    system: V2System,
    stage1: Stage1Decision,
    decision: ScenarioDecision,
    tolerance: float,
) -> SequentialReplay:
    b = system.battery
    tau = b.reserve_duration_hours
    eta_c = b.charge_efficiency
    eta_d = b.discharge_efficiency
    call_indices = {17, 18}
    energy = b.initial_energy_mwh
    path = [energy]
    mids = []
    delivered = []
    shortfalls = []
    violation = 0.0
    for t in range(system.horizon):
        c = decision.charge_mw[t]
        d = decision.discharge_mw[t]
        if t in call_indices:
            up = (
                decision.up_pv_release_mw[t]
                + decision.up_charge_reduction_mw[t]
                + decision.up_discharge_increase_mw[t]
            )
            mid = energy + tau * (
                eta_c * (c - decision.up_charge_reduction_mw[t])
                - (d + decision.up_discharge_increase_mw[t]) / eta_d
            )
            energy = mid + (b.interval_hours - tau) * (
                eta_c * c - d / eta_d
            )
            mids.append(mid)
            delivered.append(up)
            shortfalls.append(max(0.0, stage1.hybrid_up_reserve_mw[t] - up))
            violation += _distance_to_interval(
                mid, 0.0, b.energy_capacity_mwh
            )
        else:
            energy += b.interval_hours * (eta_c * c - d / eta_d)
        violation += _distance_to_interval(energy, 0.0, b.energy_capacity_mwh)
        path.append(energy)
    violation += max(0.0, b.terminal_energy_mwh - energy)
    assert len(mids) == 2
    return SequentialReplay(
        actual_soc_mwh=tuple(path),
        call_mid_soc_mwh=(mids[0], mids[1]),
        delivered_up_mw=(delivered[0], delivered[1]),
        shortfall_up_mw=(shortfalls[0], shortfalls[1]),
        physical_violation_mwh=violation if violation > tolerance else 0.0,
    )


def _cost_components(
    system: V2System,
    stage1: Stage1Decision,
    decision: ScenarioDecision,
) -> list[Tuple[str, float]]:
    p = system.penalties
    dt = system.battery.interval_hours
    tau = system.battery.reserve_duration_hours
    components: list[Tuple[str, float]] = []
    thermal_energy = sum(
        thermal_cost(unit, segments, interval_hours=dt)
        for unit, segments in zip(
            system.thermal_units, decision.thermal_segment_mw
        )
    )
    components.append(("thermal_energy", thermal_energy))
    components.append(
        (
            "thermal_reserve",
            p.thermal_reserve_per_mw
            * sum(
                sum(row)
                for matrix in (
                    stage1.thermal_up_reserve_mw,
                    stage1.thermal_down_reserve_mw,
                )
                for row in matrix
            ),
        )
    )
    da_shed = (
        decision_zeros(system.horizon)
        if len(stage1.day_ahead_load_shedding_mw) == 0
        else stage1.day_ahead_load_shedding_mw
    )
    da_spill = (
        decision_zeros(system.horizon)
        if len(stage1.day_ahead_spill_mw) == 0
        else stage1.day_ahead_spill_mw
    )
    components.append(
        (
            "day_ahead_load_shedding",
            p.load_shedding_per_mwh * dt * sum(da_shed),
        )
    )
    components.append(
        (
            "day_ahead_emergency_spill",
            p.emergency_spill_per_mwh * dt * sum(da_spill),
        )
    )
    components.append(
        (
            "hybrid_reserve",
            p.hybrid_reserve_per_mw
            * (
                sum(stage1.hybrid_up_reserve_mw)
                + sum(stage1.hybrid_down_reserve_mw)
            ),
        )
    )
    components.extend(
        (
            (
                "load_shedding",
                p.load_shedding_per_mwh * dt * sum(decision.load_shedding_mw),
            ),
            (
                "reserve_shortfall",
                p.reserve_shortfall_per_mwh
                * tau
                * (
                    sum(decision.reserve_shortfall_up_mw)
                    + sum(decision.reserve_shortfall_down_mw)
                ),
            ),
            (
                "imbalance",
                p.imbalance_per_mwh
                * dt
                * (
                    sum(decision.imbalance_positive_mw)
                    + sum(decision.imbalance_negative_mw)
                ),
            ),
            (
                "emergency_spill",
                p.emergency_spill_per_mwh
                * dt
                * sum(decision.emergency_spill_mw),
            ),
            (
                "pv_curtailment",
                p.pv_curtailment_per_mwh
                * dt
                * sum(decision.pv_curtailment_mw),
            ),
            (
                "battery_throughput",
                p.battery_throughput_per_mwh
                * dt
                * (sum(decision.charge_mw) + sum(decision.discharge_mw)),
            ),
        )
    )
    return components


def _bound(
    violations: list[str],
    label: str,
    value: float,
    lower: float,
    upper: float,
    tolerance: float,
) -> None:
    if value < lower - tolerance or value > upper + tolerance:
        violations.append(f"{label} outside [{lower}, {upper}]")


def _distance_to_interval(value: float, lower: float, upper: float) -> float:
    return max(0.0, lower - value, value - upper)


def decision_zeros(horizon: int) -> Tuple[float, ...]:
    return (0.0,) * horizon
