"""Deterministic 24-hour implementation-gate harness for the MFE.

This module intentionally stays inside the already proved Phase-I physical
semantics: lossless, discharge-only storage; must-take deterministic PV; and
isolated upward-reserve calls.  It is a reconciliation harness, not the
stochastic 54-cell MFE and not a new truth model.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, Sequence, Tuple

import numpy as np
from scipy.optimize import linprog

from .contracts import ContractKind
from .model import BatterySpec
from .replay import ReplayResult, replay_base_and_single_calls


@dataclass(frozen=True)
class ThermalUnit:
    uid: str
    power_min_mw: float
    power_max_mw: float
    ramp_mw_per_hour: float
    segment_widths_mw: Tuple[float, ...]
    segment_costs_per_mwh: Tuple[float, ...]
    reserve_cost_per_mw: float = 5.0

    def __post_init__(self) -> None:
        if self.power_min_mw < 0 or self.power_max_mw < self.power_min_mw:
            raise ValueError("invalid thermal power limits")
        if self.ramp_mw_per_hour < 0:
            raise ValueError("ramp must be nonnegative")
        if len(self.segment_widths_mw) != len(self.segment_costs_per_mwh):
            raise ValueError("segment widths and costs must have equal length")
        if any(width < 0 for width in self.segment_widths_mw):
            raise ValueError("segment widths must be nonnegative")
        headroom = self.power_max_mw - self.power_min_mw
        if abs(sum(self.segment_widths_mw) - headroom) > 1e-6:
            raise ValueError("segments must span the range above minimum")


@dataclass(frozen=True)
class DeterministicMFECase:
    study_date: date
    load_mw: Tuple[float, ...]
    must_take_pv_mw: Tuple[float, ...]
    upward_reserve_requirement_mw: Tuple[float, ...]
    battery: BatterySpec
    thermal_units: Tuple[ThermalUnit, ...]
    source_commit: str
    scope: str = "phase_i_lossless_must_take_upward_only"

    def __post_init__(self) -> None:
        horizon = self.battery.horizon
        for name, values in (
            ("load", self.load_mw),
            ("PV", self.must_take_pv_mw),
            ("reserve", self.upward_reserve_requirement_mw),
        ):
            if len(values) != horizon:
                raise ValueError(f"{name} trajectory length must equal horizon")
            if any(value < -1e-9 for value in values):
                raise ValueError(f"{name} trajectory must be nonnegative")
        if not self.thermal_units:
            raise ValueError("at least one thermal unit is required")


@dataclass(frozen=True)
class DeterministicMFEResult:
    contract: ContractKind
    objective: float
    battery_injection_mw: Tuple[float, ...]
    battery_upward_reserve_mw: Tuple[float, ...]
    thermal_dispatch_mw: Tuple[Tuple[float, ...], ...]
    thermal_upward_reserve_mw: Tuple[Tuple[float, ...], ...]
    lifted_soc_mwh: Tuple[float, ...] | None
    replay: ReplayResult
    solver_message: str


@dataclass(frozen=True)
class _Layout:
    horizon: int
    unit_segment_counts: Tuple[int, ...]
    include_soc: bool

    @property
    def battery_power(self) -> slice:
        return slice(0, self.horizon)

    @property
    def battery_reserve(self) -> slice:
        return slice(self.horizon, 2 * self.horizon)

    @property
    def segment_start(self) -> int:
        return 2 * self.horizon

    @property
    def total_segments(self) -> int:
        return sum(self.unit_segment_counts)

    @property
    def thermal_reserve_start(self) -> int:
        return self.segment_start + self.total_segments * self.horizon

    @property
    def soc_start(self) -> int:
        return self.thermal_reserve_start + len(self.unit_segment_counts) * self.horizon

    @property
    def size(self) -> int:
        return self.soc_start + (self.horizon + 1 if self.include_soc else 0)

    def segment_index(self, unit: int, segment: int, period: int) -> int:
        preceding = sum(self.unit_segment_counts[:unit])
        flat_segment = preceding + segment
        return self.segment_start + flat_segment * self.horizon + period

    def thermal_reserve_index(self, unit: int, period: int) -> int:
        return self.thermal_reserve_start + unit * self.horizon + period

    def soc_index(self, period: int) -> int:
        if not self.include_soc:
            raise ValueError("SOC variables are not present")
        return self.soc_start + period


def load_frozen_deterministic_case(repository_root: Path) -> DeterministicMFECase:
    """Load the pre-declared RTS-GMLC day and deterministic scale factors."""

    data = repository_root / "data" / "external" / "rts_gmlc"
    selected_date = date(2020, 3, 30)
    load_scale = 0.15
    pv_nameplate_mw = 200.0

    load = _read_period_rows(
        data / "DAY_AHEAD_regional_Load.csv",
        selected_date,
        value_columns=("1", "2", "3"),
    )
    raw_pv = _read_period_rows(
        data / "DAY_AHEAD_pv.csv",
        selected_date,
        value_columns=None,
    )
    raw_pv_peak = max(raw_pv)
    if raw_pv_peak <= 0:
        raise ValueError("selected study day has no PV production")

    scaled_load = tuple(load_scale * value for value in load)
    scaled_pv = tuple(pv_nameplate_mw * value / raw_pv_peak for value in raw_pv)
    reserve = tuple(0.05 * value for value in scaled_load)
    units = _load_thermal_units(data / "gen.csv")

    return DeterministicMFECase(
        study_date=selected_date,
        load_mw=scaled_load,
        must_take_pv_mw=scaled_pv,
        upward_reserve_requirement_mw=reserve,
        battery=BatterySpec(
            horizon=24,
            initial_energy_mwh=100.0,
            power_max_mw=50.0,
            interval_hours=1.0,
            reserve_duration_hours=0.5,
        ),
        thermal_units=units,
        source_commit="3ece0d3725c844056132393ee252b3083dd4eab4",
    )


def solve_deterministic_mfe_case(
    case: DeterministicMFECase, contract: ContractKind
) -> DeterministicMFEResult:
    """Solve one of the three Phase-I information lines and replay it."""

    if contract not in {
        ContractKind.C0_EXACT_MARGINAL,
        ContractKind.C1_PREFIX,
        ContractKind.C_FULL_DET,
    }:
        raise ValueError("the gate harness supports exactly C0, C1, and C_full")

    horizon = case.battery.horizon
    include_soc = contract is ContractKind.C_FULL_DET
    layout = _Layout(
        horizon,
        tuple(len(unit.segment_widths_mw) for unit in case.thermal_units),
        include_soc,
    )
    objective = np.zeros(layout.size)
    objective[layout.battery_reserve] = 0.0

    bounds: list[Tuple[float | None, float | None]] = [
        (0.0, None)
    ] * layout.size
    for unit_index, unit in enumerate(case.thermal_units):
        for segment_index, (width, cost) in enumerate(
            zip(unit.segment_widths_mw, unit.segment_costs_per_mwh)
        ):
            for period in range(horizon):
                index = layout.segment_index(unit_index, segment_index, period)
                objective[index] = cost
                bounds[index] = (0.0, width)
        for period in range(horizon):
            index = layout.thermal_reserve_index(unit_index, period)
            objective[index] = unit.reserve_cost_per_mw
            bounds[index] = (0.0, None)

    bounds[layout.battery_power] = [(0.0, case.battery.power_max_mw)] * horizon
    bounds[layout.battery_reserve] = [(0.0, case.battery.power_max_mw)] * horizon
    if include_soc:
        for period in range(horizon + 1):
            bounds[layout.soc_index(period)] = (
                0.0,
                case.battery.initial_energy_mwh,
            )

    a_eq: list[np.ndarray] = []
    b_eq: list[float] = []
    a_ub: list[np.ndarray] = []
    b_ub: list[float] = []
    thermal_minimum = sum(unit.power_min_mw for unit in case.thermal_units)

    for period in range(horizon):
        balance = np.zeros(layout.size)
        balance[layout.battery_power.start + period] = 1.0
        for unit_index, unit in enumerate(case.thermal_units):
            for segment_index in range(len(unit.segment_widths_mw)):
                balance[layout.segment_index(unit_index, segment_index, period)] = 1.0
        a_eq.append(balance)
        b_eq.append(
            case.load_mw[period]
            - case.must_take_pv_mw[period]
            - thermal_minimum
        )

        reserve = np.zeros(layout.size)
        reserve[layout.battery_reserve.start + period] = -1.0
        for unit_index in range(len(case.thermal_units)):
            reserve[layout.thermal_reserve_index(unit_index, period)] = -1.0
        a_ub.append(reserve)
        b_ub.append(-case.upward_reserve_requirement_mw[period])

        battery_headroom = np.zeros(layout.size)
        battery_headroom[layout.battery_power.start + period] = 1.0
        battery_headroom[layout.battery_reserve.start + period] = 1.0
        a_ub.append(battery_headroom)
        b_ub.append(case.battery.power_max_mw)

        for unit_index, unit in enumerate(case.thermal_units):
            headroom = np.zeros(layout.size)
            for segment_index in range(len(unit.segment_widths_mw)):
                headroom[
                    layout.segment_index(unit_index, segment_index, period)
                ] = 1.0
            headroom[layout.thermal_reserve_index(unit_index, period)] = 1.0
            a_ub.append(headroom)
            b_ub.append(unit.power_max_mw - unit.power_min_mw)

    for period in range(1, horizon):
        for unit_index, unit in enumerate(case.thermal_units):
            upward_ramp = np.zeros(layout.size)
            for segment_index in range(len(unit.segment_widths_mw)):
                upward_ramp[
                    layout.segment_index(unit_index, segment_index, period)
                ] = 1.0
                upward_ramp[
                    layout.segment_index(unit_index, segment_index, period - 1)
                ] = -1.0
            a_ub.append(upward_ramp)
            b_ub.append(unit.ramp_mw_per_hour)
            a_ub.append(-upward_ramp)
            b_ub.append(unit.ramp_mw_per_hour)

    dt = case.battery.interval_hours
    tau = case.battery.reserve_duration_hours
    if contract is ContractKind.C0_EXACT_MARGINAL:
        for period in range(horizon):
            local = np.zeros(layout.size)
            local[layout.battery_power.start + period] = dt
            local[layout.battery_reserve.start + period] = tau
            a_ub.append(local)
            b_ub.append(case.battery.initial_energy_mwh)
    elif contract is ContractKind.C1_PREFIX:
        for period in range(horizon):
            prefix = np.zeros(layout.size)
            prefix[
                layout.battery_power.start : layout.battery_power.start + period + 1
            ] = dt
            prefix[layout.battery_reserve.start + period] = tau
            a_ub.append(prefix)
            b_ub.append(case.battery.initial_energy_mwh)
    else:
        initial = np.zeros(layout.size)
        initial[layout.soc_index(0)] = 1.0
        a_eq.append(initial)
        b_eq.append(case.battery.initial_energy_mwh)
        for period in range(horizon):
            transition = np.zeros(layout.size)
            transition[layout.soc_index(period + 1)] = 1.0
            transition[layout.soc_index(period)] = -1.0
            transition[layout.battery_power.start + period] = dt
            a_eq.append(transition)
            b_eq.append(0.0)

            call = np.zeros(layout.size)
            call[layout.battery_reserve.start + period] = tau
            call[layout.soc_index(period + 1)] = -1.0
            a_ub.append(call)
            b_ub.append(0.0)

    result = linprog(
        objective,
        A_ub=np.asarray(a_ub),
        b_ub=np.asarray(b_ub),
        A_eq=np.asarray(a_eq),
        b_eq=np.asarray(b_eq),
        bounds=bounds,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"deterministic MFE gate solve failed: {result.message}")

    values = result.x
    battery_power = tuple(float(value) for value in values[layout.battery_power])
    battery_reserve = tuple(float(value) for value in values[layout.battery_reserve])
    thermal_dispatch: list[Tuple[float, ...]] = []
    thermal_reserve: list[Tuple[float, ...]] = []
    for unit_index, unit in enumerate(case.thermal_units):
        dispatch = []
        reserve = []
        for period in range(horizon):
            above_minimum = sum(
                values[layout.segment_index(unit_index, segment_index, period)]
                for segment_index in range(len(unit.segment_widths_mw))
            )
            dispatch.append(unit.power_min_mw + float(above_minimum))
            reserve.append(
                float(values[layout.thermal_reserve_index(unit_index, period)])
            )
        thermal_dispatch.append(tuple(dispatch))
        thermal_reserve.append(tuple(reserve))

    replay = replay_base_and_single_calls(
        case.battery, battery_power, battery_reserve
    )
    lifted_soc = (
        tuple(float(values[layout.soc_index(period)]) for period in range(horizon + 1))
        if include_soc
        else None
    )
    return DeterministicMFEResult(
        contract=contract,
        objective=float(result.fun),
        battery_injection_mw=battery_power,
        battery_upward_reserve_mw=battery_reserve,
        thermal_dispatch_mw=tuple(thermal_dispatch),
        thermal_upward_reserve_mw=tuple(thermal_reserve),
        lifted_soc_mwh=lifted_soc,
        replay=replay,
        solver_message=result.message,
    )


def _read_period_rows(
    path: Path,
    selected_date: date,
    value_columns: Sequence[str] | None,
) -> Tuple[float, ...]:
    values: Dict[int, float] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row_date = date(int(row["Year"]), int(row["Month"]), int(row["Day"]))
            if row_date != selected_date:
                continue
            columns = (
                tuple(value_columns)
                if value_columns is not None
                else tuple(reader.fieldnames or ())[4:]
            )
            values[int(row["Period"])] = sum(float(row[name]) for name in columns)
    if set(values) != set(range(1, 25)):
        raise ValueError(f"expected 24 periods for {selected_date} in {path}")
    return tuple(values[period] for period in range(1, 25))


def _load_thermal_units(path: Path) -> Tuple[ThermalUnit, ...]:
    selected = ("123_STEAM_3", "115_STEAM_3", "101_STEAM_3", "113_CT_1")
    rows: Dict[str, Dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["GEN UID"] in selected:
                rows[row["GEN UID"]] = row
    if set(rows) != set(selected):
        raise ValueError("one or more frozen thermal units are absent")

    units = []
    for uid in selected:
        row = rows[uid]
        p_min = float(row["PMin MW"])
        p_max = float(row["PMax MW"])
        fractions = [
            float(row["Output_pct_1"]),
            float(row["Output_pct_2"]),
            float(row["Output_pct_3"]),
        ]
        breakpoints = [p_min] + [p_max * fraction for fraction in fractions]
        widths = tuple(
            max(0.0, upper - lower)
            for lower, upper in zip(breakpoints[:-1], breakpoints[1:])
        )
        fuel_price = float(row["Fuel Price $/MMBTU"])
        vom = float(row["VOM"])
        heat_rates = [
            float(row["HR_incr_1"]),
            float(row["HR_incr_2"]),
            float(row["HR_incr_3"]),
        ]
        costs = tuple(fuel_price * rate / 1000.0 + vom for rate in heat_rates)
        units.append(
            ThermalUnit(
                uid=uid,
                power_min_mw=p_min,
                power_max_mw=p_max,
                ramp_mw_per_hour=60.0 * float(row["Ramp Rate MW/Min"]),
                segment_widths_mw=widths,
                segment_costs_per_mwh=costs,
            )
        )
    return tuple(units)

