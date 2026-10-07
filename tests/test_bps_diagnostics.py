from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import canonical_json


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"
PASSWORD = "diagnostics-password-long"


def make_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "example.workflow.yaml"),
        str(tmp_path / "diagnostics.db"),
        auth_secret="d" * 64,
        object_store_root=tmp_path / "objects",
        observability_path=tmp_path / "events.jsonl",
    )
    actor = rt.governance.create_actor("HUMAN", "diagnostics-user", [], [])
    outsider = rt.governance.create_actor("HUMAN", "diagnostics-outsider", [], [])
    rt.auth.register_human(actor, "diagnostics-user", PASSWORD)

    tenant = rt.tenancy.create_tenant(
        "Diagnostics Tenant", actor, tenant_id="tenant_diagnostics"
    )
    workspace = rt.tenancy.create_workspace(
        tenant,
        "Diagnostics Workspace",
        actor,
        workspace_id="workspace_diagnostics",
    )
    project = rt.create_scoped_project(
        "Diagnostics Project",
        tenant,
        workspace,
        actor,
        project_id="project_diagnostics",
    )

    hidden_tenant = rt.tenancy.create_tenant(
        "Hidden Diagnostics Tenant",
        outsider,
        tenant_id="tenant_diagnostics_hidden",
    )
    hidden_workspace = rt.tenancy.create_workspace(
        hidden_tenant,
        "Hidden Diagnostics Workspace",
        outsider,
        workspace_id="workspace_diagnostics_hidden",
    )
    hidden_project = rt.create_scoped_project(
        "Hidden Diagnostics Project",
        hidden_tenant,
        hidden_workspace,
        outsider,
        project_id="project_diagnostics_hidden",
    )

    rt.observer.emit("diagnostics_fixture_ready", project_id=project)
    rt.db.conn.execute(
        "INSERT INTO provider_events VALUES(?,?,?,?,?,?,?,?,?)",
        (
            "provev_visible",
            project,
            "provider-visible",
            "search",
            "SUCCESS",
            12,
            None,
            canonical_json({"private": "not projected"}),
            "2026-10-05T02:00:00+00:00",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO provider_events VALUES(?,?,?,?,?,?,?,?,?)",
        (
            "provev_hidden",
            hidden_project,
            "provider-hidden",
            "search",
            "FAILED",
            20,
            "HIDDEN_ERROR",
            canonical_json({"secret": "must not leak"}),
            "2026-10-05T02:01:00+00:00",
        ),
    )
    rt.db.conn.commit()
    return rt, project, hidden_project


def app_for(rt):
    return create_app(
        rt,
        product_info={
            "product": "Governed Workflow Runtime",
            "version": "diagnostics-test",
            "build_sha": "diagnostics-build-sha",
            "domain_id": rt.domain.domain_id,
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "server_mode": "canonical",
        },
        web_root=WEB,
    )


def login(client):
    response = client.post(
        "/browser/auth/login",
        json={"username": "diagnostics-user", "password": PASSWORD},
    )
    assert response.status_code == 200


def assert_no_secret_fields(value):
    forbidden = {
        "token",
        "access_token",
        "refresh_token",
        "password",
        "secret",
        "client_secret",
        "private_key",
        "authorization",
        "lease_token",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            assert str(key).lower() not in forbidden
            assert_no_secret_fields(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_secret_fields(child)


def test_browser_diagnostics_is_authorized_exact_and_scoped(tmp_path, monkeypatch):
    rt, project, hidden_project = make_runtime(tmp_path, monkeypatch)
    client = TestClient(app_for(rt))

    assert client.get("/browser/diagnostics").status_code == 401
    login(client)
    response = client.get("/browser/diagnostics")
    assert response.status_code == 200
    body = response.json()

    assert body["build_sha"] == "diagnostics-build-sha"
    assert body["query_status"] == "COMPLETE"
    assert body["server"]["started_at"]
    assert isinstance(body["server"]["uptime_seconds"], int)
    assert body["server"]["uptime_seconds"] >= 0
    assert body["product"]["version"] == "diagnostics-test"
    assert body["product"]["server_mode"] == "canonical"

    assert body["readiness"]["ok"] is True
    assert body["readiness"]["core_health"] == "HEALTHY"
    assert body["database"]["probe"] == "PASS"

    status = body["migrations"]["status"]
    assert status["pending"] == []
    assert status["known"]
    revisions = body["migrations"]["revisions"]
    assert revisions
    assert all(item["applied"] is True for item in revisions)
    assert all(item["checksum_matches"] is True for item in revisions)
    assert all(item["expected_checksum"] for item in revisions)
    assert all(item["stored_checksum"] for item in revisions)

    assert body["object_store"]["configured"] is True
    assert body["object_store"]["probe"] == "PASS"
    assert body["object_store"]["type"] == "LocalContentAddressedStore"

    observer = body["observability"]
    assert observer["type"] == "JsonlObserver"
    assert observer["sink"] == "JSONL"
    assert observer["probe"] == "PASS"
    assert observer["latest_event"]["event"] == "diagnostics_fixture_ready"
    assert "events" in observer["metric_keys"]
    assert "by_event" in observer["metric_keys"]

    assert [item["provider_event_id"] for item in body["provider_events"]] == [
        "provev_visible"
    ]
    assert body["provider_events"][0]["project_id"] == project
    assert hidden_project not in str(body)
    assert "provider-hidden" not in str(body)
    assert "HIDDEN_ERROR" not in str(body)
    assert "not projected" not in str(body)

    assert body["github"]["connections"] == 0
    assert body["github"]["bindings"] == 0
    assert body["github"]["attached"] == 0
    assert body["github"]["query_status"] == "COMPLETE"

    capabilities = {item["id"]: item for item in body["capabilities"]}
    assert capabilities["diagnostics"]["state"] == "LIVE_FOUNDATION"
    assert capabilities["github"]["state"] == "LIVE_MODULE"
    assert_no_secret_fields(body)
    rt.close()


def test_diagnostics_browser_ui_consumes_authoritative_projection():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")
    css = (WEB / "styles.css").read_text(encoding="utf-8")

    for element_id in (
        "diagnosticsStateBanner",
        "diagnosticsMigrationList",
        "diagnosticsFoundationServices",
        "diagnosticsGithubStatus",
        "diagnosticsProviderBody",
    ):
        assert f'id="{element_id}"' in html

    assert 'api("/browser/diagnostics")' in js
    assert "renderDiagnosticsSummary" in js
    assert 'diagnosticsValue("Server uptime"' in js
    assert "server.uptime_seconds" in js
    assert "readiness.core_health" in js
    assert "health.github || {}" in js
    assert "health.migrations?.status || {}" in js
    assert "health.migrations?.revisions || []" in js
    assert "health.github_adapter" not in js
    assert "health.runtime?." not in js
    assert "refreshDiagnostics" in js
    assert "Migration status unavailable" in js
    assert "System / GitHub is separate from core health" in js
    assert "No provider attempts are recorded in the current authorized scope." in js

    # UAT U16 regression: Diagnostics rows are label/value/detail rows, not the
    # shared icon/name/action status-row geometry.
    for selector in (
        "#diagnosticsMigrationList .status-row",
        "#diagnosticsFoundationServices .status-row",
        "#diagnosticsGithubStatus .status-row",
    ):
        assert selector in css
    assert "grid-template-columns:minmax(150px,1fr) minmax(88px,max-content) minmax(0,1.45fr)" in css
    assert "overflow-wrap:anywhere" in css
    assert "word-break:break-word" in css


def test_u16_visual_repair_is_bounded_in_final_uat_runner():
    uat = (ROOT / "scripts" / "uiux" / "bps_current_surface_uat.ps1").read_text(
        encoding="utf-8"
    )
    assert '$U16VisualRepairHead = "277dd6c32f10563ebaafca9618b3c479fcea8d41"' in uat
    assert '$drift[0] -eq "web/styles.css"' in uat
    assert "$postRepairDrift.Count -eq 0" in uat
    assert 'bounded_u16_repair=$boundedU16Repair' in uat


def test_diagnostics_route_is_registered_once():
    api_source = (ROOT / "src" / "gwr" / "api.py").read_text(encoding="utf-8")
    assert api_source.count("@app.get('/browser/diagnostics')") == 1
    assert api_source.count("def browser_diagnostics") == 1
