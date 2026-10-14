# Exact N≤3 method and the N≥4 research plan at closure

Research updates through 2026-10-12; English publication edition, 2026-10-14. Plans below record possible next steps, not ongoing research commitments. Research stopped at the stated scope.

## 0. Status

N≤3 has a proved exact O(T)-arithmetic algorithm, not brute-force request enumeration. General heterogeneous N≥4 subset bounds fail, including two-type fleets. Enlarging directions to {0,±1} is often a much better outer approximation, but coefficient-2 facets refute its general exactness. Known exact methods include request trees and successive polyhedral projection; neither has a polynomial guarantee here. The next practical step, single-state affine membership, was completed and is documented separately.

## 1. The N≤3 method

Assumptions: at most three fully available devices; arbitrary finite nonnegative capacities and asymmetric powers (one-way devices allowed); lossless dynamics e⁺=e−p; aggregate request y_t∈[l_t,u_t] must be matched exactly; actions observe current and past requests only. Period length is absorbed into the limits; losses and mode exclusivity are excluded.

Maintain tight upper/lower energy sums for all seven nonempty subsets: at most fourteen numbers. Backward from the terminal box, each period:

1. Add the request contribution: upper bounds use l, lower bounds u.
2. Merge the physical energy box by min/max convolution.
3. Use the sandwich theorem to test nonemptiness.
4. Tighten by closed-form singleton, pair and full-set formulas.

Theorem 2 establishes exact single-request subset closure from tight sub/supermodular bounds; Lemma 3 establishes exact tightening and preserves those properties in dimension three. Endpoint interpolation connects these steps into Theorem 4. Every period uses +,−,min,max; the implementation's diagnostic vertex enumeration is not part of the production recurrence. The validation tree, by contrast, has 2^T leaves.

Offline store the stage bounds. Online choose x∈K_{t+1}∩[e−D,e+C] with x(V)=e(V)−y, then p=e−x. The theorem document gives a merged-bound selector and a rational vertex alternative. Membership checks the seven subset sums. Homogeneous m-device fleets use Theorem H's 2m sorted partial-sum bounds instead; at most three proportional equal-fraction groups can be aggregated first.

## 2. Why four devices fail

In Example B, the last-period charging endpoint implies e₃+e₄≤1, and the discharging endpoint implies e₂+e₃≥1/5. Cancelling device 3 yields e₄−e₂≤4/5, propagated backward by nearly one-way devices. A subset hull cannot express this coupling.

Generally mixed constraints use disjoint A,B,M, with R₀=V∖(A∪B). M=∅ and M=R₀ are redundant. With A,B nonempty, N≤3 leaves |R₀|≤1 and no intermediate M. N=4 allows one. Separately, tightening arbitrary sub/supermodular descriptions need not preserve tight-bound modularity in dimension four: 79/255 historical synthetic float probes violated it, versus none in the tested N=3 cases. The real Example B is a third-layer counterexample, not merely a failed proof route.

## 3. Two types also fail: Example D

Targeted menus adapt Examples B/C: type X has nearly no charging (C from 0,0,0.1,0.5), type Y weak discharge (D from 0,0,0.1,0.5,1,2). Patterns XXYY,XXXYY,XXYYY use N=4/5,T=2–3. Three-/four-type patterns are controls. Floating screening used tolerance 1e−6 before rational confirmation.

| Pattern | Feasible instances | Mixed gaps flagged | Exact confirmations |
|---|---:|---:|---:|
| XXYY, three seeds | 11,700 | 3 | 3 |
| XXXYY | 1,965 | 1 | 1 |
| XXYYY | 1,858 | 1 | 1 |
| Three-type XXYZ control | 7,855 | 11 | Not individually confirmed here |
| Four-type XYZW control | 4,004 | 9 | Not individually confirmed here |

`evidence/two_types_certificate.py` certifies every true subset support and the mixed-direction optimum of both the true kernel and its subset hull, using rational primal–dual witnesses. All five have a strict gap. Representative cases:

| Case | Parameters and intervals | Direction | Subset hull | True K₀ |
|---|---|---|---:|---:|
| XXYY-b | E=(4,4,3,3), C=(0,0,2,2), D=(1/2,1/2,1/2,1/2); [3/5,9/10], [−2/5,9/5], [−27/10,−1/10] | e₄−e₂ | 27/10 | 13/5 |
| XXYY-c | E=(2,2,4,4), C=(1/2,1/2,1/2,1/2), D=(1,1,0,0); [−13/10,−1], [−6/5,1/2], [2/5,19/10] | e₄−e₂ | 4 | 39/10 |
| XXXYY | E=(5,5,5,4,4), C=(0,0,0,3,3), D=(1/2,1/2,1/2,1,1); [11/10,13/10], [−1/2,31/10], [−47/10,−9/5] | e₂−e₃+e₅ | 81/10 | 77/10 |

