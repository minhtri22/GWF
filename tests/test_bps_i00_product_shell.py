from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

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
    monkeypatch.delenv("GWR_TEST_DATABASE_URL", raising=False)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "example.workflow.yaml"),
        str(tmp_path / "bps_i00.db"),
        auth_secret="i" * 64,
        object_store_root=tmp_path / "objects",
        observability_path=tmp_path / "events.jsonl",
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
    assert body["product"]["backend"] == getattr(rt.db, "backend_name", "unknown")
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
    assert ready.json()["checks"] == {
        "database": "PASS",
        "migrations": "PASS",
        "object_store": "PASS",
        "observability": "PASS",
    }
    rt.close()




def test_i00_ready_degrades_when_object_store_verification_fails(tmp_path, monkeypatch):
    rt, _ = make_runtime(tmp_path, monkeypatch)
    client = TestClient(app_for(rt))
    monkeypatch.setattr(rt.object_store, "verify", lambda _sha: False)

    ready = client.get("/ready")
    assert ready.status_code == 503
    body = ready.json()
    assert body["ok"] is False
    assert body["core_health"] == "DEGRADED"
    assert body["reason"] == "object_store_probe_failed"
    assert body["checks"]["database"] == "PASS"
    assert body["checks"]["migrations"] == "PASS"
    assert body["checks"]["object_store"] == "FAIL"
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
    assert 'const enabled = item.state === "LIVE_FOUNDATION";' in js


def test_i00_server_config_fails_closed_without_auth_secret(tmp_path, monkeypatch):
    monkeypatch.delenv("GWR_AUTH_SECRET", raising=False)
    monkeypatch.delenv("GWR_DOMAIN_PATH", raising=False)
    monkeypatch.delenv("GWR_WEB_ROOT", raising=False)
    with pytest.raises(ServerConfigError, match="GWR_AUTH_SECRET"):
        ServerConfig.from_env(repo_root=ROOT)


def test_i00_canonical_server_builds_real_runtime_with_bootstrap_login(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    monkeypatch.delenv("GWR_TEST_DATABASE_URL", raising=False)
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
        expected_backend = "postgresql" if os.environ.get("GWR_TEST_DATABASE_URL") else "sqlite"
        assert info["backend"] == expected_backend


def test_i00_windows_launcher_and_installer_contracts_are_explicit():
    launcher = (ROOT / "scripts" / "gwf_server.ps1").read_text(encoding="utf-8")
    installer = (ROOT / "install.ps1").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'ValidateSet("start","stop","restart","status","foreground")' in launcher
    assert "process_started_at" in launcher
    assert r"gwr\.server" in launcher
    assert "GWR_AUTH_SECRET must be set to at least 32 bytes" in launcher
    assert "uvicorn>=0.30,<1" in pyproject
    assert 'gwr-server = "gwr.server:main"' in pyproject

    assert "[switch]$Qualification" in installer
    assert "$QualificationMode" in installer
    assert 'mode = if ($QualificationMode) { "QUALIFICATION" } else { "INSTALL" }' in installer
    assert "timings_seconds = $Timings" in installer
    assert 'if ($QualificationMode -and -not $SkipTests)' in installer
    assert 'if ($QualificationMode -and -not $SkipUat)' in installer


def test_i00_canonical_server_subprocess_reaches_ready(tmp_path):
    env = os.environ.copy()
    env.update({
        "GWR_AUTH_SECRET": "subprocess-server-secret-0123456789abcdef",
        "GWR_DATABASE_URL": str(tmp_path / "server-subprocess.db"),
        "GWR_OBJECT_STORE_ROOT": str(tmp_path / "objects"),
        "GWR_OBSERVABILITY_PATH": str(tmp_path / "events.jsonl"),
    })
    env.pop("GWR_TEST_DATABASE_URL", None)

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "gwr.server",
            "--repo-root",
            str(ROOT),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 20
        ready = None
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                raise AssertionError(f"canonical server exited early with code {proc.returncode}")
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/ready", timeout=1) as response:
                    ready = json.loads(response.read().decode("utf-8"))
                if ready.get("ok") is True:
                    break
            except Exception:
                time.sleep(0.2)
        assert ready is not None and ready["ok"] is True
        assert ready["core_health"] == "HEALTHY"
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)


@pytest.mark.skipif(sys.platform != "win32", reason="PowerShell ownership guard is Windows-only")
def test_i00_windows_launcher_refuses_to_stop_or_restart_unrelated_process(tmp_path):
    launcher = ROOT / "scripts" / "gwf_server.ps1"
    repo_root = tmp_path / "launcher-root"
    state_dir = repo_root / ".gwr" / "server"
    state_dir.mkdir(parents=True)

    unrelated = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        metadata = {
            "schema": "GWF-SERVER-PROCESS-v1",
            "pid": unrelated.pid,
            "process_started_at": datetime.now(timezone.utc).isoformat(),
            "repo_root": str(repo_root),
            "git_head": "test",
            "host": "127.0.0.1",
            "port": 8765,
            "stdout": str(state_dir / "server.stdout.log"),
            "stderr": str(state_dir / "server.stderr.log"),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
        pid_path = state_dir / "server-process.json"
        pid_path.write_text(json.dumps(metadata), encoding="utf-8")

        base = [
            "pwsh",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(launcher),
            "-RepoRoot",
            str(repo_root),
        ]

        for action in ("stop", "restart"):
            result = subprocess.run(
                base + ["-Action", action],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=15,
            )
            assert result.returncode != 0
            assert "Refusing to operate" in result.stdout
            assert unrelated.poll() is None
            pid_path.write_text(json.dumps(metadata), encoding="utf-8")
    finally:
        if unrelated.poll() is None:
            unrelated.terminate()
            unrelated.wait(timeout=10)

