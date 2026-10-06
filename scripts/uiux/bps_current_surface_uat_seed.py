from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import canonical_json, utcnow


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"missing required environment variable: {name}")
    return value


def seed() -> dict[str, str]:
    username = require_env("GWR_UAT_USERNAME")
    password = require_env("GWR_UAT_PASSWORD")
    auth_secret = require_env("GWR_AUTH_SECRET")
    database_url = require_env("GWR_DATABASE_URL")
    object_store_root = require_env("GWR_OBJECT_STORE_ROOT")
    observability_path = require_env("GWR_OBSERVABILITY_PATH")

    domain_path = ROOT / "domains" / "research.workflow.yaml"
    rt = GovernedWorkflowRuntime(
        str(domain_path),
        database_url,
        auth_secret=auth_secret,
        object_store_root=object_store_root,
        observability_path=observability_path,
    )
    try:
        owner = rt.governance.create_actor(
            "HUMAN", username, ["human_approver"], ["current_surface_uat"]
        )
        agent = rt.governance.create_actor(
            "AGENT",
            "current-surface-uat-agent",
            ["research_lead", "operator"],
            ["current_surface_uat"],
        )
        outsider = rt.governance.create_actor(
            "HUMAN", "current-surface-hidden-actor", [], []
        )
        rt.auth.register_human(owner, username, password)

        tenant = rt.tenancy.create_tenant(
            "Current Surface UAT Tenant",
            owner,
            tenant_id="tenant_current_surface_uat",
        )
        workspace = rt.tenancy.create_workspace(
            tenant,
            "Current Surface UAT Workspace",
            owner,
            workspace_id="workspace_current_surface_uat",
        )

        package = rt.domains.create_package(
            tenant,
            rt.domain.domain_id,
            "Current Surface UAT Domain",
            owner,
        )
        revision = rt.domains.add_revision(
            package,
            domain_path.read_text(encoding="utf-8"),
            owner,
        )
        rt.domains.publish_revision(revision, owner)

        execution_project = rt.create_scoped_project(
            "Execution Project",
            tenant,
            workspace,
            owner,
            project_id="project_uat_execution",
            domain_revision_id=revision,
        )
        lifecycle_project = rt.create_scoped_project(
            "Lifecycle Project",
            tenant,
            workspace,
            owner,
            project_id="project_uat_lifecycle",
            domain_revision_id=revision,
        )
        recovery_project = rt.create_scoped_project(
            "Recovery Project",
            tenant,
            workspace,
            owner,
            project_id="project_uat_recovery",
            domain_revision_id=revision,
        )
        archived_project = rt.create_scoped_project(
            "Archived Project",
            tenant,
            workspace,
            owner,
            project_id="project_uat_archived",
        )
        rt.db.conn.execute(
            "UPDATE project_lifecycle SET status='ARCHIVED' WHERE project_id=?",
            (archived_project,),
        )
        rt.tenancy.add_project_member(
            execution_project, agent, "RESEARCHER", owner
        )
        rt.tenancy.add_project_member(
            recovery_project, agent, "RESEARCHER", owner
        )

        hidden_tenant = rt.tenancy.create_tenant(
            "Hidden UAT Tenant",
            outsider,
            tenant_id="tenant_current_surface_hidden",
        )
        hidden_workspace = rt.tenancy.create_workspace(
            hidden_tenant,
            "Hidden UAT Workspace",
            outsider,
            workspace_id="workspace_current_surface_hidden",
        )
        rt.create_scoped_project(
            "Hidden Project",
            hidden_tenant,
            hidden_workspace,
            outsider,
            project_id="project_uat_hidden",
        )

        # Rich persisted execution state for Home, Runs, Overview and Execution.
        rt.db.conn.execute(
            "INSERT INTO workunits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "wu_current_surface_execution",
                execution_project,
                "phase_09_main_experiment",
                canonical_json(["rev_uat_input"]),
                canonical_json([{"artifact_type": "REPORT"}]),
                canonical_json([{"kind": "VALID_INPUT"}]),
                canonical_json(["QUALITY_GATE"]),
                canonical_json(["EXECUTE"]),
                canonical_json({"role": "operator"}),
                canonical_json(
                    {
                        "resources": {"cpu": 1},
                        "required_capabilities": ["python"],
                    }
                ),
                canonical_json({"max_attempts": 2}),
                canonical_json({"mode": "HUMAN_APPROVE"}),
                canonical_json(["dataset:current-surface-uat"]),
                "RUNNING",
                1,
            ),
        )
        rt.db.conn.execute(
            "INSERT INTO runs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "run_current_surface_execution",
                "wu_current_surface_execution",
                1,
                agent,
                canonical_json(["rev_uat_input"]),
                "2026-10-06T01:00:00+00:00",
                None,
                "RUNNING",
                canonical_json({"worker_exit": "pending"}),
                canonical_json([]),
                canonical_json(["evidence_current_surface"]),
                None,
                "corr-current-surface-uat",
            ),
        )
        rt.db.conn.execute(
            "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "orch_current_surface_execution",
                execution_project,
                rt.domain.domain_id,
                "RUNNING",
                "phase_09_main_experiment",
                1,
                None,
                0,
                "2026-10-06T00:59:00+00:00",
                "2026-10-06T01:00:30+00:00",
                None,
                canonical_json({"fixture": "current_surface_uat"}),
            ),
        )
        rt.db.conn.execute(
            "INSERT INTO phase_executions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "phase_current_surface_execution",
                "orch_current_surface_execution",
                "phase_09_main_experiment",
                9,
                1,
                "wu_current_surface_execution",
                "run_current_surface_execution",
                "RUNNING",
                None,
                None,
                None,
                "2026-10-06T01:00:00+00:00",
                None,
                canonical_json({"fixture": "current_surface_uat"}),
            ),
        )
        rt.db.conn.execute(
            "INSERT INTO phase_stage_events VALUES(?,?,?,?,?,?,?,?)",
            (
                "phaseevt_current_surface_execution",
                "phase_current_surface_execution",
                "EXECUTE",
                "STEP_PROGRESS",
                agent,
                "Current Surface UAT execution is running",
                canonical_json({"fixture": True}),
                "2026-10-06T01:01:00+00:00",
            ),
        )
        rt.db.conn.execute(
            "INSERT INTO phase_handoffs VALUES(?,?,?,?,?,?,?)",
            (
                "handoff_current_surface_execution",
                "phase_current_surface_execution",
                canonical_json({"summary": "UAT handoff"}),
                "handoff-hash-current-surface",
                agent,
                "2026-10-06T01:02:00+00:00",
                "Current Surface UAT handoff",
            ),
        )
        rt.db.conn.execute(
            "INSERT INTO proposals VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                "proposal_current_surface_uat",
                execution_project,
                agent,
                "APPROVE_CURRENT_SURFACE_UAT",
                canonical_json(["rev_uat_input"]),
                canonical_json({"summary": "Approve the seeded UAT proposal"}),
                "payload-hash-current-surface-uat",
                None,
                "PENDING_APPROVAL",
                "2026-10-06T01:03:00+00:00",
                "idem-current-surface-uat",
            ),
        )
        rt.db.conn.execute(
            "INSERT INTO failures VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "failure_current_surface_uat",
                execution_project,
                "wu_current_surface_execution",
                "CURRENT_SURFACE_UAT_FAILURE",
                "VERIFY",
                "run_current_surface_execution",
                "rev_uat_input",
                None,
                canonical_json(["evidence_current_surface"]),
                "rev_uat_input",
                None,
                "UNRESOLVED",
                "phase_09_main_experiment",
                "HIGH",
                "sig-current-surface-uat",
                "OPEN",
                "2026-10-06T01:04:00+00:00",
                None,
            ),
        )
        rt.db.conn.execute(
            "INSERT INTO artifacts VALUES(?,?,?,?,?,?,?,?,?)",
            (
                "artifact_current_surface_uat",
                execution_project,
                "REPORT",
                "current-surface-uat-report",
                utcnow(),
                owner,
                "revision_current_surface_uat",
                "ACTIVE",
                1,
            ),
        )
        rt.db.conn.execute(
            "INSERT INTO revisions VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                "revision_current_surface_uat",
                "artifact_current_surface_uat",
                1,
                canonical_json({"summary": "authoritative UAT revision"}),
                "revision-hash-current-surface-uat",
                owner,
                utcnow(),
                None,
                "CURRENT",
                "VALID",
            ),
        )
        rt.governance.append_audit(
            execution_project,
            agent,
            "CURRENT_SURFACE_UAT_EXECUTION_STARTED",
            "ExecutionRun",
            "run_current_surface_execution",
            reason_code="UAT_FIXTURE",
            run_id="run_current_surface_execution",
        )
        rt.db.conn.commit()

        # Distributed runtime state for Operations / Runtime and Overview.
        rt.db.conn.execute(
            "INSERT INTO workunits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "wu_current_surface_queue",
                execution_project,
                "phase_10_qa",
                canonical_json([]),
                canonical_json([]),
                canonical_json([]),
                canonical_json([]),
                canonical_json(["VERIFY"]),
                canonical_json({"role": "operator"}),
                canonical_json(
                    {
                        "resources": {"cpu": 1, "memory_mb": 256},
                        "required_capabilities": ["python"],
                    }
                ),
                canonical_json({"max_attempts": 1}),
                canonical_json({"mode": "AUTO"}),
                canonical_json(["dataset:current-surface-uat"]),
                "READY",
                0,
            ),
        )
        rt.db.conn.commit()
        rt.distributed.enqueue_workunit(
            "wu_current_surface_queue",
            idempotency_key="current-surface-uat-job",
            required_resources={"cpu": 1, "memory_mb": 256},
            required_capabilities=["python"],
        )

        # GitHub M07-A read data. No adapter is attached, so readiness remains
        # truthfully NOT_ATTACHED while binding/change-set state is inspectable.
        connection = rt.plugins.create_connection(
            execution_project,
            "github",
            "opaque-current-surface-uat",
            ["REPO_READ", "CONTENT_WRITE"],
            owner,
            metadata={"label": "Current Surface UAT", "purpose": "UAT"},
        )
        binding = rt.github.bind_repository(
            execution_project,
            connection,
            "minhtri22/GWF",
            "main",
            owner,
            allowed_branches=["feature/*", "docs/*"],
        )
        change_set = rt.github.prepare_change_set(
            execution_project,
            binding,
            "feature/current-surface-uat",
            "a" * 40,
            [
                {
                    "path": "docs/current-surface-uat-placeholder.md",
                    "operation": "CREATE",
                    "content": "Current Surface UAT fixture only.",
                }
            ],
            "Current Surface UAT prepared change set",
            owner,
        )

        # Agent protocol state with one true WAITING_HUMAN recovery decision.
        rt.db.conn.execute(
            "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "orch_current_surface_recovery",
                recovery_project,
                rt.domain.domain_id,
                "RUNNING",
                "phase_09_main_experiment",
                0,
                None,
                0,
                "2026-10-06T01:10:00+00:00",
                "2026-10-06T01:10:00+00:00",
                None,
                canonical_json({"fixture": "current_surface_recovery"}),
            ),
        )
        rt.db.conn.execute(
            "INSERT INTO phase_executions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "phase_current_surface_recovery",
                "orch_current_surface_recovery",
                "phase_09_main_experiment",
                9,
                0,
                None,
                None,
                "RUNNING",
                None,
                None,
                None,
                "2026-10-06T01:10:01+00:00",
                None,
                canonical_json({"fixture": "current_surface_recovery"}),
            ),
        )
        rt.db.conn.commit()

        skill_package = rt.agent_protocol.create_skill_package(
            "current-surface-uat-skill",
            "Current Surface UAT Skill",
            agent,
        )
        skill_revision = rt.agent_protocol.add_skill_revision(
            skill_package,
            "1.0.0",
            "# Current Surface UAT\nExecute, verify, recover, handoff.",
            agent,
            tool_requirements=["python"],
            qa_contract={"requires_evidence": True},
        )
        rt.agent_protocol.create_protocol(
            "phase_current_surface_recovery",
            skill_revision,
            agent,
            recovery_mode="HUMAN_APPROVE",
            retry_budget=2,
        )
        rt.agent_protocol.record_preflight(
            "phase_current_surface_recovery",
            [{"name": "ready", "pass": True}],
            agent,
        )
        rt.agent_protocol.create_plan(
            "phase_current_surface_recovery",
            "Execute current surface recovery UAT",
            [{"title": "Seeded risky step"}],
            agent,
        )
        rt.agent_protocol.start_execution(
            "phase_current_surface_recovery", agent
        )
        rt.agent_protocol.update_step(
            "phase_current_surface_recovery", 1, "FAIL", agent
        )
        problem_id = rt.agent_protocol.record_problem(
            "phase_current_surface_recovery",
            agent,
            code="CURRENT_SURFACE_UAT",
            summary="Human recovery decision required",
            detail="Persisted UAT problem",
            affected_step=1,
            severity="HIGH",
        )
        recovery = rt.agent_protocol.propose_recovery(
            problem_id,
            agent,
            action="REPLAN",
            target_step=1,
            rationale="Use a controlled revised plan",
            risk_class="MEDIUM",
            normative_change=False,
        )
        if recovery["status"] != "WAITING_HUMAN":
            raise RuntimeError("recovery seed did not reach WAITING_HUMAN")

        rt.governance.append_audit(
            recovery_project,
            agent,
            "CURRENT_SURFACE_UAT_RECOVERY_WAITING_HUMAN",
            "PhaseExecution",
            "phase_current_surface_recovery",
            reason_code="UAT_FIXTURE",
        )
        rt.db.conn.commit()

        return {
            "actor_id": owner,
            "tenant_id": tenant,
            "workspace_id": workspace,
            "domain_package_id": package,
            "domain_revision_id": revision,
            "execution_project_id": execution_project,
            "lifecycle_project_id": lifecycle_project,
            "recovery_project_id": recovery_project,
            "archived_project_id": archived_project,
            "approval_id": "proposal_current_surface_uat",
            "recovery_phase_id": "phase_current_surface_recovery",
            "recovery_proposal_id": recovery["proposal_id"],
            "github_binding_id": binding,
            "github_change_set_id": change_set,
        }
    finally:
        rt.close()


def main() -> None:
    result = seed()
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
