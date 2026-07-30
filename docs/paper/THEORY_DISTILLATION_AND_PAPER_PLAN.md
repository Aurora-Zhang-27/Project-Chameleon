# Project Chameleon — final theory and paper plan

Date: 2026-07-30

Status: theory and numerical validation frozen; manuscript drafting may begin.

## 1. Central question

How much information about a complex flexible resource must be exposed so
that an external capability contract is exact enough, safe enough, and
composable under the operational semantics for which it is used?

The paper treats capability contracts as **information projections of
physical flexibility**. Battery and PV+BESS provide canonical models, while
the conceptual contribution concerns information compression under
operational semantics.

## 2. Unifying principle

> As operational semantics progress from static scheduling to sequential
> execution and stochastic recourse, exact and composable capability contracts
> require progressively richer sufficient state representations:
> intertemporal envelopes, activation-conditioned reachable sets, and
> information-pattern-aware stochastic states.

This is a framework principle, not one theorem asserted under a single common
assumption set.

## 3. Four main structural results

### Main Result I — Local truthfulness is not trajectory composability

Exact per-period projections can become false when multiplied across time.
For the restricted deterministic discharge-only model,
reserve-conditional prefix inequalities give the exact projection. Terminal
energy obligations require the corresponding terminal cut.

Supporting material:

- `PROPOSITION_PREFIX_EXACTNESS.md`
- `SMALL_MODEL_DERIVATION.md`
- discharge-only part of `TERMINAL_SOC_ANALYSIS.md`

Reviewer-safe claim:

> For the Phase-I discharge-only model, reserve-conditional prefix
> constraints provide an exact projection.

### Main Result II — Physical conversion determines contract geometry

Lossless bidirectional operation admits an exact two-sided prefix description
under the stated restricted assumptions. Direction-dependent losses require
direction-aware mappings. With lossy charge/discharge complementarity, the
exact net-injection projection can be nonconvex. Removing complementarity is
a strict outer relaxation in general.

The numerical reserve-branch counterexample strengthens this result: positive
losses and positive throughput cost do not guarantee contract-exactness of
the full relaxation once reserve-conditioned recourse is present.

Supporting material:

- `CHARGING_PREFIX_ANALYSIS.md`
- `PROPOSITION_3_NONCONVEXITY.md`
- `TERMINAL_SOC_ANALYSIS.md`
- `MFE_V4_RELAXATION_GATE_REPORT.md`

### Main Result III — One-shot feasibility is not sequential composability

An aggregate `(h,r+,r-)` tuple can be existentially feasible for an isolated
call while hiding witnesses with different post-activation SOC. Consequently
the tuple is not generally a sufficient statistic for repeated calls.

In the stated lossless model, an activation-conditioned reachable-SOC
interval is an exact Markov contract state. Losses, complementarity, and
source ambiguity can require mode-aware or source-labelled transitions.

Supporting material:

- `SEQUENTIAL_RESERVE_ANALYSIS.md`
- reserve-source examples in `DETERMINISTIC_PV_BESS_ANALYSIS.md`

### Main Result IV — Under uncertainty, the information pattern is state

An unconditional reachable-SOC interval can merge scenario-contingent states
with different continuation capabilities. A marginal SOC belief can also
discard the state-scenario correspondence needed for continuation.

Depending on the guarantee, sufficient contract state may include
node-conditioned reachable sets, a joint node-SOC belief, nonanticipativity
structure, and remaining risk budget. Leaf-wise witnesses without
nonanticipativity are an outer information relaxation.

Supporting material:

- `STOCHASTIC_MARKOV_CONTRACT_ANALYSIS.md`

## 4. Contract-information hierarchy

\[
\text{local power/reserve fields}
\rightarrow
\text{prefix energy envelopes}
\rightarrow
\text{activation-conditioned reachable states}
\rightarrow
\text{node-conditioned stochastic states}.
\]

The economic experiment evaluates only a central part of this hierarchy:
static/current-style fields versus a recourse-aware intertemporal envelope,
with pathwise wait-and-see as an information boundary.

## 5. Paper storyboard

### 1. Introduction and motivating failure

- Question: why can a truthful capability report still fail operationally?
- Evidence: two-period Cartesian-product counterexample.
- Figure: operator–contract–physical-truth architecture.

### 2. Capability contracts as information projections

- Define physical feasible set, projection, contract fields, exact/inner/outer
  relations, isolated/sequential semantics, and full-information benchmarks.
- Table: unified notation and guarantee taxonomy.

### 3. Static trajectory composability

- Present Main Result I.
- Keep the smallest counterexample and restricted prefix exactness result.
- Move 3--6 period enumeration to the appendix.

### 4. Geometry of exact abstraction

