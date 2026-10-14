"""Single-state decision on the sandwich-experiment states (2026-10-11).

Re-runs sandwich_experiment.py with the same seeds, instances and sampled initial states (the random
stream is consumed identically), and adds two inner tests from affine_decision.py:
  'affine'      history-dependent affine policies,
  'segregated'  history-dependent policies affine in (y^+, y^-) (contains affine and the fixed
                participation factors of sandwich_experiment.inner_accepts).
For every sampled state (all lie inside the subset outer approximation) we record:
  exact (endpoint-tree LP, presolve-off re-solve on infeasibility), pf (participation factors, float),
  and the affine / segregated decision ('certified' = exact rational check passed, 'float_only',
  'rejected').  Safety is asserted: no inner test may accept a state the tree LP rejects.
Timing per LP call is recorded for the tree LP and the segregated LP.
Usage: python3 affine_sandwich.py SEED INSTANCES [--positive]"""
import json, sys, time
import numpy as np
from oracle2 import build, member_status, subset_recursion
from sandwich_experiment import instance, in_outer, inner_accepts
from affine_decision import AffinePolicyLP

if __name__ == '__main__':
    seed, count = int(sys.argv[1]), int(sys.argv[2]); positive = '--positive' in sys.argv
    rng = np.random.default_rng(seed); rows = []
    for _ in range(count):
        E, C, D, ms = instance(rng, positive)
        K = subset_recursion(C, D, E, ms)
        if K is None:
            continue
        M = build(C, D, E, ms)
        lps = {k: AffinePolicyLP(E, C, D, ms, k) for k in ('affine', 'segregated')}
        r = dict(N=len(E), T=len(ms), E=E.tolist(), C=C.tolist(), D=D.tolist(), menus=ms, samples=0, exact_ok=0,
                 pf_ok=0, affine={}, segregated={}, undecided_points=[], t_tree=0., t_seg=0.)
        tries = 0
        while r['samples'] < 25 and tries < 4000:
            tries += 1
            e = rng.uniform(0, E)
            if not in_outer(e, K):
                continue
            r['samples'] += 1
            t0 = time.perf_counter()
            ex = member_status(M, e) or member_status(M, e, presolve=False)
            r['t_tree'] += time.perf_counter() - t0
            pf = inner_accepts(e, E, C, D, ms)
            r['exact_ok'] += ex; r['pf_ok'] += pf
            assert not (pf and not ex)
            for k, lp in lps.items():
                t0 = time.perf_counter()
                d = lp.decide(e)[0]
                if k == 'segregated':
                    r['t_seg'] += time.perf_counter() - t0
                assert not (d in ('certified', 'float_only') and not ex), ('unsafe acceptance', k, E, C, D, ms, e)
                r[k][d] = r[k].get(d, 0) + 1
                if k == 'segregated' and ex and d == 'rejected':
                    r['undecided_points'].append(e.tolist())
        if r['samples']:
            rows.append(r)
    tag = 'positive' if positive else 'with-zeros'
    json.dump(rows, open(f'affine_{tag}_{seed}.json', 'w'))
    print(tag, seed, 'instances with samples:', len(rows), flush=True)
