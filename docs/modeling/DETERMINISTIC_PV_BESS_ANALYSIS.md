# Deterministic PV+BESS Extension

## 1. Scope and notation

This extension keeps one deterministic PV+BESS resource, a 3–6 period
horizon, fixed-duration isolated reserve calls, exact rational-grid
enumeration, and independent physical replay. It adds no uncertainty, unit
commitment, network, GFM, or frequency dynamics.

Let:

\[
g_t=w_t-q_t,\qquad 0\le g_t\le w_t
\]

denote delivered PV, and let complementary battery net power be

\[
b_t=d_t-c_t,\qquad c_td_t=0.
\]

Hybrid net injection is:

\[
h_t=g_t+b_t.
\]

For lossy operation define battery energy depletion:

\[
\phi(b)=
\begin{cases}
b/\eta_d,&b\ge0,\\
\eta_c b,&b<0.
\end{cases}
\]

Thus \(e_{t+1}=e_t-\phi(b_t)\Delta_t\).

## 2. Stage A: must-take deterministic PV

With no curtailment:

\[
h_t=w_t+b_t.
\]

### Proposition 6 — Affine translation exactness for must-take PV

**For a fixed operator-visible deterministic PV trajectory \(w\), the exact
hybrid net-injection projection under must-take PV is the affine translation
of the corresponding battery-only projection:**

\[
\boxed{
\mathcal H_A^{exact}=w+\mathcal B^{exact}.
}
\]

The same translation preserves exact, inner, and outer relations. In
particular, if

\[
\mathcal B^{inner}\subseteq
\mathcal B^{exact}\subseteq
\mathcal B^{outer},
\]

then:

\[
w+\mathcal B^{inner}\subseteq
\mathcal H_A^{exact}\subseteq
w+\mathcal B^{outer}.
\]

**Proof.** The map \(b\mapsto h=w+b\) is an affine bijection when \(w\) is
fixed. A hybrid trajectory has a feasible physical realization if and only if
the translated battery trajectory \(b=h-w\) has one. Affine translation
preserves equality and set inclusion. \(\square\)

This stage creates no new geometry. It does create a contract-versioning
requirement: either \(w\) must be visible to the operator, or the contract
must identify the deterministic PV trajectory against which its limits were
constructed. A contract that silently changes \(w\) changes its feasible set.

## 3. Stage B: deterministic PV with curtailment

For fixed \(h_t\), delivered PV can vary over \([0,w_t]\). Therefore feasible
battery net power lies in:

\[
\boxed{
a_t(h_t)\le b_t\le z_t(h_t)
}
\]

where:

\[
a_t(h_t)=\max\{-P^{ch},h_t-w_t\},
\qquad
z_t(h_t)=\min\{P^{dis},h_t\}.
\tag{B1}
\]

The interval is empty if \(a_t>z_t\).

### Proposition 7 — Exact reachable-interval projection

Let \([\ell_t,u_t]\) be the set of SOC values reachable before period \(t\),
starting with:

\[
[\ell_1,u_1]=[E_0,E_0].
\]

For a proposed hybrid injection \(h_t\), define:

\[
\ell_{t+1}
=
\max\left\{
\underline E,\,
\ell_t-\phi(z_t(h_t))\Delta_t
\right\},
\tag{B2}
\]

\[
u_{t+1}
=
\min\left\{
\overline E,\,
u_t-\phi(a_t(h_t))\Delta_t
\right\}.
\tag{B3}
\]

**The curtailed-PV hybrid trajectory \(h\) is physically feasible if and only
if (B1) is nonempty and \(\ell_t\le u_t\) at every step.**

**Proof.** The complementary signed battery power \(b_t\) continuously spans
the interval in (B1). The depletion map \(\phi\) is continuous and strictly
increasing, so its image is
\([\phi(a_t),\phi(z_t)]\). The image of the reachable SOC interval under
\(e_{t+1}=e_t-\phi(b_t)\Delta_t\) is therefore exactly the interval before
intersection in (B2)–(B3). Intersecting with the SOC bounds is exact.
Induction over \(t\) proves necessity and sufficiency. \(\square\)

This result is important but should not be misread: net injection determines
a **reachable SOC interval**, not a unique SOC trajectory.

### Corollary 7.1 — Convexity in the lossless case

When \(\eta_c=\eta_d=1\), the physical model in lifted variables
\((h,g,b,e)\) is linear. Hence:

\[
\mathcal H_{B,\mathrm{lossless}}^{physical}
=
\Pi_h(\mathcal F_{B,\mathrm{lossless}})
\]

is a convex polytope. Equations (B1)–(B3) give an exact piecewise-linear
membership recursion. The continuous charge/discharge relaxation has the
same net-injection projection:

\[
\boxed{
\mathcal H_{B,\mathrm{lossless}}^{physical}
=
\mathcal H_{B,\mathrm{lossless}}^{relaxed}.
}
\]

Simultaneous charge and discharge changes no lossless SOC result that cannot
be reproduced by the same complementary net battery power.

### Proposition 8 — Nonconvexity survives deterministic curtailment

**Under lossy bidirectional battery operation with charge/discharge
complementarity, the exact curtailed-PV hybrid net-injection projection need
not be convex.**

Take two periods, or append a zero third period, with:

\[
E_0=\tfrac12,\quad
[\underline E,\overline E]=[0,1],\quad
P^{ch}=P^{dis}=1,\quad
\eta_c=\eta_d=\tfrac45,\quad
w=(\tfrac15,\tfrac15).
\]

Consider:

\[
h^A=(-\tfrac35,0),
\qquad
h^B=(\tfrac15,-\tfrac9{10}).
\]

Both are feasible by fully curtailing PV:

- \(h^A\) charges \(3/5\), ending at \(0.98\);
- \(h^B\) discharges \(1/5\) and then charges \(9/10\), with SOC
  \(0.50\to0.25\to0.97\).

Their midpoint is:

\[
\bar h=(-\tfrac15,-\tfrac9{20}).
\]

Because both components are negative, any delivered PV would require still
more battery charging. Full curtailment therefore minimizes SOC gain, yet:

\[
e_3
\ge
\tfrac12+\tfrac45
\left(\tfrac15+\tfrac9{20}\right)
=1.02>1.
\]

Thus \(\bar h\) is infeasible and the projection is nonconvex. \(\square\)

### Corollary 8.1 — The continuous relaxation is a strict outer set

For the same midpoint, use \(g=(0,0)\) and:

\[
c=(0.30,0.45),\qquad d=(0.10,0).
\]

This satisfies the converter convex hull and produces
\(\bar h=(-0.20,-0.45)\). Its SOC path is:

\[
0.50\to0.615\to0.975.
\]

Therefore:

\[
\boxed{
\mathcal H_{B,\mathrm{lossy}}^{physical}
\subsetneq
\mathcal H_{B,\mathrm{lossy}}^{relaxed}
}
\]

in general.

The must-take translated contract remains a safe but generally strict inner
set because \(q=0\) is one allowed curtailed-PV realization:

\[
\mathcal H_A^{exact}
\subseteq
\mathcal H_B^{physical}.
\]

### Proposition 9 — Net injection does not identify hybrid state

Let \(E_0=0\), \(w_1=1\), and \(h_1=0\). Two feasible internal actions are:

1. curtail all PV and leave the battery idle;
2. deliver 1 MW of PV and charge the battery at 1 MW.

Both expose the same hybrid injection \(h_1=0\), but their next SOC values are
\(0\) and \(\eta_c\), respectively.

**Hence a curtailed-PV net-injection trajectory is not a sufficient statistic
for the internal SOC trajectory.** Its exact continuation state is generally
set-valued. This is the first structural difference from must-take PV and
from the signed battery-only model.

## 4. Stage C: isolated upward and downward reserve branches

For one common base decomposition
\((g_t,c_t,d_t)\), define separate branch actions
\((g_t^+,c_t^+,d_t^+)\) and
\((g_t^-,c_t^-,d_t^-)\) satisfying:

\[
g_t^+ + d_t^+ - c_t^+ = h_t+r_t^+,
\]

\[
g_t^- + d_t^- - c_t^- = h_t-r_t^-.
\]

Under the existing end-of-interval, fixed-duration, single-call semantics:

\[
e_{t,+}^{call}
=e_t+s_t(\Delta_t-\tau)+s_t^+\tau,
\]

\[
e_{t,-}^{call}
=e_t+s_t(\Delta_t-\tau)+s_t^-\tau,
\]

where:

\[
s=\eta_c c-d/\eta_d.
\]

Both branch endpoints must satisfy SOC bounds. Calls do not alter the later
base SOC trajectory.

### Proposition 10 — Reserve-source non-identifiability

**Scheduled hybrid injection and aggregate reserve quantities do not, in
general, identify the reserve-induced SOC transition.**

For upward reserve, let \(w=1\), \(E_0=1\), \(h=0\), \(r^+=1\), and use an
idle, fully curtailed base point. The call can be supplied by:

- releasing 1 MW of curtailed PV, ending at SOC \(1\); or
- discharging the battery by 1 MW, ending at SOC \(0\).

Both expose the same \((h,r^+)=(0,1)\).

For downward reserve, start from delivered PV \(g=1\), battery idle,
\((h,r^-)=(1,1)\). The call can be supplied by:

- curtailing 1 MW of PV, leaving SOC unchanged; or
- charging the battery by 1 MW, increasing SOC by 1 MWh.

Thus the external reserve award does not reveal whether flexibility came from
curtailment headroom, charging reduction/increase, or stored energy.
\(\square\)

### Interpretation: what aggregate reserve is and is not sufficient for

Under the deliberately narrow **isolated-call, resource-controlled**
semantics, aggregate \((h,r^+,r^-)\) remains sufficient as coordinates for an
existential feasibility set:

\[
\mathcal C_C^{exact}
=
\Pi_{h,r^+,r^-}
\left(
\mathcal F_C^{source\text{-}lifted}
\right).
\]

The implementation tests this projection by enumerating a common base
decomposition and both branch decompositions, then independently replaying
their SOC paths.

However, aggregate quantities are not sufficient for:

- determining activated SOC;
- updating future capability after an observed call;
- enforcing source-specific reserve products;
- composing repeated calls without additional state.

An exact sequential contract must therefore expose at least one of:

- source allocation or mode information;
- an activation-conditioned SOC/state interval;
- lifted internal variables;
- a conservative worst-case energy envelope.

This is an information insufficiency result, not a claim that the isolated
existential projection cannot be written.

### Exact, inner, and outer relations

Let \(\mathcal C_C^{physical}\) use complementary source actions and let
\(\mathcal C_C^{relaxed}\) allow simultaneous battery charge/discharge:

\[
\mathcal C_C^{physical}
\subseteq
\mathcal C_C^{relaxed}.
\]

The inclusion is strict in general because the zero-reserve face contains the
strict Stage-B relaxation example:

\[
\boxed{
\mathcal C_C^{physical}
\subsetneq
\mathcal C_C^{relaxed}.
}
\]

A contract that fixes admissible reserve sources, such as PV-release-only
upward reserve, is a source-labelled inner set:

\[
\mathcal C_C^{source\text{-}restricted}
\subseteq
\mathcal C_C^{physical}.
\]

A continuous convex aggregate contract can use the relaxed projection as an
outer approximation or choose a conservative convex inner approximation. It
cannot equal a generally nonconvex exact projection without lifted/discrete
information or conservatism.

## 5. Exact 3–6 period enumeration and replay

All counts below are exact on the stated rational grids. Every retained
external point has an explicit internal witness that is checked by the
independent replay code.

### Stages A and B

Use \(w_t=1\), \(P^{ch}=P^{dis}=1\), and a 1 MW grid.

- Stage A and lossless Stage B:
  \(E_0=1\), \([\underline E,\overline E]=[0,2]\).
- Lossy Stage B:
  \(E_0=2\), \([\underline E,\overline E]=[0,4]\),
  \(\eta_c=\eta_d=1/2\).

| Horizon | Stage A must-take | Stage B lossless | Stage B lossy |
|---:|---:|---:|---:|
| 3 | 17 | 52 | 54 |
| 4 | 41 | 194 | 189 |
| 5 | 99 | 730 | 647 |
| 6 | 239 | 2,756 | 2,258 |

For both Stage-B columns, the explicit internal-action projection equals the
independent reachable-interval membership result on the full external grid
\(h_t\in\{-1,0,1,2\}\).

### Stage C

Use \(E_0=1/2\), \([\underline E,\overline E]=[0,1]\),
\(w_t=P^{ch}=P^{dis}=1\), lossless operation, and:

\[
h_t\in\{0,1\},\qquad r_t^\pm\in\{0,1\}.
\]

Upward and downward products are enumerated separately, with a zero branch in
the opposite direction.

| Horizon | Candidate \((h,r)\) points | Feasible upward | Feasible downward |
|---:|---:|---:|---:|
| 3 | 64 | 27 | 27 |
| 4 | 256 | 81 | 81 |
| 5 | 1,024 | 243 | 243 |
| 6 | 4,096 | 729 | 729 |

The test suite also directly verifies the two upward-source witnesses and the
two downward-source witnesses in Proposition 10.

## 6. What this establishes

Stage A is only an affine translation of battery capability.

Stage B is the first genuine hybrid-resource result:

- curtailment makes the internal state transition hidden and set-valued;
- the lossless exact projection remains a compact convex polytope;
- lossy complementarity can retain nonconvexity;
- the continuous relaxation is a strict outer approximation.

Stage C adds a second information loss:

- aggregate reserve quantity does not identify its physical source or energy
  consequence;
- exact isolated-call feasibility is still available through a lifted
  projection;
- stateful or repeated-call use requires more contract information.

These claims remain restricted to deterministic, single-resource, small-
horizon PV+BESS operation.
