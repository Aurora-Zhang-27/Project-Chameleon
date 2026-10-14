"""Exact certificate for the N=3 tightening lemma (Lemma 3 of N3_THEOREM_N4_COUNTEREXAMPLE.md).

Setting: V={1,2,3}; b submodular, a supermodular on 2^V, a(∅)=b(∅)=0, a<=b pointwise.  These
linear inequalities define the cone CONE in the 14 coordinates (a(T), b(T)), T nonempty.
K = {x : a(S) <= x(S) <= b(S) for all S},  beta(S) = max_K x(S).
LP duality: beta(S) = min over vertices v of D_S = {theta >= 0 : sum_k theta_k col_k = 1_S} of L_v(a,b),
columns +1_T (cost b(T)) and -1_T (cost -a(T)).  All vertices are enumerated exactly (Fraction).

Checks (every "certified" below is an exact rational Farkas identity, found by LP and then verified
with Fraction arithmetic; nothing is accepted on floating-point evidence):
 (1) every fractional dual vertex is dominated on CONE by a convex combination of integral ones
     (so tight bounds are integer combinations of a, b: no division, no denominator growth);
 (2) closed forms, labels i=1, j=2, k=3 (other labels by the symmetry of CONE):
        beta(1)   = min{b1, b12-a2, b13-a3, b123-a23}
        beta(12)  = min{b12, b123-a3, b123+b1-a13, b123+b2-a23}
        beta(123) = b123
     each listed term is dual feasible (a valid upper bound) and every dual vertex is dominated;
 (3) submodularity type T2: for every vertex pair (v1 in D_12, v2 in D_13) there are convex weights
     sigma on D_1 and nu >= 0 with  L_v1 + L_v2 - b123 - sum sigma L = sum nu g  (g: CONE's inequalities),
     hence beta(12) + beta(13) >= b123 + beta(1) >= beta(123) + beta(1).
With argument 4 (~9 minutes) check (3) is run unchanged, i.e. with b({1,2,3}) on the right-hand side.
For N=4, b(123) is not beta(123) and the inequality is stronger than submodularity, so the number of
uncertified pairs only shows that the check is not vacuous; it is NOT a count of submodularity
counterexamples (an uncertified pair is not a counterexample certificate either).
Usage: python3 n3_lemma_certificate.py [N]
"""
import itertools, sys
import numpy as np
from fractions import Fraction as F
from scipy.optimize import linprog

N = int(sys.argv[1]) if len(sys.argv) > 1 else 3
FULL = (1 << N) - 1
MS = list(range(1, FULL + 1))
DIM = 2 * len(MS)


def ia(T): return T - 1                 # coordinate of a(T)
def ib(T): return len(MS) + T - 1       # coordinate of b(T)
def vec(T): return [1 if T >> i & 1 else 0 for i in range(N)]
def zero(): return [F(0)] * DIM


# ---- linear forms that are >= 0 on CONE
GEN = []
for T, U in itertools.combinations(range(FULL + 1), 2):
    if T & U in (T, U):
        continue                                     # comparable pairs give trivial inequalities
    g = zero()
    for X, s in ((T, 1), (U, 1), (T | U, -1), (T & U, -1)):
        if X: g[ib(X)] += s
    GEN.append(g)                                    # b(T)+b(U)-b(T∪U)-b(T∩U) >= 0
    g = zero()
    for X, s in ((T | U, 1), (T & U, 1), (T, -1), (U, -1)):
        if X: g[ia(X)] += s
    GEN.append(g)                                    # a(T∪U)+a(T∩U)-a(T)-a(U) >= 0
for T in MS:
    g = zero(); g[ib(T)] += 1; g[ia(T)] -= 1
    GEN.append(g)                                    # b(T)-a(T) >= 0

COLS = [(T, +1) for T in MS] + [(T, -1) for T in MS]


def solve(A, rhs):
    n = len(A)
    M = [[F(A[r][c]) for c in range(n)] + [F(rhs[r])] for r in range(n)]
    for c in range(n):
        p = next((r for r in range(c, n) if M[r][c] != 0), None)
        if p is None:
            return None
        M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c and M[r][c] != 0:
                f = M[r][c] / M[c][c]
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [M[r][n] / M[r][r] for r in range(n)]


