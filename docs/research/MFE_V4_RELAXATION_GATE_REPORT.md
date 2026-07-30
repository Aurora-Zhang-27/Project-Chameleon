# MFE v4 relaxation gate report

Date: 2026-07-30

Decision: **full continuous relaxation rejected; 384-scenario execution not
opened.** A sparse adaptive-integrality formulation is mathematically
certifiable on completion, but its first 64-scenario pressure pilot did not
finish quickly enough to justify scaling.

## 1. Question tested

The v3 truth model has three charge/discharge mode binaries per scenario-hour:
one for the base trajectory and one for each isolated up/down activation
branch. The proposed computational shortcut was to relax those binaries to
continuous variables in `[0,1]`.

The required standard was contract exactness, not merely a similar objective:
the relaxed solve had to preserve the stage-1 hybrid schedule, reserve awards,
scenario delivery, cost, and independent physical replay.

## 2. Smallest benchmark counterexample

The pinned RTS-GMLC four-unit 24-hour case with:

- one-hour battery;
- initial SOC 75%;
- reserve tier 20%;
- deterministic forecast PV path;
- `C_full`;
- registered lossy battery, curtailment, slack prices, and terminal SOC;

rejects the full LP relaxation.

| Quantity | Full MILP | All modes relaxed |
|---|---:|---:|
| objective (USD) | 201,327.897881 | 201,322.091094 |
| mode binaries | 72 | 0 |
| maximum simultaneous power | 0 MW | 10.625 MW |

The relaxed down-activation branch simultaneously charges and discharges
10.625 MW in hour 1 and 0.125 MW in hour 18. Mode-only recovery is impossible.
Fixing the relaxed stage-1 contract and resolving physical recourse gives
USD 204,203.165340, so the issue is not just an arbitrary fractional mode
label: the relaxed stage-1 tuple exploits cheaper nonphysical continuation.

Therefore the registered positive losses and throughput cost do **not** make
the complete base-plus-reserve relaxation contract-exact.

## 3. Broader lightweight checks

Across 18 deterministic `C_full` cells (three durations, three initial SOC
levels, and two reserve tiers), all-mode relaxation produced nonrecoverable
simultaneous operation in the three one-hour/20% reserve cells.

Relaxing only the base-trajectory mode was more promising:

- 18 deterministic `C_full` cells passed;
- 36 deterministic `C0`/`C1-v3` line-cells passed;
- nine `C_full` cells with eight PV scenarios each passed;
- every accepted relaxed trajectory admitted mode-only recovery and
  independent replay;
- median deterministic speedup was about 1.85x;
- the binary count fell by one third, not to zero.

These are regression results, not a general exactness proof. In particular,
the result must not be stated as “the continuous relaxation is exact.”

## 4. A posteriori exactness certificate

**Proposition (partial-relaxation sandwich certificate).** Consider any subset
of the mode variables retained as binary and relax all remaining modes to
`[0,1]`. Suppose the partial problem is solved to the registered optimality
tolerance and its optimal power actions satisfy charge/discharge
complementarity at every relaxed base and activation position. Then binary
modes can be assigned without changing any power, SOC, stage-1, reserve,
delivery, or cost variable. The recovered point is feasible for the full MILP
at the partial-relaxation objective. Since the partial feasible set contains
the full MILP feasible set, the two optimal values coincide within solver
tolerance. Thus the recovered solution is contract-exact within that
tolerance.

The implementation starts with the LP, adds integrality at every
branch-hour exhibiting simultaneous operation, and repeats. It must terminate
in at most 72 global branch-hour additions for the 24-hour model, with the full
MILP as the worst case. This is a certificate-generating algorithm, not an
assumption of exactness.

On an eight-scenario high-stress cell, the algorithm certified the full-MILP
objective using 168 binaries instead of 576 after five solves. Independent
replay passed for every scenario.

## 5. Runtime stop

The corresponding 64-scenario stress cell behaved as follows:

- initial all-continuous LP: 1.87 seconds;
- detected conflicting hours: up `{11,15,16}` and down `{1,17,18,24}`
  in one-based notation;
- first partial problem: 448 binaries;
- with a 20-second per-solve cap, the first partial solve terminated
  unresolved at the cap;
- an earlier uncapped attempt was manually stopped after roughly 130 seconds
  without producing the final certificate.

This does not prove that the adaptive formulation can never finish. It does
show that sparsity alone has not removed the practical scaling risk. Under the
predeclared stop rule, no 384-scenario or 54-cell comparison is launched.

## 6. What remains usable

- The full-LP counterexample is a valid mirror to the existing nonconvexity
  result: favorable prices are not by themselves enough once reserve branches
  and hidden recourse channels are present.
- The sandwich certificate is exact whenever it terminates with complementary
  actions.
- Base-mode-only relaxation is a tested engineering option for future solver
  work, but presently removes only one third of the binaries.
- `C_ASSOC` can still be specified and tested on deterministic/small-scenario
  cases. It must not be attached to an uncompleted confirmatory frontier.

