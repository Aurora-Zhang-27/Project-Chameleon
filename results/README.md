# Active results

Only paper-facing evidence and the current reproducible full-binary result set
remain in this directory.

## `mfe_v3_lightweight_full_binary/` — current main result

- `v3full_*.json`: six duration-by-reserve cells, including full stage-1 solver
  diagnostics and 768 paired held-out line-path records.
- `regime_summary.csv`: exact line-by-cell aggregates.
- `paired_statistics.csv`: paired `C1` comparisons against `C_ASSOC` and
  `C_full-32`.
- `validation_summary.json`: structural, replay, reconciliation, and solver
  validation.
- `figures/full_binary_frontier.png`: paper-facing comparison against the
  full-binary benchmark.

All six `C_full-32` solves retain the complete 24-hour charge/discharge mode
binaries and reached a relative gap at or below 0.1%.

## `mfe_final/staircase/`

Three completed `C_full-32` sentinel certificates and the corresponding C0
candidate fits. All passed independent replay.

## `mfe_lean/` — superseded comparison retained for provenance

- `held_out_records.csv`: 1,536 frozen path-level records.
- `regime_table.csv`: exact line-by-cell aggregates.
- `paired_statistics.csv`: paired differences and uncertainty intervals.
- `validation_summary.json`: structural and replay validation.
- `figures/lean_frontier.png`: paper-facing summary figure.
- `CHART_CONTRACT.md`: the figure's metric and presentation contract.

`SHA256SUMS.txt` covers every active result file except itself.
