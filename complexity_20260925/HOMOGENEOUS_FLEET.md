# From device count to device types: exact homogeneous-fleet results

Drafted 2026-10-07; revised after independent review on 2026-10-09, with October 10–12 updates. English publication edition, 2026-10-14.

**Status:** [independently reviewed](REVIEW_THEOREM_H_20261007_CODEX.md). Theorem H, Propositions 5/6 and Example C passed; no mathematical error was found. Twelve recommendations were addressed (§9). Numerical checks remain evidence; Example C has rational certificates. Theorem H's literature priority is unconfirmed.

## 0. Results

| Result | Regime | Conclusion |
|---|---|---|
| Proposition 5 | At most three proportional groups with equal energy fractions within each group | Exact after aggregation and Theorem 4; sufficient condition |
| Theorem H | m identical lossless devices, arbitrary energies | Exact 2m-bound recursion, O(mT) arithmetic; membership by sorting |
| Proposition 6 | One type; or allocation within a type | Balancing is a universal optimal policy; main result already known from Evans 2019 |
| Example C | Three types with unequal within-type states | Subset hull can falsely accept |
| Example D | Two types, N=4 or 5, T=3 | Five exact counterexamples, including positive-power versions |

Theorem H characterizes which initial states can deliver a bidirectional interval commitment, rather than claiming a new optimal balancing controller. Multi-type failures are general counterexamples, not a claim that every unequal-state instance fails.

## 1. Proposition 5: proportional groups with equal energy fractions

For a group G assume (E_i,C_i,D_i)=α_i(Ē,C̄,D̄), α_i>0, and e_i=α_i s̄. Replace it by a virtual device with parameters (Σα_iĒ,Σα_iC̄,Σα_iD̄) and energy Σe_i.

**Proposition 5.** For every commitment, the original fleet is causally feasible iff the fleet of virtual devices is causally feasible.

**Proof.** Lift virtual power q by p_i=α_iq/Σα. Every power and energy constraint scales accordingly, equal fractions persist, and the allocation is causal. Conversely sum any original causal policy's powers and energies within each group. The summed constraints give a causal virtual policy; it can simulate internal states from the known initial state and observed history. ∎

With at most three groups, apply Theorem 4. Aggregating parameters costs O(N); the backward core is O(T); allocating actions back to all devices costs O(N) each period.

Aggregation is a known modelling practice. Evans–Tindemans–Angeli 2110.08549v3 §V-B provides equal-time-to-go virtual-battery conditions in a discharge-then-recovery framework without cross-charging. It is background rather than a proof of this bidirectional statement. Equal fractions are sufficient for general exact aggregation, not necessary for every instance: two E=2,D=1 devices at (1,1) can discharge 2 in one period, whereas (0,2) can discharge only 1 despite the same total energy. Without the condition, summed parameters generally give an outer model.

## 2. Proposition 6: universal balancing policy

Assume m devices have identical parameters.

**Lemma 6a.** For a current state e and request y, suppose

    X={x:e−D≤x≤e+C, Σx=Σe−y}

is nonempty. Its water-filling point x*_i=clip(λ,e_i−D,e_i+C), with λ chosen for the correct sum, is majorized by every x∈X: x*≺x. λ may be nonunique on a saturated plateau, but x* is unique.

**Proof.** If x≠x*, select an excess coordinate i and deficit coordinate j. Because x*_i is not upper-clipped, x_i>x*_i≥λ; because x*_j is not lower-clipped, x_j<x*_j≤λ. Transfer δ=min(x_i−x*_i,x*_j−x_j) from i to j. Neither coordinate crosses its target or leaves its interval; at least one reaches its target and is no longer changed. At most m transfers reach x*. Each is a Robin Hood transfer and does not increase Σφ(x_i) for any convex φ. Equal sums and the Hardy–Littlewood–Pólya criterion give x*≺x. ∎

X need not include the physical box explicitly: if some x∈X∩K_{t+1} exists, the next lemma places x* in K_{t+1}, hence in the box. This is a known least-majorized-base phenomenon; relevant tools include Tamir (1995), Fujishige (1980) and Schoot Uiterkamp 2201.06596.

**Lemma 6b.** A convex permutation-invariant set S contains z whenever x∈S and z≺x. Indeed z=Px for a doubly stochastic P by Hardy–Littlewood–Pólya; Birkhoff's theorem expresses P as a convex combination of permutation matrices.

