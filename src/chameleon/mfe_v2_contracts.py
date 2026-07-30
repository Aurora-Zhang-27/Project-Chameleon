"""Pure-arithmetic MFE v2 scenario bands and contract constructions."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Sequence, Tuple

import numpy as np

from .truth_model import V2BatterySpec


SIGMA_LEVELS = (0.03, 0.08, 0.15)
BAND_SEED = 2026080105


@dataclass(frozen=True)
class PVBand:
    sigma: float
    lower_quantile: float
    upper_quantile: float
    lower_mw: Tuple[float, ...]
    upper_mw: Tuple[float, ...]
    path_count: int
    seed: int
    path_digest_sha256: str


@dataclass(frozen=True, order=True)
class C0Parameters:
    power_cap_mw: float
    up_reserve_cap_mw: float
    down_reserve_cap_mw: float
    ramp_cap_mw_per_hour: float


@dataclass(frozen=True)
class C1Evaluation:
    accepted: bool
    discharge_prefix_mwh: Tuple[float, ...]
    charge_prefix_mwh: Tuple[float, ...]
    violations: Tuple[str, ...]


def generate_pv_paths_by_level(
    forecast_pv_mw: Sequence[float],
    *,
    count_per_level: int,
    seed: int,
    sigma_levels: Sequence[float] = SIGMA_LEVELS,
) -> Dict[float, np.ndarray]:
    """Generate registered two-sided AR(1) paths from one ordered RNG stream."""

    if count_per_level < 1:
        raise ValueError("count_per_level must be positive")
    forecast = np.asarray(forecast_pv_mw, dtype=float)
    if forecast.ndim != 1:
        raise ValueError("forecast must be one-dimensional")
    generator = np.random.default_rng(seed)
    result: Dict[float, np.ndarray] = {}
    ar_scale = math.sqrt(1.0 - 0.8**2)
    for sigma in sigma_levels:
        if float(sigma) not in SIGMA_LEVELS:
            raise ValueError("unregistered sigma level")
        innovations = generator.standard_normal((count_per_level, len(forecast)))
        latent = np.empty_like(innovations)
        latent[:, 0] = innovations[:, 0]
        for t in range(1, len(forecast)):
            latent[:, t] = 0.8 * latent[:, t - 1] + ar_scale * innovations[:, t]
        result[float(sigma)] = np.clip(
            forecast[None, :] * (1.0 + float(sigma) * latent),
            0.0,
            200.0,
        )
    return result


def generate_latent_ar1_records(
    *,
    count: int,
    horizon: int,
    seed: int,
) -> np.ndarray:
    """Generate the Amendment-5 common latent construction records."""

    if count < 1 or horizon < 1:
        raise ValueError("count and horizon must be positive")
    generator = np.random.default_rng(seed)
    innovations = generator.standard_normal((count, horizon))
    latent = np.empty_like(innovations)
    latent[:, 0] = innovations[:, 0]
    ar_scale = math.sqrt(1.0 - 0.8**2)
    for t in range(1, horizon):
        latent[:, t] = 0.8 * latent[:, t - 1] + ar_scale * innovations[:, t]
    return latent


def transform_latent_pv(
    forecast_pv_mw: Sequence[float],
    latent_records: np.ndarray,
    sigma: float,
) -> np.ndarray:
    """Transform common latent record IDs at one registered sigma."""

    if sigma not in SIGMA_LEVELS:
        raise ValueError("unregistered sigma level")
    forecast = np.asarray(forecast_pv_mw, dtype=float)
    latent = np.asarray(latent_records, dtype=float)
    if latent.ndim != 2 or latent.shape[1] != len(forecast):
        raise ValueError("latent records have the wrong shape")
    return np.clip(forecast[None, :] * (1.0 + sigma * latent), 0.0, 200.0)


def build_registered_c1_bands(
    forecast_pv_mw: Sequence[float],
    *,
    count_per_level: int = 2_000,
    seed: int = BAND_SEED,
) -> Dict[str, Dict[float, PVBand]]:
    """Build both registered 1/99 and 5/95 nodewise PV bands."""

    paths = generate_pv_paths_by_level(
        forecast_pv_mw,
        count_per_level=count_per_level,
        seed=seed,
    )
    result: Dict[str, Dict[float, PVBand]] = {"1/99": {}, "5/95": {}}
    for sigma in SIGMA_LEVELS:
        values = paths[sigma]
        digest = hashlib.sha256(values.tobytes(order="C")).hexdigest()
        for label, lower_q, upper_q in (
            ("1/99", 0.01, 0.99),
            ("5/95", 0.05, 0.95),
        ):
            lower = np.quantile(values, lower_q, axis=0, method="linear")
            upper = np.quantile(values, upper_q, axis=0, method="linear")
            result[label][sigma] = PVBand(
                sigma=sigma,
                lower_quantile=lower_q,
                upper_quantile=upper_q,
                lower_mw=tuple(float(value) for value in lower),
                upper_mw=tuple(float(value) for value in upper),
                path_count=count_per_level,
                seed=seed,
                path_digest_sha256=digest,
            )
    return result


def evaluate_c1_envelope(
    battery: V2BatterySpec,
    scheduled_hybrid_injection_mw: Sequence[float],
    upward_reserve_mw: Sequence[float],
    downward_reserve_mw: Sequence[float],
    band: PVBand,
    *,
    tolerance: float = 1e-9,
) -> C1Evaluation:
    """Evaluate the registered two-sided lossy inner prefix and terminal cut."""

    h = tuple(float(value) for value in scheduled_hybrid_injection_mw)
    rup = tuple(float(value) for value in upward_reserve_mw)
    rdn = tuple(float(value) for value in downward_reserve_mw)
    if not (len(h) == len(rup) == len(rdn) == len(band.lower_mw)):
        raise ValueError("C1 trajectories and band must have equal length")
    if any(value < -tolerance for value in rup + rdn):
        raise ValueError("reserve must be nonnegative")

    dt = battery.interval_hours
    tau = battery.reserve_duration_hours
    eta_c = battery.charge_efficiency
    eta_d = battery.discharge_efficiency
    discharge_budget = battery.initial_energy_mwh
    charge_budget = battery.energy_capacity_mwh - battery.initial_energy_mwh
    terminal_budget = battery.initial_energy_mwh - battery.terminal_energy_mwh
    cumulative_discharge = 0.0
    cumulative_charge = 0.0
    dis_prefix = []
    ch_prefix = []
    violations = []
    for t, (schedule, low, high) in enumerate(
        zip(h, band.lower_mw, band.upper_mw)
    ):
        x_dis = max(0.0, schedule - low)
        x_ch = max(0.0, high - schedule)
        cumulative_discharge += x_dis * dt / eta_d
        cumulative_charge += eta_c * x_ch * dt
        dis_value = cumulative_discharge + rup[t] * tau / eta_d
        ch_value = cumulative_charge + eta_c * rdn[t] * tau
        dis_prefix.append(dis_value)
        ch_prefix.append(ch_value)
        if dis_value > discharge_budget + tolerance:
            violations.append(f"upper prefix at hour {t + 1}")
        if ch_value > charge_budget + tolerance:
            violations.append(f"lower prefix at hour {t + 1}")
    if cumulative_discharge > terminal_budget + tolerance:
        violations.append("terminal cut")
    return C1Evaluation(
        accepted=not violations,
        discharge_prefix_mwh=tuple(dis_prefix),
        charge_prefix_mwh=tuple(ch_prefix),
        violations=tuple(violations),
    )


def evaluate_c1_v3_envelope(
    battery: V2BatterySpec,
    scheduled_hybrid_injection_mw: Sequence[float],
    upward_reserve_mw: Sequence[float],
    downward_reserve_mw: Sequence[float],
    band: PVBand,
    *,
    tolerance: float = 1e-9,
) -> C1Evaluation:
    """Evaluate the final recourse-aware v3 C1 inner envelope.

    Upper-PV deviations are assigned to priced curtailment and therefore do
    not consume battery charging headroom.  At the lower-PV boundary,
    downward response is supplied by reducing discharge, charging, and then
    curtailing PV, in that registered order.
    """

    h = tuple(float(value) for value in scheduled_hybrid_injection_mw)
    rup = tuple(float(value) for value in upward_reserve_mw)
    rdn = tuple(float(value) for value in downward_reserve_mw)
    if not (len(h) == len(rup) == len(rdn) == len(band.lower_mw)):
        raise ValueError("C1 trajectories and band must have equal length")
    if any(value < -tolerance for value in rup + rdn):
        raise ValueError("reserve must be nonnegative")
    if any(value < -tolerance for value in h):
        return C1Evaluation(False, tuple(), tuple(), ("negative hybrid injection",))

    dt = battery.interval_hours
    tau = battery.reserve_duration_hours
    eta_c = battery.charge_efficiency
    eta_d = battery.discharge_efficiency
    terminal_budget = battery.initial_energy_mwh - battery.terminal_energy_mwh
    charge_headroom = battery.energy_capacity_mwh - battery.initial_energy_mwh
    cumulative_discharge = 0.0
    dis_prefix = []
    charged_on_call = []
    violations = []
    for t, (scheduled, r_up, r_down, lower_pv) in enumerate(
        zip(h, rup, rdn, band.lower_mw)
    ):
        x_dis = max(scheduled - lower_pv, 0.0)
        cumulative_discharge += x_dis * dt / eta_d
        dis_prefix.append(cumulative_discharge)
        if cumulative_discharge + r_up * tau / eta_d > (
            battery.initial_energy_mwh + tolerance
        ):
            violations.append(f"discharge prefix at hour {t + 1}")

        if r_down > (
            x_dis + battery.charge_max_mw + lower_pv + tolerance
        ):
            violations.append(f"downward power at hour {t + 1}")
        charge_increment = min(
            max(r_down - x_dis, 0.0),
            battery.charge_max_mw,
        )
        call_energy = eta_c * charge_increment * tau
        charged_on_call.append(call_energy)
        if call_energy > charge_headroom + tolerance:
            violations.append(f"downward energy at hour {t + 1}")

    if cumulative_discharge > terminal_budget + tolerance:
        violations.append("terminal discharge budget")
    return C1Evaluation(
        accepted=not violations,
        discharge_prefix_mwh=tuple(dis_prefix),
        charge_prefix_mwh=tuple(charged_on_call),
        violations=tuple(violations),
    )


def c0_finalists(
    battery: V2BatterySpec,
    *,
    cap: int = 12,
) -> Tuple[C0Parameters, ...]:
    """Apply the frozen 10 MW coarse screen and 5 MW refinement."""

    coarse = []
    for power in range(0, 51, 10):
        for rup in range(0, 51, 10):
            for rdn in range(0, 51, 10):
                for ramp in range(10, 51, 10):
                    item = C0Parameters(float(power), float(rup), float(rdn), float(ramp))
                    if _inverter_filter(item):
                        coarse.append(item)
    retained = _cap(_pareto(coarse, battery), battery, cap)
    neighborhood = set()
    for item in retained:
        coordinates = (
            item.power_cap_mw,
            item.up_reserve_cap_mw,
            item.down_reserve_cap_mw,
            item.ramp_cap_mw_per_hour,
        )
        options = [
            tuple(value + offset for offset in (-5.0, 0.0, 5.0))
            for value in coordinates
        ]
        for power in options[0]:
            for rup in options[1]:
                for rdn in options[2]:
                    for ramp in options[3]:
                        candidate = C0Parameters(power, rup, rdn, ramp)
                        if (
                            0.0 <= power <= 50.0
                            and 0.0 <= rup <= 50.0
                            and 0.0 <= rdn <= 50.0
                            and 10.0 <= ramp <= 50.0
                            and _inverter_filter(candidate)
                        ):
                            neighborhood.add(candidate)
    return tuple(_cap(_pareto(neighborhood, battery), battery, cap))


def _inverter_filter(item: C0Parameters) -> bool:
    return (
        item.power_cap_mw + item.up_reserve_cap_mw <= 50.0
        and item.power_cap_mw + item.down_reserve_cap_mw <= 50.0
    )


def _proxy(
    item: C0Parameters, battery: V2BatterySpec
) -> Tuple[float, float]:
    denominator_up = max(battery.initial_energy_mwh, 1e-9)
    denominator_down = max(
        battery.energy_capacity_mwh - battery.initial_energy_mwh, 1e-9
    )
    duty_up = (
        4.0 * item.power_cap_mw
        + battery.reserve_duration_hours * item.up_reserve_cap_mw
    ) / (battery.discharge_efficiency * denominator_up)
    duty_down = battery.charge_efficiency * (
        4.0 * item.power_cap_mw
        + battery.reserve_duration_hours * item.down_reserve_cap_mw
    ) / denominator_down
    risk = max(duty_up, duty_down)
    value = sum(
        math.log1p(component)
        for component in (
            item.power_cap_mw,
            item.up_reserve_cap_mw,
            item.down_reserve_cap_mw,
            item.ramp_cap_mw_per_hour,
        )
    )
    return value, risk


def _pareto(
    candidates: Iterable[C0Parameters],
    battery: V2BatterySpec,
) -> list[C0Parameters]:
    items = sorted(set(candidates))
    proxies = {item: _proxy(item, battery) for item in items}
    survivors = []
    for item in items:
        value, risk = proxies[item]
        dominated = False
        for other in items:
            if other == item:
                continue
            other_value, other_risk = proxies[other]
            if (
                other_value >= value
                and other_risk <= risk
                and (other_value > value or other_risk < risk)
            ):
                dominated = True
                break
        if not dominated:
            survivors.append(item)
    return survivors


def _cap(
    candidates: Iterable[C0Parameters],
    battery: V2BatterySpec,
    cap: int,
) -> list[C0Parameters]:
    items = list(candidates)
    if cap < 1:
        raise ValueError("cap must be positive")
    # Sort exactly as registered: increasing value, risk, then theta.
    items.sort(key=lambda item: (*_proxy(item, battery), item))
    if len(items) <= cap:
        return items
    indices = []
    for j in range(cap):
        raw = j * (len(items) - 1) / (cap - 1)
        index = int(math.floor(raw + 0.5))
        if index not in indices:
            indices.append(index)
    return [items[index] for index in indices]
