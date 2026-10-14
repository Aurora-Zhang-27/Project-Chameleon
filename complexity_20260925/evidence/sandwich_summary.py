"""Summarise sandwich_experiment.py output files.
Usage: python3 sandwich_summary.py FILE.json [FILE.json ...]
Per group: instances, sampled states (all inside the outer approximation), and
  wrong-accept  = exact infeasible among outer-accepted states (outer approximation too large),
  inner-accept  = states certified by the participation-factor policy (safe side),
  undecided     = outer accepts but inner rejects (exact answer needed),
  inner-miss    = exact feasible but inner rejects (how conservative the inner approximation is),
  instances with any wrong accept."""
import json, sys
from collections import defaultdict

rows = []
for f in sys.argv[1:]:
    rows += json.load(open(f))


def bucket_rho(r):
    x = r['rho']
    return 'rho=0 (one-way device)' if x == 0 else ('0<rho<=0.25' if x <= .25 else ('0.25<rho<=0.5' if x <= .5 else 'rho>0.5'))


def table(key, title):
    g = defaultdict(lambda: dict(inst=0, s=0, ok=0, inner=0, wrong=0, inst_wrong=0))
    for r in rows:
        k = key(r); d = g[k]
        d['inst'] += 1; d['s'] += r['samples']; d['ok'] += r['exact_ok']; d['inner'] += r['inner_ok']
        d['wrong'] += r['wrong_accept']; d['inst_wrong'] += r['wrong_accept'] > 0
    print(f'\n{title}')
    print(f"{'group':<26}{'inst':>6}{'states':>8}{'wrong-acc':>11}{'inner-acc':>11}{'undecided':>11}{'inner-miss':>11}{'inst w/ wrong':>15}")
    for k in sorted(g):
        d = g[k]; s = d['s']
        und = s - d['inner'] - d['wrong']          # outer accepts, inner rejects, exact feasible
        miss = (d['ok'] - d['inner']) / d['ok'] if d['ok'] else 0
        print(f"{str(k):<26}{d['inst']:>6}{s:>8}{d['wrong']/s:>11.4%}{d['inner']/s:>11.1%}{(und + d['wrong'])/s:>11.1%}{miss:>11.1%}{d['inst_wrong']:>15}")


short = sum(1 for r in rows if r['samples'] < 25)
print(f'instances kept: {len(rows)}; with fewer than 25 accepted points: {short} '
      f'(instances with no accepted point were dropped by the experiment)')
n4 = [r for r in rows if r['N'] >= 4]
print(f"N>=4 only: instances {len(n4)}, states {sum(r['samples'] for r in n4)}, "
      f"wrong accepts {sum(r['wrong_accept'] for r in n4)}")
table(lambda r: r['N'], 'by number of devices N')
table(bucket_rho, 'by power ratio rho = min_i min(C_i,D_i) / max_i max(C_i,D_i)')
table(lambda r: (r['N'] >= 4, bucket_rho(r)), 'N>=4 only, by rho  (key: (N>=4, rho bucket))')
