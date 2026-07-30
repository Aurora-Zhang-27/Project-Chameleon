# Smallest Stochastic Markov Contract for PV+BESS

## 1. Scope

This is the first stochastic Project Chameleon extension. It keeps:

- one PV+BESS resource;
- a finite PV scenario tree;
- 3–4 periods;
- sequential reserve activation;
- exact rational-grid enumeration;
- explicit nonanticipative policies;
- independent tree replay.

It adds no unit commitment, network, frequency dynamics, GFM, or large-scale
market simulation.

## 2. Information structure and timing

At each scenario-tree node \(n\):

1. the resource arrives with SOC information \(S_n\);
2. the node and current PV availability \(w_n\) are observed;
3. one internal base/reserve action is selected for node \(n\);
4. the realized reserve branch is activated;
5. the realized endpoint SOC is carried to a child node;
6. the node-conditioned SOC state, belief, and risk budget are updated.

```mermaid
flowchart LR
    A["Arrive at node n with state S_n"] --> B["Observe node and current PV w_n"]
    B --> C["Choose one nonanticipative node action"]
    C --> D["Realize reserve activation"]
    D --> E["Carry activated SOC to child node"]
    E --> F["Update conditional state, belief, and risk budget"]
```

Actions may adapt after the current node is observed. They may not depend on
which descendant leaf will occur. One action at a node is therefore shared by
all of its descendants.

This is the nonanticipativity information carried by the tree.

## 3. Exact node model

At node \(n\), let:

\[
a_n=(g_n,c_n,d_n)
\]

be the base action, with upward and downward branches \(a_n^+\) and \(a_n^-\).
They satisfy:

\[
h(a_n)=h_n,
\qquad
h(a_n^+)=h_n+r_n^+,
\qquad
h(a_n^-)=h_n-r_n^-.
\]

For realized activation
\(\alpha_n\in\{0,+,-\}\), the sequential transition is:

\[
e_{n}^{out}
=
\begin{cases}
e_n+s(a_n)\Delta,&\alpha_n=0,\\
e_n+s(a_n)(\Delta-\tau)+s(a_n^+)\tau,&\alpha_n=+,\\
e_n+s(a_n)(\Delta-\tau)+s(a_n^-)\tau,&\alpha_n=-,
\end{cases}
\]

where:

\[
s(a)=\eta_c c-d/\eta_d.
\]

The base endpoint and both awarded reserve branches are checked against SOC
bounds. The realized endpoint becomes the common starting state of every
child before the child observation.

## 4. Three stochastic semantics

Let \(\pi\) be a node-adapted policy and let
\(\Pr_\pi(\mathrm{success})\) be the total probability of feasible leaves.

### 4.1 Robust feasibility

The exact nonanticipative robust contract is:

\[
\boxed{
\exists\pi\ \text{nonanticipative}:
\Pr_\pi(\mathrm{success})=1.
}
\tag{R}
\]

Internal actions may adapt to observed nodes, but one policy must cover every
PV scenario.

### 4.2 Chance-constrained feasibility

For violation probability \(\epsilon\):

\[
\boxed{
\exists\pi\ \text{nonanticipative}:
\Pr_\pi(\mathrm{success})\ge1-\epsilon.
}
\tag{C}
\]

This is evaluated exactly from finite leaf probabilities. No sampling,
Gaussian approximation, or asymptotic chance-constraint surrogate is used.

### 4.3 Existential recourse

The implementation computes:

\[
V_n(e)
=
\max_{\pi\text{ adapted below }n}
\Pr(\mathrm{successful descendant}\mid n,e).
\tag{E1}
\]

This dynamic program provides:

- robust feasibility when \(V_{\mathrm{root}}(E_0)=1\);
- chance feasibility when
  \(V_{\mathrm{root}}(E_0)\ge1-\epsilon\);
- weak existential recourse when
  \(V_{\mathrm{root}}(E_0)>0\).

The leaf-wise full-information benchmark allows the root action to depend on
the eventual leaf. It drops nonanticipativity and is only an outer
benchmark—not an implementable recourse contract.

## 5. Smallest state-compression counterexample

Consider two equally likely continuation nodes:

- \(n_c\): next-period PV is zero;
- \(n_s\): next-period PV is 1 MW.

The next call requires \(h=0,r^+=1\). Use a lossless 1 MWh battery with
\(P^{dis}=1\).

Compare two node-conditioned SOC states.

### State A: energy aligned with scarcity

\[
S^A_{n_c}=\{1\},
\qquad
S^A_{n_s}=\{0\}.
\]