- Present Main Result II.
- Main examples: lossless exact prefix and lossy midpoint nonconvexity.
- Include the reserve-conditioned relaxation counterexample.
- Move terminal and must-take-PV variants to the appendix.

### 5. Sequential execution and Markov contract states

- Present Main Result III as the conceptual center.
- Show explicit two-witness, two-call counterexample.
- Introduce set-valued transition contracts and source labels.

### 6. Stochastic information patterns

- Present Main Result IV.
- Show the smallest scenario-correspondence counterexample.
- Relate carefully to dynamic programming, POMDP beliefs,
  nonanticipativity, and risk budgets.

### 7. Design implications and contract taxonomy

- Present the recommended disclosure band.
- Distinguish technology-neutral semantics from technology-specific
  implementations such as the `C_ASSOC` proxy.

### 8. Numerical verification

- Present the lean six-cell result as representative-regime validation.
- Main figure: cost gap to `C_WS` and sequential stress.
- Report the full-LP counterexample and three certified `C_full-32` sentinels.
- State clearly that the powered 54-cell study is deferred.

### 9. Limitations and future work

- Synthetic benchmark, one PV+BESS, copper plate, small theory horizons.
- No observed CAISO outcome data, network, UC, GFM, or frequency dynamics.
- Full powered market study requires server/laboratory execution.

## 6. Main figures and tables

1. Operator–contract–physical truth–recourse architecture.
2. Contract information hierarchy.
3. Dependency graph from counterexamples and lemmas to Main Results I--IV.
4. Evolution of sufficient contract state.
5. Lean numerical frontier.
6. Summary table: semantics, hidden information, sufficient state,
   exactness, convexity, composability, and required disclosure.

## 7. Main-text versus appendix

Main text keeps:

- smallest memoryless counterexample;
- restricted prefix exactness;
- lossy nonconvexity counterexample;
- sequential two-witness counterexample;
- stochastic correspondence counterexample;
- four-level hierarchy;
- relaxation market counterexample;
- lean frontier.

Appendix keeps:

- all 3--6 period enumerations;
- terminal-SOC case splits;
- must-take PV translation;
- continuous-relaxation variants;
- full proposition inventory and technical corollaries;
- replay specifications and numerical audit trail.

## 8. Reviewer-risk controls

| Objection | Current answer | Remaining limitation |
|---|---|---|
| scope is too broad | four structural results under explicit separate assumptions | do not market the framework as a universal theorem |
| battery assumptions are narrow | batteries are canonical models for the information principle | general-resource theorem not proved |
| overlap with projection literature | prefix exactness is supporting groundwork; sequential and stochastic sufficiency are central | related-work comparison must stay theorem-level |
| results are definitions dressed as theorems | minimal counterexamples, exact set relations, and independent enumeration provide falsifiable content | avoid elevating taxonomy alone as a theorem |
| POMDP/DP overlap | contribution is the contract interpretation and exact missing correspondence fields | do not claim belief-state sufficiency as new |
| small horizons are insufficient | horizons verify exact structural claims and smallest counterexamples | they do not establish market-scale effect sizes |
| market relevance is vague | `C_ASSOC` proxy and lean cost comparison provide a concrete anchor | no observed CAISO performance claim |
| numerical design is underpowered | numerical claims are explicitly representative and descriptive | full powered grid remains future work |

## 9. Candidate framing

Candidate title:

> Capability Contracts as Information Projections: Minimal Sufficient State
> for Composable Flexibility

Alternative titles:

1. *What Must Flexible Resources Reveal? Information, Geometry, and
   Composability of Capability Contracts*
2. *From Local Flexibility to Composable Contracts: Intertemporal, Sequential,
   and Stochastic Information States*

Problem statement:

> Flexible resources are commonly represented by compressed operating
> envelopes. A report can be truthful at each instant yet fail when the
> operator composes it across time, activates reserves repeatedly, or conditions
> recourse on uncertain information. The design problem is therefore not only
> how to approximate a physical feasible set, but which hidden information
> must survive compression under the intended operational semantics.

Contribution summary:

> The paper characterizes a hierarchy of sufficient contract states. Restricted
> storage models establish when prefix envelopes exactly restore trajectory
> feasibility; lossy mode-exclusive operation shows why exact projections may
> be nonconvex; sequential reserve examples identify activation-conditioned
> reachable states as the missing Markov information; and finite-tree examples
> show that stochastic continuation additionally depends on scenario
> correspondence and information timing. A lean PV+BESS experiment anchors
> the theory against a current-style market proxy.

## 10. Freeze

No additional propositions, resources, market layers, local grids, seeds, or
thresholds are authorized. The next phase is manuscript writing.
