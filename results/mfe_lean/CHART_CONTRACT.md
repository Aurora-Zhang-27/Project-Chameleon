# Lean MFE chart contract

- Analytical question: across six representative duration/reserve regimes, how
  much realized-cost gap remains relative to pathwise wait-and-see, and how often
  does the fixed-policy two-call stress protocol fail?
- Scope: one RTS-GMLC-based synthetic PV+BESS system, fixed 50% initial SOC,
  fixed PV error scale 0.08, 64 paired held-out paths per cell, seed 2026080104.
- Chart family: two-panel categorical dot plot with one row per regime and one
  marker per contract line. A line chart is intentionally avoided because the
  duration settings are only three discrete design points.
- Panel A metric: mean paired realized-cost gap to C_WS, percent of mean C_WS
  cost. C_WS is the zero reference.
- Panel B metric: fraction of paths failing the preregistered fixed-policy
  sequential two-call stress protocol. It is not a calibrated probability of
  real-world reserve failure.
- Uncertainty: 95% normal intervals for paired mean cost gaps and Wilson 95%
  intervals for binary stress-failure rates.
- Palette: four muted categorical colors, reinforced by distinct marker shapes
  so the figure remains readable in grayscale.
- Output: `results/mfe_lean/figures/lean_frontier.png`, with the CSV regime table
  retained as the exact-value fallback.
- QA: inspect the exported PNG for clipping, legibility, correct zero/percentage
  axes, and agreement with the source CSV.
