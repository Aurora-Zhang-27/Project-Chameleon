"""Seed result for the complexity blueprint (2026-09-25).

Two heterogeneous, lossless, bidirectional batteries. The request sequences
a = (-1, -2) and b = (-1, +1.5) share the first request, but the set of
first-period allocations that can continue to a and the set that can continue
to b are disjoint. Hence no commitment-agnostic causal rule serves every
sequence that some causal rule can serve, i.e. no robustly maximal policy
exists (contrast: Evans-Tindemans-Angeli prove one exists for discharge-only).

Run: python3 no_universal_policy.py   (needs numpy, scipy)
"""
import numpy as np
from scipy.optimize import linprog

E = np.array([2.0, 4.0])   # energy capacity (MWh)
P = np.array([2.0, 0.5])   # symmetric charge/discharge limit (MW)
e0 = np.array([0.0, 2.0])  # initial energy (MWh); period length 1 h, lossless


def first_alloc_range(menus):
    """[min, max] of battery-1 net output at t=0 over causal trees that honour
    every request in the per-period menus (each menu is a finite set)."""
    N, T = 2, len(menus)
    nodes = []

    def rec(t, hist):
        if t == T:
            return
        for y in menus[t]:
            nodes.append((t, hist + (y,)))
            rec(t + 1, hist + (y,))

    rec(0, ())
    idx = {n: k for k, n in enumerate(nodes)}
    nv = len(nodes) * N
    Aeq, beq, Aub, bub = [], [], [], []
    for (t, h), k in idx.items():
        row = np.zeros(nv); row[k * N:(k + 1) * N] = 1
        Aeq.append(row); beq.append(h[-1])                 # sum_i p_i = y
        path = [idx[(s, h[:s + 1])] for s in range(t + 1)]
        for i in range(N):
            row = np.zeros(nv)
            for kk in path:
                row[kk * N + i] = 1
            Aub.append(row.copy()); bub.append(e0[i])        # energy >= 0
            Aub.append(-row); bub.append(E[i] - e0[i])       # energy <= E
    bounds = [(-P[i], P[i]) for _ in nodes for i in range(N)]
    root = idx[(0, (menus[0][0],))] * N
    out = []
    for sign in (1, -1):
        c = np.zeros(nv); c[root] = sign
        r = linprog(c, A_ub=np.array(Aub), b_ub=bub, A_eq=np.array(Aeq),
                    b_eq=beq, bounds=bounds, method="highs")
        if r.status != 0:
            return None
        out.append(r.x[root])
    return out


if __name__ == "__main__":
    ra = first_alloc_range([[-1.0], [-2.0]])
    rb = first_alloc_range([[-1.0], [1.5]])
    print("battery-1 output at t=0 compatible with a=(-1,-2):  ", ra)   # [-0.5, -0.5]
    print("battery-1 output at t=0 compatible with b=(-1,+1.5):", rb)   # [-1.5, -1.0]
    print("disjoint -> no robustly maximal causal policy:", ra[1] < rb[0] or rb[1] < ra[0])
