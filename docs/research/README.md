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
7. [Final lean validation report](MFE_LEAN_PAPER_VALIDATION_REPORT.md)

## Final status

- Full continuous mode relaxation is not contract-exact.
- The adaptive partial-integrality sandwich method is certificate-generating
  when it terminates with complementary relaxed actions.
- Three `C_full-32` sentinel cases were certified and replay-valid.
- The final local comparison uses six representative cells and 64 paired
  held-out paths per cell.
- The powered 54-cell study is deferred to server/laboratory execution.

The final lean report records the relevant v1--v4 design changes, stop
decisions, and limitations needed to interpret the published results.