**Proposition 6.** Each K_t is convex and permutation-invariant. The policy moving to x* each period succeeds for every commitment whenever any causal policy succeeds.

**Proof.** Identical devices make the backward operator commute with permutations; convexity is preserved. At e∈K_t, the endpoint lemma ensures X∩K_{t+1} is nonempty for every observed y in the interval. Take feasible x there. Lemmas 6a/6b yield x*∈K_{t+1}; backward induction completes the argument. ∎

**Multi-type corollary.** Once total power for each type is fixed, balancing within that type loses nothing. Fix all other type coordinates: the slice of K_{t+1} is convex and invariant under within-type permutations, so the same two lemmas apply. The remaining decision is how to divide power among types. This complements S1's absence of a commitment-independent universal rule for general heterogeneous bidirectional fleets.

**Known result.** Evans' 2019 Imperial thesis, Chapter 8, already proves the main policy result for proportional fleets. Conditions (8.5) require η_i=1, r_i=αq_i and equal maximum time-to-go; with positive discharge powers these mean equal E_i/D_i and C_i/D_i. Theorem 8.3.4 gives universal optimality for signed requests with cross-charging; Lemma 8.3.10, equation (8.12), gives

    z_i=min(max(x_i−Δt,ẑ),x_i+αΔt),

and Corollary 8.3.13 gives discrete-time optimality. For identical devices x_i=e_i/D,α=C/D recovers water-filling. These ratios do not cover zero power directly; the proof above does. The majorization proof is an alternative proof, not a new controller result.

A universal policy also makes causal interval feasibility equivalent to feasibility of every fixed request sequence, because that same policy succeeds on every feasible sequence. However, expressing K_t as an intersection of fixed-sequence sets alone does not establish subset facet directions. Here that property follows from Theorem H, not from this observation.

## 3. Theorem H: exact recursion for arbitrary homogeneous fleet size

Let top_k(e) sum the k largest coordinates and bottom_k(e) the k smallest. For m≥1 identical lossless devices with finite nonnegative E,C,D and l_t≤u_t, every nonempty kernel has the exact form

    K_t={e:top_k(e)≤b_k, bottom_k(e)≥a_k, k=1,…,m},

where b is concave, a convex, and b_0=a_0=0. The recursion uses only +,−,min,max:

1. Terminal: b_k=Ek, a_k=0.
2. Empty successor, l<−Cm or u>Dm: return empty.
3. Single-request bounds:
   b̃_k=b_k+min(Dk,l+C(m−k));
   ã_k=a_k+max(−Ck,u−D(m−k)).
4. Physical box: b̂_k=min(Ek,b̃_k), â_k=max(0,ã_k).
5. Nonempty iff â_m≤b̂_m.
6. Tighten simultaneously:
   b_k=min(b̂_k,b̂_m−â_{m−k});
   a_k=max(â_k,â_m−b̂_{m−k}).

Both assignments in step 6 must read the old b̂,â arrays.

### 3.1 Lemma S: tight bounds of a symmetric description

Suppose b(S)=b_|S| is concave and a(S)=a_|S| convex, both normalized, and K={x:a(S)≤x(S)≤b(S) for every S}. Then K is nonempty iff a_m≤b_m, and its tight bounds are

    β_k=min(b_k,b_m−a_{m−k}),
    α_k=max(a_k,a_m−b_{m−k}).

β is concave and α convex.

**Proof.** Sort x decreasingly and set s_j=top_j(x). The adjacent differences are nonincreasing, so s is a concave sequence with s_0=0; conversely every such sequence gives a sorted vector by its differences. Upper constraints are s_j≤b_j. Lower constraints are s_m−s_{m−j}≥a_j, equivalently s_i≤s_m−a_{m−i}.

Fix total s_m=σ and define c_j(σ)=min(b_j,σ−a_{m−j}). Both sequences are concave. Their pointwise minimum is concave: at interior j choose a minimizing sequence f, then c_{j−1}+c_{j+1}≤f_{j−1}+f_{j+1}≤2f_j=2c_j. If a_m≤σ≤b_m, c_0=0,c_m=σ, so c itself is feasible and pointwise maximal among feasible partial-sum sequences.

