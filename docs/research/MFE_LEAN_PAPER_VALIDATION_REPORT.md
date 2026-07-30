# MFE lean paper-validation report

Date: 2026-07-30

Status: **complete; local numerical development permanently closed.**

## 1. Bottom line

The reduced experiment is sufficient for a theory paper's numerical
validation. It does not replace a powered market study.

Across six representative PV+BESS regimes, the recourse-aware intertemporal
contract `C1`:

- delivered every isolated upward and downward reserve call on all 384 paired
  path-cell observations;
- reduced mean realized cost by **12.9%–16.1%** relative to the frozen
  `C_ASSOC` market proxy;
- remained only **4.2%–6.1%** above the pathwise wait-and-see cost boundary,
  compared with **20.0%–24.9%** for `C_ASSOC`;
- improved fixed-policy two-call stress performance in three longer-duration
  cells, while providing no improvement in the three cells where both
  contracts failed every stress path.

The safe interpretation is:

> In this reproducible synthetic benchmark, adding recourse-aware
> intertemporal disclosure recovered substantial economic value without
> reducing one-shot physical delivery. Sequential composability still depended
> on duration and reserve stress and cannot be inferred from one-shot
> feasibility alone.

## 2. Why the design was reduced

The preregistered 54-cell, 218-path design is a powered market-simulation
study. Its repeated extensive-form mixed-integer solves caused unacceptable
local thermal load and are not required to validate the paper's structural
theory.

The lean design was frozen before inspecting the seven checkpoints produced
by the interrupted full-grid run. Those seven files remain provenance only
and are excluded here. The governing amendment is
[`MFE_LEAN_PAPER_VALIDATION_AMENDMENT_2026-07-30.md`](MFE_LEAN_PAPER_VALIDATION_AMENDMENT_2026-07-30.md).

## 3. Experimental scope

| Item | Frozen choice |
|---|---|
| resource | one PV+BESS at a four-unit single-node benchmark |
| source data | RTS-GMLC public reproducible **synthetic benchmark**, not observed CAISO operations |
| horizon | 24 hours |
| storage duration | 1, 2, and 4 hours |
| reserve requirement | 5% and 20% |
| initial SOC | 50% |
| PV error scale | 0.08 |
| held-out paths | 64 paired paths per cell |
| held-out seed | 2026080104 |
| cells | 6 |
| contract lines | `C0-fixture`, `C1`, `C_ASSOC`, `C_WS` |
| execution | one process, one BLAS/OpenMP thread |

`C0-fixture` uses the frozen static tuple `(15,35,35,50)` and is not refitted
per cell. `C1` is the v3 recourse-aware 1/99 inner envelope. `C_ASSOC` is a
CAISO-style battery-rule **market proxy**, not a claim that the entire CAISO
market has been reproduced. `C_WS` observes each path before its stage-1
choice; it is a lower-cost information boundary, not an implementable
contract.

## 4. Execution and validation

The six-cell run completed in approximately 25 seconds. Mean single-path solve
time across the aggregated line-cell results was 0.014 seconds.

The consolidated file contains 1,536 records:

\[
6\ \text{cells}\times64\ \text{paths}\times4\ \text{lines}=1{,}536.
\]

Independent validation found:

| Check | Result |
|---|---:|
| duplicate `(cell,path,line)` keys | 0 |
| incomplete four-line path pairs | 0 |
| unexpected line-cell counts | 0 |
| independent physical replay failures | 0 |
| independent cost-reconciliation failures | 0 |
| solver-unresolved records | 0 |
| nonfinite costs | 0 |
| pathwise violations of `C_WS <= contract cost` | 0 |

All comparisons use common random numbers. Cost intervals are paired
normal-approximation 95% intervals. Binary stress-rate intervals in the
regime table are Wilson 95% intervals. These intervals describe the 64
registered paths; they are not population-level CAISO inference.

## 5. Main cost result

### 5.1 `C1` relative to the market proxy

Negative values mean that `C1` is cheaper.

| Duration | Reserve | Paired mean `C1-C_ASSOC` | 95% interval | Relative to `C_ASSOC` |
|---:|---:|---:|---:|---:|
| 1 h | 5% | -$32,370 | [-$46,159, -$18,581] | -13.95% |
| 1 h | 20% | -$40,595 | [-$53,948, -$27,241] | -16.14% |
| 2 h | 5% | -$29,590 | [-$43,617, -$15,563] | -12.94% |
| 2 h | 20% | -$39,014 | [-$51,572, -$26,456] | -15.52% |
| 4 h | 5% | -$30,002 | [-$44,026, -$15,978] | -13.16% |
| 4 h | 20% | -$37,660 | [-$49,203, -$26,117] | -15.02% |

The sign is the same in every registered cell, and every paired 95% interval
excludes zero. Within this design, the finding is not driven by one duration
or one reserve tier.

### 5.2 Distance from the information boundary

