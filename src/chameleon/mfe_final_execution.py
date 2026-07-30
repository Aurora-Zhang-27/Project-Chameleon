"""Final, preregistered MFE scenario-staircase and held-out execution."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from .mfe_v2_contracts import (
    C0Parameters,
    build_registered_c1_bands,
    c0_finalists,
    generate_latent_ar1_records,
    transform_latent_pv,
)
from .relaxation_v4 import (
    AdaptiveRelaxationResult,
    solve_adaptive_extensive_form,
)
from .replay_v2 import replay_v2
from .truth_model import SolverConfig, load_v2_system
from .truth_model import solve_extensive_form, solve_stage2, solve_wait_and_see


CONSTRUCTION_SEED = 2026080101
HELD_OUT_SEED = 2026080104
STAIRCASE = (32, 16)
STAIRCASE_GAP = 0.001
STAIRCASE_SECONDS = 900.0
FROZEN_SCENARIO_COUNT = 32
HELD_OUT_COUNT = 218
LEAN_HELD_OUT_COUNT = 64
LEAN_SIGMA = 0.08
LEAN_INITIAL_SOC = 0.50
LEAN_C0 = C0Parameters(15.0, 35.0, 35.0, 50.0)


@dataclass(frozen=True)
class Sentinel:
    label: str
    duration_hours: int
    initial_soc_fraction: float
    sigma: float
    reserve_fraction: float


SENTINELS = (
    Sentinel("S1", 1, 0.75, 0.15, 0.20),
    Sentinel("S2", 2, 0.50, 0.08, 0.20),
    Sentinel("S3", 4, 0.25, 0.03, 0.05),
)


def cell_grid() -> tuple[Sentinel, ...]:
    cells = []
    for sigma in (0.03, 0.08, 0.15):
        for duration in (1, 2, 4):
            for initial_soc in (0.25, 0.50, 0.75):
                for reserve in (0.05, 0.20):
                    label = (
                        f"s{int(round(100 * sigma)):02d}"
                        f"_d{duration}"
                        f"_e{int(round(100 * initial_soc)):02d}"
                        f"_r{int(round(100 * reserve)):02d}"
                    )
                    cells.append(
                        Sentinel(
                            label,
                            duration,
                            initial_soc,
                            sigma,
                            reserve,
                        )
                    )
    return tuple(cells)


def lean_cell_grid() -> tuple[Sentinel, ...]:
    return tuple(
        Sentinel(
            label=f"lean_d{duration}_r{int(round(100 * reserve)):02d}",
            duration_hours=duration,
            initial_soc_fraction=LEAN_INITIAL_SOC,
            sigma=LEAN_SIGMA,
            reserve_fraction=reserve,
        )
        for duration in (1, 2, 4)
        for reserve in (0.05, 0.20)
    )


def construction_paths(system, *, sigma: float, count: int):
    latent = generate_latent_ar1_records(
        count=count,
        horizon=system.horizon,
        seed=CONSTRUCTION_SEED,
    )
    return transform_latent_pv(system.forecast_pv_mw, latent, sigma)


def _adaptive_record(
    adaptive: AdaptiveRelaxationResult,
    *,
    system,
    paths,
) -> dict[str, object]:
    result = adaptive.result
    replay_valid = False
    cost_reconciled = False
    non_delivery_count = len(paths)
    max_shortfall = None
    if result.stage1 is not None and len(result.scenarios) == len(paths):
        replays = [
            replay_v2(system, result.stage1, decision, path)
            for decision, path in zip(result.scenarios, paths)
        ]
        replay_valid = all(item.physically_valid for item in replays)
        cost_reconciled = all(item.cost_reconciled for item in replays)
        shortfalls = [
            max(
                max(item.activation.shortfall_up_mw),
                max(item.activation.shortfall_down_mw),
            )
            for item in replays
        ]
        non_delivery_count = sum(value > 1e-6 for value in shortfalls)
        max_shortfall = max(shortfalls, default=0.0)
    total_solve_seconds = sum(
        iteration.solve_seconds for iteration in adaptive.iterations
    )
    passed = (
        adaptive.certified_contract_exact
        and not result.diagnostics.solver_unresolved
        and replay_valid
        and cost_reconciled
        and total_solve_seconds <= STAIRCASE_SECONDS + 1e-6
    )
    return {
        "passed": passed,
        "certified_contract_exact": adaptive.certified_contract_exact,
        "objective_usd": result.objective,
        "relative_gap": result.diagnostics.relative_gap,
        "solver_unresolved": result.diagnostics.solver_unresolved,
        "termination": result.diagnostics.termination,
        "final_binary_count": result.diagnostics.binary_count,
        "final_variable_count": result.diagnostics.variable_count,
        "final_constraint_count": result.diagnostics.constraint_count,
        "total_solve_seconds": total_solve_seconds,
        "iteration_count": len(adaptive.iterations),
        "iterations": [asdict(item) for item in adaptive.iterations],
        "integer_base_hours": adaptive.integer_base_hours,
        "integer_up_hours": adaptive.integer_up_hours,
        "integer_down_hours": adaptive.integer_down_hours,
        "replay_valid": replay_valid,
        "cost_reconciled": cost_reconciled,
        "non_delivery_count": non_delivery_count,
        "non_delivery_rate": non_delivery_count / len(paths),
        "max_shortfall_mw": max_shortfall,
    }


def run_full_sentinel(
    repository_root: Path,
    sentinel: Sentinel,
    *,
    scenario_count: int,
) -> dict[str, object]:
    system = load_v2_system(
        repository_root,
        duration_hours=sentinel.duration_hours,
        initial_soc_fraction=sentinel.initial_soc_fraction,
        reserve_fraction=sentinel.reserve_fraction,
    )
    paths = construction_paths(
        system,
        sigma=sentinel.sigma,
        count=scenario_count,
    )
    adaptive = solve_adaptive_extensive_form(
        system,
        paths,
        "c_full",
        config=SolverConfig(
            mip_rel_gap=STAIRCASE_GAP,
            time_limit_seconds=STAIRCASE_SECONDS,
        ),
        total_time_limit_seconds=STAIRCASE_SECONDS,
    )
    return {
        "line": f"C_full-{scenario_count}",
        "scenario_count": scenario_count,
        "sentinel": asdict(sentinel),
        **_adaptive_record(adaptive, system=system, paths=paths),
    }


def run_c0_sentinel_fit(
    repository_root: Path,
    sentinel: Sentinel,
    *,
    scenario_count: int,
    candidate_limit: int = 12,
) -> dict[str, object]:
    system = load_v2_system(
        repository_root,
        duration_hours=sentinel.duration_hours,
        initial_soc_fraction=sentinel.initial_soc_fraction,
        reserve_fraction=sentinel.reserve_fraction,
    )
    paths = construction_paths(
        system,
        sigma=sentinel.sigma,
        count=scenario_count,
    )
    candidates = c0_finalists(system.battery, cap=candidate_limit)
    records = []
    for candidate in candidates:
        adaptive = solve_adaptive_extensive_form(
            system,
            paths,
            "c0",
            c0_parameters=candidate,
            config=SolverConfig(
                mip_rel_gap=STAIRCASE_GAP,
                time_limit_seconds=STAIRCASE_SECONDS,
            ),
            total_time_limit_seconds=STAIRCASE_SECONDS,
        )
        records.append(
            {
                "parameters": asdict(candidate),
                **_adaptive_record(adaptive, system=system, paths=paths),
            }
        )

    certified = [
        record
        for record in records
        if record["passed"] and record["non_delivery_rate"] <= 0.01
    ]
    selected = None
    if certified:
        selected = min(
            certified,
            key=lambda record: (
                float(record["objective_usd"]),
                float(record["non_delivery_rate"]),
                tuple(record["parameters"].values()),
            ),
        )
    gate_passed = len(records) == len(candidates) and all(
        record["passed"] for record in records
    ) and selected is not None
    return {
        "line": f"C0-fit-{scenario_count}",
        "scenario_count": scenario_count,
        "sentinel": asdict(sentinel),
        "candidate_count": len(candidates),
        "gate_passed": gate_passed,
        "selected_parameters": (
            None if selected is None else selected["parameters"]
        ),
        "candidate_records": records,
    }


def _sentinel_by_label(label: str) -> Sentinel:
    for sentinel in SENTINELS:
        if sentinel.label == label:
            return sentinel
    raise ValueError(f"unknown sentinel {label}")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2)


def _solve_frozen_stage1_lines(
    repository_root: Path,
    cell: Sentinel,
) -> tuple[dict[str, object], dict[str, object]]:
    system = load_v2_system(
        repository_root,
        duration_hours=cell.duration_hours,
        initial_soc_fraction=cell.initial_soc_fraction,
        reserve_fraction=cell.reserve_fraction,
    )
    paths = construction_paths(
        system,
        sigma=cell.sigma,
        count=FROZEN_SCENARIO_COUNT,
    )

    c0_fit = run_c0_sentinel_fit(
        repository_root,
        cell,
        scenario_count=FROZEN_SCENARIO_COUNT,
    )
    if not c0_fit["gate_passed"] or c0_fit["selected_parameters"] is None:
        raise RuntimeError(f"{cell.label}: C0 fit unresolved")
    theta = C0Parameters(**c0_fit["selected_parameters"])
    c0 = solve_adaptive_extensive_form(
        system,
        paths,
        "c0",
        c0_parameters=theta,
        config=SolverConfig(
            mip_rel_gap=STAIRCASE_GAP,
            time_limit_seconds=STAIRCASE_SECONDS,
        ),
        total_time_limit_seconds=STAIRCASE_SECONDS,
    )
    if not c0.certified_contract_exact or c0.result.stage1 is None:
        raise RuntimeError(f"{cell.label}: selected C0 did not certify")

    full = solve_adaptive_extensive_form(
        system,
        paths,
        "c_full",
        config=SolverConfig(
            mip_rel_gap=STAIRCASE_GAP,
            time_limit_seconds=STAIRCASE_SECONDS,
        ),
        total_time_limit_seconds=STAIRCASE_SECONDS,
    )
    if not full.certified_contract_exact or full.result.stage1 is None:
        raise RuntimeError(f"{cell.label}: C_full-32 did not certify")

    bands = build_registered_c1_bands(system.forecast_pv_mw)
    c1 = solve_extensive_form(
        system,
        (system.forecast_pv_mw,),
        "c1_v3",
        c1_band=bands["1/99"][cell.sigma],
        config=SolverConfig(mip_rel_gap=1e-4),
    )
    assoc = solve_extensive_form(
        system,
        (system.forecast_pv_mw,),
        "c_assoc",
        config=SolverConfig(mip_rel_gap=1e-4),
    )
    if c1.stage1 is None or assoc.stage1 is None:
        raise RuntimeError(f"{cell.label}: cheap contract stage 1 failed")

    normal_det = solve_extensive_form(
        system,
        (system.forecast_pv_mw,),
        "c_full",
    )
    zero_det = solve_extensive_form(
        system,
        (system.forecast_pv_mw,),
        "c_full",
        force_hybrid_reserve_zero=True,
    )
    if (
        normal_det.stage1 is None
        or zero_det.stage1 is None
        or not normal_det.scenarios
        or not zero_det.scenarios
    ):
        raise RuntimeError(f"{cell.label}: pivotality solve failed")
    normal_replay = replay_v2(
        system,
        normal_det.stage1,
        normal_det.scenarios[0],
        system.forecast_pv_mw,
    )
    zero_replay = replay_v2(
        system,
        zero_det.stage1,
        zero_det.scenarios[0],
        system.forecast_pv_mw,
    )
    objective_delta = float(zero_det.objective - normal_det.objective)
    normal_shortfall = sum(normal_replay.activation.shortfall_up_mw) + sum(
        normal_replay.activation.shortfall_down_mw
    )
    zero_shortfall = sum(zero_replay.activation.shortfall_up_mw) + sum(
        zero_replay.activation.shortfall_down_mw
    )
    pivotal_threshold = max(1.0, 1e-6 * abs(float(normal_det.objective)))
    pivotal = (
        objective_delta >= pivotal_threshold
        or zero_shortfall - normal_shortfall > 1e-6
    )

    stage1 = {
        "C0": c0.result.stage1,
        "C1": c1.stage1,
        "C_ASSOC": assoc.stage1,
        "C_full-32": full.result.stage1,
    }
    construction = {
        "cell": asdict(cell),
        "construction_seed": CONSTRUCTION_SEED,
        "scenario_count": FROZEN_SCENARIO_COUNT,
        "c0_fit": c0_fit,
        "c0_selected_certificate": _adaptive_record(
            c0,
            system=system,
            paths=paths,
        ),
        "c_full_certificate": _adaptive_record(
            full,
            system=system,
            paths=paths,
        ),
        "c1_deterministic_objective_usd": c1.objective,
        "c_assoc_deterministic_objective_usd": assoc.objective,
        "pivotal": pivotal,
        "pivotal_objective_delta_usd": objective_delta,
        "pivotal_shortfall_delta_mw_sum": zero_shortfall - normal_shortfall,
    }
    return {"system": system, "stage1": stage1}, construction


def _held_out_record(
    *,
    cell: Sentinel,
    path_id: int,
    line: str,
    solve,
    replay,
) -> dict[str, object]:
    cost_components = dict(replay.cost_components)
    max_up = max(replay.activation.shortfall_up_mw)
    max_down = max(replay.activation.shortfall_down_mw)
    isolated_non_delivery = max(max_up, max_down) > 1e-6
    sequential_shortfall = max(replay.sequential.shortfall_up_mw)
    sequential_non_delivery = (
        sequential_shortfall > 1e-6
        or replay.sequential.physical_violation_mwh > 1e-6
    )
    return {
        **asdict(cell),
        "path_id": path_id,
        "line": line,
        "realized_cost_usd": replay.replay_cost,
        "isolated_non_delivery": isolated_non_delivery,
        "max_isolated_up_shortfall_mw": max_up,
        "max_isolated_down_shortfall_mw": max_down,
        "sequential_non_delivery": sequential_non_delivery,
        "sequential_shortfall_mw": sequential_shortfall,
        "sequential_physical_violation_mwh": (
            replay.sequential.physical_violation_mwh
        ),
        "reserve_shortfall_cost_usd": cost_components.get(
            "reserve_shortfall", 0.0
        ),
        "load_shedding_cost_usd": cost_components.get("load_shedding", 0.0),
        "emergency_spill_cost_usd": cost_components.get(
            "emergency_spill", 0.0
        ),
        "imbalance_cost_usd": cost_components.get("imbalance", 0.0),
        "pv_curtailment_cost_usd": cost_components.get(
            "pv_curtailment", 0.0
        ),
        "battery_throughput_cost_usd": cost_components.get(
            "battery_throughput", 0.0
        ),
        "physical_replay_valid": replay.physically_valid,
        "cost_reconciled": replay.cost_reconciled,
        "solver_unresolved": solve.diagnostics.solver_unresolved,
        "solve_seconds": solve.diagnostics.solve_seconds,
    }


def run_confirmatory_cell(
    repository_root: Path,
    cell: Sentinel,
) -> dict[str, object]:
    frozen, construction = _solve_frozen_stage1_lines(repository_root, cell)
    system = frozen["system"]
    latent = generate_latent_ar1_records(
        count=HELD_OUT_COUNT,
        horizon=system.horizon,
        seed=HELD_OUT_SEED,
    )
    paths = transform_latent_pv(
        system.forecast_pv_mw,
        latent,
        cell.sigma,
    )
    records = []
    for path_id, path in enumerate(paths, start=1):
        for line, stage1 in frozen["stage1"].items():
            solved = solve_stage2(system, stage1, path)
            if solved.decision is None:
                raise RuntimeError(
                    f"{cell.label}/{path_id}/{line}: no stage-2 incumbent"
                )
            replay = replay_v2(system, stage1, solved.decision, path)
            records.append(
                _held_out_record(
                    cell=cell,
                    path_id=path_id,
                    line=line,
                    solve=solved,
                    replay=replay,
                )
            )

        ws = solve_wait_and_see(system, path)
        if ws.stage1 is None or not ws.scenarios:
            raise RuntimeError(f"{cell.label}/{path_id}/C_WS: no incumbent")
        ws_replay = replay_v2(system, ws.stage1, ws.scenarios[0], path)
        records.append(
            _held_out_record(
                cell=cell,
                path_id=path_id,
                line="C_WS",
                solve=ws,
                replay=ws_replay,
            )
        )
    return {
        "cell": asdict(cell),
        "held_out_seed": HELD_OUT_SEED,
        "held_out_count": HELD_OUT_COUNT,
        "construction": construction,
        "records": records,
    }


def run_all_confirmatory_cells(
    repository_root: Path,
    output_directory: Path,
    *,
    shard_index: int = 0,
    shard_count: int = 1,
) -> None:
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise ValueError("invalid confirmatory shard")
    output_directory.mkdir(parents=True, exist_ok=True)
    for index, cell in enumerate(cell_grid(), start=1):
        if (index - 1) % shard_count != shard_index:
            continue
        output = output_directory / f"{cell.label}.json"
        if output.exists():
            print(f"[{index:02d}/54] {cell.label}: checkpoint exists", flush=True)
            continue
        print(f"[{index:02d}/54] {cell.label}: start", flush=True)
        payload = run_confirmatory_cell(repository_root, cell)
        _write_json(output, payload)
        print(f"[{index:02d}/54] {cell.label}: complete", flush=True)


def consolidate_confirmatory(
    input_directory: Path,
    output_csv: Path,
) -> None:
    records = []
    for cell in cell_grid():
        path = input_directory / f"{cell.label}.json"
        if not path.exists():
            raise FileNotFoundError(path)
        with path.open(encoding="utf-8") as stream:
            payload = json.load(stream)
        records.extend(payload["records"])
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def run_lean_cell(
    repository_root: Path,
    cell: Sentinel,
) -> dict[str, object]:
    system = load_v2_system(
        repository_root,
        duration_hours=cell.duration_hours,
        initial_soc_fraction=cell.initial_soc_fraction,
        reserve_fraction=cell.reserve_fraction,
    )
    bands = build_registered_c1_bands(system.forecast_pv_mw)
    c0 = solve_extensive_form(
        system,
        (system.forecast_pv_mw,),
        "c0",
        c0_parameters=LEAN_C0,
    )
    c1 = solve_extensive_form(
        system,
        (system.forecast_pv_mw,),
        "c1_v3",
        c1_band=bands["1/99"][cell.sigma],
    )
    assoc = solve_extensive_form(
        system,
        (system.forecast_pv_mw,),
        "c_assoc",
    )
    if c0.stage1 is None or c1.stage1 is None or assoc.stage1 is None:
        raise RuntimeError(f"{cell.label}: deterministic stage 1 failed")
    stage1 = {
        "C0-fixture": c0.stage1,
        "C1": c1.stage1,
        "C_ASSOC": assoc.stage1,
    }

    latent = generate_latent_ar1_records(
        count=LEAN_HELD_OUT_COUNT,
        horizon=system.horizon,
        seed=HELD_OUT_SEED,
    )
    paths = transform_latent_pv(
        system.forecast_pv_mw,
        latent,
        cell.sigma,
    )
    records = []
    for path_id, path in enumerate(paths, start=1):
        for line, frozen_stage1 in stage1.items():
            solved = solve_stage2(system, frozen_stage1, path)
            if solved.decision is None:
                raise RuntimeError(
                    f"{cell.label}/{path_id}/{line}: no stage-2 incumbent"
                )
            replay = replay_v2(
                system,
                frozen_stage1,
                solved.decision,
                path,
            )
            records.append(
                _held_out_record(
                    cell=cell,
                    path_id=path_id,
                    line=line,
                    solve=solved,
                    replay=replay,
                )
            )

        ws = solve_wait_and_see(system, path)
        if ws.stage1 is None or not ws.scenarios:
            raise RuntimeError(f"{cell.label}/{path_id}/C_WS: no incumbent")
        ws_replay = replay_v2(system, ws.stage1, ws.scenarios[0], path)
        records.append(
            _held_out_record(
                cell=cell,
                path_id=path_id,
                line="C_WS",
                solve=ws,
                replay=ws_replay,
            )
        )

    return {
        "cell": asdict(cell),
        "design": "lean-paper-validation",
        "held_out_seed": HELD_OUT_SEED,
        "held_out_count": LEAN_HELD_OUT_COUNT,
        "stage1": {
            "C0-fixture": {
                "parameters": asdict(LEAN_C0),
                "deterministic_objective_usd": c0.objective,
            },
            "C1": {"deterministic_objective_usd": c1.objective},
            "C_ASSOC": {"deterministic_objective_usd": assoc.objective},
        },
        "records": records,
    }


def run_all_lean_cells(
    repository_root: Path,
    output_directory: Path,
) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    for index, cell in enumerate(lean_cell_grid(), start=1):
        output = output_directory / f"{cell.label}.json"
        if output.exists():
            print(f"[{index}/6] {cell.label}: checkpoint exists", flush=True)
            continue
        print(f"[{index}/6] {cell.label}: start", flush=True)
        payload = run_lean_cell(repository_root, cell)
        _write_json(output, payload)
        print(f"[{index}/6] {cell.label}: complete", flush=True)


def consolidate_lean(
    input_directory: Path,
    output_csv: Path,
) -> None:
    records = []
    for cell in lean_cell_grid():
        path = input_directory / f"{cell.label}.json"
        if not path.exists():
            raise FileNotFoundError(path)
        with path.open(encoding="utf-8") as stream:
            records.extend(json.load(stream)["records"])
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "full",
            "c0",
            "confirm-cell",
            "confirm-all",
            "consolidate",
            "lean-cell",
            "lean-all",
            "lean-consolidate",
        ),
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sentinel")
    parser.add_argument("--scenarios", type=int, choices=STAIRCASE)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    arguments = parser.parse_args()

    if arguments.command == "confirm-all":
        run_all_confirmatory_cells(
            arguments.root,
            arguments.output,
            shard_index=arguments.shard_index,
            shard_count=arguments.shard_count,
        )
        return
    if arguments.command == "lean-all":
        run_all_lean_cells(arguments.root, arguments.output)
        return
    if arguments.command == "lean-consolidate":
        if arguments.input is None:
            parser.error("lean-consolidate requires --input")
        consolidate_lean(arguments.input, arguments.output)
        return
    if arguments.command == "lean-cell":
        if arguments.sentinel is None:
            parser.error("lean-cell requires --sentinel")
        matching = [
            cell for cell in lean_cell_grid()
            if cell.label == arguments.sentinel
        ]
        if not matching:
            parser.error("unknown lean cell label")
        payload = run_lean_cell(arguments.root, matching[0])
        _write_json(arguments.output, payload)
        print(json.dumps(payload["cell"], indent=2))
        return
    if arguments.command == "consolidate":
        if arguments.input is None:
            parser.error("consolidate requires --input")
        consolidate_confirmatory(arguments.input, arguments.output)
        return
    if arguments.command == "confirm-cell":
        if arguments.sentinel is None:
            parser.error("confirm-cell requires --sentinel cell label")
        matching = [
            cell for cell in cell_grid() if cell.label == arguments.sentinel
        ]
        if not matching:
            parser.error("unknown confirmatory cell label")
        payload = run_confirmatory_cell(arguments.root, matching[0])
        _write_json(arguments.output, payload)
        print(json.dumps(payload["cell"], indent=2))
        return

    if arguments.sentinel is None or arguments.scenarios is None:
        parser.error("full/c0 require --sentinel and --scenarios")
    sentinel = _sentinel_by_label(arguments.sentinel)
    if arguments.command == "full":
        payload = run_full_sentinel(
            arguments.root,
            sentinel,
            scenario_count=arguments.scenarios,
        )
    else:
        payload = run_c0_sentinel_fit(
            arguments.root,
            sentinel,
            scenario_count=arguments.scenarios,
        )
    _write_json(arguments.output, payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
