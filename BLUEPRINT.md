Project Chameleon

Research Blueprint

Working title

Chameleon: Quantifying the Abstraction Gap of One-Shot Capability Contracts for Renewable Hybrid Resources

Vision title

Chameleon: How Much Must a Grid Resource Reveal?

Project status

Conditional GO. The project has passed three adversarial novelty checks, but its defensible contribution is materially narrower than the original “renewable wrapper” concept. The initial implementation must therefore be theory-first, small-scale, and explicitly designed as a kill experiment.

⸻

1. Executive Summary

Future power systems will contain increasingly heterogeneous resources, including renewable-storage hybrids, virtual power plants, electric-vehicle fleets, electrolyzers, flexible data centers, aggregated distributed energy resources, and inverter-based resources with fast dynamic capabilities.

A system operator cannot realistically maintain a separate detailed scheduling model for every technology, vendor, controller, and internal device configuration. At the same time, treating every complex resource as a conventional memoryless generator can lead to infeasible schedules, reserve non-delivery, hidden state exhaustion, and overestimation of dynamic capabilities.

Project Chameleon studies the interface between these two extremes.

The central question is:

How much information must a complex grid resource reveal for a system operator to schedule it safely and efficiently?

Chameleon does not propose a new virtual power plant controller, a new battery MPC, or a new grid-forming inverter model. Instead, it studies the consequences of replacing full internal resource disclosure with standardized, technology-agnostic, one-shot capability contracts.

The project will define a hierarchy of capability-contract classes with increasing expressiveness and compare them against a fully-aware scheduling benchmark using one common physical truth model. The main output will be an abstraction-gap frontier showing how scheduling cost, operational reliability, security, computational burden, and information disclosure change as the capability interface becomes more expressive.

The first phase will focus only on a renewable-plus-battery hybrid participating in energy and reserve scheduling under renewable uncertainty and intertemporal state-of-charge coupling. Dynamic frequency response, network interactions, multiple correlated resources, and full transmission-distribution coordination are reserved for later stages.

⸻

2. Origin of the Project

The original Chameleon idea was motivated by the increasing burden placed on system operators as renewable and inverter-based technologies become more diverse.

The initial intuition was:

Rather than repeatedly modifying SCUC and SCED to understand every renewable technology, allow the resource to adapt internally and present itself externally as a dispatchable generator.

The original conceptual architecture was:

[
\text{Forecasting}
\rightarrow
\text{Renewable generation}
\rightarrow
\text{Battery and local controller}
\rightarrow
\text{Generator-like wrapper}
\rightarrow
\text{Legacy SCUC/SCED}
]

The operator would see a generic dispatchable resource, while the plant would internally handle:

* renewable forecasting;
* forecast uncertainty;
* battery charging and discharging;
* state of charge;
* reserve delivery;
* curtailment;
* grid-forming control;
* virtual inertia;
* droop;
* current limits;
* local dispatch tracking.

After multiple literature reviews, this architecture was found to be insufficient as a research contribution by itself.

Dispatchable feeders already demonstrate renewable-plus-storage trajectory tracking. Dynamic virtual power plant research already demonstrates generator-like aggregate dynamic behaviour. Existing market rules already permit hybrid resources to participate as unified resources. Aggregate flexibility and realizability literature already studies feasible regions and device-level disaggregation.

Therefore, Chameleon was pivoted from a wrapper architecture to an information-abstraction problem.

The wrapper may still be used as experimental infrastructure, but it is not the core contribution.

⸻

3. Research Motivation

3.1 Increasing resource heterogeneity

Future operators may need to schedule resources such as:

* PV plus battery hybrids;
* wind plus battery hybrids;
* virtual power plants;
* aggregated residential batteries;
* electric-vehicle fleets;
* flexible industrial loads;
* hydrogen electrolyzers;
* data centers;
* distributed energy resource aggregators;
* mixed grid-forming and grid-following inverter portfolios.

These resources differ internally in:

* energy availability;
* intertemporal constraints;
* uncertainty;
* ramping behaviour;
* reserve duration;
* recovery requirements;
* efficiency;
* degradation;
* communication delay;
* control structure;
* saturation behaviour;
* disturbance response.

A technology-specific scheduling formulation for every resource type would become increasingly difficult to maintain, validate, standardize, and audit.

3.2 Full disclosure is not automatically desirable

A fully-aware system operator could theoretically receive:

* device-level models;
* internal state variables;
* renewable scenarios;
* detailed battery parameters;
* controller equations;
* inverter current limits;
* network topology;
* disaggregation logic;
* internal forecast models.

However, full disclosure may create:

* large optimization models;
* technology-specific market rules;
* proprietary-information concerns;
* verification and certification burdens;
* vendor-dependent modelling;
* poor scalability;
* difficult model maintenance;
* barriers to market participation.

3.3 Excessive abstraction is also dangerous

A conventional generator-style interface may only expose:

[
P^{\min}_t,\quad P^{\max}_t,\quad RU_t,\quad RD_t,\quad R^\uparrow_t,\quad R^\downarrow_t
]

Such an interface may fail to represent:

* state-of-charge coupling across time;
* cumulative energy limitations;
* renewable forecast uncertainty;
* conditional reserve availability;
* response duration;
* saturation;
* post-response recovery;
* dependence between energy and ancillary-service commitments.

The result may be a schedule that is valid in the operator’s abstract model but impossible for the physical resource to implement.

3.4 The central trade-off

The project studies the trade-off:

[
\text{less disclosure}
\longleftrightarrow
\text{simpler and more standardized scheduling}
]

versus

[
\text{more disclosure}
\longleftrightarrow
\text{better feasibility, reliability, and optimality}
]

The practical problem is not whether zero disclosure or full disclosure is universally superior.

The practical problem is:

What level of information is sufficient for a specified operating objective?

⸻

4. Literature Positioning

Three adversarial literature checks were conducted before implementation.

4.1 Dispatchable feeder literature

