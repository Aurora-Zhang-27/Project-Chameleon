# Exact subset-bound recursion for N≤3 and an N=4 counterexample

Drafted 2026-09-28; revised after independent review on 2026-09-29. English publication edition, 2026-10-14.

**Status: independently reviewed.** [The review](REVIEW_N3_N4_20260928_CODEX.md) found no mathematical error. Its thirteen recommendations are addressed in §9. Literature priority remains unconfirmed. Dependencies are the real sandwich theorem, LP duality and the endpoint lemma ([N2 theorem](SEED_N2_THEOREM.md), §4; also Xie & Chen, Proposition 2). Lemma 3 has both a manual proof and a rational certificate. N=4 counterexamples have exact certificates; floating-point checks are supporting evidence only.

## 0. Results

| Result | Scope | Basis |
|---|---|---|
| Proposition 1: explicit single-request H-description using {0,±1} normals | Any N; submodular/supermodular input description | Sandwich theorem |
| Theorem 2: K∈H3″ implies K+P_y∈H3″, with additive tight bounds | N≤3 | Proposition 1 |
| Lemma 3: closed-form tightening preserves sub/supermodularity | Singleton/full-set formulas for any N; pair formula and preservation for N=3 | Manual proof and rational certificate |
| Theorem 4: exact recursion using at most 14 bounds and +,−,min,max | N≤3; polynomial bit complexity for rational inputs | Theorem 2, Lemma 3, endpoint lemma |
| Example A: synthetic H3″ closure fails | N=4; first-layer counterexample | Exact calculation |
| Example B: a real kernel has a mixed-sign facet | N=4,T=2; extend to any N≥4 with inert devices | Rational certificate |

The three layers distinguish synthetic closure failure, a real recursion leaving H3″, and real non-subset facets. Only the last disproves exact subset representation.

## 1. Notation and tools

V={1,…,N}, x(S)=Σ_{i∈S}x_i, and

    P_y={p:−C≤p≤D, p(V)=y},
    P(b)={x:x(S)≤b(S) for all S},
    Q(a)={x:x(S)≥a(S) for all S}.

Every set function is normalized at ∅. E,C,D are finite and nonnegative, l_t≤u_t, and period duration is one or absorbed into the power limits. The mathematical theorem allows real parameters; rational encoding is a separate complexity assumption.

Class 𝓗 consists of K=P(b)∩Q(a), where b is submodular and a supermodular; descriptions need not be tight. Class H3″ consists of nonempty sets equal to their tight subset description, with b_K(S)=max_K x(S) submodular and a_K(S)=min_K x(S) supermodular. Thus H3″⊆𝓗.

**F1: support additivity.** b_{K+P}(S)=b_K(S)+b_P(S), and similarly for lower bounds.

**F2: one-request bounds.** P_y is nonempty iff −C(V)≤y≤D(V). Then

    b_{P_y}(S)=min(D(S),y+C(V∖S)),
    a_{P_y}(S)=max(−C(S),y−D(V∖S)).

The feasible range of p(S) is the intersection of [−C(S),D(S)] and [y−D(V∖S),y+C(V∖S)], whose endpoints are attained by continuous allocations. With w=C+D,

    b_{P_y}(S)=−C(S)+min(w(S),y+C(V)).

This is a modular function plus a constant truncation of a nonnegative modular function, hence submodular. The lower formula is supermodular. Both are nondecreasing in y.

**F3: vector convolution.** For a vector c define

    (b□c)(S)=min_{T⊆S}[b(T)+c(S∖T)].

It is submodular and P(b)∩{x≤c}=P(b□c). Forward inclusion follows by splitting x(S); reverse inclusion takes T=S to recover P(b), and S={i},T=∅ to recover x_i≤c_i.

For submodularity, take minimizers X′⊆X,Y′⊆Y. Add the submodular inequality for b(X′),b(Y′) to the elementwise identity

    1_{X∖X′}+1_{Y∖Y′}
      =1_{(X∪Y)∖(X′∪Y′)}+1_{(X∩Y)∖(X′∩Y′)}.