Replacing every zero power by 1/100 preserves all five gaps, also exactly certified. Targeted rates are about 1/3,000 for two types, 1/700 for three, 1/450 for four. The earlier 0/22,560 two-type random screen reflected rarity, not a theorem. General fleets with at least two types and at least four devices can therefore fail; individual instances may still be exact.

The m-identical-plus-one-different subcase remains unresolved. Its old 0/9,345 screen is not conclusive.

## 4. Larger templates and single-state decisions

### 4.1 All {0,±1} directions

Subset bounds retain 2(2^N−1) same-sign directions. A unit-coefficient template retains all 3^N−1 directions, solving one small LP (3N variables) per direction per period. It is a template-polyhedron construction, specifically related to the octahedron abstract domain. It always contains the true kernel. It is exact if every stage's facets are represented in the template. For fixed N the number of LP calls is linear in T; this alone is not a bit-complexity bound.

Historical floating-point, vertex-tested pilot:

| Source | Subset exact | Subset inexact, template exact | Template inexact | Low-dimensional skips |
|---|---:|---:|---:|---:|
| Near B/C,N=4,T=3–4,two seeds | 858 | 837 | 2 | 91 |
| Near B/C,N=5,T=3–4 | 266 | 129 | 0 | 17 |
| Random N=4,T=3–4 | 665 | 2 | 0 | 17 |
| Two N=6 sandwich-error instances | 0 | 2 | 0 | 0 |

Among 972 subset-inexact instances, 970 became template-exact. Two N=4,T=4 instances did not, even when all eighty unit-template supports were exact. `evidence/n4_normal_certificate.py` proves rational gaps in n=(−1,0,0,2):

    Instance 1: template 29/20, true 7/5;
    Instance 2: template 8/5, true 13/10.

Both persist with all zero powers replaced by 1/100. The published certificate also checks dimension four of K₀ and dimension three of this support face for both instances and perturbations: these are facets, not merely arbitrary separating directions. The former unit-normal conjecture is refuted.

Possible mechanism, **not proved**: Proposition 1 assumes a sub/supermodular subset input. Once a real intermediate kernel has mixed facets, that assumption fails; further Minkowski sums may introduce coefficient 2. This resembles the earlier synthetic (2,1,1) example from an input outside H3″.

Historical facet probes near B/C:

| T | Certified instances | Maximum primitive coefficient 1 | Coefficient 2 | ≥3 or noninteger normalization |
|---|---:|---:|---:|---:|
| 4 | 1,027 | 1,025 | 2 | 0 |
| 5 | 418 | 414 | 4 | 0 |
| 6 | 109 | 109 | 0 | 0 |

Normalizing the smallest nonzero component to one happened to yield integers in these probes, equivalent here to primitive-integer normalization. A ±2 template (544 primitive directions for N=4) was numerically exact on four tested coefficient-2 instances. The T=6 sample is weak; no targeted coefficient-3 construction was completed. These search scripts and raw traces are outside the minimal release.

### 4.2 Practical single-state workflow

The history-dependent lifted-affine LP was completed on October 11; [AFFINE_DECISION.md](AFFINE_DECISION.md) records its strong empirical results and exact counterexample. Certified outer exclusion means infeasible, certified inner acceptance means feasible with a policy, and all remaining cases are unknown until another method decides them. Float-only acceptance is not a certified inner bound.

Ordinary affine policies have p_{i,t}=c_{i,t}+Σ_{s≤t}L_{i,t,s}y_s, including the current request. Universal balance becomes coefficient equalities, while interval worst cases linearize exactly into an LP with O(NT²) variables. Positive/negative lifting expands the class. Affine rejection never proves original infeasibility. A partial request subtree can safely reject if infeasible, provided common histories remain shared; feasibility of the subtree cannot justify acceptance. One worst sequence cannot capture conflicting future demands on a common action.

### 4.3 Safe fixed-weight grouping

For any group and arbitrary initial energies, fix β_i>0,Σβ_i=1 and constrain p_i=β_i q. Define

    r=min_i e_i/β_i, h=min_i(E_i−e_i)/β_i,
    E_G=r+h, e_G=r,
    C_G=min_i C_i/β_i, D_G=min_i D_i/β_i.

