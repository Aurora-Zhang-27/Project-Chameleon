# Chameleon research report

Research status as of 2026-10-12; English publication edition, 2026-10-14. Author: Aurora (Yin Zhang). Advisor: Yize Chen. Full working history remains in the local research directory; earlier public material is indexed in [ARCHIVE.md](ARCHIVE.md).

The question is whether a heterogeneous fleet of bidirectional storage devices can fulfil a precommitted aggregate power interval at every period, starting from a specified energy state. Every requested value must be matched exactly, using only information already observed. We ask when this membership problem can be solved both exactly and efficiently.

## 1. Origin and scope

The July–August 2026 version studied how much internal information flexible resources should disclose to an external dispatcher. Advisor questions about the precise set, research gap and measurable benefit led to a narrower repeated-dispatch problem. A single-device gate showed that dynamic power limits plus an internal policy sufficed, undermining the stronger disclosure claim; that recursion was standard. Literature checks on 2026-09-24 covered the earlier candidate directions.

On 2026-09-25, the project turned to algorithmic complexity. Discharge-only fleets have existing exact results, while bidirectional causal operation is less settled. Known exact methods include endpoint-request trees and successive polyhedral projection. The former is exponential in the horizon; neither has a general polynomial guarantee for this problem. The resulting questions were the representation complexity of viable initial states and whether fixed fleet size allows avoiding horizon-exponential computation.

## 2. Model and method

For device i, e_i∈[0,E_i], p_i∈[−C_i,D_i], and e⁺=e−p. Discharge is positive; losses and operating-mode constraints are excluded. At time t the observed request is any y_t∈[l_t,u_t], and Σp_i must equal y_t. Policies may depend on the initial state and observed request history, never future requests.

The viability kernel K_t contains states from which every remaining commitment can be delivered causally. With P_y={p∈[−C,D]:Σp=y},

    K_T=[0,E],
    K_t=[0,E]∩(K_{t+1}+P_{l_t})∩(K_{t+1}+P_{u_t}).

Convexity makes endpoint testing sufficient; this is a known lemma. An endpoint tree provides an exact mathematical LP benchmark with 2^T leaves, although its numerical solver still requires care. Our proposed compact representation maintains upper and lower sums for each device subset. General claims are justified by proofs; rational certificates validate important lemmas and counterexamples. Floating-point searches are evidence only. Counterexamples distinguish failure of a synthetic closure route, failure of the tight-bound invariant in a real recursion, and actual non-subset facets.

## 3. Research progression

| Date | Work | Outcome |
|---|---|---|
| September 25 | Structural conjectures and two-device analysis | A three-device example refuted g-polymatroid structure; N=2 yielded an exact six-bound recursion |
| September 28 | Sandwich theorem and explicit single-request description | Theorem 4: N≤3 exact; Example B: N=4 failure |
| September 29 | Independent audit and formula-level literature checks | No mathematical error found; no precedent found in checked sources |
| October 7–9 | Homogeneous fleets and sandwich experiments | Theorem H: arbitrary homogeneous fleet size; Example C: three types can fail; conservative participation-factor inner test |
| October 10 | Targeted two-type searches and enlarged templates | Example D: two types can fail; coefficient-2 facets; {0,±1} templates improve the outer approximation but remain inexact |
| October 11–12 | Single-state affine test and further literature checks | Strong empirical acceptance, exact affine failure certificate, full-power exact regime, and more precise source attribution |

## 4. Results

### 4.1 Proven exact regimes

| Regime | Representation and arithmetic cost | Basis |
|---|---|---|
| One device | Energy interval, O(T) | Known |
| Two or three devices, arbitrary parameters | At most 14 subset bounds, O(T) | Theorem 4, independently reviewed |
| m identical devices, arbitrary initial energies | 2m sorted partial-sum bounds, O(mT) | Theorem H, independently reviewed; priority unconfirmed |
| At most three proportional groups with equal within-group energy fractions | Aggregate each group, then apply Theorem 4 | Proposition 5; a sufficient condition |
| C_i≥E_i and D_i≥E_i for every device | Total-energy interval, O(T) | Direct proof in the method document |

All arithmetic-complexity statements are distinct from bit complexity. Polynomial bit bounds require explicitly encoded rational inputs. Grouping also has preprocessing and online allocation costs.

