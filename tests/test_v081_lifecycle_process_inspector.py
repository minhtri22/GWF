from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.domain_sdk import DomainSDK
from gwr.errors import InvalidTransition
from gwr.research_demo import DeterministicResearchExecutor
from gwr.research_orchestrator import ResearchOrchestrator
from gwr.runtime import GovernedWorkflowRuntime

ROOT = Path(__file__).parents[1]
ROLES = [
    "research_lead", "literature_reviewer", "protocol_designer", "experimenter",
    "analyst", "adversarial_reviewer", "reproducibility_reviewer",
]


def scoped_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1000)
    rt = GovernedWorkflowRuntime(str(ROOT / "domains" / "research.workflow.yaml"), str(tmp_path / "v081.db"), auth_secret="k" * 64)
    human = rt.governance.create_actor("HUMAN", "owner", ["human_approver"], [])
    rt.auth.register_human(human, "owner", "owner-password-long")
    tenant = rt.tenancy.create_tenant("Lab", human)
    workspace = rt.tenancy.create_workspace(tenant, "Research", human)
    return rt, human, tenant, workspace


def login(client):
    r = client.post("/auth/login", json={"username": "owner", "password": "owner-password-long"})
    assert r.status_code == 200
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def test_v081_migration_installs_lifecycle_tables(tmp_path):
    rt = GovernedWorkflowRuntime(str(ROOT / "domains" / "research.workflow.yaml"), str(tmp_path / "schema.db"))
    assert {"domain_packages", "domain_package_revisions", "project_domain_bindings"}.issubset(set(rt.db.list_tables()))
    assert "0004_v081_domain_project_lifecycle" in rt.db.migrations.status()["applied"]
    rt.close()


def test_domain_registry_revision_publish_and_immutable_project_pin(tmp_path, monkeypatch):
    rt, human, tenant, workspace = scoped_runtime(tmp_path, monkeypatch)
    package = rt.domains.create_package(tenant, "uat.lifecycle", "UAT Lifecycle", human)
    yaml_text = DomainSDK.scaffold("uat.lifecycle", display_name="UAT Lifecycle")
    revision = rt.domains.add_revision(package, yaml_text, human)
    assert rt.domains.get_revision(revision)["status"] == "VALIDATED"
    published = rt.domains.publish_revision(revision, human)
    assert published["status"] == "PUBLISHED"

    project = rt.create_scoped_project("Pinned Project", tenant, workspace, human, domain_revision_id=revision)
    binding = rt.domains.project_binding(project)
    assert binding["domain_revision_id"] == revision
    assert binding["domain_id"] == "uat.lifecycle"
    assert rt.db.one("SELECT domain_id FROM projects WHERE id=?", (project,))["domain_id"] == "uat.lifecycle"

    with pytest.raises(InvalidTransition):
        rt.domains.pin_project(project, revision, human)
    rt.close()


def test_invalid_domain_cannot_publish(tmp_path, monkeypatch):
    rt, human, tenant, _ = scoped_runtime(tmp_path, monkeypatch)
    package = rt.domains.create_package(tenant, "bad.lifecycle", "Bad Lifecycle", human)
    invalid = "domain_id: bad.lifecycle\nversion: 0.1.0\n"
    revision = rt.domains.add_revision(package, invalid, human)
    assert rt.domains.get_revision(revision)["status"] == "DRAFT"
    with pytest.raises(InvalidTransition):
        rt.domains.publish_revision(revision, human)
    rt.close()