This restricted policy is exactly a virtual device: actual energy is e_i+β_i(z−r), so 0≤z≤r+h enforces every physical bound. It is valid for arbitrary heterogeneity and energies but conservative. Simply summing E,C,D is unsafe without Proposition 5's conditions. At small scale enumerate groupings and a few weights, judging them by acceptance of the resulting at-most-three-device exact test. Power/capacity ratios and current fractions are possible heuristics, not proved optimal grouping criteria.

### 4.4 Direction growth remains open

Measure coefficients by primitive integer vectors. Chaining Example B to obtain coefficient 3 would only refute a coefficient-2 bound; unboundedness requires an indefinitely repeatable construction. Even unbounded direction growth only rules out one fixed finite template, not a polynomial algorithm for single-state membership. A bounded finite direction family for fixed N would permit horizon-linear LP-call recursion, subject to encoding and separation costs. Research stopped before resolving either possibility.

## 5. Related methods from other fields

The following connections were checked only at bibliography/abstract/tutorial level unless the literature record states otherwise; read original theorems before applying them.

| Field and source | Connection or possible use |
|---|---|
| Template polyhedra, Sankaranarayanan–Sipma–Manna, VMCAI 2005 | Fixed-direction LP bounds; exactness conditions and template choice |
| Octahedron domain, Clarisó–Cortadella, SAS 2004/SCP 2007 | Arbitrary 0/±1 sums; OhDD decision diagrams compress representations, but worst-case cost is still exponential |
| AARC, Ben-Tal et al., Mathematical Programming 2004 | Standard affine inner policy |
| Primal/dual decision rules, Kuhn–Wiesemann–Georghiou 2011 | Inner/outer sandwich and gap estimates |
| Lifted rules, Georghiou–Wiesemann–Kuhn 2015 | Richer piecewise policies |
| Finite adaptability, Bertsimas–Caramanis 2010 | Intermediate policy class between simple factors and trees |
| Supermodular affine optimality, Iancu–Sharma–Sviridenko 2013 | Possible exactness proof tool; not applied here |
| Two-commodity flow, Hu 1963 | Cut sufficiency analogy; not a proof of the storage dimension boundary |
| Discrete convex analysis, Chen–Li 2021 | Dynamic-programming structure preservation |
| Support-function reachability, Le Guernic–Girard 2010 | Fixed-direction computational techniques, largely open-loop context |

Octahedra should not be confused with octagons, whose constraints involve only two variables.

## 6. Proven full-power regime and exploratory ratios

If C_i≥E_i and D_i≥E_i for every device, arbitrary fleets admit an exact total-energy recursion:

    A_T=0, B_T=ΣE_i,
    A_t=max(0,A_{t+1}+u_t),
    B_t=min(ΣE_i,B_{t+1}+l_t).

Empty successor or A_t>B_t means empty. Otherwise membership is physical-box membership plus Σe∈[A_t,B_t].

**Proof.** Assume K_{t+1}=[0,E]∩{A≤Σx≤B}. From any e in the box, every x in the box is reachable by p=e−x because −E_i≤p_i≤E_i lies inside [−C_i,D_i]. A total request y is feasible iff Σe−y∈[A,B]; every intermediate total can be allocated within the box. Intersect these conditions over y∈[l,u], then with the physical box, to obtain the formulas. Backward induction proves the result for any N, with O(T) arithmetic after summing capacity. ∎

Historical float checks used 400 instances and 1,800 points, with no disagreement and total-support deviations below 2e−15. The small proof, not that search, supports the regime. It is implemented in the publication runtime.

Positive-power Examples B/C/D rule out the conjecture that any ρ>0 guarantees exactness. A higher threshold is not settled, but ρ alone omits capacities and duration; no further proof search is committed.

## 7. Source references and review resolution

Books sought: Frank, *Connections in Combinatorial Optimization* (OUP 2011, ISBN 978-0-19-920527-1); Fujishige, *Submodular Functions and Optimization*, second edition (Elsevier 2005, ISBN 978-0-444-52086-9); Murota, *Discrete Convex Analysis* (SIAM 2003, DOI 10.1137/1.9780898718508). Full access was unavailable in the recorded checks. Frank–Tardos (1988) and Murota (1998) supplied formal sources for the main tools instead.

The October 11 review confirmed both negative results, added facet dimensions, prioritized single-state membership, corrected arbitrary-state grouping, narrowed ratio claims, supplied the full-power regime, and distinguished coefficient growth from complexity hardness. Those corrections are reflected above. Historical searches and proposed extensions are retained as context, not promised next work.
