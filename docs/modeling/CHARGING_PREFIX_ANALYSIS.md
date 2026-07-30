# Charging Extension: Exactness, Efficiency, and Complementarity

## 1. Scope

This extension remains deliberately small:

- battery only;
- deterministic;
- 3–6 periods in exhaustive tests;
- signed net power \(p_t\in[-P^{ch},P^{dis}]\);
- one isolated upward-reserve call with fixed duration;
- no PV;
- no terminal SOC target beyond ordinary SOC bounds;
- no repeated reserve calls;
- no unit commitment, network, GFM, or stochastic optimization.

Positive \(p_t\) means discharge and negative \(p_t\) means charge.

## 2. Exact complementary physical model

Define the mode-aware energy-depletion function:

\[
\phi(p)
=
\begin{cases}
\dfrac{p}{\eta_d}, & p\ge0,\\[6pt]
\eta_c p, & p<0.
\end{cases}
\]

It is positive during discharge and negative during charge. Complementarity is
implicit: the sign of \(p\) selects exactly one mode.

The base SOC recursion is:

\[
e_{t+1}=e_t-\phi(p_t)\Delta_t.
\]

For an upward reserve call \(r_t\ge0\) lasting \(\tau_t\) at the end of the
interval, the reserve-branch terminal energy is:

\[
e_t^{call}
=
e_t
-\phi(p_t)(\Delta_t-\tau_t)
-\phi(p_t+r_t)\tau_t.
\]

The exact lifted model enforces:

\[
\underline E\le e_{t+1}\le\overline E,
\qquad
\underline E\le e_t^{call}\le\overline E,
\]

\[
-P^{ch}\le p_t\le P^{dis},
\qquad
r_t\ge0,
\qquad
p_t+r_t\le P^{dis}.
\]

## 3. Lossless result: two-sided prefix bounds are exact

When \(\eta_c=\eta_d=1\), \(\phi(p)=p\). Eliminating SOC gives the base
prefix bounds:

\[
E_0-\overline E
\le
\sum_{s=1}^{t}p_s\Delta_s
\le
E_0-\underline E.
\]

The upward-reserve branch adds:

\[
E_0-\overline E
\le
\sum_{s=1}^{t}p_s\Delta_s+r_t\tau_t
\le
E_0-\underline E.
\]

Because \(r_t\ge0\), the reserve branch cannot create overcharge if the base
lower bound already holds, but retaining both sides makes the semantics
explicit.

### Proposition 2

**For the deterministic, lossless, bidirectional Phase-I battery model with
fixed single-call upward-reserve semantics and no terminal coupling beyond SOC
bounds, the two-sided reserve-conditional prefix formulation is the exact
projection of the lifted physical model onto \((p,r)\):**

\[
\boxed{
\mathcal F_{\mathrm{two\text{-}sided\ prefix}}
=
\Pi_{p,r}
\left(
\mathcal F_{\mathrm{full}}^{bidirectional,lossless}
\right).
}
\]

**Proof.** Losslessness gives \(e_{t+1}=e_t-p_t\Delta_t\), so:

\[
e_t
=
E_0-\sum_{s=1}^{t-1}p_s\Delta_s.
\]

Substitution into the base SOC bounds gives the two-sided base prefix bounds.
Substitution into the fixed reserve-call branch gives the
reserve-conditional prefix bounds. This proves that every lifted trajectory
projects into the prefix set. Conversely, for any prefix-feasible \((p,r)\),
construct \(e_t\) using the displayed equality. The prefix inequalities then
verify every base and reserve-branch SOC bound in the lifted model. Thus both
set inclusions hold. \(\square\)

The proposition is restricted to the model in Section 1. It is not a statement
about general bidirectional storage.

The old discharge-only upper prefix is no longer sufficient. If
\(E_0=\overline E=1\), the trajectory \(p_1=-0.5\) passes the upper bound but
attempts to overcharge the battery. The missing information is a lower prefix
bound representing remaining charging headroom.

## 4. Lossy efficiency: the linear net-energy envelope fails

When efficiency is lossy, net MWh and SOC change are no longer identical.
The exact eliminated base bounds become:

\[
E_0-\overline E
\le
\sum_{s=1}^{t}\phi(p_s)\Delta_s
\le
E_0-\underline E.
\]

The exact reserve-conditional expression is:

\[
E_0-\overline E
\le
\sum_{s=1}^{t-1}\phi(p_s)\Delta_s
+\phi(p_t)(\Delta_t-\tau_t)
+\phi(p_t+r_t)\tau_t
\le
E_0-\underline E.
\]

These mode-aware prefix constraints are an exact projection of the stated
physical model. However, they are piecewise linear rather than one linear
envelope in net \(p\).

For \(E_0=0.5\), \(\underline E=0\), \(\overline E=1\), and
\(\eta_c=\eta_d=0.8\):

- \(p_1=0.5\) passes the naive upper net-energy bound, but requires
  \(0.5/0.8=0.625\) MWh and is physically infeasible;
- \(p_1=-0.6\) violates the naive lower net-energy bound \(-0.5\), but adds
  only \(0.8(0.6)=0.48\) MWh and is physically feasible.

Thus the naive two-sided linear net-energy prefix is **neither an inner nor an
outer approximation** of the lossy physical projection.

## 5. Counterexample 1: lossy projection is nonconvex