Both sides per element equal x+y−x′−y′, since max+min equals sum. This identity is valid for arbitrary signed c. Each resulting term bounds the corresponding convolution minimum from above, giving the required inequality.

The dual operation (a♯c)(S)=max_{U⊆S}[a(U)+c(S∖U)] is supermodular and Q(a)∩{x≥c}=Q(a♯c). Lowering only b(V), or raising only a(V), preserves submodularity/supermodularity: in nontrivial inequalities V occurs only on the right; when V is an input set, it cancels.

Source: Frank–Tardos (1988), Proposition II.2.11 gives the g-polymatroid box-intersection formula min_Y[b(Y)+g(X∖Y)−f(Y∖X)]. Taking no lower box bound gives the formula here. Submodular polyhedra are generalized polymatroids by Proposition II.2.1.

**F4: real sandwich/separation theorem.** If normalized b is submodular, a supermodular and a≤b pointwise, there exists x∈ℝ^V with a(S)≤x(S)≤b(S) for every S. Integer inputs allow an integer x. No crossing condition is needed. Thus a description in 𝓗 is nonempty iff a≤b.

Source status:

- A. Frank, *An algorithm for submodular functions on graphs*, Annals of Discrete Mathematics 16 (1982), 97–120, DOI 10.1016/S0304-0208(08)72446-0. The original full text was not obtained; no original theorem number is claimed.
- Murota, *Discrete Convex Analysis II* (2016), slide 38 explicitly states the real formula.
- Frank–Tardos, *Generalized polymatroids and submodular flows*, Mathematical Programming 42 (1988), 489–563, Theorem I.2, checked in full on 2026-10-12. For intersecting sub/supermodular real functions b′,p′, existence of a separating modular function is equivalent to Σp′(F_i)≤Σb′(G_j) for two families of disjoint subsets with the same union. Full sub/supermodularity reduces this condition to p′≤b′, giving F4.
- Murota, *Discrete convex analysis*, Mathematical Programming 83 (1998), 313–371, Theorem 3.5 is the integer version; Remark 3.1 relates it to Edmonds' intersection theorem.

**F5: weak exchange for tight bounds.** For disjoint X,Z and any nonempty compact K,

    b_K(X∪Z)≥b_K(X)+a_K(Z),
    a_K(X∪Z)≤a_K(X)+b_K(Z).

For the first, maximize x(X) over K and bound its x(Z) below; the second is symmetric. Tightness, rather than the crossing condition, is essential.

## 2. Proposition 1: exact single-request H-description for any N

Let K=P(b)∩Q(a) be nonempty with b submodular and a supermodular, not necessarily tight, and P_y nonempty. Then e∈K+P_y iff all three groups hold:

    (ii) e(T)≤b(T)+y+C(V∖T), for every T;
    (iii) e(U)≥a(U)+y−D(V∖U), for every U;
    (i) e(A)−e(B)≤b(A∪M)−a(B∪M)+D(A)+C(B),
        for pairwise disjoint A,B,M.

A and B may be empty. This gives an H-representation whose normals can be chosen from {0,±1}^N, rather than a statement about every scaled normal. For lower-dimensional sets, facets are relative to the affine hull.

**Proof.** Write e=x+p, let u=e+C, d=e−D, and β=e(V)−y. We need x∈K∩[d,u] with x(V)=β. Merge the upper box by b□u, then lower its full-set value to min(β,(b□u)(V)); call the resulting submodular function b″. Similarly merge the lower box by a♯d and raise its full-set value to max(β,(a♯d)(V)), obtaining supermodular a″. F4 says that the required x exists iff a″≤b″.

For T,U⊆S, expand a(U)+d(S∖U)≤b(T)+u(S∖T). Set

    A=T∖U, B=U∖T, M=T∩U, R=S∖(T∪U).

These four sets are disjoint; S∖U=A∪R and S∖T=B∪R. The condition becomes

    e(A)−e(B)≤b(A∪M)−a(B∪M)+D(A)+C(B)+w(R).

