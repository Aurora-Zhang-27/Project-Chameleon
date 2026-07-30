# Exact Small-Model Derivation

## 1. Scope

This note covers a lossless, discharge-only battery over \(T\in\{2,\ldots,6\}\)
periods. It contains no PV, charging, uncertainty, unit commitment, network,
GFM, or dynamic-frequency model.

Let:

- \(p_t\ge0\): scheduled battery injection in MW;
- \(r_t\ge0\): upward reserve award in MW;
- \(P\): inverter power limit in MW;
- \(E_0\): initial usable energy in MWh;
- \(\Delta\): interval duration in hours;
- \(\tau\le\Delta\): reserve sustain duration in hours;
- \(e_t\): energy at the start of period \(t\).

The reserve product is one isolated full call at the end of a period. Repeated
activation is not claimed.

## 2. Lifted full physical set

The deterministic lifted formulation is:

\[
e_1=E_0,
\]

\[
e_{t+1}=e_t-p_t\Delta,
\]

\[
0\le p_t,\quad 0\le r_t,\quad p_t+r_t\le P,
\]

\[
p_t\Delta+r_t\tau\le e_t
\qquad t=1,\ldots,T.
\]

The final inequality says that the base schedule can run for the interval and
the reserve increment can be sustained for \(\tau\).

This is \(C_{\mathrm{full}}^{\mathrm{det}}\) in lifted form.

## 3. Elimination of SOC

The formal statement, assumptions, and proof are given in
[`PROPOSITION_PREFIX_EXACTNESS.md`](PROPOSITION_PREFIX_EXACTNESS.md) as
Proposition 1. The equality below is restricted to that Phase-I
discharge-only model.

Recursively substituting the state equation gives:

\[
e_t
=
E_0-\sum_{s=1}^{t-1}p_s\Delta.
\]

Substitution into reserve deliverability yields:

\[
\sum_{s=1}^{t}p_s\Delta+r_t\tau\le E_0
\qquad t=1,\ldots,T.
\]

Together with nonnegativity and \(p_t+r_t\le P\), these are precisely the
prefix inequalities used by \(C_1^{prefix}\). Therefore, for this restricted
continuous model:

\[
C_1^{prefix}
=
\operatorname{proj}_{p,r}
\left(C_{\mathrm{full}}^{\mathrm{det}}\right).
\]

The implementations remain independent:

- `prefix_feasible` evaluates the eliminated prefix inequalities;
- `full_projected_feasible` recursively replays the state;
- the full operator LP contains explicit SOC variables and equalities.

Their equality is tested for 3–6 periods on an exact rational grid.

## 4. Exact time-local marginal

Project the full set onto \((p_t,r_t)\). Necessity gives:

\[
p_t\ge0,\quad r_t\ge0,\quad p_t+r_t\le P,
\]

\[
p_t\Delta+r_t\tau\le E_0.
\]

These conditions are also sufficient for the projection: set every other
\(p_s,r_s\) to zero. The selected pair then has a valid full-horizon witness.

Hence:

\[
\mathcal K_t
=
\left\{
(p_t,r_t):
p_t,r_t\ge0,\;
p_t+r_t\le P,\;
p_t\Delta+r_t\tau\le E_0
\right\}.
\]

The strongest fair time-separable baseline is:

\[
C_0^{exact\text{-}marginal}
=
\prod_{t=1}^{T}\mathcal K_t.
\]

Every local slice has a complete physical witness, but different slices may
require incompatible witnesses.

## 5. Inclusion and strictness

For all valid parameters:

\[
C_1^{prefix}
=
\operatorname{proj}_{p,r}
\left(C_{\mathrm{full}}^{\mathrm{det}}\right)
\subseteq
C_0^{exact\text{-}marginal}.
\]

The inclusion is strict whenever energy can couple two nonzero requests. For
\(T\ge2\), \(P=E_0=\Delta=\tau=1\), use:

\[
p_1=1,\qquad r_T=1,
\]

with all other variables zero. Each local pair lies in its exact marginal,
but the last prefix inequality reads:

\[
p_1+r_T=2>1.
\]

