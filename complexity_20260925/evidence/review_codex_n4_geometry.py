"""Independent exact certificates for Example B, including the claimed facet.

Uses only our independent StateTree builder; no imports from repository oracles.
Float LP finds candidates. Fraction primal/dual identities and affine ranks
are the acceptance criteria. Run: python3 review_codex_n4_geometry.py
"""
import itertools
from fractions import Fraction as F
from scipy.sparse import csr_matrix, vstack
from review_codex_independent import StateTree, val


def rank(rows):
    m = [list(map(F, r)) for r in rows]
    if not m:
        return 0
    r = 0
    for j in range(len(m[0])):
        p = next((i for i in range(r, len(m)) if m[i][j]), None)
        if p is None:
            continue
        m[p], m[r] = m[r], m[p]
        q = m[r][j]
        m[r] = [x/q for x in m[r]]
        for i in range(len(m)):
            if i != r:
                q = m[i][j]
                m[i] = [x-q*y for x, y in zip(m[i], m[r])]
        r += 1
    return r


def basis(points):
    origin = points[0]
    rows, out = [], [origin]
    for p in points[1:]:
        row = [x-y for x, y in zip(p, origin)]
        if rank(rows+[row]) > len(rows):
            rows.append(row)
            out.append(p)
    return out


for eps in (F(0), F(1, 100)):
    E, C, D = [4, 5, 1, 1], [eps, eps, 3, F(1, 2)], [1, F(1, 2), 2, eps]
    menus = [(F(1, 5), F(1)), (F(-1), F(6, 5))]
    tree = StateTree(E, C, D, menus)
    points, upper, lower = [], {}, {}
    count = 0
    for s in range(1, 16):
        for sign in (1, -1):
            w = tuple(sign*((s >> i) & 1) for i in range(4))
            r = tree.run(w)
            assert r is not None and r['primal'] and r['dual']
            point = r['witness']
            points.append(point)
            (upper if sign == 1 else lower)[s] = val(point, s)
            count += 1
    estar = [F(4), F(0), F(1, 5)-2*eps, F(1)]
    assert all(lower[s] <= val(estar, s) <= upper[s] for s in range(1, 16))
    rhs = F(4, 5)+5*eps
    w = (0, -1, 0, 1)
    r = tree.run(w)
    assert r['primal'] and r['dual']
    assert sum(q*x for q, x in zip(w, r['witness'])) == rhs
    assert estar[3]-estar[1] > rhs
    full_basis = basis(points)
    assert len(full_basis) == 5
    # Restrict the root to the exposed face; policies still share every prefix.
    row = [(1, -1), (3, 1)]
    tree.eq.append(row)
    tree.be.append(rhs)
    dense = [0]*tree.nv
    dense[1], dense[3] = -1, 1
    tree.Ae = vstack((tree.Ae, csr_matrix([dense])), format='csr')
    face_points = []
    for direction in itertools.product((-1, 0, 1), repeat=4):
        if not any(direction):
            continue
        r = tree.run(direction)
        assert r is not None and r['primal'] and r['dual']
        face_points.append(r['witness'])
    face_basis = basis(face_points)
    assert len(face_basis) == 4
    print('N4 EXACT', {'eps': str(eps), 'subset_optima_certified': count,
                      'estar_in_tight_subset_hull': True, 'mixed_support': str(rhs),
                      'kernel_dimension': len(full_basis)-1,
                      'face_dimension': len(face_basis)-1,
                      'face_witnesses': [tuple(map(str, p)) for p in face_basis]}, flush=True)
