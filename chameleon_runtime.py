"""Small public entry point. Exact regimes, certified affine acceptance, optional tree fallback."""
from pathlib import Path
from fractions import Fraction as F
import sys
sys.path.insert(0,str(Path(__file__).parent/'evidence'))
import n2_exact, n3_exact, homogeneous_exact
from affine_decision import AffinePolicyLP, rational


class ExactPolicy:
    def __init__(self,kind,E,C,D,e,menus,ks=None):
        self.kind,self.E,self.C,self.D,self.initial,self.menus,self.ks=kind,E,C,D,e,menus,ks

    def power(self,history):
        ys=tuple(map(rational,history));t=len(ys)-1
        if not 0<=t<len(self.menus) or any(not self.menus[j][0]<=y<=self.menus[j][1] for j,y in enumerate(ys)):
            raise ValueError('observed requests must lie in the commitment')
        if self.kind=='single':return (ys[t],)
        if self.kind=='total-energy':
            total=sum(self.E)
            if not total:return tuple(F(0) for _ in self.E)
            weights=[v/total for v in self.E]
            return tuple(self.initial[i]-weights[i]*sum(self.initial)+weights[i]*ys[0]
                         if t==0 else weights[i]*ys[t] for i in range(len(self.E)))
        e=self.initial
        for j,y in enumerate(ys):
            if self.kind=='N2':p=n2_exact.action(e,y,self.ks[j+1],self.C,self.D)
            elif self.kind=='N3':p=n3_exact.action(e,y,self.ks[j+1],self.C,self.D)
            else:
                from balance_policy_check import waterfill
                x=waterfill([v-self.D[0] for v in e],[v+self.C[0] for v in e],sum(e)-y)
                if x is None:raise RuntimeError('no action from a certified initial state')
                p=tuple(v-z for v,z in zip(e,x))
            e=tuple(v-z for v,z in zip(e,p))
        return tuple(p)


def template_bounds(E,C,D,menus):
    """Unit-template outer bounds, with exact primal/dual certificates for each LP optimum.

    None means the numerical solver did not certify a step; never an exact infeasibility claim.
    """
    from itertools import product
    from review_codex_h_independent import Model
    N=len(E)
    if N>6:raise ValueError('template enumeration is limited to N<=6; use the affine test directly')
    dirs=[d for d in product((-1,0,1),repeat=N) if any(d)]
    bounds=[sum(max(d[i],0)*E[i] for i in range(N)) for d in dirs]
    for lo,hi in reversed(menus):
        reqs=sorted({lo,hi});nv=N*(1+len(reqs));ub=[];bu=[];eq=[];be=[]
        for k,y in enumerate(reqs):
            eq.append([(N*(k+1)+i,1) for i in range(N)]);be.append(y)
            for d,h in zip(dirs,bounds):
                ub.append([(i,d[i]) for i in range(N) if d[i]]+
                          [(N*(k+1)+i,-d[i]) for i in range(N) if d[i]])
                bu.append(h)
        model=Model(nv,eq,be,ub,bu,[(F(0),v) for v in E]+[(-C[i],D[i]) for _ in reqs for i in range(N)])
        following=[]
        for d in dirs:
            r=model.solve([-v for v in d]+[0]*(nv-N))
            if r is None:return None
            following.append(r['value'])
        bounds=following
    return list(zip(dirs,bounds))


def decide(data,template=False,tree=False):
    E,C,D=[tuple(map(rational,data[k])) for k in ('E','C','D')]
    e=tuple(map(rational,data['initial']));menus=tuple(tuple(map(rational,p)) for p in data['intervals'])
    N=len(E)
    if not N or any(len(v)!=N for v in (C,D,e)) or any(x<0 for v in (E,C,D) for x in v):
        raise ValueError('equal nonempty vectors and nonnegative parameters required')
    if any(len(p)!=2 or p[0]>p[1] for p in menus):raise ValueError('ordered finite request intervals required')
    def result(status,method,**extra):return dict(status=status,method=method,**extra)
    if any(v<0 or v>cap for v,cap in zip(e,E)):
        return result('infeasible','physical-box'),None
    # Cheap exact necessary outer constraints: aggregate power and every energy prefix.
    lower=upper=F(0)
    for lo,hi in menus:
        lower+=lo;upper+=hi
        if lo < -sum(C) or hi>sum(D) or sum(e)-upper<0 or sum(e)-lower>sum(E):
            return result('infeasible','aggregate-necessary-conditions'),None
    if N==1:return result('feasible','single',certification='rational'),ExactPolicy('single',E,C,D,e,menus)
    if N==2:
        ks=n2_exact.kernels(E,C,D,menus);inside=n2_exact.contains(ks[0],e);kind='N2'
    elif N==3:
        ks=n3_exact.kernels(E,C,D,menus)
        inside=ks[0] is not None and all(ks[0][0][s]<=n3_exact.sumset(e,s)<=ks[0][1][s] for s in range(1,8));kind='N3'
    elif all(C[i]>=E[i] and D[i]>=E[i] for i in range(N)):
        a,b=F(0),sum(E)
        for lo,hi in reversed(menus):
            a,b=max(F(0),a+hi),min(sum(E),b+lo)
            if a>b:break
        inside=a<=sum(e)<=b;kind='total-energy';ks=None
    elif len(set(zip(E,C,D)))==1:
        ks=homogeneous_exact.kernels(N,E[0],C[0],D[0],menus)
        inside=homogeneous_exact.member(ks[0],e);kind='homogeneous'
    else:
        inside=None
    if inside is not None:
        return result('feasible' if inside else 'infeasible',kind,certification='rational'),\
               ExactPolicy(kind,E,C,D,e,menus,ks) if inside else None
    note=None
    if template:
        try:
            outer=template_bounds(E,C,D,menus)
            if outer is not None and any(sum(v*x for v,x in zip(d,e))>h for d,h in outer):
                return result('infeasible','unit-template',certification='rational-support-bounds'),None
            if outer is None:note='template step did not obtain a certificate'
        except (AssertionError,RuntimeError) as exc:
            note='template certificate unavailable: '+str(exc)
    lp=AffinePolicyLP(E,C,D,menus)
    status,policy=lp.decide(e)
    if status=='certified':
        return result('feasible','segregated-affine',certification='rational',policy=policy.as_dict()),policy
    info=result('unknown','segregated-affine',inner_status=status)
    if note:info['outer_note']=note
    if tree:
        if len(menus)>12:raise ValueError('tree fallback limited to T<=12 to avoid exponential allocation')
        from review_codex_h_independent import Tree
        model=Tree(E,C,D,menus);r=model.member(e)
        if r is None:
            return result('infeasible_float','endpoint-tree',certification='none',note='presolve-off cross-check; no rational Farkas certificate'),None
        return result('feasible','endpoint-tree',certification='rational-primal-witness',
                      tree_states=[list(map(str,r['x'][j:j+N])) for j in range(0,model.n,N)],
                      tree_edges=[dict(parent=p,child=c,request=str(y)) for p,c,y in model.nodes]),None
    return info,None
