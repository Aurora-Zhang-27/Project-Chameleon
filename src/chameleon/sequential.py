"""Sequential deterministic reserve activation for one PV+BESS resource."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Dict, Sequence, Tuple

from .charging import FractionInput, energy_depletion
from .pv import (
    DeterministicPVGeometry,
    HybridAction,
    HybridReserveWitness,
    enumerate_period_actions,
)


class Activation(str, Enum):
    NONE = "none"
    UP = "up"
    DOWN = "down"


class ReserveSourcePolicy(str, Enum):
    ANY = "any"
    PV_ONLY = "pv_only"
    BATTERY_ONLY = "battery_only"


@dataclass(frozen=True)
class SequentialReplayResult:
    realized_soc_path: Tuple[Fraction, ...]
    pre_activation_energy: Tuple[Fraction, ...]
    nominal_base_end_energy: Tuple[Fraction, ...]
    upward_branch_end_energy: Tuple[Fraction, ...]
    downward_branch_end_energy: Tuple[Fraction, ...]
    external_quantities_satisfied: bool
    action_bounds_satisfied: bool
    source_policy_satisfied: bool
    nominal_and_branch_soc_satisfied: bool
    realized_soc_satisfied: bool
    complementarity_satisfied: bool
    converter_hull_satisfied: bool

    @property
    def physical_feasible(self) -> bool:
        return (
            self.external_quantities_satisfied
            and self.action_bounds_satisfied
            and self.source_policy_satisfied
            and self.nominal_and_branch_soc_satisfied
            and self.realized_soc_satisfied
            and self.complementarity_satisfied
        )

    @property
    def relaxed_feasible(self) -> bool:
        return (
            self.external_quantities_satisfied
            and self.action_bounds_satisfied
            and self.source_policy_satisfied
            and self.nominal_and_branch_soc_satisfied
            and self.realized_soc_satisfied
            and self.converter_hull_satisfied
        )


@dataclass(frozen=True)
class SequentialReachability:
    period_start_intervals: Tuple[Tuple[Fraction, Fraction], ...]
    pre_activation_intervals: Tuple[
        Tuple[Fraction, Fraction] | None, ...
    ]
    period_end_intervals: Tuple[Tuple[Fraction, Fraction], ...]
    feasible: bool


def find_sequential_witness(
    geometry: DeterministicPVGeometry,
    scheduled_injection: Sequence[FractionInput],
    upward_reserve: Sequence[FractionInput],
    downward_reserve: Sequence[FractionInput],
    activations: Sequence[Activation | str],
    step: Fraction = Fraction(1),
    *,
    upward_source: (
        ReserveSourcePolicy | Sequence[ReserveSourcePolicy | str]
    ) = ReserveSourcePolicy.ANY,
    downward_source: (
        ReserveSourcePolicy | Sequence[ReserveSourcePolicy | str]
    ) = ReserveSourcePolicy.ANY,
    relaxed: bool = False,
) -> HybridReserveWitness | None:
    """Find a grid-exact source-aware witness for a realized call sequence.

    At every period, the common base action and both awarded reserve branches
    must be feasible from the currently realized SOC.  The selected branch
    endpoint, rather than the nominal base endpoint, becomes the next state.
    """

    h = _trajectory(geometry, scheduled_injection, "scheduled_injection")
    r_up = _trajectory(geometry, upward_reserve, "upward_reserve")
    r_down = _trajectory(geometry, downward_reserve, "downward_reserve")
    calls = _activations(geometry, activations)
    up_policies = _policies(geometry, upward_source)
    down_policies = _policies(geometry, downward_source)
    if any(value < 0 for value in r_up + r_down):
        raise ValueError("reserve quantities must be nonnegative")

    battery = geometry.battery
    states: Dict[
        Fraction,
        Tuple[
            Tuple[HybridAction, ...],
            Tuple[HybridAction, ...],
            Tuple[HybridAction, ...],
        ],
    ] = {battery.initial_energy: (tuple(), tuple(), tuple())}

    for t in range(battery.horizon):
        actions = enumerate_period_actions(
            geometry, t, step, relaxed=relaxed
        )
        base_options = tuple(
            action for action in actions if action.hybrid_injection == h[t]
        )
        up_options = tuple(
            action
            for action in actions
            if action.hybrid_injection == h[t] + r_up[t]
        )
        down_options = tuple(
            action
            for action in actions
            if action.hybrid_injection == h[t] - r_down[t]
        )
        next_states: Dict[
            Fraction,
            Tuple[
                Tuple[HybridAction, ...],
                Tuple[HybridAction, ...],
                Tuple[HybridAction, ...],
            ],
        ] = {}

        for energy, paths in states.items():
            for base in base_options:
                base_rate = _soc_rate(geometry, base)
                pre_call = (
                    energy
                    + base_rate
                    * (
                        battery.interval_hours
                        - battery.reserve_duration_hours
                    )
                )
                base_end = energy + base_rate * battery.interval_hours
                if not (
                    _inside(geometry, pre_call)
                    and _inside(geometry, base_end)
                ):
                    continue

                actual_up = (base,) if r_up[t] == 0 else up_options
                actual_down = (base,) if r_down[t] == 0 else down_options
                for up in actual_up:
                    if not _source_allowed(base, up, up_policies[t]):
                        continue
                    up_end = (
                        pre_call
                        + _soc_rate(geometry, up)
                        * battery.reserve_duration_hours
                    )
                    if not _inside(geometry, up_end):
                        continue
                    for down in actual_down:
                        if not _source_allowed(
                            base, down, down_policies[t]
                        ):
                            continue
                        down_end = (
                            pre_call
                            + _soc_rate(geometry, down)
                            * battery.reserve_duration_hours
                        )
                        if not _inside(geometry, down_end):
                            continue

                        if calls[t] is Activation.UP:
                            realized_end = up_end
                        elif calls[t] is Activation.DOWN:
                            realized_end = down_end
                        else:
                            realized_end = base_end
                        next_states.setdefault(
                            realized_end,
                            (
                                paths[0] + (base,),
                                paths[1] + (up,),
                                paths[2] + (down,),
                            ),
                        )
        states = next_states
        if not states:
            return None

    base, up, down = next(iter(states.values()))
    return HybridReserveWitness(base, up, down)


def replay_sequential_witness(
    geometry: DeterministicPVGeometry,
    scheduled_injection: Sequence[FractionInput],
    upward_reserve: Sequence[FractionInput],
    downward_reserve: Sequence[FractionInput],
    activations: Sequence[Activation | str],
    witness: HybridReserveWitness,
    *,
    upward_source: (
        ReserveSourcePolicy | Sequence[ReserveSourcePolicy | str]
    ) = ReserveSourcePolicy.ANY,
    downward_source: (
        ReserveSourcePolicy | Sequence[ReserveSourcePolicy | str]
    ) = ReserveSourcePolicy.ANY,
) -> SequentialReplayResult:
    """Independently replay realized SOC across reserve activations."""

    h = _trajectory(geometry, scheduled_injection, "scheduled_injection")
    r_up = _trajectory(geometry, upward_reserve, "upward_reserve")
    r_down = _trajectory(geometry, downward_reserve, "downward_reserve")
    calls = _activations(geometry, activations)
    up_policies = _policies(geometry, upward_source)
    down_policies = _policies(geometry, downward_source)
    horizon = geometry.battery.horizon
    if not (
        len(witness.base_actions)
        == len(witness.upward_actions)
        == len(witness.downward_actions)
        == horizon
    ):
        raise ValueError("witness action lengths must equal horizon")

    battery = geometry.battery
    energy = battery.initial_energy
    realized_path = [energy]
    pre_values: list[Fraction] = []
    base_ends: list[Fraction] = []
    up_ends: list[Fraction] = []
    down_ends: list[Fraction] = []
    external_ok = True
    bounds_ok = True
    source_ok = True
    all_endpoints_ok = True
    realized_ok = True
    comp_ok = True
    hull_ok = True

    for t, (base, up, down) in enumerate(
        zip(
            witness.base_actions,
            witness.upward_actions,
            witness.downward_actions,
        )
    ):
        for action in (base, up, down):
            bounds_ok = bounds_ok and _action_bounds(
                geometry, t, action
            )
            comp_ok = comp_ok and not (
                action.charge_power > 0 and action.discharge_power > 0
            )
            hull_ok = hull_ok and _converter_hull(geometry, action)

        external_ok = external_ok and (
            base.hybrid_injection == h[t]
            and up.hybrid_injection == h[t] + r_up[t]
            and down.hybrid_injection == h[t] - r_down[t]
        )
        source_ok = source_ok and _source_allowed(
            base, up, up_policies[t]
        )
        source_ok = source_ok and _source_allowed(
            base, down, down_policies[t]
        )

        base_rate = _soc_rate(geometry, base)
        pre_call = (
            energy
            + base_rate
            * (
                battery.interval_hours
                - battery.reserve_duration_hours
            )
        )
        base_end = energy + base_rate * battery.interval_hours
        up_end = (
            pre_call
            + _soc_rate(geometry, up) * battery.reserve_duration_hours
        )
        down_end = (
            pre_call
            + _soc_rate(geometry, down) * battery.reserve_duration_hours
        )
        pre_values.append(pre_call)
        base_ends.append(base_end)
        up_ends.append(up_end)
        down_ends.append(down_end)
        all_endpoints_ok = all_endpoints_ok and all(
            _inside(geometry, value)
            for value in (pre_call, base_end, up_end, down_end)
        )

        if calls[t] is Activation.UP:
            energy = up_end
        elif calls[t] is Activation.DOWN:
            energy = down_end
        else:
            energy = base_end
        realized_path.append(energy)
        realized_ok = realized_ok and _inside(geometry, energy)

    return SequentialReplayResult(
        realized_soc_path=tuple(realized_path),
        pre_activation_energy=tuple(pre_values),
        nominal_base_end_energy=tuple(base_ends),
        upward_branch_end_energy=tuple(up_ends),
        downward_branch_end_energy=tuple(down_ends),
        external_quantities_satisfied=external_ok,
        action_bounds_satisfied=bounds_ok,
        source_policy_satisfied=source_ok,
        nominal_and_branch_soc_satisfied=all_endpoints_ok,
        realized_soc_satisfied=realized_ok,
        complementarity_satisfied=comp_ok,
        converter_hull_satisfied=hull_ok,
    )


def activation_conditioned_reachability(
    geometry: DeterministicPVGeometry,
    scheduled_injection: Sequence[FractionInput],
    upward_reserve: Sequence[FractionInput],
    downward_reserve: Sequence[FractionInput],
    activations: Sequence[Activation | str],
    *,
    initial_interval: Tuple[FractionInput, FractionInput] | None = None,
) -> SequentialReachability:
    """Propagate the exact SOC interval along the realized activation path.

    This map uses unrestricted internal source choice and conditions only on
    the branch that was actually activated.  Qualification of the uncalled
    branch is an additional intersection handled by the source-lifted witness
    model.
    """

    h = _trajectory(geometry, scheduled_injection, "scheduled_injection")
    r_up = _trajectory(geometry, upward_reserve, "upward_reserve")
    r_down = _trajectory(geometry, downward_reserve, "downward_reserve")
    calls = _activations(geometry, activations)
    battery = geometry.battery
    if initial_interval is None:
        current = (battery.initial_energy, battery.initial_energy)
    else:
        current = (
            Fraction(initial_interval[0]),
            Fraction(initial_interval[1]),
        )
        if (
            current[0] > current[1]
            or current[0] < battery.energy_min
            or current[1] > battery.energy_max
        ):
            raise ValueError("invalid initial SOC interval")

    starts: list[Tuple[Fraction, Fraction]] = []
    pre_intervals: list[Tuple[Fraction, Fraction] | None] = []
    ends: list[Tuple[Fraction, Fraction]] = []

    for t in range(battery.horizon):
        starts.append(current)
        base_power = _battery_power_interval(geometry, t, h[t])
        if base_power is None:
            return SequentialReachability(
                tuple(starts), tuple(pre_intervals), tuple(ends), False
            )

        if calls[t] is Activation.NONE:
            pre_intervals.append(None)
            mapped = _map_energy_interval(
                geometry,
                current,
                base_power,
                battery.interval_hours,
            )
        else:
            pre = _map_energy_interval(
                geometry,
                current,
                base_power,
                battery.interval_hours
                - battery.reserve_duration_hours,
            )
            pre_intervals.append(pre)
            if pre is None:
                return SequentialReachability(
                    tuple(starts),
                    tuple(pre_intervals),
                    tuple(ends),
                    False,
                )
            target = (
                h[t] + r_up[t]
                if calls[t] is Activation.UP
                else h[t] - r_down[t]
            )
            branch_power = _battery_power_interval(
                geometry, t, target
            )
            if branch_power is None:
                return SequentialReachability(
                    tuple(starts),
                    tuple(pre_intervals),
                    tuple(ends),
                    False,
                )
            mapped = _map_energy_interval(
                geometry,
                pre,
                branch_power,
                battery.reserve_duration_hours,
            )
        if mapped is None:
            return SequentialReachability(
                tuple(starts), tuple(pre_intervals), tuple(ends), False
            )
        current = mapped
        ends.append(current)

    return SequentialReachability(
        tuple(starts), tuple(pre_intervals), tuple(ends), True
    )


def _battery_power_interval(
    geometry: DeterministicPVGeometry,
    period: int,
    hybrid_injection: Fraction,
) -> Tuple[Fraction, Fraction] | None:
    battery = geometry.battery
    w_t = geometry.pv_available[period]
    lower = max(-battery.charge_power_max, hybrid_injection - w_t)
    upper = min(battery.discharge_power_max, hybrid_injection)
    return None if lower > upper else (lower, upper)


def _map_energy_interval(
    geometry: DeterministicPVGeometry,
    energy_interval: Tuple[Fraction, Fraction],
    power_interval: Tuple[Fraction, Fraction],
    duration: Fraction,
) -> Tuple[Fraction, Fraction] | None:
    battery = geometry.battery
    low_energy, high_energy = energy_interval
    low_power, high_power = power_interval
    next_low = max(
        battery.energy_min,
        low_energy - energy_depletion(battery, high_power) * duration,
    )
    next_high = min(
        battery.energy_max,
        high_energy - energy_depletion(battery, low_power) * duration,
    )
    return None if next_low > next_high else (next_low, next_high)


def _source_allowed(
    base: HybridAction,
    branch: HybridAction,
    policy: ReserveSourcePolicy,
) -> bool:
    if policy is ReserveSourcePolicy.ANY:
        return True
    if policy is ReserveSourcePolicy.PV_ONLY:
        return (
            branch.charge_power == base.charge_power
            and branch.discharge_power == base.discharge_power
        )
    if policy is ReserveSourcePolicy.BATTERY_ONLY:
        return branch.pv_delivered == base.pv_delivered
    raise ValueError(f"unknown source policy: {policy}")


def _soc_rate(
    geometry: DeterministicPVGeometry, action: HybridAction
) -> Fraction:
    battery = geometry.battery
    return (
        battery.charge_efficiency * action.charge_power
        - action.discharge_power / battery.discharge_efficiency
    )


def _inside(
    geometry: DeterministicPVGeometry, energy: Fraction
) -> bool:
    return (
        geometry.battery.energy_min
        <= energy
        <= geometry.battery.energy_max
    )


def _action_bounds(
    geometry: DeterministicPVGeometry,
    period: int,
    action: HybridAction,
) -> bool:
    battery = geometry.battery
    return (
        0 <= action.pv_delivered <= geometry.pv_available[period]
        and 0 <= action.charge_power <= battery.charge_power_max
        and 0 <= action.discharge_power <= battery.discharge_power_max
    )


def _converter_hull(
    geometry: DeterministicPVGeometry, action: HybridAction
) -> bool:
    battery = geometry.battery
    utilization = Fraction(0)
    if battery.charge_power_max:
        utilization += action.charge_power / battery.charge_power_max
    elif action.charge_power:
        return False
    if battery.discharge_power_max:
        utilization += (
            action.discharge_power / battery.discharge_power_max
        )
    elif action.discharge_power:
        return False
    return utilization <= 1


def _trajectory(
    geometry: DeterministicPVGeometry,
    values: Sequence[FractionInput],
    name: str,
) -> Tuple[Fraction, ...]:
    if len(values) != geometry.battery.horizon:
        raise ValueError(f"{name} length must equal horizon")
    return tuple(Fraction(value) for value in values)


def _activations(
    geometry: DeterministicPVGeometry,
    values: Sequence[Activation | str],
) -> Tuple[Activation, ...]:
    if len(values) != geometry.battery.horizon:
        raise ValueError("activations length must equal horizon")
    return tuple(Activation(value) for value in values)


def _policies(
    geometry: DeterministicPVGeometry,
    values: ReserveSourcePolicy | Sequence[ReserveSourcePolicy | str],
) -> Tuple[ReserveSourcePolicy, ...]:
    if isinstance(values, (ReserveSourcePolicy, str)):
        policy = ReserveSourcePolicy(values)
        return (policy,) * geometry.battery.horizon
    if len(values) != geometry.battery.horizon:
        raise ValueError("source-policy length must equal horizon")
    return tuple(ReserveSourcePolicy(value) for value in values)
