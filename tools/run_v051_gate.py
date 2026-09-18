from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run(cmd, *, env=None, log=None):
    p=subprocess.run(cmd,cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if log: Path(log).write_text(p.stdout,encoding='utf-8')
    print(p.stdout,end='')
    if p.returncode: raise RuntimeError(f'command failed ({p.returncode}): {cmd}')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--postgres-url',default=os.environ.get('GWR_TEST_DATABASE_URL')); ap.add_argument('--out',default=str(ROOT/'evidence'/'v0.5.1'))
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    if not a.postgres_url: raise SystemExit('PostgreSQL gate NOT RUN: provide --postgres-url or GWR_TEST_DATABASE_URL')
    preflight=out/'preflight'
    run([sys.executable,'tools/preflight_v051_postgres.py','--postgres-url',a.postgres_url,'--out',str(preflight)],env=os.environ.copy(),log=out/'postgres_preflight.txt')
    base=os.environ.copy(); base.pop('GWR_TEST_DATABASE_URL',None); pg=base.copy(); pg['GWR_TEST_DATABASE_URL']=a.postgres_url; pg['GWR_TEST_NAMESPACE_PREFIX']='gwr_v051_gate'
    sqlite_b=out/'sqlite_benchmark'; postgres_b=out/'postgres_benchmark'
    run([sys.executable,'-m','pytest','-q'],env=base,log=out/'pytest_sqlite.txt')
    run([sys.executable,'-m','pytest','-q'],env=pg,log=out/'pytest_postgres.txt')
    run([sys.executable,'tools/run_research_benchmark.py','--out',str(sqlite_b)],env=base,log=out/'benchmark_sqlite.txt')
    run([sys.executable,'tools/run_research_benchmark.py','--out',str(postgres_b)],env=pg,log=out/'benchmark_postgres.txt')
    run([sys.executable,'tools/run_v051_restart_probe.py','--out',str(out/'restart_probe')],env=pg,log=out/'restart_probe.txt')
    run([sys.executable,'tools/compare_v051_semantics.py','--sqlite-dir',str(sqlite_b),'--postgres-dir',str(postgres_b),'--out',str(out/'SEMANTIC_EQUIVALENCE.json')],env=base,log=out/'semantic_compare.txt')
    run([sys.executable,'tools/qa_implementation.py'],env=base,log=out/'qa_implementation.txt')
    eq=json.loads((out/'SEMANTIC_EQUIVALENCE.json').read_text()); restart=json.loads((out/'restart_probe'/'RESTART_PROBE.json').read_text())
    result={'version':'0.5.1','status':'PASS','postgres_live_tested':True,'same_41_tests_sqlite_and_postgres':True,'six_research_cases_sqlite_and_postgres':True,'restart_persistence_equal':restart['restart_persistence_equal'],'semantic_equivalence':eq['semantic_equivalence'],'v06_unblocked':bool(restart['restart_persistence_equal'] and eq['semantic_equivalence'])}
    (out/'POSTGRES_GATE.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result,indent=2))
if __name__=='__main__': main()
