"""Independent attacks A-D and exact Example C certificates, commit 63837d1.

No imports of homogeneous_exact, oracle2, n3_exact or other repository solvers.
LP candidates come from SciPy; Fraction primal/dual identities certify finite
optima. All vertices for m<=4 are found via sorted chambers and exact bases.
Run: python3 -u review_codex_h_independent.py
"""
import itertools as it
import json
from fractions import Fraction as F
from functools import lru_cache
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix


def dot(x, y):
    return sum((a*b for a, b in zip(x, y)), F(0))


def sparse(rows, n):
    terms = [(i, j, c) for i, row in enumerate(rows) for j, c in row if c]
    return coo_matrix(([z[2] for z in terms], ([z[0] for z in terms], [z[1] for z in terms])),
                      shape=(len(rows), n)).tocsr()


class Model:
    def __init__(self, n, eq, be, ub, bu, bounds):
        self.n, self.eq, self.be, self.ub, self.bu, self.bounds = n, eq, be, ub, bu, bounds
        self.Ae, self.Au = sparse(eq, n), sparse(ub, n)

    def solve(self, c, fixed=None):
        c = list(map(F, c))
        bd = list(self.bounds)
        if fixed is not None:
            bd[:len(fixed)] = [(v, v) for v in fixed]
        opts = [dict(), dict(presolve=False)]
        for attempt, options in enumerate(opts):
            r = linprog(np.array(c, float), A_eq=self.Ae if self.eq else None,
                        b_eq=np.array(self.be, float) if self.eq else None,
                        A_ub=self.Au if self.ub else None,
                        b_ub=np.array(self.bu, float) if self.ub else None,
                        bounds=[(None if lo is None else float(lo), None if hi is None else float(hi))
                                for lo, hi in bd], method='highs', options=options)
            if r.status == 0:
                break
            if r.status != 2:
                raise RuntimeError(r.message)
        else:
            return None
        for cap in (10000, 1000000):
            x = [F(float(v)).limit_denominator(cap) for v in r.x]
            evaluate = lambda row: sum(co*x[j] for j, co in row)
            primal = (all((lo is None or lo<=v) and (hi is None or v<=hi) for v, (lo, hi) in zip(x, bd))
                      and all(evaluate(row)==rhs for row, rhs in zip(self.eq, self.be))
                      and all(evaluate(row)<=rhs for row, rhs in zip(self.ub, self.bu)))
            if not primal:
                continue
            lam, mu, dl, dh = [[F(float(v)).limit_denominator(cap) for v in arr] for arr in
                              (r.eqlin.marginals, r.ineqlin.marginals, r.lower.marginals, r.upper.marginals)]
            station = [a+b for a, b in zip(dl, dh)]
            for row, weight in it.chain(zip(self.eq, lam), zip(self.ub, mu)):
                for j, co in row:
                    station[j] += co*weight
            dual_value = dot(self.be, lam)+dot(self.bu, mu)
            for (lo, hi), v, w in zip(bd, dl, dh):
                if lo is not None:
                    dual_value += lo*v
                elif v:
                    break
                if hi is not None:
                    dual_value += hi*w
                elif w:
                    break
            else:
                dual = (all(v<=0 for v in mu+dh) and all(v>=0 for v in dl)
                        and station==c and dual_value==dot(c, x))
                if dual:
                    return dict(x=x, value=-dot(c, x), fallback=attempt)
        raise AssertionError('Floating candidate has no exact primal-dual certificate')


class Tree(Model):
    def __init__(self, E, C, D, menus):
        m = len(E)
        nodes, frontier = [], [0]
        for lo, hi in menus:
            following = []
            for parent in frontier:
                for y in sorted({lo, hi}):
                    child = len(nodes)+1
                    nodes.append((parent, child, y))
                    following.append(child)
            frontier = following
        eq, be, ub, bu = [], [], [], []
        for parent, child, y in nodes:
            balance = []
            for i in range(m):
                row = [(m*parent+i, 1), (m*child+i, -1)]
                balance.extend(row)
                ub.extend([row, [(j, -c) for j, c in row]])
                bu.extend([D[i], C[i]])
            eq.append(balance)
            be.append(y)
        n = m*(len(nodes)+1)
        bounds = [(F(0), E[i]) for _ in range(len(nodes)+1) for i in range(m)]
        super().__init__(n, eq, be, ub, bu, bounds)
        self.m, self.nodes = m, nodes

    def support(self, w):
        return self.solve([-v for v in w]+[0]*(self.n-self.m))

    def member(self, e):
        return self.solve([0]*self.n, fixed=e)


