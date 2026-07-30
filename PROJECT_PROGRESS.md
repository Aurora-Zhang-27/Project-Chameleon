# Project Chameleon — current status

Updated: 2026-07-30

## Status

The research-development phase is complete.

| Workstream | Status |
|---|---|
| deterministic small-model theory | complete and frozen |
| finite-tree stochastic theory | complete and frozen |
| Propositions 1--18 | consolidated into four main structural results |
| independent physical replay | complete |
| deterministic 24-hour reconciliation | complete |
| C1 safety audit | complete |
| relaxation exactness investigation | complete; full LP rejected |
| adaptive partial-integrality certificate | complete |
| lean numerical paper validation | complete |
| local numerical extensions | permanently closed |
| full powered market study | deferred to server/laboratory |
| manuscript drafting | next phase |

## Final numerical evidence

- 6 representative duration/reserve cells.
- 64 paired held-out paths per cell.
- 4 information lines.
- 1,536 total records.
- 0 duplicate keys.
- 0 incomplete path pairs.
- 0 solver-unresolved records.
- 0 independent replay failures.
- 0 cost-reconciliation failures.
- 0 violations of the pathwise `C_WS` lower-cost relation.
- 77 regression tests passed.

Across the six cells:

- `C1` cost was 12.9%--16.1% below `C_ASSOC`;
- `C1` was 4.2%--6.1% above `C_WS`;
- `C_ASSOC` was 20.0%--24.9% above `C_WS`;
- both `C1` and `C_ASSOC` had zero isolated non-delivery;
- sequential two-call stress remained regime-dependent.

## Authoritative files

- [Paper plan](docs/paper/THEORY_DISTILLATION_AND_PAPER_PLAN.md)
- [Lean validation report](docs/research/MFE_LEAN_PAPER_VALIDATION_REPORT.md)
- [Relaxation gate report](docs/research/MFE_V4_RELAXATION_GATE_REPORT.md)
- [Disclosure specification](docs/paper/RECOMMENDED_DISCLOSURE_SPECIFICATION.md)
- [Exact regime table](results/mfe_lean/regime_table.csv)
- [Paired statistics](results/mfe_lean/paired_statistics.csv)
