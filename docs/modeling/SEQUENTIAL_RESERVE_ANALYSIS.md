# Sequential Reserve Activation in Deterministic PV+BESS

## 1. Scope

This extension keeps:

- one deterministic PV+BESS resource;
- 3–6 periods;
- deterministic PV availability;
- exact rational-grid enumeration;
- fixed-duration reserve activation;
- explicit internal witnesses and independent replay.

It adds no uncertainty, unit commitment, network, GFM, or frequency dynamics.

The purpose is to distinguish one-shot deliverability from dynamically
composable reserve capability.

## 2. Two reserve semantics

Let the base internal action in period \(t\) be
\(a_t=(g_t,c_t,d_t)\), with:

\[
h_t=g_t+d_t-c_t.
\]

Let \(a_t^+\) and \(a_t^-\) be upward and downward branch actions satisfying:

\[
h(a_t^+)=h_t+r_t^+,
\qquad
h(a_t^-)=h_t-r_t^-.
\]

Write the SOC rate of an action as:

\[
s(a)=\eta_c c-\frac{d}{\eta_d}.
\]

### 2.1 Isolated one-shot semantics

The nominal base state follows:

\[
e_{t+1}^0=e_t^0+s(a_t)\Delta_t.
\]

Each reserve award is tested as an isolated branch:

\[
e_{t,+}^{iso}
=e_t^0+s(a_t)(\Delta_t-\tau)+s(a_t^+)\tau,
\]

\[
e_{t,-}^{iso}
=e_t^0+s(a_t)(\Delta_t-\tau)+s(a_t^-)\tau.
\]

The branch endpoint is checked against SOC limits but is not carried into the
next period. All later calls restart from the common nominal base trajectory.

### 2.2 Sequential activation semantics

Let \(\alpha_t\in\{0,+,-\}\) denote the realized activation. The state update
is:

\[
e_{t+1}=
\begin{cases}
e_t+s(a_t)\Delta_t,&\alpha_t=0,\\
e_t+s(a_t)(\Delta_t-\tau)+s(a_t^+)\tau,&\alpha_t=+,\\
e_t+s(a_t)(\Delta_t-\tau)+s(a_t^-)\tau,&\alpha_t=-.
\end{cases}
\tag{S1}
\]

The realized endpoint in (S1) becomes the initial state for period \(t+1\).
The implementation also verifies that the common base point and both awarded
branches are feasible from the current realized state.

There are three distinct feasibility statements:

1. **one-shot existential:** a witness exists for one isolated call;
2. **sequence existential:** a source-aware witness exists for the entire
   realized call sequence;
3. **hidden-witness robust:** every internally compliant first-call witness
   preserves the promised continuation.

Only the first statement is provided by a stagewise one-shot contract.

## 3. Smallest counterexample

Use two periods, or append a zero third period, with:

\[
E_0=1,\quad
[\underline E,\overline E]=[0,1],\quad
P^{ch}=P^{dis}=1,\quad
\eta_c=\eta_d=1,\quad
\tau=\Delta=1,
\]

\[
w=(1,0),\quad
h=(0,0),\quad
r^+=(1,1),\quad
r^-=(0,0).
\]

The base action is idle with all available PV curtailed.

At the first call, the same external tuple
\((h_1,r_1^+,r_1^-)=(0,1,0)\) has two feasible witnesses:

### Witness A: PV release

\[
g_1^+=1,\qquad d_1^+=c_1^+=0.
\]

The first call ends at:

\[
e_2^A=1.
\]

The second call, where \(w_2=0\), can then be supplied by 1 MW battery
discharge and ends at \(e_3^A=0\).

### Witness B: battery discharge

\[
d_1^+=1,\qquad g_1^+=c_1^+=0.
\]

The first call ends at:

\[
e_2^B=0.
\]

The identical second award requires another 1 MW battery discharge, which
would give \(e_3^B=-1\) and is infeasible.

Both witnesses pass isolated replay because the second call is tested from
the nominal SOC \(1\). Only Witness A passes sequential replay.

## 4. Proposition 11 — One-shot contracts are not dynamically composable

**An aggregate one-shot reserve tuple
\((h_t,r_t^+,r_t^-)\) need not be a sufficient Markov state for two or more
sequential activations, even in a deterministic lossless PV+BESS model.**

**Proof.** The two witnesses above have the same first-stage aggregate tuple
and are both one-shot feasible, but their realized post-call SOC values are
1 and 0. The second call is feasible from the first state and infeasible from
the second. Therefore the aggregate tuple does not determine continuation
feasibility. \(\square\)

### Corollary 11.1 — Impossibility of an exact memoryless continuation rule

