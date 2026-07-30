# Proposition 1: Exact Prefix Projection in the Phase-I Discharge-Only Model

## Model and assumptions

Fix a finite horizon \(\mathcal T=\{1,\ldots,T\}\). For every period
\(t\in\mathcal T\), let:

- \(p_t\ge 0\) be scheduled battery discharge power;
- \(r_t\ge 0\) be awarded upward reserve power;
- \(\Delta_t>0\) be the scheduling-interval duration;
- \(\tau_t\in(0,\Delta_t]\) be the fixed reserve-sustain duration;
- \(P_t\ge0\) be the discharge-plus-reserve power limit;
- \(e_t\) be usable battery energy at the start of period \(t\);
- \(E_0\ge0\) be initial usable energy above the lower SOC bound.

The result is restricted to the following assumptions:

1. **Battery only:** there is no PV or other exogenous energy source.
2. **Discharge only:** charging is prohibited and there is no charging
   opportunity.
3. **Deterministic:** all parameters are known and no uncertainty set or
   scenario index is present.
4. **Lossless state equation:**

   \[
   e_{t+1}=e_t-p_t\Delta_t.
   \]

5. **Fixed single-call reserve semantics:** in period \(t\), the awarded
   reserve is tested as one isolated upward call of magnitude \(r_t\) and
   duration \(\tau_t\). The incremental reserve-energy requirement is
   \(r_t\tau_t\).
6. **No repeated-call guarantee:** reserve awards in different periods are
   not assumed to be activated sequentially on the same realized state path.
   Each call is tested from the common scheduled base trajectory.
7. **No additional terminal coupling:** the only terminal requirement is
   nonnegative remaining usable energy.
8. **No other intertemporal constraints:** there is no recovery rule,
   degradation budget, ramp-memory state, minimum charge/discharge duration,
   or state-dependent power limit.

These assumptions define the **Phase-I discharge-only model**.

## Lifted physical feasible set

Define the lifted deterministic feasible set
\(\mathcal F_{\mathrm{full}}^{\mathrm{DO}}\) as the set of
\((p,r,e)\) satisfying:

\[
e_1=E_0,
\tag{1a}
\]

\[
e_{t+1}=e_t-p_t\Delta_t
\qquad \forall t\in\mathcal T,
\tag{1b}
\]

\[
p_t\ge0,\qquad r_t\ge0,
\tag{1c}
\]

\[
p_t+r_t\le P_t
\qquad \forall t\in\mathcal T,
\tag{1d}
\]

\[
p_t\Delta_t+r_t\tau_t\le e_t
\qquad \forall t\in\mathcal T.
\tag{1e}
\]

Constraint (1e) requires enough energy to execute the scheduled discharge for
the interval and add one reserve response of duration \(\tau_t\).

Let:

\[
\Pi_{p,r}
\left(
\mathcal F_{\mathrm{full}}^{\mathrm{DO}}
\right)
\]

denote its projection onto the operator-visible energy and reserve variables.

## Prefix-contract feasible set

Define \(\mathcal F_{\mathrm{prefix}}^{\mathrm{DO}}\) as the set of
\((p,r)\) satisfying:

\[
p_t\ge0,\qquad r_t\ge0,
\tag{2a}
\]

\[
p_t+r_t\le P_t
\qquad \forall t\in\mathcal T,
\tag{2b}
\]

and the reserve-conditional prefix inequalities:

\[
\sum_{s=1}^{t}p_s\Delta_s+r_t\tau_t
\le E_0
\qquad \forall t\in\mathcal T.
\tag{2c}
\]

## Proposition 1

**For the Phase-I discharge-only model, reserve-conditional prefix
constraints provide an exact projection:**

\[
\boxed{
\mathcal F_{\mathrm{prefix}}^{\mathrm{DO}}
=
\Pi_{p,r}
\left(
\mathcal F_{\mathrm{full}}^{\mathrm{DO}}
\right)
}.
\tag{3}
\]

Equivalently, an operator-visible trajectory \((p,r)\) satisfies the prefix
contract if and only if there exists an SOC trajectory \(e\) satisfying the
complete lifted physical model.