Since w≥0, R=∅ is strongest, actually occurs in the system, and implies every R≠∅ case. These are (i). At S=V, with L=(a♯d)(V), U₀=(b□u)(V), the additional comparison is max(L,β)≤min(U₀,β), equivalent to L≤U₀, L≤β and β≤U₀. The first is already in (i); the last two expand to (iii) and (ii). No other conditions are missing. ∎

Necessity of (i) can also be seen directly from e(A)−e(B)=x(A∪M)−x(B∪M)+p(A)−p(B).

Historical numerical check: 150 descriptions each at N=3 and N=4, twenty directions each; maximum support discrepancies 3.6e−15 and 7.1e−15. That search script is outside this minimal release.

## 3. Theorem 2: one-request closure of H3″ for N≤3

If N≤3, K∈H3″ with tight bounds (a,b), and P_y≠∅, then

    K+P_y=Õ={e:a(S)+a_{P_y}(S)≤e(S)≤b(S)+b_{P_y}(S)}.

Its displayed bounds are tight, submodular/supermodular, so it belongs to H3″.

**Proof.** F1 gives inclusion in Õ. Conditions (ii),(iii) follow immediately from F2. For (i) with B=∅, e(A)≤b(A)+D(A)≤b(A∪M)−a(M)+D(A), by F5. A=∅ is symmetric; A=B=∅ is just a(M)≤b(M).

For nonempty A,B, put R₀=V∖(A∪B), choose N₀⊆R₀ and let Ṅ=R₀∖N₀ and s=y+C(B)−D(A). Subtract Õ's upper/lower bounds on A∪N₀ and B∪N₀:

    e(A)−e(B)≤b(A∪N₀)−a(B∪N₀)+D(A)+C(B)+g(N₀),
    g(N₀)=min(D(N₀),s+C(Ṅ))+min(C(N₀),D(Ṅ)−s).

The exact substitutions are b_P(A∪N₀)=D(A)+min(D(N₀),s+C(Ṅ)) and −a_P(B∪N₀)=C(B)+min(C(N₀),D(Ṅ)−s). For every real s, even outside [−C(R₀),D(R₀)],

    g(∅)=min(0,s+C(R₀))+min(0,D(R₀)−s)≤0,
    g(R₀)=min(D(R₀),s)+min(C(R₀),−s)≤s−s=0.

Thus (i) follows for M=∅ or R₀, taking N₀=M. With N≤3 and A,B nonempty, |R₀|≤1, so these are the only choices. Proposition 1 proves equality. F1 then proves tightness, and F2 gives sub/supermodularity. ∎

At N≥4 an intermediate ∅≠M⊊R₀ may have g(M)>0. Example A realizes this gap.

## 4. Lemma 3: tightening a sub/supermodular description

Let nonempty K=P(b)∩Q(a)∈𝓗, and β(S)=max_K x(S), α(S)=min_K x(S).

### (a) Singleton bounds, any N

    β(i)=min_{S∋i}[b(S)−a(S∖i)],
    α(i)=max_{S∋i}[a(S)−b(S∖i)].

To impose x_i≥θ, set a′(X)=a(X) if i∉X, and a′(X)=max(a(X),θ+a(X∖i)) otherwise. This exactly describes K∩{x_i≥θ}. The following table verifies supermodularity for every branch, with U=X∪Y,I=X∩Y:

| Case | Chosen left branches | Right lower bounds | Original supermodular pair |
|---|---|---|---|
| Neither contains i | a(X)+a(Y) | a(U)+a(I) | X,Y |
| Only X contains i, unshifted | a(X)+a(Y) | a′(U)≥a(U), a′(I)=a(I) | X,Y |
| Only X contains i, shifted | θ+a(X∖i)+a(Y) | a′(U)≥θ+a(U∖i), a′(I)=a(I) | X∖i,Y |
| Both contain i, neither shifted | a(X)+a(Y) | a′(U)≥a(U), a′(I)≥a(I) | X,Y |
| Both shifted | 2θ+a(X∖i)+a(Y∖i) | Shifted branches at U and I | X∖i,Y∖i |
| Only Y shifted | a(X)+θ+a(Y∖i) | a′(U)≥a(U), a′(I)≥θ+a(I∖i) | X,Y∖i |
| Only X shifted | θ+a(X∖i)+a(Y) | Symmetric to preceding row | X∖i,Y |

