# Project Chameleon

Runnable code and selected results for causal deliverability of lossless storage fleets. Device energy is `e_i ∈ [0,E_i]`, power is `p_i ∈ [-C_i,D_i]`, and `e_next = e - p`. Each period's observed aggregate request must be matched exactly using only current and past requests. Period duration is absorbed into the power limits; losses and operating-mode constraints are excluded.

## Run

Python 3.9–3.12 is recommended for the pinned environment. Dependencies are NumPy and SciPy.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-reproduce.txt
python run.py --demo
python run.py --input examples/affine.json --requests 0 1/10
```

Inputs contain `E`, `C`, `D`, `initial`, and `intervals`. Use JSON strings such as `"1/3"` for exact fractions. See `examples/` for complete inputs.

The entry point uses exact rational recursions for N≤3, identical devices, and devices with `C_i≥E_i` and `D_i≥E_i`. Other inputs use aggregate necessary conditions and a history-dependent affine-policy LP. Only rationally certified policies justify acceptance; this policy class is not generally exact.

Statuses:

- `feasible`: accepted by exact recursion or a rationally checked policy/tree witness.
- `infeasible`: excluded by exact bounds or certified necessary conditions.
- `unknown`: unresolved; affine rejection or float-only acceptance does not prove infeasibility.
- `infeasible_float`: optional tree LP reports infeasibility after a presolve-off retry, without a rational infeasibility certificate.

Optional stronger checks:

```bash
python run.py --input examples/affine_gap.json --template
python run.py --input examples/affine_gap.json --tree
```

`--template` checks all 0/±1 directions with rational primal–dual certificates, limited to N≤6. `--tree` expands shared-history endpoint requests, limited to T≤12. Direction enumeration is exponential in N; trees are exponential in T. A tree witness is not returned as an executable controller for interior requests.

API: `from chameleon_runtime import decide`; `result, policy = decide(data)`. When available, `policy.power(observed_history)` returns fractional powers and `policy.as_dict()` serializes a certified affine policy.

## Verify and reproduce

```bash
python -m unittest discover -s tests -v
python verify_release.py
```

`evidence/` contains solver implementations, experiment scripts and rational counterexample certificates. The verifier runs 17 checks, including N2/N3/homogeneous recursions, two-type and coefficient-2 counterexamples, affine failure certificates, and runtime regressions.

Selected results in `results/`:

- `affine_samples.csv`: historical sample counts; strict unresolved count is samples minus segregated_certified.
- `affine_scaling.csv`: historical median timings; blank tree_feasible_float means the tree was not run.
- `vertex_summary.json`: historical floating-point vertex-screening aggregates.
- `provenance.json`: source commit and hashes of original result files, which are not bundled.
- `certificates.txt`, `release_checks.json`: current verification output and environment.

The historical samples total 211,063 states: 210,959 rational affine certificates, 101 float-only acceptances and three affine rejections. Strict affine testing leaves 104 states for other methods. Historical timings and acceptance rates are distribution-dependent evidence; the full sample collection is not rerun by the release verifier.