def tighten(a, b):
    m = len(a)-1
    if a[m]>b[m]:
        return None
    return ([max(a[k], a[m]-b[m-k]) for k in range(m+1)],
            [min(b[k], b[m]-a[m-k]) for k in range(m+1)])


def kernels(m, E, C, D, menus):
    out = [None]*(len(menus)+1)
    out[-1] = ([F(0)]*(m+1), [E*k for k in range(m+1)])
    for t in reversed(range(len(menus))):
        lo, hi = menus[t]
        if out[t+1] is None or lo < -m*C or hi > m*D:
            continue
        a, b = out[t+1]
        aa = [max(F(0), a[k]+max(-C*k, hi-D*(m-k))) for k in range(m+1)]
        bb = [min(E*k, b[k]+min(D*k, lo+C*(m-k))) for k in range(m+1)]
        out[t] = tighten(aa, bb)
        if out[t] is not None:
            a, b = out[t]
            assert a[0]==b[0]==0
            assert all(a[k-1]+a[k+1]>=2*a[k] and b[k-1]+b[k+1]<=2*b[k] for k in range(1, m))
    return out


@lru_cache(None)
def chamber_rows(m):
    rows = [tuple(int(i<k) for i in range(m)) for k in range(1, m+1)]
    rows += [tuple(-int(i>=m-k) for i in range(m)) for k in range(1, m+1)]
    rows += [tuple(-int(i==k)+int(i==k+1) for i in range(m)) for k in range(m-1)]
    return rows


def chamber(a, b):
    m = len(a)-1
    rows = chamber_rows(m)
    ub = [[(i, v) for i, v in enumerate(row) if v] for row in rows]
    return Model(m, [], [], ub, b[1:]+[-v for v in a[1:]]+[F(0)]*(m-1), [(None, None)]*m)


def eliminate(rows, inverse=False):
    n = len(rows[0]) if rows else 0
    mat = [list(map(F, row)) + ([F(i==j) for j in range(n)] if inverse else [])
           for i, row in enumerate(rows)]
    rank = 0
    for col in range(n):
        p = next((i for i in range(rank, len(mat)) if mat[i][col]), None)
        if p is None:
            continue
        mat[p], mat[rank] = mat[rank], mat[p]
        q = mat[rank][col]
        mat[rank] = [x/q for x in mat[rank]]
        for i in range(len(mat)):
            if i != rank:
                q = mat[i][col]
                mat[i] = [x-q*y for x, y in zip(mat[i], mat[rank])]
        rank += 1
    return ([row[n:] for row in mat] if rank==n else None) if inverse else rank


@lru_cache(None)
def bases(m):
    rows = chamber_rows(m)
    result = []
    for ids in it.combinations(range(len(rows)), m):
        inv = eliminate([rows[i] for i in ids], inverse=True)
        if inv is not None:
            result.append((ids, inv))
    return result


def chamber_vertices(a, b, true_vertices=False):
    m = len(a)-1
    rows = chamber_rows(m)
    rhs = b[1:]+[-v for v in a[1:]]+[F(0)]*(m-1)
    points = set()
    for ids, inv in bases(m):
        point = tuple(dot(row, [rhs[i] for i in ids]) for row in inv)
        if all(dot(row, point)<=z for row, z in zip(rows, rhs)):
            points.add(point)
    if true_vertices:
        full = [tuple(sign*int(s>>i&1) for i in range(m)) for sign in (1, -1) for s in range(1, 1<<m)]
        fullrhs = [b[bin(s).count('1')] for s in range(1, 1<<m)]+[-a[bin(s).count('1')] for s in range(1, 1<<m)]
        points = {point for point in points if eliminate([row for row, z in zip(full, fullrhs)
                                                         if dot(row, point)==z])==m}
    return sorted(points)


