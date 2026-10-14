"""Re-run necessary release checks without searching for new results."""
from pathlib import Path
import subprocess,sys,json,time,platform,hashlib,re
import numpy,scipy

ROOT=Path(__file__).resolve().parent
CODE=ROOT/'complexity_20260925/evidence'
COMMANDS=[
 ('runtime regressions',['-m','unittest','discover','-s','tests','-v'],ROOT),
 ('CLI demo',['run.py','--demo'],ROOT),
 ('CLI policy execution',['run.py','--input','examples/affine.json','--requests','0','1/10'],ROOT),
 ('N2 recursion',['n2_exact.py'],CODE),
 ('N3 recursion',['n3_exact.py'],CODE),
 ('N3 lemma certificates',['n3_lemma_certificate.py'],CODE),
 ('homogeneous recursion',['homogeneous_exact.py','3','100'],CODE),
 ('independent homogeneous attack',['review_codex_h_independent.py'],CODE),
 ('Example B facet certificate',['review_codex_n4_geometry.py'],CODE),
 ('Example C certificate',['n4_real_certificate.py','--three-types'],CODE),
 ('Example C positive certificate',['n4_real_certificate.py','1/100','--three-types'],CODE),
 ('two-type certificates',['two_types_certificate.py'],CODE),
 ('two-type positive certificates',['two_types_certificate.py','1/100'],CODE),
 ('coefficient-2 facets',['n4_normal_certificate.py'],CODE),
 ('coefficient-2 positive facets',['n4_normal_certificate.py','1/100'],CODE),
 ('affine gap certificate',['affine_gap_certificate.py'],CODE),
 ('affine positive gap certificate',['affine_gap_certificate.py','1/100'],CODE),
]

def main():
    records=[];logs=[]
    for name,args,cwd in COMMANDS:
        start=time.perf_counter()
        r=subprocess.run([sys.executable,*args],cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
        records.append(dict(check=name,command='python '+' '.join(args),cwd=str(cwd.relative_to(ROOT)) or '.',
                            exit_code=r.returncode,seconds=round(time.perf_counter()-start,3)))
        logs.append(name+'\n$ python '+' '.join(args)+'\n'+r.stdout)
        print(name,'PASS' if r.returncode==0 else 'FAIL',flush=True)
        if r.returncode:print(r.stdout);break
    broken=[]
    for path in ROOT.rglob('*.md'):
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text()):
            target=target.strip('<>').split('#')[0]
            if not target or '://' in target or target.startswith('mailto:'):continue
            if not (path.parent/target).exists():broken.append(dict(file=str(path.relative_to(ROOT)),target=target))
    english_violations=[]
    ignored={'.git','.venv','__pycache__'}
    han=re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]')
    for path in ROOT.rglob('*'):
        rel=path.relative_to(ROOT)
        if not path.is_file() or any(part in ignored for part in rel.parts):continue
        if han.search(str(rel)) or '_ZH.md' in str(rel):
            english_violations.append(dict(file=str(rel),reason='non-English document name'))
        try:content=path.read_text(encoding='utf-8')
        except UnicodeError:continue
        if han.search(content):
            english_violations.append(dict(file=str(rel),reason='Han characters in published text'))
    summary=dict(date='2026-10-14',python=platform.python_version(),numpy=numpy.__version__,scipy=scipy.__version__,
                 checks=records,broken_markdown_links=broken,english_violations=english_violations,
                 historical_211063_samples_rerun=False,
                 note='Rational certificate scripts validate exact identities. Other LP comparisons remain floating-point evidence.',
                 passed=len(records)==len(COMMANDS) and all(r['exit_code']==0 for r in records) and not broken and not english_violations)
    (ROOT/'results/certificates.txt').write_text('\n\n'.join(logs))
    (ROOT/'results/release_checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print('markdown links:',broken or 'PASS')
    print('English publication:',english_violations or 'PASS')
    if not summary['passed']:raise SystemExit(1)

if __name__=='__main__':main()
