from __future__ import annotations

import argparse
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


USERNAME = "projects-uat"
PASSWORD = "projects-uat-password"


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


def _seed_projects(rt: GovernedWorkflowRuntime, actor: str) -> None:
    tenant_id = rt.tenancy.create_tenant(
        "Projects UAT Tenant", actor, tenant_id="tenant_projects_uat"
    )
    workspace_id = rt.tenancy.create_workspace(
        tenant_id,
        "Projects UAT Workspace",
        actor,
        workspace_id="workspace_projects_uat",
    )

    executing = rt.create_scoped_project(
        "Executing Project",
        tenant_id,
        workspace_id,
        actor,
        project_id="project_uat_executing",
    )
    paused = rt.create_scoped_project(
        "Paused Project",
        tenant_id,
        workspace_id,
        actor,
        project_id="project_uat_paused",
    )
    queued = rt.create_scoped_project(
        "Queued Project",
        tenant_id,
        workspace_id,
        actor,
        project_id="project_uat_queued",
    )
    archived = rt.create_scoped_project(
        "Archived Project",
        tenant_id,
        workspace_id,
        actor,
        project_id="project_uat_archived",
    )
    rt.db.conn.execute(
        "UPDATE project_lifecycle SET status='ARCHIVED' WHERE project_id=?",
        (archived,),
    )

    package_id = rt.domains.create_package(
        tenant_id, rt.domain.domain_id, "Pinned UAT Domain", actor
    )
    revision_id = rt.domains.add_revision(
        package_id,
        (ROOT / "domains" / "example.workflow.yaml").read_text(encoding="utf-8"),
        actor,
    )
    rt.domains.publish_revision(revision_id, actor)
    rt.domains.pin_project(executing, revision_id, actor)

    rt.db.conn.execute(
        "INSERT INTO workunits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "wu_projects_uat_executing", executing, "ANALYZE",
            "[]", "[]", "[]", "[]", "[]",
            "{}", "{}", "{}", "{}", "[]", "RUNNING", 0,
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO runs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "run_projects_uat_executing",
            "wu_projects_uat_executing",
            1,
            actor,
            "[]",
            "2026-09-25T10:00:00+00:00",
            None,
            "RUNNING",
            None,
            "[]",
            "[]",
            None,
            "corr-projects-uat",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "orch_projects_uat_executing",
            executing,
            rt.domain.domain_id,
            "RUNNING",
            "phase-alpha",
            0,
            None,
            0,
            "2026-09-25T10:00:00+00:00",
            "2026-09-25T10:00:00+00:00",
            None,
            "{}",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "orch_projects_uat_paused",
            paused,
            rt.domain.domain_id,
            "PAUSED",
            "phase-beta",
            0,
            None,
            0,
            "2026-09-25T10:01:00+00:00",
            "2026-09-25T10:01:00+00:00",
            None,
            "{}",
        ),
    )

    rt.db.conn.execute(
        "INSERT INTO workunits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "wu_projects_uat_queued", queued, "ANALYZE",
            "[]", "[]", "[]", "[]", "[]",
            "{}", "{}", "{}", "{}", "[]", "READY", 0,
        ),
    )
    rt.db.conn.commit()
    rt.distributed.enqueue_workunit(
        "wu_projects_uat_queued",
        idempotency_key="projects-uat-queued",
    )

    rt.db.conn.execute(
        "INSERT INTO proposals VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            "proposal_projects_uat",
            executing,
            actor,
            "APPROVE_TEST",
            "[]",
            "{}",
            "hash-projects-uat",
            None,
            "PENDING_APPROVAL",
            "2026-09-25T10:02:00+00:00",
            "idem-projects-uat",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO failures VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "failure_projects_uat",
            executing,
            "wu_projects_uat_executing",
            "PROJECTS_UAT_FAILURE",
            "EXECUTION",
            "run_projects_uat_executing",
            None,
            None,
            "[]",
            None,
            None,
            "UNRESOLVED",
            None,
            "HIGH",
            "sig-projects-uat",
            "OPEN",
            "2026-09-25T10:03:00+00:00",
            None,
        ),
    )
    rt.governance.append_audit(
        executing,
        actor,
        "RUN_STARTED",
        "ExecutionRun",
        "run_projects_uat_executing",
        run_id="run_projects_uat_executing",
    )
    rt.db.conn.commit()

    outsider = rt.governance.create_actor("HUMAN", "projects-uat-outsider", [], [])
    hidden_tenant = rt.tenancy.create_tenant(
        "Hidden Tenant", outsider, tenant_id="tenant_projects_uat_hidden"
    )
    hidden_workspace = rt.tenancy.create_workspace(
        hidden_tenant,
        "Hidden Workspace",
        outsider,
        workspace_id="workspace_projects_uat_hidden",
    )
    rt.create_scoped_project(
        "Hidden Project",
        hidden_tenant,
        hidden_workspace,
        outsider,
        project_id="project_uat_hidden",
    )