def in_kernel(K, e):
    if K is None:
        return False
    a, b = K
    x = sorted(e)
    prefix = [F(0)]
    for v in x:
        prefix.append(prefix[-1]+v)
    return all(prefix[k]>=a[k] and prefix[-1]-prefix[len(x)-k]<=b[k] for k in range(1, len(x)+1))


def waterfill(e, C, D, y):
    lo, hi, total = [x-D for x in e], [x+C for x in e], sum(e)-y
    if not sum(lo)<=total<=sum(hi):
        return None
    knots = sorted(set(lo+hi))
    f = lambda z: sum(min(max(z, a), b) for a, b in zip(lo, hi))
    for z in knots:
        if f(z)==total:
            return [min(max(z, a), b) for a, b in zip(lo, hi)]
    for left, right in zip(knots, knots[1:]):
        fl, fr = f(left), f(right)
        if fl<total<fr:
            z = left+(right-left)*(total-fl)/(fr-fl)
            return [min(max(z, a), b) for a, b in zip(lo, hi)]
    raise AssertionError('no waterfill interval')


def policy(e, E, C, D, menus):
    levels = [[lo, (2*lo+hi)/3, (lo+2*hi)/3, hi] for lo, hi in menus]
    frontier = [e]
    steps = 0
    for ys in levels:
        following = []
        for e in frontier:
            for y in sorted(set(ys)):
                x = waterfill(e, C, D, y)
                steps += 1
                if x is None or any(z<0 or z>E for z in x):
                    return False, steps
                assert sum(e)-sum(x)==y and all(-C<=z-v<=D for z, v in zip(e, x))
                following.append(x)
        frontier = following
    return True, steps


def attacks():
    rng = np.random.default_rng(1009)
    cases = []
    profiles = [(F(1),F(0),F(0)), (F(0),F(1),F(1)), (F(1),F(100),F(1)),
                (F(1),F(1),F(100)), (F(1,100),F(100),F(100)),
                (F(3),F(1),F(1)), (F(2),F(0),F(1)), (F(2),F(1),F(0))]
    for m in range(1,9):
        for T in range(1,6):
            for rep in range(2):
                E,C,D = profiles[(m+T+rep*3)%len(profiles)]
                q = max(E,F(1,100))/(20*T)
                ms = [(-q, q) if (t+rep)%3 else (F(0),F(0)) for t in range(T)]
                cases.append((m,E,C,D,ms))
    for m in range(1,9):
        cases.append((m,F(0),F(0),F(0),[(F(0),F(0))]*5))
        # Nonzero-capacity lower-dimensional kernel: total energy is forced to m/2.
        cases.append((m,F(1),F(1),F(1),[(-F(m,2),F(m,2))]+[(F(0),F(0))]*4))
    for m in range(1,5):
        for trial in range(12):
            E=F(int(rng.integers(1,7)),2)
            C=F(int(rng.integers(1,7)),3)
            D=F(int(rng.integers(1,7)),3)
            T=1+trial%5
            q=min(E/(4*T),C/3,D/3)
            menus=[(-q,F(int(rng.integers(1,4)),3)*q) for _ in range(T)]
            cases.append((m,E,C,D,menus))
    st = dict(cases=0, nonempty=0, empty=0, exact_subset_supports=0, mixed_orbits=0,
              mixed_directions_covered=0, vertex_orbits=0, vertices=0, lowdim_cases=0,
              point_checks=0, policy_points=0, policy_transitions=0, fallbacks=0)
    for m,E,C,D,ms in cases:
        ks = kernels(m,E,C,D,ms)
        tree = Tree([E]*m,[C]*m,[D]*m,ms)
        initial = tree.support([1]*m)
        assert (initial is None)==(ks[0] is None)
        st['cases']+=1
        if initial is None:
            st['empty']+=1
        else:
            st['nonempty']+=1
            a,b = ks[0]
            for k in range(1,m+1):
                for sign in (1,-1):
                    r = tree.support([sign]*k+[0]*(m-k))
                    assert r is not None and r['value']==(b[k] if sign==1 else -a[k])
                    st['exact_subset_supports']+=1
                    st['fallbacks']+=r['fallback']
            outer = chamber(a,b)
            for p in range(1,m):
                for n in range(1,m-p+1):
                    w = [1]*p+[0]*(m-p-n)+[-1]*n
                    real, bound = tree.support(w), outer.solve([-v for v in w])
                    assert real is not None and bound is not None and real['value']==bound['value']
                    st['mixed_orbits']+=1
                    st['mixed_directions_covered']+=__import__('math').comb(m,p)*__import__('math').comb(m-p,n)
            if m<=4:
                points = chamber_vertices(a,b,true_vertices=True)
                assert points
                allpoints = set()
                for point in points:
                    r = tree.member(point)
                    assert r is not None
                    # A simultaneous permutation of the exact tree policy certifies each orbit member.
                    allpoints.update(it.permutations(point))
                    st['vertex_orbits']+=1
                st['vertices']+=len(allpoints)
                st['lowdim_cases']+=int(a[m]==b[m] or a[1]==b[1])
        roots = [[F(0)]*m, [E]*m, [E/2]*m,
                 [E*F(int(v),4) for v in rng.integers(0,5,m)]]
        for e in roots:
            r = tree.member(e)
            inside = in_kernel(ks[0],e)
            assert (r is not None)==inside
            survives, steps = policy(e,E,C,D,ms)
            assert survives==inside
            st['point_checks']+=1
            st['policy_points']+=1
            st['policy_transitions']+=steps
        if st['cases']%16==0:
            print('AB/D progress',st,flush=True)
    print('AB/D RESULT',json.dumps(st),flush=True)


