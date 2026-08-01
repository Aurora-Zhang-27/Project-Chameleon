# Project Chameleon — current status

Updated: 2026-08-01

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
| adaptive partial-integrality certificate | retained as a negative-result diagnostic |
| lightweight full-binary numerical validation | complete |
| current local numerical stage | complete |
| full powered market study | deferred to server/laboratory |
| manuscript drafting | next phase |

## Final numerical evidence

- 6 representative duration/reserve cells.
- 32 paired held-out paths per cell.
- 4 information lines.
- 768 total records.
- 0 duplicate keys.
- 0 incomplete path pairs.
- 0 solver-unresolved records.
- 0 independent replay failures.
- 0 cost-reconciliation failures.
- 0 construction or held-out physical replay failures.
- all six `C_full-32` solves reached a gap at or below 0.1%.
- 79 regression tests passed.

Across the six cells:

- `C1` cost was 10.66%--13.94% below `C_ASSOC`;
- `C1` was 1.06%--2.55% above `C_full-32`;
- both `C1` and `C_ASSOC` had zero isolated non-delivery;
- sequential two-call stress remained regime-dependent.

## Authoritative files

- [Complete Chinese process-and-results report](docs/paper/PROJECT_CHAMELEON_COMPLETE_PROCESS_AND_RESULTS_ZH.md)
- [Typeset Chinese PDF](output/pdf/Project_Chameleon_完整研究过程与成果_中文.pdf)
- [Paper plan](docs/paper/THEORY_DISTILLATION_AND_PAPER_PLAN.md)
- [Full-binary lightweight validation report](docs/research/MFE_LEAN_PAPER_VALIDATION_REPORT.md)
- [Relaxation gate report](docs/research/MFE_V4_RELAXATION_GATE_REPORT.md)
- [Disclosure specification](docs/paper/RECOMMENDED_DISCLOSURE_SPECIFICATION.md)
- [Exact regime table](results/mfe_v3_lightweight_full_binary/regime_summary.csv)
- [Paired statistics](results/mfe_v3_lightweight_full_binary/paired_statistics.csv)
