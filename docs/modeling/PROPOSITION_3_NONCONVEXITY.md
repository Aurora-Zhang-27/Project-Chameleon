# Proposition 3: Nonconvexity Under Lossy Bidirectional Operation

## Proposition 3

**Nonconvexity of the exact net-injection projection under lossy
bidirectional operation.**

Consider the deterministic bidirectional battery model with:

\[
0<\eta_c<1,
\qquad
0<\eta_d<1,
\]

finite lower and upper SOC bounds, and mutually exclusive charging and
discharging. Then the projection of the physical feasible set onto
net-injection trajectories need not be convex.

The statement is existential and model-class specific: it says
**need not be convex**, not that every lossy battery instance has a nonconvex
projection.

## Proof by counterexample

Use two active periods and append a zero third period to stay inside the
3–6-period experiment range. Let:

\[
E_0=0.5,
\quad
\underline E=0,
\quad
\overline E=1,
\quad
P^{ch}=P^{dis}=1,
\quad
\eta_c=\eta_d=0.8.
\]

Positive net injection denotes discharge and negative net injection denotes
charge. Consider:

\[
p^A=(-0.6,\ 0,\ 0).
\]

Its SOC trajectory is:

\[
0.5
\rightarrow
0.5+0.8(0.6)
=0.98
\rightarrow0.98
\rightarrow0.98.
\]

Thus \(p^A\) is physically feasible.

Now consider:

\[
p^B=(0.2,\ -0.9,\ 0).
\]

Its SOC trajectory is:

\[
0.5
\rightarrow
0.5-\frac{0.2}{0.8}
=0.25
\rightarrow
0.25+0.8(0.9)
=0.97
\rightarrow0.97.
\]

Thus \(p^B\) is physically feasible.

Their midpoint is:

\[
\bar p
=
\frac{p^A+p^B}{2}
=
(-0.2,\ -0.45,\ 0).
\]

Under physical charge/discharge complementarity, its SOC trajectory is:

\[
0.5
\rightarrow
0.5+0.8(0.2)
=0.66
\rightarrow
0.66+0.8(0.45)
=1.02.
\]

The midpoint violates \(\overline E=1\), so:

\[
p^A,p^B
\in
\Pi_p(\mathcal F_{\mathrm{physical}}),
\qquad
\frac{p^A+p^B}{2}
\notin
\Pi_p(\mathcal F_{\mathrm{physical}}).
\]

Therefore the exact net-injection projection need not be convex.
\(\square\)

## Corollary 3.1: no exact convex net-injection-only contract in general

For this model class, no contract whose feasible region is a continuous convex
set solely in net-injection space can be both exact and complete in general.

This follows immediately because a convex set containing both \(p^A\) and
\(p^B\) must contain their midpoint, while the exact physical projection does
not.

The careful implication is:

- an exact formulation generally must retain nonconvex mode structure,
  commonly through lifted charge/discharge variables with complementarity,
  discrete mode information, SOS1 constraints, or an equivalent disjunction;
- a continuous convex net-injection contract must generally accept either a
  conservative inner approximation or an unsafe outer approximation.

Additional continuous lifted variables with only convex constraints cannot by
themselves produce an exact nonconvex projection, because projections of
convex sets are convex.

## Corollary 3.2: simultaneous charge/discharge relaxation is not contract-exact

Removing charge/discharge complementarity can strictly enlarge the projected
feasible set:

\[
\Pi_p(\mathcal F_{\mathrm{physical}})
\subsetneq
\Pi_p(\mathcal F_{\mathrm{relaxed}})
\]

for this model class.

For the midpoint above, take the relaxed split variables:

\[
c=(0.3,\ 0.45,\ 0),
\qquad
d=(0.1,\ 0,\ 0).
\]

They satisfy:

\[
\bar p=d-c=(-0.2,-0.45,0)
\]

and the converter convex-hull constraint:

\[
\frac{c_t}{P^{ch}}+\frac{d_t}{P^{dis}}\le1.
\]

Their relaxed SOC trajectory is:

\[
0.5
\rightarrow
0.5+0.8(0.3)-\frac{0.1}{0.8}
=0.615
\rightarrow
0.615+0.8(0.45)
=0.975.
\]

The relaxed trajectory is feasible even though the complementary physical
trajectory with the same net injections reaches \(1.02\). Simultaneous
charging and discharging dissipates energy and creates artificial SOC
headroom. Hence the inclusion is strict.

This corollary does not claim strictness for every parameterization. In the
restricted lossless model, simultaneous charge/discharge does not change SOC
beyond net power, and the relaxed and complementary net projections can
coincide.