The three/four-device boundary arises from mixed-sign inequalities e(A)−e(B) after cancelling shared devices M. If A and B are both nonempty and N≤3, their complement has at most one device; only the empty and full choices of M exist, and both inequalities are redundant. With four devices an intermediate M can impose a new, necessary constraint.

### 4.2 General heterogeneous fleets

Exact rational counterexamples show that subset bounds fail for four heterogeneous devices (Example B), three device types (Example C), and even two types with unequal within-type states (Example D). Positive-power perturbations preserve these failures. Real four-device kernels can have a facet proportional to (−1,0,0,2), so all {0,±1} directions are also insufficient.

A practical single-state workflow is:

1. Reject states excluded by a certified outer bound.
2. Accept when a history-dependent lifted-affine LP supplies a rationally certified policy.
3. Use an endpoint tree or another exact method when unresolved.

Affine rejection excludes only that policy class. In the historical sample collection, no tree-feasible state was missed by the floating-point affine test, but strict certification leaves 101 float-only acceptances and 3 affine rejections unresolved by that test: 104/211,063, about 0.049%. The publication returns the repaired fractional coefficients actually checked. Short-horizon tree LPs can be faster; at longer horizons affine solving is much faster in the measured examples.

The affine class is not generally exact. A rational four-device, four-period example has max_K₀(e₄−e₁)=9/20 versus 2/5 for the lifted-affine feasible set. The failure persists after replacing zero powers by 1/100. Only one of 788 numerically certified geometry instances failed the historical vertex test, but this is distribution-dependent evidence, not a theorem.

### 4.3 Refuted conjectures

- Every kernel is a g-polymatroid.
- Every subset-sum polytope is closed under the predecessor operation.
- Subset bounds are exact for arbitrary fleet size or every two-type fleet.
- Facet directions always have coefficients in {0,±1}.
- Affine or positive/negative lifted-affine policies always suffice.

### 4.4 Literature position

No precedent was found in the checked sources for the explicit single-request formula, the N≤3/N=4 boundary, Theorem 4 and Example B, Theorem H, Example D, the coefficient-2 facet certificates, or the systematic multi-device affine tests and exact failure certificate. This is a scoped search result, not an absolute priority claim.

Known tools include the endpoint lemma and kernel recursion, sandwich/separation theorems and vector convolution, the universal balancing policy for proportional fleets (Evans 2019), and affine/lifted decision rules. Single-battery affine exactness has related existing results. Xie & Chen already observed equality of affine and exact objective values in six numerical examples.

Guo et al. (IEEE TPS 2022) give exact successive polyhedral projection without a polynomial guarantee. Frank–Tardos (1988) provides the real separation theorem and box-intersection formula; Murota (1998) gives the integer separation theorem. Zhai-group papers checked in full concern exact single-storage conditions or sufficient multi-storage conditions, rather than the exact heterogeneous aggregate kernel here. Unavailable books and partial reading remain explicitly identified in the [literature record](complexity_20260925/LITERATURE_CHECK_20260929.md).

## 5. Open questions retained at closure

1. Conditions guaranteeing affine-policy exactness; candidates include N≤3, identical devices and full one-period reachability.
2. Whether primitive integer facet coefficients or the number of directions grow unboundedly with T for N≥4. A coefficient-3 example alone would not establish unbounded growth.
3. Polynomial-time exact single-state membership or a complexity lower bound for heterogeneous N≥4. Unbounded facet directions alone would not prove hardness.
4. Losses and mutually exclusive charging/discharging.
5. Exact subset representation for m identical devices plus one different device.
6. Remaining priority checks in unavailable books and related citation chains.

Research has stopped here. A possible future paper could combine exact regimes, counterexamples and certified affine membership experiments, but no further investigation is committed by this release.

## 6. Lessons and document index

Use exact witnesses rather than random point checks for structural claims. Test at N+1 before extrapolating in dimension. Retry surprising floating-point infeasibility through another formulation or without presolve, then verify a rational witness. Zero observed counterexamples can reflect rarity; inspect formulas and tables before making novelty claims.

See the [document index](complexity_20260925/README.md) for complete proofs, counterexample mechanisms, experiments, independent reviews and retained certificate scripts. Historical large searches remain outside the minimal publication; aggregate outputs and provenance hashes are in `results/`.