The EPFL dispatchable feeder literature already demonstrates:

* day-ahead dispatch planning;
* adaptive forecasting;
* battery-backed dispatch tracking;
* real-time receding-horizon control;
* experimental operation on a real distribution feeder.

Therefore, Chameleon must not claim that renewable-plus-storage resources can be made dispatchable or can track an external trajectory under forecast error.

4.2 Dynamic virtual power plant literature

DVPP research already demonstrates:

* aggregation of heterogeneous distributed resources;
* desired aggregate dynamic behaviour;
* dynamic participation factors;
* fast frequency and voltage support;
* generator-like control and contractual specifications;
* adaptation to fluctuating resource capacities;
* hardware-in-the-loop validation.

Therefore, Chameleon must not claim that heterogeneous inverter resources can collectively emulate conventional generator dynamics.

4.3 Aggregate flexibility and realizability literature

Existing work already studies:

* aggregate feasible sets;
* virtual battery models;
* time-coupled flexibility regions;
* deterministic element-level realizability;
* device-level disaggregation;
* complementarity constraints;
* unit-commitment integration.

Therefore, Chameleon must not claim deterministic aggregate dispatch realizability as an entirely new concept.

4.4 TSO–DSO interface literature

The TSO–DSO and operating-envelope literature already contains:

* active and reactive power flexibility regions;
* multi-period flexibility regions;
* uncertainty-aware regions;
* continuous-time flexibility models;
* operating envelopes;
* privacy-preserving energy and reserve coordination;
* dynamic equivalents;
* comparisons of coordination architectures.

Therefore, Chameleon must not claim to be the first technology-agnostic interface, the first time-coupled flexibility envelope, or the first uncertainty-aware interface abstraction.

4.5 Remaining research space

The literature checks did not identify a work that jointly provides:

* a formal ordered family of one-shot capability contracts;
* a common physical truth model;
* comparison against fully-aware stochastic scheduling;
* cost, reliability, and dynamic-security abstraction gaps;
* stochastic reserve-conditional realizability;
* formal limits on what per-resource contracts can certify.

The surviving research space is the joint and quantified abstraction problem, not any individual control or flexibility component.

⸻

5. Core Research Thesis

The project’s central thesis is:

A complex grid resource does not necessarily need to reveal its full internal model to be scheduled effectively. However, conventional generator parameters may conceal important intertemporal and uncertainty-dependent constraints. There may exist intermediate, technology-agnostic capability contracts that capture most of the value of full disclosure at significantly lower informational and computational complexity.

This thesis must be tested rather than assumed.

The project must remain valid under three possible outcomes:

1. A compact contract captures most of the full-information value.
2. Only highly expressive contracts approach full-information performance.
3. Conventional generator contracts are already sufficient under broad conditions.

All three are scientifically meaningful outcomes if supported by rigorous experiments and analysis.

⸻

6. Central Research Questions

RQ1 — Contract design

What information should a technology-agnostic capability contract contain?

This question concerns the representation of externally visible capability, not internal technology.

Potential information categories include:

* instantaneous power bounds;
* ramping bounds;
* reserve bounds;
* cumulative energy limits;
* state-dependent future capability;
* uncertainty confidence;
* response duration;
* saturation;
* recovery requirements.

RQ2 — Abstraction gap

How much cost, reliability, and security performance is lost when full internal resource information is replaced by a lower-dimensional capability contract?

This is the main empirical question.

RQ3 — Minimal sufficient interface

What is the least expressive contract class that achieves prescribed cost and reliability tolerances relative to a fully-aware benchmark?

For example, given tolerances:

[
\delta_{\text{cost}}
]

and

[
\epsilon_{\text{risk}},
]

find the least expressive contract class (\mathcal C_k) satisfying:

[
\frac{J(\mathcal C_k)-J(\mathcal C_{\text{full}})}
{J(\mathcal C_{\text{full}})}
\leq
\delta_{\text{cost}}
]

and

[
\Pr(\text{operational violation}\mid \mathcal C_k)
\leq
\epsilon_{\text{risk}}.
]

RQ4 — Realizability under uncertainty

Can a one-shot contract provide a probabilistic guarantee that dispatch and reserve instructions selected by the operator will remain physically realizable under renewable uncertainty?

RQ5 — Fundamental limits

Which operational or security properties cannot be certified through any isolated per-resource one-shot capability contract?

Candidate limits include:

* system-wide small-signal stability;
* correlated multi-resource failure;
* state-dependent feasibility through memoryless contracts;
* interaction-dependent inverter dynamics.

⸻

7. Hypotheses

H1 — Static contracts are insufficient under strong state coupling

When battery energy capacity is small relative to dispatch and reserve requirements, a memoryless generator-style contract will produce higher infeasibility and reserve non-delivery than an intertemporal contract.

H2 — A small amount of intertemporal information has high marginal value

Adding cumulative energy or trajectory-feasibility constraints will recover a large fraction of the reliability and cost performance of a fully-aware scheduler.

H3 — Information value exhibits diminishing returns

The transition:

[
\mathcal C_0 \rightarrow \mathcal C_1
]

may produce a large performance improvement, while:

[
\mathcal C_1 \rightarrow \mathcal C_2 \rightarrow \mathcal C_{\text{full}}
]

may provide progressively smaller gains.

This would create an “elbow” in the abstraction frontier.

H4 — Uncertainty-aware contracts reduce reserve failure

Contracts constructed using renewable uncertainty and reserve conditionality will reduce out-of-sample reserve non-delivery compared with deterministic energy-envelope contracts.

H5 — Some security properties are non-decomposable

No isolated resource-level contract can universally certify network-wide oscillatory stability because stability depends on network topology, operating point, resource location, and controller interactions.

⸻

8. Scope

8.1 First-stage scope

The first-stage study will include:

* one renewable-plus-battery hybrid resource;
* several conventional thermal generators;
* day-ahead unit commitment or economic dispatch;
* energy scheduling;
* upward and downward reserve;
* intertemporal battery state of charge;
* renewable forecast uncertainty;
* one-shot capability declaration;
* out-of-sample real-time realization;
* comparison with a fully-aware benchmark.

8.2 First-stage system

Start with a copper-plate system:

* one electrical bus;
* four to six thermal generators;
* one PV-plus-BESS hybrid;
* one system load;
* hourly day-ahead intervals;
* optional 5-minute real-time realization;
* 24-hour scheduling horizon.

The initial model should be deliberately small enough that every result can be manually inspected.

8.3 Later-stage extensions

Only after the first-stage kill experiment succeeds may the project expand to:

* IEEE 9-bus or IEEE 39-bus systems;
* network congestion;
* locational reserve;
* multiple hybrid resources;
* correlated renewable uncertainty;
* distributed aggregators;
* dynamic frequency-security constraints;
* grid-forming response envelopes;
* current saturation;
* post-contingency recovery;
* TSO–DSO boundary applications;
* data centers and other flexible loads.

⸻

9. Non-Goals

The following are explicitly outside the first-stage contribution.

9.1 No new forecasting model

Forecasting may generate scenarios, but prediction accuracy is not the research contribution.

9.2 No new battery MPC

The internal controller may use optimization or a rule-based dispatch policy, but controller novelty is not required.

9.3 No new GFM or VSG design

The first stage does not design virtual inertia, droop, or grid-forming controllers.

9.4 No claim of first dispatchable hybrid resource

Renewable-plus-storage dispatchability already exists in literature and practice.

9.5 No claim of first flexibility envelope

Time-coupled, uncertainty-aware, and operating-envelope representations already exist.

9.6 No full dynamic simulation in Phase I

The first stage does not require EMT, transient-stability, or small-signal simulation.

9.7 No universal “legacy SCUC” claim

The project should not claim that an entirely unmodified legacy SCUC can consume every contract class.

The safer description is:

technology-agnostic, minimally augmented scheduling

A strict conventional interface may require no formulation changes. More expressive interfaces may require generic additional constraints, but not technology-specific PV, battery, or inverter equations.

9.8 No universal security guarantee

Per-resource capability contracts are not expected to guarantee all system-level dynamic properties.

⸻

10. Conceptual Architecture

The project uses a separation between the operator model and the physical truth model.

10.1 Operator layer

The operator receives a contract:

[
\mathcal C_k
]

and solves a scheduling problem:

[
\min J^{\text{operator}}
]

subject to:

* system power balance;
* thermal-unit constraints;
* reserve requirements;
* contract-specific hybrid constraints.

The operator does not necessarily see:

* battery state;
* renewable scenarios;
* internal charging and discharging;
* internal control logic.

10.2 Resource layer

The physical hybrid contains:

* renewable production;
* battery;
* state of charge;
* internal charging and discharging;
* curtailment;
* reserve activation;
* actual forecast error.

10.3 Evaluation layer

The operator’s schedule is passed to the physical truth model.

The evaluator determines:

* whether dispatch is realizable;
* whether reserve is deliverable;
* whether SOC remains feasible;
* whether real-time imbalance occurs;
* whether recourse is required;
* total realized system cost.

10.4 Key experimental control

The physical truth model must remain identical across all contract classes.

Only the operator-visible information changes.

This is the central fairness requirement of the study.

⸻

11. Physical Truth Model

11.1 Renewable generation

Let:

[
\hat P^{ren}_t
]

be the day-ahead forecast and:

[
P^{ren}_{t,\omega}
]

be the realized renewable output under scenario (\omega).

Forecast error is:

[
\xi_{t,\omega}

P^{ren}_{t,\omega}-\hat P^{ren}_t.
]

Initial experiments may use:

* empirical forecast errors;
* Gaussian or truncated Gaussian errors;
* scenario-based errors;
* temporally correlated errors;
* synthetic cloud-ramp events.

The first implementation should start with a simple transparent model and add correlation later.

11.2 Battery model

Charging and discharging variables:

[
P^{ch}{t,\omega}\geq0,
\qquad
P^{dis}{t,\omega}\geq0.
]

State-of-charge dynamics:

[
E_{t+1,\omega}

E_{t,\omega}
+
\eta_cP^{ch}_{t,\omega}\Delta t

\frac{P^{dis}_{t,\omega}}{\eta_d}\Delta t.
]

Battery limits:

[
0\leq P^{ch}_{t,\omega}\leq \overline P^{ch},
]

[
0\leq P^{dis}_{t,\omega}\leq \overline P^{dis},
]

[
\underline E
\leq
E_{t,\omega}
\leq
\overline E.
]

Simultaneous charging and discharging should either be:

* prohibited through binary variables;
* prevented through complementarity;
* or strongly discouraged through efficiency and cost.

The implementation choice must be documented.

11.3 Hybrid net injection

The hybrid’s net injection is:

[
P^{hyb}_{t,\omega}

P^{ren}{t,\omega}
+
P^{dis}{t,\omega}

P^{ch}_{t,\omega}

P^{curt}_{t,\omega}.
]

11.4 Reserve capability

Upward reserve may come from:

* renewable headroom;
* reduced battery charging;
* additional battery discharge.

Downward reserve may come from:

* renewable curtailment capability;
* increased battery charging;
* reduced battery discharge.

Reserve delivery must be connected to both:

* instantaneous power capability;
* duration-dependent energy capability.

For an upward reserve requirement (R^\uparrow_t) sustained for duration (\tau), battery energy must satisfy an appropriate condition such as:

[
E_t-\underline E
\geq
\frac{R^\uparrow_t\tau}{\eta_d}.
]

This condition may be simplified initially but must not be ignored.

11.5 Internal recourse

The physical truth model may use internal recourse after renewable realization.

Possible recourse actions include:

* battery redispatch;
* curtailment;
* reserve reduction;
* imbalance settlement;
* load shedding as an emergency penalty;
* thermal redispatch, if allowed by the experiment.