This constructs a point for every total in [a_m,b_m] and proves nonemptiness. The maximum c_k occurs at σ=b_m, giving β_k. The minimum bottom_k=σ−c_{m−k}=max(a_k,σ−b_{m−k}) occurs at σ=a_m, giving α_k. Permutations attain these bounds for every specified subset. β is a minimum of two concave sequences; α a maximum of two convex sequences. The same local inequality proves both, with β_0=α_0=0. Also a_k≤(k/m)a_m≤(k/m)b_m≤b_k. ∎

The formulas resemble Frank–Tardos (1988), Proposition II.2.10, for intersecting a g-polymatroid with a total slab. Their result requires a crossing condition. Lemma S replaces that condition with symmetry and concavity/convexity.

### 3.2 Proposition H2: symmetric one-request closure

Suppose K is nonempty, exactly described by its tight subset bounds, with symmetric concave b and convex a (hence in H3″), and −mC≤y≤mD. Then K+P_y equals its subset hull, with tight bounds b+b_P,a+a_P, for every m.

A symmetric function φ(|S|) is submodular iff φ is concave: its marginal increments φ_{k+1}−φ_k are nonincreasing. The supermodular analogue is convexity.

**Proof.** Follow Theorem 2. Its only use of N≤3 was restricting M to ∅ or R₀ in mixed inequalities. Here b(A∪M)−a(B∪M)=b_{|A|+j}−a_{|B|+j} depends only on j=|M| and is concave. Its minimum on 0≤j≤|R₀| occurs at an endpoint. Thus intermediate-M constraints follow from the endpoint constraints already implied by the subset hull; both g endpoint estimates hold in every dimension and for every real s. One-sided cases still use F5, requiring tight bounds. Support additivity proves that the resulting bounds are truly tight. ∎

### 3.3 Proof of Theorem H

Backward induction starts at b_k=Ek,a_k=0. H2 gives exact single-request sums; b_P(k)=min(Dk,y+C(m−k)) is concave and nondecreasing in y, and a_P is convex and nondecreasing. Endpoint intersection therefore selects upper l and lower u, yielding concave b̃ and convex ã.

F3 merges the physical box:

    b̂_k=min_{j≤k}[b̃_j+E(k−j)]
        =Ek+min_{j≤k}[b̃_j−Ej]=min(Ek,b̃_k).

The bracketed function is concave with value zero at j=0, so its minimum is at 0 or k. The lower max convolution similarly becomes max(0,ã_k) because ã is convex and ã_0=0. b̂ remains concave and â convex. Lemma S tests emptiness and supplies tight concave/convex bounds, closing the induction. ∎

All degeneracies, fixed totals, l=u, E=0, C=0,D=0, m=1 and T=0 are covered; no interior assumption is used.

### 3.4 Complexity and implementation

Each period costs O(m) arithmetic operations, for O(mT). Sort the initial state once and use prefix sums to check all 2m inequalities in O(m log m). m is the explicit number of listed devices, not a binary-compressed count; this is not a polynomial in log m. Constants kE,kC,kD can be precomputed by O(m) additions. The no-division claim concerns bound recursion only; solving water-filling for λ may use division.

For rational inputs let L be their denominator lcm. Bounds stay in (1/L)ℤ and log L is bounded by total denominator encoding length. Nonempty tight bounds satisfy 0≤a_k≤b_k≤mE. Intermediate magnitudes are O(m(E+C+D)+max_t(|l_t|+|u_t|)); stop at emptiness. Numerators and each arithmetic operation have polynomial bit cost, so total bit complexity is polynomial in explicit input length.

`evidence/homogeneous_exact.py` uses the two-term box formulas directly; O(m²) convolution occurs only in optional CROSSCHECK diagnostics. Historical rational timings at T=20 for m=100,1,000,10,000,100,000 were about 0.02,0.18,1.9,19 seconds; membership at m=100,000 took about 0.37 seconds. Timings are hardware-dependent evidence.

## 4. Example C: three types can fail

    E=(4,4,1,1), C=(0,0,3,1/2), D=(1,1,2,0),
    intervals [1/5,3/5], [−1,8/5].

Devices 1 and 2 are identical, so there are three types. At the last period, −1 implies e₃+e₄≤1; 8/5 implies e₂+e₃≥3/5. Thus K₁ satisfies e₄−e₂≤2/5. Since first-period p₂≥0,p₄≤0, the difference cannot decrease, and K₀ satisfies the same bound. Its subset hull contains e*=(19/10,1/10,1/5,1), whose difference is 9/10.