def lemma_tests():
    rng=np.random.default_rng(1010)
    st=dict(cases=0, nonempty=0, empty=0, exact_supports=0, exact_vertex_comparisons=0,
            raw_not_tight=0, negative_entries=0)
    for m in range(1,9):
        for trial in range(12):
            db=sorted([F(int(v),3) for v in rng.integers(-9,10,m)],reverse=True)
            da=sorted([F(int(v),3) for v in rng.integers(-9,10,m)])
            # Half the inputs have an adjustable modular shift, including deliberately empty ones.
            shift=F(int(rng.integers(-3,4)))
            da=[v+shift for v in da]
            a,b=[F(0)],[F(0)]
            for u,v in zip(da,db):
                a.append(a[-1]+u); b.append(b[-1]+v)
            st['cases']+=1
            model=chamber(a,b)
            first=model.solve([0]*m)
            tight=tighten(a,b)
            assert (first is None)==(tight is None)
            if first is None:
                st['empty']+=1; continue
            st['nonempty']+=1
            aa,bb=tight
            st['raw_not_tight']+=int((aa,bb)!=(a,b))
            st['negative_entries']+=int(any(v<0 for v in a+b))
            for k in range(1,m+1):
                hi=model.solve([-1]*k+[0]*(m-k))
                lo=model.solve([0]*(m-k)+[1]*k)
                assert hi['value']==bb[k] and lo['value']==-aa[k]
                st['exact_supports']+=2
            if m<=4:
                points=chamber_vertices(a,b)
                assert points
                assert [F(0)]+[max(sum(x[:k]) for x in points) for k in range(1,m+1)]==bb
                assert [F(0)]+[min(sum(x[-k:]) for x in points) for k in range(1,m+1)]==aa
                st['exact_vertex_comparisons']+=2*m
    print('C RESULT',json.dumps(st),flush=True)


def example_c():
    for eps in (F(0),F(1,100)):
        E=[F(4),F(4),F(1),F(1)]
        C=[eps,eps,F(3),F(1,2)];D=[F(1),F(1),F(2),eps]
        menus=[(F(1,5),F(3,5)),(F(-1),F(8,5))]
        tree=Tree(E,C,D,menus)
        e=[F(19,10),F(1,10),F(1,5),F(1)] if not eps else [F(47,25),F(3,50),F(6,25),F(1)]
        for s in range(1,16):
            w=[int(s>>i&1) for i in range(4)]
            hi=tree.support(w);lo=tree.support([-v for v in w])
            assert -lo['value']<=dot(e,w)<=hi['value']
        bound=tree.support([0,-1,0,1])
        rhs=F(2,5)+5*eps
        assert bound['value']==rhs<e[3]-e[1]
        print('EXAMPLE C EXACT',dict(eps=str(eps),subset_optima=30,lhs=str(e[3]-e[1]),
                                     rhs=str(rhs),estar_in_true_subset_hull=True),flush=True)


if __name__=='__main__':
    attacks()
    lemma_tests()
    example_c()