The recourse policy should be consistent across contract classes.

⸻

12. Operator Scheduling Model

12.1 Thermal-unit commitment

For thermal generator (g):

[
u_{g,t}\in{0,1}
]

indicates commitment.

Generation:

[
P_{g,t}.
]

Constraints may include:

* minimum and maximum output;
* ramping;
* start-up and shut-down;
* minimum up and down time;
* reserve provision.

The initial model may begin as economic dispatch before adding binary commitment decisions.

12.2 Power balance

[
\sum_g P_{g,t}
+
P^{hyb}_t

D_t.
]

12.3 Reserve requirement

[
\sum_g R^\uparrow_{g,t}
+
R^\uparrow_{hyb,t}
\geq
R^\uparrow_{sys,t},
]

[
\sum_g R^\downarrow_{g,t}
+
R^\downarrow_{hyb,t}
\geq
R^\downarrow_{sys,t}.
]

12.4 Objective

A generic objective is:

[
\min
\sum_t
\left[
\sum_g
\left(
C_g(P_{g,t})
+
C_g^{SU}y_{g,t}
+
C_g^{SD}z_{g,t}
\right)
+
C^{res}_t
+
C^{hyb}_t
\right].
]

Out-of-sample evaluation should add realized penalties for:

* imbalance;
* reserve non-delivery;
* curtailment;
* load shedding;
* emergency redispatch;
* battery degradation, if modelled.

⸻

13. Capability-Contract Hierarchy

The hierarchy should be nested whenever possible:

[
\mathcal C_0
\preceq
\mathcal C_1
\preceq
\mathcal C_2
\preceq
\mathcal C_{\text{full}}.
]

The symbol (\preceq) means that the later contract is at least as expressive as the earlier contract.

The initial project should use “nested hierarchy” or “partially ordered family,” not “formal lattice,” unless lattice properties are later proven.

⸻

13.1 Contract (C_0): Static generator-style contract

The operator sees only conventional resource parameters.

Possible fields:

[
P^{\min}_t,
\quad
P^{\max}_t,
\quad
RU_t,
\quad
RD_t,
\quad
R^\uparrow_t,
\quad
R^\downarrow_t.
]

Characteristics:

* approximately memoryless;
* no explicit SOC;
* no cumulative energy limit;
* no renewable scenario model;
* no explicit reserve-duration guarantee.

Purpose:

* represent the conventional abstraction baseline;
* demonstrate when static capability overstates future feasibility.

Important design choice:

The parameters must be generated using a documented rule. They must not be chosen arbitrarily to make (C_0) fail.

Potential constructions include:

* forecast-based available power;
* conservative quantile bounds;
* historical derating;
* resource-provided nominal limits.

⸻

13.2 Contract (C_1): Intertemporal capability contract

(C_1) adds generic time-coupled information without revealing the battery model.

Possible representations include:

Cumulative-energy envelope

For every interval ([1,t]):

[
\underline Q_t
\leq
\sum_{\tau=1}^{t}
P^{hyb}_\tau\Delta t
\leq
\overline Q_t.
]

Trajectory polytope

[
A P^{hyb}
\leq
b.
]

Energy-state envelope

[
\underline E_t
\leq
E^{virtual}_t
\leq
\overline E_t.
]

The operator may use a generic virtual-energy state without knowing that the internal technology is a battery.

Characteristics:

* captures intertemporal feasibility;
* remains technology-agnostic;
* does not reveal renewable scenarios;
* may still be deterministic.

Primary question:

How much performance is recovered by adding only time coupling?

⸻

13.3 Contract (C_2): Uncertainty-aware reserve-realizability contract

(C_2) adds uncertainty information and probabilistic delivery semantics.

Possible guarantee:

[
\Pr_\xi
\left[
\text{scheduled energy and reserve are realizable}
\right]
\geq
1-\epsilon.
]

The contract may include:

* confidence level (\epsilon);
* uncertainty-adjusted power envelope;
* uncertainty-adjusted cumulative-energy envelope;
* reserve-duration conditions;
* scenario-based inner approximation;
* robust or chance-constrained feasible region.

A stronger set-level interpretation is:

For any operator schedule contained in the declared contract set, an internal feasible policy exists with probability at least (1-\epsilon).

This interpretation is more valuable than guaranteeing one preselected dispatch trajectory, but it is also more technically difficult.

The first implementation may begin with a weaker schedule-specific probabilistic guarantee, then determine whether a set-level guarantee is tractable.

⸻

13.4 Contract (C_3): Dynamic-response contract

This is not required in Phase I.

A later contract may add a response envelope:

[
\underline{\Delta P}(\tau)
\leq
\Delta P(\tau)
\leq
\overline{\Delta P}(\tau),
]

with:

* response delay;
* ramp rate;
* maximum amplitude;
* sustain duration;
* current saturation;
* energy recovery;
* availability probability.

This should describe externally guaranteed behaviour rather than expose controller parameters such as exact virtual inertia or droop gains.

⸻

13.5 Contract (C_{\text{full}}): Fully-aware benchmark

The operator sees the full relevant hybrid model:

* renewable forecast scenarios;
* renewable probability distribution;
* initial SOC;
* battery power limits;
* battery energy limits;
* charging and discharging efficiencies;
* curtailment;
* reserve activation logic;
* internal operating constraints;
* scenario-dependent recourse.

This is not expected to be the practical solution.

It is the performance benchmark against which abstraction loss is measured.

⸻

14. Benchmarks

The study should include at least three endpoint benchmarks.

Benchmark A — Static one-shot interface

Contract (C_0).

Benchmark B — Fully-aware centralized scheduling

Contract (C_{\text{full}}).

Benchmark C — Iterative or full-exchange coordination

Optional in the first version, but valuable as a second endpoint.

This benchmark may represent:

* repeated exchange of boundary schedules and constraints;
* distributed optimization;
* resource-operator iterative coordination;
* near-full-information convergence.

