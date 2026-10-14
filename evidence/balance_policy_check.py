"""Point 1 of the 10-07 plan: for IDENTICAL devices, is "balance the state of charge" an optimal causal
policy for every commitment?  Policy: after seeing y, move to the least-majorized point of the set of
reachable next states {e - p : -C <= p <= D, sum p = y}, i.e. the water-filling point
x_i = clip(lam, e_i - D, e_i + C) with sum x = e(V) - y.  It uses no information about the commitment.

Check: random initial states e0 are classified (a) by the endpoint-tree LP (floating point; a reported
infeasibility is re-solved with presolve off) and (b) by simulating the policy in exact rational
arithmetic on every request path built from {l, midpoint, u} in each period.  The claim predicts
(a) feasible  <=>  (b) the policy stays inside [0,E] on every path.
Usage: python3 balance_policy_check.py SEED COUNT"""
import itertools, sys
from fractions import Fraction as F
import numpy as np
from oracle2 import build, member_status


def waterfill(lo, hi, total):
    """Least-majorized point of {lo <= x <= hi, sum x = total}, exact; None if empty."""
    if total < sum(lo) or total > sum(hi):
        return None
    f = lambda lam: sum(min(max(lam, a), b) for a, b in zip(lo, hi))
    pts = sorted(set(lo) | set(hi))
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        fa, fb = f(a), f(b)
        if fa <= total <= fb:
            lam = a if fb == fa else a + (total - fa) * (b - a) / (fb - fa)
            return [min(max(lam, x), y) for x, y in zip(lo, hi)]
    lam = pts[0] if total <= f(pts[0]) else pts[-1]
    return [min(max(lam, x), y) for x, y in zip(lo, hi)]


def policy_survives(e0, E, C, D, ms):
    menus = [sorted({l, (l + u) / 2, u}) for l, u in ms]
    for path in itertools.product(*menus):
        e = list(e0)
        for y in path:
            x = waterfill([ei - D[i] for i, ei in enumerate(e)], [ei + C[i] for i, ei in enumerate(e)], sum(e) - y)
            if x is None or any(xi < 0 or xi > E[i] for i, xi in enumerate(x)):
                return False
            e = x
    return True


if __name__ == '__main__':
    seed, count = int(sys.argv[1]), int(sys.argv[2])
    rng = np.random.default_rng(seed)
    st = dict(points=0, lp_feasible=0, lp_infeasible=0, agree=0, disagree=0)
    bad = []
    for _ in range(count):
        N = int(rng.integers(2, 6)); T = int(rng.integers(1, 4))
        E1 = F(int(rng.integers(1, 6))); C1 = F(int(rng.integers(0, 7)), 2); D1 = F(int(rng.integers(0, 7)), 2)
        E, C, D = [E1] * N, [C1] * N, [D1] * N
        ms = []
        for _ in range(T):
            c = F(int(rng.integers(-6, 7)), 4) * C1 * N / 2 if rng.random() < .5 else F(int(rng.integers(-6, 7)), 4) * D1 * N / 2
            h = F(int(rng.integers(0, 5)), 4) * (C1 + D1) * N / 4
            ms.append((c - h, c + h))
        M = build(np.array([float(c) for c in C]), np.array([float(d) for d in D]), np.array([float(x) for x in E]), [(float(l), float(u)) for l, u in ms])
        for _ in range(6):
            e0 = [F(int(rng.integers(0, 4 * int(E1) + 1)), 4) for _ in range(N)]
            x = np.array([float(v) for v in e0])
            lp = member_status(M, x) or member_status(M, x, presolve=False)   # other statuses raise
            pol = policy_survives(e0, E, C, D, ms)
            st['points'] += 1; st['lp_feasible' if lp else 'lp_infeasible'] += 1
            if lp == pol: st['agree'] += 1
            else:
                st['disagree'] += 1; bad.append((N, str(E1), str(C1), str(D1), [(str(l), str(u)) for l, u in ms], [str(v) for v in e0], lp, pol))
    print(seed, st)
    for b in bad[:5]: print('   ', b)
