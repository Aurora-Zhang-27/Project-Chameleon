"""Auditable execution helpers for the final MFE v3 instrument."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import time

import numpy as np

from .mfe_v2_contracts import (
    C0Parameters,
    build_registered_c1_bands,
    generate_latent_ar1_records,
    generate_pv_paths_by_level,
    transform_latent_pv,
)
from .mfe_v3_certificates import certify_v3_reference_and_reserve
from .replay_v2 import replay_v2
from .truth_model import (
    load_v2_system,
    solve_extensive_form,
    solve_multistratum_c0,
    solve_wait_and_see,
)


SAFETY_SEED = 2026080102
SAFETY_PATH_COUNT = 10_000
PILOT_SEED = 2026080103


def run_deterministic_reconciliation(
    repository_root: Path,
    output_directory: Path,
) -> dict[str, object]:
    """Run and serialize the frozen four-line 24-hour v3 gate case."""

    system = load_v2_system(
        repository_root,
        duration_hours=4,
        initial_soc_fraction=0.5,
        reserve_fraction=0.05,
    )
    bands = build_registered_c1_bands(system.forecast_pv_mw)
    specifications = (
        (
            "C0_fixture",
            "c0",
            {"c0_parameters": C0Parameters(15.0, 35.0, 35.0, 50.0)},
        ),
        (
            "C1_1_99",
            "c1_v3",
            {"c1_band": bands["1/99"][0.08]},
        ),
        (
            "C1_5_95",
            "c1_v3",
            {"c1_band": bands["5/95"][0.08]},
        ),
        ("C_full_det", "c_full", {}),
    )
    records: dict[str, tuple[object, object]] = {}
    summary = []
    for label, contract, keyword_arguments in specifications:
        solved = solve_extensive_form(
            system,
            (system.forecast_pv_mw,),
            contract,
            **keyword_arguments,
        )
        if solved.stage1 is None or not solved.scenarios:
            raise RuntimeError(f"{label} did not return a primal solution")
        replay = replay_v2(
            system,
            solved.stage1,
            solved.scenarios[0],
            system.forecast_pv_mw,
        )
        if not replay.physically_valid or not replay.cost_reconciled:
            raise RuntimeError(
                f"{label} failed replay: {replay.physical_violations}"
            )
        records[label] = (solved, replay)
        summary.append(
            {
                "line": label,
                "termination": solved.diagnostics.termination,
                "objective_usd": solved.objective,
                "relative_gap": solved.diagnostics.relative_gap,
                "binary_count": solved.diagnostics.binary_count,
                "solve_seconds": solved.diagnostics.solve_seconds,
                "replay_cost_usd": replay.replay_cost,
                "cost_residual_usd": replay.cost_residual,
                "max_balance_residual_mw": max(
                    abs(value) for value in replay.system_balance_residual_mw
                ),
                "max_soc_residual_mwh": max(
                    abs(value) for value in replay.soc_identity_residual_mwh
                ),
                "max_up_shortfall_mw": max(
                    replay.activation.shortfall_up_mw
                ),
                "max_down_shortfall_mw": max(
                    replay.activation.shortfall_down_mw
                ),
                "terminal_soc_mwh": replay.reconstructed_soc_mwh[-1],
                "sequential_violation_mwh": (
                    replay.sequential.physical_violation_mwh
                ),
            }
        )

    output_directory.mkdir(parents=True, exist_ok=True)
    with (output_directory / "summary.json").open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    fieldnames = ["hour", "load_mw", "pv_mw"]
    for label, _, _ in specifications:
        fieldnames.extend(
            (
                f"{label}_thermal_mw",
                f"{label}_hybrid_schedule_mw",
                f"{label}_hybrid_realized_mw",
                f"{label}_charge_mw",
                f"{label}_discharge_mw",
                f"{label}_soc_end_mwh",
                f"{label}_up_reserve_mw",
                f"{label}_down_reserve_mw",
                f"{label}_up_shortfall_mw",
                f"{label}_down_shortfall_mw",
            )
        )
    with (output_directory / "hourly_reconciliation.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for t in range(system.horizon):
            row: dict[str, float | int] = {
                "hour": t + 1,
                "load_mw": system.load_mw[t],
                "pv_mw": system.forecast_pv_mw[t],
            }
            for label, _, _ in specifications:
                solved, replay = records[label]
                stage1 = solved.stage1
                decision = solved.scenarios[0]
                row.update(
                    {
                        f"{label}_thermal_mw": sum(
                            unit[t] for unit in replay.thermal_dispatch_mw
                        ),
                        f"{label}_hybrid_schedule_mw": (
                            stage1.hybrid_injection_mw[t]
                        ),
                        f"{label}_hybrid_realized_mw": (
                            replay.hybrid_injection_mw[t]
                        ),
                        f"{label}_charge_mw": decision.charge_mw[t],
                        f"{label}_discharge_mw": decision.discharge_mw[t],
                        f"{label}_soc_end_mwh": (
                            replay.reconstructed_soc_mwh[t + 1]
                        ),
                        f"{label}_up_reserve_mw": (
                            stage1.hybrid_up_reserve_mw[t]
                        ),
                        f"{label}_down_reserve_mw": (
                            stage1.hybrid_down_reserve_mw[t]
                        ),
                        f"{label}_up_shortfall_mw": (
                            replay.activation.shortfall_up_mw[t]
                        ),
                        f"{label}_down_shortfall_mw": (
                            replay.activation.shortfall_down_mw[t]
                        ),
                    }
                )
            writer.writerow(row)

    cost_names = [name for name, _ in records["C0_fixture"][1].cost_components]
    with (output_directory / "cost_reconciliation.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["component", *(label for label, _, _ in specifications)],
        )
        writer.writeheader()
        for name in cost_names:
            row: dict[str, str | float] = {"component": name}
            for label, _, _ in specifications:
                row[label] = dict(records[label][1].cost_components)[name]
            writer.writerow(row)
        writer.writerow(
            {
                "component": "total",
                **{
                    label: records[label][1].replay_cost
                    for label, _, _ in specifications
                },
            }
        )
    return {"summary": summary, "output_directory": str(output_directory)}


def run_c1_safety_audit(
    repository_root: Path,
    output_directory: Path,
) -> dict[str, object]:
    """Execute the registered v3 resource-level boundary safety audit."""

    reference = load_v2_system(
        repository_root,
        duration_hours=4,
        initial_soc_fraction=0.5,
        reserve_fraction=0.05,
    )
    bands = build_registered_c1_bands(reference.forecast_pv_mw)
    safety_paths = generate_pv_paths_by_level(
        reference.forecast_pv_mw,
        count_per_level=SAFETY_PATH_COUNT,
        seed=SAFETY_SEED,
    )
    rows = []
    tolerance = 1e-6
    for duration in (1, 2, 4):
        for initial_soc in (0.25, 0.5, 0.75):
            system = load_v2_system(
                repository_root,
                duration_hours=duration,
                initial_soc_fraction=initial_soc,
                reserve_fraction=0.05,
            )
            battery = system.battery
            for sigma in (0.03, 0.08, 0.15):
                paths = safety_paths[sigma]
                for band_label in ("1/99", "5/95"):
                    band = bands[band_label][sigma]
                    lower = np.asarray(band.lower_mw)
                    upper = np.asarray(band.upper_mw)
                    inside = np.all(
                        (paths >= lower[None, :] - tolerance)
                        & (paths <= upper[None, :] + tolerance),
                        axis=1,
                    )
                    certificate = certify_v3_reference_and_reserve(
                        battery, band
                    )
                    reserve = certificate.max_two_sided_reserve_mw
                    selected = paths[inside]
                    failures = np.zeros(len(selected), dtype=bool)
                    maximum_violation = 0.0
                    if len(selected):
                        base_curtailment = selected - lower[None, :]
                        up_pv_release = np.minimum(
                            base_curtailment, reserve
                        )
                        up_discharge = reserve - up_pv_release
                        down_charge = min(
                            reserve, battery.charge_max_mw
                        )
                        down_extra_curtailment = max(
                            0.0, reserve - battery.charge_max_mw
                        )
                        up_mid_soc = (
                            battery.initial_energy_mwh
                            - up_discharge
                            * battery.reserve_duration_hours
                            / battery.discharge_efficiency
                        )
                        down_mid_soc = (
                            battery.initial_energy_mwh
                            + battery.charge_efficiency
                            * down_charge
                            * battery.reserve_duration_hours
                        )

                        violation_arrays = (
                            np.maximum(-base_curtailment, 0.0),
                            np.maximum(
                                base_curtailment - selected, 0.0
                            ),
                            np.maximum(-up_discharge, 0.0),
                            np.maximum(
                                up_discharge
                                - battery.discharge_max_mw,
                                0.0,
                            ),
                            np.maximum(-up_mid_soc, 0.0),
                            np.maximum(
                                up_mid_soc
                                - battery.energy_capacity_mwh,
                                0.0,
                            ),
                            np.maximum(
                                down_mid_soc
                                - battery.energy_capacity_mwh,
                                0.0,
                            )
                            * np.ones_like(up_mid_soc),
                            np.maximum(
                                down_extra_curtailment - lower, 0.0
                            )[None, :]
                            * np.ones_like(up_mid_soc),
                            np.abs(
                                up_pv_release + up_discharge - reserve
                            ),
                            abs(
                                down_charge
                                + down_extra_curtailment
                                - reserve
                            )
                            * np.ones_like(up_mid_soc),
                        )
                        for values in violation_arrays:
                            failures |= np.any(values > tolerance, axis=1)
                            maximum_violation = max(
                                maximum_violation,
                                float(np.max(values)),
                            )
                        if (
                            battery.initial_energy_mwh
                            < battery.terminal_energy_mwh - tolerance
                        ):
                            failures[:] = True
                            maximum_violation = max(
                                maximum_violation,
                                battery.terminal_energy_mwh
                                - battery.initial_energy_mwh,
                            )
                    rows.append(
                        {
                            "duration_hours": duration,
                            "initial_soc_fraction": initial_soc,
                            "sigma": sigma,
                            "band": band_label,
                            "paths_total": SAFETY_PATH_COUNT,
                            "inside_band_paths": int(np.sum(inside)),
                            "outside_band_paths": int(np.sum(~inside)),
                            "certified_common_reserve_mw": reserve,
                            "inside_failures": int(np.sum(failures)),
                            "max_violation_mw_or_mwh": maximum_violation,
                            "gate_pass": int(np.sum(failures)) == 0,
                        }
                    )

    output_directory.mkdir(parents=True, exist_ok=True)
    csv_path = output_directory / "c1_safety_audit.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "seed": SAFETY_SEED,
        "paths_per_duration_soc_error": SAFETY_PATH_COUNT,
        "audit_rows": len(rows),
        "inside_band_paths": sum(
            int(row["inside_band_paths"]) for row in rows
        ),
        "outside_band_paths": sum(
            int(row["outside_band_paths"]) for row in rows
        ),
        "inside_failures": sum(int(row["inside_failures"]) for row in rows),
        "gate_pass": all(bool(row["gate_pass"]) for row in rows),
        "csv": str(csv_path),
    }
    with (output_directory / "summary.json").open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)
    return summary


def _diagnostic_record(label: str, diagnostics, replay_seconds: float) -> dict:
    return {
        "label": label,
        "termination": diagnostics.termination,
        "success": diagnostics.success,
        "solver_unresolved": diagnostics.solver_unresolved,
        "incumbent_available": diagnostics.incumbent_objective is not None,
        "best_bound_available": diagnostics.best_bound is not None,
        "relative_gap": diagnostics.relative_gap,
        "node_count": diagnostics.node_count,
        "variable_count": diagnostics.variable_count,
        "constraint_count": diagnostics.constraint_count,
        "binary_count": diagnostics.binary_count,
        "solve_seconds": diagnostics.solve_seconds,
        "replay_seconds": replay_seconds,
    }


def run_runtime_pilot(
    repository_root: Path,
    output_directory: Path,
) -> dict[str, object]:
    """Run the frozen non-comparative v3 runtime pilot."""

    latent = generate_latent_ar1_records(
        count=384,
        horizon=24,
        seed=PILOT_SEED,
    )
    records = []

    c0_systems = []
    c0_paths = []
    block = 0
    for sigma in (0.03, 0.08, 0.15):
        for reserve_fraction in (0.05, 0.20):
            system = load_v2_system(
                repository_root,
                duration_hours=2,
                initial_soc_fraction=0.5,
                reserve_fraction=reserve_fraction,
            )
            c0_systems.append(system)
            c0_paths.append(
                transform_latent_pv(
                    system.forecast_pv_mw,
                    latent[block * 64 : (block + 1) * 64],
                    sigma,
                )
            )
            block += 1
    c0 = solve_multistratum_c0(
        tuple(c0_systems),
        tuple(c0_paths),
        C0Parameters(15.0, 35.0, 35.0, 50.0),
    )
    replay_start = time.perf_counter()
    if c0.stage1_by_stratum:
        for system, stage1, paths, decisions in zip(
            c0_systems,
            c0.stage1_by_stratum,
            c0_paths,
            c0.scenarios_by_stratum,
        ):
            for path, decision in zip(paths, decisions):
                replay_v2(system, stage1, decision, path)
    records.append(
        _diagnostic_record(
            "C0_fixture_multistratum_384",
            c0.diagnostics,
            time.perf_counter() - replay_start,
        )
    )

    system = load_v2_system(
        repository_root,
        duration_hours=2,
        initial_soc_fraction=0.5,
        reserve_fraction=0.20,
    )
    paths = transform_latent_pv(
        system.forecast_pv_mw, latent, 0.08
    )
    bands = build_registered_c1_bands(system.forecast_pv_mw)
    for label, contract, keyword_arguments in (
        (
            "C1_1_99_extensive_384",
            "c1_v3",
            {"c1_band": bands["1/99"][0.08]},
        ),
        ("C_full_extensive_384", "c_full", {}),
    ):
        solved = solve_extensive_form(
            system,
            paths,
            contract,
            **keyword_arguments,
        )
        replay_start = time.perf_counter()
        if solved.stage1 is not None:
            for path, decision in zip(paths, solved.scenarios):
                replay_v2(system, solved.stage1, decision, path)
        records.append(
            _diagnostic_record(
                label,
                solved.diagnostics,
                time.perf_counter() - replay_start,
            )
        )

    ws_records = []
    for index, path in enumerate(paths[:16]):
        solved = solve_wait_and_see(system, path)
        replay_start = time.perf_counter()
        if solved.stage1 is not None and solved.scenarios:
            replay_v2(system, solved.stage1, solved.scenarios[0], path)
        ws_records.append(
            _diagnostic_record(
                f"C_WS_pilot_{index + 1:02d}",
                solved.diagnostics,
                time.perf_counter() - replay_start,
            )
        )
    records.extend(ws_records)

    output_directory.mkdir(parents=True, exist_ok=True)
    with (output_directory / "solver_runtime_log.csv").open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    summary = {
        "seed": PILOT_SEED,
        "held_out_paths_per_cell_frozen": 218,
        "solve_records": len(records),
        "extensive_form_records": 3,
        "wait_and_see_records": 16,
        "solver_unresolved_count": sum(
            bool(row["solver_unresolved"]) for row in records
        ),
        "max_solve_seconds": max(
            float(row["solve_seconds"]) for row in records
        ),
        "total_solve_seconds": sum(
            float(row["solve_seconds"]) for row in records
        ),
        "total_replay_seconds": sum(
            float(row["replay_seconds"]) for row in records
        ),
        "records": records,
    }
    with (output_directory / "summary.json").open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("reconcile", "safety", "pilot"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
    )
    arguments = parser.parse_args()
    if arguments.command == "reconcile":
        output = arguments.output or Path(
            "results/mfe_v3_deterministic_reconciliation"
        )
        result = run_deterministic_reconciliation(
            arguments.root.resolve(),
            output.resolve(),
        )
        print(json.dumps(result, indent=2))
    elif arguments.command == "safety":
        output = arguments.output or Path("results/mfe_v3_c1_safety_audit")
        result = run_c1_safety_audit(
            arguments.root.resolve(),
            output.resolve(),
        )
        print(json.dumps(result, indent=2))
    elif arguments.command == "pilot":
        output = arguments.output or Path("results/mfe_v3_runtime_pilot")
        result = run_runtime_pilot(
            arguments.root.resolve(),
            output.resolve(),
        )
        # Intentionally omit any objective values from the runtime output.
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