The cloudy node uses battery energy; the sunny node uses PV. Continuation
success probability is 1.

### State B: energy anti-aligned with scarcity

\[
S^B_{n_c}=\{0\},
\qquad
S^B_{n_s}=\{1\}.
\]

The cloudy node has neither PV nor stored energy and fails. Continuation
success probability is \(1/2\).

Yet both states have the same unconditional SOC interval:

\[
\operatorname{hull}(S^A)=
\operatorname{hull}(S^B)=[0,1].
\]

They also have the same marginal SOC belief:

\[
\Pr(e=0)=\Pr(e=1)=\tfrac12.
\]

Only the joint association between scenario node and SOC differs.

This is a two-node, one-continuation-call mechanism. It is embedded in the
3-period tests.

## 6. Proposition 15 — Unconditional SOC information is not Markov sufficient

**Under uncertain PV, neither an unconditional reachable-SOC interval nor a
marginal belief over SOC is generally sufficient for exact continuation
feasibility.**

**Proof.** States A and B have identical unconditional support and identical
SOC marginal distribution, but their continuation success probabilities are
1 and \(1/2\). Any contract state retaining only either common summary must
assign the same continuation capability to both and is therefore inexact.
\(\square\)

### Required additional information

The missing information is the dependence between:

- observation history or scenario-tree node;
- hidden SOC;
- future PV continuation.

On a finite tree, this can be represented by:

- scenario-indexed reachable-SOC sets \(S_n\); or
- an exact joint belief over \((n,e)\).

A belief over \(e\) alone is insufficient.

## 7. Proposition 16 — Node-conditioned sets are robust-Markov sufficient

Let \(S_n\) be the reachable SOC set at node \(n\), and let
\(\mathcal T_n\) be the source-aware activation-conditioned transition
relation at that node.

**For the finite deterministic-within-node PV+BESS model, the collection**

\[
\boxed{
\left\{
n,\ S_n,\ \mathcal T_n,\ \text{child relation}
\right\}
}
\]

**is sufficient for exact nonanticipative robust dynamic programming.**

The robust viability recursion is:

\[
\mathcal V_n
=
\left\{
e\in S_n:
\exists a_n\ 
\text{s.t.}\ 
e_n^{out}\in
\bigcap_{m\in child(n)}\mathcal V_m
\right\}.
\tag{R1}
\]

At a leaf, \(\mathcal V_n\) contains exactly the states supporting that node's
base and reserve branches.

The child intersection enforces that one node action must preserve every
continuation. In the lossless one-dimensional model, these sets may often be
represented by intervals. The node index must still be retained; replacing
all \(S_n\) by their unconditional hull is only conservative or optimistic,
depending on the quantifier used.

## 8. Chance constraints, beliefs, and risk budgets

Support sets alone do not determine chance feasibility. Probabilities matter.

For example, if one node succeeds and one fails:

- success probability \(0.75\) satisfies \(\epsilon=0.25\);
- success probability \(0.50\) does not;
- both models can have identical support sets.

At node \(n\), let \(\beta_n\) be the remaining conditional violation budget.
A dynamically consistent allocation must satisfy:

\[
\sum_{m\in child(n)}
\Pr(m\mid n)\beta_m
\le
\beta_n.
\tag{C1}
\]

## 9. Proposition 17 — Chance-Markov state requires probability and risk state

**An exact finite-tree chance-constrained contract generally requires:**

\[
\boxed{
\left(
n,\ \text{joint/node-conditioned SOC belief},\ \beta_n
\right).
}
\]

Node-conditioned support without probabilities cannot evaluate (C).
Probabilities without remaining risk budget cannot make sequential chance
decisions dynamically consistent after some branches have already consumed
allowed violation mass.

For the exact rational-grid implementation, the belief can be stored as
probability mass on node-energy pairs. Scenario-indexed intervals plus node
probabilities are sufficient only when interval-internal probability detail
is irrelevant or the contract uses robust quantification inside each
interval.

## 10. Smallest nonanticipativity counterexample

Use a 3-period two-leaf tree.

At the root:

\[
w_0=1,\quad h_0=0,\quad r_0^+=1,
\]

with an upward activation and \(E_0=1\).

The root call has two source choices:

- PV release preserves SOC at 1;
- battery discharge reduces SOC to 0.

At the next observation:

- left node requires a downward battery-charging call and therefore needs
  SOC 0;
- right node requires an upward battery-discharge call and therefore needs
  SOC 1.

If the future leaf were known at the root:

- choose battery discharge for the left leaf;
- choose PV release for the right leaf.

Thus every leaf is individually feasible under full information.

