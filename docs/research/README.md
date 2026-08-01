# Current research evidence

This directory contains only the authoritative final numerical documents.
Superseded intermediate preregistrations, runtime logs, and stopped-run
artifacts were removed from the publication package after their verified
conclusions were consolidated into the final reports.

## Read in this order

1. [Data provenance audit](MFE_V4_DATA_PROVENANCE_AUDIT.md)
2. [C_ASSOC market-proxy specification](C_ASSOC_MARKET_PROXY_SPECIFICATION.md)
3. [Relaxation gate report](MFE_V4_RELAXATION_GATE_REPORT.md)
4. [Scenario-staircase amendment](MFE_FINAL_SCENARIO_STAIRCASE_AMENDMENT_2026-07-30.md)
5. [Scenario-staircase decision](MFE_FINAL_STAIRCASE_GATE_DECISION.md)
6. [Lean-design amendment](MFE_LEAN_PAPER_VALIDATION_AMENDMENT_2026-07-30.md)
7. [Full-binary lightweight pilot note](MFE_V3_LIGHTWEIGHT_FULL_BINARY_PILOT_2026-08-01.md)
8. [Current full-binary lightweight validation report](MFE_LEAN_PAPER_VALIDATION_REPORT.md)

## Final status

- Full continuous mode relaxation is not contract-exact.
- The adaptive partial-integrality sandwich method is retained as a diagnostic
  negative-result route rather than the current main solver.
- All six lightweight `C_full-32` cells retained complete mode binaries and
  reached a relative gap at or below 0.1%.
- The final local comparison uses six representative cells and 32 paired
  held-out paths per cell, producing 768 validated line-path records.
- The powered 54-cell study is deferred to server/laboratory execution.

The current report records the relevant v1--v4 design changes, the reason for
reducing repeated solve counts rather than physical fidelity, and the limits
needed to interpret the published results.
