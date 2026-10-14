"""Exact rational six-bound recursion for two lossless batteries.

Run this file for an independent floating-point tree-LP comparison.
The recursion itself uses only Fraction arithmetic, no LP.
Bounds are (a1, b1, a2, b2, a12, b12); None denotes the empty set.
"""
from fractions import Fraction as F


def rational(x):
    return x if isinstance(x, F) else F(str(x))


def normalize(bounds):
    if bounds is None:
        return None
    a1, b1, a2, b2, a12, b12 = map(rational, bounds)
    lo, hi = max(a12, a1 + a2), min(b12, b1 + b2)
    if a1 > b1 or a2 > b2 or lo > hi:
        return None
    return (max(a1, lo-b2), min(b1, hi-a2),
            max(a2, lo-b1), min(b2, hi-a1), lo, hi)


def contains(bounds, e):
    if bounds is None:
        return False
    a1, b1, a2, b2, lo, hi = bounds
    x, z = map(rational, e)
    return a1 <= x <= b1 and a2 <= z <= b2 and lo <= x+z <= hi


def predecessor(bounds, C, D, y):
    """Unclipped predecessor for one aggregate request."""
    K = normalize(bounds)
    if K is None:
        return None
    c1, c2 = map(rational, C)
    d1, d2 = map(rational, D)
    y = rational(y)
    L, U = max(-c1, y-d2), min(d1, y+c2)
    if L > U:
        return None
    a1, b1, a2, b2, lo, hi = K
    return normalize((a1+L, b1+U, a2+y-U, b2+y-L, lo+y, hi+y))


def step(bounds, E, C, D, l, u):
    l, u = rational(l), rational(u)
    if l > u:
        raise ValueError('request interval must be nonempty')
    left, right = predecessor(bounds, C, D, l), predecessor(bounds, C, D, u)
    if left is None or right is None:
        return None
    e1, e2 = map(rational, E)
    box = (F(0), e1, F(0), e2, F(0), e1+e2)
    return normalize(tuple((max if i % 2 == 0 else min)(left[i], right[i], box[i])
                           for i in range(6)))


def kernels(E, C, D, menus):
    E, C, D = [tuple(map(rational, a)) for a in (E, C, D)]
    if any(len(a) != 2 for a in (E, C, D)) or min(E+C+D) < 0:
        raise ValueError('two devices with nonnegative capacities and power limits required')
    out = [None] * (len(menus)+1)
    out[-1] = normalize((0, E[0], 0, E[1], 0, sum(E)))
    for t in range(len(menus)-1, -1, -1):
        out[t] = step(out[t+1], E, C, D, *menus[t])
    return out


def action(e, y, next_bounds, C, D):
    """Causal selector: choose the lower endpoint of the feasible p1 interval."""
    K = normalize(next_bounds)
    if K is None:
        raise ValueError('empty next kernel')
    x, z = map(rational, e)
    y = rational(y)
    c1, c2 = map(rational, C)
    d1, d2 = map(rational, D)
    a1, b1, a2, b2, lo, hi = K
    lower = max(-c1, y-d2, x-b1, a2-z+y)
    upper = min(d1, y+c2, x-a1, b2-z+y)
    if lower > upper or not lo <= x+z-y <= hi:
        raise ValueError('no feasible action')
    return lower, y-lower


def validate():
    import itertools
    import numpy as np
    from oracle2 import build, support
    rng = np.random.default_rng(20260925)
    cases = [([0, 0], [0, 0], [0, 0], [(0, 0)]),
             ([0, 0], [0, 0], [0, 0], [(0, 1)]),
             ([0, 2], [0, 1], [0, 2], [(-1, 0), (0, 1)]),
             ([2, 2], [0, 0], [0, 0], [(0, 0)]),
             ([2, 2], [1, 1], [1, 1], [(2, 2), (2, 2)])]
    for _ in range(300):
        E = rng.integers(0, 5, 2).tolist()
        C = (rng.integers(0, 5, 2)/2).tolist()
        D = (rng.integers(0, 5, 2)/2).tolist()
        ms = [tuple(sorted((rng.integers(-6, 7, 2)/2).tolist()))
              for _ in range(int(rng.integers(1, 6)))]
        cases.append((E, C, D, ms))
    feasible = empty = support_checks = replay_edges = 0
    for E, C, D, ms in cases:
        ks = kernels(E, C, D, ms)
        M = build(np.array(C), np.array(D), np.array(E), ms)
        first = support(M, [1, 1])
        assert (ks[0] is None) == (first is None), (E, C, D, ms)
        if ks[0] is None:
            empty += 1
            continue
        feasible += 1
        for j, d in enumerate(([1, 0], [0, 1], [1, 1])):
            hi = support(M, d)[1]
            lo = -support(M, -np.array(d))[1]
            assert abs(hi-float(ks[0][2*j+1])) < 1e-7
            assert abs(lo-float(ks[0][2*j])) < 1e-7
            support_checks += 2
        # One initial state and every path of a three-point menu, exact arithmetic.
        a1, b1, a2, b2, lo, hi = ks[0]
        x = a1
        z = max(a2, lo-x)
        assert contains(ks[0], (x, z))
        frontier = [(x, z)]
        for t, (l, u) in enumerate(ms):
            ys = sorted({rational(l), rational(u), (rational(l)+rational(u))/2})
            nxt = []
            for e, y in itertools.product(frontier, ys):
                p = action(e, y, ks[t+1], C, D)
                assert sum(p) == y
                assert all(-rational(C[i]) <= p[i] <= rational(D[i]) for i in range(2))
                ep = tuple(e[i]-p[i] for i in range(2))
                assert contains(ks[t+1], ep)
                nxt.append(ep)
                replay_edges += 1
            frontier = nxt
    print(dict(cases=len(cases), feasible=feasible, empty=empty,
               support_checks=support_checks, rational_replay_edges=replay_edges,
               disagreements=0))


if __name__ == '__main__':
    validate()
