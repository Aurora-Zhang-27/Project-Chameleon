"""Single-initial-state decision with history-dependent affine policies (2026-10-11).

Question: given an initial state e, is there a causal policy that honours every request sequence
y_t in [l_t, u_t]?  This module gives an INNER test: it searches a restricted policy class by one LP.
Acceptance is safe (the found policy is a valid causal policy); rejection only means that the class
contains no valid policy.

Policy classes (each p_{i,t} may use the current request y_t and all earlier ones, never later ones):
  'affine'      p_{i,t} = a_{i,t} + sum_{s<=t} G_{i,t,s} y_s
  'segregated'  p_{i,t} = a_{i,t} + sum_{s<=t} (G+_{i,t,s} y_s^+ + G-_{i,t,s} y_s^-),
                with y^+ = max(y, 0), y^- = max(-y, 0).  Contains 'affine' (G- = -G+) and the fixed
                participation factors of sandwich_experiment.py (only s = t, signs split).
Robust counterpart (exact for the class): every constraint is linear in the lifted requests
(y_s^+, y_s^-), which range independently over the convex hull of {(max(y,0), max(-y,0)) : y in
[l_s, u_s]}: a segment, or the triangle with vertices (u_s, 0), (0, 0), (0, -l_s) when l_s < 0 < u_s.
A linear function attains its maximum over this product of polytopes at vertices, period by period,
so "constant + sum_s max_v (coefficient . v) <= rhs" is the exact worst case; each max becomes an
auxiliary variable z_s >= coefficient . v for the 2 or 3 vertices v.  Balance sum_i p_{i,t} = y_t for
all requests is imposed coefficient-wise.  LP size: O(N T^2) variables, O(N T^3) nonzeros.

Certification of an acceptance: the LP is solved (HiGHS primal feasibility tolerance 1e-9) with the
inequalities tightened by MARGIN (first all of them, except the power rows of inert devices whose policy
is fixed to 0; then, if needed, only those with a positive right-hand side); the
policy coefficients are rounded to fractions (denominators up to 1e4, 1e6, 1e9 tried), the device with the
widest power range absorbs the rounding so that the
balance holds exactly, and every robust inequality is re-checked in exact arithmetic (Fraction),
with the instance data read as the decimals they were written in.  If no tightened LP is feasible (some
constraints may be forced to hold with equality), the untightened solution is rounded and checked the
same way.  Returns 'certified' only when an exact check passes, with the repaired CertifiedPolicy object. Float-only and rejected results are unknown deliverability.
Usage (smoke test on Examples B and C): python3 affine_decision.py"""
from fractions import Fraction as F
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix

MARGIN = 1e-7


def lifted_vertices(l, u):
    pts = {(max(l, 0.), max(-l, 0.)), (max(u, 0.), max(-u, 0.))}
    if l < 0 < u:
        pts.add((0., 0.))
    return sorted(pts)



def rational(v):
    return v if isinstance(v, F) else F(str(v))


class CertifiedPolicy:
    """The actual repaired rational coefficients, checked over the whole request box."""
    def __init__(self, lp, values, initial):
        self.N, self.T, self.kind = lp.N, lp.T, lp.kind
        self.ia, self.ig = dict(lp.ia), dict(lp.ig)
        self.values = dict(values)
        self.initial = tuple(map(rational, initial))
        self.E, self.C, self.D, self.menus = lp.Eq, lp.Cq, lp.Dq, lp.menusq

    def power(self, history):
        """Power for the latest observed request; never reads future requests."""
        ys = tuple(map(rational, history)); t = len(ys)-1
        if not 0 <= t < self.T:
            raise ValueError('one to T observed requests required')
        if any(not self.menus[s][0] <= y <= self.menus[s][1] for s,y in enumerate(ys)):
            raise ValueError('request outside the commitment')
        out = []
        for i in range(self.N):
            value = self.values[self.ia[i,t]]
            for j,y in enumerate(ys):
                if self.kind == 'affine':
                    value += self.values[self.ig[i,t,j,'+']]*y
                else:
                    value += self.values[self.ig[i,t,j,'+']]*max(y,0)
                    value += self.values[self.ig[i,t,j,'-']]*max(-y,0)
            out.append(value)
        return tuple(out)

    def as_dict(self):
        return dict(kind=self.kind,initial=list(map(str,self.initial)),
            intervals=[[str(v) for v in pair] for pair in self.menus],
            intercepts=[[str(self.values[self.ia[i,t]]) for t in range(self.T)] for i in range(self.N)],
            gains=[dict(device=i,time=t,request_time=j,sign=sg,value=str(self.values[k]))
                   for (i,t,j,sg),k in self.ig.items()])


