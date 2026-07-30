"""Terminal-energy extension for the deterministic small battery models.

The terminal requirement applies to the scheduled base trajectory:

    e[T + 1] >= terminal_energy.

Reserve calls retain the Phase-I single-call semantics and do not alter the
subsequent base SOC trajectory. A recovery-after-activation requirement would
be a different contract and is intentionally not modeled here.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from typing import Iterable, Sequence, Tuple, Union

from .charging import (
    BidirectionalBatteryGeometry,
    ChargingContractKind,
    FractionInput,
    contract_feasible,
)


@dataclass(frozen=True)
class TerminalReplayResult:
    soc_path: Tuple[Fraction, ...]
    reserve_branch_end_energy: Tuple[Fraction, ...]
    terminal_energy: Fraction
    terminal_shortfall: Fraction
    base_bounds_satisfied: bool
    reserve_bounds_satisfied: bool
    power_bounds_satisfied: bool

    @property
    def terminal_satisfied(self) -> bool:
        return self.terminal_shortfall == 0

    @property
    def physically_feasible(self) -> bool:
        return (
            self.base_bounds_satisfied
            and self.reserve_bounds_satisfied
            and self.power_bounds_satisfied
            and self.terminal_satisfied
        )


def replay_terminal_soc(
    geometry: BidirectionalBatteryGeometry,
    net_power: Sequence[FractionInput],
    terminal_energy: FractionInput,
    upward_reserve: Sequence[FractionInput] | None = None,
) -> TerminalReplayResult:
    """Independently replay base SOC, isolated reserve branches, and terminal SOC.

    This implementation does not call the prefix or full-feasibility
    predicates from :mod:`chameleon.charging`.
    """

    p, r = _normalize(geometry, net_power, upward_reserve)
    target = Fraction(terminal_energy)
    _validate_terminal_target(geometry, target)

    energy = geometry.initial_energy
    soc_path = [energy]
    reserve_end_values: list[Fraction] = []
    base_bounds_satisfied = True
    reserve_bounds_satisfied = True
    power_bounds_satisfied = True

    for p_t, r_t in zip(p, r):
        if not (
            -geometry.charge_power_max <= p_t
            and p_t <= geometry.discharge_power_max
            and r_t >= 0
            and p_t + r_t <= geometry.discharge_power_max
        ):
            power_bounds_satisfied = False

        reserve_end = (
            energy
            + _soc_rate(geometry, p_t)
            * (geometry.interval_hours - geometry.reserve_duration_hours)
            + _soc_rate(geometry, p_t + r_t)
            * geometry.reserve_duration_hours
        )
        reserve_end_values.append(reserve_end)
        if not geometry.energy_min <= reserve_end <= geometry.energy_max:
            reserve_bounds_satisfied = False

        energy += _soc_rate(geometry, p_t) * geometry.interval_hours
        soc_path.append(energy)
        if not geometry.energy_min <= energy <= geometry.energy_max:
            base_bounds_satisfied = False

    shortfall = max(Fraction(0), target - energy)
    return TerminalReplayResult(
        soc_path=tuple(soc_path),
        reserve_branch_end_energy=tuple(reserve_end_values),
        terminal_energy=energy,
        terminal_shortfall=shortfall,
        base_bounds_satisfied=base_bounds_satisfied,
        reserve_bounds_satisfied=reserve_bounds_satisfied,
        power_bounds_satisfied=power_bounds_satisfied,
    )


def lossless_terminal_cut_feasible(
    geometry: BidirectionalBatteryGeometry,
    net_power: Sequence[FractionInput],
    terminal_energy: FractionInput,
) -> bool:
    """Check the linear terminal cut for a lossless signed-power model."""

    if not geometry.is_lossless:
        raise ValueError("lossless_terminal_cut_feasible requires eta_c=eta_d=1")
    if len(net_power) != geometry.horizon:
        raise ValueError("net-power trajectory length must equal horizon")
    target = Fraction(terminal_energy)
    _validate_terminal_target(geometry, target)
    total_depletion = sum(
        Fraction(p_t) * geometry.interval_hours for p_t in net_power
    )
    return total_depletion <= geometry.initial_energy - target


def mode_aware_terminal_cut_feasible(
    geometry: BidirectionalBatteryGeometry,
    net_power: Sequence[FractionInput],
    terminal_energy: FractionInput,
) -> bool:
    """Check the efficiency- and direction-aware terminal cut."""

    if len(net_power) != geometry.horizon:
        raise ValueError("net-power trajectory length must equal horizon")
    target = Fraction(terminal_energy)
    _validate_terminal_target(geometry, target)
    total_depletion = sum(
        _depletion(geometry, Fraction(p_t)) * geometry.interval_hours
        for p_t in net_power
    )
    return total_depletion <= geometry.initial_energy - target


def prefix_with_terminal_feasible(
    geometry: BidirectionalBatteryGeometry,
    prefix_kind: ChargingContractKind,
    net_power: Sequence[FractionInput],
    terminal_energy: FractionInput,
    upward_reserve: Sequence[FractionInput] | None = None,
) -> bool:
    """Intersect an existing prefix contract with the correct terminal cut."""

    if not contract_feasible(
        geometry, prefix_kind, net_power, upward_reserve
    ):
        return False
    if prefix_kind is ChargingContractKind.TWO_SIDED_LINEAR_PREFIX:
        return lossless_terminal_cut_feasible(
            geometry, net_power, terminal_energy
        )
    if prefix_kind is ChargingContractKind.MODE_AWARE_PREFIX:
        return mode_aware_terminal_cut_feasible(
            geometry, net_power, terminal_energy
        )
    raise ValueError(
        "terminal exactness is defined only for two-sided lossless or "
        "mode-aware prefixes"
    )


def full_with_terminal_feasible(
    geometry: BidirectionalBatteryGeometry,
    net_power: Sequence[FractionInput],
    terminal_energy: FractionInput,
    upward_reserve: Sequence[FractionInput] | None = None,
) -> bool:
    """Use the independent replay as the full terminal physical predicate."""

    return replay_terminal_soc(
        geometry, net_power, terminal_energy, upward_reserve
    ).physically_feasible


def relaxed_with_terminal_feasible(
    geometry: BidirectionalBatteryGeometry,
    charge_power: Sequence[FractionInput],
    discharge_power: Sequence[FractionInput],
    terminal_energy: FractionInput,
) -> bool:
    """Check the continuous split-variable relaxation with a terminal target."""

    if len(charge_power) != geometry.horizon:
        raise ValueError("charge trajectory length must equal horizon")
    if len(discharge_power) != geometry.horizon:
        raise ValueError("discharge trajectory length must equal horizon")
    target = Fraction(terminal_energy)
    _validate_terminal_target(geometry, target)

    energy = geometry.initial_energy
    for c_raw, d_raw in zip(charge_power, discharge_power):
        c_t = Fraction(c_raw)
        d_t = Fraction(d_raw)
        if c_t < 0 or d_t < 0:
            return False
        if c_t > geometry.charge_power_max:
            return False
        if d_t > geometry.discharge_power_max:
            return False

        utilization = Fraction(0)
        if geometry.charge_power_max > 0:
            utilization += c_t / geometry.charge_power_max
        elif c_t > 0:
            return False
        if geometry.discharge_power_max > 0:
            utilization += d_t / geometry.discharge_power_max
        elif d_t > 0:
            return False
        if utilization > 1:
            return False

        energy += (
            geometry.charge_efficiency * c_t
            - d_t / geometry.discharge_efficiency
        ) * geometry.interval_hours
        if not geometry.energy_min <= energy <= geometry.energy_max:
            return False
    return energy >= target


def enumerate_relaxed_terminal_net_grid(
    geometry: BidirectionalBatteryGeometry,
    terminal_energy: FractionInput,
    step: Fraction = Fraction(1),
) -> frozenset[Tuple[Fraction, ...]]:
    """Enumerate the relaxed terminal set and project it onto net power."""

    if step <= 0:
        raise ValueError("step must be positive")
    local_splits = tuple(_local_split_grid(geometry, step))
    projected: set[Tuple[Fraction, ...]] = set()
    for selected in product(local_splits, repeat=geometry.horizon):
        c = tuple(pair[0] for pair in selected)
        d = tuple(pair[1] for pair in selected)
        if relaxed_with_terminal_feasible(
            geometry, c, d, terminal_energy
        ):
            projected.add(tuple(d_t - c_t for c_t, d_t in zip(c, d)))
    return frozenset(projected)


def _soc_rate(
    geometry: BidirectionalBatteryGeometry, net_power: Fraction
) -> Fraction:
    if net_power >= 0:
        return -net_power / geometry.discharge_efficiency
    return geometry.charge_efficiency * (-net_power)


def _depletion(
    geometry: BidirectionalBatteryGeometry, net_power: Fraction
) -> Fraction:
    return -_soc_rate(geometry, net_power)


def _normalize(
    geometry: BidirectionalBatteryGeometry,
    net_power: Sequence[FractionInput],
    upward_reserve: Sequence[FractionInput] | None,
) -> Tuple[Tuple[Fraction, ...], Tuple[Fraction, ...]]:
    if len(net_power) != geometry.horizon:
        raise ValueError("net-power trajectory length must equal horizon")
    p = tuple(Fraction(value) for value in net_power)
    if upward_reserve is None:
        r = (Fraction(0),) * geometry.horizon
    else:
        if len(upward_reserve) != geometry.horizon:
            raise ValueError("reserve trajectory length must equal horizon")
        r = tuple(Fraction(value) for value in upward_reserve)
    return p, r


def _validate_terminal_target(
    geometry: BidirectionalBatteryGeometry, target: Fraction
) -> None:
    if not geometry.energy_min <= target <= geometry.energy_max:
        raise ValueError("terminal target must lie within SOC bounds")


def _local_split_grid(
    geometry: BidirectionalBatteryGeometry, step: Fraction
) -> Iterable[Tuple[Fraction, Fraction]]:
    charge_steps = int(geometry.charge_power_max / step)
    discharge_steps = int(geometry.discharge_power_max / step)
    for c_index in range(charge_steps + 1):
        c_t = c_index * step
        for d_index in range(discharge_steps + 1):
            d_t = d_index * step
            utilization = Fraction(0)
            if geometry.charge_power_max > 0:
                utilization += c_t / geometry.charge_power_max
            if geometry.discharge_power_max > 0:
                utilization += d_t / geometry.discharge_power_max
            if utilization <= 1:
                yield c_t, d_t

