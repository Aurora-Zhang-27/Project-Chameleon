# Independent review of Theorem H and the October 7 results

**Overall verdict: Theorem H holds.** For identical lossless devices with finite nonnegative capacities/powers and independent interval requests each period, the exact 2m sorted partial-sum representation, tightening formulas and O(mT)-arithmetic algorithm are valid. Lemma S and Proposition H2 close the induction. No mathematical error overturning Theorem H was found; Propositions 5/6 and Example C also passed.

The audited implementation, however, used quadratic per-step convolution and quadratic membership summation; these were code-complexity errors, subsequently fixed. Some assumptions, sampling statements and broad claims also needed correction. Literature priority was not confirmed.

Review date 2026-10-09, retaining the requested 20261007 filename. Audited branch `codex/full-binary-lightweight-release-20260801`, commit `63837d124c50864b0778327d3e7e249e0159c52a`. CLAUDE.md and the original review request were read first. Existing files/frozen results were not modified during that audit. The independent script `evidence/review_codex_h_independent.py` uses only standard Python, NumPy and SciPy; it imports neither homogeneous_exact, oracle2, n3_exact nor another repository solver.

This English edition preserves historical findings. Old line numbers and references to unbundled searches concern the audited revision. Two-type exactness was open on the review date and later refuted on October 10; current implementation fixes are recorded in the homogeneous theorem document.

## 1. Categories and model

| Category | Finding | Effect |
|---|---|---|
| Mathematical error | None found in Theorem H, S, Propositions 5/6 or C | Keep the theorem |
| Code error/verification gap | Two quadratic implementations; incomplete float-failure handling; Example-C output citing B-only script | Repair implementation/evidence wording, not formulas |
| Overstatement/ambiguity | H2 prerequisites, finite-transfer proof, bit bounds, subset-facet inference, proportional-condition necessity, sample distribution | State conditions and narrow claims |
| Undetermined | Full priority; two-type case at the time | Preserve historical open status; mark later update separately |

Each period's duration is absorbed into parameters; p∈[−C,D],e⁺=e−p,terminal box only, cross-charging allowed. Policies may use known initial energies and observed history. Assume m≥1,l≤u. Experiments do not replace proofs.

## 2. Lemma S: all seven checkpoints pass

| Checkpoint | Reason |
|---|---|
| S1: subset constraints versus top/bottom sums | Largest/smallest k-subset sum is top_k/bottom_k |
| S2: concave partial sums versus sorted vectors | Nonincreasing differences reconstruct the sorted coordinates, including negative ones |
| S3: c(σ) concavity and endpoints | b_j and σ−a_{m−j} are concave; their minimum is concave; c_0=0,c_m=σ for a_m≤σ≤b_m |
| S4: feasibility and pointwise maximality | c satisfies both upper bounds and reconstructs a real feasible vector |
| S5: tight formulas | β_k attained at σ=b_m; α_k at σ=a_m; permutations handle every specified subset |
| S6: nonempty iff a_m≤b_m | Feasible construction for every σ in that interval, plus necessity |
| S7: tight-bound shape | Minimum of two concave sequences is concave; maximum of convex sequences is convex |

At interior j, choose a minimizing sequence f: c_{j−1}+c_{j+1}≤f_{j−1}+f_{j+1}≤2f_j=2c_j. Endpoints retain normalization without requiring a second difference. Also σ−c_{m−k}(σ)=max(a_k,σ−b_{m−k}), nondecreasing in σ, while c_k is nondecreasing. These prove attainment, not merely validity. The chord inequality a_k≤(k/m)a_m≤(k/m)b_m≤b_k is consistent with the constructive nonempty test. Fixed totals, m=1, negative bounds and nontight descriptions are covered.

Independent evidence: 96 rational descriptions, including fifteen nonempty nontight cases and forty-six nonempty cases containing negative entries; 428 exact primal–dual support certificates and 128 exact vertex extrema.

## 3. Proposition H2