Taking maxima does not automatically preserve supermodularity; this branch argument is necessary. F4 yields feasibility exactly when θ≤b(S)−a(S∖i) for every S∋i. Finite bounds make K closed and bounded, so the threshold is attained. Apply the mirror argument to −K for α.

The construction cannot simply replace i by a pair. On V={1,2,3}, take a(X)=1[{1,3}⊆X], b(X)=3|X|, I₀={1,2},θ=1. The analogous a′ gives a′(12)+a′(13)=2>1=a′(123)+a′(1), violating supermodularity.

### (b) Full-set bounds, any N

β(V)=b(V), α(V)=a(V). Raise a(V) to b(V), preserving supermodularity by F3; a≤b remains true and F4 supplies an attaining point. The lower formula is symmetric.

### (c) Pair bounds for N=3

For {i,j,k}=V,

    β(ij)=min(b_ij,b_V−a_k,b_V+b_i−a_ik,b_V+b_j−a_jk),
    α(ij)=max(a_ij,a_V−b_k,a_V+a_i−b_ik,a_V+a_j−b_jk).

Slice at x_k=t. Its six bounds are

    u_i=min(b_i,b_ik−t), u_j=min(b_j,b_jk−t),
    u_ij=min(b_ij,b_V−t),
    ℓ_i=max(a_i,a_ik−t), ℓ_j=max(a_j,a_jk−t),
    ℓ_ij=max(a_ij,a_V−t),

with a_k≤t≤b_k. Projection of compact convex K onto x_k is exactly the closed interval [α(k),β(k)], including attained endpoints. Nonempty slices can be points or segments; the N2 lemma still applies. Their maximum pair sum is min(u_ij,u_i+u_j), nonincreasing in t. Therefore choose t=α(k).

Substitute α(k)=max(a_k,a_ik−b_i,a_jk−b_j,a_V−b_ij). The expansion of b_V−α(k) gives the three nontrivial terms in β(ij) and b_V−a_V+b_ij≥b_ij. The four terms of u_i+u_j are redundant:

    b_i+b_j≥b_ij,
    b_i+b_jk−α(k)≥b_V−α(k),
    b_ik+b_j−α(k)≥b_V−α(k),
    b_ik+b_jk−2α(k)≥b_V+b_k−2α(k)≥b_V−α(k).

The last uses b_k≥β(k)≥α(k). These are description bounds, not assumed tight. Mirroring gives α(ij).

### (d) Tight-bound sub/supermodularity for N=3

Incomparable pairs are exactly: distinct singletons, a singleton and its complementary pair, or overlapping pairs. The first two are disjoint, so support subadditivity gives β(X)+β(Y)≥β(X∪Y). It remains to show β(ij)+β(ik)≥β(V)+β(i).

Take i=1,j=2,k=3. Let P₁…P₄ be the four terms for β(12), Q₁…Q₄ those for β(13). Since β(V)=b123 and β(1)=min(b1,b12−a2,b13−a3,b123−a23), every P+Q−b123 must dominate one of these four terms:

| P,Q | P+Q−b123 | Lower bound | Reason |
|---|---|---|---|
| b12,b13 | b12+b13−b123 | b1 | Submodularity |
| b12,b123−a2 | b12−a2 | b12−a2 | Equality |
| b12,b123+b1−a12 | b12+b1−a12 | b1 | b12≥a12 |
| b12,b123+b3−a23 | b12+b3−a23 | b123−a23 | b12+b3≥b123 |
| b123−a3,b13 | b13−a3 | b13−a3 | Equality |
| b123−a3,b123−a2 | b123−a2−a3 | b123−a23 | a23≥a2+a3 |
| b123−a3,b123+b1−a12 | b123+b1−a3−a12 | b1 | a12+a3≤a123≤b123 |
| b123−a3,b123+b3−a23 | b123+b3−a3−a23 | b123−a23 | b3≥a3 |
| b123+b1−a13,b13 | b1+b13−a13 | b1 | b13≥a13 |
| b123+b1−a13,b123−a2 | b123+b1−a13−a2 | b1 | a13+a2≤a123≤b123 |
| b123+b1−a13,b123+b1−a12 | b123+2b1−a12−a13 | b1 | a12+a13≤a123+a1≤b123+b1 |
| b123+b1−a13,b123+b3−a23 | b123+b1+b3−a13−a23 | b1 | a13+a23≤a123+a3≤b123+b3 |
| b123+b2−a23,b13 | b13+b2−a23 | b123−a23 | b13+b2≥b123 |
| b123+b2−a23,b123−a2 | b123+b2−a2−a23 | b123−a23 | b2≥a2 |
| b123+b2−a23,b123+b1−a12 | b123+b1+b2−a12−a23 | b1 | a12+a23≤a123+a2≤b123+b2 |
| b123+b2−a23,b123+b3−a23 | b123+b2+b3−2a23 | b123−a23 | b2+b3≥b23≥a23 |

Relabelling covers all overlapping pairs. Apply the same argument to −K, with description (−b,−a), to prove α supermodular. ∎

**Independent exact certificate:** `evidence/n3_lemma_certificate.py` enumerates all dual vertices (nine or eleven per S at N=3) and uses rational Farkas identities to show closed-form equivalence, domination of fractional dual vertices by integral ones, and all 121 vertex-pair inequalities. Consequently tightening uses only integer combinations of a,b; division is unnecessary.

Its optional N=4 mode leaves 21,616/50,176 pairs uncertified, but the target uses description b(123), not tight β(123). It tests a stronger statement than submodularity; uncertified pairs are not counterexamples. Historical floating-point cut-type tests separately found 79/255 N=4 tight-bound violations and none in 657 N=3 descriptions.

## 5. Theorem 4: exact backward recursion for N≤3

Assume the lossless, fully available model above with N≤3, arbitrary finite nonnegative E,C,D, including asymmetric powers, zero capacities and zero powers. Each K_t is either empty or in H3″. The exact recursion is:

1. Terminal tight bounds: a_T(S)=0, b_T(S)=E(S).
2. Empty successor, l_t<−C(V), or u_t>D(V): return empty.
3. Request bounds: b̃=b_{t+1}+b_{P_l}, ã=a_{t+1}+a_{P_u}.
4. Physical box: b̂=b̃□E, â=ã♯0, preserving sub/supermodularity.
5. Nonempty iff â≤b̂ pointwise, by F4.
6. Tighten by Lemma 3 to obtain (a_t,b_t).

**Proof.** Backward induction starts with the modular tight terminal bounds. The endpoint lemma gives K_t=[0,E]∩(K+P_l)∩(K+P_u). Theorem 2 provides exact subset descriptions for both sums; F2's monotonicity selects l for upper bounds and u for lower bounds. F3 merges the box, possibly giving a nontight description in 𝓗. F4 tests nonemptiness; Lemma 3 returns truly tight sub/supermodular bounds. Replacing an exact subset description by its tight bounds does not change its set. Thus K_t∈H3″ and F5's tightness assumption remains valid at the next step. ∎

N=2 agrees with the six-bound theorem; N=1,2 can also be embedded with inert E=C=D=0 devices. T=0 is just terminal-box membership.

**Complexity.** The real theorem and rational bit-cost assertion are separate. For binary-encoded rational inputs listing T intervals explicitly:

- Each period has at most 14 request bounds, eight terms per box convolution, and four terms per tightening formula. Arithmetic cost is O(T).
- Let L be the least common multiple of all input denominators. Each min/max selects an existing expression; on the selected branch every bound is an integer linear combination of inputs, with denominator dividing L. It is not one fixed linear expression valid across all branches.
- Set R=1+E(V)+C(V)+D(V)+max_t(|l_t|+|u_t|), using zero for the last maximum when T=0. Tight inputs lie in [0,E(V)]; every intermediate is a constant-size sum/difference of these bounds, powers and endpoints, with magnitude at most cR for fixed N≤3. Tightening at each period prevents uncontrolled accumulation; stop at emptiness.
- After scaling by L, integers have O(1+log L+log R) bits, polynomial in input length. Total bit complexity is therefore polynomial.

