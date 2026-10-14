"""Example B (layer 3, real recursion): exact rational certificate that K_0 differs from its
subset outer approximation for N=4, T=2.
Instance: E=(4,5,1,1), C=(eps,eps,3,1/2), D=(1,1/2,2,eps), requests [1/5, 1] then [-1, 6/5];
eps = 0 (default) or eps = 1/100 (all powers strictly positive).
(a) For each of the 30 subset directions, a rational endpoint-tree policy is found by LP and then
    verified exactly; it certifies a point of K_0, hence bh(S) <= max_K0 e(S) and ah(S) >= min_K0 e(S).
    Only feasibility is certified exactly; optimality is not needed for the counterexample.
    Q = {ah <= e(S) <= bh} lies inside the subset outer approximation of K_0.
(b) An exact vertex e* of Q maximizing e1 - e2 + e4.
(c) Elementary valid inequalities for K_0 (derived by hand in the document) that e* violates.
Endpoint-tree sufficiency: SEED_N2_THEOREM.md §4 convexity argument (also Xie & Chen Prop 2).
With --three-types (added 2026-10-07, HOMOGENEOUS_FLEET.md §4) the instance is Example C: devices 1 and 2
are identical, so the fleet has only three device types: E=(4,4,1,1), C=(0,0,3,1/2), D=(1,1,2,0),
requests [1/5, 3/5] then [-1, 8/5]; the valid inequality is e4 - e2 <= 2/5.
Usage: python3 n4_real_certificate.py [eps] [--three-types]   e.g.  python3 n4_real_certificate.py 1/100"""
import itertools, sys
import numpy as np
from fractions import Fraction as F
from scipy.optimize import linprog

args = [x for x in sys.argv[1:] if not x.startswith('--')]
three = '--three-types' in sys.argv
eps = F(args[0]) if args else F(0)
N = 4; MS = range(1, 16)
if three:
    E = [F(4), F(4), F(1), F(1)]; C = [eps, eps, F(3), F(1, 2)]; D = [F(1), F(1), F(2), eps]
    Y0 = [F(1, 5), F(3, 5)]; Y1 = [F(-1), F(8, 5)]
else:
    E = [F(4), F(5), F(1), F(1)]; C = [eps, eps, F(3), F(1, 2)]; D = [F(1), F(1, 2), F(2), eps]
    Y0 = [F(1, 5), F(1)]; Y1 = [F(-1), F(6, 5)]
ind = lambda s: [1 if s >> i & 1 else 0 for i in range(N)]
ss = lambda v, s: sum((v[i] for i in range(N) if s >> i & 1), F(0))

# variables: e0 (4) | p at first-stage nodes k0=0,1 | p at second-stage nodes 2+2*k0+k1
nv = 4 + 4 * 6
pidx = lambda k: 4 + 4 * k
Aeq, beq, Aub, bub = [], [], [], []
for k0, y0 in enumerate(Y0):
    r = [0] * nv
    for i in range(N): r[pidx(k0) + i] = 1
    Aeq.append(r); beq.append(y0)
    for k1, y1 in enumerate(Y1):
        k = 2 + 2 * k0 + k1; r = [0] * nv
        for i in range(N): r[pidx(k) + i] = 1
        Aeq.append(r); beq.append(y1)
        for path in ([pidx(k0)], [pidx(k0), pidx(k)]):
            for i in range(N):
                r = [0] * nv; r[i] = 1
                for base in path: r[base + i] = -1
                Aub.append(r); bub.append(E[i])                    # energy <= E
                Aub.append([-v for v in r]); bub.append(F(0))     # energy >= 0
bnd = [(F(0), E[i]) for i in range(N)] + [(-C[i], D[i]) for _ in range(6) for i in range(N)]


def exact_ok(x):
    dot = lambda r: sum(c * v for c, v in zip(r, x))
    return (all(dot(r) == v for r, v in zip(Aeq, beq)) and all(dot(r) <= v for r, v in zip(Aub, bub))
            and all(lo <= v <= hi for v, (lo, hi) in zip(x, bnd)))


