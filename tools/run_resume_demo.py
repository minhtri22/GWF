from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from gwr.runtime import GovernedWorkflowRuntime
from gwr.research_orchestrator import ResearchOrchestrator
from gwr.research_demo import DeterministicResearchExecutor

ROLES=['research_lead','literature_reviewer','protocol_designer','experimenter','analyst','adversarial_reviewer','reproducibility_reviewer']
out=ROOT/'evidence'/'research_v02'/'resume'
out.mkdir(parents=True,exist_ok=True)
db=out/'runtime.db'
if db.exists(): db.unlink()
rt=GovernedWorkflowRuntime(str(ROOT/'domains'/'research.workflow.yaml'),str(db))
p=rt.create_project('v0.2-resume')
actors={r:rt.governance.create_actor('AGENT',f'{r}-resume',[r],[p]) for r in ROLES}
h=rt.governance.create_actor('HUMAN','human-resume',['human_approver'],[p])
o=ResearchOrchestrator(rt,actors,human_approver_id=h)
first=o.start(p,DeterministicResearchExecutor('pass'),max_steps=3)
assert first['status']=='PAUSED'
second=o.resume(first['checkpoint_id'],DeterministicResearchExecutor('pass'),max_steps=100)
assert second['status']=='COMPLETED'
(o.write_report(second['orchestration_id'],out/'REPORT.md'))
(out/'result.json').write_text(json.dumps({'first':first,'resumed':second},indent=2),encoding='utf-8')
print(json.dumps({'first':first,'resumed':second},indent=2))
rt.close()