The purpose is not to claim iterative methods are impractical in all settings. The purpose is to distinguish:

* one-shot standardized market participation;
* iterative coordination regimes.

⸻

15. Meaning of “One-Shot”

A one-shot capability contract is submitted before market clearing and consumed by the scheduling model without repeated resource-specific negotiation.

Conceptually:

[
\text{resource submits contract}
\rightarrow
\text{market clears}
\rightarrow
\text{dispatch is issued}.
]

This restriction is relevant because real scheduling and market processes often require:

* standardized offers;
* reproducibility;
* auditability;
* equal treatment;
* bounded clearing time;
* gaming oversight;
* limited communication complexity.

The project must not claim iterative coordination is impossible.

The correct distinction is:

Iterative coordination solves a different institutional and computational regime. Chameleon asks what can be achieved when each resource must submit a standardized one-shot representation before clearing.

⸻

16. Abstraction Gap

For contract class (\mathcal C_k), define cost gap:

[
G^{cost}_k

\frac{
J_k-J_{\text{full}}
}{
J_{\text{full}}
}.
]

Possible realized-cost definition:

[
J_k

J^{DA}k
+
\mathbb E\omega
\left[
J^{RT}_{k,\omega}
\right].
]

Reliability gap may include:

[
G^{fail}_k

\Pr_\omega
\left(
\text{dispatch or reserve is not deliverable}
\right).
]

Additional gaps may include:

* expected imbalance;
* expected unserved energy;
* expected reserve shortfall;
* SOC-violation frequency;
* curtailment;
* thermal start-ups;
* battery throughput;
* solve time;
* model size;
* number of contract constraints;
* number of disclosed quantities.

The abstraction gap should not be reduced to one scalar too early.

The primary output should be a multi-objective frontier.

⸻

17. Minimal Sufficient Contract

Given target tolerances:

[
\delta
]

for cost and:

[
\epsilon
]

for reliability, define:

[
\mathcal C^*

\min_{\preceq}
\left{
\mathcal C_k:
G^{cost}_k\leq\delta,
\quad
G^{fail}_k\leq\epsilon
\right}.
]

The minimum is taken with respect to contract expressiveness, not raw parameter count alone.

A possible practical interpretation:

The least expressive contract class whose out-of-sample performance is statistically indistinguishable from the fully-aware benchmark within predefined tolerances.

⸻

18. Experimental Design

18.1 Base system

Initial system:

* 24-hour horizon;
* hourly day-ahead decisions;
* optional 5-minute real-time realization;
* four to six thermal generators;
* one load profile;
* one PV-plus-BESS hybrid;
* system reserve requirement;
* no network constraints.

18.2 Main experimental factors

Vary:

Renewable penetration

* low;
* moderate;
* high.

Battery duration

* 0.5 hour;
* 1 hour;
* 2 hours;
* 4 hours.

Forecast uncertainty

* low;
* moderate;
* high;
* ramp-event stress cases.

Reserve requirement

* low;
* moderate;
* high.

Initial SOC

* low;
* medium;
* high.

Correlation

Initially no cross-resource correlation because there is one hybrid.

Later:

* multiple hybrids;
* correlated forecast errors.

Contract conservatism

* nominal;
* quantile-based;
* robust;
* chance-constrained.

18.3 Monte Carlo evaluation

For every day-ahead solution:

1. solve the operator scheduling problem;
2. generate many out-of-sample renewable realizations;
3. apply the same internal recourse policy;
4. record feasibility and realized cost;
5. compare contract classes.

Training or contract-construction scenarios must be separated from evaluation scenarios.

18.4 Stress tests

Include deliberately difficult events:

* rapid evening solar decline;
* prolonged forecast overestimation;
* prolonged forecast underestimation;
* high reserve activation during low SOC;
* repeated reserve calls;
* battery near energy limits;
* high-load ramp;
* renewable common-mode ramp in later multi-resource studies.

⸻

19. Metrics

19.1 Economic metrics

* day-ahead production cost;
* realized total operating cost;
* start-up and shut-down cost;
* reserve procurement cost;
* real-time balancing cost;
* curtailment cost;
* load-shedding penalty;
* gap to fully-aware benchmark.

19.2 Reliability metrics

* dispatch non-delivery probability;
* upward reserve shortfall probability;
* downward reserve shortfall probability;
* expected reserve shortfall;
* energy imbalance;
* SOC violation count;
* unserved energy;
* emergency redispatch frequency.

19.3 Resource metrics

* renewable curtailment;
* battery throughput;
* battery cycling;
* end-of-horizon SOC deviation;
* reserve utilization;
* headroom utilization.

19.4 Complexity metrics

* model variable count;
* model constraint count;
* binary variable count;
* solve time;
* contract dimension;
* amount of resource information disclosed;
* contract-construction time.

19.5 Later security metrics

Reserved for later phases:

* frequency nadir;
* rate of change of frequency;
* reserve activation delay;
* response saturation;
* small-signal damping ratio;
* dynamic-security violation rate.

⸻

20. Primary Figures

The first paper should be designed around a small set of high-value figures.

Figure 1 — Chameleon architecture

Show:

[
\text{Physical truth model}
\rightarrow
\text{contract generator}
\rightarrow
\text{operator scheduling}
\rightarrow
\text{real-time evaluation}
]

with internal technology hidden from the operator.

Figure 2 — Contract hierarchy

Show:

[
C_0
\rightarrow
C_1
\rightarrow
C_2
\rightarrow
C_{\text{full}}
]

and what information is added at each level.

Figure 3 — Abstraction frontier

Horizontal axis:

* contract expressiveness or disclosure.

Vertical axes or panels:

* cost gap;
* failure probability;
* solve time.

The desired result is an identifiable elbow.

Figure 4 — Failure mechanism

Illustrate why a static contract fails:

* operator schedules energy;
* operator also schedules reserve;
* SOC becomes exhausted;
* reserve cannot be delivered.

