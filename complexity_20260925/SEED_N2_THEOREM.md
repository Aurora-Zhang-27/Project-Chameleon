# Two-device causal interval commitments: exact six-bound recursion and selector

Drafted 2026-09-25; selector added 2026-09-28. The result was independently reviewed. The algorithm uses rational arithmetic; tree-LP comparisons are floating-point evidence. This document supplies a lemma for Theorem 4 rather than claiming independent literature priority.

## 1. Model and representation

Two lossless, continuously available devices have finite nonnegative E_i,C_i,D_i. Period duration is one hour (or absorbed into the limits): energy is in MWh, power in MW. After observing y∈[l,u], choose p∈[−C,D] with p₁+p₂=y and next state e−p. No future requests may be used. The terminal set is K_T=[0,E].

Write a nonempty future set using six bounds:

    a₁≤x₁≤b₁, a₂≤x₂≤b₂, a₁₂≤x₁+x₂≤b₁₂.

## 2. Feasibility and tight bounds, including degeneracies

Let A=max(a₁₂,a₁+a₂), B=min(b₁₂,b₁+b₂). The set is nonempty iff a_i≤b_i for both coordinates and A≤B. Its tight bounds are

    â₁=max(a₁,A−b₂), b̂₁=min(b₁,B−a₂),
    â₂=max(a₂,A−b₁), b̂₂=min(b₂,B−a₁),
    â₁₂=A, b̂₁₂=B.

All assignments read the original coordinate bounds simultaneously. To prove attainment, fix x₁. An x₂ exists exactly when [a₂,b₂] intersects [A−x₁,B−x₁], yielding the stated projection interval. Every total in [A,B] can be split inside the coordinate box, so A and B are attained. This covers points, line segments, zero capacity, zero power and equality cases; no strict interior is needed.

## 3. Exact predecessor for one request

Let L=max(−C₁,y−D₂), U=min(D₁,y+C₂). If L>U, P_y is empty. Otherwise let q=p₁, p₂=y−q. Feasibility is precisely the nonemptiness of

    [L,U] ∩ [e₁−b₁,e₁−a₁] ∩ [a₂−e₂+y,b₂−e₂+y],

together with a₁₂+y≤e₁+e₂≤b₁₂+y. Intervals on the real line have a common intersection iff every pair intersects. Expanding the pairwise conditions gives

    a₁+L≤e₁≤b₁+U,
    a₂+y−U≤e₂≤b₂+y−L,
    a₁+a₂+y≤e₁+e₂≤b₁+b₂+y.

For tight input bounds, the final pair of inequalities is dominated by the total bounds. Thus K+P_y has exactly six bounds

    (a₁+L, b₁+U, a₂+y−U, b₂+y−L, a₁₂+y, b₁₂+y).

## 4. Endpoint lemma and recursion

For a fixed e, feasible endpoint actions p_l,p_u interpolate: if y=(1−λ)l+λu, take p=(1−λ)p_l+λp_u. The power box and K are convex, so e−p remains in K. For l=u use the single action directly. Consequently

    K_t=[0,E]∩(K_{t+1}+P_l)∩(K_{t+1}+P_u).

Start at the terminal box. Each backward step computes both endpoint descriptions, intersects their six inequalities with the physical box, tests nonemptiness and applies §2 to obtain tight bounds. Empty successor or endpoint power set means empty predecessor. This is an exact induction, including lower-dimensional sets.

## 5. Executable causal selector

For e∈K_t and the currently observed y, use the tight bounds of K_{t+1} and define

    q₋=max(−C₁,y−D₂,e₁−b₁,a₂−e₂+y),
    q₊=min(D₁,y+C₂,e₁−a₁,b₂−e₂+y).

The endpoint lemma and §3 ensure q₋≤q₊, including interior requests. The total-state condition follows from the endpoint total bounds. Choose p₁=q₋, p₂=y−q₋. Then all power and next-state bounds hold. This rule uses only the current state and request plus precomputed future bounds, and is therefore causal. It covers singleton requests and saturated inequalities. T=0 needs only initial-box membership.

## 6. Cost and evidence

There are O(T) arithmetic operations. Rolling bounds suffice for membership; retain O(T) bounds for policy execution. The recurrence introduces no new denominator beyond those in the rational inputs, but arithmetic complexity must not be confused with a linear bit-cost guarantee.

Implementation: `evidence/n2_exact.py`, using Fraction. Historical validation used 305 cases (five boundary cases and 300 random cases): 30 nonempty, 275 empty, 180 floating-point support comparisons and 207 exactly checked action transitions at endpoints and midpoints. Finite request sampling is supporting evidence; continuous-request validity follows from the proof above.
