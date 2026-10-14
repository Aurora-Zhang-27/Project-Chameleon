"""v2 oracle: lossless N-battery causal feasibility on the endpoint request tree, asymmetric C/D,
certified facet enumeration, subset-sum recursion, and set-equality check.
All floating-point (HiGHS); tolerances are explicit."""
import itertools, numpy as np
from scipy.optimize import linprog
from scipy.spatial import ConvexHull, HalfspaceIntersection
TOL_SUP = 1e-7      # support-function tolerance
TOL_NORM = 1e-6     # tolerance when certifying a subset-vector facet
def subsets(N): return [s for r in range(1, N+1) for s in itertools.combinations(range(N), r)]

def build(C, D, E, ms):
    """LP data with e0 as the last N variables. ms: list of (l,u); endpoint tree."""
    N = len(E); T = len(ms); nodes = []
    def rec(t, h):
        if t == T: return
        for y in sorted(set(ms[t])):
            nodes.append((t, h + (y,))); rec(t + 1, h + (y,))
    rec(0, ())
    idx = {n: k for k, n in enumerate(nodes)}; nv = len(nodes) * N + N
    Aeq, beq, Aub, bub = [], [], [], []
    for (t, h), k in idx.items():
        r = np.zeros(nv); r[k*N:(k+1)*N] = 1; Aeq.append(r); beq.append(h[-1])
        path = [idx[(s, h[:s+1])] for s in range(t + 1)]
        for i in range(N):
            r = np.zeros(nv)
            for kk in path: r[kk*N + i] = 1
            r2 = r.copy(); r2[-N+i] = -1; Aub.append(r2); bub.append(0)      # energy >= 0
            r3 = -r.copy(); r3[-N+i] = 1; Aub.append(r3); bub.append(E[i])   # energy <= E
    bnd = [(-C[i], D[i]) for _ in nodes for i in range(N)] + [(0, E[i]) for i in range(N)]
    return dict(Aub=np.array(Aub), bub=np.array(bub), Aeq=np.array(Aeq), beq=np.array(beq), bnd=bnd, nv=nv, N=N)

class SolverFailure(Exception):
    """LP ended in a status other than optimal (0) or infeasible (2)."""

def support(M, c, presolve=True):
    """Returns (argmax, value); None only if HiGHS certifies infeasibility (status 2).
    Any other non-optimal status raises SolverFailure so it is never counted as infeasible.
    presolve=False is the cross-check for a reported infeasibility (see member())."""
    N, nv = M['N'], M['nv']; cc = np.zeros(nv); cc[-N:] = -np.asarray(c, float)
    r = linprog(cc, A_ub=M['Aub'], b_ub=M['bub'], A_eq=M['Aeq'], b_eq=M['beq'], bounds=M['bnd'], method='highs',
                options={'presolve': presolve})
    if r.status == 2: return None
    if r.status != 0: raise SolverFailure(f'status {r.status}: {r.message}')
    return (r.x[-N:], -r.fun)

def member_status(M, e, presolve=True):
    """Like member(), but separates outcomes: True (status 0), False (status 2, infeasible);
    any other status raises SolverFailure instead of being read as infeasible."""
    N = M['N']; b = list(M['bnd'])
    for i in range(N): b[-N+i] = (e[i], e[i])
    r = linprog(np.zeros(M['nv']), A_ub=M['Aub'], b_ub=M['bub'], A_eq=M['Aeq'], b_eq=M['beq'], bounds=b,
                method='highs', options={'presolve': presolve})
    if r.status == 0: return True
    if r.status == 2: return False
    raise SolverFailure(f'status {r.status}: {r.message}')

def member(M, e, presolve=True):
    """True iff HiGHS reports the tree LP with root fixed at e as feasible.
    presolve=False is the cross-check for a reported infeasibility: on one case (E=(4,3,4), C=(2,1.5,0),
    D=(2,0,2), menus [(-.5,2),(1,2),(1,1.5)], root (4,2.5,1.5)) default HiGHS returned a false
    'infeasible' although an exact rational policy exists (REVIEW_N3_N4_20260928_CODEX.md §7.6)."""
    N = M['N']; b = list(M['bnd'])
    for i in range(N): b[-N+i] = (e[i], e[i])
    return linprog(np.zeros(M['nv']), A_ub=M['Aub'], b_ub=M['bub'], A_eq=M['Aeq'], b_eq=M['beq'], bounds=b,
                   method='highs', options={'presolve': presolve}).status == 0

def affine_dim_certified(M, P):
    """Grow the point set until it spans the affine hull of K0, certified by support widths:
    for every direction v orthogonal to the current span, max v.e - min v.e <= TOL_SUP over K0.
    Returns (points, dim)."""
    N = M['N']
    while True:
        Q = P - P[0]
        if len(P) > 1:
            _, sv, Vt = np.linalg.svd(Q); r = int(np.sum(sv > 1e-9))
        else:
            r = 0; Vt = np.eye(N)
        if r == N: return P, N
        grew = False
        for v in Vt[r:]:
            hi = support(M, v); lo = support(M, -v)
            if hi[1] + lo[1] > TOL_SUP:           # width in direction v
                P = np.vstack([P, hi[0], lo[0]]); grew = True
        if not grew: return P, r

