"""Lightweight 24-hour MFE v3 execution with the full binary truth model.

This runner reduces repeated solves, not physical fidelity.  It keeps the
24-hour lossy bidirectional PV+BESS MILP, including charge/discharge mode
binaries, curtailment, recourse, reserve activation, and terminal SOC.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .mfe_v2_contracts import (
    C0Parameters,
    build_registered_c1_bands,
    generate_latent_ar1_records,
    transform_latent_pv,
)
from .replay_v2 import replay_v2
from .truth_model import (
    SolverConfig,
    load_v2_system,
    solve_extensive_form,
    solve_stage2,
)


CONSTRUCTION_SCENARIOS = 32
HELD_OUT_SCENARIOS = 32
CONSTRUCTION_SEED = 2026080101
HELD_OUT_SEED = 2026080104
MIP_REL_GAP = 0.001
TIME_LIMIT_SECONDS = 120.0
SIGMA = 0.08
INITIAL_SOC_FRACTION = 0.50
C0_FIXTURE = C0Parameters(15.0, 35.0, 35.0, 50.0)


@dataclass(frozen=True)
class LightweightCell:
    label: str
    duration_hours: int
    reserve_fraction: float
    initial_soc_fraction: float = INITIAL_SOC_FRACTION
    sigma: float = SIGMA


def cell_grid() -> tuple[LightweightCell, ...]:
    """Return the six frozen duration-by-reserve cells."""

    return tuple(
        LightweightCell(
            label=f"v3full_d{duration}_r{int(round(100 * reserve)):02d}",
            duration_hours=duration,
            reserve_fraction=reserve,
        )
        for duration in (1, 2, 4)
        for reserve in (0.05, 0.20)
    )


def _paths(system, *, count: int, seed: int, sigma: float):
    latent = generate_latent_ar1_records(
        count=count,
        horizon=system.horizon,
        seed=seed,
    )
    return transform_latent_pv(system.forecast_pv_mw, latent, sigma)


def _diagnostics(solved) -> dict[str, object]:
    diagnostics = solved.diagnostics
    return {
        "termination": diagnostics.termination,
        "success": diagnostics.success,
        "solver_unresolved": diagnostics.solver_unresolved,
        "objective_usd": solved.objective,
        "relative_gap": diagnostics.relative_gap,
        "solve_seconds": diagnostics.solve_seconds,
        "variable_count": diagnostics.variable_count,
        "constraint_count": diagnostics.constraint_count,
        "binary_count": diagnostics.binary_count,
    }


def _held_out_record(*, cell, path_id, line, solve, replay):
    return {
        **asdict(cell),
        "path_id": path_id,
        "line": line,
        "realized_cost_usd": replay.replay_cost,
        "physical_replay_valid": replay.physically_valid,
        "cost_reconciled": replay.cost_reconciled,
        "max_up_shortfall_mw": max(replay.activation.shortfall_up_mw),
        "max_down_shortfall_mw": max(replay.activation.shortfall_down_mw),
        "sequential_shortfall_mw": max(
            replay.sequential.shortfall_up_mw
        ),
        "sequential_physical_violation_mwh": (
            replay.sequential.physical_violation_mwh
        ),
        "stage2_solver_unresolved": solve.diagnostics.solver_unresolved,
        "stage2_solve_seconds": solve.diagnostics.solve_seconds,
    }


def run_cell(repository_root: Path, cell: LightweightCell) -> dict[str, object]:
    """Run one lightweight cell with four contract lines and paired paths."""

    system = load_v2_system(
        repository_root,
        duration_hours=cell.duration_hours,
        initial_soc_fraction=cell.initial_soc_fraction,
        reserve_fraction=cell.reserve_fraction,
    )
    construction_paths = _paths(
        system,
        count=CONSTRUCTION_SCENARIOS,
        seed=CONSTRUCTION_SEED,
        sigma=cell.sigma,
    )
    bands = build_registered_c1_bands(system.forecast_pv_mw)

    c0 = solve_extensive_form(
        system,
        (system.forecast_pv_mw,),
        "c0",
        c0_parameters=C0_FIXTURE,
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
    full = solve_extensive_form(
        system,
        construction_paths,
        "c_full",
        config=SolverConfig(
            mip_rel_gap=MIP_REL_GAP,
            time_limit_seconds=TIME_LIMIT_SECONDS,
        ),
    )
    solved_lines = {
        "C0-fixture": c0,
        "C1": c1,
        "C_ASSOC": assoc,
        "C_full-32": full,
    }
    for line, solved in solved_lines.items():
        if solved.stage1 is None:
            raise RuntimeError(f"{cell.label}/{line}: no stage-1 incumbent")
    if full.diagnostics.solver_unresolved:
        raise RuntimeError(
            f"{cell.label}/C_full-32: unresolved after "
            f"{full.diagnostics.solve_seconds:.1f}s"
        )

    construction_replays = [
        replay_v2(system, full.stage1, decision, path)
        for decision, path in zip(full.scenarios, construction_paths)
    ]
    construction_validation = {
        "replay_count": len(construction_replays),
        "physical_failures": sum(
            not replay.physically_valid for replay in construction_replays
        ),
        "cost_reconciliation_failures": sum(
            not replay.cost_reconciled for replay in construction_replays
        ),
    }
    if (
        construction_validation["physical_failures"]
        or construction_validation["cost_reconciliation_failures"]
    ):
        raise RuntimeError(f"{cell.label}/C_full-32: construction replay failed")

    held_out_paths = _paths(
        system,
        count=HELD_OUT_SCENARIOS,
        seed=HELD_OUT_SEED,
        sigma=cell.sigma,
    )
    records = []
    for path_id, path in enumerate(held_out_paths, start=1):
        for line, solved in solved_lines.items():
            stage2 = solve_stage2(system, solved.stage1, path)
            if stage2.decision is None:
                raise RuntimeError(
                    f"{cell.label}/{path_id}/{line}: no stage-2 incumbent"
                )
            replay = replay_v2(system, solved.stage1, stage2.decision, path)
            records.append(
                _held_out_record(
                    cell=cell,
                    path_id=path_id,
                    line=line,
                    solve=stage2,
                    replay=replay,
                )
            )

    return {
        "design": "mfe-v3-lightweight-full-binary",
        "cell": asdict(cell),
        "construction_scenarios": CONSTRUCTION_SCENARIOS,
        "held_out_scenarios": HELD_OUT_SCENARIOS,
        "construction_seed": CONSTRUCTION_SEED,
        "held_out_seed": HELD_OUT_SEED,
        "contract_lines": list(solved_lines),
        "stage1": {
            line: _diagnostics(solved)
            for line, solved in solved_lines.items()
        },
        "construction_validation": construction_validation,
        "held_out_records": records,
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2)


def run_all(repository_root: Path, output_directory: Path) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    cells = cell_grid()
    for index, cell in enumerate(cells, start=1):
        output = output_directory / f"{cell.label}.json"
        if output.exists():
            print(f"[{index}/6] {cell.label}: checkpoint exists", flush=True)
            continue
        print(f"[{index}/6] {cell.label}: start", flush=True)
        _write_json(output, run_cell(repository_root, cell))
        print(f"[{index}/6] {cell.label}: complete", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("cell", "all"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/mfe_v3_lightweight_full_binary"),
    )
    parser.add_argument("--cell")
    arguments = parser.parse_args()
    repository_root = arguments.root.resolve()
    output = arguments.output.resolve()
    if arguments.command == "all":
        run_all(repository_root, output)
        return
    if not arguments.cell:
        parser.error("cell command requires --cell")
    selected = [cell for cell in cell_grid() if cell.label == arguments.cell]
    if not selected:
        parser.error("unknown cell")
    payload = run_cell(repository_root, selected[0])
    output_path = output / f"{selected[0].label}.json"
    _write_json(output_path, payload)
    print(json.dumps({"output": str(output_path), "cell": payload["cell"]}))


if __name__ == "__main__":
    main()