Figure 5 — Out-of-sample reliability

Plot reserve shortfall or dispatch failure across:

* uncertainty;
* battery duration;
* contract class.

Figure 6 — Value of intertemporal information

Show the marginal improvement:

[
C_0\rightarrow C_1
]

separately from:

[
C_1\rightarrow C_2.
]

⸻

21. Kill Criteria

The first-stage experiment is explicitly a kill experiment.

Kill Condition A — No meaningful abstraction gap

If:

[
C_0\approx C_{\text{full}}
]

across realistic uncertainty, storage duration, and reserve conditions, then the conventional generator contract may already be sufficient for the target setting.

The project should not artificially increase difficulty merely to create a result.

Kill Condition B — No compact sufficient abstraction exists

If only near-full disclosure achieves acceptable reliability and cost, then the hypothesis that a compact contract is sufficient is rejected.

This may still support a negative result, but the practical contract-design contribution weakens.

Kill Condition C — Contract advantage depends on artificial assumptions

If improvements occur only under unrealistic penalties, extreme forecast errors, or hand-selected battery parameters, the result is not robust.

Kill Condition D — Existing work already reproduces the same comparison

If a newly discovered paper already defines the same contract classes and common-truth-model abstraction frontier, the project must pivot again.

Success Pattern A — Clear elbow

The strongest result would be:

* (C_0) has substantial failure or cost gap;
* (C_1) recovers most value;
* (C_2) improves reliability further;
* full disclosure adds limited marginal value.

Success Pattern B — Conditional sufficiency map

A useful result may also be:

Static contracts are sufficient when battery duration and uncertainty lie in one region, while richer contracts are necessary outside it.

This would produce a regime map rather than one universal answer.

Success Pattern C — Strong negative boundary

Another valid result is:

No compact one-shot contract achieves both low cost and low failure under specified uncertainty and reserve conditions.

This would establish an abstraction limit.

⸻

22. Impossibility and Boundary Results

These results should begin as propositions or counterexamples, not grand theorem claims.

22.1 Memoryless contract limitation

Construct two physical resource states with identical current power bounds but different SOC.

If the operator receives the same memoryless contract for both states, it may issue the same schedule even though only one state can sustain it.

This demonstrates that a state-free interface cannot universally characterize time-coupled feasibility.

22.2 Reliability non-composability

For multiple resources, show that:

[
\Pr(A_i)\geq1-\epsilon_i
]

for every resource does not imply a desired bound on:

[
\Pr\left(\bigcap_i A_i\right)
]

without assumptions on dependence.

Under strongly correlated renewable uncertainty, simultaneous non-delivery may remain high.

22.3 Dynamic-security non-decomposability

Show conceptually or mathematically that system eigenvalues depend on the combined system matrix:

[
A_{sys}

f(
A_{network},
A_{resources},
A_{controllers},
x_{operating}
).
]

Therefore, isolated per-resource response parameters cannot universally certify system-wide oscillatory stability.

These results should be framed as the boundary of Chameleon rather than a failure of the project.

⸻

23. Implementation Strategy

23.1 Phase 0 — Reproducible skeleton

Build:

* configuration system;
* deterministic random seeds;
* solver abstraction;
* data validation;
* logging;
* experiment registry;
* unit tests.

23.2 Phase 1 — Deterministic dispatch model

Implement:

* thermal economic dispatch;
* hybrid truth model;
* battery SOC;
* deterministic renewable forecast;
* (C_0);
* (C_{\text{full}}).

Purpose:

* verify basic model consistency;
* create manually checkable test cases.

23.3 Phase 2 — Intertemporal contract

Implement (C_1):

* cumulative energy bounds;
* trajectory polytope or virtual-energy state;
* contract generation from truth model;
* operator-side generic constraints.

23.4 Phase 3 — Uncertainty and recourse

Implement:

* renewable scenarios;
* out-of-sample Monte Carlo;
* real-time battery recourse;
* imbalance and reserve penalties;
* reliability metrics.

23.5 Phase 4 — Uncertainty-aware contract

Implement (C_2):

* quantile-based envelopes;
* robust inner approximation;
* scenario-based chance constraints;
* reserve-duration feasibility.

23.6 Phase 5 — Experiment sweep

Sweep:

* renewable penetration;
* battery duration;
* uncertainty;
* reserve requirement;
* initial SOC;
* contract confidence.

23.7 Phase 6 — Analysis and figures

Produce:

* abstraction frontier;
* regime maps;
* stress-case trajectories;
* sensitivity tables;
* statistical uncertainty intervals.

23.8 Phase 7 — Optional network extension

Only after Phase I success:

* DC power flow;
* IEEE test system;
* locational effects;
* multiple hybrids.

⸻

24. Proposed Repository Structure

chameleon/
├── README.md
├── PROJECT_BLUEPRINT.md
├── LITERATURE.md
├── ROADMAP.md
├── pyproject.toml
├── configs/
│   ├── base.yaml
│   ├── systems/
│   ├── resources/
│   ├── contracts/
│   └── experiments/
├── data/
│   ├── raw/
│   ├── processed/
│   └── synthetic/
├── src/
│   └── chameleon/
│       ├── systems/
│       │   ├── thermal.py
│       │   ├── load.py
│       │   └── copper_plate.py
│       ├── resources/
│       │   ├── renewable.py
│       │   ├── battery.py
│       │   └── hybrid.py
│       ├── contracts/
│       │   ├── base.py
│       │   ├── static.py
│       │   ├── intertemporal.py
│       │   ├── stochastic.py
│       │   └── full_information.py
│       ├── optimization/
│       │   ├── dispatch.py
│       │   ├── unit_commitment.py
│       │   ├── reserve.py
│       │   └── recourse.py
│       ├── scenarios/
│       │   ├── renewable_errors.py
│       │   └── sampling.py
│       ├── evaluation/
│       │   ├── feasibility.py
│       │   ├── reliability.py
│       │   ├── cost.py
│       │   └── abstraction_gap.py
│       ├── experiments/
│       │   ├── runner.py
│       │   ├── sweeps.py
│       │   └── registry.py
│       └── visualization/
│           ├── frontier.py
│           ├── trajectories.py
│           └── regime_maps.py
├── scripts/
│   ├── run_baseline.py
│   ├── run_monte_carlo.py
│   ├── run_sweep.py
│   └── make_figures.py
├── tests/
│   ├── test_battery.py
│   ├── test_contracts.py
│   ├── test_dispatch.py
│   ├── test_recourse.py
│   └── test_reproducibility.py
├── notebooks/
│   ├── 01_sanity_checks.ipynb
│   ├── 02_contract_comparison.ipynb
│   └── 03_abstraction_frontier.ipynb
└── results/
    ├── raw/
    ├── tables/
    └── figures/

