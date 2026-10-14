"""Exact certificate that history-dependent affine policies are not always exact (2026-10-11).

Instance: the coefficient-2 instance of n4_normal_certificate.py (case 1), N = 4, T = 4.
A = {e : some policy of the class honours every request from e} (class 'segregated' of
affine_decision.py, which contains plain affine policies).  A is the projection of the LP
  {(e, policy) : robust power and energy constraints, balance},
so h_A(n) = max n.e over that LP.  We compute, each with a rational primal-dual optimality certificate
(review_codex_h_independent.Model / Tree):
  h_K0(n)  over the endpoint-tree LP, with an exact maximiser x* in K_0,
  h_A(n)   over the affine-policy LP,
for a direction n chosen in float from the facet normals of K_0.  If h_A(n) < h_K0(n), then x* is in
K_0 but not in A: from x* every request sequence can be honoured, but by no policy of the class.
Usage: python3 affine_gap_certificate.py [eps]   (eps replaces zero powers, e.g. 1/100)"""
import sys
from fractions import Fraction as F
import numpy as np
from oracle2 import build, certified_hull, support
from affine_decision import AffinePolicyLP
import review_codex_h_independent as rc
from review_codex_h_independent import Model, Tree

_sparse = rc.sparse                    # Codex's Model builds its float matrices with integer data in mind;
rc.sparse = lambda rows, n: _sparse([[(j, float(c)) for j, c in row] for row in rows], n)   # exact data stay in Fractions

eps = F(sys.argv[1]) if len(sys.argv) > 1 else F(0)
E = ['4', '5', '1', '1']; C = ['0', '0', '3', '1/2']; D = ['1', '3/2', '2', '0']
MS = [('3/10', '7/10'), ('-9/10', '17/10'), ('4/5', '9/10'), ('-4/5', '11/5')]
Eq = [F(v) for v in E]; Cq = [F(v) or eps for v in C]; Dq = [F(v) or eps for v in D]; Mq = [tuple(map(F, m)) for m in MS]
N = 4
fl = lambda v: [float(x) for x in v]
lp = AffinePolicyLP(fl(Eq), fl(Cq), fl(Dq), [tuple(fl(m)) for m in Mq], 'segregated')


def affine_set_model():
    """The affine-policy LP with e as extra variables (columns lp.nv .. lp.nv+N-1), rational data."""
    q = lambda x: F(repr(float(x)))
    A = lp.Aub.tocoo(); rows = {}
    for r, c, v in zip(A.row, A.col, A.data):
        rows.setdefault(int(r), []).append((int(c), q(v)))
    ub, bu = [], []
    for k in range(lp.nrow):
        row = list(rows.get(k, []))
        tag = lp.rhs_e[k]
        if tag is None:
            b = q(lp.rhs_const[k])
        else:
            i, sg = tag
            if sg > 0: row.append((lp.nv + i, F(-1))); b = F(0)          # P <= e_i
            else: row.append((lp.nv + i, F(1))); b = Eq[i]                # -P <= E_i - e_i
        ub.append(row); bu.append(b)
        if tag is None and lp.rowinfo[k] is not None:                     # power rows: exact C, D
            dev, kind = lp.rowdev[k]; const, per_s, sign = lp.rowinfo[k]
            bu[-1] = Dq[dev] if sign > 0 else Cq[dev]
    Ae = lp.Aeq.tocoo(); eqrows = {}
    for r, c, v in zip(Ae.row, Ae.col, Ae.data):
        eqrows.setdefault(int(r), []).append((int(c), q(v)))
    eq = [eqrows.get(k, []) for k in range(lp.Aeq.shape[0])]; be = [q(v) for v in lp.beq]
    bounds = [(None if lo is None else F(lo), None if hi is None else F(hi)) for lo, hi in lp.bounds]
    bounds += [(F(0), Eq[i]) for i in range(N)]
    return Model(lp.nv + N, eq, be, ub, bu, bounds)


# float: choose the facet normal of K_0 with the largest gap h_K0 - h_A
M = build(np.array(fl(Cq)), np.array(fl(Dq)), np.array(fl(Eq)), [tuple(fl(m)) for m in Mq])
st, H = certified_hull(M, np.random.default_rng(0))
model = affine_set_model()
best = None
for eqn in np.unique(np.round(H.equations[:, :N], 9), axis=0):
    s = eqn / np.min(np.abs(eqn[np.abs(eqn) > 1e-9]))
    if np.max(np.abs(s - np.round(s))) > 1e-6:
        continue
    n = [int(round(v)) for v in s]
    hk = support(M, np.array(n, float))[1]
    c = np.zeros(model.n); c[lp.nv:] = -np.array(n, float)
    from scipy.optimize import linprog
    r = linprog(c, A_ub=model.Au, b_ub=np.array([float(b) for b in model.bu]), A_eq=model.Ae,
                b_eq=np.array([float(b) for b in model.be]),
                bounds=[(None if lo is None else float(lo), None if hi is None else float(hi)) for lo, hi in model.bounds],
                method='highs')
    gap = hk - (-r.fun)
    if best is None or gap > best[0]:
        best = (gap, n)
print('float: largest gap', round(best[0], 6), 'in direction', best[1])

n = best[1]
tree = Tree(Eq, Cq, Dq, Mq)
hk = tree.support(n)
ha = model.solve([F(0)] * lp.nv + [F(-v) for v in n])
xstar = hk['x'][:N]
print(f'eps = {eps}: h_K0(n) = {hk["value"]} (exact maximiser x* = {tuple(str(v) for v in xstar)}),'
      f' h_A(n) = {ha["value"]}  (both with rational primal-dual certificates)')
print('=> x* is in K_0 but admits no policy of the class:', ha['value'] < hk['value'])
