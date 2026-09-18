from pathlib import Path
from gwr.runtime import GovernedWorkflowRuntime

def test_crash_restart_preserves_authoritative_state(tmp_path):
    domain=Path(__file__).parents[1]/"domains"/"example.workflow.yaml"; db=tmp_path/'persistent.db'
    rt=GovernedWorkflowRuntime(str(domain),str(db)); p=rt.create_project('persist'); actor=rt.governance.create_actor('AGENT','x',['planner'],[p]); a=rt.knowledge.create_artifact(p,'intent','persist-key',actor)
    rt.close(); rt2=GovernedWorkflowRuntime(str(domain),str(db)); assert rt2.knowledge.get_artifact(a)['logical_key']=='persist-key'; rt2.close()
