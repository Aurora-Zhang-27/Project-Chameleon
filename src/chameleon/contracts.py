"""Contract definitions and exact small-model feasibility checks.

The continuous model is a lossless, discharge-only battery.  The day-ahead
base schedule is ``p[t]`` and upward reserve award is ``r[t]``.  A reserve call
adds ``r[t]`` to the base injection for ``reserve_duration_hours`` at the end
of the interval.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from itertools import product
from typing import Iterable, Iterator, Sequence, Tuple, Union


class ContractKind(str, Enum):
    """Operator-visible contract classes in the small deterministic model."""

    C0_EXACT_MARGINAL = "c0_exact_marginal"
    C1_PREFIX = "c1_prefix"
    C_FULL_DET = "c_full_det"
    C0_MARKET = "c0_market_placeholder"


@dataclass(frozen=True)
class BatteryGeometry:
    """Parameters needed to define the contract feasible sets."""

    horizon: int
    initial_energy: Fraction
    power_max: Fraction
    interval_hours: Fraction = Fraction(1)
    reserve_duration_hours: Fraction = Fraction(1)

    def __post_init__(self) -> None:
        if self.horizon < 1:
            raise ValueError("horizon must be positive")
        if self.initial_energy < 0:
            raise ValueError("initial_energy must be nonnegative")
        if self.power_max < 0:
            raise ValueError("power_max must be nonnegative")
        if self.interval_hours <= 0:
            raise ValueError("interval_hours must be positive")
        if not (
            Fraction(0) < self.reserve_duration_hours <= self.interval_hours
        ):
            raise ValueError(
                "reserve_duration_hours must be in (0, interval_hours]"
            )


Trajectory = Tuple[Tuple[Fraction, ...], Tuple[Fraction, ...]]
FractionInput = Union[int, float, str, Fraction]


def _as_fraction_tuple(values: Sequence[FractionInput]) -> Tuple[Fraction, ...]:
    return tuple(Fraction(value) for value in values)


def local_pair_feasible(
    geometry: BatteryGeometry, p_t: Fraction, r_t: Fraction
) -> bool:
    """Return membership in one exact time-local marginal.

    With every other period set to zero, a local pair is extendable to a
    full-horizon physical trajectory exactly when it respects nonnegativity,
    inverter power, and its own energy requirement.
    """

    if p_t < 0 or r_t < 0:
        return False
    if p_t + r_t > geometry.power_max:
        return False
    local_energy = (
        p_t * geometry.interval_hours
        + r_t * geometry.reserve_duration_hours
    )
    return local_energy <= geometry.initial_energy


def c0_exact_marginal_feasible(
    geometry: BatteryGeometry,
    p: Sequence[FractionInput],
    r: Sequence[FractionInput],
) -> bool:
    """Membership in the Cartesian product of exact local projections."""

    p_fraction = _as_fraction_tuple(p)
    r_fraction = _as_fraction_tuple(r)
    _validate_lengths(geometry, p_fraction, r_fraction)
    return all(
        local_pair_feasible(geometry, p_t, r_t)
        for p_t, r_t in zip(p_fraction, r_fraction)
    )


def prefix_feasible(
    geometry: BatteryGeometry,
    p: Sequence[FractionInput],
    r: Sequence[FractionInput],
) -> bool:
    """Membership in the interpretable prefix-energy contract."""

    p_fraction = _as_fraction_tuple(p)
    r_fraction = _as_fraction_tuple(r)
    _validate_lengths(geometry, p_fraction, r_fraction)

    if not c0_exact_marginal_feasible(geometry, p_fraction, r_fraction):
        return False

    cumulative_base_energy = Fraction(0)
    for p_t, r_t in zip(p_fraction, r_fraction):
        cumulative_base_energy += p_t * geometry.interval_hours
        reserve_call_energy = r_t * geometry.reserve_duration_hours
        if cumulative_base_energy + reserve_call_energy > geometry.initial_energy:
            return False
    return True


def full_projected_feasible(
    geometry: BatteryGeometry,
    p: Sequence[FractionInput],
    r: Sequence[FractionInput],
) -> bool:
    """Exact projection of the lifted deterministic physical model.

    This independent state recursion deliberately does not call
    :func:`prefix_feasible`.  Equality of the two predicates is a testable
    consequence of eliminating the SOC variables, not an implementation
    alias.
    """

    p_fraction = _as_fraction_tuple(p)
    r_fraction = _as_fraction_tuple(r)
    _validate_lengths(geometry, p_fraction, r_fraction)

    energy_at_start = geometry.initial_energy
    for p_t, r_t in zip(p_fraction, r_fraction):
        if p_t < 0 or r_t < 0:
            return False
        if p_t + r_t > geometry.power_max:
            return False

        base_energy = p_t * geometry.interval_hours
        reserve_energy = r_t * geometry.reserve_duration_hours
        if base_energy + reserve_energy > energy_at_start:
            return False

        energy_at_start -= base_energy
        if energy_at_start < 0:
            return False
    return True


def contract_feasible(
    geometry: BatteryGeometry,
    kind: ContractKind,
    p: Sequence[FractionInput],
    r: Sequence[FractionInput],
) -> bool:
    """Dispatch to a contract membership predicate."""

    if kind is ContractKind.C0_EXACT_MARGINAL:
        return c0_exact_marginal_feasible(geometry, p, r)
    if kind is ContractKind.C1_PREFIX:
        return prefix_feasible(geometry, p, r)
    if kind is ContractKind.C_FULL_DET:
        return full_projected_feasible(geometry, p, r)
    if kind is ContractKind.C0_MARKET:
        raise NotImplementedError(
            "C0_MARKET is intentionally reserved for a later scalar market baseline"
        )
    raise ValueError(f"unknown contract kind: {kind}")


def enumerate_grid_trajectories(
    geometry: BatteryGeometry,
    kind: ContractKind,
    step: Fraction = Fraction(1),
) -> Iterator[Trajectory]:
    """Enumerate every grid trajectory admitted by ``kind`` using exact rationals.

    This is a finite cross-check, not a substitute for the continuous
    elimination proof.  The implementation first builds the exact local grid
    marginal and then forms its Cartesian power.
    """

    if step <= 0:
        raise ValueError("step must be positive")
    if kind is ContractKind.C0_MARKET:
        raise NotImplementedError(
            "C0_MARKET is intentionally reserved for a later scalar market baseline"
        )

    local_pairs = tuple(_enumerate_local_pairs(geometry, step))
    for selected_pairs in product(local_pairs, repeat=geometry.horizon):
        p = tuple(pair[0] for pair in selected_pairs)
        r = tuple(pair[1] for pair in selected_pairs)
        if contract_feasible(geometry, kind, p, r):
            yield p, r


def exact_local_grid_projection(
    geometry: BatteryGeometry,
    period: int,
    step: Fraction = Fraction(1),
) -> frozenset[Tuple[Fraction, Fraction]]:
    """Project enumerated full trajectories onto one period."""

    if not 0 <= period < geometry.horizon:
        raise IndexError("period outside horizon")
    return frozenset(
        (p[period], r[period])
        for p, r in enumerate_grid_trajectories(
            geometry, ContractKind.C_FULL_DET, step
        )
    )


def exact_local_grid_pairs(
    geometry: BatteryGeometry, step: Fraction = Fraction(1)
) -> frozenset[Tuple[Fraction, Fraction]]:
    """Return the analytically derived exact local marginal on a grid."""

    return frozenset(_enumerate_local_pairs(geometry, step))


def strict_c0_witness(
    geometry: BatteryGeometry,
) -> Trajectory | None:
    """Construct a simple trajectory in C0 but outside the full set, if possible."""

    if geometry.horizon < 2:
        return None
    quantity = min(
        geometry.power_max,
        geometry.initial_energy / geometry.interval_hours,
        geometry.initial_energy / geometry.reserve_duration_hours,
    )
    if quantity <= 0:
        return None

    p = [Fraction(0)] * geometry.horizon
    r = [Fraction(0)] * geometry.horizon
    p[0] = quantity
    r[-1] = quantity
    candidate = (tuple(p), tuple(r))
    if c0_exact_marginal_feasible(geometry, *candidate) and not (
        full_projected_feasible(geometry, *candidate)
    ):
        return candidate
    return None


def _enumerate_local_pairs(
    geometry: BatteryGeometry, step: Fraction
) -> Iterable[Tuple[Fraction, Fraction]]:
    max_index = int(geometry.power_max / step)
    for p_index in range(max_index + 1):
        p_t = step * p_index
        for r_index in range(max_index + 1):
            r_t = step * r_index
            if local_pair_feasible(geometry, p_t, r_t):
                yield p_t, r_t


def _validate_lengths(
    geometry: BatteryGeometry,
    p: Sequence[Fraction],
    r: Sequence[Fraction],
) -> None:
    if len(p) != geometry.horizon or len(r) != geometry.horizon:
        raise ValueError("trajectory length must equal horizon")
