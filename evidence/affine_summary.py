"""Summarise affine_sandwich.py outputs: how many sampled states each inner test decides.
All states lie inside the subset outer approximation.  'accept' counts certified + float_only acceptances
(certified ones are checked in exact arithmetic); 'undecided' = exactly feasible but not accepted, i.e.
states that would still need the tree LP.  Infeasible states are rejected by every inner test (asserted).
Usage: python3 affine_summary.py FILE..."""
import json, sys


def main(files):
    rows = [r for f in files for r in json.load(open(f))]
    groups = {}
    for r in rows:
        for key in (str(r['N']), 'N>=4' if r['N'] >= 4 else None, 'all'):
            if key:
                groups.setdefault(key, []).append(r)
    print(f"{'group':>6} {'inst':>6} {'states':>7} {'feasible':>9} | {'pf acc':>7} {'aff acc':>8} {'seg acc':>8} | "
          f"{'pf undec':>8} {'aff undec':>9} {'seg undec':>9} | {'seg float-only':>14}")
    for key in sorted(groups, key=lambda k: (k == 'all', k == 'N>=4', k)):
        g = groups[key]; S = sum(r['samples'] for r in g); X = sum(r['exact_ok'] for r in g)
        acc = lambda k: sum(r[k].get('certified', 0) + r[k].get('float_only', 0) for r in g)
        pf = sum(r['pf_ok'] for r in g); af = acc('affine'); sg = acc('segregated')
        fo = sum(r['segregated'].get('float_only', 0) for r in g)
        pct = lambda a: f"{100 * a / X:6.2f}%" if X else '   n/a'
        print(f"{key:>6} {len(g):>6} {S:>7} {X:>9} | {pct(pf):>7} {pct(af):>8} {pct(sg):>8} | "
              f"{pct(X - pf):>8} {pct(X - af):>9} {pct(X - sg):>9} | {fo:>14}")
    t_tree = sum(r['t_tree'] for r in rows); t_seg = sum(r['t_seg'] for r in rows); S = sum(r['samples'] for r in rows)
    print(f"mean time per state: tree LP {1e3 * t_tree / S:.2f} ms, segregated decision (incl. exact check) "
          f"{1e3 * t_seg / S:.2f} ms")
    und = [(r['N'], r['T'], len(r['undecided_points'])) for r in rows if r['undecided_points']]
    print('instances with segregated-undecided states:', len(und), 'states:', sum(u[2] for u in und))


if __name__ == '__main__':
    main(sys.argv[1:])
