"""Three-device exact rational recursion (N=3, closed-form subset bounds).

step() is the theorem's algorithm: add the single-request bounds (l end for upper, u end for lower),
fold in the physical box by convolution, test nonemptiness by a <= b (Frank sandwich), and tighten
with the closed forms of Lemma 3.  Only +, -, min, max: no division, so no denominator growth.
The theorem rests on Frank's sandwich theorem, LP duality and the exact finite certificate in
n3_lemma_certificate.py; it was independently reviewed in September 2026.

With CROSSCHECK on, every step is also tightened by exact vertex enumeration of the 14 subset
inequalities (independent of Lemma 3) and the two results must agree; the H3'' property of the
output is asserted as well.  These asserts are checks, not the source of correctness.
LP (floating point) is used only by validate().
Run: python3 evidence/n3_exact.py
"""
from fractions import Fraction as F
from functools import lru_cache
from itertools import combinations

N = 3
MASKS = tuple(range(1, 8))
VECTORS = tuple(tuple((s >> i) & 1 for i in range(3)) for s in MASKS)
NORMALS = VECTORS + tuple(tuple(-v for v in row) for row in VECTORS)


def q(x):
    return x if isinstance(x, F) else F(str(x))


def sumset(x, s):
    return sum((x[i] for i in range(3) if s & (1 << i)), F(0))


def dot(a, b):
    return sum((v*w for v, w in zip(a, b)), F(0))


@lru_cache(None)
def bases():
    out = []
    for inds in combinations(range(14), 3):
        a, b, c = [NORMALS[i] for i in inds]
        det = (a[0]*(b[1]*c[2]-b[2]*c[1])
               - a[1]*(b[0]*c[2]-b[2]*c[0])
               + a[2]*(b[0]*c[1]-b[1]*c[0]))
        if det == 0:
            continue
        inv = ((b[1]*c[2]-b[2]*c[1], a[2]*c[1]-a[1]*c[2], a[1]*b[2]-a[2]*b[1]),
               (b[2]*c[0]-b[0]*c[2], a[0]*c[2]-a[2]*c[0], a[2]*b[0]-a[0]*b[2]),
               (b[0]*c[1]-b[1]*c[0], a[1]*c[0]-a[0]*c[1], a[0]*b[1]-a[1]*b[0]))
        out.append((inds, tuple(tuple(F(v, det) for v in row) for row in inv)))
    return tuple(out)


def vertices(a, b, first_only=False):
    """All vertices of a bounded 14-inequality polytope, or () if empty."""
    if any(a[s] > b[s] for s in MASKS):
        return ()
    rhs = tuple(b[1:]) + tuple(-x for x in a[1:])
    found = set()
    for inds, inv in bases():
        r = tuple(rhs[i] for i in inds)
        x = tuple(dot(row, r) for row in inv)
        if x in found:
            continue
        if all(dot(row, x) <= z for row, z in zip(NORMALS, rhs)):
            if first_only:
                return (x,)
            found.add(x)
    return tuple(sorted(found))


def tighten(a, b):
    points = vertices(a, b)
    if not points:
        return None
    lo = (F(0),) + tuple(min(sumset(x, s) for x in points) for s in MASKS)
    hi = (F(0),) + tuple(max(sumset(x, s) for x in points) for s in MASKS)
    return lo, hi


def in_class(K):
    if K is None:
        return True
    a, b = K
    return all(b[s]+b[t] >= b[s|t]+b[s&t] and a[s]+a[t] <= a[s|t]+a[s&t]
               for s in range(8) for t in range(8))


CROSSCHECK = False


def submasks(s):
    t = s
    while True:
        yield t
        if t == 0:
            return
        t = (t - 1) & s


def tighten_closed(a, b):
    """Tight bounds of {a(S) <= x(S) <= b(S)} for b submodular, a supermodular (Lemma 3), or None.

    Nonempty iff a <= b pointwise (Frank's sandwich theorem).  Closed forms, {i,j,k} = {1,2,3}:
      beta(i)  = min{b_i, b_ij - a_j, b_ik - a_k, b_V - a_jk},   beta(V) = b_V,
      beta(ij) = min{b_ij, b_V - a_k, b_V + b_i - a_ik, b_V + b_j - a_jk},
    and the mirror images for alpha (swap min/max and the roles of a, b)."""
    if any(a[s] > b[s] for s in MASKS):
        return None
    lo, hi = [F(0)] * 8, [F(0)] * 8
    for i in range(3):
        s = 1 << i
        j, k = [1 << m for m in range(3) if m != i]
        hi[s] = min(b[s], b[s | j] - a[j], b[s | k] - a[k], b[7] - a[j | k])
        lo[s] = max(a[s], a[s | j] - b[j], a[s | k] - b[k], a[7] - b[j | k])
        p, r = j | k, s                                   # pair p = {j,k}, remaining element r = i
        hi[p] = min(b[p], b[7] - a[r], b[7] + b[j] - a[j | r], b[7] + b[k] - a[k | r])
        lo[p] = max(a[p], a[7] - b[r], a[7] + a[j] - b[j | r], a[7] + a[k] - b[k | r])
    hi[7], lo[7] = b[7], a[7]
    return tuple(lo), tuple(hi)