def certified_hull(M, rng, max_iter=200):
    """Returns (status, hull). status in {'infeasible','lowdim','notconverged','certified'}.
    'infeasible' only on a certified infeasible LP; 'lowdim' only when support widths certify
    that K0 lies in a proper affine subspace; 'certified' means every hull facet was checked
    against the support function (within TOL_SUP), so the hull equals K0 up to that tolerance.
    Solver failures propagate as SolverFailure."""
    N = M['N']
    first = support(M, np.ones(N))
    if first is None: return 'infeasible', None
    pts = [support(M, c)[0] for c in rng.normal(size=(8*N*N, N))]
    P = np.unique(np.round(np.array(pts), 9), axis=0)
    P, d = affine_dim_certified(M, P)
    if d < N: return 'lowdim', None
    for _ in range(max_iter):
        H = ConvexHull(P); added = False
        for eq in H.equations:
            x, h = support(M, eq[:N])
            if h > -eq[N] + TOL_SUP:
                P = np.vstack([P, x]); added = True
        if not added: return 'certified', ConvexHull(P)
    return 'notconverged', None

def facet_normals(H):
    """Group hull simplices into facets; return list of (unit-max normal, vertex array)."""
    N = H.points.shape[1]; groups = {}
    for eq, simp in zip(H.equations, H.simplices):
        n = eq[:N] / np.max(np.abs(eq[:N])); key = tuple(np.round(n, 6))
        groups.setdefault(key, set()).update(simp.tolist())
    return [(np.array(k), H.points[sorted(v)]) for k, v in groups.items()]

def is_subset_facet(M, n, V):
    """Certify: n equals a same-sign 0/1 vector s (componentwise within TOL_NORM after scaling), and the
    facet's vertices lie on s.e = support(s) within TOL_SUP, spanning dimension N-1."""
    s = np.where(np.abs(n) > 0.5, np.sign(n), 0.0)
    if not (np.all(s >= 0) or np.all(s <= 0)) or np.max(np.abs(n - s)) > TOL_NORM: return False
    h = support(M, s)[1]
    on = np.abs(V @ s - h) <= 1e-6
    W = V[on]
    return len(W) >= M['N'] and np.linalg.matrix_rank(W - W[0], tol=1e-8) == M['N'] - 1

def subset_recursion(C, D, E, ms):
    """Backward recursion keeping tight subset-sum bounds (outer approximation of K0; exact iff H3' holds
    at every step). Returns dict S->(lo,hi) or None if empty."""
    N = len(E); SS = subsets(N)
    K = {S: (0.0, float(sum(E[list(S)]))) for S in SS}
    for (l, u) in reversed(ms):
        nv = 3*N; A = []; b = []
        for S, (lo, hi) in K.items():
            for off in (N, 2*N):
                r = np.zeros(nv); r[list(S)] = 1; r[[off+i for i in S]] = -1
                A.append(r.copy()); b.append(hi); A.append(-r); b.append(-lo)
        Aeq = []; beq = []
        for off, y in ((N, l), (2*N, u)):
            r = np.zeros(nv); r[off:off+N] = 1; Aeq.append(r); beq.append(y)
        bnd = [(0, E[i]) for i in range(N)] + [(-C[i], D[i]) for i in range(N)]*2
        newK = {}
        for S in SS:
            c = np.zeros(nv); c[list(S)] = 1
            r1 = linprog(-c, A_ub=np.array(A), b_ub=b, A_eq=np.array(Aeq), b_eq=beq, bounds=bnd, method='highs')
            if r1.status != 0: return None
            r2 = linprog(c, A_ub=np.array(A), b_ub=b, A_eq=np.array(Aeq), b_eq=beq, bounds=bnd, method='highs')
            newK[S] = (r2.fun, -r1.fun)
        K = newK
    return K

def outer_vertices(K, N):
    """Vertices of {e: lo_S <= e(S) <= hi_S} (full-dimensional case) via halfspace intersection."""
    hs = []
    for S, (lo, hi) in K.items():
        a = np.zeros(N); a[list(S)] = 1
        hs.append(np.r_[a, -hi]); hs.append(np.r_[-a, lo])
    hs = np.array(hs)
    # interior point by Chebyshev LP
    A = hs[:, :N]; b = -hs[:, N]; nrm = np.linalg.norm(A, axis=1)
    r = linprog(np.r_[np.zeros(N), -1], A_ub=np.c_[A, nrm], b_ub=b, bounds=[(None, None)]*N + [(0, None)], method='highs')
    if r.status != 0 or r.x[-1] < 1e-7: return None
    return np.unique(np.round(HalfspaceIntersection(hs, r.x[:N]).intersections, 9), axis=0)
