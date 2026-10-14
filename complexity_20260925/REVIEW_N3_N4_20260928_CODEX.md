# Independent Codex review: N≤3 theorem and N=4 counterexample

**Overall verdict: Theorem 4 holds.** In the lossless, fully available, continuous bidirectional-power model, the proof of exact tight-subset recursion for N≤3 is valid, including zero capacities/powers, singleton requests and lower-dimensional sets. Example B is valid and refutes general H3′. No mathematical error overturning the theorem or error in the closed-form implementation was found. The stress run produced one discrepancy, independently diagnosed as false infeasibility on the local default solver path, not a counterexample.

Review completed 2026-09-29; the date in the filename follows the original request. Audited branch `codex/full-binary-lightweight-release-20260801`, commit `babbb919f52c201687aaa0f423e386c68803558e`. This English publication edition preserves the historical audit and separates later fixes; line numbers and missing large-search scripts refer to the audited revision, not current publication locations. Existing source files and frozen results were not modified during the original review.

The review read CLAUDE.md, the main proof, referenced two-dimensional lemmas and blueprint sections 1/4. Independent attacks did not import oracle2,n3_exact or n2_exact. Manual derivations establish general claims; rational Farkas identities cover the parameter cone; rational instance certificates certify only those instances. Passing this review does not establish literature priority.

## 1. Checkpoint conclusions

| Checkpoint | Conclusion | Category and reason |
|---|---|---|
| F3 convolution, set equivalence, elementwise identity | Pass | Correct proof; nine legal element patterns checked exactly |
| Real F4 and Frank 1982 attribution | Pass with source qualification | Author slides give the exact real statement; original Frank full text unavailable at review date |
| Proposition 1, full-set edits and three condition groups | Pass | Modularity preserved; expansion complete; correct R=∅ dominance |
| Theorem 2, g and dimension boundary | Pass | Endpoint bounds valid for all real s; induction supplies tightness |
| Lemma 3(a)(b) | Pass | Singleton modification supermodular; full extrema attained; pair substitution fails |
| Lemma 3(c) | Pass; wording gap | Correct formula/dominance; spell out three lower slice bounds |
| Lemma 3(d), sixteen rows | Pass | Every row valid; incomparable-pair classification exhaustive |
| Theorem 4 induction and emptiness | Pass | Every recursive input is genuinely tight |
| Complexity paragraph | Wording gap, directly repairable | Specify rational binary inputs, L/R, branch-dependent combinations and candidate counts |
| Causal selector explanation | Wording gap | Merge coordinate box and total equality before using Lemma 3(a) |
| Example B steps 1–4 | Pass | Valid root inequality; correct dynamic signs |
| Original B rational policies | Pass; output wording issue | Feasible witnesses suffice; they alone do not certify optimal support |
| Independent B optimality and facets | Pass | Exact primal–dual certificates, dimensions four/three for both ε values |
| Lemma-certificate N3 mode | Pass | Final Fraction checks every Farkas identity |
| Optional N4 mode interpretation | Wording issue | Uses b(123), a stronger target than true tight-bound submodularity |
| Fixed implementation and counterexample scripts | Pass | Expected output; precise exact/float scopes below |
| Stress seed 5 | Verification-layer error | Original N3 dis=1,assert_fail=0; exact policy proves solver false infeasibility |
| Independent attacks A/B/C | Pass on tested instances | Sixty recursions and 160 synthetic descriptions; no counterexample |
| Blueprint assumptions and three layers | Pass with minor clarification | Specify finite nonnegative parameters, interval ordering and units |
| Full literature priority | Undetermined | Relevant source checks completed, not an exhaustive exclusion |

## 2. F3/F4 and Proposition 1

For element indicators x,y,x′,y′ with x′≤x,y′≤y,

    max(x,y)−max(x′,y′)+min(x,y)−min(x′,y′)=x+y−x′−y′.

Containment makes these differences the desired set-difference indicators. Multiplying by arbitrary signed c_i preserves equality. Add b's submodularity, then compare each candidate to the appropriate convolution minimum; the inequality direction is correct. Set equality follows from splitting x(S); T=S and singleton S,T=∅ recover the original constraints. Lower max convolution follows by sign reversal.

Only lowering b(V) preserves submodularity: if an input is V it cancels, otherwise V can occur only on the right as a union. The mirror applies to raising a(V). Proposition 1 uses min(old,β) and max(old,β), correctly.

