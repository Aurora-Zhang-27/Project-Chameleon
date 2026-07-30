"""Low-load analysis and reporting for the frozen lean MFE."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, stdev


LINES = ("C0-fixture", "C1", "C_ASSOC", "C_WS")
COMPARISONS = (
    ("C1", "C_ASSOC"),
    ("C0-fixture", "C_ASSOC"),
    ("C1", "C_WS"),
    ("C_ASSOC", "C_WS"),
)
EXPECTED_PATHS = 64


def _as_bool(value: str) -> bool:
    if value == "True":
        return True
    if value == "False":
        return False
    raise ValueError(f"Unexpected Boolean encoding: {value!r}")


def _mean_ci(values: list[float]) -> tuple[float, float, float]:
    center = mean(values)
    if len(values) < 2:
        return center, center, center
    half = 1.96 * stdev(values) / math.sqrt(len(values))
    return center, center - half, center + half


def _wilson(successes: int, total: int) -> tuple[float, float, float]:
    z = 1.96
    rate = successes / total
    denom = 1 + z * z / total
    center = (rate + z * z / (2 * total)) / denom
    half = (
        z
        * math.sqrt(rate * (1 - rate) / total + z * z / (4 * total * total))
        / denom
    )
    return rate, max(0.0, center - half), min(1.0, center + half)


def load_and_validate(source: Path) -> tuple[list[dict[str, str]], dict]:
    with source.open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    required = {
        "label",
        "duration_hours",
        "initial_soc_fraction",
        "sigma",
        "reserve_fraction",
        "path_id",
        "line",
        "realized_cost_usd",
        "isolated_non_delivery",
        "sequential_non_delivery",
        "physical_replay_valid",
        "cost_reconciled",
        "solver_unresolved",
    }
    missing_columns = sorted(required - set(rows[0])) if rows else sorted(required)
    keys = [(row["label"], row["path_id"], row["line"]) for row in rows]
    duplicate_count = len(keys) - len(set(keys))

    paired: dict[tuple[str, str], dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        paired[(row["label"], row["path_id"])][row["line"]] = row

    cell_line_counts = Counter((row["label"], row["line"]) for row in rows)
    expected_count_failures = {
        f"{label}|{line}": count
        for (label, line), count in cell_line_counts.items()
        if count != EXPECTED_PATHS
    }
    incomplete_pairs = sum(set(group) != set(LINES) for group in paired.values())
    replay_failures = sum(
        not _as_bool(row["physical_replay_valid"]) for row in rows
    )
    cost_failures = sum(not _as_bool(row["cost_reconciled"]) for row in rows)
    unresolved = sum(_as_bool(row["solver_unresolved"]) for row in rows)
    nonfinite_costs = sum(
        not math.isfinite(float(row["realized_cost_usd"])) for row in rows
    )

    ws_bound_violations = []
    for pair_key, group in paired.items():
        if set(group) != set(LINES):
            continue
        ws_cost = float(group["C_WS"]["realized_cost_usd"])
        for line in LINES[:-1]:
            gap = ws_cost - float(group[line]["realized_cost_usd"])
            if gap > 1e-5:
                ws_bound_violations.append((*pair_key, line, gap))

    labels = sorted({row["label"] for row in rows})
    expected_rows = len(labels) * EXPECTED_PATHS * len(LINES)
    valid = not any(
        (
            missing_columns,
            duplicate_count,
            expected_count_failures,
            incomplete_pairs,
            replay_failures,
            cost_failures,
            unresolved,
            nonfinite_costs,
            ws_bound_violations,
            len(rows) != expected_rows,
        )
    )
    summary = {
        "valid": valid,
        "row_count": len(rows),
        "expected_row_count": expected_rows,
        "cell_count": len(labels),
        "paired_path_count": len(paired),
        "duplicate_key_count": duplicate_count,
        "incomplete_pair_count": incomplete_pairs,
        "unexpected_cell_line_counts": expected_count_failures,
        "physical_replay_failures": replay_failures,
        "cost_reconciliation_failures": cost_failures,
        "solver_unresolved_count": unresolved,
        "nonfinite_cost_count": nonfinite_costs,
        "ws_lower_bound_violation_count": len(ws_bound_violations),
        "max_ws_lower_bound_violation_usd": max(
            (item[-1] for item in ws_bound_violations), default=0.0
        ),
    }
    if not valid:
        raise ValueError(f"Lean MFE validation failed: {summary}")
    return rows, summary


def aggregate_regimes(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["label"], row["line"])].append(row)

    ws_means = {
        label: mean(
            float(row["realized_cost_usd"])
            for row in grouped[(label, "C_WS")]
        )
        for label, _line in grouped
    }
    output = []
    for (label, line), group in sorted(grouped.items()):
        costs = [float(row["realized_cost_usd"]) for row in group]
        cost_mean, cost_lo, cost_hi = _mean_ci(costs)
        ws_cost = ws_means[label]
        isolated = sum(_as_bool(row["isolated_non_delivery"]) for row in group)
        sequential = sum(
            _as_bool(row["sequential_non_delivery"]) for row in group
        )
        iso_rate, iso_lo, iso_hi = _wilson(isolated, len(group))
        seq_rate, seq_lo, seq_hi = _wilson(sequential, len(group))
        first = group[0]
        output.append(
            {
                "label": label,
                "duration_hours": int(first["duration_hours"]),
                "reserve_fraction": float(first["reserve_fraction"]),
                "line": line,
                "paths": len(group),
                "mean_realized_cost_usd": cost_mean,
                "cost_ci95_low_usd": cost_lo,
                "cost_ci95_high_usd": cost_hi,
                "mean_cost_gap_to_cws_usd": cost_mean - ws_cost,
                "mean_cost_gap_to_cws_percent": 100
                * (cost_mean - ws_cost)
                / ws_cost,
                "isolated_non_delivery_rate": iso_rate,
                "isolated_ci95_low": iso_lo,
                "isolated_ci95_high": iso_hi,
                "sequential_stress_failure_rate": seq_rate,
                "sequential_ci95_low": seq_lo,
                "sequential_ci95_high": seq_hi,
                "mean_solve_seconds": mean(
                    float(row["solve_seconds"]) for row in group
                ),
            }
        )
    return output


def paired_statistics(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    paired: dict[tuple[str, str], dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        paired[(row["label"], row["path_id"])][row["line"]] = row

    labels = sorted({label for label, _path in paired})
    output = []
    for label in labels:
        groups = [
            group for (item_label, _path), group in paired.items()
            if item_label == label
        ]
        first = groups[0][LINES[0]]
        for line_a, line_b in COMPARISONS:
            cost_diffs = [
                float(group[line_a]["realized_cost_usd"])
                - float(group[line_b]["realized_cost_usd"])
                for group in groups
            ]
            iso_diffs = [
                float(_as_bool(group[line_a]["isolated_non_delivery"]))
                - float(_as_bool(group[line_b]["isolated_non_delivery"]))
                for group in groups
            ]
            seq_diffs = [
                float(_as_bool(group[line_a]["sequential_non_delivery"]))
                - float(_as_bool(group[line_b]["sequential_non_delivery"]))
                for group in groups
            ]
            cost_mean, cost_lo, cost_hi = _mean_ci(cost_diffs)
            iso_mean, iso_lo, iso_hi = _mean_ci(iso_diffs)
            seq_mean, seq_lo, seq_hi = _mean_ci(seq_diffs)
            baseline = mean(
                float(group[line_b]["realized_cost_usd"]) for group in groups
            )
            output.append(
                {
                    "label": label,
                    "duration_hours": int(first["duration_hours"]),
                    "reserve_fraction": float(first["reserve_fraction"]),
                    "line_a": line_a,
                    "line_b": line_b,
                    "paths": len(groups),
                    "paired_cost_difference_usd": cost_mean,
                    "paired_cost_ci95_low_usd": cost_lo,
                    "paired_cost_ci95_high_usd": cost_hi,
                    "paired_cost_difference_percent_of_b": 100
                    * cost_mean
                    / baseline,
                    "paired_isolated_rate_difference": iso_mean,
                    "paired_isolated_ci95_low": iso_lo,
                    "paired_isolated_ci95_high": iso_hi,
                    "paired_sequential_rate_difference": seq_mean,
                    "paired_sequential_ci95_low": seq_lo,
                    "paired_sequential_ci95_high": seq_hi,
                }
            )
    return output


def _write_csv(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def make_figure(regimes: list[dict[str, object]], output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = sorted(
        {str(row["label"]) for row in regimes},
        key=lambda label: (
            int(label.split("_")[1][1:]),
            int(label.split("_")[2][1:]),
        ),
    )
    display = {
        label: (
            f"{int(next(r['duration_hours'] for r in regimes if r['label']==label))}h, "
            f"{100 * float(next(r['reserve_fraction'] for r in regimes if r['label']==label)):.0f}% reserve"
        )
        for label in labels
    }
    line_order = ("C0-fixture", "C1", "C_ASSOC", "C_WS")
    colors = {
        "C0-fixture": "#6B7280",
        "C1": "#0072B2",
        "C_ASSOC": "#D55E00",
        "C_WS": "#009E73",
    }
    markers = {
        "C0-fixture": "s",
        "C1": "o",
        "C_ASSOC": "^",
        "C_WS": "D",
    }
    offsets = {
        "C0-fixture": -0.24,
        "C1": -0.08,
        "C_ASSOC": 0.08,
        "C_WS": 0.24,
    }
    lookup = {(row["label"], row["line"]): row for row in regimes}

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 6.4), sharey=True)
    ybase = list(range(len(labels)))
    for line in line_order:
        ys = [y + offsets[line] for y in ybase]
        cost_x = [
            float(lookup[(label, line)]["mean_cost_gap_to_cws_percent"])
            for label in labels
        ]
        axes[0].scatter(
            cost_x,
            ys,
            label=line,
            color=colors[line],
            marker=markers[line],
            s=46,
            zorder=3,
        )
        seq_x = [
            100
            * float(
                lookup[(label, line)]["sequential_stress_failure_rate"]
            )
            for label in labels
        ]
        seq_lo = [
            100
            * (
                float(lookup[(label, line)]["sequential_stress_failure_rate"])
                - float(lookup[(label, line)]["sequential_ci95_low"])
            )
            for label in labels
        ]
        seq_hi = [
            100
            * (
                float(lookup[(label, line)]["sequential_ci95_high"])
                - float(lookup[(label, line)]["sequential_stress_failure_rate"])
            )
            for label in labels
        ]
        axes[1].errorbar(
            seq_x,
            ys,
            xerr=[seq_lo, seq_hi],
            fmt=markers[line],
            color=colors[line],
            markersize=6,
            capsize=2,
            linestyle="none",
            zorder=3,
        )

    axes[0].axvline(0, color="#9CA3AF", linewidth=0.8)
    axes[0].set_xlabel("Mean realized-cost gap to C_WS (%)")
    axes[0].set_title("A. Cost of information restriction")
    axes[1].set_xlim(-3, 103)
    axes[1].set_xlabel("Fixed-policy sequential stress failures (%)")
    axes[1].set_title("B. Dynamic composability stress")
    axes[0].set_yticks(ybase, [display[label] for label in labels])
    axes[0].invert_yaxis()
    for axis in axes:
        axis.grid(axis="x", color="#E5E7EB", linewidth=0.8)
        axis.spines[["top", "right", "left"]].set_visible(False)
        axis.tick_params(axis="y", length=0)

    handles, labels_legend = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels_legend,
        loc="lower center",
        ncol=4,
        frameon=False,
        bbox_to_anchor=(0.5, 0.045),
    )
    fig.suptitle(
        "Lean contract comparison across six representative PV+BESS regimes",
        fontsize=14,
        y=0.99,
    )
    fig.text(
        0.5,
        0.935,
        "RTS-GMLC synthetic benchmark; 64 paired paths/cell; 50% initial SOC; PV error scale 0.08",
        ha="center",
        fontsize=9,
        color="#4B5563",
    )
    fig.text(
        0.5,
        0.012,
        "Sequential failures are from a fixed-policy two-call stress protocol, not real-world failure probabilities.",
        ha="center",
        fontsize=8.5,
        color="#4B5563",
    )
    fig.tight_layout(rect=(0, 0.105, 1, 0.92))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(fig)


def analyze(source: Path, output_dir: Path) -> None:
    rows, validation = load_and_validate(source)
    regimes = aggregate_regimes(rows)
    paired = paired_statistics(rows)
    _write_csv(output_dir / "regime_table.csv", regimes)
    _write_csv(output_dir / "paired_statistics.csv", paired)
    (output_dir / "validation_summary.json").write_text(
        json.dumps(validation, indent=2) + "\n"
    )
    make_figure(regimes, output_dir / "figures" / "lean_frontier.png")
    print(json.dumps(validation, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("results/mfe_lean/held_out_records.csv"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/mfe_lean"),
    )
    args = parser.parse_args()
    analyze(args.source, args.output_dir)


if __name__ == "__main__":
    main()
