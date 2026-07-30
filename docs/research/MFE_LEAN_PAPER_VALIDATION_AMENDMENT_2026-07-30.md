# MFE lean paper-validation amendment

Date: 2026-07-30

Status: frozen before inspecting any contract-gap result from the seven
previously completed 54-cell checkpoints.

## 1. Reason for simplification

The 54-cell, 218-path design is a powered market-simulation study. It is not
required to support the paper's structural theory, relaxation counterexample,
market-proxy comparison, or disclosure-design implications. Local execution
also imposed unacceptable sustained CPU and thermal load.

The complete market experiment is deferred to a server or laboratory
environment. The local paper package uses a representative-regime validation
only. This decision is based on computational scope and hardware load, not on
observed contract rankings or cost gaps.

The seven completed full-design cell files are retained for provenance but
are excluded from the lean analysis.

## 2. Frozen representative cells

The lean grid is:

| Dimension | Levels |
|---|---|
| storage duration | 1 h, 2 h, 4 h |
| reserve requirement | 5%, 20% |
| initial SOC | fixed at 50% |
| PV error | fixed at sigma 0.08 |

This gives six cells spanning the two central physical stress dimensions:
energy duration and reserve demand.

## 3. Contract lines

- `C0-fixture`: static parameters `(15,35,35,50)`. No per-cell candidate
  fitting is performed.
- `C1`: recourse-aware `C1-v3` 1/99 envelope, optimized once against the
  deterministic day-ahead PV forecast.
- `C_ASSOC`: the frozen CAISO-style market proxy, optimized once against the
  deterministic day-ahead PV forecast.
- `C_WS`: pathwise wait-and-see lower-cost boundary, reported separately and
  never described as an implementable contract.

The already certified `C_full-32` sentinel results remain computational
evidence for the adaptive method. `C_full-32` is not rebuilt across the lean
grid.

## 4. Paths and execution

- 64 paired held-out paths per cell;
- existing disjoint held-out seed `2026080104`;
- identical AR(1) PV transformation;
- identical truth model, penalties, reserve activation, stage-2 optimizer,
  and independent replay;
- one process only;
- BLAS/OpenMP thread count fixed to one during execution;
- one cell at a time with a checkpoint after each cell.

No 2-percentage-point MDE claim is made. Confidence intervals are descriptive
paired uncertainty intervals over the 64 paths.

## 5. Paper claims permitted

The lean experiment may support:

1. directional and representative-regime cost/reliability comparisons between
   current-style `C_ASSOC` disclosure and the proposed `C1` envelope;
2. whether conclusions change between short/long storage and low/high reserve;
3. each contract's distance to the pathwise `C_WS` information bound;
4. mechanism consistency with the analytical counterexamples and exactness
   results.

It may not support:

- population-wide CAISO performance claims;
- 2pp powered non-delivery inference;
- claims covering all SOC or uncertainty levels;
- replacement of the deferred 54-cell market simulation;
- claims that RTS-GMLC is observed CAISO operating data.

## 6. Permanent local closure

After the six-cell report, no additional local grid, seed, threshold,
contract line, or numerical extension is added. Larger powered experiments
belong to future server/laboratory work.

