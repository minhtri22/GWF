from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gwr.auth import HumanAuthService
from gwr.errors import AuthorityDenied
from gwr.api import create_app
from gwr.runtime import GovernedWorkflowRuntime
from gwr.server import ServerConfig, ServerConfigError, build_application


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"


def make_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "example.workflow.yaml"),
        str(tmp_path / "bps_i00.db"),
        auth_secret="i" * 64,
    )
    actor = rt.governance.create_actor("HUMAN", "operator", [], [])
    rt.auth.register_human(actor, "operator", "operator-password-long")
    return rt, actor


def app_for(rt):
    return create_app(
        rt,
        product_info={
            "product": "Governed Workflow Runtime",
            "version": "test-version",
            "build_sha": "abc123",
            "domain_id": rt.domain.domain_id,
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "server_mode": "canonical",
        },
        web_root=WEB,
    )


def test_i00_live_shell_and_bootstrap_are_authoritative(tmp_path, monkeypatch):
    rt, _ = make_runtime(tmp_path, monkeypatch)
    client = TestClient(app_for(rt))

    shell = client.get("/app")
    assert shell.status_code == 200
    assert "Governed Knowledge Studio" in shell.text
    assert "Static UAT mode" not in shell.text

    bootstrap = client.get("/browser/bootstrap")
    assert bootstrap.status_code == 200
    body = bootstrap.json()
    assert body["authenticated"] is False
    assert body["product"]["build_sha"] == "abc123"
    assert body["product"]["backend"] == "sqlite"
    assert body["shell_authority"] == "BPS-I00"

    capabilities = {x["id"]: x for x in body["capabilities"]}
    assert capabilities["home"]["state"] == "LOCKED"
    assert capabilities["projects"]["state"] == "LOCKED"
    assert capabilities["shared-library"]["state"] == "PLANNED_BLOCKED"
    assert capabilities["reference-acquisition"]["state"] == "PLANNED_BLOCKED"
    assert capabilities["agents"]["state"] == "PLANNED_BLOCKED"
    assert capabilities["diagnostics"]["state"] == "LIVE_FOUNDATION"

    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["ok"] is True
    assert ready.json()["core_health"] == "HEALTHY"
    assert ready.json()["build_sha"] == "abc123"
    rt.close()


def test_i00_browser_session_uses_httponly_cookie_and_revocation(tmp_path, monkeypatch):
    rt, actor = make_runtime(tmp_path, monkeypatch)
    client = TestClient(app_for(rt))

    login = client.post(
        "/browser/auth/login",
        json={"username": "operator", "password": "operator-password-long"},
    )
    assert login.status_code == 200
    assert login.json()["actor_id"] == actor
    assert "access_token" not in login.json()
    set_cookie = login.headers["set-cookie"].lower()
    assert "gwr_browser_session=" in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=strict" in set_cookie

    raw_token = client.cookies.get("gwr_browser_session")
    assert raw_token
    me = client.get("/browser/auth/me")
    assert me.status_code == 200
    assert me.json()["actor_id"] == actor
    assert client.get("/browser/bootstrap").json()["authenticated"] is True

    logout = client.post("/browser/auth/logout")
    assert logout.status_code == 200
    with pytest.raises(AuthorityDenied):
        rt.auth.verify(raw_token)
    assert client.get("/browser/auth/me").status_code == 401
    rt.close()


def test_i00_existing_bearer_api_remains_valid(tmp_path, monkeypatch):
    rt, actor = make_runtime(tmp_path, monkeypatch)
    client = TestClient(app_for(rt))
    token = client.post(
        "/auth/login",
        json={"username": "operator", "password": "operator-password-long"},
    ).json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["actor_id"] == actor
    rt.close()


def test_i00_shell_javascript_contains_only_presentation_local_storage():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert 'const THEME_KEY = "gwr-ui-theme"' in js
    assert 'const SIDEBAR_KEY = "gwr-ui-sidebar"' in js
    assert "gwr-uat-domains" not in js
    assert "demo-data.json" not in js
    assert "access_token" not in js
    assert "localStorage.setItem(THEME_KEY" in js
    assert "localStorage.setItem(SIDEBAR_KEY" in js


def test_i00_server_config_fails_closed_without_auth_secret(tmp_path, monkeypatch):
    monkeypatch.delenv("GWR_AUTH_SECRET", raising=False)
    monkeypatch.delenv("GWR_DOMAIN_PATH", raising=False)
    monkeypatch.delenv("GWR_WEB_ROOT", raising=False)
    with pytest.raises(ServerConfigError, match="GWR_AUTH_SECRET"):
        ServerConfig.from_env(repo_root=ROOT)


def test_i00_canonical_server_builds_real_runtime_with_bootstrap_login(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    config = ServerConfig(
        repo_root=ROOT,
        domain_path=ROOT / "domains" / "example.workflow.yaml",
        database_target=str(tmp_path / "server.db"),
        auth_secret="s" * 64,
        object_store_root=tmp_path / "objects",
        observability_path=tmp_path / "events.jsonl",
        web_root=WEB,
        host="127.0.0.1",
        port=8765,
        browser_cookie_secure=False,
        bootstrap_username="bootstrap",
        bootstrap_password="bootstrap-password-long",
    )

    app = build_application(config)
    with TestClient(app) as client:
        login = client.post(
            "/browser/auth/login",
            json={"username": "bootstrap", "password": "bootstrap-password-long"},
        )
        assert login.status_code == 200
        assert client.get("/ready").json()["ok"] is True
        info = client.get("/product/meta").json()
        assert info["server_mode"] == "canonical"
        assert info["backend"] == "sqlite"


def test_i00_windows_launcher_and_installer_contracts_are_explicit():
    launcher = (ROOT / "scripts" / "gwf_server.ps1").read_text(encoding="utf-8")
    installer = (ROOT / "install.ps1").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'ValidateSet("start","stop","restart","status","foreground")' in launcher
    assert "process_started_at" in launcher
    assert "gwr\.server" in launcher
    assert "GWR_AUTH_SECRET must be set to at least 32 bytes" in launcher
    assert "uvicorn>=0.30,<1" in pyproject
    assert 'gwr-server = "gwr.server:main"' in pyproject

    assert "[switch]$Qualification" in installer
    assert "$QualificationMode" in installer
    assert 'mode = if ($QualificationMode) { "QUALIFICATION" } else { "INSTALL" }' in installer
    assert "timings_seconds = $Timings" in installer
    assert 'if ($QualificationMode -and -not $SkipTests)' in installer
    assert 'if ($QualificationMode -and -not $SkipUat)' in installer