No rule using only the current aggregate tuple can both:

1. accept all feasible first-call realizations in the counterexample; and
2. guarantee the second reserve call without additional state or source
   information.

It must either:

- expose activation-conditioned state/source information; or
- reject some feasible first-call witnesses through a conservative rule.

This is an operational failure, not merely an interpretability issue.

### Important qualification

The full aggregate trajectory together with a specified activation sequence
can still be tested by existential projection:

\[
\mathcal C_{seq}^{exists}
=
\Pi_{h,r,\alpha}
\left(
\mathcal F_{seq}^{source\text{-}lifted}
\right).
\]

What fails is time-separable composition of one-shot existential statements,
not the existence of a larger lifted sequential model.

## 5. Lossless activation-conditioned reachable intervals

For any required hybrid output \(y\), feasible battery net power lies in:

\[
I_t(y)=
\left[
\max\{-P^{ch},y-w_t\},
\min\{P^{dis},y\}
\right].
\tag{S2}
\]

For an SOC interval \(S=[L,U]\), power interval \(I=[a,b]\), and duration
\(\delta\), define the lossless interval map:

\[
\mathcal M_\delta(S,I)
=
\left[
\max\{\underline E,L-b\delta\},
\min\{\overline E,U-a\delta\}
\right].
\tag{S3}
\]

An empty interval means infeasibility.

For no call:

\[
\mathcal T_0(S_t;h_t)
=\mathcal M_{\Delta_t}(S_t,I_t(h_t)).
\]

For a realized upward call:

\[
\mathcal T_+(S_t;h_t,r_t^+)
=
\mathcal M_\tau
\left(
\mathcal M_{\Delta_t-\tau}(S_t,I_t(h_t)),
I_t(h_t+r_t^+)
\right).
\tag{S4}
\]

The downward map replaces \(h_t+r_t^+\) with \(h_t-r_t^-\).

## 6. Proposition 12 — Exact lossless set-valued Markov contract

**For the deterministic lossless PV+BESS model with unrestricted internal
source selection, the activation-conditioned reachable SOC interval is a
sufficient state for exact path-conditioned sequential feasibility.**

The compact Markov-style contract is:

\[
\boxed{
S_{t+1}
=
\mathcal T_{\alpha_t}
\left(
S_t;h_t,r_t^+,r_t^-
\right),
\qquad
S_1=\{E_0\}.
}
\tag{S5}
\]

**Proof.** Under lossless operation, each feasible battery-power set in (S2)
is an interval and the SOC transition is affine. The Minkowski image of two
intervals is an interval, and intersection with SOC bounds remains an
interval. Applying this argument to the base and activated subintervals gives
(S3)–(S4). Induction establishes exact reachability for the full activation
path. \(\square\)

Equation (S5) conditions on the realized branch. If the contract must also
qualify the uncalled direction at each state, the exact transition is the
projection of the common-base, dual-branch lifted polytope. In the lossless
model its scalar next-SOC projection remains an interval, although computing
it requires the additional branch intersection.

## 7. Lossy complementary operation

Define:

\[
\phi(p)=
\begin{cases}
p/\eta_d,&p\ge0,\\
\eta_c p,&p<0.
\end{cases}
\]

The lossy interval map is:

\[
\mathcal M_\delta^\eta([L,U],[a,b])
=
\left[
\max\{\underline E,L-\phi(b)\delta\},
\min\{\overline E,U-\phi(a)\delta\}
\right].
\tag{S6}
\]

Because \(\phi\) is continuous and increasing, (S6) still maps an SOC
interval exactly to an SOC interval for unrestricted internal source choice.

## 8. Proposition 13 — Interval state remains sufficient, but the lossy
transition is mode-aware

**In the present one-dimensional deterministic PV+BESS model, lossy
charge/discharge complementarity does not by itself require a disconnected
reachable-SOC state set: an interval remains sufficient along a fixed
activation path. However, the exact transition graph is piecewise linear,
direction dependent, and generally nonconvex in the external contract
variables.**

The signed mode must enter through \(\phi\). Replacing (S6) by the lossless
net-energy map is not exact.

The Stage-B nonconvex trajectories remain a counterexample on the no-call
face of the sequential transition relation. Thus a globally exact continuous
convex transition contract cannot generally be written solely in aggregate
net-injection variables without:

- mode-aware or discrete information;
- lifted charge/discharge variables; or
- conservatism.

When source policies couple base and branch actions, such as requiring
\(g_t^+=g_t\) for battery-only reserve, the exact transition may require the
source-lifted relation even though its final scalar SOC projection can still
be summarized by interval endpoints.

