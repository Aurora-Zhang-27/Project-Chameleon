"""Independent audit of commit babbb91. No imports from repository implementations.

State-variable endpoint-tree LP; separately transcribed closed recursion; exact
Fraction vertex enumeration; rational primal/dual certificate verification.
Run from evidence/: python3 review_codex_independent.py
"""
import itertools as it
import json
from fractions import Fraction as F
from functools import lru_cache
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix


def rat(x):
    return x if isinstance(x, F) else F(str(x))


def subsets(s):
    return [t for t in range(s+1) if t & s == t]


def val(x, s):
    return sum((v for i, v in enumerate(x) if s >> i & 1), F(0))


def upper(a, b):
    ans = [F(0)] * 8
    for s in range(1, 8):
        ids = [i for i in range(3) if s >> i & 1]
        if len(ids) == 1:
            ans[s] = min(b[t]-a[t ^ s] for t in range(8) if t & s == s)
        elif len(ids) == 3:
            ans[s] = b[7]
        else:
            k = 7 ^ s
            i, j = [1 << m for m in ids]
            ans[s] = min(b[s], b[7]-a[k], b[7]+b[i]-a[i | k], b[7]+b[j]-a[j | k])
    return ans


def tight_closed(a, b):
    if any(x > y for x, y in zip(a, b)):
        return None
    return [-x for x in upper([-x for x in b], [-x for x in a])], upper(a, b)


def closed(E, C, D, menus):
    E, C, D = [list(map(rat, v)) for v in (E, C, D)]
    a, b = [F(0)]*8, [val(E, s) for s in range(8)]
    for l, u in reversed(menus):
        l, u = rat(l), rat(u)
        if l > u:
            raise ValueError('invalid interval')
        if l < -sum(C) or u > sum(D):
            return None
        low = [a[s]+max(-val(C, s), u-val(D, 7 ^ s)) for s in range(8)]
        high = [b[s]+min(val(D, s), l+val(C, 7 ^ s)) for s in range(8)]
        aa = [max(low[t] for t in subsets(s)) for s in range(8)]
        bb = [min(high[t]+val(E, s ^ t) for t in subsets(s)) for s in range(8)]
        result = tight_closed(aa, bb)
        if result is None:
            return None
        a, b = result
        assert mod_ok(a, b)
    return a, b


def mod_ok(a, b):
    return all(a[s]+a[t] <= a[s | t]+a[s & t] and b[s]+b[t] >= b[s | t]+b[s & t]
               for s in range(8) for t in range(8))


def inverse(rows):
    n = len(rows)
    m = [[F(x) for x in r] + [F(i == j) for j in range(n)] for i, r in enumerate(rows)]
    for col in range(n):
        pivot = next((i for i in range(col, n) if m[i][col]), None)
        if pivot is None:
            return None
        m[pivot], m[col] = m[col], m[pivot]
        d = m[col][col]
        m[col] = [x/d for x in m[col]]
        for i in range(n):
            if i != col:
                d = m[i][col]
                m[i] = [x-d*y for x, y in zip(m[i], m[col])]
    return [r[n:] for r in m]


@lru_cache(None)
def basis_data():
    rows = [tuple(sign*((s >> i) & 1) for i in range(3))
            for sign in (1, -1) for s in range(1, 8)]
    bases = []
    for ids in it.combinations(range(14), 3):
        inv = inverse([rows[i] for i in ids])
        if inv is not None:
            bases.append((ids, inv))
    return rows, bases


def verts(a, b):
    rows, bases = basis_data()
    rhs = b[1:] + [-x for x in a[1:]]
    out = set()
    for ids, inv in bases:
        x = tuple(sum(row[j]*rhs[ids[j]] for j in range(3)) for row in inv)
        if x not in out and all(sum(z*v for z, v in zip(row, x)) <= d for row, d in zip(rows, rhs)):
            out.add(x)
    return sorted(out)


