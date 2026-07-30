# Project Chameleon

Project Chameleon studies one question:

> How much internal information must a complex flexible energy resource
> disclose so that an external schedule is physically feasible, economically
> useful, and composable across time, activations, and uncertainty?

Battery and PV+BESS are the canonical model classes. The broader object is a
**capability contract**: an information projection of a resource's physical
flexibility.

## Current status

- Deterministic and minimal stochastic theory: complete and frozen.
- Propositions 1--18: consolidated into four structural results.
- Independent physical replay and regression suite: complete.
- Lean numerical paper validation: complete.
- Local numerical development: closed.
- Full powered market study: deferred to server/laboratory execution.
- Next work: manuscript drafting only.

## Read these first

1. [Final paper plan](docs/paper/THEORY_DISTILLATION_AND_PAPER_PLAN.md)
2. [Lean numerical report](docs/research/MFE_LEAN_PAPER_VALIDATION_REPORT.md)
3. [Recommended disclosure specification](docs/paper/RECOMMENDED_DISCLOSURE_SPECIFICATION.md)
4. [Current progress](PROJECT_PROGRESS.md)

## Final headline results

1. Exact time-local capability does not imply trajectory feasibility.
2. Lossless restricted models can admit compact exact prefix contracts, while
   lossy bidirectional operation with mode exclusivity can make the exact
   net-injection projection nonconvex.
3. One-shot reserve feasibility does not imply sequential composability;
   activation-conditioned reachable-state sets restore Markov sufficiency in
   the stated lossless model.
4. Under uncertainty, a marginal SOC interval or marginal belief is generally
   insufficient; scenario correspondence, information timing,
   nonanticipativity, and risk state can become contract fields.
5. In the final six-cell synthetic PV+BESS validation, `C1` reduced mean
   realized cost by 12.9%--16.1% relative to the `C_ASSOC` market proxy, with
   zero isolated non-delivery for both lines.

## Repository map

| Path | Purpose |
|---|---|
| `BLUEPRINT.md` | original comprehensive research blueprint |
| `docs/modeling/` | formal derivations, counterexamples, and Propositions 1--18 |
| `docs/paper/` | final paper architecture and disclosure specification |
| `docs/research/` | current authoritative numerical design and reports |
| `src/chameleon/` | tested theory examples, truth model, replay, and analysis |
| `tests/` | 77 regression and physical-consistency tests |
| `data/external/rts_gmlc/` | pinned public reproducible synthetic benchmark data |
| `results/` | only final active evidence and checksums |
| `papers/` | source literature and primary CAISO documents |

## Reproduce

Run all tests with one numerical thread:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
PYTHONPATH=src python -m pytest -q tests
```

Rebuild the lean tables and figure from the frozen paired records:

```bash
MPLCONFIGDIR=/tmp/chameleon-mpl \
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
PYTHONPATH=src python -m chameleon.mfe_lean_analysis
```

The RTS-GMLC inputs are authentic public benchmark files, but they are
synthetic. Nothing in this repository should describe them as observed CAISO
operating data.
