"""Exact check of the 2-type candidates from two_types_search.py (2026-10-10).

For each instance (two device types; devices of a type are identical, initial energies may differ):
  (a) the exact tight subset bounds of K_0: every subset support of the endpoint-tree LP, with a
      rational primal-dual optimality certificate (review_codex_h_independent.Tree);
  (b) the exact maximum of the signed direction w over the subset outer approximation Q of K_0, with
      a rational primal-dual certificate of that small LP, and the maximizing vertex e*;
  (c) the exact support of K_0 in direction w (same certificate as (a)).
If (b) > (c), then e* lies in the subset outer approximation but not in K_0, so K_0 has a facet that is
not a subset facet (layer 3 of the counterexample rule).  Endpoint-tree sufficiency: endpoint lemma.
With EPS (e.g. 1/100) every zero power is replaced by EPS, so all powers are strictly positive.
Usage: python3 two_types_certificate.py [EPS]"""
import sys
from fractions import Fraction as F
from review_codex_h_independent import Model, Tree, dot

CASES = {  # E, C, D, menus, signed direction w; all from two_types_search.py runs on 2026-10-10
    'XXYY-a': ([5, 5, 2, 2], [0, 0, 3, 3], ['3', '3', '1/2', '1/2'],
               [('9/5', '13/5'), ('7/10', '57/10'), ('-39/10', '-13/5')], [-1, 0, 0, 1]),
    'XXYY-b': ([4, 4, 3, 3], [0, 0, 2, 2], ['1/2'] * 4,
               [('3/5', '9/10'), ('-2/5', '9/5'), ('-27/10', '-1/10')], [0, -1, 0, 1]),
    'XXYY-c': ([2, 2, 4, 4], ['1/2'] * 4, [1, 1, 0, 0],
               [('-13/10', '-1'), ('-6/5', '1/2'), ('2/5', '19/10')], [0, -1, 0, 1]),
    'XXYYY': ([3, 3, 1, 1, 1], ['1/10', '1/10', '1/2', '1/2', '1/2'], [3, 3, 0, 0, 0],
              [('-9/10', '-1/10'), ('-13/10', '3/5'), ('7/5', '21/5')], [0, -1, 0, 0, 1]),
    'XXXYY': ([5, 5, 5, 4, 4], [0, 0, 0, 3, 3], ['1/2', '1/2', '1/2', 1, 1],
              [('11/10', '13/10'), ('-1/2', '31/10'), ('-47/10', '-9/5')], [0, 1, -1, 0, 1]),
}


def certify(E, C, D, menus, w):
    E, C, D = [list(map(F, v)) for v in (E, C, D)]; menus = [tuple(map(F, m)) for m in menus]
    N = len(E); tree = Tree(E, C, D, menus)
    rows, rhs, bounds = [], [], {}
    for s in range(1, 1 << N):
        ind = [int(s >> i & 1) for i in range(N)]
        hi = tree.support(ind)
        if hi is None:
            return dict(status='K0 empty')
        lo = tree.support([-v for v in ind])
        b, a = hi['value'], -lo['value']; bounds[s] = (a, b)
        rows.append([(i, 1) for i in range(N) if ind[i]]); rhs.append(b)
        rows.append([(i, -1) for i in range(N) if ind[i]]); rhs.append(-a)
    outer = Model(N, [], [], rows, rhs, [(None, None)] * N).solve([-F(v) for v in w])
    estar, outer_max = outer['x'], outer['value']
    true_max = tree.support(w)['value']
    in_outer = all(a <= sum(estar[i] for i in range(N) if s >> i & 1) <= b for s, (a, b) in bounds.items())
    return dict(status='gap' if outer_max > true_max else 'no gap', outer_max=outer_max, true_max=true_max,
                estar=estar, estar_in_outer=in_outer, estar_value=dot(estar, list(map(F, w))))


if __name__ == '__main__':
    eps = F(sys.argv[1]) if len(sys.argv) > 1 else F(0)
    print('zero powers replaced by', eps)
    for name, (E, C, D, menus, w) in CASES.items():
        C = [F(c) or eps for c in C]; D = [F(d) or eps for d in D]
        r = certify(E, C, D, menus, w)
        if r['status'] == 'K0 empty':
            print(name, 'K0 empty'); continue
        print(f"{name}: w={w}  max over subset outer = {r['outer_max']}  max over K0 = {r['true_max']}  "
              f"-> {r['status']}")
        print(f"    e* = {tuple(str(v) for v in r['estar'])}, in subset outer (exact): {r['estar_in_outer']}, "
              f"w.e* = {r['estar_value']}")