At review time, [Frank's publisher page](https://www.sciencedirect.com/science/article/pii/S0304020808724460) confirmed the 1982 bibliography but not the needed real theorem number. [Murota's 2016 lecture slides, slide 38](https://kzmurota.fpark.tmu.ac.jp/paper/160510BonnHCMecon2web.pdf#page=38) explicitly state real separation for normalized sub/supermodular functions under pointwise order, without a crossing condition. Later author revisions added Frank–Tardos (1988), Theorem I.2, as a checked formal real source; this later check should not be retroactively attributed to the September review.

Writing e=x+p gives x∈[e−D,e+C] and x(V)=e(V)−y. Merge boxes by F3 and impose full-total upper/lower edits. For T=A∪M,U=B∪M,S=A∪B∪M∪R, S∖U=A∪R and S∖T=B∪R, yielding

    e(A)−e(B)≤b(A∪M)−a(B∪M)+D(A)+C(B)+(C+D)(R).

R=∅ occurs among the original comparisons and implies the others because C+D≥0. At S=V, max(L,β)≤min(U,β) is exactly L≤U,L≤β,β≤U. These produce (i),(iii),(ii), with no omitted fourth condition. Say normals **can be chosen** in {0,±1}; arbitrary rescaling or low-dimensional normal cones require direction/relative-facet language.

## 3. Theorem 2

Direct F2 substitution gives

    b_P(A∪N₀)=D(A)+min(D(N₀),s+C(Ṅ)),
    −a_P(B∪N₀)=C(B)+min(C(N₀),D(Ṅ)−s),

where s=y+C(B)−D(A),Ṅ=R₀∖N₀. No complement or power term is missing. g(∅) is a sum of nonpositive minima; g(R₀)≤s−s=0. Both hold for every real s, including outside [−C(R₀),D(R₀)]. One-sided A/B cases use F5's true tightness, not a crossing condition or interior assumption. Nonempty A,B consume two distinct devices, so N≤3 implies |R₀|≤1 and M can only be empty/full. Once equality is proved, F1 gives genuine tight additive bounds; adding arbitrary nontight input functions would not justify this step.

## 4. Lemma 3

### 4.1 Singleton/full-set formulas

The added-bound description K∩{x_i≥θ}=P(b)∩Q(a′) is exact. For neither set containing i, original supermodularity suffices. If only X contains i, its unshifted/shifted branches use (X,Y)/(X∖i,Y). If both contain i, the four branch combinations use (X,Y), (X∖i,Y∖i), (X,Y∖i), (X∖i,Y). These are all seven rows of the revised proof table; every left branch has a corresponding right lower bound. F4 yields the threshold θ≤min_{S∋i}(b(S)−a(S∖i)); compactness gives attainment.

Replacing the singleton by I₀={1,2} fails already on V={1,2,3}: a(X)=1[{1,3}⊆X],b(X)=3|X|,θ=1 gives a′(12)+a′(13)=2>1=a′(123)+a′(1). The independent script checks this exact gap of one. Full-set attainment is valid by raising a(V) to b(V), or lowering b(V) to a(V), and applying F4.

### 4.2 Pair slices

Complete the three lower bounds as ℓ_i=max(a_i,a_ik−t),ℓ_j=max(a_j,a_jk−t),ℓ_ij=max(a_ij,a_V−t), with a_k≤t≤b_k. Projection of compact convex K is the attained interval [α(k),β(k)]; lower-dimensional slices are permitted. On each nonempty slice the maximum pair sum is min(u_ij,u_i+u_j), nonincreasing in t, so t=α(k) is valid. This does not require nested slices.

Substitution gives the stated three terms plus b_V−a_V+b_ij≥b_ij. The four coordinate-sum expansions are dominated by b_ij or b_V−α(k), using submodularity and b_k≥β(k)≥α(k). The last inequality needs only a description bound, not tight b_k.

### 4.3 Sixteen-row check

The revised main document retains every algebraic expression. The audit's lower bounds for P_m+Q_n−b123 are:

| P row / Q column | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| 1 | b1 | b12−a2 | b1 | b123−a23 |
| 2 | b13−a3 | b123−a23 | b1 | b123−a23 |
| 3 | b1 | b1 | b1 | b1 |
| 4 | b123−a23 | b123−a23 | b1 | b123−a23 |

Every entry is a candidate defining β(1), hence at least β(1). The reasons, respectively by rows, are:

1. b12+b13≥b123+b1; equality; b12≥a12; b12+b3≥b123.
2. Equality; a23≥a2+a3; a12+a3≤a123≤b123; b3≥a3.
3. b13≥a13; a13+a2≤a123≤b123; a12+a13≤a123+a1≤b123+b1; a13+a23≤a123+a3≤b123+b3.
4. b13+b2≥b123; b2≥a2; a12+a23≤a123+a2≤b123+b2; b2+b3≥b23≥a23.

Distinct singletons and singleton/complement pairs are disjoint; overlapping pairs are the only remaining incomparable case at N=3. Comparable pairs give equality. Applying the result to −K proves lower supermodularity.

## 5. Theorem 4 and cost

The endpoint lemma uses convex power boxes, convex successor sets and linear lossless dynamics. Endpoint actions share the same current state; interpolation handles each interior request, then recursion produces a causal policy. It does not independently choose an earlier action for every leaf. l=u needs no interpolation division.

F2 monotonicity selects lower endpoint l for upper bounds and u for lower bounds. F3 gives a possibly nontight but sub/supermodular box-merged description; F4 tests emptiness; Lemma 3 returns truly tight bounds. Tightening an exact subset description preserves the set, hence supplies H3″ for the next step and the tightness needed by F5. Inert embedding covers N=1,2 and all degeneracies; T=0 is the box.

For binary rational inputs listing T intervals, let L be the input-denominator lcm and R=1+E(V)+C(V)+D(V)+max_t(|l_t|+|u_t|), last maximum zero at T=0. Bounds are integer input combinations **on each selected branch**, not one fixed global linear function. Denominators divide L; tight inputs lie in [0,E(V)] and intermediate magnitudes are ≤cR for fixed N≤3. Scaled integer bit length is O(1+log L+log R), giving polynomial bit cost and O(T) arithmetic. Box convolution has up to eight terms; only tightening has at most four.

The closed-form selector must merge the action box and full-total equality before Lemma 3(a). The vertex-enumeration action implementation is correct without assuming raw singleton edits preserve modularity.

## 6. Example B and exact geometry

At the last charging request −1, p₃+p₄≤−1 and terminal capacity gives e₃+e₄≤1: net absorption is **at least** one. At discharge 6/5, p₂+p₃≥1/5, so e₂+e₃≥1/5. Subtract to get e₄−e₂≤4/5. The first action gives next difference=current−p₄+p₂≥current; hence the inequality holds at the root. e*=(4,0,1/5,1) violates it with difference one.

For C₁=C₂=D₄=ε, the last-period difference bound is 4/5+3ε; the first period adds at most 2ε slack. At ε=1/100 the valid root bound is 17/20, violated by e*=(4,0,9/50,1).

The original thirty rational feasible policies give witness upper values no greater than true upper supports and lower values no smaller than true lower supports. Their hull is contained in the true subset hull, so e* membership suffices without exact optimality. The old output suggesting exact support certification was therefore too broad; a tolerance comparison to float optima is not a dual certificate.

`review_codex_n4_geometry.py` independently certifies all thirty supports and the mixed optimum, and rational affine ranks give dimensions four/three. Four equality roots for ε=0 are (9/5,0,2/5,4/5),(9/5,1/5,1/5,1),(2,0,1/5,4/5),(4,0,1/5,4/5). For ε=1/100 they are (179/100,0,39/100,17/20),(179/100,3/20,6/25,1),(2,0,9/50,17/20),(4,0,9/50,17/20). All have exact feasible trees; additional roots span dimension four. Higher-dimensional inert extensions use relative facets.

## 7. Historical reruns and certificate scope

Commands ran in `complexity_20260925/evidence`, with Python 3.9.6, NumPy 1.26.4, SciPy 1.13.1. Large stress/synthetic scripts are not retained in this publication.

| Command | Output |
|---|---|
| `python3 n3_lemma_certificate.py` | Fractional vertices not dominated:0; closed-form S=1,3,7 dual-feasible True and undominated 0; vertex pairs certified121,not certified0 |
| `python3 n3_exact.py` | cases46,feasible43,empty3,support_checks602,exact_actions94 |
| `python3 n4_real_certificate.py` | e*=(4,0,1/5,1),in Q True,lhs1,rhs4/5,final True |
| `python3 n4_real_certificate.py 1/100` | e*=(4,0,9/50,1),in Q True,lhs1,rhs17/20,final True |
| `python3 n4_single_request_cx.py` | Tight upper/lower modularity True; crossing violations3; outer membership exact True; mixed support2.0 versus4.0; membership status2; full-operator gap also2.0 versus4.0 |

The lemma certificate enumerates all rational dual bases and verifies nonnegative solutions. Degenerate vertices can be completed to N-column bases, so smaller supports are not lost. GEN encodes the parameter cone. Float LP searches for

    L_target=Σσ_j L_j+Σν_k g_k, σ,ν≥0, Σσ_j=1,

but Fraction checks nonnegativity, weights and all fourteen coordinate identities before accepting. This is an exact cone-wide certificate. Representative subsets extend by relabelling and sign reversal. N4's optional b(123) target is stronger than β(123); its 21,616 uncertified pairs are not tight-submodularity counterexamples.

N3 support checks are float; its 94 midpoint transitions are rational, not all-tree replay. The synthetic Example A can also be proved independently of its numerical LP: its exact tight bounds are attainable by corner allocations, and e₁−e₂≤2 is attained by x=(5,5,5,5),p=(1,−1,0,0).

### 7.1 Stress discrepancy, preserved rather than overwritten

`python3 -u review_stress.py 5` originally returned

    N2: cases1500,nonempty745,dis0,verts6008;
    N3: cases10182,nonempty7979,dis1,verts83121,assert_fail0.

Only the N3 loop was limited to 300 seconds; case count depends on speed. The disputed case is E=(4,3,4),C=(2,3/2,0),D=(2,0,2), intervals [−1/2,2],[1,2],[1,3/2], root (4,5/2,3/2). The old oracle treated all unsuccessful statuses as False; this particular solve returned status2. Merely classifying solver failures would not fix it.

Independent state-tree modelling found an exact feasible policy. Rebuilding the cumulative-power tree gave default highs status2; highs with presolve=False status0 and exact_feasible True; highs-ds with presolve=False likewise; default highs-ipm still status2. This confirms a local solver-path error, not a claim about every HiGHS version.

| Request history | Action | Next energy |
|---|---|---|
| (−1/2) | (0,−1/2,0) | (4,3,3/2) |
| (2) | (2,0,0) | (2,5/2,3/2) |
| (−1/2,1) | (1,0,0) | (3,3,3/2) |
| (−1/2,2) | (2,0,0) | (2,3,3/2) |
| (2,1) | (1,0,0) | (1,5/2,3/2) |
| (2,2) | (2,0,0) | (0,5/2,3/2) |
| (−1/2,1,1) | (−1/2,0,3/2) | (7/2,3,0) |
| (−1/2,1,3/2) | (0,0,3/2) | (3,3,0) |
| (−1/2,2,1) | (1,0,0) | (1,3,3/2) |
| (−1/2,2,3/2) | (0,0,3/2) | (2,3,0) |
| (2,1,1) | (1,0,0) | (0,5/2,3/2) |
| (2,1,3/2) | (0,0,3/2) | (1,5/2,0) |
| (2,2,1) | (−1/2,0,3/2) | (1/2,5/2,0) |
| (2,2,3/2) | (0,0,3/2) | (0,5/2,0) |

Every sum, power bound and next-energy bound is exact; common histories share actions. Endpoint interpolation extends this tree to continuous requests. This witness alone refutes the reported infeasibility.

## 8. Independent attacks

`python3 review_codex_independent.py` uses independently written state-tree LPs, closed formulas, Fraction Gaussian elimination and primal–dual checking.

| Attack | Coverage | Evidence |
|---|---|---|
| A: extreme N3,T=5–6 | Twelve fixed and 48 seeded cases; zero/inert devices, 100:1 ratios, asymmetric powers, crossing-zero and singleton menus | 60 cases,50 nonempty,10 empty;461 outer vertices with exact feasible policies,failures0 |
| B: subset and mixed directions | Every mixed {0,±1} direction in the fifty nonempty cases | 700 subset+600 mixed=1,300 exact optimal-support certificates,failures0 |
| C: nontight descriptions | 160 coverage/cut/modular-minus-AND descriptions; signed modular shifts | 62 raw-nontight;2,240 exact vertex comparisons+2,240 float LP checks;no modularity violations |

Every successful support certificate verifies rational primal feasibility, dual signs, exact stationarity and objective equality. All outer vertices are enumerated exactly. Their feasibility plus convexity and independently certified support inclusion establishes equality for the tested nonempty kernels. The ten empty-tree classifications remain float evidence, without rational infeasibility certificates. Random long-horizon menus were small (mainly 0.01–0.02) to avoid trivial universal emptiness; the test is not a parameter-space exhaustion.

## 9. Blueprint and literature

Model timing, continuous powers and three counterexample layers are consistent. Explicit domain/unit statements were recommended. The three-device crossing-condition example does not refute H3″; the synthetic non-submodular upper-bound example is not a Theorem-2 input.

[Moriguchi–Murota 2110.10445, §6.3](https://arxiv.org/html/2110.10445#S6.SS3) defines continuous M♮₂ as intersections of two g-polymatroids; its max/min bounds need not retain modularity. H3″ is a proper subclass. The review found no identical Proposition-1 formula, three-dimensional pair-tightening formula or storage dimension boundary, but that is not an exhaustive novelty exclusion. Singleton/full-set lemmas should be tools rather than claimed contributions.

## 10. Suggested changes and later resolution

The original review proposed thirteen changes: rational complexity assumptions and L/R; accurate source status; complete slice bounds; all singleton branches; merge before action selection; feasible-witness wording; N4 certificate-target qualification; direction/relative-facet language; net-absorption and ε derivation; parameter/inert/T=0 domain; precise stress time limits; limited novelty wording; presolve-off retries and the rational regression. The main document's §9 records their subsequent resolution. Original stress dis=1 remains unchanged in this historical audit.