def certified_point(c):
    cc = np.zeros(nv); cc[:4] = -np.array(c, float)
    r = linprog(cc, A_ub=np.array(Aub, float), b_ub=np.array(bub, float), A_eq=np.array(Aeq, float),
                b_eq=np.array(beq, float), bounds=[(float(lo), float(hi)) for lo, hi in bnd], method='highs')
    assert r.status == 0
    for den in (10, 20, 40, 60, 100, 120, 200, 400, 600, 1000, 10000, 100000):
        x = [F(v).limit_denominator(den) for v in r.x]
        if exact_ok(x):
            return x[:4], -r.fun
    raise RuntimeError('rationalization failed')


bh, ah = {}, {}
for s in MS:
    z, fv = certified_point(ind(s)); bh[s] = ss(z, s); assert abs(float(bh[s]) - fv) < 1e-7
    z, fv = certified_point([-v for v in ind(s)]); ah[s] = ss(z, s); assert abs(float(ah[s]) + fv) < 1e-7
print(f"instance = {'Example C (three types)' if three else 'Example B'}, eps = {eps}")
opt_ref = ('review_codex_h_independent.py (Example C: exact optima of the 30 subset supports; not a facet certificate)'
           if three else 'review_codex_n4_geometry.py (Example B, with facet-dimension certificate)')
print('(a) 30 rational feasible-policy witnesses verified exactly (they bound the true subset supports;\n'
      '    agreement with the float LP optimum within 1e-7 is a float check only; exact optimality of these\n'
      f'    values is certified separately in {opt_ref})')

w = [0, -1, 0, 1] if three else [1, -1, 0, 1]
cons = [(ind(s), bh[s]) for s in MS] + [([-v for v in ind(s)], -ah[s]) for s in MS]
r = linprog(-np.array(w, float), A_ub=[c for c, _ in cons], b_ub=[float(v) for _, v in cons],
            bounds=[(None, None)] * N, method='highs')
act = [k for k, (c, v) in enumerate(cons) if abs(np.dot(c, r.x) - float(v)) < 1e-9]


def solve(Ar, br):
    M = [[F(v) for v in row] + [rhs] for row, rhs in zip(Ar, br)]
    for col in range(N):
        piv = next(i for i in range(col, N) if M[i][col] != 0); M[col], M[piv] = M[piv], M[col]
        for i in range(N):
            if i != col and M[i][col] != 0:
                f = M[i][col] / M[col][col]; M[i] = [x - f * y for x, y in zip(M[i], M[col])]
    return [M[i][N] / M[i][i] for i in range(N)]


inQ = lambda x: all(sum(F(c) * v for c, v in zip(row, x)) <= rhs for row, rhs in cons)
estar = None
for combo in itertools.combinations(act, N):
    Ar = [cons[k][0] for k in combo]
    if abs(np.linalg.det(np.array(Ar, float))) < 1e-9: continue
    x = solve(Ar, [cons[k][1] for k in combo])
    if inQ(x): estar = x; break
print('(b) e* =', tuple(str(v) for v in estar), ' in Q (hence in the subset outer approximation):', inQ(estar))

# (c) valid bounds for K_1 = [0,E] ∩ (box + P_{-1}) ∩ (box + P_{6/5}), then for K_1 + P_{y0}
bP = lambda y, s: min(ss(D, s), y + ss(C, 15 ^ s)); aP = lambda y, s: max(-ss(C, s), y - ss(D, 15 ^ s))
b1 = {0: F(0)}; a1 = {0: F(0)}
for s in MS:
    b1[s] = min([ss(E, s)] + [ss(E, s) + bP(y, s) for y in Y1])
    a1[s] = max([F(0)] + [aP(y, s) for y in Y1])
viol = []
for y0 in Y0:
    for lab in itertools.product(range(4), repeat=N):
        A = sum(1 << i for i in range(N) if lab[i] == 1); B = sum(1 << i for i in range(N) if lab[i] == 2)
        M = sum(1 << i for i in range(N) if lab[i] == 3)
        lhs = ss(estar, A) - ss(estar, B); rhs = b1[A | M] - a1[B | M] + ss(D, A) + ss(C, B)
        if lhs > rhs: viol.append((str(y0), ind(A), ind(B), ind(M), str(lhs), str(rhs)))
print('(c) violated valid inequalities e(A)-e(B) <= b1(A∪M)-a1(B∪M)+D(A)+C(B)  [y0, A, B, M, lhs, rhs]:')
for v in viol[:4]: print('   ', v)
print('=> e* lies in the subset outer approximation of K_0 but not in K_0:', bool(viol))
