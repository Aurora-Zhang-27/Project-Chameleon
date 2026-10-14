# Single-state membership using history-dependent affine policies

Research dated 2026-10-11, with October 12 source checks and publication corrections. English edition, 2026-10-14. This tests one initial state without constructing all of K₀.

## 0. Conclusions and certification scope

Historical sandwich samples contain 211,063 states. The floating-point tree LP classified 211,060 as feasible; the lifted-affine test accepted all of them numerically. Of these, 210,959 passed rational policy certification and 101 were float_only. Three other states were rejected by the affine test and classified infeasible by the tree LP. Thus a **strict certified workflow leaves 104 states unresolved by the affine test**, about 0.049%, rather than zero fallback. No false acceptance was observed in the numerical comparison.

The class is **not exact in general**: a rational N=4,T=4 example is feasible but admits no such policy. In historical vertex screening of 788 numerically certified instances and 51,441 vertices, only one instance failed. These are distribution-dependent observations, not a polynomial-time exact algorithm or a general acceptance guarantee.

Affine adjustable robust counterparts and positive/negative lifted decision rules are known methods. Xie & Chen already observed affine/exact objective equality in six examples. No matching systematic heterogeneous membership test or the particular rational failure certificate was found in checked sources; priority is not claimed absolutely. Source depth is recorded in [the literature check](LITERATURE_CHECK_20260929.md), §§9–10.

## 1. Policy class and robust LP

Ordinary affine policies have

    p_{i,t}=a_{i,t}+Σ_{s≤t}G_{i,t,s}y_s.

The lifted class splits y_s into y_s⁺=max(y_s,0), y_s⁻=max(−y_s,0):

    p_{i,t}=a_{i,t}+Σ_{s≤t}(G⁺_{i,t,s}y_s⁺+G⁻_{i,t,s}y_s⁻).

It contains ordinary affine policies (G⁻=−G⁺) and current-request participation factors with separate charging/discharging weights. Ordinary affine policies and participation factors do not contain each other: the latter can kink at zero. All classes are causal because no future request appears.

Aggregate balance Σ_i p_{i,t}=y_t is imposed for every history by linear coefficient equalities on the relevant request domain. Power and prefix-energy constraints are linear functions of lifted requests. Each period's lifted domain is a line segment when the interval is one-sided, or the convex hull of (u_s,0),(0,0),(0,−l_s) when it crosses zero. A linear worst case is exact on those vertices. Periods are independent, so maximize separately and add; auxiliary variables represent each maximum. This produces an exact robust counterpart **for the restricted policy class**, with O(NT²) variables and O(NT³) nonzeros. No request tree is needed.

Acceptance supplies a feasible causal policy. Rejection only excludes this policy class, not the original viability problem.

### 1.1 Rational policy certification

`evidence/affine_decision.py` first searches with a 10⁻⁷ margin and HiGHS feasibility tolerance 10⁻⁹; inert devices have zero policies. Coefficients are reconstructed as fractions, and a device with a large power range absorbs rounding corrections to enforce exact balance. Every robust constraint is then checked with exact arithmetic, using the written decimal/rational input values. Only a fully checked policy is certified.

Forced equality can prevent a margin-based search from succeeding, historically producing float_only. Equality is not a theoretical obstacle to rational certification; this status means the implemented process has not certified the candidate. The publication returns the **repaired fractional coefficients actually verified**, checks the initial physical box and handles all-inert zero-request cases. Raw float solutions are not certified controllers.

## 2. Historical sandwich sample results

Retained reproduction scripts: `evidence/affine_sandwich.py` and `affine_summary.py`. Raw instance files are outside this minimal package; aggregate tables and source hashes are in `../results/`.

N=3–6,T=2–4, the same seeds, instances and initial states as the participation-factor experiment; its participation-factor counts matched exactly. Samples are drawn inside the subset outer approximation.

| Family | N | Samples | Tree-feasible, float | Participation acceptance | Lifted certified | Float-only | Affine rejected |
|---|---:|---:|---:|---:|---:|---:|---:|
| Zero powers allowed | 3 | 25,681 | 25,681 | 75.8% | 25,630 | 51 | 0 |
| Zero powers allowed | 4 | 25,719 | 25,719 | 69.5% | 25,719 | 0 | 0 |
| Zero powers allowed | 5 | 27,591 | 27,591 | 66.3% | 27,591 | 0 | 0 |
| Zero powers allowed | 6 | 26,540 | 26,537 | 63.4% | 26,537 | 0 | 3 |
| All powers positive | 3 | 27,513 | 27,513 | 71.0% | 27,463 | 50 | 0 |
| All powers positive | 4 | 25,743 | 25,743 | 65.0% | 25,743 | 0 | 0 |
| All powers positive | 5 | 26,058 | 26,058 | 64.0% | 26,058 | 0 | 0 |
| All powers positive | 6 | 26,218 | 26,218 | 60.8% | 26,218 | 0 | 0 |