All algebraic checkpoints pass; the original statement needed explicit prerequisites: nonempty K, an exact tight H3″ subset description, and nonempty P_y (−mC≤y≤mD). Permutation invariance and concave/convex support values alone are not a complete description assumption.

Symmetric submodularity is equivalent to nonincreasing cardinality increments. For disjoint A,B and R₀ their complement, f(j)=b_{|A|+j}−a_{|B|+j} is concave, so f(j)≥min(f(0),f(|R₀|)). Endpoint mixed constraints imply all intermediate choices of M. The two estimates

    g(∅)=min(0,s+C(R₀))+min(0,D(R₀)−s)≤0,
    g(R₀)=min(D(R₀),s)+min(C(R₀),−s)≤0

hold for every real s. One-sided cases correctly use F5 and true tight input bounds. Support additivity then proves tightness. Empty P_y has no finite usual tight bounds; the main algorithm already rejects it, so this wording gap did not invalidate Theorem H.

## 4. Theorem H, degeneracies and complexity

Single-request bounds have the required concavity/convexity and are nondecreasing in y. Thus upper l/lower u selection is correct. For box merging, g(j)=b̃_j−Ej is concave with g(0)=0, so min_{j≤k}g(j)=min(0,g(k)); the lower convex analogue gives max(0,ã_k). Nonempty power endpoints guarantee both zero normalizations. Lemma S tests nonemptiness and returns tight concave/convex arrays, closing the terminal-box induction.

Convex interpolation of endpoint actions uses the same current state and supports interior requests. Shared history, not independent leaf actions, enforces causality. E=0,C=0,D=0,C=D=0,l=u,m=1,T=0 and fixed-total lower-dimensional kernels are covered. Tightening must read both old arrays simultaneously.

**Audited code errors:** `homogeneous_exact.py:44–45` computed (m+1)(m+2)/2 convolution terms before checking the simplified formula, so even `python -O` did not remove Θ(m²T) cost. Its old `member()` resummed slices for each k, giving Θ(m²) after sorting. Direct two-term box formulas and one prefix-sum pass recover O(mT) and O(m log m) membership. These fixes were subsequently made in the published implementation; optional full-convolution diagnostics have separate cost.

For rational binary input let L be the denominator lcm. Recursion stays in (1/L)ℤ; kE,kC,kD can be precomputed by O(m) additions. Nonempty tight bounds lie in [0,mE], and intermediate magnitudes are O(m(E+C+D)+max_t(|l_t|+|u_t|)); stop on emptiness. log L and numerator lengths are polynomial in explicit input length. m denotes explicitly listed devices, not a compressed binary count. No-division concerns bound recursion, not λ in water-filling.

## 5. Proposition 6

The majorization direction and proof pass. If x_i>x*_i and x_j<x*_j, then x_i>x*_i≥λ≥x*_j>x_j. Choose δ=min(x_i−x*_i,x*_j−x_j); at least one coordinate reaches its target and is never changed again. At most m transfers terminate, without crossing targets or power intervals. Equal sums and convex-function decrease yield x*≺x. An arbitrary small transfer would not itself justify finite termination.

State X must be nonempty; λ can be nonunique but x* is unique. The omission of the physical box from X is harmless: from feasible x∈X∩K_{t+1}, permutation-invariant convex closure places x* in K_{t+1}. For multiple types, fix other coordinates and apply the same argument to the type slice.

The earlier statement that an intersection of fixed-path feasible sets “naturally has only subset facets” lacked a proof of those individual facet directions. Universal balancing establishes causal/pathwise equivalence, but not that structural inference. Make subset facets a consequence of Theorem H or supply a separate applicable pathwise theorem.

Independent rational water-filling sampled endpoints and two trisecting requests: 576 initial states,32,489 transitions, no disagreement with tree/recursion decisions. Finite grids remain evidence.

## 6. Proposition 5

Both aggregation directions pass. Virtual actions lift by α_i/Σα, preserving fractions; original actions sum causally, simulating known internal states if needed. Two E=2,D=1 devices at (1,1) versus (0,2) correctly disprove general aggregation by total energy alone. Equal within-group fractions are sufficient, not a necessary condition for every exact method or every instance. Add O(N) preprocessing and O(N) per-period lifting to the O(T) fixed-group recurrence.

