"""Independent physical replay for schedules produced by the operator LP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

from .model import BatterySpec


@dataclass(frozen=True)
class ReplayResult:
    soc_start_mwh: Tuple[float, ...]
    soc_base_end_mwh: Tuple[float, ...]
    deliverable_reserve_mw: Tuple[float, ...]
    reserve_shortfall_mw: Tuple[float, ...]
    reserve_shortfall_mwh: Tuple[float, ...]
    base_energy_violation_mwh: Tuple[float, ...]

    @property
    def total_reserve_shortfall_mwh(self) -> float:
        return sum(self.reserve_shortfall_mwh)


def replay_base_and_single_calls(
    battery: BatterySpec,
    hybrid_energy_mw: Sequence[float],
    hybrid_reserve_mw: Sequence[float],
    *,
    tolerance: float = 1e-10,
) -> ReplayResult:
    """Replay the base SOC and test each reserve award as one isolated call.

    The replay is intentionally independent of the LP matrices.  It advances
    the base schedule sequentially.  At each period it asks how much awarded
    upward reserve could be added for the declared duration after honoring the
    full interval's base energy.  Reserve calls are evaluated individually
    from the common base trajectory; repeated-call semantics are outside this
    deterministic Phase I model.
    """

    horizon = battery.horizon
    if len(hybrid_energy_mw) != horizon:
        raise ValueError("hybrid_energy_mw length must equal horizon")
    if len(hybrid_reserve_mw) != horizon:
        raise ValueError("hybrid_reserve_mw length must equal horizon")

    energy = battery.initial_energy_mwh
    starts: list[float] = []
    ends: list[float] = []
    deliverable: list[float] = []
    shortfall: list[float] = []
    shortfall_energy: list[float] = []
    base_violations: list[float] = []

    for p_t, r_t in zip(hybrid_energy_mw, hybrid_reserve_mw):
        if p_t < -tolerance or r_t < -tolerance:
            raise ValueError("replay received a negative schedule or reserve")
        starts.append(energy)

        base_energy = max(0.0, p_t) * battery.interval_hours
        violation = max(0.0, base_energy - energy)
        base_violations.append(violation)

        energy_after_base = energy - base_energy
        energy_headroom_mw = max(
            0.0, energy_after_base / battery.reserve_duration_hours
        )
        power_headroom_mw = max(0.0, battery.power_max_mw - p_t)
        deliverable_t = min(max(0.0, r_t), energy_headroom_mw, power_headroom_mw)
        shortfall_t = max(0.0, r_t - deliverable_t)

        deliverable.append(deliverable_t)
        shortfall.append(shortfall_t)
        shortfall_energy.append(
            shortfall_t * battery.reserve_duration_hours
        )
        energy = max(0.0, energy_after_base)
        ends.append(energy)

    return ReplayResult(
        soc_start_mwh=tuple(starts),
        soc_base_end_mwh=tuple(ends),
        deliverable_reserve_mw=tuple(deliverable),
        reserve_shortfall_mw=tuple(shortfall),
        reserve_shortfall_mwh=tuple(shortfall_energy),
        base_energy_violation_mwh=tuple(base_violations),
    )
