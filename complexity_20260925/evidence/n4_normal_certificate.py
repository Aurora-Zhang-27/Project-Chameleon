"""Exact certificate (2026-10-10): for N = 4 the real K_0 can have a facet normal outside {0,+-1}^N.

Instance (found by template_pilot near Example B, then confirmed here): see CASES.
  (a) exact support of K_0 in all 80 directions d in {0,+-1}^4 \\ {0}, each with a rational primal-dual
      optimality certificate of the endpoint-tree LP (review_codex_h_independent.Tree);
      T = {e : d.e <= h_K0(d) for all 80 d} is the {0,+-1} template hull of K_0;
  (b) exact maximum of n.e over T for a direction n with an entry 2 (rational primal-dual certificate of
      that small LP) and the maximizing point v;
  (c) exact support h_K0(n).
If (b) > (c), then v is in the template hull but not in K_0: K_0 is not the intersection of its
{0,+-1} supporting halfspaces, so it has a facet whose normal is not in {0,+-1}^4.  Consequently the
{0,+-1} template recursion (all 3^N - 1 directions) is not exact for N = 4 in general.
Usage: python3 n4_normal_certificate.py [eps]   (eps replaces the zero powers, e.g. 1/100)"""
import itertools, sys
from fractions import Fraction as F
from review_codex_h_independent import Model, Tree, dot, eliminate

CASES = {
    'case 1': ([4, 5, 1, 1], [0, 0, 3, '1/2'], [1, '3/2', 2, 0],
               [('3/10', '7/10'), ('-9/10', '17/10'), ('4/5', '9/10'), ('-4/5', '11/5')], [-1, 0, 0, 2]),
    'case 2': ([3, 4, 1, 1], [0, 0, 3, '1/2'], ['9/10', 1, 3, 0],
               [('2/5', '3/5'), ('2/5', 2), ('1/5', '1/2'), ('-9/10', '3/2')], [-1, 0, 0, 2]),
}


def certify(E, C, D, menus, n, eps=F(0)):
    E = list(map(F, E)); C = [F(c) or eps for c in C]; D = [F(d) or eps for d in D]
    menus = [tuple(map(F, m)) for m in menus]; N = len(E); tree = Tree(E, C, D, menus)
    rows, rhs = [], []
    for d in itertools.product((-1, 0, 1), repeat=N):
        if not any(d):
            continue
        h = tree.support(list(d))
        if h is None:
            return None
        rows.append([(i, d[i]) for i in range(N) if d[i]]); rhs.append(h['value'])
    best = Model(N, [], [], rows, rhs, [(None, None)] * N).solve([-F(v) for v in n])
    v, hull_max = best['x'], best['value']
    true_max = tree.support(n)['value']
    in_hull = all(sum(c * v[i] for i, c in row) <= b for row, b in zip(rows, rhs))
    # Certify that this particular supporting direction is a facet, not just a separator.
    face=Model(tree.n,tree.eq+[[(i,value) for i,value in enumerate(n) if value]],
               tree.be+[true_max],tree.ub,tree.bu,tree.bounds)
    full_points,face_points=[],[]
    rank=lambda pts: eliminate([[x-y for x,y in zip(p,pts[0])] for p in pts[1:]]) if pts else -1
    for direction in itertools.product((-1,0,1),repeat=N):
        if not any(direction):continue
        if rank(full_points)<N:full_points.append(tree.support(direction)['x'][:N])
        if rank(face_points)<N-1:
            r=face.solve([F(-value) for value in direction]+[F(0)]*(tree.n-N))
            assert r is not None
            face_points.append(r['x'][:N])
        if rank(full_points)==N and rank(face_points)==N-1:break
    assert rank(full_points)==N and rank(face_points)==N-1
    return dict(C=C,D=D,v=v,in_hull=in_hull,hull_max=hull_max,true_max=true_max,
                kernel_dimension=rank(full_points),face_dimension=rank(face_points))


if __name__ == '__main__':
    eps = F(sys.argv[1]) if len(sys.argv) > 1 else F(0)
    for name, (E, C, D, menus, n) in CASES.items():
        r = certify(E, C, D, menus, n, eps)
        print(f"{name} (zero powers -> {eps}): C={[str(x) for x in r['C']]} D={[str(x) for x in r['D']]}")
        print(f"   n = {n}: max over the {{0,+-1}} template hull = {r['hull_max']}, max over K_0 = {r['true_max']}"
              f"  -> {'normal outside {0,+-1}^4 certified' if r['hull_max'] > r['true_max'] else 'no gap'}")
        print(f"   v = {tuple(str(x) for x in r['v'])} lies in the template hull (exact): {r['in_hull']}")

        print('   exact dimensions:',r['kernel_dimension'],'kernel,',r['face_dimension'],'supporting face; facet certified')