def build_fixture(mode: str, runtime_root: Path):
    if mode not in {"data", "error"}:
        raise ValueError("mode must be 'data' or 'error'")

    runtime_root.mkdir(parents=True, exist_ok=True)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "example.workflow.yaml"),
        str(runtime_root / "projects-uat.db"),
        auth_secret="projects-uat-auth-secret-0123456789abcdef",
        object_store_root=str(runtime_root / "objects"),
        observability_path=str(runtime_root / "events.jsonl"),
    )
    actor = rt.governance.create_actor("HUMAN", USERNAME, [], [])
    rt.auth.register_human(actor, USERNAME, PASSWORD)

    if mode == "data":
        _seed_projects(rt, actor)

    app = create_app(
        rt,
        product_info={
            "product": "Governed Workflow Runtime",
            "version": "projects-uat-fixture",
            "build_sha": _git_head(),
            "domain_id": rt.domain.domain_id,
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "server_mode": "PROJECTS_UAT_FIXTURE",
        },
        web_root=ROOT / "web",
        browser_cookie_secure=False,
    )

    if mode == "error":
        @app.middleware("http")
        async def controlled_projects_unavailable(request, call_next):
            if request.url.path == "/browser/projects-index":
                return JSONResponse(
                    status_code=503,
                    content={
                        "detail": "PROJECTS_UAT_CONTROLLED_UNAVAILABLE",
                        "fixture": True,
                    },
                )
            return await call_next(request)

    return app, rt


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Isolated browser fixture for Projects index UAT."
    )
    parser.add_argument("--mode", choices=("data", "error"), default="data")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8878)
    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit("uvicorn is required; run the repository install first") from exc

    with tempfile.TemporaryDirectory(prefix="gwf-projects-uat-") as temp_dir:
        runtime_root = Path(temp_dir)
        app, rt = build_fixture(args.mode, runtime_root)
        print()
        print("GWF PROJECTS UAT FIXTURE")
        print("========================")
        print(f"mode       = {args.mode}")
        print(f"head       = {_git_head()}")
        print(f"browser_url= http://localhost:{args.port}/app/projects")
        print(f"bind_url   = http://{args.host}:{args.port}/app/projects")
        print(f"username   = {USERNAME}")
        print(f"password   = {PASSWORD}")
        print(f"runtime    = {runtime_root}")
        print("cookie host= localhost (isolated from 127.0.0.1 sessions)")
        print("working DB = NOT USED")
        print()
        if args.mode == "data":
            print("Expected authorized rows: Executing, Paused, Queued, Archived.")
            print("Hidden Project must not appear.")
        else:
            print("Expected state: Projects data unavailable; never fake zero.")
        print()
        print("Stop with Ctrl+C. Temporary data is deleted on exit.")
        print()
        try:
            uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
        finally:
            rt.close()


if __name__ == "__main__":
    main()