**Causal execution.** After observing y at e∈K_t, select x in K_{t+1}∩[e−D,e+C]∩{x(V)=e(V)−y} and return p=e−x. First merge the coordinate box using F3, then the full-total equality as in Proposition 1. Lemma 3(a) can maximize x₁, after which a two-dimensional slice gives a selector. Merely editing singleton values can destroy sub/supermodularity, so merging cannot be omitted. Alternatively `n3_exact.action()` uses rational vertex enumeration.

`evidence/n3_exact.py` implements the recursion. Optional CROSSCHECK performs exact independent vertex tightening and H3″ assertions; this extra validation is not part of the production arithmetic bound. Its validation gives 46 cases (43 feasible, three empty), 602 floating-point tree-support comparisons and 94 rational action transitions at midpoint requests. Independent attacks gave 60 extreme N=3,T=5–6 cases, 461 exact feasible outer-vertex witnesses in 50 nonempty cases, 1,300 rational primal–dual support certificates, and 160 nontight descriptions matching exact geometry.

A historical stress run had one false infeasibility from the default HiGHS presolve path. A complete rational policy and a presolve-off solve proved the point feasible. The review preserves the original dis=1; it is not a mathematical counterexample. The large historical stress script is not part of the minimal release.

## 6. N=4 counterexamples

### 6.1 Example A: synthetic closure failure

    K={x∈[0,10]^4:x₁+x₃≤10, x₂+x₃≥10}, C=D=1, y=0.

Its tight bounds are b(S)=10|S|−10·1[{1,3}⊆S] (submodular) and a(S)=10·1[{2,3}⊆S] (supermodular). Three crossing inequalities fail, so it is in H3″ but not a g-polymatroid. The point e=(7,3,5,5) satisfies all thirty subset bounds of Õ, yet e₁−e₂=4. On K+P₀,

    e₁−e₂=(x₁+x₃)−(x₂+x₃)+p₁−p₂≤2.

Equality is attained at x=(5,5,5,5),p=(1,−1,0,0). Intersecting with [0,10]^4 preserves a gap of 2 versus 4 in the tight subset hull. In Theorem 2's notation A={1},B={2},M={3},R₀={3,4}, and g(M)=2. This disproves synthetic closure, not by itself a real-storage invariant. The original `n4_single_request_cx.py` is outside the minimal publication; the construction above is self-contained.

### 6.2 Example B: a real kernel with a mixed-sign facet

    E=(4,5,1,1), C=(0,0,3,1/2), D=(1,1/2,2,0),
    intervals [1/5,1], [−1,6/5].

1. At t=1, request −1 forces p₃+p₄≤−1 since p₁,p₂≥0. Terminal capacities imply e₃+e₄≤1.
2. Request 6/5 has p₁+p₄≤1, hence e₂+e₃≥1/5.
3. Subtracting gives e₄−e₂≤4/5 throughout K₁.
4. The first-period difference becomes e₄−e₂−p₄+p₂≥e₄−e₂, because p₄≤0,p₂≥0. Thus K₀ also satisfies e₄−e₂≤4/5.
5. Its tight subset hull contains e*=(4,0,1/5,1), whose difference is 1.

`evidence/n4_real_certificate.py` supplies thirty rational endpoint-tree policies, checking every constraint exactly. Their subset sums prove that e* lies in a subset hull contained in the true tight subset hull; exact support optimality is unnecessary for this logic. The elementary valid inequality excludes e*.

`review_codex_n4_geometry.py` separately certifies all thirty optimal supports and max_K₀(e₄−e₂)=4/5 using rational primal–dual witnesses. K₀ has dimension four and the equality face dimension three, so this is a facet.

