"""Exact recursion for a HOMOGENEOUS fleet (m identical lossless devices, any m, any initial SoCs),
HOMOGENEOUS_FLEET_ZH.md Theorem H.  K_t is described by 2m numbers: b_k bounds the sum of the k largest
SoCs from above, a_k bounds the sum of the k smallest from below (k = 0..m, a_0 = b_0 = 0).
One step (only +, -, min, max; exact Fractions; O(m) arithmetic operations):
  b~_k = b_k + min(D k, l + C (m-k)),          a~_k = a_k + max(-C k, u - D (m-k))
  b^_k = min(E k, b~_k),                        a^_k = max(0, a~_k)          (physical box, Theorem H step 4)
  empty iff a^_m > b^_m
  b_k <- min(b^_k, b^_m - a^_{m-k}),            a_k <- max(a^_k, a^_m - b^_{m-k}) (tightening; both read
                                                                                   the OLD arrays b^, a^)
Membership: sort e once, build prefix sums, check the 2m inequalities: O(m log m).
The products E k, D k, C(m-k) are written as multiplications for readability; they can be accumulated by
additions, so the recursion itself needs no division.  (The water-filling POLICY does divide.)
Optimal causal policy (any commitment): water-filling, see balance_policy_check.py.

CROSSCHECK (switched on by validate(), off by default) additionally computes the full box convolution
b^_k = min_{j<=k}[b~_j + E(k-j)] and a^_k = max_{j<=k} a~_j in O(m^2) and asserts it equals the two-term
form, and asserts the concavity/convexity invariant.  These asserts are checks, not the source of correctness.

validate() compares with the endpoint-tree LP (floating point): every tight bound against the LP support
value in the corresponding subset direction; for m in 2..4 every vertex of the 2m-bound description must be
LP-feasible (set-equality certificate, float; skipped cases are counted by reason); and membership of random
points.  A floating 'infeasible' (emptiness or membership) is re-solved with presolve off; other solver
statuses raise.  Pass thresholds are asserted at the end.  Usage: python3 homogeneous_exact.py [SEED] [COUNT]"""
from fractions import Fraction as F
import sys

CROSSCHECK = False


def q(x):
    return x if isinstance(x, F) else F(str(x))


def kernels(m, E, C, D, menus):
    E, C, D = q(E), q(C), q(D)
    out = [None] * (len(menus) + 1)
    out[-1] = ([F(0)] * (m + 1), [E * k for k in range(m + 1)])
    for t in range(len(menus) - 1, -1, -1):
        out[t] = step(out[t + 1], m, E, C, D, *menus[t])
    return out


def step(K, m, E, C, D, l, u):
    if K is None:
        return None
    l, u = q(l), q(u)
    if l > u:
        raise ValueError('empty request interval')
    if l < -C * m or u > D * m:
        return None
    a, b = K
    bt = [b[k] + min(D * k, l + C * (m - k)) for k in range(m + 1)]
    at = [a[k] + max(-C * k, u - D * (m - k)) for k in range(m + 1)]
    bh = [min(E * k, bt[k]) for k in range(m + 1)]
    ah = [max(F(0), at[k]) for k in range(m + 1)]
    if CROSSCHECK:   # full convolution, O(m^2): must equal the two-term form (Theorem H step 4)
        assert bh == [min(bt[j] + E * (k - j) for j in range(k + 1)) for k in range(m + 1)]
        assert ah == [max(at[j] for j in range(k + 1)) for k in range(m + 1)]
    if ah[m] > bh[m]:
        return None
    nb = [min(bh[k], bh[m] - ah[m - k]) for k in range(m + 1)]
    na = [max(ah[k], ah[m] - bh[m - k]) for k in range(m + 1)]
    if CROSSCHECK:
        assert nb[0] == 0 and na[0] == 0
        assert all(nb[k - 1] + nb[k + 1] <= 2 * nb[k] and na[k - 1] + na[k + 1] >= 2 * na[k] for k in range(1, m)), \
            'concavity/convexity invariant violated'
    return na, nb


