import pytest
from pathlib import Path
from gwr.runtime import GovernedWorkflowRuntime

@pytest.fixture
def runtime(tmp_path):
    domain=Path(__file__).parents[1]/"domains"/"example.workflow.yaml"
    rt=GovernedWorkflowRuntime(str(domain), str(tmp_path/"gwr.db"))
    yield rt
    rt.close()

@pytest.fixture
def seeded(runtime):
    p=runtime.create_project("demo")
    planner=runtime.governance.create_actor("AGENT","planner-1",["planner"],[p])
    operator=runtime.governance.create_actor("AGENT","operator-1",["operator"],[p])
    approver=runtime.governance.create_actor("HUMAN","human-1",["approver"],[p])
    return runtime,p,planner,operator,approver
