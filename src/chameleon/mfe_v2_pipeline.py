"""Registered MFE v2 construction, fitting, and evaluation pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Tuple

import numpy as np

from .mfe_v2_contracts import (
    C0Parameters,
    PVBand,
    SIGMA_LEVELS,
    c0_finalists,
    generate_latent_ar1_records,
    transform_latent_pv,
)
from .replay_v2 import replay_v2
from .truth_model import (
    ExtensiveFormResult,
    MultiStratumResult,
    SolverConfig,
    V2System,
    load_v2_system,
    solve_extensive_form,
    solve_multistratum_c0,
)


CONSTRUCTION_SEED = 2026080101
CONSTRUCTION_COUNT = 384
STRATUM_COUNT = 64
RESERVE_TIERS = (0.05, 0.20)


@dataclass(frozen=True)
class C0CandidateFit:
    parameters: C0Parameters
    mean_realized_cost: float | None
    isolated_non_delivery_rate: float | None
    accepted: bool
    solver_unresolved: bool
    solve_seconds: float
    termination: str


@dataclass(frozen=True)
class C0FitResult:
    selected: C0Parameters | None
    candidates: Tuple[C0CandidateFit, ...]
    solve_count: int


def common_construction_latent(horizon: int = 24) -> np.ndarray:
    return generate_latent_ar1_records(
        count=CONSTRUCTION_COUNT,
        horizon=horizon,
        seed=CONSTRUCTION_SEED,
    )


def construction_paths_for_cell(
    forecast_pv_mw: Sequence[float],
    sigma: float,
) -> np.ndarray:
    """Transform all 384 common construction record IDs for one cell."""

    return transform_latent_pv(
        forecast_pv_mw,
        common_construction_latent(len(forecast_pv_mw)),
        sigma,
    )


def c0_fitting_strata(
    repository_root: Path,
    *,
    duration_hours: int,
    initial_soc_fraction: float,
) -> Tuple[Tuple[V2System, ...], Tuple[np.ndarray, ...]]:
    """Build the fixed six 64-record Amendment-5 fitting strata."""

    latent = common_construction_latent()
    systems = []
    paths = []
    block = 0
    for sigma in SIGMA_LEVELS:
        for reserve_fraction in RESERVE_TIERS:
            start = block * STRATUM_COUNT
            stop = start + STRATUM_COUNT
            system = load_v2_system(
                repository_root,
                duration_hours=duration_hours,
                initial_soc_fraction=initial_soc_fraction,
                reserve_fraction=reserve_fraction,
            )
            systems.append(system)
            paths.append(
                transform_latent_pv(
                    system.forecast_pv_mw,
                    latent[start:stop],
                    sigma,
                )
            )
            block += 1
    return tuple(systems), tuple(paths)


def fit_c0(
    repository_root: Path,
    *,
    duration_hours: int,
    initial_soc_fraction: float,
    config: SolverConfig = SolverConfig(),
    candidate_limit: int | None = None,
) -> C0FitResult:
    """Execute the registered bounded C0 within-class fit."""

    systems, paths = c0_fitting_strata(
        repository_root,
        duration_hours=duration_hours,
        initial_soc_fraction=initial_soc_fraction,
    )
    candidates = c0_finalists(systems[0].battery)
    if candidate_limit is not None:
        if candidate_limit < 1:
            raise ValueError("candidate_limit must be positive")
        candidates = candidates[:candidate_limit]
    records = []
    for parameters in candidates:
        solved = solve_multistratum_c0(
            systems,
            paths,
            parameters,
            config=config,
        )
        records.append(_score_c0(parameters, systems, paths, solved))
    accepted = [
        item
        for item in records
        if item.accepted
        and item.mean_realized_cost is not None
        and item.isolated_non_delivery_rate is not None
    ]
    accepted.sort(
        key=lambda item: (
            item.mean_realized_cost,
            item.isolated_non_delivery_rate,
            item.parameters,
        )
    )
    return C0FitResult(
        selected=accepted[0].parameters if accepted else None,
        candidates=tuple(records),
        solve_count=len(records),
    )


def solve_cell_construction(
    system: V2System,
    *,
    sigma: float,
    contract: str,
    c0_parameters: C0Parameters | None = None,
    c1_band: PVBand | None = None,
    config: SolverConfig = SolverConfig(),
) -> ExtensiveFormResult:
    paths = construction_paths_for_cell(system.forecast_pv_mw, sigma)
    return solve_extensive_form(
        system,
        paths,
        contract,
        c0_parameters=c0_parameters,
        c1_band=c1_band,
        config=config,
    )


def _score_c0(
    parameters: C0Parameters,
    systems: Sequence[V2System],
    paths: Sequence[np.ndarray],
    solved: MultiStratumResult,
) -> C0CandidateFit:
    if solved.diagnostics.solver_unresolved or not solved.stage1_by_stratum:
        return C0CandidateFit(
            parameters=parameters,
            mean_realized_cost=None,
            isolated_non_delivery_rate=None,
            accepted=False,
            solver_unresolved=True,
            solve_seconds=solved.diagnostics.solve_seconds,
            termination=solved.diagnostics.termination,
        )
    costs = []
    failures = 0
    total = 0
    for system, stage1, stratum_paths, decisions in zip(
        systems,
        solved.stage1_by_stratum,
        paths,
        solved.scenarios_by_stratum,
    ):
        for path, decision in zip(stratum_paths, decisions):
            replay = replay_v2(system, stage1, decision, path)
            costs.append(replay.replay_cost)
            total += 1
            if (
                not replay.physically_valid
                or max(replay.activation.shortfall_up_mw) > 1e-6
                or max(replay.activation.shortfall_down_mw) > 1e-6
            ):
                failures += 1
    rate = failures / total
    return C0CandidateFit(
        parameters=parameters,
        mean_realized_cost=float(np.mean(costs)),
        isolated_non_delivery_rate=rate,
        accepted=rate <= 0.01,
        solver_unresolved=False,
        solve_seconds=solved.diagnostics.solve_seconds,
        termination=solved.diagnostics.termination,
    )