class StateTree:
    """Variables are root energy and post-request energies, never pathwise allocations."""
    def __init__(self, E, C, D, menus):
        self.E, self.C, self.D = [list(map(rat, v)) for v in (E, C, D)]
        self.n = len(E)
        self.nodes = []
        frontier = [0]
        for lo, hi in menus:
            following = []
            for parent in frontier:
                for y in sorted({rat(lo), rat(hi)}):
                    k = len(self.nodes)+1
                    self.nodes.append((parent, k, y))
                    following.append(k)
            frontier = following
        self.nv = self.n*(1+len(self.nodes))
        self.eq, self.ub, self.be, self.bu = [], [], [], []
        for parent, k, y in self.nodes:
            row = []
            for i in range(self.n):
                pair = [(self.n*parent+i, 1), (self.n*k+i, -1)]
                row.extend(pair)
                self.ub.append(pair)
                self.bu.append(self.D[i])
                self.ub.append([(j, -c) for j, c in pair])
                self.bu.append(self.C[i])
            self.eq.append(row)
            self.be.append(y)
        def matrix(rows):
            entries = [(i, j, c) for i, row in enumerate(rows) for j, c in row]
            return coo_matrix(([z[2] for z in entries], ([z[0] for z in entries], [z[1] for z in entries])),
                              shape=(len(rows), self.nv)).tocsr()
        self.Ae, self.Au = matrix(self.eq), matrix(self.ub)
        self.bounds = [(F(0), self.E[i]) for _ in range(1+len(self.nodes)) for i in range(self.n)]

    def run(self, direction=None, root=None):
        direction = [0]*self.n if direction is None else direction
        c = [-rat(x) for x in direction]+[F(0)]*(self.nv-self.n)
        bd = list(self.bounds)
        if root is not None:
            bd[:self.n] = [(x, x) for x in root]
        r = linprog(np.array(c, float), A_ub=self.Au, b_ub=np.array(self.bu, float),
                    A_eq=self.Ae, b_eq=np.array(self.be, float),
                    bounds=[(float(a), float(b)) for a, b in bd], method='highs')
        if r.status not in (0, 2):
            raise RuntimeError(r.message)
        if r.status == 2:
            return None
        exact_p = exact_d = False
        witness = None
        for cap in (1000, 1000000):
            x = [F(float(v)).limit_denominator(cap) for v in r.x]
            pdot = lambda row: sum(co*x[j] for j, co in row)
            exact_p = (all(a <= z <= b for z, (a, b) in zip(x, bd))
                       and all(pdot(row) == z for row, z in zip(self.eq, self.be))
                       and all(pdot(row) <= z for row, z in zip(self.ub, self.bu)))
            if not exact_p:
                continue
            witness = x[:self.n]
            if root is not None:
                break
            du = [[F(float(v)).limit_denominator(cap) for v in arr] for arr in
                  (r.eqlin.marginals, r.ineqlin.marginals, r.lower.marginals, r.upper.marginals)]
            lam, mu, dl, dh = du
            station = [a+b for a, b in zip(dl, dh)]
            for row, w in it.chain(zip(self.eq, lam), zip(self.ub, mu)):
                if w:
                    for j, co in row:
                        station[j] += co*w
            dual = sum(z*w for z, w in zip(self.be, lam))+sum(z*w for z, w in zip(self.bu, mu))
            dual += sum(a*l+b*h for (a, b), l, h in zip(bd, dl, dh))
            primal = sum(v*w for v, w in zip(c, x))
            exact_d = (all(w <= 0 for w in mu+dh) and all(w >= 0 for w in dl)
                       and station == c and primal == dual)
            if exact_d:
                break
        return dict(value=-r.fun, primal=exact_p, dual=exact_d, witness=witness,
                    solution=x if exact_p else None)


def attacks():
    cases = []
    for T in (5, 6):
        cases += [('all_zero', [0]*3, [0]*3, [0]*3, [(0, 0)]*T),
                  ('zero_impossible', [0]*3, [0]*3, [0]*3, [(0, 0)]*(T-1)+[(0, F(1, 100))]),
                  ('inert_device', [0, 2, 3], [0, F(1,100), 1], [0, 1, F(1,100)], [(-F(1,100), F(1,100))]*T),
                  ('ratio100', [4, 5, 1], [1, F(1,100), F(1,2)], [F(1,100), 1, F(1,10)], [(-F(1,100), F(1,100))]*T),
                  ('deterministic', [1, 2, 3], [0, 1, 100], [100, 1, 0], [(0, 0)]*T),
                  ('capacity_zero', [0, 1, 0], [100, 1, 1], [1, 1, 100], [(-F(1,10), F(1,10))]*T)]
    rng = np.random.default_rng(928)
    for k in range(48):
        E = [F(int(v), 10) for v in rng.choice([0, 1, 10, 30, 100], 3)]
        choices = [F(0), F(1,100), F(1,10), F(1), F(100)]
        C = [choices[int(i)] for i in rng.integers(0, 5, 3)]
        D = [choices[int(i)] for i in rng.integers(0, 5, 3)]
        T = 5+k%2
        menus = []
        for t in range(T):
            if k % 4 == 0:
                y = F(int(rng.integers(-1, 2)), 100)
                menus.append((y, y))
            else:
                menus.append((-F(int(rng.integers(0, 3)), 100), F(int(rng.integers(0, 3)), 100)))
        cases.append(('random_extreme', E, C, D, menus))
    stats = dict(cases=0, nonempty=0, empty=0, vertices=0, exact_vertex_witnesses=0,
                 subset_supports=0, mixed_supports=0, exact_support_certificates=0, failures=0)
    mixed = [v for v in it.product((-1, 0, 1), repeat=3) if min(v) < 0 < max(v)]
    for label, E, C, D, menus in cases:
        K = closed(E, C, D, menus)
        tree = StateTree(E, C, D, menus)
        first = tree.run([1, 1, 1])
        assert (K is None) == (first is None), (label, E, C, D, menus)
        stats['cases'] += 1
        if K is None:
            stats['empty'] += 1
            continue
        stats['nonempty'] += 1
        points = verts(*K)
        assert points
        for point in points:
            r = tree.run(root=point)
            assert r is not None, (label, point)
            stats['vertices'] += 1
            stats['exact_vertex_witnesses'] += int(r['primal'])
        signed = [tuple(sign*((s >> i) & 1) for i in range(3)) for sign in (-1, 1) for s in range(1, 8)]
        for direction in signed+mixed:
            r = tree.run(direction)
            bound = max(sum(q*x for q, x in zip(direction, p)) for p in points)
            assert r is not None and abs(r['value']-float(bound)) <= 1e-7
            if r['primal'] and r['dual']:
                assert sum(q*x for q, x in zip(direction, r['witness'])) == bound
            stats['subset_supports' if direction in signed else 'mixed_supports'] += 1
            stats['exact_support_certificates'] += int(r['primal'] and r['dual'])
        if stats['cases'] % 10 == 0:
            print('AB progress', stats, flush=True)
    print('AB RESULT', json.dumps(stats), flush=True)