## 9. Source-specific reserve allocation

The implementation distinguishes:

- **PV-only:** branch battery charge/discharge equals the base battery action;
- **battery-only:** branch delivered PV equals base delivered PV;
- **any source:** either mechanism or a combination may be used.

In the counterexample:

- labelling the first call PV-only and the second battery-only produces the
  feasible SOC path \(1\to1\to0\);
- labelling both calls battery-only is infeasible.

## 10. Proposition 14 — Source labels refine the transition

Let \(\sigma\) denote a reserve-source allocation. Then:

\[
\mathcal C_{seq}^{\sigma}
\subseteq
\mathcal C_{seq}^{any},
\qquad
\mathcal C_{seq}^{any}
=
\bigcup_\sigma
\mathcal C_{seq}^{\sigma}.
\]

**A disclosed source allocation removes the specific ambiguity in
Proposition 11 and yields a tighter activation-conditioned SOC transition.**

A coarse label need not always determine one exact SOC value: the base hybrid
injection itself may still admit multiple PV/battery decompositions. Exact
deterministic state update requires the pre-call SOC together with sufficient
base and branch battery-energy information. Otherwise the correct state
remains an interval.

## 11. Exact, inner, and outer relations

### Repeated upward calls

When upward activation cannot increase SOC:

\[
\mathcal C_{seq}^{exists}
\subseteq
\mathcal C_{iso}^{product}.
\]

The inclusion is strict by Proposition 11. The isolated product is an outer
approximation to sequential feasibility in this restricted direction.

### Mixed upward and downward calls

There is no general inclusion between isolated and sequential sets. A
downward call may charge the battery and make a later call feasible even when
the isolated test from the nominal path rejects it. Conversely, an upward
call may deplete SOC and invalidate a later award.

### Robust hidden-witness guarantee

Define:

\[
\mathcal C_{seq}^{robust}
=
\left\{
x:
\text{every compliant realized witness preserves continuation}
\right\}.
\]

Then:

\[
\boxed{
\mathcal C_{seq}^{robust}
\subseteq
\mathcal C_{seq}^{exists}.
}
\]

The inclusion is strict in the counterexample: a PV-first witness succeeds
but a battery-first witness fails. The robust set is a conservative inner
contract relative to existential sequential feasibility.

### Continuous charge/discharge relaxation

\[
\mathcal C_{seq}^{physical}
\subseteq
\mathcal C_{seq}^{relaxed}.
\]

The inclusion is strict in general because the no-call and zero-reserve faces
contain the existing lossy simultaneous-charge/discharge counterexample.

## 12. Exact 3–6 period enumeration

### Lossless repeated upward calls

Use:

\[
E_0=1,\quad [\underline E,\overline E]=[0,1],\quad
w=(1,0,\ldots,0),\quad h_t=0,
\]

\[
r_t^+\in\{0,1\},\quad r_t^-=0,
\]

with an upward activation in every period where the award is positive.

| Horizon | Candidate sequences | Isolated product | Sequential exact |
|---:|---:|---:|---:|
| 3 | 8 | 8 | 6 |
| 4 | 16 | 16 | 8 |
| 5 | 32 | 32 | 10 |
| 6 | 64 | 64 | 12 |

The first upward call can use PV without depleting SOC. Across all later
periods, only one 1 MWh battery call can be supported. Hence the exact count
is \(2T\), while all \(2^T\) sequences pass isolated tests.

### Lossy repeated upward calls

Use:

\[
\eta_c=\eta_d=\tfrac12,\quad
w=(\tfrac12,0,\ldots,0),\quad
r_t^+\in\{0,\tfrac12\}.
\]

A \(1/2\) MW battery call consumes 1 MWh, so the same counts result:

| Horizon | Candidate sequences | Sequential exact |
|---:|---:|---:|
| 3 | 8 | 6 |
| 4 | 16 | 8 |
| 5 | 32 | 10 |
| 6 | 64 | 12 |

For every horizon and candidate sequence:

- grid-exact source-aware witness search agrees with the
  activation-conditioned interval recursion;
- every accepted witness passes independent sequential SOC replay;
- rejected second calls exhibit an explicit SOC shortage.

## 13. Boundary established

The deterministic result is:

> A one-shot aggregate reserve tuple can be existentially exact for the first
> activation while failing to be a sufficient Markov state for the second.

The minimal additional information is not necessarily a stochastic forecast.
In the lossless model it can be an activation-conditioned reachable-SOC
interval and transition map. In the lossy model the state interval can remain
compact, but the exact transition must retain efficiency direction and may
require source-lifted or mode-aware structure.
