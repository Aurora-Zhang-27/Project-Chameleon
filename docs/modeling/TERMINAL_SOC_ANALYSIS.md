# Terminal SOC Extension

## 1. Semantics and scope

Add the base-schedule terminal requirement:

\[
e_{T+1}\ge E^{term}.
\]

The target applies to the scheduled base trajectory. Existing upward-reserve
awards remain isolated single-call capability tests from that base trajectory;
they do not modify later base SOC. Requiring recovery to \(E^{term}\) after a
reserve activation would define a stronger recovery contract and is not
silently assumed here.

The model remains deterministic, battery-only, and 3–6 periods. No PV,
uncertainty, unit commitment, network, GFM, or frequency dynamics is added.

## 2. Case 1: discharge-only lossless operation

For:

\[
e_{t+1}=e_t-p_t\Delta_t,
\qquad p_t\ge0,
\]

the terminal condition is equivalent to:

\[
\boxed{
\sum_{t=1}^{T}p_t\Delta_t
\le
E_0-E^{term}
}.
\tag{T1}
\]

The previous prefix contract alone is no longer exact for the terminal model.
For example:

\[
E_0=1,\quad E^{term}=0.5,\quad p=(1,0,0)
\]

satisfies the old physical SOC bounds but ends at zero. This is the smallest
failure mechanism; it is embedded in three periods for the experiment.

The exact terminal projection is:

\[
\mathcal F_{\mathrm{old\ prefix}}
\cap
\left\{
p:
\sum_t p_t\Delta_t\le E_0-E^{term}
\right\}.
\]

It is not correct to replace every reserve-delivery budget by
\(E_0-E^{term}\) under the chosen semantics: isolated reserve calls are tested
against physical SOC bounds, while the terminal target constrains the base
schedule.

## 3. Case 2: bidirectional lossless operation

With signed \(p_t\in[-P^{ch},P^{dis}]\) and lossless dynamics:

\[
e_{t+1}=e_t-p_t\Delta_t,
\]

the existing two-sided prefix formulation remains exact after adding the same
linear terminal cut (T1).

### Proposition 4

**For the deterministic lossless bidirectional Phase-I model, the exact
terminal-energy projection equals the two-sided reserve-conditional prefix
set intersected with the linear terminal cut (T1).**

**Proof.** Proposition 2 gives exactness of the two-sided prefix set for all
base and isolated reserve-branch SOC bounds. Eliminating \(e_{T+1}\) from the
lossless state recursion gives (T1). Conversely, constructing the SOC path
from the signed prefix sums verifies both the original lifted constraints and
the terminal target. \(\square\)

Thus terminal SOC is an additional contract field or cut, but it does not
destroy the compact-polytope result in the lossless model.

## 4. Case 3: bidirectional lossy operation with complementarity

Define:

\[
\phi(p)
=
\begin{cases}
p/\eta_d,&p\ge0,\\
\eta_c p,&p<0.
\end{cases}
\]

The exact terminal cut becomes:

\[
\boxed{
\sum_{t=1}^{T}\phi(p_t)\Delta_t
\le
E_0-E^{term}
}.
\tag{T2}
\]

### Proposition 5

**For the deterministic lossy bidirectional Phase-I model with mutually
exclusive charging and discharging, the exact terminal projection equals the
mode-aware prefix set intersected with (T2).**

The proof is direct elimination of:

\[
e_{T+1}
=
E_0-\sum_t\phi(p_t)\Delta_t.
\]

The formulation remains piecewise linear and generally nonconvex. Terminal
SOC does not restore convexity. In Proposition 3's counterexample, choose:

\[
E^{term}=0.95.
\]

The two endpoint trajectories finish at \(0.98\) and \(0.97\), so both meet
the terminal target. Their midpoint still violates the upper SOC bound at
\(1.02\). Therefore the terminal-constrained exact projection remains
nonconvex.

Terminal SOC is absorbable into the mode-aware prefix representation as one
additional direction-dependent cut. It is not absorbable into the naive
lossless net-energy sum without losing exactness.

## 5. Case 4: continuous relaxation without complementarity

The split-variable relaxation uses:

\[
p_t=d_t-c_t,
\qquad
c_t,d_t\ge0,
\]

\[
\frac{c_t}{P^{ch}}+\frac{d_t}{P^{dis}}\le1,
\]

with linear SOC dynamics:

\[
e_{t+1}
=
e_t+\eta_c c_t\Delta_t
-\frac{d_t}{\eta_d}\Delta_t.
\]

The terminal target adds the linear constraint
\(e_{T+1}\ge E^{term}\). The relaxation is still an outer approximation:

\[
\Pi_p(\mathcal F_{\mathrm{physical}}^{term})
\subseteq
\Pi_p(\mathcal F_{\mathrm{relaxed}}^{term}).
\]

The inclusion remains strict for the Proposition 3 midpoint with
\(E^{term}=0.95\):

- physical midpoint: infeasible because SOC reaches \(1.02\);
- relaxed midpoint: feasible with terminal SOC \(0.975\).

In the lossless restricted model, the relaxed and complementary projections
continue to coincide after the terminal cut because SOC depends only on net
power.

## 6. Exact, inner, and outer relations

### Lossless models

\[
\mathcal F_{\mathrm{full}}^{term}
=
\mathcal F_{\mathrm{prefix}}^{lossless}
\cap H_{term},
\]

where \(H_{term}\) is the linear half-space (T1). This is exact and convex.

### Lossy complementary model

\[
\mathcal F_{\mathrm{full}}^{term}
=
\mathcal F_{\mathrm{prefix}}^{mode-aware}
\cap H_{term}^{mode-aware}.
\]

This is exact, piecewise linear, and generally nonconvex.

### Lossy continuous relaxation

\[
\mathcal F_{\mathrm{full}}^{term}
\subsetneq
\mathcal F_{\mathrm{relaxed}}^{term}
\]

in general. The relaxation is an outer approximation and is not
contract-exact.

A safe continuous convex contract would need to choose:

\[
\mathcal F_{\mathrm{inner}}^{term}
\subseteq
\mathcal F_{\mathrm{full}}^{term},
\]

accepting conservatism. It cannot equal a nonconvex exact projection while
remaining a convex set solely in net-injection variables.

## 7. Exact 3–6 period enumeration

The implementation enumerates a common rational-grid superset, then evaluates
the terminal prefix and independent SOC replay predicates separately.

### Discharge-only lossless

Parameters:
\((E_0,\underline E,\overline E,E^{term},P^{dis})
=(1,0,1,0.5,1)\), using a 0.5 MW grid.

| Horizon | Prefix + terminal cut | Full terminal replay |
|---:|---:|---:|
| 3 | 65 | 65 |
| 4 | 211 | 211 |
| 5 | 665 | 665 |
| 6 | 2,059 | 2,059 |

### Bidirectional lossless

Parameters:
\((E_0,\underline E,\overline E,E^{term},P^{ch},P^{dis})
=(1,0,2,1,1,1)\), using a 1 MW grid.

| Horizon | Two-sided prefix + terminal cut | Full terminal replay |
|---:|---:|---:|
| 3 | 87 | 87 |
| 4 | 357 | 357 |
| 5 | 1,461 | 1,461 |
| 6 | 5,973 | 5,973 |

For zero-reserve net-power trajectories, the lossless complementary and
continuous relaxed terminal projections also agree:

| Horizon | Complementary projection | Relaxed projection |
|---:|---:|---:|
| 3 | 12 | 12 |
| 4 | 29 | 29 |
| 5 | 70 | 70 |
| 6 | 169 | 169 |

### Bidirectional lossy

Parameters:
\((E_0,\underline E,\overline E,E^{term},P^{ch},P^{dis},\eta_c,\eta_d)
=(3,0,5,2,1,1,0.8,0.8)\), using a 1 MW grid.

| Horizon | Mode-aware prefix + terminal cut | Full terminal replay |
|---:|---:|---:|
| 3 | 161 | 161 |
| 4 | 820 | 820 |
| 5 | 4,343 | 4,343 |
| 6 | 23,065 | 23,065 |

These finite enumerations are regression evidence. Continuous exactness in
the lossless and mode-aware cases follows from the analytical elimination in
Propositions 4 and 5.

## 8. Information interpretation

Terminal SOC is a future obligation. In the current models:

- discharge-only lossless: one scalar terminal budget is sufficient;
- bidirectional lossless: the same scalar cut augments the two-sided prefix;
- bidirectional lossy: the obligation is still one cut, but evaluating it
  requires direction-aware mode information;
- relaxed lossy: the same apparent terminal value can be achieved through
  artificial cycling, so terminal SOC alone does not repair the missing
  complementarity information.

Thus \(E^{term}\) is an additional contract field, while its enforceability
depends on the energy-conversion and mode semantics already present in the
contract.

## 9. What remains deferred

This analysis does not include:

- terminal recovery after reserve activation;
- terminal equality or terminal penalties;
- deterministic PV and curtailment;
- uncertainty or chance constraints;
- repeated reserve calls;
- degradation or state-dependent efficiency.

Deterministic PV remains the next structural extension after review of this
terminal result.
