import itertools,json,unittest
from pathlib import Path
from fractions import Fraction as F
from chameleon_runtime import decide,AffinePolicyLP

ROOT=Path(__file__).resolve().parents[1]
class ReleaseTests(unittest.TestCase):
    def check_paths(self,data,policy):
        E,C,D=[list(map(F,data[k])) for k in ('E','C','D')]
        menus=[sorted(set((F(l),(F(l)+F(u))/2,F(u)))) for l,u in data['intervals']]
        for ys in itertools.product(*menus):
            e=list(map(F,data['initial']))
            for t,y in enumerate(ys):
                p=policy.power(ys[:t+1]);self.assertEqual(sum(p),y)
                self.assertTrue(all(-C[i]<=v<=D[i] for i,v in enumerate(p)))
                e=[x-v for x,v in zip(e,p)]
                self.assertTrue(all(0<=x<=E[i] for i,x in enumerate(e)))
    def test_exact_regime_policies(self):
        for name in ('single','n2','n3','homogeneous','full_reach'):
            data=json.loads((ROOT/'examples'/f'{name}.json').read_text())
            r,p=decide(data);self.assertEqual(r['status'],'feasible');self.check_paths(data,p)
    def test_fraction_policy_returned_and_executes(self):
        data=json.loads((ROOT/'examples/affine.json').read_text());r,p=decide(data)
        self.assertEqual(r['certification'],'rational')
        self.assertTrue(all(isinstance(x,F) for x in p.values.values()));self.check_paths(data,p)
    def test_affine_gap_is_unknown_without_tree(self):
        data=json.loads((ROOT/'examples/affine_gap.json').read_text());r,p=decide(data)
        self.assertEqual(r['status'],'unknown');self.assertIsNone(p)
        r,p=decide(data,tree=True);self.assertEqual(r['status'],'feasible')
        self.assertEqual(r['certification'],'rational-primal-witness')
    def test_inert_zero_request(self):
        for kind in ('affine','segregated'):
            lp=AffinePolicyLP([1],[0],[0],[(0,0)],kind);s,p=lp.decide([F(1,2)])
            self.assertEqual(s,'certified');self.assertEqual(p.power([0]),(F(0),))
    def test_initial_box_and_empty_horizon(self):
        lp=AffinePolicyLP([1],[1],[1],[(1,1)])
        self.assertEqual(lp.decide([F(3,2)])[0],'rejected')
        self.assertFalse(lp.exact_check([0]*lp.nv,[F(3,2)]))
        s,p=AffinePolicyLP([1],[1],[1],[]).decide([F(1,2)])
        self.assertEqual(s,'certified')
    def test_outside_commitment_not_executed(self):
        data=json.loads((ROOT/'examples/affine.json').read_text());_,p=decide(data)
        with self.assertRaises(ValueError):p.power([1])
    def test_invalid_request_interval(self):
        with self.assertRaises(ValueError):AffinePolicyLP([1],[1],[1],[(2,1)])
    def test_necessary_rejection(self):
        data=dict(E=[1]*4,C=[1]*4,D=[1]*4,initial=[0]*4,intervals=[[1,2]])
        r,p=decide(data);self.assertEqual(r['status'],'infeasible')
    def test_template_rejects_known_outer_gap(self):
        data=dict(E=[4,5,1,1],C=[0,0,3,'1/2'],D=[1,'1/2',2,0],
                  initial=[4,0,'1/5',1],intervals=[['1/5',1],[-1,'6/5']])
        r,p=decide(data,template=True)
        self.assertEqual(r['status'],'infeasible')
        self.assertEqual(r['certification'],'rational-support-bounds')
    def test_certified_template(self):
        data=json.loads((ROOT/'examples/affine.json').read_text())
        r,p=decide(data,template=True);self.assertEqual(r['status'],'feasible')
if __name__=='__main__':unittest.main()
