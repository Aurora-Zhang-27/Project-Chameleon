"""Small deterministic dispatch LPs for Project Chameleon."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence, Tuple

import numpy as np
from scipy.optimize import linprog

from .contracts import BatteryGeometry, ContractKind


@dataclass(frozen=True)
class BatterySpec:
    horizon: int
    initial_energy_mwh: float
    power_max_mw: float
    interval_hours: float = 1.0
    reserve_duration_hours: float = 1.0

    def __post_init__(self) -> None:
        # Reuse the exact geometry validation.
        self.exact_geometry()

    def exact_geometry(self) -> BatteryGeometry:
        return BatteryGeometry(
            horizon=self.horizon,
            initial_energy=Fraction(str(self.initial_energy_mwh)),
            power_max=Fraction(str(self.power_max_mw)),
            interval_hours=Fraction(str(self.interval_hours)),
            reserve_duration_hours=Fraction(str(self.reserve_duration_hours)),
        )


@dataclass(frozen=True)
class DispatchCase:
    battery: BatterySpec
    load_mw: Tuple[float, ...]
    reserve_requirement_mw: Tuple[float, ...]
    thermal_power_max_mw: float = 1.0
    thermal_energy_cost_per_mwh: float = 100.0
    thermal_reserve_cost_per_mw: float = 10.0
    hybrid_energy_cost_per_mwh: float = 0.0
    hybrid_reserve_cost_per_mw: float = 0.0

    def __post_init__(self) -> None:
        horizon = self.battery.horizon
        if len(self.load_mw) != horizon:
            raise ValueError("load_mw length must equal horizon")
        if len(self.reserve_requirement_mw) != horizon:
            raise ValueError("reserve requirement length must equal horizon")
        if min(self.load_mw, default=0.0) < 0:
            raise ValueError("load must be nonnegative")
        if min(self.reserve_requirement_mw, default=0.0) < 0:
            raise ValueError("reserve requirement must be nonnegative")
        if self.thermal_power_max_mw < 0:
            raise ValueError("thermal power maximum must be nonnegative")


@dataclass(frozen=True)
class DispatchResult:
    contract: ContractKind
    objective: float
    hybrid_energy_mw: Tuple[float, ...]
    hybrid_reserve_mw: Tuple[float, ...]
    thermal_energy_mw: Tuple[float, ...]
    thermal_reserve_mw: Tuple[float, ...]
    lifted_soc_mwh: Tuple[float, ...] | None
    solver_message: str


@dataclass(frozen=True)
class _Layout:
    horizon: int
    include_soc: bool

    @property
    def p_h(self) -> slice:
        return slice(0, self.horizon)

    @property
    def r_h(self) -> slice:
        return slice(self.horizon, 2 * self.horizon)

    @property
    def p_g(self) -> slice:
        return slice(2 * self.horizon, 3 * self.horizon)

    @property
    def r_g(self) -> slice:
        return slice(3 * self.horizon, 4 * self.horizon)

    @property
    def soc(self) -> slice:
        return slice(4 * self.horizon, 5 * self.horizon + 1)

    @property
    def size(self) -> int:
        return 5 * self.horizon + 1 if self.include_soc else 4 * self.horizon


def solve_dispatch(case: DispatchCase, contract: ContractKind) -> DispatchResult:
    """Solve one deterministic operator LP.

    ``C_FULL_DET`` uses explicit lifted SOC variables.  ``C1_PREFIX`` uses the
    eliminated prefix inequalities.  ``C0_EXACT_MARGINAL`` keeps only exact
    time-local projections.
    """

    if contract is ContractKind.C0_MARKET:
        raise NotImplementedError(
            "C0_MARKET is intentionally reserved for a later scalar market baseline"
        )

    horizon = case.battery.horizon
    include_soc = contract is ContractKind.C_FULL_DET
    layout = _Layout(horizon=horizon, include_soc=include_soc)
    objective = np.zeros(layout.size)
    dt = case.battery.interval_hours
    tau = case.battery.reserve_duration_hours

    objective[layout.p_h] = case.hybrid_energy_cost_per_mwh * dt
    objective[layout.r_h] = case.hybrid_reserve_cost_per_mw
    objective[layout.p_g] = case.thermal_energy_cost_per_mwh * dt
    objective[layout.r_g] = case.thermal_reserve_cost_per_mw

    a_eq: list[np.ndarray] = []
    b_eq: list[float] = []
    a_ub: list[np.ndarray] = []
    b_ub: list[float] = []

    # Copper-plate power balance.
    for t in range(horizon):
        row = np.zeros(layout.size)
        row[layout.p_h.start + t] = 1.0
        row[layout.p_g.start + t] = 1.0
        a_eq.append(row)
        b_eq.append(case.load_mw[t])

    # Reserve requirement: -(r_h + r_g) <= -R.
    for t in range(horizon):
        row = np.zeros(layout.size)
        row[layout.r_h.start + t] = -1.0
        row[layout.r_g.start + t] = -1.0
        a_ub.append(row)
        b_ub.append(-case.reserve_requirement_mw[t])

    # Inverter and thermal headroom.
    for t in range(horizon):
        hybrid_power = np.zeros(layout.size)
        hybrid_power[layout.p_h.start + t] = 1.0
        hybrid_power[layout.r_h.start + t] = 1.0
        a_ub.append(hybrid_power)
        b_ub.append(case.battery.power_max_mw)

        thermal_power = np.zeros(layout.size)
        thermal_power[layout.p_g.start + t] = 1.0
        thermal_power[layout.r_g.start + t] = 1.0
        a_ub.append(thermal_power)
        b_ub.append(case.thermal_power_max_mw)

    if contract is ContractKind.C0_EXACT_MARGINAL:
        # Exact projection onto each time slice with all other periods free:
        # p_t * dt + r_t * tau <= E_init.
        for t in range(horizon):
            row = np.zeros(layout.size)
            row[layout.p_h.start + t] = dt
            row[layout.r_h.start + t] = tau
            a_ub.append(row)
            b_ub.append(case.battery.initial_energy_mwh)

    elif contract is ContractKind.C1_PREFIX:
        # Causal energy cuts:
        # sum_{s<=t} p_s * dt + r_t * tau <= E_init.
        for t in range(horizon):
            row = np.zeros(layout.size)
            row[layout.p_h.start : layout.p_h.start + t + 1] = dt
            row[layout.r_h.start + t] = tau
            a_ub.append(row)
            b_ub.append(case.battery.initial_energy_mwh)

    elif contract is ContractKind.C_FULL_DET:
        # e_0 = E_init.
        initial = np.zeros(layout.size)
        initial[layout.soc.start] = 1.0
        a_eq.append(initial)
        b_eq.append(case.battery.initial_energy_mwh)

        for t in range(horizon):
            # e_{t+1} = e_t - p_t * dt.
            transition = np.zeros(layout.size)
            transition[layout.soc.start + t + 1] = 1.0
            transition[layout.soc.start + t] = -1.0
            transition[layout.p_h.start + t] = dt
            a_eq.append(transition)
            b_eq.append(0.0)

            # Full call at the end of the interval:
            # p_t * dt + r_t * tau <= e_t.
            reserve_energy = np.zeros(layout.size)
            reserve_energy[layout.p_h.start + t] = dt
            reserve_energy[layout.r_h.start + t] = tau
            reserve_energy[layout.soc.start + t] = -1.0
            a_ub.append(reserve_energy)
            b_ub.append(0.0)
    else:
        raise ValueError(f"unknown contract kind: {contract}")

    result = linprog(
        objective,
        A_ub=np.asarray(a_ub) if a_ub else None,
        b_ub=np.asarray(b_ub) if b_ub else None,
        A_eq=np.asarray(a_eq) if a_eq else None,
        b_eq=np.asarray(b_eq) if b_eq else None,
        bounds=[(0.0, None)] * layout.size,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"dispatch LP failed: {result.message}")

    values = result.x
    lifted_soc = (
        tuple(float(v) for v in values[layout.soc]) if include_soc else None
    )
    return DispatchResult(
        contract=contract,
        objective=float(result.fun),
        hybrid_energy_mw=_slice_tuple(values, layout.p_h),
        hybrid_reserve_mw=_slice_tuple(values, layout.r_h),
        thermal_energy_mw=_slice_tuple(values, layout.p_g),
        thermal_reserve_mw=_slice_tuple(values, layout.r_g),
        lifted_soc_mwh=lifted_soc,
        solver_message=result.message,
    )


def _slice_tuple(values: Sequence[float], selected: slice) -> Tuple[float, ...]:
    return tuple(float(v) for v in values[selected])

