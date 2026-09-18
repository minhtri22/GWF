from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def load(p: Path): return json.loads(p.read_text(encoding='utf-8'))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--sqlite-dir',required=True); ap.add_argument('--postgres-dir',required=True); ap.add_argument('--out',required=True)
    a=Path(ap.parse_args().sqlite_dir); b=Path(ap.parse_args().postgres_dir); out=Path(ap.parse_args().out)
    sa=load(a/'BENCHMARK_SUMMARY.json'); sb=load(b/'BENCHMARK_SUMMARY.json')
    errors=[]; cases=[]
    amap={c['case_id']:c for c in sa['cases']}; bmap={c['case_id']:c for c in sb['cases']}
    if set(amap)!=set(bmap): errors.append(f'case sets differ: sqlite={sorted(amap)} postgres={sorted(bmap)}')
    for cid in sorted(set(amap)&set(bmap)):
        aa=load(a/cid/'semantic_snapshot.json'); bb=load(b/cid/'semantic_snapshot.json')
        equal=aa==bb
        if not equal: errors.append(f'{cid}: semantic snapshot differs')
        cases.append({'case_id':cid,'equal':equal,'sqlite_sha256':amap[cid].get('semantic_sha256'),'postgres_sha256':bmap[cid].get('semantic_sha256'),'outcome':amap[cid]['outcome'],'pivot_count':amap[cid]['pivot_count']})
    # Dataset and quality fixtures do not touch the persistence backend but their expected verdicts must remain identical.
    q1=[(x['id'],x['pass'],x['expected_issue']) for x in sa['quality_cases']]
    q2=[(x['id'],x['pass'],x['expected_issue']) for x in sb['quality_cases']]
    if q1!=q2: errors.append('quality-case semantics differ')
    d1=[(x['dataset_id'],x['ok']) for x in sa['dataset_integrity']]
    d2=[(x['dataset_id'],x['ok']) for x in sb['dataset_integrity']]
    if d1!=d2: errors.append('dataset-integrity semantics differ')
    result={'version':'0.5.1','result':'PASS' if not errors else 'FAIL','semantic_equivalence':not errors,'cases':cases,'errors':errors}
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps(result,indent=2))
    raise SystemExit(1 if errors else 0)
if __name__=='__main__': main()