def test_domain_and_project_lifecycle_api(tmp_path, monkeypatch):
    rt, _, tenant, workspace = scoped_runtime(tmp_path, monkeypatch)
    client = TestClient(create_app(rt))
    auth = login(client)

    p = client.post(f"/product/tenants/{tenant}/domains", headers=auth, json={"domain_id": "api.lifecycle", "name": "API Lifecycle"})
    assert p.status_code == 200
    package = p.json()["package_id"]
    yaml_text = DomainSDK.scaffold("api.lifecycle")
    r = client.post(f"/product/domains/{package}/revisions", headers=auth, json={"yaml_text": yaml_text})
    assert r.status_code == 200
    revision = r.json()["revision_id"]
    assert client.post(f"/product/domain-revisions/{revision}/validate", headers=auth).json()["ok"] is True
    assert client.post(f"/product/domain-revisions/{revision}/publish", headers=auth).json()["status"] == "PUBLISHED"

    created = client.post(
        f"/workspaces/{workspace}/projects", headers=auth,
        json={"name": "API Project", "domain_revision_id": revision},
    )
    assert created.status_code == 200
    assert created.json()["domain_binding"]["domain_revision_id"] == revision
    project = created.json()["project_id"]
    dashboard = client.get(f"/product/projects/{project}/dashboard", headers=auth)
    assert dashboard.status_code == 200
    assert dashboard.json()["domain_binding"]["domain_id"] == "api.lifecycle"
    rt.close()


def test_process_inspector_preserves_history_and_phase_detail(tmp_path):
    rt = GovernedWorkflowRuntime(str(ROOT / "domains" / "research.workflow.yaml"), str(tmp_path / "process.db"))
    project = rt.create_project("process")
    actors = {role: rt.governance.create_actor("AGENT", f"{role}-v081", [role], [project]) for role in ROLES}
    human = rt.governance.create_actor("HUMAN", "human-v081", ["human_approver"], [project])
    orch = ResearchOrchestrator(rt, actors, human_approver_id=human)
    result = orch.start(project, DeterministicResearchExecutor("runtime_retry"))
    assert result["status"] == "COMPLETED"

    process = rt.process.process(project)
    assert process["status"] == "COMPLETED"
    phases = process["orchestrations"][0]["phases"]
    main = [p for p in phases if p["phase_id"] == "phase_09_main_experiment"]
    assert len(main) == 2
    assert {p["status"] for p in main} >= {"FAILED", "SUCCEEDED"}

    failed = next(p for p in main if p["status"] == "FAILED")
    detail = rt.process.phase_detail(failed["phase_execution_id"])
    assert detail["run"]["runtime_status"] == "FAILED"
    assert detail["failure"]["failure_class"] == "runtime_timeout"
    events = detail["events"]
    assert any(e["event"] == "PHASE_STARTED" for e in events)
    assert any(e["event"] == "FAILURE_RECORDED" for e in events)
    assert events == sorted(events, key=lambda e: (e.get("timestamp") or "", e["event"], e["ref"] or ""))
    rt.close()


def test_process_api_exposes_history_and_phase_log(tmp_path, monkeypatch):
    rt, human, tenant, workspace = scoped_runtime(tmp_path, monkeypatch)
    project = rt.create_scoped_project("Process API", tenant, workspace, human)
    oid = "orch_api_1"
    peid = "phase_exec_api_1"
    rt.db.conn.execute(
        "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (oid, project, rt.domain.domain_id, "RUNNING", "phase_00_lock_goal", 0, None, 0,
         "2026-09-18T00:00:00+00:00", "2026-09-18T00:00:01+00:00", None, "{}"),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_executions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (peid, oid, "phase_00_lock_goal", 0, 0, None, None, "RUNNING", None, None, None,
         "2026-09-18T00:00:00+00:00", None, "{}"),
    )
    rt.db.conn.commit()
    client = TestClient(create_app(rt))
    auth = login(client)
    process = client.get(f"/product/projects/{project}/process", headers=auth)
    assert process.status_code == 200
    assert process.json()["current_phase"]["phase_execution_id"] == peid
    detail = client.get(f"/product/phases/{peid}", headers=auth)
    assert detail.status_code == 200
    assert detail.json()["phase"]["phase_id"] == "phase_00_lock_goal"
    ev = client.get(f"/product/phases/{peid}/events", headers=auth)
    assert ev.status_code == 200
    assert ev.json()["events"][0]["event"] == "PHASE_STARTED"
    rt.close()