| Duration | Reserve | `C0-fixture` gap | `C1` gap | `C_ASSOC` gap |
|---:|---:|---:|---:|---:|
| 1 h | 5% | 21.60% | 4.63% | 21.60% |
| 1 h | 20% | 23.45% | 4.66% | 24.79% |
| 2 h | 5% | 19.98% | 4.46% | 19.99% |
| 2 h | 20% | 20.71% | 5.52% | 24.90% |
| 4 h | 5% | 19.95% | 4.16% | 19.95% |
| 4 h | 20% | 20.54% | 6.11% | 24.86% |

These are mean realized-cost gaps relative to mean `C_WS` cost. They measure
the economic price of restricted information in this model, not a universal
market-efficiency loss.

## 6. Delivery and sequential stress

All four lines had zero isolated non-delivery on all six cells. Thus the cost
comparison does not trade lower cost against registered one-shot physical
delivery.

The fixed-policy sequential stress protocol deliberately makes two reserve
calls without reoptimizing the remaining policy:

| Duration | Reserve | `C0-fixture` | `C1` | `C_ASSOC` | `C_WS` |
|---:|---:|---:|---:|---:|---:|
| 1 h | 5% | 100.0% | 100.0% | 100.0% | 100.0% |
| 1 h | 20% | 100.0% | 100.0% | 100.0% | 100.0% |
| 2 h | 5% | 65.6% | 0.0% | 65.6% | 100.0% |
| 2 h | 20% | 100.0% | 100.0% | 100.0% | 100.0% |
| 4 h | 5% | 64.1% | 0.0% | 64.1% | 100.0% |
| 4 h | 20% | 65.6% | 0.0% | 59.4% | 100.0% |

These percentages are stress failures, not observed or forecast real-world
failure probabilities. `C_WS` minimizes cost with pathwise information but is
not optimized for the later two-call protocol; its 100% stress failure is
therefore not a contradiction and confirms that wait-and-see cost optimality
is not sequential robustness.

The result supports, rather than replaces, the analytical sequential
counterexample: one-shot feasibility and even full path information do not
make an unpriced, unmodelled second activation automatically composable.

## 7. Relaxation result retained in the paper

The failed full-LP shortcut is a substantive numerical result:

- full physical MILP cost: $201,327.897881;
- all-mode relaxed LP cost: $201,322.091094;
- maximum simultaneous charge/discharge: 10.625 MW;
- physical recourse cost after fixing the relaxed stage-1 tuple:
  $204,203.165340.

Thus reserve-conditioned downward flexibility can make simultaneous
charge/discharge economically useful inside the relaxation even with positive
losses and throughput costs. The relaxed tuple is cheaper mathematically,
physically unrealizable as stated, and more expensive after physical repair.

The companion positive result is the partial-relaxation sandwich certificate:
when the adaptive partial problem terminates with complementary relaxed power
actions, mode recovery supplies a feasible full-MILP point at the relaxation
lower bound, certifying equality within solver tolerance. The three frozen
`C_full-32` sentinel cases were certified and replay-valid; the complete
54-cell rebuild is intentionally deferred.

See [`MFE_V4_RELAXATION_GATE_REPORT.md`](MFE_V4_RELAXATION_GATE_REPORT.md) and
[`MFE_FINAL_STAIRCASE_GATE_DECISION.md`](MFE_FINAL_STAIRCASE_GATE_DECISION.md).

## 8. Paper-facing conclusion

The lean result selects the following descriptive branch:

> The current-style proxy leaves material value on the table in every tested
> regime. A recourse-aware intertemporal envelope recovers most of the
> wait-and-see cost gap without sacrificing isolated delivery. Dynamic
> composability remains a separate disclosure problem and becomes binding
> under short duration or high reserve stress.

This supports the paper's proposed disclosure band:

1. schedule and reserve fields;
2. explicit activation semantics;
3. intertemporal energy envelopes;
4. state/terminal boundaries and conversion conventions;
5. activation-conditioned reachable-state information when repeated calls
   matter.

The experiment does not price every possible disclosure field. It supplies a
lower-complexity empirical anchor for the theoretically derived band.

## 9. What remains unsupported

- No claim about observed CAISO cost savings or reliability.
- No powered 2-percentage-point non-delivery inference.
- No coverage of all initial SOC or PV-error levels.
- No full 54-cell `C_full` frontier.
- No causal claim that the disclosure change alone would produce the same
  savings in another market design.
- No wind, hydro, network, unit-commitment, GFM, or frequency-dynamic
  simulation.

Those are future server/laboratory extensions, not blockers for the structural
theory paper.

## 10. Reproducible artifacts

- Raw paired records:
  [`results/mfe_lean/held_out_records.csv`](../../results/mfe_lean/held_out_records.csv)
- Exact regime table:
  [`results/mfe_lean/regime_table.csv`](../../results/mfe_lean/regime_table.csv)
- Paired statistics:
  [`results/mfe_lean/paired_statistics.csv`](../../results/mfe_lean/paired_statistics.csv)
- Validation summary:
  [`results/mfe_lean/validation_summary.json`](../../results/mfe_lean/validation_summary.json)
- Main figure:
  [`results/mfe_lean/figures/lean_frontier.png`](../../results/mfe_lean/figures/lean_frontier.png)
- Analysis implementation:
  [`src/chameleon/mfe_lean_analysis.py`](../../src/chameleon/mfe_lean_analysis.py)

Final regression status: **77 tests passed**.

