from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastapi.responses import JSONResponse

from gwr.api import create_app
from gwr.runtime import GovernedWorkflowRuntime


USERNAME = "home-uat"
PASSWORD = "home-uat-password"


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def _seed_authoritative_home_data(rt: GovernedWorkflowRuntime, actor: str) -> None:
    tenant_id = rt.tenancy.create_tenant("Home UAT Tenant", actor)
    workspace_id = rt.tenancy.create_workspace(tenant_id, "Home UAT Workspace", actor)

    project_id = rt.create_scoped_project(
        "Home UAT Executing Project",
        tenant_id,
        workspace_id,
        actor,
        project_id="project_home_uat_1",
    )
    archived_project_id = rt.create_scoped_project(
        "Home UAT Archived Project",
        tenant_id,
        workspace_id,
        actor,
        project_id="project_home_uat_2",
    )

    rt.db.conn.execute(
        "UPDATE project_lifecycle SET status='ARCHIVED' WHERE project_id=?",
        (archived_project_id,),
    )
    rt.db.conn.execute(
        "INSERT INTO workunits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "wu_home_uat_1",
            project_id,
            "ANALYZE",
            "[]",
            "[]",
            "[]",
            "[]",
            "[]",
            "{}",
            "{}",
            "{}",
            "{}",
            "[]",
            "RUNNING",
            0,
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO runs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "run_home_uat_1",
            "wu_home_uat_1",
            1,
            actor,
            "[]",
            "2026-09-24T07:00:00+00:00",
            None,
            "RUNNING",
            None,
            "[]",
            "[]",
            None,
            "corr-home-uat",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "orch_home_uat_1",
            project_id,
            rt.domain.domain_id,
            "RUNNING",
            "phase-alpha",
            0,
            None,
            0,
            "2026-09-24T07:00:00+00:00",
            "2026-09-24T07:00:00+00:00",
            None,
            "{}",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_executions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "phase_home_uat_1",
            "orch_home_uat_1",
            "phase-alpha",
            0,
            0,
            "wu_home_uat_1",
            "run_home_uat_1",
            "RUNNING",
            None,
            None,
            None,
            "2026-09-24T07:00:00+00:00",
            None,
            "{}",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO proposals VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            "proposal_home_uat_1",
            project_id,
            actor,
            "APPROVE_TEST",
            "[]",
            "{}",
            "hash-home-uat",
            None,
            "PENDING_APPROVAL",
            "2026-09-24T07:01:00+00:00",
            "idem-home-uat",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO failures VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "failure_home_uat_1",
            project_id,
            "wu_home_uat_1",
            "HOME_UAT_FAILURE",
            "EXECUTION",
            "run_home_uat_1",
            None,
            None,
            "[]",
            None,
            None,
            "UNRESOLVED",
            None,
            "HIGH",
            "sig-home-uat",
            "OPEN",
            "2026-09-24T07:02:00+00:00",
            None,
        ),
    )
    rt.governance.append_audit(
        project_id,
        actor,
        "RUN_STARTED",
        "ExecutionRun",
        "run_home_uat_1",
        run_id="run_home_uat_1",
    )
    rt.db.conn.commit()


def build_fixture(mode: str, runtime_root: Path):
    if mode not in {"data", "error"}:
        raise ValueError("mode must be 'data' or 'error'")

    runtime_root.mkdir(parents=True, exist_ok=True)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "example.workflow.yaml"),
        str(runtime_root / "home-uat.db"),
        auth_secret="home-uat-auth-secret-0123456789abcdef",
        object_store_root=str(runtime_root / "objects"),
        observability_path=str(runtime_root / "events.jsonl"),
    )

    actor = rt.governance.create_actor("HUMAN", USERNAME, [], [])
    rt.auth.register_human(actor, USERNAME, PASSWORD)

    if mode == "data":
        _seed_authoritative_home_data(rt, actor)

    app = create_app(
        rt,
        product_info={
            "product": "Governed Workflow Runtime",
            "version": "home-uat-fixture",
            "build_sha": _git_head(),
            "domain_id": rt.domain.domain_id,
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "server_mode": "HOME_UAT_FIXTURE",
        },
        web_root=ROOT / "web",
        browser_cookie_secure=False,
    )

    if mode == "error":
        @app.middleware("http")
        async def controlled_home_unavailable(request, call_next):
            if request.url.path == "/browser/home-summary":
                return JSONResponse(
                    status_code=503,
                    content={
                        "detail": "HOME_UAT_CONTROLLED_UNAVAILABLE",
                        "fixture": True,
                    },
                )
            return await call_next(request)

    return app, rt


def _print_banner(mode: str, host: str, port: int, runtime_root: Path) -> None:
    print()
    print("GWF HOME UAT FIXTURE")
    print("====================")
    print(f"mode       = {mode}")
    print(f"head       = {_git_head()}")
    print(f"url        = http://{host}:{port}/app/home")
    print(f"username   = {USERNAME}")
    print(f"password   = {PASSWORD}")
    print(f"runtime    = {runtime_root}")
    print("isolation  = EPHEMERAL TEMP DIRECTORY")
    print("working DB = NOT USED")
    print()
    if mode == "data":
        print("Use this mode for H-UAT-04/05/06/07 and H-UAT-08R.")
        print("Expected visible data: one executing project, one running run,")
        print("one pending approval, one unresolved failure, and recent activity.")
    else:
        print("Use this mode for H-UAT-09.")
        print("Expected Home state: controlled unavailable/error, not fake zero.")
    print()
    print("Stop with Ctrl+C. The temporary database is deleted on exit.")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Isolated browser fixture for the remaining Home screen UAT."
    )
    parser.add_argument("--mode", choices=("data", "error"), default="data")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8877)
    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit("uvicorn is required; run the repository install first") from exc

    with tempfile.TemporaryDirectory(prefix="gwf-home-uat-") as temp_dir:
        runtime_root = Path(temp_dir)
        app, rt = build_fixture(args.mode, runtime_root)
        _print_banner(args.mode, args.host, args.port, runtime_root)
        try:
            uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
        finally:
            rt.close()


if __name__ == "__main__":
    main()