Thus the trajectory is in \(C_0^{exact\text{-}marginal}\) but outside both
\(C_1^{prefix}\) and \(C_{\mathrm{full}}^{\mathrm{det}}\).

## 6. Gap-disappearance regime

If energy is nonbinding over the entire horizon, the prefix inequalities add
nothing. A sufficient condition is:

\[
E_0\ge TP\Delta
\qquad\text{when}\qquad \tau\le\Delta.
\]

Indeed, local power limits imply:

\[
\sum_{s=1}^{t}p_s\Delta+r_t\tau
\le tP\Delta
\le TP\Delta
\le E_0.
\]

Therefore:

\[
C_0^{exact\text{-}marginal}
=C_1^{prefix}
=\operatorname{proj}_{p,r}
\left(C_{\mathrm{full}}^{\mathrm{det}}\right).
\]

This is the required case in which the abstraction gap disappears without
changing costs, penalties, or the physical model.

## 7. Information content versus feasible-set inclusion

The notation \(C_a\preceq C_b\) should mean that \(C_b\) communicates at least
the distinctions needed to enforce every constraint communicated by \(C_a\),
and possibly additional cross-time distinctions. It is an **information
preorder**, not the statement \(C_a\subseteq C_b\).

In this model:

\[
C_0^{exact\text{-}marginal}
\preceq
C_1^{prefix}
\preceq
C_{\mathrm{full}}^{\mathrm{det}}.
\]

Yet the admitted schedule sets satisfy the reverse-looking relation:

\[
\operatorname{proj}_{p,r}
\left(C_{\mathrm{full}}^{\mathrm{det}}\right)
=C_1^{prefix}
\subseteq
C_0^{exact\text{-}marginal}.
\]

More information removes spurious schedules. It need not enlarge the
operator-visible feasible set.

In the present pure-battery model, \(C_1^{prefix}\) and the projection of
\(C_{\mathrm{full}}^{\mathrm{det}}\) admit exactly the same \((p,r)\)
trajectories. They still differ as messages:

- \(C_1^{prefix}\) reveals only \(P,E_0,\Delta,\tau\) through interpretable
  inequalities;
- \(C_{\mathrm{full}}^{\mathrm{det}}\) exposes an internal state variable and
  its transition equation.

Thus equality of induced feasible sets for one task does not imply identical
information disclosure. Conversely, if two messages induce the same feasible
set for every operator decision problem in the declared model class, they are
operationally equivalent for that class even if their syntax differs.

The relation may be a preorder rather than a partial order until messages that
are operationally equivalent are quotiented into equivalence classes.

## 8. Exact computational checks

The test suite performs four complementary checks:

1. SciPy/HiGHS solves the two-period LP under all three contracts.
2. `replay_base_and_single_calls` recomputes SOC and reserve delivery outside
   the optimizer.
3. `Fraction`-valued enumeration checks \(C_1^{prefix}=C_{\mathrm{full}}^{det}\)
   for horizons 3–6 on a half-MW grid.
4. Exact local grid projections of full trajectories are compared with the
   analytically derived marginal \(\mathcal K_t\) for every period.

The finite grids are regression checks. The continuous equality follows from
the SOC elimination in Section 3.

For \(P=E_0=\Delta=\tau=1\) and a 0.5 MW grid, the exhaustive counts are:

| Horizon | \(C_0^{exact\text{-}marginal}\) | \(C_1^{prefix}\) | \(C_{\mathrm{full}}^{det}\) |
|---:|---:|---:|---:|
| 3 | 216 | 90 | 90 |
| 4 | 1,296 | 301 | 301 |
| 5 | 7,776 | 966 | 966 |
| 6 | 46,656 | 3,025 | 3,025 |

The strict reduction from \(C_0\) is visible, while the independently tested
prefix and lifted-full counts agree at every horizon.

## 9. Reserved market baseline

`C0_MARKET` exists only as an enum value and raises `NotImplementedError`.
Future work may define conventional scalar parameters such as \(P^{max}\) and
\(R^{up}\), but no such construction is part of the current result.