Run `evidence/n4_real_certificate.py --three-types`. Thirty rational feasible tree policies certify hull membership. For ε=1/100 replacing zero powers, the valid root bound is 2/5+5ε=9/20; e*=(47/25,3/50,6/25,1) has difference 47/50. The independent H-review script certifies all true subset optima for both versions. These certificates do not assert facet dimension for Example C.

## 5. Numerical and independent evidence

| Check | Historical outcome |
|---|---|
| Random one-type fleets, m=4,5,6 | 1,384+997+207 feasible instances, no mixed gap |
| Early two-/three-type menus | One gap in AABBC; none in other tested type patterns |
| Four-type control | One gap in 1,474 feasible instances |
| Targeted Example-B modification | 274 gaps among 2,268 grid configurations; maximum 0.5, yielding Example C |
| Rational balancing simulation | 19,800 states, m=2–5,T≤3; no disagreement with floating-point tree LP |
| Symmetric nontight descriptions, m=4–7 | About 1,950 nonempty instances; tight bounds concave/convex, maximum float discrepancy 3.6e−15 |
| Homogeneous recursion, seeds 3,4,7 | 3,800 cases, 2,124 nonempty; 15,138 support checks; 16,229 feasible outer vertices at m=2–4; nine vertex checks skipped for unavailable interior, not certified low dimension; 16,992 point comparisons without disagreement |
| Independent rational attack | 144 cases,m=1–8,T=1–5; 681 exact vertex witnesses, 820 exact subset supports, 836 mixed-direction orbits covering 79,848 combinations, no gap; Lemma S verified on 96 descriptions; 576 policy roots, 32,489 rational transitions |

Search scripts not listed in the root verifier are outside this minimal release. Finite tests do not replace the general proof.

## 6. Literature position

Proportional aggregation, least-majorized bases and Evans' universal balancing policy are known tools. In the checked Evans thesis chapters, Chapter 8 gives the policy, while Theorem 4.2.8 concerns nonnegative-request E-p comparisons. The later DLR paper restricts operation to discharge followed by recovery without cross-charging. Neither checked passage contains Theorem H's arbitrary-sign interval-commitment backward recursion. No identical recursion was found in the checked sources; priority remains unconfirmed. See the [literature record](LITERATURE_CHECK_20260929.md) for unavailable books and reading depth.

## 7. Two types: historical screening and later refutation

On October 7, ordinary and zero-heavy random menus found no gap in about 22,560 feasible two-type instances. The four-type control rate was about 1/4,000. This supported only a tentative conjecture, not exactness. On October 10 targeted menus found five exact N=4/5,T=3 counterexamples, including all-positive perturbations: `evidence/two_types_certificate.py`. The shared set M occupies one type in the remaining devices, a corner not controlled by the empty/full choices. The comparable targeted rates were about 1/3,000 for two types and 1/700 for three types. Details are in [the method document](N3_METHOD_AND_N4_PLAN.md), §3.

## 8. Open issues at closure

Theorem H's priority is unconfirmed despite further source checks. Two-type exactness is refuted. The special m-identical-plus-one-different regime remains unresolved, as does balancing with losses. No further investigation is committed.

## 9. Resolution of the twelve review recommendations

| # | Recommendation | Resolution |
|---|---|---|
| 1 | Simultaneous tightening and proof of minimum-concavity | Explicit in §3 and Lemma S |
| 2 | H2's exact-description/nonempty assumptions | Explicit in §3.2 |
| 3 | O(m) production recurrence and prefix-sum membership | Implemented; full convolution optional |
| 4 | Rational bit bounds, explicit m, limited no-division claim | Explicit in §3.4 |
| 5 | Nonempty water-filling set and finite transfers; type slices | Explicit in §2 |
| 6 | Unsupported inference of subset facets | Made a consequence of Theorem H |
| 7 | Proportional condition sufficient; allocation costs | Explicit in §1 |
| 8 | Example-C output must not cite Example-B-only geometry | Correct mode-specific certificate reference |
| 9 | Retry presolve failures, classify skips, assert thresholds | Verification code revised; historical review retained |
| 10 | At most 25 samples, retained-instance denominator, save inputs | Sandwich report and rerun protocol revised |
| 11 | Restrict empirical exactness and one-step slack claims | Experiment report revised |
| 12 | Known policy and unconfirmed priority; source-depth limits | Explicit; later two-type refutation clearly dated |