def dual_vertices(S):
    """All basic feasible solutions of D_S, as linear forms in (a,b)."""
    out = set()
    for cols in itertools.combinations(range(len(COLS)), N):
        A = [[COLS[k][1] * vec(COLS[k][0])[i] for k in cols] for i in range(N)]
        th = solve(A, vec(S))
        if th is None or min(th) < 0:
            continue
        L = zero()
        for k, t in zip(cols, th):
            T, s = COLS[k]
            if s > 0: L[ib(T)] += t
            else: L[ia(T)] -= t
        out.add(tuple(L))
    return [list(L) for L in out]


def dominated(target, cands):
    """Exact certificate that target >= some convex combination of cands on CONE, or None."""
    nc, ng = len(cands), len(GEN)
    Aeq = np.zeros((DIM + 1, nc + ng)); beq = np.zeros(DIM + 1)
    for j, c in enumerate(cands): Aeq[:DIM, j] = [float(x) for x in c]
    for j, g in enumerate(GEN): Aeq[:DIM, nc + j] = [float(x) for x in g]
    beq[:DIM] = [float(x) for x in target]; Aeq[DIM, :nc] = 1; beq[DIM] = 1
    r = linprog(np.zeros(nc + ng), A_eq=Aeq, b_eq=beq, bounds=[(0, None)] * (nc + ng), method='highs')
    if r.status == 2:
        return None
    if r.status != 0:
        raise RuntimeError(r.message)
    for den in (1, 2, 4, 6, 12, 24, 60, 120, 720):
        w = [F(x).limit_denominator(den) for x in r.x]
        if min(w) < 0 or sum(w[:nc]) != 1:
            continue
        lhs = [sum(w[j] * cands[j][d] for j in range(nc)) + sum(w[nc + j] * GEN[j][d] for j in range(ng))
               for d in range(DIM)]
        if lhs == list(target):
            return w
    raise RuntimeError('LP feasible but exact rationalization failed')


def integral(L): return all(x.denominator == 1 for x in L)


def dual_feasible(L, S):
    """L encodes lambda_T = coefficient of b(T) >= 0 and mu_T = -coefficient of a(T) >= 0."""
    ok = all(L[ib(T)] >= 0 and L[ia(T)] <= 0 for T in MS)
    rep = [sum((L[ib(T)] + L[ia(T)]) * vec(T)[i] for T in MS) for i in range(N)]
    return ok and rep == vec(S)


def lf(*terms):
    L = zero()
    for kind, T, c in terms: L[ib(T) if kind == 'b' else ia(T)] += c
    return L


CLOSED = {  # N=3 closed forms, labels i=1 (mask 1), j=2 (mask 2), k=3 (mask 4)
    1: [lf(('b', 1, 1)), lf(('b', 3, 1), ('a', 2, -1)), lf(('b', 5, 1), ('a', 4, -1)),
        lf(('b', 7, 1), ('a', 6, -1))],
    3: [lf(('b', 3, 1)), lf(('b', 7, 1), ('a', 4, -1)), lf(('b', 7, 1), ('b', 1, 1), ('a', 5, -1)),
        lf(('b', 7, 1), ('b', 2, 1), ('a', 6, -1))],
    7: [lf(('b', 7, 1))],
}

if __name__ == '__main__':
    D = {S: dual_vertices(S) for S in MS}
    print(f'N={N}: {len(GEN)} cone inequalities; dual vertices per S:', {S: len(D[S]) for S in MS},
          '; fractional:', {S: sum(not integral(L) for L in D[S]) for S in MS})
    bad = sum(dominated(L, [M for M in D[S] if integral(M)]) is None
              for S in MS for L in D[S] if not integral(L))
    print('(1) fractional dual vertices not dominated by integral ones:', bad)
    if N == 3:
        for S, terms in CLOSED.items():
            feas = all(dual_feasible(t, S) for t in terms)
            und = sum(dominated(L, terms) is None for L in D[S])
            print(f'(2) closed form S={S}: terms dual feasible {feas}; dual vertices not dominated {und}')
    bV = lf(('b', 7, 1))
    ok = fail = 0
    for L1 in D[3]:
        for L2 in D[5]:
            target = [x + y - z for x, y, z in zip(L1, L2, bV)]
            if dominated(target, D[1]) is None: fail += 1
            else: ok += 1
    note = '' if N == 3 else '  [N>3: RHS uses b(123), stronger than submodularity; not a counterexample count]'
    print(f'(3) T2 beta(12)+beta(13) >= b123+beta(1): vertex pairs certified {ok}, not certified {fail}{note}')
