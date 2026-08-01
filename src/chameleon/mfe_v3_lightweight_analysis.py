"""Validate and summarize the lightweight full-binary MFE v3 results."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, stdev


LINES = ("C0-fixture", "C1", "C_ASSOC", "C_full-32")
EXPECTED_CELLS = 6
EXPECTED_PATHS = 32


def _mean_ci(values: list[float]) -> tuple[float, float, float]:
    center = mean(values)
    half = 0.0 if len(values) < 2 else 1.96 * stdev(values) / math.sqrt(len(values))
    return center, center - half, center + half


def load_and_validate(source: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    payloads = []
    for path in sorted(source.glob("v3full_*.json")):
        with path.open(encoding="utf-8") as stream:
            payloads.append(json.load(stream))
    rows = [row for payload in payloads for row in payload["held_out_records"]]
    keys = [(row["label"], row["path_id"], row["line"]) for row in rows]
    counts = Counter((row["label"], row["line"]) for row in rows)
    paired: dict[tuple[str, int], set[str]] = defaultdict(set)
    for row in rows:
        paired[(str(row["label"]), int(row["path_id"]))].add(str(row["line"]))
    construction = [payload["construction_validation"] for payload in payloads]
    summary = {
        "valid": True,
        "cell_count": len(payloads),
        "held_out_record_count": len(rows),
        "expected_record_count": EXPECTED_CELLS * EXPECTED_PATHS * len(LINES),
        "duplicate_key_count": len(keys) - len(set(keys)),
        "incomplete_pair_count": sum(group != set(LINES) for group in paired.values()),
        "unexpected_cell_line_count": sum(count != EXPECTED_PATHS for count in counts.values()),
        "construction_physical_failures": sum(item["physical_failures"] for item in construction),
        "construction_cost_reconciliation_failures": sum(
            item["cost_reconciliation_failures"] for item in construction
        ),
        "held_out_physical_failures": sum(not row["physical_replay_valid"] for row in rows),
        "held_out_cost_reconciliation_failures": sum(not row["cost_reconciled"] for row in rows),
        "held_out_solver_unresolved": sum(row["stage2_solver_unresolved"] for row in rows),
        "full_binary_solve_seconds": sum(
            payload["stage1"]["C_full-32"]["solve_seconds"] for payload in payloads
        ),
        "max_full_binary_solve_seconds": max(
            payload["stage1"]["C_full-32"]["solve_seconds"] for payload in payloads
        ),
    }
    summary["valid"] = not any(
        (
            summary["cell_count"] != EXPECTED_CELLS,
            summary["held_out_record_count"] != summary["expected_record_count"],
            summary["duplicate_key_count"],
            summary["incomplete_pair_count"],
            summary["unexpected_cell_line_count"],
            summary["construction_physical_failures"],
            summary["construction_cost_reconciliation_failures"],
            summary["held_out_physical_failures"],
            summary["held_out_cost_reconciliation_failures"],
            summary["held_out_solver_unresolved"],
        )
    )
    if not summary["valid"]:
        raise ValueError(f"Lightweight full-binary validation failed: {summary}")
    return rows, summary


def aggregate(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["label"]), str(row["line"]))].append(row)
    output = []
    for label in sorted({label for label, _line in grouped}):
        full_mean = mean(
            float(row["realized_cost_usd"])
            for row in grouped[(label, "C_full-32")]
        )
        for line in LINES:
            group = grouped[(label, line)]
            values = [float(row["realized_cost_usd"]) for row in group]
            center, low, high = _mean_ci(values)
            first = group[0]
            output.append(
                {
                    "label": label,
                    "duration_hours": int(first["duration_hours"]),
                    "reserve_fraction": float(first["reserve_fraction"]),
                    "line": line,
                    "paths": len(group),
                    "mean_realized_cost_usd": center,
                    "cost_ci95_low_usd": low,
                    "cost_ci95_high_usd": high,
                    "mean_gap_to_c_full_usd": center - full_mean,
                    "mean_gap_to_c_full_percent": 100 * (center - full_mean) / full_mean,
                    "physical_failure_count": sum(not row["physical_replay_valid"] for row in group),
                    "cost_failure_count": sum(not row["cost_reconciled"] for row in group),
                    "solver_unresolved_count": sum(row["stage2_solver_unresolved"] for row in group),
                }
            )
    return output


def paired(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, int], dict[str, dict[str, object]]] = defaultdict(dict)
    for row in rows:
        groups[(str(row["label"]), int(row["path_id"]))][str(row["line"])] = row
    output = []
    for label in sorted({label for label, _path in groups}):
        paths = [group for (item, _path), group in groups.items() if item == label]
        first = paths[0]["C1"]
        for line_a, line_b in (("C1", "C_ASSOC"), ("C1", "C_full-32")):
            differences = [
                float(group[line_a]["realized_cost_usd"])
                - float(group[line_b]["realized_cost_usd"])
                for group in paths
            ]
            center, low, high = _mean_ci(differences)
            baseline = mean(float(group[line_b]["realized_cost_usd"]) for group in paths)
            output.append(
                {
                    "label": label,
                    "duration_hours": int(first["duration_hours"]),
                    "reserve_fraction": float(first["reserve_fraction"]),
                    "line_a": line_a,
                    "line_b": line_b,
                    "paths": len(paths),
                    "paired_mean_difference_usd": center,
                    "paired_ci95_low_usd": low,
                    "paired_ci95_high_usd": high,
                    "paired_difference_percent_of_b": 100 * center / baseline,
                }
            )
    return output


def _write_csv(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def make_figure(regimes: list[dict[str, object]], output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    labels = sorted(
        {str(row["label"]) for row in regimes},
        key=lambda label: (
            int(label.split("_")[1][1:]),
            int(label.split("_")[2][1:]),
        ),
    )
    lookup = {(str(row["label"]), str(row["line"])): row for row in regimes}
    display = [
        f"{lookup[(label, 'C1')]['duration_hours']}h / "
        f"{100 * float(lookup[(label, 'C1')]['reserve_fraction']):.0f}%"
        for label in labels
    ]
    lines = ("C0-fixture", "C1", "C_ASSOC")
    colors = {"C0-fixture": "#7A8792", "C1": "#245A7A", "C_ASSOC": "#D07A32"}
    hatches = {"C0-fixture": "//", "C1": "", "C_ASSOC": ".."}
    y = np.arange(len(labels))
    height = 0.23
    fig, ax = plt.subplots(figsize=(10.6, 6.1))
    for offset, line in zip((-height, 0.0, height), lines):
        values = [float(lookup[(label, line)]["mean_gap_to_c_full_percent"]) for label in labels]
        bars = ax.barh(
            y + offset,
            values,
            height=height * 0.86,
            label=line,
            color=colors[line],
            edgecolor="#26343D",
            linewidth=0.5,
            hatch=hatches[line],
        )
        ax.bar_label(bars, labels=[f"{value:.1f}%" for value in values], padding=3, fontsize=8)
    ax.set_yticks(y, display)
    ax.invert_yaxis()
    ax.set_xlim(left=0)
    ax.set_xlabel("Mean realized-cost gap to full-binary C_full-32 (%)")
    fig.text(
        0.075,
        0.965,
        "Six-cell cost comparison against the full-binary benchmark",
        fontsize=16,
        weight="bold",
        color="#17212B",
    )
    fig.text(
        0.075,
        0.937,
        "24-hour model; 32 paired held-out paths per cell; descriptive means",
        fontsize=9,
        color="#65727D",
    )
    ax.grid(axis="x", color="#D5DCE1", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(
        frameon=False,
        ncol=3,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.09),
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.91))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=190, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    source = root / "results/mfe_v3_lightweight_full_binary"
    rows, validation = load_and_validate(source)
    regimes = aggregate(rows)
    statistics = paired(rows)
    _write_csv(source / "regime_summary.csv", regimes)
    _write_csv(source / "paired_statistics.csv", statistics)
    with (source / "validation_summary.json").open("w", encoding="utf-8") as stream:
        json.dump(validation, stream, indent=2)
    make_figure(regimes, source / "figures/full_binary_frontier.png")
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
