"""Run one initial-state decision, optionally execute a certified policy."""
import argparse,json
from pathlib import Path
from fractions import Fraction
from chameleon_runtime import decide

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path)
    parser.add_argument('--demo',action='store_true')
    parser.add_argument('--template',action='store_true',help='certified unit-template outer test (N<=6)')
    parser.add_argument('--tree',action='store_true',help='exponential fallback on unknown states (T<=12)')
    parser.add_argument('--requests',nargs='+',help='observed requests; execute the available causal policy')
    args=parser.parse_args()
    paths=sorted((Path(__file__).parent/'examples').glob('*.json')) if args.demo else [args.input]
    if not paths or paths[0] is None:parser.error('choose --input or --demo')
    for path in paths:
        try:
            result,policy=decide(json.loads(path.read_text()),template=args.template,tree=args.tree)
            if args.requests:
                if policy is None:raise ValueError('no executable policy from this decision; tree states cover endpoints only')
                ys=list(map(Fraction,args.requests));result['powers']=[list(map(str,policy.power(ys[:t+1]))) for t in range(len(ys))]
            print(json.dumps(dict(example=path.name,**result),ensure_ascii=False))
        except (ValueError,KeyError,RuntimeError,AssertionError) as exc:parser.error(str(exc))

if __name__=='__main__':main()