⸻

25. Coding Principles

25.1 Truth model and operator model must be separated

Never allow operator-side code to access hidden truth-model parameters unless the experiment uses (C_{\text{full}}).

25.2 Contracts must be serializable

Each contract should be exportable as a standalone structured object, such as JSON or YAML.

The contract object should contain only operator-visible information.

25.3 Every contract needs explicit semantics

For each field, document:

* physical meaning;
* units;
* time resolution;
* guarantee type;
* confidence level;
* duration;
* assumptions.

25.4 No hidden hand-tuning

Contract parameters must be generated by reproducible algorithms.

25.5 Every optimization model needs feasibility checks

After solving, independently verify:

* power balance;
* SOC dynamics;
* reserve constraints;
* contract satisfaction;
* integrality;
* numerical tolerance.

25.6 Small examples before large sweeps

Every new model component must first pass a manually inspectable example.

25.7 Reproducibility

Every reported result must include:

* configuration;
* random seed;
* solver;
* solver version;
* optimality gap;
* runtime;
* code commit.

⸻

26. Data Strategy

The first stage does not require a large proprietary dataset.

Possible inputs:

* synthetic load profile;
* public system load profile;
* public solar profile;
* generated forecast-error scenarios;
* standard thermal-generator test data.

The priority is transparent causal experiments rather than data volume.

Later empirical validation may use:

* CAISO load and renewable data;
* NREL solar profiles;
* public battery and hybrid-resource parameters;
* actual day-ahead and real-time forecast errors.

Forecasting should remain modular so that the study can swap:

* synthetic uncertainty;
* empirical residuals;
* probabilistic forecast scenarios.

⸻

27. Statistical Evaluation

Out-of-sample results should report uncertainty.

For each contract class, estimate:

* mean realized cost;
* confidence interval;
* reserve failure probability;
* confidence interval for failure probability;
* expected shortfall;
* tail quantiles;
* conditional value at risk, if useful.

Use enough scenarios that differences between contract classes are statistically meaningful.

Avoid reporting only one “representative day.”

Possible methods:

* bootstrap confidence intervals;
* Wilson intervals for failure probability;
* paired scenario comparisons;
* common random numbers across contracts.

Using the same renewable realization scenarios for all contract classes will reduce comparison noise.

⸻

28. Contribution Claims

The project should aim for carefully bounded claims.

Candidate Contribution 1

A nested family of one-shot, technology-agnostic capability contracts for renewable-storage hybrid scheduling.

Candidate Contribution 2

A common-truth-model methodology for quantifying economic and reliability abstraction gaps between contract classes and fully-aware scheduling.

Candidate Contribution 3

A quantified abstraction frontier identifying the least expressive contract class that satisfies prescribed cost and reliability tolerances under specified conditions.

Candidate Contribution 4

An uncertainty-aware, reserve-conditional realizability formulation for renewable-storage capability contracts.

Candidate Contribution 5

Counterexamples or limit results showing which properties cannot be certified through memoryless or isolated per-resource contracts.

Claims must not use “first” unless the final literature review supports it at submission time.

⸻

29. Expected Negative Results

The project should actively look for cases where abstraction fails.

Expected failure modes include:

* insufficient energy after sustained reserve commitments;
* renewable forecast overestimation;
* low initial SOC;
* repeated reserve activation;
* static power limits that ignore future depletion;
* overconservative uncertainty-aware envelopes;
* hidden cost caused by conservative abstraction;
* full-aware scheduling outperforming contracts during rare extreme events.

Negative results should be treated as evidence about the limits of standardized interfaces.

⸻

30. Paper Structure

1. Introduction

* increasing resource heterogeneity;
* incompatibility between full technology-specific modelling and overly simple generator abstractions;
* one-shot market interface;
* research questions;
* contributions.

2. Related Work

Organize by problem solved:

* dispatchable renewable-storage resources;
* dynamic virtual power plants;
* hybrid-resource market participation;
* aggregate flexibility and realizability;
* TSO–DSO flexibility regions;
* privacy-preserving and iterative coordination;
* frequency-aware scheduling.

End with the exact gap:

Existing work provides many individual capability representations, but does not systematically quantify the cost and reliability loss across an ordered family of one-shot contracts using one common physical truth model.

3. Problem Formulation

* system model;
* hybrid truth model;
* uncertainty;
* reserve;
* operator scheduling;
* one-shot information structure.

4. Capability Contracts

* (C_0);
* (C_1);
* (C_2);
* (C_{\text{full}});
* ordering and semantics.

5. Abstraction-Gap Framework

* cost gap;
* reliability gap;
* complexity;
* minimal sufficient contract;
* evaluation methodology.

6. Case Study

* copper-plate test system;
* parameter ranges;
* scenarios;
* stress tests;
* solver and implementation.

7. Results

* baseline;
* abstraction frontier;
* sensitivity;
* failure cases;
* regime maps;
* computational complexity.

8. Limits of Capability Contracts

* memoryless limitation;
* correlation;
* non-decomposable security;
* interpretation.

9. Conclusion

* what information mattered;
* where abstraction was sufficient;
* where it failed;
* implications for future market interfaces.

