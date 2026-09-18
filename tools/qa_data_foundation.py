from __future__ import annotations
import json, sys, yaml
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from gwr.datasets import DatasetRegistry
from gwr.research_benchmark import ResearchBenchmarkSuite

def main():
    reg=DatasetRegistry(ROOT/'datasets'); suite=ResearchBenchmarkSuite(ROOT/'benchmarks'/'research_reliability.yaml')
    errors=[]; warnings=[]
    for did in reg.ids():
        r=reg.validate_integrity(did)
        if not r['ok']: errors.append(f'{did}: {r["errors"]}')
        m=reg.get(did).manifest
        if m.get('kind')=='real':
            for k in ['license','source_url','doi','citation','sha256']:
                if not m.get(k): errors.append(f'{did}: missing {k}')
        if m.get('kind')=='synthetic' and m.get('generator_seed')!=170917: errors.append(f'{did}: missing canonical generator seed')
    for c in suite.cases.values():
        if c.data['dataset_id'] not in reg.ids(): errors.append(f'{c.id}: dataset missing')
        if c.data.get('pivot_dataset_id') and c.data['pivot_dataset_id'] not in reg.ids(): errors.append(f'{c.id}: pivot dataset missing')
        for k in ['group_column','value_column','group_a','group_b','min_effect','min_per_group','alpha']:
            if k not in c.data: errors.append(f'{c.id}: missing {k}')
    for q in suite.quality_cases:
        if q['dataset_id'] not in reg.ids(): errors.append(f'{q["id"]}: dataset missing')
    summary={'datasets':len(reg.ids()),'research_cases':len(suite.cases),'quality_cases':len(suite.quality_cases),'errors':errors,'warnings':warnings,'result':'PASS' if not errors else 'FAIL'}
    print(json.dumps(summary,indent=2)); raise SystemExit(1 if errors else 0)
if __name__=='__main__': main()
