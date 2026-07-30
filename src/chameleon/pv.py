"""Deterministic PV+BESS projection and independent replay models.

The module deliberately stops at one deterministic PV+BESS resource over a
small horizon.  PV availability is exogenous and known.  Curtailment, when
enabled, is represented by delivered PV ``g_t = w_t - q_t``.

Positive battery net power means discharge and negative net power means
charging.  Complementary physical actions use exactly one of charge and
discharge.  The continuous relaxation uses the converter convex hull.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from typing import Dict, Iterable, Iterator, Sequence, Tuple

from .charging import (
    BidirectionalBatteryGeometry,
    ChargingContractKind,
    FractionInput,
    contract_feasible,
    energy_depletion,
)


@dataclass(frozen=True)
class DeterministicPVGeometry:
    battery: BidirectionalBatteryGeometry
    pv_available: Tuple[Fraction, ...]

    def __post_init__(self) -> None:
        values = tuple(Fraction(value) for value in self.pv_available)
        object.__setattr__(self, "pv_available", values)
        if len(values) != self.battery.horizon:
            raise ValueError("pv_available length must equal horizon")
        if any(value < 0 for value in values):
            raise ValueError("PV availability must be nonnegative")


@dataclass(frozen=True)
class HybridAction:
    pv_delivered: Fraction
    charge_power: Fraction
    discharge_power: Fraction

    def __post_init__(self) -> None:
        object.__setattr__(self, "pv_delivered", Fraction(self.pv_delivered))
        object.__setattr__(self, "charge_power", Fraction(self.charge_power))
        object.__setattr__(
            self, "discharge_power", Fraction(self.discharge_power)
        )

    @property
    def battery_net_power(self) -> Fraction:
        return self.discharge_power - self.charge_power

    @property
    def hybrid_injection(self) -> Fraction:
        return self.pv_delivered + self.battery_net_power


@dataclass(frozen=True)
class HybridScheduleReplay:
    hybrid_injection: Tuple[Fraction, ...]
    soc_path: Tuple[Fraction, ...]
    pv_bounds_satisfied: bool
    battery_power_satisfied: bool
    complementarity_satisfied: bool
    converter_hull_satisfied: bool
    soc_bounds_satisfied: bool

    @property
    def physical_feasible(self) -> bool:
        return (
            self.pv_bounds_satisfied
            and self.battery_power_satisfied
            and self.complementarity_satisfied
            and self.soc_bounds_satisfied
        )

    @property
    def relaxed_feasible(self) -> bool:
        return (
            self.pv_bounds_satisfied
            and self.battery_power_satisfied
            and self.converter_hull_satisfied
            and self.soc_bounds_satisfied
        )


@dataclass(frozen=True)
class HybridReachability:
    reachable_energy_intervals: Tuple[Tuple[Fraction, Fraction], ...]
    local_battery_power_intervals: Tuple[Tuple[Fraction, Fraction], ...]
    feasible: bool


@dataclass(frozen=True)
class HybridReserveWitness:
    base_actions: Tuple[HybridAction, ...]
    upward_actions: Tuple[HybridAction, ...]
    downward_actions: Tuple[HybridAction, ...]


@dataclass(frozen=True)
class HybridReserveReplay:
    scheduled_injection: Tuple[Fraction, ...]
    upward_reserve: Tuple[Fraction, ...]
    downward_reserve: Tuple[Fraction, ...]
    base_soc_path: Tuple[Fraction, ...]
    upward_branch_end_energy: Tuple[Fraction, ...]
    downward_branch_end_energy: Tuple[Fraction, ...]
    upward_source: Tuple[Tuple[Fraction, Fraction, Fraction], ...]
    downward_source: Tuple[Tuple[Fraction, Fraction, Fraction], ...]
    action_bounds_satisfied: bool
    external_quantities_satisfied: bool
    base_soc_satisfied: bool
    branch_soc_satisfied: bool
    complementarity_satisfied: bool
    converter_hull_satisfied: bool

    @property
    def physical_feasible(self) -> bool:
        return (
            self.action_bounds_satisfied
            and self.external_quantities_satisfied
            and self.base_soc_satisfied
            and self.branch_soc_satisfied
            and self.complementarity_satisfied
        )

    @property
    def relaxed_feasible(self) -> bool:
        return (
            self.action_bounds_satisfied
            and self.external_quantities_satisfied
            and self.base_soc_satisfied
            and self.branch_soc_satisfied
            and self.converter_hull_satisfied
        )


def translated_battery_power(
    geometry: DeterministicPVGeometry,
    hybrid_injection: Sequence[FractionInput],
) -> Tuple[Fraction, ...]:
    """Translate must-take hybrid injection into battery net power."""

    h = _trajectory(geometry, hybrid_injection, "hybrid_injection")
    return tuple(
        h_t - w_t for h_t, w_t in zip(h, geometry.pv_available)
    )


def must_take_contract_feasible(
    geometry: DeterministicPVGeometry,
    hybrid_injection: Sequence[FractionInput],
    battery_contract: ChargingContractKind,
) -> bool:
    """Apply any battery-only contract after the exact affine translation."""

    return contract_feasible(
        geometry.battery,
        battery_contract,
        translated_battery_power(geometry, hybrid_injection),
    )


def replay_hybrid_schedule(
    geometry: DeterministicPVGeometry,
    actions: Sequence[HybridAction],
) -> HybridScheduleReplay:
    """Independently replay explicit PV delivery and battery actions."""

    if len(actions) != geometry.battery.horizon:
        raise ValueError("action trajectory length must equal horizon")

    battery = geometry.battery
    energy = battery.initial_energy
    soc_path = [energy]
    injections: list[Fraction] = []
    pv_ok = True
    power_ok = True
    complementary = True
    hull_ok = True
    soc_ok = True

    for w_t, action in zip(geometry.pv_available, actions):
        injections.append(action.hybrid_injection)
        pv_ok = pv_ok and 0 <= action.pv_delivered <= w_t
        power_ok = power_ok and (
            0 <= action.charge_power <= battery.charge_power_max
            and 0 <= action.discharge_power <= battery.discharge_power_max
        )
        complementary = complementary and not (
            action.charge_power > 0 and action.discharge_power > 0
        )
        hull_ok = hull_ok and _converter_hull_feasible(battery, action)

        energy += _soc_rate(battery, action) * battery.interval_hours
        soc_path.append(energy)
        soc_ok = soc_ok and battery.energy_min <= energy <= battery.energy_max

    return HybridScheduleReplay(
        hybrid_injection=tuple(injections),
        soc_path=tuple(soc_path),
        pv_bounds_satisfied=pv_ok,
        battery_power_satisfied=power_ok,
        complementarity_satisfied=complementary,
        converter_hull_satisfied=hull_ok,
        soc_bounds_satisfied=soc_ok,
    )


def exact_hybrid_reachability(
    geometry: DeterministicPVGeometry,
    hybrid_injection: Sequence[FractionInput],
    *,
    must_take: bool = False,
) -> HybridReachability:
    """Exact continuous projection test using reachable SOC intervals.

    With curtailment, a fixed hybrid injection permits battery power

    ``p_t in [h_t - w_t, h_t]``

    after intersection with battery power limits.  Energy depletion is
    continuous and strictly increasing in signed battery power, so an SOC
    interval maps to another interval exactly, including under lossy
    complementary operation.
    """

    h = _trajectory(geometry, hybrid_injection, "hybrid_injection")
    battery = geometry.battery
    reachable = [(battery.initial_energy, battery.initial_energy)]
    local_intervals: list[Tuple[Fraction, Fraction]] = []

    for h_t, w_t in zip(h, geometry.pv_available):
        if must_take:
            p_low = p_high = h_t - w_t
        else:
            p_low = max(-battery.charge_power_max, h_t - w_t)
            p_high = min(battery.discharge_power_max, h_t)
        local_intervals.append((p_low, p_high))
        if p_low > p_high:
            return HybridReachability(
                tuple(reachable), tuple(local_intervals), False
            )

        old_low, old_high = reachable[-1]
        next_low = max(
            battery.energy_min,
            old_low
            - energy_depletion(battery, p_high)
            * battery.interval_hours,
        )
        next_high = min(
            battery.energy_max,
            old_high
            - energy_depletion(battery, p_low)
            * battery.interval_hours,
        )
        if next_low > next_high:
            return HybridReachability(
                tuple(reachable), tuple(local_intervals), False
            )
        reachable.append((next_low, next_high))

    return HybridReachability(
        tuple(reachable), tuple(local_intervals), True
    )


def enumerate_hybrid_projection(
    geometry: DeterministicPVGeometry,
    step: Fraction = Fraction(1),
    *,
    must_take: bool = False,
    relaxed: bool = False,
) -> Dict[Tuple[Fraction, ...], Tuple[HybridAction, ...]]:
    """Exhaustively enumerate a rational-grid projection with witnesses."""

    local_actions = tuple(
        _actions_for_period(
            geometry.battery,
            geometry.pv_available[t],
            step,
            must_take=must_take,
            relaxed=relaxed,
        )
        for t in range(geometry.battery.horizon)
    )
    projected: Dict[Tuple[Fraction, ...], Tuple[HybridAction, ...]] = {}
    for actions in product(*local_actions):
        replay = replay_hybrid_schedule(geometry, actions)
        feasible = replay.relaxed_feasible if relaxed else replay.physical_feasible
        if feasible:
            projected.setdefault(replay.hybrid_injection, tuple(actions))
    return projected


def enumerate_period_actions(
    geometry: DeterministicPVGeometry,
    period: int,
    step: Fraction = Fraction(1),
    *,
    must_take: bool = False,
    relaxed: bool = False,
) -> Tuple[HybridAction, ...]:
    """Return all rational-grid internal actions for one period."""

    if not 0 <= period < geometry.battery.horizon:
        raise IndexError("period index out of range")
    return tuple(
        _actions_for_period(
            geometry.battery,
            geometry.pv_available[period],
            step,
            must_take=must_take,
            relaxed=relaxed,
        )
    )


def find_reserve_witness(
    geometry: DeterministicPVGeometry,
    scheduled_injection: Sequence[FractionInput],
    upward_reserve: Sequence[FractionInput],
    downward_reserve: Sequence[FractionInput],
    step: Fraction = Fraction(1),
    *,
    relaxed: bool = False,
) -> HybridReserveWitness | None:
    """Find an exact rational-grid witness for two isolated reserve branches.

    Upward and downward calls share one base decomposition.  Each branch
    replaces the base action only for the declared reserve duration at the end
    of its interval.  Calls are isolated and do not alter the later base SOC.
    """

    h = _trajectory(geometry, scheduled_injection, "scheduled_injection")
    r_up = _trajectory(geometry, upward_reserve, "upward_reserve")
    r_down = _trajectory(geometry, downward_reserve, "downward_reserve")
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
    ] = {
        battery.initial_energy: (tuple(), tuple(), tuple())
    }

    for t in range(battery.horizon):
        actions = tuple(
            _actions_for_period(
                battery,
                geometry.pv_available[t],
                step,
                must_take=False,
                relaxed=relaxed,
            )
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
                if not _action_valid(
                    battery, geometry.pv_available[t], base, relaxed
                ):
                    continue
                base_rate = _soc_rate(battery, base)
                base_end = energy + base_rate * battery.interval_hours
                if not battery.energy_min <= base_end <= battery.energy_max:
                    continue
                pre_call = (
                    energy
                    + base_rate
                    * (
                        battery.interval_hours
                        - battery.reserve_duration_hours
                    )
                )
                actual_up = (base,) if r_up[t] == 0 else up_options
                actual_down = (base,) if r_down[t] == 0 else down_options
                for up in actual_up:
                    up_end = (
                        pre_call
                        + _soc_rate(battery, up)
                        * battery.reserve_duration_hours
                    )
                    if not battery.energy_min <= up_end <= battery.energy_max:
                        continue
                    for down in actual_down:
                        down_end = (
                            pre_call
                            + _soc_rate(battery, down)
                            * battery.reserve_duration_hours
                        )
                        if not (
                            battery.energy_min
                            <= down_end
                            <= battery.energy_max
                        ):
                            continue
                        next_states.setdefault(
                            base_end,
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


def replay_reserve_witness(
    geometry: DeterministicPVGeometry,
    scheduled_injection: Sequence[FractionInput],
    upward_reserve: Sequence[FractionInput],
    downward_reserve: Sequence[FractionInput],
    witness: HybridReserveWitness,
) -> HybridReserveReplay:
    """Replay reserve branches without calling the witness search."""

    h = _trajectory(geometry, scheduled_injection, "scheduled_injection")
    r_up = _trajectory(geometry, upward_reserve, "upward_reserve")
    r_down = _trajectory(geometry, downward_reserve, "downward_reserve")
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
    base_path = [energy]
    up_ends: list[Fraction] = []
    down_ends: list[Fraction] = []
    up_sources: list[Tuple[Fraction, Fraction, Fraction]] = []
    down_sources: list[Tuple[Fraction, Fraction, Fraction]] = []
    bounds_ok = True
    external_ok = True
    base_soc_ok = True
    branch_soc_ok = True
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
            bounds_ok = bounds_ok and _basic_action_bounds(
                battery, geometry.pv_available[t], action
            )
            comp_ok = comp_ok and not (
                action.charge_power > 0 and action.discharge_power > 0
            )
            hull_ok = hull_ok and _converter_hull_feasible(battery, action)

        external_ok = external_ok and (
            base.hybrid_injection == h[t]
            and up.hybrid_injection == h[t] + r_up[t]
            and down.hybrid_injection == h[t] - r_down[t]
        )

        base_rate = _soc_rate(battery, base)
        pre_call = (
            energy
            + base_rate
            * (
                battery.interval_hours
                - battery.reserve_duration_hours
            )
        )
        up_end = (
            pre_call
            + _soc_rate(battery, up) * battery.reserve_duration_hours
        )
        down_end = (
            pre_call
            + _soc_rate(battery, down) * battery.reserve_duration_hours
        )
        up_ends.append(up_end)
        down_ends.append(down_end)
        branch_soc_ok = branch_soc_ok and (
            battery.energy_min <= up_end <= battery.energy_max
            and battery.energy_min <= down_end <= battery.energy_max
        )

        # Raw source increments sum to the external reserve quantity.
        up_sources.append(
            (
                up.pv_delivered - base.pv_delivered,
                base.charge_power - up.charge_power,
                up.discharge_power - base.discharge_power,
            )
        )
        down_sources.append(
            (
                base.pv_delivered - down.pv_delivered,
                down.charge_power - base.charge_power,
                base.discharge_power - down.discharge_power,
            )
        )

        energy += base_rate * battery.interval_hours
        base_path.append(energy)
        base_soc_ok = base_soc_ok and (
            battery.energy_min <= energy <= battery.energy_max
        )

    return HybridReserveReplay(
        scheduled_injection=h,
        upward_reserve=r_up,
        downward_reserve=r_down,
        base_soc_path=tuple(base_path),
        upward_branch_end_energy=tuple(up_ends),
        downward_branch_end_energy=tuple(down_ends),
        upward_source=tuple(up_sources),
        downward_source=tuple(down_sources),
        action_bounds_satisfied=bounds_ok,
        external_quantities_satisfied=external_ok,
        base_soc_satisfied=base_soc_ok,
        branch_soc_satisfied=branch_soc_ok,
        complementarity_satisfied=comp_ok,
        converter_hull_satisfied=hull_ok,
    )


def enumerate_reserve_projection(
    geometry: DeterministicPVGeometry,
    hybrid_values: Sequence[FractionInput],
    reserve_values: Sequence[FractionInput],
    step: Fraction = Fraction(1),
    *,
    direction: str,
    relaxed: bool = False,
) -> Dict[
    Tuple[Tuple[Fraction, ...], Tuple[Fraction, ...]],
    HybridReserveWitness,
]:
    """Enumerate an external grid for one isolated reserve direction."""

    if direction not in {"up", "down"}:
        raise ValueError("direction must be 'up' or 'down'")
    h_values = tuple(Fraction(value) for value in hybrid_values)
    r_values = tuple(Fraction(value) for value in reserve_values)
    if any(value < 0 for value in r_values):
        raise ValueError("reserve_values must be nonnegative")
    zero = (Fraction(0),) * geometry.battery.horizon
    projected: Dict[
        Tuple[Tuple[Fraction, ...], Tuple[Fraction, ...]],
        HybridReserveWitness,
    ] = {}
    for h in product(h_values, repeat=geometry.battery.horizon):
        for reserve in product(r_values, repeat=geometry.battery.horizon):
            up = reserve if direction == "up" else zero
            down = reserve if direction == "down" else zero
            witness = find_reserve_witness(
                geometry, h, up, down, step, relaxed=relaxed
            )
            if witness is not None:
                projected[(tuple(h), tuple(reserve))] = witness
    return projected


def _actions_for_period(
    battery: BidirectionalBatteryGeometry,
    pv_available: Fraction,
    step: Fraction,
    *,
    must_take: bool,
    relaxed: bool,
) -> Iterator[HybridAction]:
    if step <= 0:
        raise ValueError("step must be positive")
    pv_values = (
        (pv_available,)
        if must_take
        else tuple(_grid_values(pv_available, step))
    )
    if relaxed:
        for g_t in pv_values:
            for c_t in _grid_values(battery.charge_power_max, step):
                for d_t in _grid_values(battery.discharge_power_max, step):
                    action = HybridAction(g_t, c_t, d_t)
                    if _action_valid(battery, pv_available, action, True):
                        yield action
    else:
        signed_values = tuple(
            _signed_grid(
                battery.charge_power_max,
                battery.discharge_power_max,
                step,
            )
        )
        for g_t in pv_values:
            for p_t in signed_values:
                yield HybridAction(
                    g_t,
                    max(Fraction(0), -p_t),
                    max(Fraction(0), p_t),
                )


def _grid_values(limit: Fraction, step: Fraction) -> Iterable[Fraction]:
    count, remainder = divmod(limit, step)
    if remainder:
        raise ValueError("grid step must divide each enumerated limit")
    for index in range(int(count) + 1):
        yield index * step


def _signed_grid(
    charge_limit: Fraction,
    discharge_limit: Fraction,
    step: Fraction,
) -> Iterable[Fraction]:
    charge_count, charge_remainder = divmod(charge_limit, step)
    discharge_count, discharge_remainder = divmod(discharge_limit, step)
    if charge_remainder or discharge_remainder:
        raise ValueError("grid step must divide battery power limits")
    for index in range(-int(charge_count), int(discharge_count) + 1):
        yield index * step


def _basic_action_bounds(
    battery: BidirectionalBatteryGeometry,
    pv_available: Fraction,
    action: HybridAction,
) -> bool:
    return (
        0 <= action.pv_delivered <= pv_available
        and 0 <= action.charge_power <= battery.charge_power_max
        and 0 <= action.discharge_power <= battery.discharge_power_max
    )


def _action_valid(
    battery: BidirectionalBatteryGeometry,
    pv_available: Fraction,
    action: HybridAction,
    relaxed: bool,
) -> bool:
    if not _basic_action_bounds(battery, pv_available, action):
        return False
    if relaxed:
        return _converter_hull_feasible(battery, action)
    return not (
        action.charge_power > 0 and action.discharge_power > 0
    )


def _converter_hull_feasible(
    battery: BidirectionalBatteryGeometry,
    action: HybridAction,
) -> bool:
    utilization = Fraction(0)
    if battery.charge_power_max > 0:
        utilization += action.charge_power / battery.charge_power_max
    elif action.charge_power > 0:
        return False
    if battery.discharge_power_max > 0:
        utilization += action.discharge_power / battery.discharge_power_max
    elif action.discharge_power > 0:
        return False
    return utilization <= 1


def _soc_rate(
    battery: BidirectionalBatteryGeometry, action: HybridAction
) -> Fraction:
    return (
        battery.charge_efficiency * action.charge_power
        - action.discharge_power / battery.discharge_efficiency
    )


def _trajectory(
    geometry: DeterministicPVGeometry,
    values: Sequence[FractionInput],
    name: str,
) -> Tuple[Fraction, ...]:
    if len(values) != geometry.battery.horizon:
        raise ValueError(f"{name} length must equal horizon")
    return tuple(Fraction(value) for value in values)