def descriptions():
    rng = np.random.default_rng(929)
    stats = dict(cases=0, raw_not_tight=0, exact_vertex_comparisons=0, lp_support_checks=0,
                 submod_violations=0)
    for trial in range(160):
        funcs = []
        for side in range(2):
            f = [F(0)]*8
            for _ in range(7):
                typ, weight = int(rng.integers(0, 3)), F(int(rng.integers(0, 5)))
                mask = int(rng.integers(1, 8))
                i, j = map(int, rng.choice(3, 2, replace=False))
                for s in range(8):
                    if typ == 0:  # coverage
                        f[s] += weight*bool(s & mask)
                    elif typ == 1:  # directed cut
                        f[s] += weight*bool(s >> i & 1)*(not bool(s >> j & 1))
                    else:  # modular minus AND
                        f[s] += weight*(bin(s & mask).count('1')-int(s & mask == mask))
            funcs.append(f)
        m = [F(int(v)) for v in rng.integers(-3, 4, 3)]
        a = [val(m, s)-funcs[0][s] for s in range(8)]
        b = [val(m, s)+funcs[1][s] for s in range(8)]
        assert mod_ok(a, b) and all(x <= y for x, y in zip(a, b))
        aa, bb = tight_closed(a, b)
        points = verts(a, b)
        assert points
        assert aa == [min(val(p, s) for p in points) for s in range(8)]
        assert bb == [max(val(p, s) for p in points) for s in range(8)]
        assert mod_ok(aa, bb)
        rows, _ = basis_data()
        rhs = b[1:]+[-x for x in a[1:]]
        for s in range(1, 8):
            for sign in (-1, 1):
                direction = [sign*((s >> i) & 1) for i in range(3)]
                r = linprog(-np.array(direction), A_ub=rows, b_ub=np.array(rhs, float),
                            bounds=[(None, None)]*3, method='highs')
                expected = bb[s] if sign == 1 else -aa[s]
                assert r.status == 0 and abs(-r.fun-float(expected)) < 1e-7
                stats['lp_support_checks'] += 1
        stats['cases'] += 1
        stats['raw_not_tight'] += int((a, b) != (aa, bb))
        stats['exact_vertex_comparisons'] += 14
    print('C RESULT', json.dumps(stats), flush=True)


def algebra():
    # F3 indicator identity, independently enumerate each legal element membership.
    count = 0
    for x, y, xp, yp in it.product((0, 1), repeat=4):
        if xp > x or yp > y:
            continue
        assert x-xp+y-yp == max(x,y)-max(xp,yp)+min(x,y)-min(xp,yp)
        count += 1
    # The invalid pair-version of Lemma 3(a), explicit exact counterexample.
    a = [F(bool(s & 5 == 5)) for s in range(8)]
    ap = [max(a[s], 1+a[s ^ 3]) if s & 3 == 3 else a[s] for s in range(8)]
    assert ap[3]+ap[5] > ap[7]+ap[1]
    print('ALGEBRA', dict(F3_element_patterns=count, pair_extension_violation=str(ap[3]+ap[5]-ap[7]-ap[1])))


if __name__ == '__main__':
    algebra()
    attacks()
    descriptions()
