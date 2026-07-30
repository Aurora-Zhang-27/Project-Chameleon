"""Closed-form v2/v3 C1 non-emptiness and capacity certificates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

from .mfe_v2_contracts import PVBand
from .truth_model import V2BatterySpec


@dataclass(frozen=True)
class V2C1Certificate:
    band_width_mwh: float
    discharge_allocation_capacity_mwh: float
    charge_allocation_capacity_mwh: float
    total_allocation_capacity_mwh: float
    margin_mwh: float
    nonempty: bool


@dataclass(frozen=True)
class V3C1Certificate:
    reference_schedule_mw: Tuple[float, ...]
    reference_nonempty: bool
    max_up_reserve_mw: float
    max_down_reserve_mw: float
    max_two_sided_reserve_mw: float


def certify_v2_c1_nonempty(
    battery: V2BatterySpec,
    band: PVBand,
    *,
    tolerance: float = 1e-9,
) -> V2C1Certificate:
    """Exact zero-reserve feasibility test for the registered v2 envelope.

    Eliminating ``h_t`` gives nonnegative allocations ``y_t=x_dis`` and
    ``z_t=x_ch`` with ``y_t+z_t >= upper_t-lower_t``.  Since all prefix
    increments are nonnegative, the final prefix and terminal cut are
    sufficient.  Feasibility is therefore equivalent to total band width
    not exceeding the sum of the raw discharge- and charge-side allocation
    capacities below.
    """

    width = sum(
        max(0.0, upper - lower)
        for lower, upper in zip(band.lower_mw, band.upper_mw)
    ) * battery.interval_hours
    discharge_energy_budget = max(
        0.0, battery.initial_energy_mwh - battery.terminal_energy_mwh
    )
    discharge_allocation = (
        battery.discharge_efficiency
        * discharge_energy_budget
        / battery.interval_hours
    )
    charge_allocation = (
        max(
            0.0,
            battery.energy_capacity_mwh - battery.initial_energy_mwh,
        )
        / battery.charge_efficiency
        / battery.interval_hours
    )
    total = discharge_allocation + charge_allocation
    margin = total - width
    return V2C1Certificate(
        band_width_mwh=width,
        discharge_allocation_capacity_mwh=discharge_allocation,
        charge_allocation_capacity_mwh=charge_allocation,
        total_allocation_capacity_mwh=total,
        margin_mwh=margin,
        nonempty=margin >= -tolerance,
    )


def certify_v3_reference_and_reserve(
    battery: V2BatterySpec,
    band: PVBand,
    *,
    inverter_limit_mw: float = 50.0,
    tolerance: float = 1e-9,
) -> V3C1Certificate:
    """Certify h=lower-PV, zero-reserve feasibility and reserve capacity.

    At the reference schedule ``x_dis=0``.  Isolated upward reserve is
    limited by discharge power and initial energy.  Registered downward
    reserve first uses charging and then PV curtailment; at the night-time
    minimum lower-PV value, charging headroom is the binding closed-form
    certificate when it is below one full 50 MW call.
    """

    reference = tuple(float(value) for value in band.lower_mw)
    tau = battery.reserve_duration_hours
    up_energy = (
        battery.discharge_efficiency
        * battery.initial_energy_mwh
        / tau
    )
    max_up = min(inverter_limit_mw, up_energy)

    headroom = battery.energy_capacity_mwh - battery.initial_energy_mwh
    full_charge_energy = (
        battery.charge_efficiency * battery.charge_max_mw * tau
    )
    if headroom + tolerance < full_charge_energy:
        max_down = min(
            inverter_limit_mw,
            headroom / (battery.charge_efficiency * tau),
        )
    else:
        max_down = min(
            inverter_limit_mw,
            battery.charge_max_mw + min(reference),
        )
    return V3C1Certificate(
        reference_schedule_mw=reference,
        reference_nonempty=True,
        max_up_reserve_mw=max_up,
        max_down_reserve_mw=max_down,
        max_two_sided_reserve_mw=min(max_up, max_down),
    )