## 7. Example C

Parameters E=(4,4,1,1),C=(0,0,3,1/2),D=(1,1,2,0), menus [1/5,3/5],[−1,8/5] truly have three types. Last request −1 gives e₃+e₄≤1; 8/5 gives e₂+e₃≥3/5; their difference is ≤2/5. First-period p₂−p₄≥0 propagates the same bound to K₀.

Exact independently certified hull points:

    ε=0: e*=(19/10,1/10,1/5,1), difference9/10>2/5;
    ε=1/100: e*=(47/25,3/50,6/25,1), difference47/50>9/20.

The ε derivation gives last-period bound2/5+3ε and first-period slack2ε. Devices 1/2 remain identical and every power becomes positive. Thirty feasible subset-policy witnesses in the original script already suffice; the independent script additionally certifies all true optimal supports. No Example-C facet dimension is asserted.

The old script's mode-independent output cited `review_codex_n4_geometry.py`, which only covers Example B. It needed a mode-specific reference to the independent H-review script. This was subsequently corrected.

## 8. Historical requested reruns

All seven commands exited successfully in `complexity_20260925/evidence`. Search/probe scripts not retained here are historical references.

| Command | Audited output |
|---|---|
| `python3 homogeneous_exact.py 3 1500` | nonempty854,empty646,supports6178,deviation0;points6832,dis0;vertices6952,skips7 |
| `python3 homogeneous_exact.py 4 1500` | nonempty819,empty681,supports5730,deviation0;points6552,dis0;vertices5877,skips2 |
| `python3 balance_policy_check.py 2 3000` | points18000,LP-feasible4378,infeasible13622,agree18000,disagree0 |
| `python3 symmetric_tight_probe.py 5` | m=4,5,6,7 nonempty285,293,293,98;violations0;maximum discrepancy3.552713678800501e−15 |
| `python3 n4_real_certificate.py --three-types` | e*=(19/10,1/10,1/5,1),gap9/10 versus2/5,True |
| `python3 n4_real_certificate.py 1/100 --three-types` | e*=(47/25,3/50,6/25,1),gap47/50 versus9/20,True |
| `python3 n4_real_certificate.py` | Example B root(4,0,1/5,1),True |

Historical verification gaps: support deviation and disagreement counts lacked explicit thresholds; failed interior LPs/small radii/Qhull failures were all called lowdim skips without dimension certification; some support infeasibility calls lacked presolve-off retries; nonzero solver status could be conflated with infeasibility; the probe's promised nonsymmetric control was not implemented. Rational recursion and sampled policy transitions were exact, but tree comparisons and numerical geometry were not. This rerun did not reproduce every historical seed or every two-type screen. Later revisions fixed the relevant validation paths.

## 9. Independent attacks A–D

Run `python3 -u review_codex_h_independent.py` from `evidence/`. The independently modelled state tree gives a single energy variable per history; parent/child differences impose power and request constraints. SciPy locates candidates; Fraction checks all successful primal/dual solutions, signs, stationarity and objective equality. Certificate failure raises an error. Infeasibility is retried without presolve, but no rational Farkas infeasibility certificates are produced: empty/rejected classifications remain float evidence.

| Attack | Coverage and result |
|---|---|
| A: extreme fleets and all vertices | 144 cases,m=1–8,T=1–5;108 nonempty,36 empty;100:1/1:100 ratios,one-way/inert devices,tiny capacities,crossing-zero/singleton menus;234 vertex orbits,681 distinct vertices with exact policies,including eight lower-dimensional cases |
| B: mixed directions | 836 sign-count orbits covering79,848 direction/instance combinations;both true/outer supports exactly certified,no gap;820 exact subset supports |
| C: Lemma S | 96 descriptions,50 nonempty,46 empty;15 nontight and46 negative-entry nonempty cases;428 exact supports and128 exact vertex comparisons |
| D: water-filling | 576 roots,32,489 exact transitions at endpoints/trisecting values;no disagreement |
| Additional Example C | Thirty exact subset optima per ε;counterexample membership exact,values9/10>2/5 and47/50>9/20 |