class AffinePolicyLP:
    """Build once per instance (E, C, D, menus); call decide(e) for each initial state."""

    def __init__(self, E, C, D, menus, kind='segregated'):
        self.Eq, self.Cq, self.Dq = [tuple(map(rational,v)) for v in (E,C,D)]
        self.menusq = tuple(tuple(map(rational,pair)) for pair in menus)
        if not self.Eq or not len(self.Eq)==len(self.Cq)==len(self.Dq):
            raise ValueError('equal nonempty device vectors required')
        if any(v<0 for vec in (self.Eq,self.Cq,self.Dq) for v in vec):
            raise ValueError('nonnegative parameters required')
        if any(len(pair)!=2 or pair[0]>pair[1] for pair in self.menusq):
            raise ValueError('ordered request intervals required')
        if kind not in ('affine','segregated'):
            raise ValueError('unknown policy class')
        self.E, self.C, self.D = [list(map(float,v)) for v in (self.Eq,self.Cq,self.Dq)]
        self.menus = [(float(l), float(u)) for l,u in self.menusq]
        self.certified_policy = None
        self.kind = kind; N = self.N = len(E); T = self.T = len(menus)
        self.V = [lifted_vertices(l, u) for l, u in self.menus]
        nv = 0
        self.ia = {}
        for i in range(N):
            for t in range(T):
                self.ia[i, t] = nv; nv += 1
        self.ig = {}                               # (i, t, s, sign) -> column; affine uses one column per (i,t,s)
        for i in range(N):
            for t in range(T):
                for s in range(t + 1):
                    if kind == 'affine':
                        self.ig[i, t, s, '+'] = nv; nv += 1
                    else:
                        self.ig[i, t, s, '+'] = nv; self.ig[i, t, s, '-'] = nv + 1; nv += 2
        self.ncore = nv
        rows, cols, vals, rhs_const, rhs_e = [], [], [], [], []   # rhs = rhs_const + rhs_e . e
        self.rowinfo = []; self.rowdev = {}; cur_dev = [None]
        r = 0

        def coef_pm(i, t, s):
            """(coefficient dict on y^+, coefficient dict on y^-) of p_{i,t} for request s."""
            if kind == 'affine':
                c = self.ig[i, t, s, '+']; return {c: 1.}, {c: -1.}
            return {self.ig[i, t, s, '+']: 1.}, {self.ig[i, t, s, '-']: 1.}

        def robust(const, per_s, sign, b_const, b_e):
            """sign * (const + sum_s coef_s . v_s) <= b for all lifted requests; const, coef: dicts."""
            nonlocal r, nv
            row = {k: sign * v for k, v in const.items()}
            for s, (cp, cm) in per_s.items():
                z = nv; nv += 1; row[z] = 1.
                for vp, vm in self.V[s]:
                    rr = {}
                    for k, v in cp.items(): rr[k] = rr.get(k, 0.) + sign * v * vp
                    for k, v in cm.items(): rr[k] = rr.get(k, 0.) + sign * v * vm
                    rr[z] = -1.
                    for k, v in rr.items():
                        if v: rows.append(r); cols.append(k); vals.append(v)
                    rhs_const.append(0.); rhs_e.append(None); self.rowinfo.append(None); r += 1
            for k, v in row.items():
                if v: rows.append(r); cols.append(k); vals.append(v)
            rhs_const.append(b_const); rhs_e.append(b_e); self.rowinfo.append((const, per_s, sign)); r += 1
            self.rowdev[len(self.rowinfo) - 1] = cur_dev[0]

        for i in range(N):
            for t in range(T):
                per = {s: coef_pm(i, t, s) for s in range(t + 1)}
                cur_dev[0] = (i, 'power')
                robust({self.ia[i, t]: 1.}, per, +1, self.D[i], None)            # p <= D
                robust({self.ia[i, t]: 1.}, per, -1, self.C[i], None)            # -p <= C
                cur_dev[0] = (i, 'energy')
                const = {self.ia[i, tau]: 1. for tau in range(t + 1)}
                cum = {}
                for s in range(t + 1):
                    cp, cm = {}, {}
                    for tau in range(s, t + 1):
                        a, b = coef_pm(i, tau, s)
                        for k, v in a.items(): cp[k] = cp.get(k, 0.) + v
                        for k, v in b.items(): cm[k] = cm.get(k, 0.) + v
                    cum[s] = (cp, cm)
                robust(const, cum, +1, 0., (i, +1))                             # P <= e_i
                robust(const, cum, -1, self.E[i], (i, -1))                      # -P <= E_i - e_i
        self.nv = nv; self.nrow = r
        self.Aub = coo_matrix((vals, (rows, cols)), shape=(r, nv)).tocsr()
        self.rhs_const = np.array(rhs_const); self.rhs_e = rhs_e
        er, ec, ev, beq = [], [], [], []
        q = 0
        for t in range(T):
            for i in range(N):
                er.append(q); ec.append(self.ia[i, t]); ev.append(1.)
            beq.append(0.); q += 1
            for s in range(t + 1):
                signs = ('+',) if kind == 'affine' else ('+', '-')
                for sg in signs:
                    for i in range(N):
                        er.append(q); ec.append(self.ig[i, t, s, sg]); ev.append(1.)
                    beq.append(0. if s < t else (1. if sg == '+' else -1.)); q += 1
        self.Aeq = coo_matrix((ev, (er, ec)), shape=(q, nv)).tocsr(); self.beq = np.array(beq)
        # inert devices (C = D = 0) never move: their policy is fixed to 0 exactly
        self.inert = {i for i in range(N) if self.C[i] == 0 and self.D[i] == 0}
        self.bounds = [(None, None)] * nv
        for (i, t), k in self.ia.items():
            if i in self.inert: self.bounds[k] = (0., 0.)
        for (i, t, s, sg), k in self.ig.items():
            if i in self.inert: self.bounds[k] = (0., 0.)
        movable = [i for i in range(N) if i not in self.inert] or [N - 1]
        self.rep = max(movable, key=lambda i: self.C[i] + self.D[i])   # absorbs rounding in exact_check

    def _rhs(self, e, margin, mode):
        """Right-hand sides, main rows tightened by margin.  mode 'all': every main row except the power
        rows of inert devices; mode 'positive': only rows whose right-hand side is positive (a zero power
        limit is left exact, so a one-way device is not forced to move)."""
        b = self.rhs_const.copy()
        for k, tag in enumerate(self.rhs_e):
            if tag is not None:
                i, sg = tag
                b[k] = (e[i] if sg > 0 else self.E[i] - e[i])
            if self.rowinfo[k] is None:
                continue
            dev, kind = self.rowdev[k]
            if mode == 'all' and not (kind == 'power' and dev in self.inert):
                b[k] -= margin
            elif mode == 'positive' and b[k] > 0:
                b[k] -= margin
        return b

    def decide(self, e, certify=True):
        """'certified' | 'float_only' | 'rejected' (no policy in the class)."""
        self.certified_policy = None
        eq = tuple(map(rational,e))
        if len(eq)!=self.N or any(v<0 or v>cap for v,cap in zip(eq,self.Eq)):
            return 'rejected', None
        if self.T==0 or (len(self.inert)==self.N and all(l==u==0 for l,u in self.menusq)):
            val={k:F(0) for k in list(self.ia.values())+list(self.ig.values())}
            self.certified_policy=CertifiedPolicy(self,val,eq)
            return ('certified',self.certified_policy) if certify else ('float_ok',np.zeros(self.nv))
        e = [float(x) for x in eq]
        attempts = [('all', MARGIN), ('positive', MARGIN), ('none', 0.)] if certify else [('none', 0.)]
        for mode, margin in attempts:
            r = linprog(np.zeros(self.nv), A_ub=self.Aub, b_ub=self._rhs(e, margin, mode), A_eq=self.Aeq,
                        b_eq=self.beq, bounds=self.bounds, method='highs',
                        options={'primal_feasibility_tolerance': 1e-9})
            if r.status == 2 and margin == 0:
                r = linprog(np.zeros(self.nv), A_ub=self.Aub, b_ub=self._rhs(e,0.,'none'),
                            A_eq=self.Aeq,b_eq=self.beq,bounds=self.bounds,method='highs',
                            options={'primal_feasibility_tolerance':1e-9,'presolve':False})
            if r.status == 0:
                if not certify:
                    return 'float_ok', r.x
                if self.exact_check(r.x, eq):                  # also tried without margin: forced
                    return 'certified', self.certified_policy                   # equalities leave no room to tighten
                if margin == 0:
                    return 'float_only', r.x
            elif r.status != 2:
                raise RuntimeError(r.message)
        return 'rejected', None

    def exact_check(self, x, e):
        """Round the policy to fractions, repair the balance with the last device, check every
        robust inequality exactly."""
        N, T = self.N, self.T
        E, C, D = list(self.Eq), list(self.Cq), list(self.Dq)
        V = [[(rational(a),rational(b)) for a,b in lifted_vertices(l,u)] for l,u in self.menusq]
        ee = list(map(rational,e))
        self.certified_policy = None
        if len(ee)!=N or any(v<0 or v>cap for v,cap in zip(ee,E)):
            return False
        for cap in (10 ** 4, 10 ** 6, 10 ** 9):
            if self._exact_check_cap(x, e, cap, E, C, D, V, ee):
                return True
        return False

    def _exact_check_cap(self, x, e, cap, E, C, D, V, ee):
        N, T = self.N, self.T
        val = {k: F(float(x[k])).limit_denominator(cap) for k in list(self.ia.values()) + list(self.ig.values())}
        q = self.rep; others = [i for i in range(N) if i != q]
        for t in range(T):                                     # exact balance through device q
            val[self.ia[q, t]] = -sum(val[self.ia[i, t]] for i in others)
            for s in range(t + 1):
                for sg in (('+',) if self.kind == 'affine' else ('+', '-')):
                    target = F(0) if s < t else (F(1) if sg == '+' else F(-1))
                    val[self.ig[q, t, s, sg]] = target - sum(val[self.ig[i, t, s, sg]] for i in others)
        k = 0
        for i in range(N):
            for t in range(T):
                for kind_row in ('p+', 'p-', 'e+', 'e-'):
                    while self.rowinfo[k] is None:
                        k += 1
                    const, per_s, sign = self.rowinfo[k]
                    lhs = sign * sum((val[c] * F(v) for c, v in const.items()), F(0))
                    for s, (cp, cm) in per_s.items():
                        lhs += max(sign * (sum((val[c] * F(v) for c, v in cp.items()), F(0)) * vp
                                           + sum((val[c] * F(v) for c, v in cm.items()), F(0)) * vm)
                                   for vp, vm in V[s])
                    b = {'p+': D[i], 'p-': C[i], 'e+': ee[i], 'e-': E[i] - ee[i]}[kind_row]
                    if lhs > b:
                        return False
                    k += 1
        self.certified_policy = CertifiedPolicy(self,val,ee)
        return True


if __name__ == '__main__':
    from oracle2 import build, member_status
    cases = {'Example B': ([4, 5, 1, 1], [0, 0, 3, .5], [1, .5, 2, 0], [(.2, 1.), (-1., 1.2)]),
             'Example C': ([4, 4, 1, 1], [0, 0, 3, .5], [1, 1, 2, 0], [(.2, .6), (-1., 1.6)])}
    rng = np.random.default_rng(0)
    for name, (E, C, D, ms) in cases.items():
        M = build(np.array(C, float), np.array(D, float), np.array(E, float), ms)
        lps = {k: AffinePolicyLP(E, C, D, ms, k) for k in ('affine', 'segregated')}
        tally = {k: {} for k in lps}
        for _ in range(300):
            e = rng.uniform(0, E)
            ok = member_status(M, e) or member_status(M, e, presolve=False)
            for k, lp in lps.items():
                d = lp.decide(e)[0]
                assert not (d in ('certified', 'float_only') and not ok), (name, k, e)
                key = f"{'feasible' if ok else 'infeasible'}:{d}"
                tally[k][key] = tally[k].get(key, 0) + 1
        print(name, {k: dict(sorted(v.items())) for k, v in tally.items()})