## Proof

We prove both inclusions.

### Full projection is contained in the prefix set

Take any:

\[
(p,r)\in
\Pi_{p,r}
\left(
\mathcal F_{\mathrm{full}}^{\mathrm{DO}}
\right).
\]

By definition, there exists \(e\) such that (1a)-(1e) hold. Repeated
substitution of (1b) into (1a) gives:

\[
e_t
=
E_0-\sum_{s=1}^{t-1}p_s\Delta_s.
\tag{4}
\]

Substitute (4) into (1e):

\[
p_t\Delta_t+r_t\tau_t
\le
E_0-\sum_{s=1}^{t-1}p_s\Delta_s.
\]

Rearranging gives:

\[
\sum_{s=1}^{t}p_s\Delta_s+r_t\tau_t
\le E_0,
\]

which is (2c). Conditions (1c) and (1d) give (2a) and (2b).
Therefore:

\[
\Pi_{p,r}
\left(
\mathcal F_{\mathrm{full}}^{\mathrm{DO}}
\right)
\subseteq
\mathcal F_{\mathrm{prefix}}^{\mathrm{DO}}.
\tag{5}
\]

### Prefix set is contained in the full projection

Take any:

\[
(p,r)\in\mathcal F_{\mathrm{prefix}}^{\mathrm{DO}}.
\]

Construct:

\[
e_1=E_0,
\qquad
e_t
=
E_0-\sum_{s=1}^{t-1}p_s\Delta_s
\quad
t=2,\ldots,T+1.
\tag{6}
\]

Construction (6) satisfies (1a) and (1b). From (2c):

\[
\sum_{s=1}^{t}p_s\Delta_s+r_t\tau_t
\le E_0.
\]

Using (6), this is exactly:

\[
p_t\Delta_t+r_t\tau_t\le e_t,
\]

so (1e) holds. Because \(r_t\tau_t\ge0\), (2c) also implies:

\[
\sum_{s=1}^{t}p_s\Delta_s\le E_0,
\]

and hence \(e_{t+1}\ge0\). Conditions (2a) and (2b) give (1c) and
(1d). Thus the constructed \(e\) makes \((p,r,e)\) feasible in the lifted
model, implying:

\[
\mathcal F_{\mathrm{prefix}}^{\mathrm{DO}}
\subseteq
\Pi_{p,r}
\left(
\mathcal F_{\mathrm{full}}^{\mathrm{DO}}
\right).
\tag{7}
\]

Combining (5) and (7) proves (3). \(\square\)

## Interpretation

The proposition is an elimination result. Under the stated assumptions, SOC
is not additional information needed to describe the operator-visible
\((p,r)\) feasible set: eliminating SOC produces exactly the prefix
inequalities (2c).

It does **not** say that the two messages disclose identical information.
The lifted model exposes the internal state and its transition equation,
whereas the prefix contract exposes only the resulting trajectory
restrictions. They are operationally equivalent for this specific scheduling
task and model class.

## What Proposition 1 does not claim

Proposition 1 does not establish that:

- prefix contracts exactly represent general storage capability;
- the result holds when charging is permitted;
- the result holds with PV or another uncertain energy source;
- the result holds under stochastic or robust reserve guarantees;
- one prefix budget certifies repeated or correlated reserve calls;
- the result survives state-dependent efficiency, degradation, recovery,
  ramp-memory, or terminal-value constraints;
- the prefix representation remains exact for bidirectional reserve;
- the prefix representation is minimal among all possible messages;
- the same equivalence holds for cost, strategic bidding, or information
  privacy beyond physical feasibility.

Any extension that introduces one of these features requires a new feasible
set and a new proof. Equation (3) should not be reused by analogy.

## Suggested citation sentence

The safe paper-level sentence is:

> For the Phase-I deterministic, lossless, discharge-only battery model with
> fixed single-call upward-reserve semantics, reserve-conditional prefix
> constraints provide an exact projection of the lifted physical feasible set
> onto scheduled energy and reserve variables.

The unsafe sentence is:

> Prefix contracts exactly represent storage capability.