For C₁=C₂=D₄=ε, the last-period bounds become e₃+e₄≤1+2ε and e₂+e₃≥1/5−ε, so its difference is at most 4/5+3ε. The first action can reduce that difference by at most 2ε, giving the root bound 4/5+5ε. At ε=1/100, e*=(4,0,9/50,1) still has difference 1>17/20. Both exact certificates and dimensions four/three persist with every power positive. A historical floating scan loses the gap near ε≈0.04.

Appending inert devices gives K_t×{0}, so failure extends to every N≥4; facets are then relative to the affine hull. The shared device 3 cancels from the upper/lower constraints, while nearly one-way devices 2 and 4 preserve the mixed difference. N=3 lacks the fourth device in R₀∖M.

### 6.3 Historical numerical screening

| Check | Result |
|---|---|
| Four seeds, 1,500 zero-allowed instances each | Ten mixed gaps, 0.1–0.7, in 4,018 nonempty instances |
| Positive powers ≥0.5 | No gap in about 3,970 feasible instances |
| Example B perturbation | Fails at ε=0,0.01; no gap observed at 0.05,0.1,0.2 |
| Early facet enumeration | Two mixed unit-coefficient examples in 2,973 certified instances; no other directions observed |

These early searches are not included here and do not imply exactness for positive powers or larger horizons. Later coefficient-2 counterexamples supersede the early direction observation.

## 7. Implications and literature

General N≥4 subset recursion is an outer approximation, not an exact method. This does not exclude special regimes such as homogeneous fleets. The earlier question whether all real facet directions lie in {0,±1} was answered negatively on 2026-10-10: `n4_normal_certificate.py` certifies a (−1,0,0,2) facet at N=4,T=4. Growth of primitive coefficients with T remains open; see [the method document](N3_METHOD_AND_N4_PLAN.md).

Treat F3/F4 and Lemma 3(a)(b) as known tools. No precedent was found in the checked sources for Proposition 1, Lemma 3(c)(d), Theorem 4 or the three/four-device boundary. Relevant comparisons are Moriguchi–Murota's L-convex sums, Danilov–Koshevoy's unimodular edge-direction class, and the two-phase Evans–Tindemans–Angeli storage framework. The literature record states reading depth and unavailable sources.

H3″ is a proper subclass of continuous M♮₂ polyhedra, which are intersections of two g-polymatroids; max/min of their descriptions need not preserve super/submodularity. The general M♮₂ framework therefore does not prove this invariant.

## 8. Review checkpoints

The independent audit checked F3's elementwise identity; Proposition 1's four-set expansion; F2 substitution and both g endpoints; every singleton-supermodularity branch; all six slice bounds and their dominance; the sixteen-row table; the exact endpoint/box/tightening induction; Example B's first four steps; and the lemma/implementation/counterexample scripts. Its report distinguishes exact certificates from float comparisons and preserves solver discrepancies.

## 9. Resolution of the thirteen review recommendations

| # | Recommendation | Resolution |
|---|---|---|
| 1 | Rational encoding, L/R, branchwise combinations and term counts | Explicit in §5 |
| 2 | Sandwich sources and original-text status | Explicit in F4; formal sources added October 12 |
| 3 | Slice lower bounds and attainable projection endpoints | Added in Lemma 3(c) |
| 4 | Every singleton-supermodularity branch | Seven-row table and pair counterexample |
| 5 | Merge box and total before action selection | Added in §5 |
| 6 | Distinguish feasible witnesses from optimality certificates | Separate certificate scopes in Example B |
| 7 | Correct interpretation of optional N4 dual test | Stronger target and non-counterexample status specified |
| 8 | Normal directions and relative facets | H-representation wording; dimension certificates |
| 9 | Net absorption at least one and ε slack | Exact derivation in Example B |
| 10 | Parameter domain, inert embeddings and T=0 | Explicit |
| 11 | Stress-test time limit | Historical 300-second limit applied only to N3 |
| 12 | Tools versus possible new structure | Separated in §7; priority remains open |
| 13 | Solver false infeasibility | Presolve-off retry and rational regression witness; original dis=1 retained |