For m≤4, rational activity-basis enumeration in the sorted chamber is filtered by rank of the original subset normals to avoid counting sorting-boundary artifacts as true vertices. Policy permutations certify every vertex orbit member. Convexity plus all-vertex feasibility establishes equality for these tested nonempty instances. Sign-count symmetry pairs +1 with largest and −1 with smallest coordinates, giving actual outer support rather than an arbitrary chamber subset.

The reported `fallbacks=0` counted only A's subset-support retries, not every LP. Optional two-type attack E was not run; no two-type conclusion follows from homogeneous certification.

## 10. Sandwich experiment audit

This section audited design/code/aggregates and reran summary scripts, not the full hundred-thousand-point experiment. Participation factors form a valid causal inner class because nonnegative weights make powers monotone and prefix extrema occur at interval endpoints. Float status0 and the numerical implication assertion are not exact policy certificates.

The old “25 uniform points per instance” wording was wrong: at most4,000 draws and at most25 retained;206 zero-allowed and242 positive instances retained fewer, and zero-sample instances were discarded. Pooled draws are weighted by retained sample count, underrepresenting thin/low-dimensional hulls. Counts were correct, but N≥4 discussion should use3/79,850 and0/78,019, rather than denominators105,531/105,532 that include proved-exact N=3. Shared parameters prevent treating all points as independent Bernoulli trials.

The participation inner test left about24–39% unresolved, not a few rare cases. “Almost exact under normal parameters” or “the outer bound is not the bottleneck” must be restricted to the retained empirical distribution; positive-power exact counterexamples already prevent a general claim. The g(M) estimate bounds one-step inequality slack, not a multi-step set distance. Old JSON lacked full inputs/false-acceptance states; later reruns began saving them. Exact certificates for those three historical false classifications are still not supplied here.

## 11. Literature scope

[Evans' Imperial thesis](https://spiral.imperial.ac.uk/entities/publication/e3a49a0c-a991-470f-a866-a5ae052ab7a5) was read at theorem/formula level in Chapters4/8. Conditions(8.5),Theorem 8.3.4,Lemma 8.3.10 equation(8.12),Corollary 8.3.13 support proportional lossless universal balancing. For positive discharge powers, E_i/D_i and C_i/D_i are equal; z_i=min(max(x_i−Δt,ẑ),x_i+αΔt) converts to water-filling. Zero powers need the separate direct proof. Theorem 4.2.8 concerns nonnegative-request E-p transforms, not the arbitrary-sign backward interval recursion.

[DLR 2110.08549v3](https://arxiv.org/html/2110.08549v3) limits the framework to discharge then recovery and no cross-charging; its virtual-battery result is background, not a direct proof of bidirectional Proposition 5. [Schoot Uiterkamp2201.06596](https://arxiv.org/abs/2201.06596) supports the known majorization tool. [2203.08659](https://arxiv.org/abs/2203.08659) is by Angeli,Dong,Strbac, not Evans; its formula-level audit was not repeated in this review.

No identical Theorem-H recursion was found in the checked chapters, but all citation chains and unavailable books were not exhausted. Program-analysis/control checks were at abstract/tutorial level, so “no applicable result seen” is justified; exclusion of the entire template-exactness literature is not.

## 12. Suggested changes

Keep the theorem and formulas. Make tightening simultaneous; spell out minimum-concavity and H2 prerequisites; implement direct O(m) box formulas and prefix sums; state rational bit bounds/explicit m/no-division scope; complete finite water-filling transfers and type slices; make subset facets a theorem consequence; describe proportional grouping as sufficient and include allocation costs; fix Example-C certificate references; add presolve retries, status/skip classifications and explicit thresholds; state at-most25 sampling and N≥4 denominators, save error inputs; narrow empirical/slack claims; retain the known policy and unconfirmed priority. The theorem document records all twelve resolutions and dates the later two-type refutation separately.