def step(K, E, C, D, l, u):
    if K is None:
        return None
    l, u = q(l), q(u)
    if l > u:
        raise ValueError('empty request interval')
    if l < -sum(C) or u > sum(D):
        return None
    a, b = K
    aa, bb = [F(0)], [F(0)]
    for s in MASKS:
        comp = 7 ^ s
        aa.append(a[s] + max(-sumset(C, s), u-sumset(D, comp)))
        bb.append(b[s] + min(sumset(D, s), l+sumset(C, comp)))
    # physical box: b <- b conv E (submodular), a <- max over submasks with a(∅)=0 (supermodular)
    bb = [F(0)] + [min(bb[t] + sumset(E, s ^ t) for t in submasks(s)) for s in MASKS]
    aa = [F(0)] + [max(aa[t] for t in submasks(s)) for s in MASKS]
    out = tighten_closed(aa, bb)
    if CROSSCHECK:
        assert out == tighten(aa, bb), 'closed-form tightening disagrees with vertex enumeration'
        assert in_class(out), 'N=3 invariant violated in exact arithmetic'
    return out


def kernels(E, C, D, menus):
    E, C, D = [tuple(map(q, v)) for v in (E, C, D)]
    if any(len(v) != 3 for v in (E, C, D)) or min(E+C+D) < 0:
        raise ValueError('three nonnegative device parameter vectors required')
    out = [None] * (len(menus)+1)
    out[-1] = (tuple(F(0) for _ in range(8)), tuple(sumset(E, s) for s in range(8)))
    for t in range(len(menus)-1, -1, -1):
        out[t] = step(out[t+1], E, C, D, *menus[t])
    return out


def action(e, y, next_K, C, D):
    """Choose one feasible next-state vertex using only current e,y and next_K."""
    if next_K is None:
        raise ValueError('empty next kernel')
    e, C, D = [tuple(map(q, v)) for v in (e, C, D)]
    y = q(y)
    a, b = map(list, next_K)
    for i in range(3):
        s = 1 << i
        a[s], b[s] = max(a[s], e[i]-D[i]), min(b[s], e[i]+C[i])
    total = sum(e)-y
    a[7], b[7] = max(a[7], total), min(b[7], total)
    points = vertices(a, b, first_only=True)
    if not points:
        raise ValueError('no feasible action')
    return tuple(e[i]-points[0][i] for i in range(3))


def validate():
    global CROSSCHECK
    CROSSCHECK = True
    import numpy as np
    from oracle2 import build, support
    rng = np.random.default_rng(20260926)
    cases = [([4, 4, 4], [2, .5, .5], [2, .5, .5], [(-.5, 2), (0, 1.5), (-3, 2.5)]),
             ([0, 0, 0], [0, 0, 0], [0, 0, 0], [(0, 0)]),
             ([0, 0, 0], [0, 0, 0], [0, 0, 0], [(0, 1)]),
             ([0, 2, 3], [0, 1, .5], [0, .5, 2], [(-.5, .5), (0, 1)]),
             ([1, 1, 1], [0, 0, 0], [0, 0, 0], [(0, 0)]),
             ([1, 1, 1], [1, 1, 1], [1, 1, 1], [(3, 3)])]
    for _ in range(40):
        E = rng.integers(1, 5, 3).tolist()
        C = (rng.integers(0, 5, 3)/2).tolist()
        D = (rng.integers(0, 5, 3)/2).tolist()
        ms = [tuple(sorted((rng.integers(-2, 3, 2)/2).tolist()))
              for _ in range(int(rng.integers(1, 5)))]
        cases.append((E, C, D, ms))
    stats = dict(cases=0, feasible=0, empty=0, support_checks=0, exact_actions=0)
    for E, C, D, ms in cases:
        ks = kernels(E, C, D, ms)
        M = build(np.array(C), np.array(D), np.array(E), ms)
        first = support(M, [1, 1, 1])
        assert (ks[0] is None) == (first is None), (E, C, D, ms)
        stats['cases'] += 1
        if ks[0] is None:
            stats['empty'] += 1
            continue
        stats['feasible'] += 1
        a, b = ks[0]
        for s, row in zip(MASKS, VECTORS):
            assert abs(float(b[s])-support(M, row)[1]) < 1e-7
            assert abs(float(a[s])+support(M, -np.array(row))[1]) < 1e-7
            stats['support_checks'] += 2
        # Midpoint request at every step, starting at an exact viable vertex.
        e = vertices(a, b, first_only=True)[0]
        for t, (l, u) in enumerate(ms):
            y = (q(l)+q(u))/2
            p = action(e, y, ks[t+1], C, D)
            assert sum(p) == y
            assert all(-q(C[i]) <= p[i] <= q(D[i]) for i in range(3))
            e = tuple(e[i]-p[i] for i in range(3))
            aa, bb = ks[t+1]
            assert all(aa[s] <= sumset(e, s) <= bb[s] for s in MASKS)
            stats['exact_actions'] += 1
    print(stats)


if __name__ == '__main__':
    validate()