⸻

31. Roadmap

Milestone 1 — Model sanity

Deliverables:

* deterministic copper-plate dispatch;
* thermal generators;
* PV+BESS truth model;
* validated SOC equations;
* full-information benchmark.

Exit criterion:

All constraints independently verified on small cases.

Milestone 2 — Static abstraction

Deliverables:

* (C_0);
* operator schedule using only static parameters;
* truth-model evaluation;
* first failure example.

Exit criterion:

A reproducible case where static abstraction succeeds or fails for understood reasons.

Milestone 3 — Intertemporal abstraction

Deliverables:

* (C_1);
* generic energy envelope;
* comparison with (C_0) and full-aware benchmark.

Exit criterion:

Quantified marginal value of intertemporal information.

Milestone 4 — Uncertainty

Deliverables:

* renewable scenarios;
* out-of-sample simulation;
* Monte Carlo evaluation;
* reserve non-delivery metrics.

Exit criterion:

Stable and reproducible reliability estimates.

Milestone 5 — Stochastic contract

Deliverables:

* (C_2);
* uncertainty-adjusted capability;
* confidence calibration;
* comparison across uncertainty levels.

Exit criterion:

Observed relationship between declared confidence and actual out-of-sample reliability.

Milestone 6 — Abstraction frontier

Deliverables:

* main figures;
* sensitivity sweeps;
* regime maps;
* kill-condition assessment.

Exit criterion:

Clear decision: continue, pivot, or stop.

Milestone 7 — Paper-scale extension

Only after Milestone 6:

* unit commitment;
* larger system;
* network constraints;
* multiple hybrids;
* formal propositions.

⸻

32. Decision Gates

Gate 1 — After deterministic comparison

Question:

Does static abstraction create a meaningful and understandable difference from full awareness?

If no, revise the setting or reconsider the project.

Gate 2 — After (C_1)

Question:

Does intertemporal information recover meaningful value?

If no, determine whether:

* static contracts are sufficient;
* the chosen envelope is poor;
* uncertainty rather than time coupling is the real issue.

Gate 3 — After Monte Carlo

Question:

Are contract differences robust out of sample?

If results depend on a few scenarios, do not scale the project.

Gate 4 — Before dynamic extension

Question:

Has the energy-reserve abstraction framework already produced a coherent paper-level result?

If no, do not add frequency dynamics merely to make the system look more sophisticated.

⸻

33. Instructions for Codex

Codex should treat this Blueprint as authoritative.

Codex should do

* formalize the mathematical models;
* identify ambiguous definitions;
* propose multiple valid formulations;
* implement reproducible optimization code;
* write unit tests;
* validate constraints;
* construct synthetic test systems;
* automate parameter sweeps;
* run Monte Carlo experiments;
* generate tables and figures;
* document assumptions;
* maintain literature comparison tables;
* flag when an implementation departs from the Blueprint.

Codex should not do

* redefine the research contribution;
* replace the contract problem with a controller-design problem;
* add GFM, EMT, or IEEE 39-bus complexity before the first kill experiment;
* claim novelty based on architecture alone;
* silently expose truth-model information to abstracted scheduling models;
* tune contract parameters separately for each evaluation scenario;
* choose only favourable cases;
* treat prediction accuracy as the central metric;
* assume a positive result in advance.

Codex must ask, before every major addition

1. Does this help answer the abstraction-gap question?
2. Does it change only operator-visible information, or does it accidentally change the physical system?
3. Is this already solved in the literature?
4. Is this required for the first-stage kill experiment?
5. Could the result be explained with a smaller model?

⸻

34. Immediate Next Tasks

The first Codex assignment should not be “build the entire project.”

It should be:

Task 1 — Formal model memo

Produce a technical memo defining:

* deterministic copper-plate dispatch;
* thermal generators;
* PV+BESS truth model;
* reserve;
* (C_0);
* (C_1);
* (C_{\text{full}});
* out-of-sample realization;
* all variables, parameters, constraints, and units.

The memo should explicitly distinguish:

* operator-visible variables;
* hidden truth-model variables;
* contract-generation variables;
* real-time recourse variables.

Task 2 — Small counterexample

Construct the smallest numerical example showing why a memoryless generator contract can schedule energy and reserve that a state-coupled hybrid cannot deliver.

The example should be manually verifiable.

Task 3 — Repository skeleton

Create the proposed repository structure, configuration system, tests, and deterministic baseline.

Task 4 — Contract alternatives

Propose at least three mathematically valid versions of (C_1):

* cumulative-energy envelope;
* virtual battery;
* trajectory polytope.

Compare:

* expressiveness;
* complexity;
* ease of SCUC integration;
* literature precedent;
* suitability for Phase I.

No large experiment should begin until these four tasks are reviewed.

⸻

35. Final Project Statement

Project Chameleon investigates how complex, stateful, and uncertain grid resources can participate in scheduling through standardized, technology-agnostic capability interfaces.

Its purpose is not to hide complexity for its own sake.

Its purpose is to determine:

* which internal details the operator truly needs;
* which details can be abstracted safely;
* how much economic and reliability performance is lost through abstraction;
* when richer information stops providing meaningful value;
* which system properties cannot be certified through per-resource contracts at all.

The project’s guiding question is:

How much must a grid resource reveal?

The first-stage objective is deliberately narrower:

For a renewable-storage hybrid providing energy and reserve, how much intertemporal and uncertainty information must be added to a conventional generator-style offer before scheduling performance approaches a fully-aware benchmark?

The project should proceed from small to large:

[
\text{counterexample}
\rightarrow
\text{copper-plate model}
\rightarrow
\text{contract hierarchy}
\rightarrow
\text{abstraction frontier}
\rightarrow
\text{network extension}
\rightarrow
\text{dynamic capability}.
]

The first responsibility is not to prove Chameleon works.

The first responsibility is to determine honestly whether a compact capability interface is meaningful, sufficient, and worth building.