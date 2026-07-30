"""Exact small-horizon feasibility models with charging and discharging.

Positive net power means discharge/injection. Negative net power means
charge/withdrawal. The exact physical model uses a signed-power representation,
so charge/discharge complementarity is implicit in the sign of net power.

This module remains deterministic and battery-only. It intentionally contains
no PV, terminal target, repeated reserve calls, or stochastic model.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from itertools import product
from typing import Iterable, Iterator, Sequence, Tuple, Union


class ChargingContractKind(str, Enum):
    """Feasibility descriptions compared in the charging extension."""

    UPPER_ONLY_LINEAR_PREFIX = "upper_only_linear_prefix"
    TWO_SIDED_LINEAR_PREFIX = "two_sided_linear_prefix"
    MODE_AWARE_PREFIX = "mode_aware_prefix"
    FULL_PHYSICAL_COMPLEMENTARY = "full_physical_complementary"


@dataclass(frozen=True)
class BidirectionalBatteryGeometry:
    horizon: int
    initial_energy: Fraction
    energy_min: Fraction
    energy_max: Fraction
    charge_power_max: Fraction
    discharge_power_max: Fraction
    charge_efficiency: Fraction = Fraction(1)
    discharge_efficiency: Fraction = Fraction(1)
    interval_hours: Fraction = Fraction(1)
    reserve_duration_hours: Fraction = Fraction(1)

    def __post_init__(self) -> None:
        if self.horizon < 1:
            raise ValueError("horizon must be positive")
        if not self.energy_min <= self.initial_energy <= self.energy_max:
            raise ValueError("initial energy must lie within energy bounds")
        if self.charge_power_max < 0 or self.discharge_power_max < 0:
            raise ValueError("power limits must be nonnegative")
        if not Fraction(0) < self.charge_efficiency <= Fraction(1):
            raise ValueError("charge efficiency must lie in (0, 1]")
        if not Fraction(0) < self.discharge_efficiency <= Fraction(1):
            raise ValueError("discharge efficiency must lie in (0, 1]")
        if self.interval_hours <= 0:
            raise ValueError("interval_hours must be positive")
        if not (
            Fraction(0) < self.reserve_duration_hours <= self.interval_hours
        ):
            raise ValueError(
                "reserve_duration_hours must lie in (0, interval_hours]"
            )

    @property
    def is_lossless(self) -> bool:
        return (
            self.charge_efficiency == 1
            and self.discharge_efficiency == 1
        )


SignedTrajectory = Tuple[Tuple[Fraction, ...], Tuple[Fraction, ...]]
FractionInput = Union[int, float, str, Fraction]


def energy_depletion(
    geometry: BidirectionalBatteryGeometry, net_power: Fraction
) -> Fraction:
    """Energy removed from SOC per hour at one complementary operating point.

    The value is positive for discharge and negative for charge.
    """

    if net_power >= 0:
        return net_power / geometry.discharge_efficiency
    return geometry.charge_efficiency * net_power


def local_power_feasible(
    geometry: BidirectionalBatteryGeometry,
    net_power: Fraction,
    upward_reserve: Fraction,
) -> bool:
    """Check signed base power and upward-reserve converter limits."""

    return (
        -geometry.charge_power_max <= net_power
        and net_power <= geometry.discharge_power_max
        and upward_reserve >= 0
        and net_power + upward_reserve <= geometry.discharge_power_max
    )


def full_physical_feasible(
    geometry: BidirectionalBatteryGeometry,
    net_power: Sequence[FractionInput],
    upward_reserve: Sequence[FractionInput] | None = None,
) -> bool:
    """Replay the exact complementary signed-power physical model."""

    p, r = _normalize_trajectory(geometry, net_power, upward_reserve)
    energy = geometry.initial_energy
    dt = geometry.interval_hours
    tau = geometry.reserve_duration_hours

    for p_t, r_t in zip(p, r):
        if not local_power_feasible(geometry, p_t, r_t):
            return False

        # One isolated upward call at the end of the interval.
        reserve_end = (
            energy
            - energy_depletion(geometry, p_t) * (dt - tau)
            - energy_depletion(geometry, p_t + r_t) * tau
        )
        if not geometry.energy_min <= reserve_end <= geometry.energy_max:
            return False

        energy -= energy_depletion(geometry, p_t) * dt
        if not geometry.energy_min <= energy <= geometry.energy_max:
            return False
    return True


def upper_only_linear_prefix_feasible(
    geometry: BidirectionalBatteryGeometry,
    net_power: Sequence[FractionInput],
    upward_reserve: Sequence[FractionInput] | None = None,
) -> bool:
    """Naive net-energy upper prefix bound.

    This formulation ignores the upper SOC bound and uses net MWh as if the
    battery were lossless. It is included specifically to demonstrate failure.
    """

    p, r = _normalize_trajectory(geometry, net_power, upward_reserve)
    cumulative_net_energy = Fraction(0)
    usable_energy = geometry.initial_energy - geometry.energy_min

    for p_t, r_t in zip(p, r):
        if not local_power_feasible(geometry, p_t, r_t):
            return False
        cumulative_net_energy += p_t * geometry.interval_hours
        if (
            cumulative_net_energy
            + r_t * geometry.reserve_duration_hours
            > usable_energy
        ):
            return False
    return True


def two_sided_linear_prefix_feasible(
    geometry: BidirectionalBatteryGeometry,
    net_power: Sequence[FractionInput],
    upward_reserve: Sequence[FractionInput] | None = None,
) -> bool:
    """Lossless-style lower and upper net-energy prefix envelope."""

    p, r = _normalize_trajectory(geometry, net_power, upward_reserve)
    cumulative_net_energy = Fraction(0)
    lower_depletion = geometry.initial_energy - geometry.energy_max
    upper_depletion = geometry.initial_energy - geometry.energy_min

    for p_t, r_t in zip(p, r):
        if not local_power_feasible(geometry, p_t, r_t):
            return False
        cumulative_net_energy += p_t * geometry.interval_hours
        if not lower_depletion <= cumulative_net_energy <= upper_depletion:
            return False
        reserve_depletion = (
            cumulative_net_energy
            + r_t * geometry.reserve_duration_hours
        )
        if not lower_depletion <= reserve_depletion <= upper_depletion:
            return False
    return True


def mode_aware_prefix_feasible(
    geometry: BidirectionalBatteryGeometry,
    net_power: Sequence[FractionInput],
    upward_reserve: Sequence[FractionInput] | None = None,
) -> bool:
    """Efficiency-aware prefix formulation with complementary mode semantics.

    This is the exact eliminated formulation for the model in
    :func:`full_physical_feasible`. It is piecewise linear in net power and is
    generally nonconvex when efficiencies are lossy and the upper SOC bound
    matters.
    """

    p, r = _normalize_trajectory(geometry, net_power, upward_reserve)
    cumulative_base_depletion = Fraction(0)
    lower_depletion = geometry.initial_energy - geometry.energy_max
    upper_depletion = geometry.initial_energy - geometry.energy_min
    dt = geometry.interval_hours
    tau = geometry.reserve_duration_hours

    for p_t, r_t in zip(p, r):
        if not local_power_feasible(geometry, p_t, r_t):
            return False

        prior_depletion = cumulative_base_depletion
        cumulative_base_depletion += energy_depletion(geometry, p_t) * dt
        if not (
            lower_depletion
            <= cumulative_base_depletion
            <= upper_depletion
        ):
            return False

        reserve_depletion = (
            prior_depletion
            + energy_depletion(geometry, p_t) * (dt - tau)
            + energy_depletion(geometry, p_t + r_t) * tau
        )
        if not lower_depletion <= reserve_depletion <= upper_depletion:
            return False
    return True


def contract_feasible(
    geometry: BidirectionalBatteryGeometry,
    kind: ChargingContractKind,
    net_power: Sequence[FractionInput],
    upward_reserve: Sequence[FractionInput] | None = None,
) -> bool:
    if kind is ChargingContractKind.UPPER_ONLY_LINEAR_PREFIX:
        return upper_only_linear_prefix_feasible(
            geometry, net_power, upward_reserve
        )
    if kind is ChargingContractKind.TWO_SIDED_LINEAR_PREFIX:
        return two_sided_linear_prefix_feasible(
            geometry, net_power, upward_reserve
        )
    if kind is ChargingContractKind.MODE_AWARE_PREFIX:
        return mode_aware_prefix_feasible(
            geometry, net_power, upward_reserve
        )
    if kind is ChargingContractKind.FULL_PHYSICAL_COMPLEMENTARY:
        return full_physical_feasible(geometry, net_power, upward_reserve)
    raise ValueError(f"unknown charging contract: {kind}")


def relaxed_split_feasible(
    geometry: BidirectionalBatteryGeometry,
    charge_power: Sequence[FractionInput],
    discharge_power: Sequence[FractionInput],
) -> bool:
    """Feasibility in the convex split-variable relaxation.

    Complementarity is replaced by the convex-hull converter constraint
    ``c/Pch + d/Pdis <= 1``. Reserve is fixed to zero in this diagnostic.
    """

    if len(charge_power) != geometry.horizon:
        raise ValueError("charge trajectory length must equal horizon")
    if len(discharge_power) != geometry.horizon:
        raise ValueError("discharge trajectory length must equal horizon")

    c = tuple(Fraction(value) for value in charge_power)
    d = tuple(Fraction(value) for value in discharge_power)
    energy = geometry.initial_energy

    for c_t, d_t in zip(c, d):
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
    return True


def enumerate_signed_grid_trajectories(
    geometry: BidirectionalBatteryGeometry,
    kind: ChargingContractKind,
    step: Fraction = Fraction(1),
    *,
    include_reserve: bool = True,
) -> Iterator[SignedTrajectory]:
    """Enumerate exact rational-grid net-power and reserve trajectories."""

    if step <= 0:
        raise ValueError("step must be positive")
    local_pairs = tuple(
        _enumerate_local_signed_pairs(
            geometry, step, include_reserve=include_reserve
        )
    )
    for selected in product(local_pairs, repeat=geometry.horizon):
        p = tuple(pair[0] for pair in selected)
        r = tuple(pair[1] for pair in selected)
        if contract_feasible(geometry, kind, p, r):
            yield p, r


def enumerate_relaxed_net_grid_trajectories(
    geometry: BidirectionalBatteryGeometry,
    step: Fraction = Fraction(1),
) -> frozenset[Tuple[Fraction, ...]]:
    """Project the exact rational-grid convex relaxation onto net power."""

    if step <= 0:
        raise ValueError("step must be positive")
    local_splits = tuple(_enumerate_local_splits(geometry, step))
    projected: set[Tuple[Fraction, ...]] = set()
    for selected in product(local_splits, repeat=geometry.horizon):
        c = tuple(pair[0] for pair in selected)
        d = tuple(pair[1] for pair in selected)
        if relaxed_split_feasible(geometry, c, d):
            projected.add(tuple(d_t - c_t for c_t, d_t in zip(c, d)))
    return frozenset(projected)


def _enumerate_local_signed_pairs(
    geometry: BidirectionalBatteryGeometry,
    step: Fraction,
    *,
    include_reserve: bool,
) -> Iterable[Tuple[Fraction, Fraction]]:
    charge_steps = int(geometry.charge_power_max / step)
    discharge_steps = int(geometry.discharge_power_max / step)
    reserve_steps = int(
        (geometry.charge_power_max + geometry.discharge_power_max) / step
    )

    for p_index in range(-charge_steps, discharge_steps + 1):
        p_t = p_index * step
        r_indices = range(reserve_steps + 1) if include_reserve else range(1)
        for r_index in r_indices:
            r_t = r_index * step
            if local_power_feasible(geometry, p_t, r_t):
                yield p_t, r_t


def _enumerate_local_splits(
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


def _normalize_trajectory(
    geometry: BidirectionalBatteryGeometry,
    net_power: Sequence[FractionInput],
    upward_reserve: Sequence[FractionInput] | None,
) -> SignedTrajectory:
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
