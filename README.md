# Project Chameleon — causal storage deliverability

Minimal runnable package and research results, updated 2026-10-14. Research has stopped at the scope recorded here; unresolved questions remain open.

Given heterogeneous lossless storage devices and an interval of aggregate power requests at each period, decide whether an initial energy state admits a causal policy that fulfils every allowed request sequence. This package contains exact recursions for proven regimes, rational counterexample certificates, and a certified affine-policy inner test.

## Model and results

Device energy is e_i∈[0,E_i], power is p_i∈[−C_i,D_i], and e⁺=e−p, with Σp_i=y_t∈[l_t,u_t]. An action may use current and past requests, but not future requests. The model is lossless and allows cross-charging between devices; period duration is absorbed into the power limits. Losses and mutually exclusive operating modes are outside these results.

| Regime | Result |
|---|---|
| N≤3, arbitrary parameters | Exact rational recursion; at most 14 subset bounds, O(T) arithmetic operations; independently reviewed |
| One device type, arbitrary m and initial state | Exact 2m sorted partial-sum bounds, O(mT); independently reviewed |
| C_i≥E_i and D_i≥E_i | Exact total-energy interval recursion, O(T) |
| At most 3 proportional groups with equal energy fractions within each group | Exact after aggregation; a sufficient condition |
| General heterogeneous N≥4 | Subset bounds and the {0,±1} template can fail; rational certificates include two-type examples and coefficient-2 facets |
| History-dependent affine policies lifted into positive/negative request parts | O(NT²) LP variables; certified acceptance is safe, rejection only excludes the policy class; exact failure certificate included |

Growth of facet directions and polynomial-time exact heterogeneous membership remain open. Novelty means only that no precedent was found in the checked sources. Affine decision rules and the universal balancing policy for proportional fleets are known methods.

## Installation and minimal usage

Python 3.9+; Python 3.9–3.12 is recommended for the pinned environment. Newer versions can use compatible packages from requirements.txt. Only NumPy and SciPy are needed; no solver licence, plotting package or external dataset is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-reproduce.txt
python run.py --demo
python run.py --input examples/affine.json --requests 0 1/10
```

Input fields are `E`, `C`, `D`, `initial`, and `intervals`. Use JSON strings such as `"1/3"` for nonterminating fractions to preserve rational semantics.

For proportional groups, first apply Proposition 5 to obtain at most three virtual devices, then pass their parameters to the entry point. The package does not search for groupings automatically.

Returned statuses:

- `feasible`: an exact recursion accepts, or a policy/tree witness has passed all rational checks.
- `infeasible`: exclusion by the physical box, exact necessary conditions, an exact recursion, or certified template bounds.
- `unknown`: affine `rejected`/`float_only`; neither proves infeasibility of the original problem.
- `infeasible_float`: the optional tree LP reports infeasibility even after retrying without presolve; no rational Farkas certificate is supplied.

For general heterogeneous inputs, the entry point first checks exact aggregate necessary conditions, then searches for an affine policy. Optional stronger outer bounds and fallback:

```bash
python run.py --input examples/affine_gap.json --template
python run.py --input examples/affine_gap.json --tree
```

`--template` uses all 0/±1 directions and checks rational primal–dual certificates for every LP, limited to N≤6; direction enumeration is exponential in N. `--tree` expands endpoint requests only when the result is unresolved, limited to T≤12 and exponential in T. Its witness shares actions at common histories; it is not returned as a controller for arbitrary interior requests.

API: `from chameleon_runtime import decide`; `result, policy = decide(data)`. When an executable policy is available, `policy.power(observed_history)` returns exact fractional powers. The affine policy contains the repaired coefficients that passed certification; `policy.as_dict()` serializes them. Raw floating-point coefficients are not delivered as a certified policy.

## Reproduction and retained results

```bash
python -m unittest discover -s tests -v
python verify_release.py
```

Checks cover N2/N3/homogeneous algorithms, zero-power and positive-power counterexamples, the affine gap, and interface boundaries. See [results](results/README.md). Records distinguish exact certificates from floating-point comparisons.

Historical sandwich samples total 211,063 states: the floating-point tree LP classified 211,060 as feasible, 210,959 obtained rational lifted-affine certification, 101 were accepted only numerically, and 3 were rejected by the affine test. A strict workflow leaves 104 states for other methods, about 0.049%; this is neither zero fallback nor a general acceptance-rate guarantee. These are aggregates from the earlier research version; the full sample collection was not rerun for this release.

Only aggregate results, source hashes and release certificate logs are retained. Personal materials, full papers and large search traces are excluded.

## Reading guide

1. [Research report](RESEARCH_REPORT.md): question, results and open problems.
2. [Proofs, experiments and independent reviews](complexity_20260925/README.md).
3. [Archive and publication scope](ARCHIVE.md). Earlier frozen MFE material remains available in its original commit and archive tag; the complete local research directory is unchanged.
