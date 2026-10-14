"""Points 2 and 3 of the 10-07 plan: sandwich the exact answer between an outer and an inner approximation.

For random heterogeneous fleets (N = 3..6) and interval commitments:
  outer  = subset-bound recursion (oracle2.subset_recursion; exact for N <= 3 by Theorem 4, an outer
           approximation for N >= 4, so it may accept commitments that cannot be honoured);
  inner  = fixed participation factors: device i takes share w+_i of a discharge request and w-_i of a
           charge request (shares sum to 1, chosen by an LP for the given initial state and commitment);
           this is a valid causal policy, so acceptance is safe;
  exact  = endpoint-tree LP (floating point; a reported infeasibility is re-solved with presolve off).
Initial states are sampled INSIDE the outer approximation by rejection sampling from the box: at most
4000 draws and at most 25 accepted points per instance; instances with no accepted point are dropped.
For one instance this samples uniformly from its outer approximation; pooled over instances it is an
empirical distribution weighted by the number of accepted points (thin outer sets are under-represented).
Each saved row records the instance inputs and the sampled states that the exact test rejected.
Each instance records rho = min_i min(C_i, D_i) / max_i max(C_i, D_i) (0 when some device is one-way).
Floating point throughout; the counts are evidence, not proofs.
Usage: python3 sandwich_experiment.py SEED INSTANCES [--positive]"""
import json, sys
import numpy as np
from scipy.optimize import linprog
from oracle2 import build, member_status, subset_recursion


def inner_accepts(e, E, C, D, ms):
    """LP over shares w = (w+, w-) in R^{2N}: power and energy limits hold for every request path."""
    N = len(E); nv = 2 * N
    A, b = [], []
    pos = [max(u, 0.) for l, u in ms]; neg_l = [min(l, 0.) for l, u in ms]
    hi_p = lambda s: (max(ms[s][1], 0.), min(ms[s][1], 0.))      # p_i,s is increasing in y: max at u_s
    lo_p = lambda s: (max(ms[s][0], 0.), min(ms[s][0], 0.))      # min at l_s
    for i in range(N):
        for t in range(len(ms)):
            r = np.zeros(nv); r[i] = pos[t]; A.append(r); b.append(D[i])            # w+_i u_t <= D_i
            r = np.zeros(nv); r[N + i] = -neg_l[t]; A.append(r); b.append(C[i])     # -w-_i l_t <= C_i
            r = np.zeros(nv)                                                        # e_i - sum max p >= 0
            for s in range(t + 1):
                a1, a2 = hi_p(s); r[i] += a1; r[N + i] += a2
            A.append(r); b.append(e[i])
            r = np.zeros(nv)                                                        # e_i - sum min p <= E_i
            for s in range(t + 1):
                a1, a2 = lo_p(s); r[i] -= a1; r[N + i] -= a2
            A.append(r); b.append(E[i] - e[i])
    Aeq = [np.r_[np.ones(N), np.zeros(N)], np.r_[np.zeros(N), np.ones(N)]]
    res = linprog(np.zeros(nv), A_ub=np.array(A), b_ub=np.array(b), A_eq=np.array(Aeq), b_eq=[1., 1.],
                  bounds=[(0, None)] * nv, method='highs')
    return res.status == 0


def in_outer(e, K):
    return all(lo - 1e-9 <= sum(e[i] for i in S) <= hi + 1e-9 for S, (lo, hi) in K.items())


def instance(rng, positive):
    N = int(rng.integers(3, 7)); menu = [.5, 1, 2, 3] if positive else [0, .5, 1, 2, 3]
    E = rng.integers(1, 6, N).astype(float); C = rng.choice(menu, N); D = rng.choice(menu, N)
    ms = []
    for _ in range(int(rng.integers(2, 5))):
        c = rng.uniform(-0.5 * C.sum(), 0.5 * D.sum()); h = rng.uniform(0, 0.35) * (C.sum() + D.sum()) / 2
        ms.append((round(c - h, 2), round(c + h, 2)))
    return E, C, D, ms


if __name__ == '__main__':
    seed, count = int(sys.argv[1]), int(sys.argv[2]); positive = '--positive' in sys.argv
    rng = np.random.default_rng(seed); rows = []
    for _ in range(count):
        E, C, D, ms = instance(rng, positive)
        K = subset_recursion(C, D, E, ms)
        if K is None:
            continue
        M = build(C, D, E, ms)
        rho = float(min(np.minimum(C, D)) / max(np.maximum(C, D))) if max(np.maximum(C, D)) > 0 else 0.
        r = dict(N=len(E), T=len(ms), rho=round(rho, 3), samples=0, exact_ok=0, inner_ok=0, wrong_accept=0,
                 E=E.tolist(), C=C.tolist(), D=D.tolist(), menus=ms, wrong_points=[])
        tries = 0
        while r['samples'] < 25 and tries < 4000:
            tries += 1
            e = rng.uniform(0, E)
            if not in_outer(e, K):
                continue
            r['samples'] += 1
            ex = member_status(M, e) or member_status(M, e, presolve=False)   # other statuses raise
            inn = inner_accepts(e, E, C, D, ms)
            r['exact_ok'] += ex; r['inner_ok'] += inn; r['wrong_accept'] += (not ex)
            if not ex:
                r['wrong_points'].append(e.tolist())
            assert not (inn and not ex), ('inner accepted an infeasible point', E, C, D, ms, e)
        if r['samples']:
            rows.append(r)
    tag = 'positive' if positive else 'with-zeros'
    json.dump(rows, open(f'sandwich_{tag}_{seed}.json', 'w'))
    print(tag, seed, 'instances with samples:', len(rows))
