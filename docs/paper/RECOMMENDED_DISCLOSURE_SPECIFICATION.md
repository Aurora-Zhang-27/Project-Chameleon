# Chameleon recommended capability disclosure

Date: 2026-07-30

This is a paper-facing specification for what a complex flexible resource
should disclose without revealing its complete internal model. Battery and
PV+BESS are the canonical examples; the fields are organized by operational
meaning rather than technology name.

| Field | Unit / object | Formal meaning | Guarantee | When required |
|---|---|---|---|---|
| Scheduled net-injection envelope | MW by interval | admissible `h_t` range and ramp transitions | exact, inner, or outer must be labelled | always |
| Up/down reserve envelope | MW by interval | admissible `(r_t^+,r_t^-)` conditional on schedule | fixed product semantics | whenever reserve is sold |
| Activation semantics | duration, timing, call count | start time, sustain duration, isolated or sequential calls | explicit, not inferred | whenever reserve is sold |
| Intertemporal energy envelope | MWh prefix inequalities | cumulative injection/withdrawal budgets conditional on reserve | exact for stated restricted model or certified inner | energy-limited resources |
| State boundary | MWh point or interval | initial/current energy and terminal obligation | timestamped | when continuation depends on stored state |
| Conversion convention | efficiency map / mode flag | direction-dependent losses and whether modes are exclusive | physical | lossy bidirectional resources |
| Activation-conditioned reachable state | interval or set-valued transition | possible post-call state set from the disclosed current state | Markov-sufficient for stated semantics | repeated or sequential calls |
| Flexibility-source attribution | MW by source | battery energy, reduced charging, renewable headroom, curtailment | source-labelled | hybrid resources when future consequences differ by source |
| Scenario/node correspondence | node-indexed set or transition | which states remain reachable under each information-tree node | nonanticipative | uncertain multistage operation |
| Belief and remaining risk budget | probability measure and scalar/vector budget | joint hidden-state/scenario belief and unused violation allowance | chance-constrained | probabilistic guarantees |

## Recommended disclosure band

The lower edge is the smallest bundle that should normally be demanded from an
energy-limited resource:

\[
\{\text{power/reserve fields},\ \text{activation semantics},\
\text{intertemporal energy envelope},\ \text{state/terminal boundary},\
\text{conversion convention}\}.
\]

Below this bundle, the verified counterexamples show a recurring risk of
trajectory or activation failure even when every local field is individually
truthful.

The practical upper edge for deterministic sequential operation is:

\[
\{\text{lower-edge fields},\
\text{activation-conditioned reachable-state transition},\
\text{source attribution when hybrid}\}.
\]

Under uncertainty, node correspondence, nonanticipativity, and the relevant
belief/risk state are added only when the market asks for a stochastic
guarantee. Beyond that upper edge, exposing internal component schedules,
device identities, or a complete physical model should require evidence of
material incremental cost or reliability value.

The lean MFE supplies a representative-regime price for one central step
inside this band. Across six registered PV+BESS cells, the recourse-aware
intertemporal `C1` envelope reduced mean realized cost by 12.9%--16.1%
relative to the `C_ASSOC` market proxy, with zero isolated non-delivery for
both lines. `C1` remained 4.2%--6.1% above the pathwise wait-and-see cost
boundary, compared with 20.0%--24.9% for `C_ASSOC`.

This does not price every field. In particular, the fixed-policy two-call
stress test confirms that sequential composability is a distinct requirement:
the benefit of `C1` depended on battery duration and reserve tier, and
short-duration or high-reserve cells still failed. The theoretical lower and
upper edges therefore remain the primary disclosure recommendation; the lean
experiment is a mechanism-consistent numerical anchor, not a population-wide
market estimate.
