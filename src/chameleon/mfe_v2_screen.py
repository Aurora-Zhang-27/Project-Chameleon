"""Closed-form, pre-run sufficiency screen for MFE v2.

This module performs no optimization and draws no scenarios.  It reproduces
the capacity rescaling and the 54-cell battery-alone sequential energy labels
frozen in the v2 pre-registration.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Tuple

from .mfe_harness import load_frozen_deterministic_case


RAW_LOAD_SCALE = 0.15
TOTAL_THERMAL_CAPACITY_MW = 636.0
BATTERY_DISCHARGE_CAPACITY_MW = 50.0
HIGH_RESERVE_TIER = 0.20
RESERVE_MARGIN_MULTIPLIER = 1.10
DISCHARGE_EFFICIENCY = 0.95
CALL_DURATION_HOURS = 0.5
STRESS_PERIODS_ZERO_BASED = (17, 18)


@dataclass(frozen=True)
class V2SufficiencyRow:
    cell_id: str
    pv_sigma: float
    duration_h: int
    initial_soc_fraction: float
    reserve_tier: float
    load_scale: float
    scaled_peak_mw: float
    capacity_mw: float
    capacity_required_mw: float
    capacity_pass: bool
    initial_energy_mwh: float
    pv_low_stress_mwh: float
    sequential_energy_lb_mwh: float
    battery_alone_energy_pass: bool

    @property
    def energy_label(self) -> str:
        return (
            "battery-alone adequate"
            if self.battery_alone_energy_pass
            else "system-recourse required"
        )


def build_v2_sufficiency_screen(
    repository_root: Path,
) -> Tuple[V2SufficiencyRow, ...]:
    case = load_frozen_deterministic_case(repository_root)
    raw_load = tuple(value / RAW_LOAD_SCALE for value in case.load_mw)
    raw_peak = max(raw_load)
    capacity = TOTAL_THERMAL_CAPACITY_MW + BATTERY_DISCHARGE_CAPACITY_MW
    load_scale = min(
        RAW_LOAD_SCALE,
        capacity
        / (
            (1.0 + RESERVE_MARGIN_MULTIPLIER * HIGH_RESERVE_TIER)
            * raw_peak
        ),
    )
    scaled_load = tuple(value * load_scale for value in raw_load)
    scaled_peak = max(scaled_load)

    rows = []
    for index, (sigma, duration, soc, tier) in enumerate(
        product(
            (0.03, 0.08, 0.15),
            (1, 2, 4),
            (0.25, 0.50, 0.75),
            (0.05, 0.20),
        ),
        start=1,
    ):
        initial_energy = 50.0 * duration * soc
        pv_low_stress = 0.0
        sequential_energy = (
            CALL_DURATION_HOURS
            * tier
            * sum(scaled_load[period] for period in STRESS_PERIODS_ZERO_BASED)
            / DISCHARGE_EFFICIENCY
        )
        capacity_required = (1.0 + tier) * scaled_peak
        rows.append(
            V2SufficiencyRow(
                cell_id=f"V2-{index:02d}",
                pv_sigma=sigma,
                duration_h=duration,
                initial_soc_fraction=soc,
                reserve_tier=tier,
                load_scale=load_scale,
                scaled_peak_mw=scaled_peak,
                capacity_mw=capacity,
                capacity_required_mw=capacity_required,
                capacity_pass=capacity + 1e-10 >= capacity_required,
                initial_energy_mwh=initial_energy,
                pv_low_stress_mwh=pv_low_stress,
                sequential_energy_lb_mwh=sequential_energy,
                battery_alone_energy_pass=(
                    initial_energy + pv_low_stress + 1e-10
                    >= sequential_energy
                ),
            )
        )
    return tuple(rows)

