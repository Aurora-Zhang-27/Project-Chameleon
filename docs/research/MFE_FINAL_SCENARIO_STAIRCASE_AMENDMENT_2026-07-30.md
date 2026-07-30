# MFE final scenario-staircase amendment

Date: 2026-07-30

Status: frozen before any staircase or held-out comparison. This is the final
numerical amendment. After the execution and reporting defined here, the MFE
code and thresholds are permanently closed.

## 1. Motivation and permitted change

The v3 384-scenario pilot established that the computational wall is the
nonanticipative stage-1 extensive form, not one-path physical recourse or
independent replay. The v4 relaxation gate then established:

- deleting all battery mode binaries is not contract-exact;
- adaptive partial integrality produces an exact sandwich certificate when it
  terminates with complementary actions;
- a 64-scenario stress diagnostic remained computationally risky.

This amendment changes only the in-sample scenario count used to construct
`C_full` and fit `C0`. It does not change the truth model, penalties,
54-cell grid, held-out count, seeds, replay, practical thresholds, or paired
statistics.

## 2. Scenario staircase

Candidate in-sample sizes are tested in descending order:

\[
N\in\{32,16\}.
\]

Construction paths use latent seed `2026080101`. For a cell with error level
`\sigma`, the first `N` ordered latent records are transformed using the
already registered AR(1) rule. Held-out seed `2026080104` remains disjoint.

The maximum `N` passing every gate below is frozen. No intermediate value,
alternative seed, or cell-specific `N` is allowed.

## 3. Sentinel cells

The three sentinels are frozen to cover the previously observed relaxation
stress, the original central runtime cell, and an energy-rich/low-error case:

| Sentinel | Duration | Initial SOC | PV error | Reserve tier |
|---|---:|---:|---:|---:|
| S1 | 1 h | 75% | 0.15 | 20% |
| S2 | 2 h | 50% | 0.08 | 20% |
| S3 | 4 h | 25% | 0.03 | 5% |

No sentinel may be replaced after observing runtime, objective, delivery, or
mode-conflict results.

## 4. `C_full-N` gate

For each sentinel and candidate `N`, solve the `C_full` nonanticipative
stage-1 problem with adaptive partial integrality.

A sentinel passes only if the complete adaptive solve, including every
partial-integrality iteration, finishes within 900 seconds:

1. solver relative gap is at most `0.001` (0.1%);
2. the adaptive solver returns its sandwich certificate;
3. every in-sample scenario independently replays with zero physical
   violation above `1e-6`;
4. replayed and serialized costs reconcile under the existing tolerance.

If all three sentinels pass, the line is named `C_full-N`. It is not called
the 384-scenario full-information optimum.

Reducing in-sample scenarios weakens estimation of the stochastic stage-1
optimum. Its held-out bias is expected to make `C_full-N` worse or more
variable than a well-solved larger-sample `C_full`; this can make contract
lines look relatively better. This direction is disclosed in every figure
and table.

## 5. `C0` fitting gate

`C0` retains the registered coarse-to-fine candidate list, 1% in-sample
non-delivery screen, mean-cost selection rule, and tie-breaks. Candidate
evaluation uses the same `N`, adaptive certificate, solver gap, 900-second
total limit per candidate,
replay tolerance, and construction seed as `C_full-N`.

For the sentinel gate, candidates are fitted separately on each sentinel
using its `N` paths. The gate passes only if every finalist needed to apply
the registered selection rule either:

- returns a sandwich-certified solution within 0.1% and 900 seconds; or
- is solver-unresolved and is retained as unresolved rather than silently
  discarded.

At least one certified candidate satisfying the 1% in-sample non-delivery
screen must exist in each sentinel. If a lower-cost candidate is unresolved,
the fit is unresolved and the sentinel fails.

After `N` is frozen, the same deterministic fitting rule is applied to all
54 cells. Cell-specific fits are permitted because each cell is reported
separately; the same candidate list and selection algorithm are used in every
cell.

## 6. Cheap stage-1 lines

`C1` and `C_ASSOC` do not use an `N`-scenario extensive form.

- `C1` is the already registered recourse-aware `C1-v3` 1/99 envelope. Its
  stage-1 schedule is optimized once against the deterministic day-ahead PV
  forecast, then frozen for all held-out paths.
- `C_ASSOC` is the market proxy in
  `C_ASSOC_MARKET_PROXY_SPECIFICATION.md`. Its declared SOC path and
  30-minute reserve sufficiency are optimized once against the deterministic
  day-ahead PV forecast, then frozen.

This is an information policy, not perfect foresight: neither line sees
held-out PV before stage 1. The difference from `C_full-N` is identified
explicitly in the paper.

## 7. Permanent fallback

- Try `N=32`.
- If either `C_full` or `C0` gate fails, try `N=16`.
- If both pass at 16, freeze `N=16`.
- If `C_full` fails at 16, delete the `C_full` line.
- If `C0` fitting fails at 16, use the registered deterministic `C0_fixture`
  parameters `(15,35,35,50)` and label the line `C0-fixture`, not fitted
  `C0`.

When `C_full` is deleted, the frontier contains
`C0`, `C1`, and `C_ASSOC`; `C_WS` is shown separately as a pathwise
wait-and-see lower-cost boundary. Because `C_WS` has more information than
any nonanticipative implementable policy, each line's gap to `C_WS` is an
upper bound on that line's possible cost improvement, not an estimate of its
gap to the unavailable stochastic optimum.

There is no additional solver amendment, scenario reduction, gap relaxation,
threshold change, or v5 after this fallback.

## 8. Confirmatory execution

Held-out evaluation remains:

- 218 common-random-number paths per cell;
- seed `2026080104`;
- all 54 cells;
- identical one-path physical stage-2 optimizer and independent replay;
- isolated up/down primary delivery;
- fixed hours 18/19 sequential upward stress;
- frozen 1% cost, 2 percentage-point delivery, and 80% value-recovery
  interpretation thresholds.

Outputs are:

1. frontier figure;
2. 54-row regime table;
3. six-stratum paired statistics;
4. branch decision;
5. solver-unresolved register;
6. completed disclosure-specification table with measured values;
7. a permanent numerical-closure record.