Ordinary and lifted affine numerical acceptance agreed on all tree-feasible samples. All 101 float-only acceptances were in N=3 cases. The three outer false acceptances were affine-rejected. The average short-horizon tree solve took about 1.1 ms per state versus 3.7 ms for lifted-affine solving including rational checks. Short horizons can favour trees; longer horizons show the opposite.

## 3. Exact failure certificate

### 3.1 Vertex-screening design and results

The feasible initial-state set A of this policy class is convex and contained in K₀. Thus A=K₀ iff every K₀ vertex belongs to A. Historical screening enumerated vertices with a geometric termination check and tested them numerically; rejected vertices were moved 10⁻⁷ toward the centre to distinguish a slight geometric overshoot, then a bisection estimated the failure distance. This inward-jitter procedure is evidence rather than exact per-vertex equality certification.

| Family | Certified geometry instances | Vertices | Instances passing every tested vertex |
|---|---:|---:|---:|
| Random N=3–6,T=2–5, four seeds | 412 | 32,087 | 412 |
| Perturbations near Examples B/C, N=4–5,T=3–4 | 367 | 18,662 | 367 |
| Nine fixed counterexample instances | 9 | 692 | 8 |

The exception is coefficient-2 instance 1:

    E=(4,5,1,1), C=(0,0,3,1/2), D=(1,3/2,2,0),
    intervals [3/10,7/10], [−9/10,17/10], [4/5,9/10], [−4/5,11/5].

Six vertices failed; the centre-to-vertex lines reached about 97.4% before failure. Coefficient-2 instance 2 passed, so the facet coefficient alone does not explain failure. The large vertex-search script is not retained; its aggregate results are in `vertex_summary.json`.

### 3.2 Rational primal–dual proof

Run `evidence/affine_gap_certificate.py`:

    max_K₀(e₄−e₁)=9/20, attained at x*=(3/20,5,7/20,3/5),
    max_A(e₄−e₁)=2/5.

The script treats the initial state as a variable and certifies both optimal values with rational primal–dual checks. x* is viable but outside A, hence has neither a lifted-affine nor an ordinary affine policy. With all zero powers replaced by 1/100 the gap persists: 109/200 versus 1/2. These are exact counterexamples, unlike the frequency estimate above.

## 4. Horizon scaling

Historical medians depend on machine and solver versions; long-horizon samples are small. The complete 23-row table is retained in `../results/affine_scaling.csv`. Representative entries:

| N,T | Instances/states | Tree LP | Affine LP | Re-solving and rational checks |
|---|---|---:|---:|---:|
| 4,4 | 18/90 | 0.0014 s | 0.0020 s | 0.005 s |
| 4,8 | 11/48 | 0.061 s | 0.0081 s | 0.022 s |
| 4,12 | 2/10 | 19.9 s | 0.043 s | 0.079 s |
| 6,10 | 3/15 | 4.2 s | 0.045 s | 0.079 s |
| 8,8 | 6/30 | 0.22 s | 0.035 s | 0.062 s |
| 4,24, mild | 5/15 | Not run | 0.23 s | 0.46 s |
| 4,36, mild | 4/12 | Not run | 1.6 s | 2.2 s |
| 6,36, mild | 1/3 | Not run | 8.2 s | 10.4 s |
| 8,24, mild | 4/12 | Not run | 1.1 s | 1.5 s |

For N=4,T=12, LP solving alone was about 460 times faster. A depth-24 endpoint tree has over 30 million nodes. Longer-horizon mild samples had no tree comparison, but their certified policies prove their feasibility. One N=4,T=8 historical acceptance was float_only. Polynomial LP size is not a guarantee about every solver's measured runtime, nor exactness of membership.

## 5. Practical decision workflow and limits

Reject only by valid outer bounds or another justified necessary condition. Accept only after exact recursion or a certified policy. Treat float_only/rejected inner tests as unresolved and use other methods as needed. The exact affine counterexample really does require a richer policy or exact fallback.

Open questions include exactness conditions for this policy class, the failure mechanism, richer lifting breakpoints and limited-memory policies to reduce O(NT³) nonzeros. Partial shared-history request subtrees could safely reject on infeasibility, but are not implemented. A single worst request sequence cannot replace a causal test because different future branches can impose conflicting requirements on a shared earlier action.

Research is closed at this scope. Full historical samples were not rerun for the publication; runtime fixes and retained certificates are recorded in `../results/release_checks.json`.