Under nonanticipativity, the root must choose one source before the child is
known. Either choice preserves only one of the two leaves. Maximum success
probability is \(1/2\).

## 11. Proposition 18 — Leaf-wise recourse is a strict outer benchmark

Let:

- \(\mathcal C_{\mathrm{NA}}\) be the exact nonanticipative policy set;
- \(\mathcal C_{\mathrm{FI}}\) be the leaf-wise full-information set.

Then:

\[
\boxed{
\mathcal C_{\mathrm{NA}}
\subseteq
\mathcal C_{\mathrm{FI}},
}
\]

and the inclusion can be strict.

**Proof.** Every nonanticipative policy induces a feasible leaf-specific
action collection. The converse fails in the two-leaf example: separate root
actions make both leaves feasible, while no common root action does.
\(\square\)

Therefore a scenario list with independent witnesses is not an exact
multistage contract. The scenario-tree node structure and nonanticipativity
classes are information fields, not implementation details.

## 12. Exact, inner, and outer relations

For \(0\le\epsilon_1\le\epsilon_2<1\):

\[
\mathcal C_{\mathrm{static\ robust}}
\subseteq
\mathcal C_{\mathrm{NA\ robust}}
\subseteq
\mathcal C_{\mathrm{NA\ chance}}(\epsilon_1)
\subseteq
\mathcal C_{\mathrm{NA\ chance}}(\epsilon_2).
\]

The first set forces one nonadaptive internal action schedule and is a
conservative inner contract relative to node-adapted robust recourse.

Dropping nonanticipativity gives an outer set:

\[
\mathcal C_{\mathrm{NA\ chance}}(\epsilon)
\subseteq
\mathcal C_{\mathrm{FI\ chance}}(\epsilon).
\]

Using an unconditional SOC hull with universal state quantification is a safe
but generally strict robust inner approximation:

\[
\mathcal C_{\mathrm{hull\ robust}}
\subseteq
\mathcal C_{\mathrm{node\ robust}}^{exact}.
\]

Using the hull existentially is an outer approximation and may accept State B
as if its stored energy were available in the cloudy node:

\[
\mathcal C_{\mathrm{node}}^{exact}
\subseteq
\mathcal C_{\mathrm{hull\ existential}}.
\]

The continuous charge/discharge relaxation remains an outer approximation of
every physical stochastic set because each deterministic node model is
relaxed.

## 13. Exact 3–4 period scenario-tree enumeration

The test tree has:

- one root;
- two equally likely period-1 children;
- deterministic zero-action tails through period 2 or 3;
- one root upward call that can be supplied by PV or battery;
- each child independently assigned an upward or downward call.

There are four exact external branch-contract combinations:

\[
(+,+),\quad (+,-),\quad (-,+),\quad (-,-).
\]

For both 3- and 4-period trees:

| Horizon | Contracts | NA robust | NA chance, \(\epsilon=0.5\) | Full-information feasible |
|---:|---:|---:|---:|---:|
| 3 | 4 | 2 | 4 | 4 |
| 4 | 4 | 2 | 4 | 4 |

Interpretation:

- matching child directions admit a common root source and are robust;
- opposite child directions require different root sources;
- mixed cases have exact nonanticipative success probability \(1/2\);
- full information incorrectly reports probability 1 for all four if used as
  an implementable contract.

Every chosen policy is replayed independently over the entire tree. The
replay recomputes:

- node starting SOC;
- base and reserve branch feasibility;
- realized sequential SOC;
- source-label compliance;
- feasible leaf probability.

## 14. The stochastic Markov contract boundary

The deterministic state:

\[
S_t=[L_t,U_t]
\]

is no longer generally sufficient after PV uncertainty branches.

The smallest exact finite-tree replacements are:

### Robust

\[
\left\{
n,\ S_n,\ \mathcal T_n,\ child(n)
\right\}.
\]

### Chance constrained

\[
\left\{
n,\ \Pr(n,e\mid\text{history}),\ \beta_n
\right\}.
\]

### Multistage recourse

\[
\left\{
\text{node-conditioned action policy},
\text{nonanticipativity classes},
\text{node-state transition}
\right\}.
\]

This is the first Chameleon result where a state support, a probability
belief, and an information partition become separate contract objects.

## 15. Restricted interpretation

These results apply only to:

- a finite, explicitly supplied PV scenario tree;
- one small PV+BESS resource;
- exact small rational grids;
- fixed reserve activation semantics;
- 3–4 periods.

They do not establish a scalable stochastic market design. They identify the
minimum information structure that such a design would have to preserve.