The reviewer-facing formal statement and relaxation corollaries are given in
[`PROPOSITION_3_NONCONVEXITY.md`](PROPOSITION_3_NONCONVEXITY.md).

Use two active periods, embedded in the 3-period implementation with a zero
third period:

\[
E_0=0.5,\quad
\underline E=0,\quad
\overline E=1,\quad
P^{ch}=P^{dis}=1,\quad
\eta_c=\eta_d=0.8.
\]

Consider:

\[
p^A=(-0.6,\ 0,\ 0),
\]

\[
p^B=(0.2,\ -0.9,\ 0).
\]

Both are physically feasible:

- \(p^A\) produces SOC path \(0.5\rightarrow0.98\rightarrow0.98\);
- \(p^B\) produces SOC path
  \(0.5\rightarrow0.25\rightarrow0.97\).

Their midpoint is:

\[
\bar p
=
\frac{p^A+p^B}{2}
=
(-0.2,\ -0.45,\ 0).
\]

Under physical complementarity:

\[
0.5
\rightarrow
0.5+0.8(0.2)=0.66
\rightarrow
0.66+0.8(0.45)=1.02,
\]

so \(\bar p\) is infeasible. The exact net-injection projection is therefore
nonconvex.

This is already a two-period counterexample; the implementation embeds it in a
3-period trajectory by appending a zero third period so that it remains inside
the declared 3–6 period experiment range.

## 6. Why the convex relaxation is not exact

Write net power as:

\[
p_t=d_t-c_t,
\qquad
c_t,d_t\ge0.
\]

Replace complementarity by the converter convex-hull constraint:

\[
\frac{c_t}{P^{ch}}+\frac{d_t}{P^{dis}}\le1.
\]

The midpoint of the lifted witnesses above is:

\[
c=(0.3,\ 0.45,\ 0),
\qquad
d=(0.1,\ 0,\ 0).
\]

It projects to \(\bar p=(-0.2,-0.45,0)\) and produces the relaxed SOC path:

\[
0.5
\rightarrow
0.5+0.8(0.3)-0.1/0.8
=0.615
\rightarrow
0.975.
\]

The relaxation is feasible because simultaneous charging and discharging
dissipates energy and creates artificial charging headroom. The physically
complementary trajectory with the same net injections is infeasible.

Consequently:

\[
\Pi_p
\left(
\mathcal F_{\mathrm{full}}^{complementary}
\right)
\subsetneq
\Pi_p
\left(
\mathcal F_{\mathrm{convex\ relaxation}}
\right)
\]

in general when efficiency is lossy and the upper SOC bound matters.

In the lossless case, \(e_{t+1}=e_t+c_t-d_t=e_t-p_t\), so simultaneous
charge/discharge does not change SOC beyond net power. The convex relaxation
and complementary model then have the same net-power projection for this
restricted model.

## 7. Missing information structure

The charging extension identifies three additional information requirements:

1. **Charging headroom:** an upper SOC limit appears as a lower prefix bound.
2. **Direction-aware energy conversion:** with losses, net power alone cannot
   be converted to SOC change by one linear coefficient across both modes.
3. **Mode/complementarity information:** an exact lifted linear formulation
   needs charge/discharge variables plus a mode indicator, SOS1 constraint, or
   equivalent disjunctive representation.

This produces the first genuine fork:

- **Lossless bidirectional model:** a compact continuous two-sided prefix
  polytope is exact.
- **Lossy complementary model:** the mode-aware prefix description is exact
  but piecewise linear and generally nonconvex.
- **Lossy convex relaxation:** compact and continuous, but can admit artificial
  cycling and is only an outer approximation in net-injection space.
- **Conservative convex contract:** possible, but it must be deliberately
  constructed as a safe inner approximation rather than called exact.

## 8. Exact 3–6 period enumeration

The implementation enumerates rational-grid \((p,r)\) trajectories and checks
the prefix and full-state formulations independently.

For the lossless case
\((E_0,\underline E,\overline E,P^{ch},P^{dis})=(1,0,2,1,1)\), with a
1 MW grid:

| Horizon | Upper only | Two-sided linear | Mode-aware | Full |
|---:|---:|---:|---:|---:|
| 3 | 189 | 99 | 99 | 99 |
| 4 | 1,098 | 405 | 405 | 405 |
| 5 | 6,444 | 1,656 | 1,656 | 1,656 |
| 6 | 38,052 | 6,768 | 6,768 | 6,768 |

For the lossy case
\((E_0,\underline E,\overline E,P^{ch},P^{dis},\eta_c,\eta_d)
=(3,0,5,1,1,0.8,0.8)\):

| Horizon | Upper only | Naive two-sided linear | Mode-aware | Full |
|---:|---:|---:|---:|---:|
| 3 | 216 | 189 | 186 | 186 |
| 4 | 1,293 | 969 | 939 | 939 |
| 5 | 7,737 | 4,902 | 4,911 | 4,911 |
| 6 | 46,296 | 24,696 | 26,019 | 26,019 |

The naive lossy linear count may be either above or below the exact count
because that formulation is neither an inner nor an outer approximation.
The mode-aware and independently replayed full sets agree at every tested
horizon.

## 9. What remains deferred

This result does not include:

- terminal SOC targets;
- deterministic PV or curtailment;
- stochastic renewable availability;
- repeated or correlated reserve calls;
- degradation, self-discharge, ramp-memory, or state-dependent efficiency.

Terminal SOC is the next separate extension. It should not be folded into the
present exactness claim.
