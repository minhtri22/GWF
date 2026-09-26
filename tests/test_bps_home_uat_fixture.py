from __future__ import annotations

import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient

from gwr.auth import HumanAuthService


ROOT = Path(__file__).parents[1]
FIXTURE_PATH = ROOT / "scripts" / "bps_home_uat_fixture.py"


def load_fixture_module():
    spec = importlib.util.spec_from_file_location("bps_home_uat_fixture", FIXTURE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_home_uat_data_fixture_exposes_authoritative_nonempty_states(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    fixture = load_fixture_module()
    app, rt = fixture.build_fixture("data", tmp_path / "data")
    try:
        with TestClient(app) as client:
            login = client.post(
                "/browser/auth/login",
                json={"username": fixture.USERNAME, "password": fixture.PASSWORD},
            )
            assert login.status_code == 200

            summary = client.get("/browser/home-summary")
            assert summary.status_code == 200
            body = summary.json()

            assert body["query_status"] == "COMPLETE"
            assert body["kpis"]["total_projects"] == 2
            assert body["kpis"]["lifecycle_active"] == 1
            assert body["kpis"]["executing_now"] == 1
            assert body["kpis"]["running_runs"] == 1
            assert body["kpis"]["pending_approvals"] == 1
            assert body["kpis"]["attention_required"] == 2

            assert len(body["executing_projects"]) == 1
            assert body["executing_projects"][0]["project_id"] == "project_home_uat_1"
            assert body["executing_projects"][0]["execution_activity"] == "EXECUTING"

            assert len(body["live_runs"]) == 1
            assert body["live_runs"][0]["run_id"] == "run_home_uat_1"
            assert body["live_runs"][0]["status"] == "RUNNING"

            assert {item["kind"] for item in body["attention"]} == {
                "PENDING_APPROVAL",
                "FAILURE",
            }
            assert body["recent_activity"]

            # Fresh-session refresh discriminator: the cookie must remain valid
            # across repeated HomeSummary reads well inside the 15-minute TTL.
            for _ in range(3):
                assert client.get("/browser/home-summary").status_code == 200
    finally:
        rt.close()


def test_home_uat_error_fixture_preserves_shell_and_forces_home_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    fixture = load_fixture_module()
    app, rt = fixture.build_fixture("error", tmp_path / "error")
    try:
        with TestClient(app) as client:
            login = client.post(
                "/browser/auth/login",
                json={"username": fixture.USERNAME, "password": fixture.PASSWORD},
            )
            assert login.status_code == 200
            assert client.get("/browser/bootstrap").json()["authenticated"] is True
            assert client.get("/app/home").status_code == 200

            response = client.get("/browser/home-summary")
            assert response.status_code == 503
            assert response.json()["detail"] == "HOME_UAT_CONTROLLED_UNAVAILABLE"
    finally:
        rt.close()
