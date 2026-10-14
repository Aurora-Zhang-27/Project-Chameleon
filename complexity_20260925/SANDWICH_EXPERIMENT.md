# Sandwich experiments: subset outer bounds and participation-factor inner policies

Drafted 2026-10-07; sampling and claims revised after the October 9 independent review. These are **floating-point experiments on the tested distribution**, not worst-case bounds, a proof of exactness or a universal false-acceptance-rate guarantee.

## 0. Conclusions

For N≥4 only, excluding N=3 where exactness is proved, sampled outer-accepted states had three tree-infeasible classifications in 79,850 zero-allowed samples, and none in 78,019 positive-power samples. The three occurred in two N=6 instances with one-way devices. Samples share instance parameters and are not independent Bernoulli trials. Positive-power exact counterexamples elsewhere already refute global exactness.

The implemented participation-factor inner test accepted roughly 61–76%; about 24–39% remained unresolved by that test, nearly all numerically tree-feasible. In this distribution better inner policies could narrow the sandwich. This is not a reason to stop improving the outer bound. The later affine results are in [AFFINE_DECISION.md](AFFINE_DECISION.md).

## 1. Design

`evidence/sandwich_experiment.py` generates N=3–6,T=2–4, integer E∈{1,…,5}, and powers from either {0,1/2,1,2,3} or {1/2,1,2,3}. Intervals use random centres and half-widths. Each family uses four seeds and 1,500 instances per seed; about 4,350 instances per family have a nonempty outer bound and retained samples. `sandwich_summary.py` summarizes generated JSON. Raw historical arrays are not published; aggregate tables and provenance are retained.

The outer test is subset recursion. The inner policy uses nonnegative w⁺,w⁻, each summing to one:

    p_i(y)=w⁺_i max(y,0)+w⁻_i min(y,0).

This is monotone in y, so prefix-energy extremes occur on all-l or all-u request prefixes. A small LP enforces those energy constraints and power bounds. It is a mathematically valid causal policy class, but historical LP status=0 alone is not a rational acceptance certificate. Each sample was also checked by an endpoint-tree LP; reported infeasibility was retried without presolve. The implication from inner acceptance to tree feasibility held numerically in every sample.

For each instance, rejection sampling makes at most 4,000 draws and retains **at most 25 states** inside the outer hull. Instances with no retained state are discarded. There were 206 zero-allowed and 242 positive retained instances with fewer than 25 points. For a fixed positive-volume hull the conditional draw is uniform; pooled results weight instances by successful sample count and underrepresent thin or lower-dimensional hulls. Since October 9, generated JSON includes parameters, menus and falsely accepted states for later rational checking.

Power-ratio diagnostic: ρ=min_i min(C_i,D_i)/max_i max(C_i,D_i); one-way devices give ρ=0. This omits capacity and period duration and is not itself an exactness condition.

## 2. Results

| Family | N | Instances | States | Outer false acceptances, float | Participation acceptance | Unresolved by inner test |
|---|---:|---:|---:|---:|---:|---:|
| Zero allowed | 3 | 1,046 | 25,681 | 0 | 75.8% | 24.2% |
| Zero allowed | 4 | 1,060 | 25,719 | 0 | 69.5% | 30.5% |
| Zero allowed | 5 | 1,137 | 27,591 | 0 | 66.3% | 33.7% |
| Zero allowed | 6 | 1,110 | 26,540 | 3 | 63.4% | 36.6% |
| Positive | 3 | 1,121 | 27,513 | 0 | 71.0% | 29.0% |
| Positive | 4 | 1,062 | 25,743 | 0 | 65.0% | 35.0% |
| Positive | 5 | 1,086 | 26,058 | 0 | 64.0% | 36.0% |
| Positive | 6 | 1,100 | 26,218 | 0 | 60.8% | 39.2% |

| Scope | Zero-allowed instances/states/false acceptances | Positive instances/states/false acceptances |
|---|---|---|
| N=3–6 | 4,353 / 105,531 / 3 | 4,369 / 105,532 / 0 |
| N≥4 | 3,307 / 79,850 / 3 | 3,248 / 78,019 / 0 |

The three points were in historical zero-allowed seeds 3 (two points,T=3) and 4 (one point,T=4). Their counts have no individual rational infeasibility certificates here. All ρ>0 strata in this experiment had zero observed false acceptances; this is a restricted empirical observation, not a general positive-power result.

## 3. One-step slack and limits

Theorem 2's derivation gives

    g(M)≤min(w(M),w(R₀∖M)), w=C+D.

Indeed each of its two min terms is bounded by the corresponding power on M, and also by the complementary expressions whose s values cancel. This bounds slack in a particular **single-request mixed inequality**, not a distance between multi-step kernels. Powers can be comparable to capacities, so this bound does not explain tiny observed false-acceptance rates.

The shared upper/lower subset structure in Examples B/C plus nearly one-way devices explains a possible mechanism, not a full characterization. Their 1/100 perturbations show that ρ>0 does not suffice for exactness. Uniform interior sampling can miss thin gaps; adversarial examples have much larger gaps. T≤4,N≤6 and selected menus limit extrapolation. Xie & Chen's rectangular inner approximation was not reproduced.

A future safe inner model could use at most three fixed-weight groups and Theorem 4, or the homogeneous theorem where applicable. The history-dependent affine test was subsequently implemented, but the original participation experiment remains a separate historical comparison.
