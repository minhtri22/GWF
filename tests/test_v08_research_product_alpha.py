from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.domain_sdk import DomainSDK
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import canonical_json, uid, utcnow

ROOT = Path(__file__).parents[1]


def runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1000)
    rt = GovernedWorkflowRuntime(str(ROOT / "domains" / "research.workflow.yaml"), str(tmp_path / "v08.db"), auth_secret="x" * 64)
    human = rt.governance.create_actor("HUMAN", "operator", ["human_approver"], [])
    rt.auth.register_human(human, "operator", "operator-password-long")
    tenant = rt.tenancy.create_tenant("UAT", human)
    workspace = rt.tenancy.create_workspace(tenant, "Research", human)
    project = rt.create_scoped_project("Alpha Project", tenant, workspace, human)
    rt.tenancy.add_project_member(project, human, "APPROVER", human)
    return rt, human, project


def login(client):
    r = client.post("/auth/login", json={"username": "operator", "password": "operator-password-long"})
    assert r.status_code == 200
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def test_domain_sdk_validates_inspects_and_scaffolds(tmp_path):
    report = DomainSDK.validate(ROOT / "domains" / "research.workflow.yaml")
    assert report.ok is True
    assert report.counts["workunit_templates"] >= 1
    inspected = DomainSDK.inspect(ROOT / "domains" / "research.workflow.yaml")
    assert inspected["domain_id"] == "research.full-cycle"
    scaffold = DomainSDK.scaffold("uat.example", display_name="UAT Example")
    path = tmp_path / "uat.workflow.yaml"
    path.write_text(scaffold, encoding="utf-8")
    generated = DomainSDK.validate(path)
    assert generated.ok is True
    assert generated.domain_id == "uat.example"


def test_operator_dashboard_aggregates_run_approval_failure_and_recovery(tmp_path, monkeypatch):
    rt, human, project = runtime(tmp_path, monkeypatch)
    agent = rt.governance.create_actor("AGENT", "researcher", ["research_lead"], [])
    rt.tenancy.add_project_member(project, agent, "RESEARCHER", human)

    proposal = rt.governance.prepare_system_proposal(
        project, "CONFIRM_ROOT", ["demo-root"], {"failure_id": "f-demo", "root": "experiment_plan"}, "human_recovery_confirmation"
    )

    failure_id = uid("fail")
    rt.db.conn.execute(
        "INSERT INTO failures VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (failure_id, project, "wu-demo", "pilot_degenerate", "PILOT", "run-demo", None, None, "[]",
         "experiment_plan", None, "PROPOSED", "phase_06_plan_and_implement_experiment", "MEDIUM",
         "sig-demo", "OPEN", utcnow(), None),
    )
    recovery_id = uid("rec")
    rt.db.conn.execute(
        "INSERT INTO recoveries VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (recovery_id, project, failure_id, "experiment_plan", "phase_06_plan_and_implement_experiment",
         "[]", "[]", "[]", "[]", "[]", "[]", "[]", "AFTER_INVALIDATION", "PLANNED", utcnow()),
    )
    rt.db.conn.commit()

    client = TestClient(create_app(rt))
    auth = login(client)
    res = client.get(f"/product/projects/{project}/dashboard", headers=auth)
    assert res.status_code == 200
    body = res.json()
    assert body["project"]["id"] == project
    assert body["metrics"]["pending_approvals"] == 1
    assert body["metrics"]["open_failures"] == 1
    assert body["failure_graph"]["edges"]
    pending = client.get(f"/product/projects/{project}/approvals", headers=auth)
    assert pending.status_code == 200
    assert pending.json()["approvals"][0]["proposal_id"] == proposal
    rt.close()


def test_authenticated_exact_hash_rejection_endpoint(tmp_path, monkeypatch):
    rt, human, project = runtime(tmp_path, monkeypatch)
    proposal = rt.governance.prepare_system_proposal(
        project, "CONFIRM_ROOT", ["demo"], {"root": "protocol"}, "human_recovery_confirmation"
    )
    row = rt.db.one("SELECT payload_hash FROM proposals WHERE proposal_id=?", (proposal,))
    client = TestClient(create_app(rt))
    auth = login(client)

    wrong = client.post(f"/proposals/{proposal}/reject", headers=auth, json={"expected_hash": "wrong", "reason": "UAT"})
    assert wrong.status_code == 400
    ok = client.post(f"/proposals/{proposal}/reject", headers=auth, json={"expected_hash": row["payload_hash"], "reason": "Needs revision"})
    assert ok.status_code == 200
    assert rt.db.one("SELECT status FROM proposals WHERE proposal_id=?", (proposal,))["status"] == "REJECTED"
    approval = rt.db.one("SELECT * FROM approvals WHERE proposal_id=?", (proposal,))
    assert approval["decision"] == "REJECTED"
    rt.close()


def test_product_api_hides_cross_tenant_dashboard(tmp_path, monkeypatch):
    rt, alice, project_a = runtime(tmp_path, monkeypatch)
    bob = rt.governance.create_actor("HUMAN", "bob", ["human_approver"], [])
    rt.auth.register_human(bob, "bob", "bob-password-longgg")
    tenant_b = rt.tenancy.create_tenant("B", bob)
    workspace_b = rt.tenancy.create_workspace(tenant_b, "B", bob)
    project_b = rt.create_scoped_project("B Project", tenant_b, workspace_b, bob)

    client = TestClient(create_app(rt))
    auth = login(client)
    assert client.get(f"/product/projects/{project_a}/dashboard", headers=auth).status_code == 200
    assert client.get(f"/product/projects/{project_b}/dashboard", headers=auth).status_code == 404
    rt.close()


def test_domain_validation_api(tmp_path, monkeypatch):
    rt, _, _ = runtime(tmp_path, monkeypatch)
    client = TestClient(create_app(rt))
    auth = login(client)
    yaml_text = DomainSDK.scaffold("api.example")
    res = client.post("/product/domains/validate", headers=auth, json={"yaml_text": yaml_text})
    assert res.status_code == 200
    assert res.json()["ok"] is True
    rt.close()