def member(K, e):
    if K is None:
        return False
    a, b = K
    s = sorted(q(x) for x in e)
    m = len(s)
    pre = [F(0)]
    for x in s:
        pre.append(pre[-1] + x)                      # pre[k] = sum of the k smallest
    tot = pre[m]
    return all(tot - pre[m - k] <= b[k] and pre[k] >= a[k] for k in range(1, m + 1))


def validate(seed=1, count=300):
    global CROSSCHECK
    CROSSCHECK = True
    import numpy as np
    from itertools import combinations
    from scipy.spatial import QhullError
    from oracle2 import build, support, member_status, outer_vertices
    rng = np.random.default_rng(seed)
    st = dict(cases=0, nonempty=0, empty=0, support_checks=0, support_dev=0.0, points=0, point_disagree=0,
              vertices=0, vertex_rejected=0, vertex_skipped_no_interior=0, vertex_skipped_qhull=0,
              presolve_off_rescues=0)

    def lp_feasible(M, x):
        if member_status(M, x):
            return True
        if member_status(M, x, presolve=False):
            st['presolve_off_rescues'] += 1
            return True
        return False

    for _ in range(count):
        m = int(rng.integers(1, 7)); T = int(rng.integers(1, 5))
        E = F(int(rng.integers(1, 6))); C = F(int(rng.integers(0, 7)), 2); D = F(int(rng.integers(0, 7)), 2)
        menus = []
        for _ in range(T):
            c = F(int(rng.integers(-4, 5)), 8) * (C + D) * m / 2; h = F(int(rng.integers(0, 3)), 8) * (C + D) * m / 2
            menus.append((c - h, c + h))
        ks = kernels(m, E, C, D, menus)
        M = build(np.array([float(C)] * m), np.array([float(D)] * m), np.array([float(E)] * m),
                  [(float(l), float(u)) for l, u in menus])
        lp_empty = support(M, np.ones(m)) is None
        if lp_empty and support(M, np.ones(m), presolve=False) is not None:
            lp_empty = False; st['presolve_off_rescues'] += 1
        st['cases'] += 1
        assert lp_empty == (ks[0] is None), ('emptiness disagreement', m, E, C, D, menus)
        if ks[0] is None:
            st['empty'] += 1; continue
        st['nonempty'] += 1
        a, b = ks[0]
        for k in range(1, m + 1):
            v = np.array([1.] * k + [0.] * (m - k))
            st['support_dev'] = max(st['support_dev'], abs(support(M, v)[1] - float(b[k])),
                                    abs(-support(M, -v)[1] - float(a[k])))
            st['support_checks'] += 2
        if 2 <= m <= 4:   # set-equality certificate: every vertex of the 2m-bound description is LP-feasible
            Kd = {S: (float(a[len(S)]), float(b[len(S)])) for r in range(1, m + 1) for S in combinations(range(m), r)}
            try:
                V = outer_vertices(Kd, m)
                if V is None:
                    st['vertex_skipped_no_interior'] += 1   # Chebyshev LP failed or inner radius < 1e-7
            except QhullError:
                V = None; st['vertex_skipped_qhull'] += 1
            for v in (V if V is not None else []):
                st['vertices'] += 1
                if not lp_feasible(M, v):
                    st['vertex_rejected'] += 1
        for _ in range(8):
            e = [F(int(rng.integers(0, 4 * int(E) + 1)), 4) for _ in range(m)]
            st['points'] += 1
            if lp_feasible(M, np.array([float(z) for z in e])) != member(ks[0], e):
                st['point_disagree'] += 1
    dev = st['support_dev']; st['support_dev'] = f'{dev:.2e}'
    print(st)
    assert dev <= 1e-7 and st['point_disagree'] == 0 and st['vertex_rejected'] == 0, 'validation FAILED'
    print('validation passed: support deviation <= 1e-7, no point disagreement, no rejected vertex')


if __name__ == '__main__':
    validate(int(sys.argv[1]) if len(sys.argv) > 1 else 1, int(sys.argv[2]) if len(sys.argv) > 2 else 300)
