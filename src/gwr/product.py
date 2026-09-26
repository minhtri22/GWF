from __future__ import annotations

from typing import Any

from .errors import AuthorityDenied, NotFound
from .tenancy import PROJECT_ROLE_PERMISSIONS, TENANT_ROLE_PERMISSIONS, WORKSPACE_ROLE_PERMISSIONS
from .utils import parse_json, utcnow


def _parsed(row, fields: tuple[str, ...]):
    if row is None:
        return None
    out = dict(row)
    for field in fields:
        if field in out:
            out[field] = parse_json(out[field], None)
    return out


class ProjectDashboardService:
    """Read model for the operator-facing product surface."""

    def __init__(self, runtime):
        self.runtime = runtime
        self.db = runtime.db

    def _project(self, project_id: str):
        row = self.db.one("SELECT * FROM projects WHERE id=?", (project_id,))
        if not row:
            raise NotFound("Project not found")
        out = dict(row)
        scope = self.runtime.tenancy.scope_for_project(project_id)
        out["scope"] = {
            "tenant_id": scope.tenant_id,
            "workspace_id": scope.workspace_id,
        } if scope else None
        return out

    def pending_approvals(self, project_id: str):
        rows = self.db.all("SELECT * FROM proposals WHERE project_id=? AND status='PENDING_APPROVAL' ORDER BY created_at", (project_id,))
        result = []
        for row in rows:
            item = _parsed(row, ("resource_refs", "frozen_payload"))
            item["approval_history"] = [
                _parsed(a, ("scope", "conditions"))
                for a in self.db.all("SELECT * FROM approvals WHERE proposal_id=? ORDER BY created_at", (row["proposal_id"],))
            ]
            result.append(item)
        return result

    def failures(self, project_id: str):
        rows = self.db.all("SELECT * FROM failures WHERE project_id=? ORDER BY created_at", (project_id,))
        out = []
        for row in rows:
            item = _parsed(row, ("evidence_ids",))
            item["recovery_plans"] = [
                _parsed(r, ("keep_valid_refs", "invalidate_refs", "mark_stale_refs", "required_revision_actions", "required_workunits", "required_retests", "required_approvals"))
                for r in self.db.all("SELECT * FROM recoveries WHERE failure_id=? ORDER BY created_at", (row["failure_id"],))
            ]
            out.append(item)
        return out

    def failure_graph(self, project_id: str):
        failures = self.failures(project_id)
        nodes = []
        edges = []
        for failure in failures:
            fid = failure["failure_id"]
            nodes.append({
                "id": fid, "kind": "failure", "label": failure["failure_class"],
                "status": failure["status"], "severity": failure["severity"],
            })
            if failure.get("root_ref"):
                root_id = f"root:{failure['root_ref']}"
                nodes.append({"id": root_id, "kind": "root", "label": failure["root_ref"], "status": failure["root_status"]})
                edges.append({"from": fid, "to": root_id, "label": "root cause"})
            for recovery in failure["recovery_plans"]:
                rid = recovery["recovery_id"]
                nodes.append({"id": rid, "kind": "recovery", "label": recovery["resume_target"], "status": recovery["status"]})
                edges.append({"from": fid, "to": rid, "label": "recovery"})
                resume_id = f"resume:{recovery['resume_target']}"
                nodes.append({"id": resume_id, "kind": "resume", "label": recovery["resume_target"], "status": "TARGET"})
                edges.append({"from": rid, "to": resume_id, "label": "resume"})
        # stable unique nodes
        dedup = {}
        for node in nodes:
            dedup[node["id"]] = node
        return {"nodes": list(dedup.values()), "edges": edges}

    def runs(self, project_id: str):
        rows = self.db.all(
            "SELECT r.*,w.workunit_type,w.status AS workunit_status FROM runs r "
            "JOIN workunits w ON w.workunit_id=r.workunit_id WHERE w.project_id=? ORDER BY r.started_at",
            (project_id,),
        )
        return [_parsed(r, ("input_revision_ids", "exit_metadata", "produced_revision_ids", "evidence_ids")) for r in rows]

    def distributed(self, project_id: str):
        rows = self.db.all("SELECT job_id FROM distributed_jobs WHERE project_id=? ORDER BY created_at,job_id", (project_id,))
        jobs = [self.runtime.distributed.get_job(r["job_id"]) for r in rows]
        workers = []
        seen = set()
        for job in jobs:
            wid = job.get("lease_worker_id")
            if wid and wid not in seen:
                seen.add(wid)
                workers.append(self.runtime.distributed.get_worker(wid))
        return {"jobs": jobs, "workers": workers}

    def orchestrations(self, project_id: str):
        out = []
        for row in self.db.all("SELECT * FROM orchestrations WHERE project_id=? ORDER BY started_at DESC", (project_id,)):
            item = _parsed(row, ("metadata",))
            item["phases"] = [
                _parsed(p, ("metadata",))
                for p in self.db.all("SELECT * FROM phase_executions WHERE orchestration_id=? ORDER BY started_at", (row["orchestration_id"],))
            ]
            out.append(item)
        return out

    def home_summary(self, actor_id: str, *, build_sha: str, core_health: str) -> dict[str, Any]:
        """Authorized read-only projection for the global Home command dashboard."""
        projects = self.runtime.tenancy.list_accessible_projects(actor_id)
        project_ids = [p["id"] for p in projects]
        project_names = {p["id"]: p["name"] for p in projects}

        attention_items: list[dict[str, Any]] = []
        project_attention: dict[str, int] = {pid: 0 for pid in project_ids}
        project_rows: list[dict[str, Any]] = []
        live_runs: list[dict[str, Any]] = []

        def add_attention(project_id, kind, record_id, label, created_at):
            attention_items.append({
                "attention_id": f"{kind}:{record_id}",
                "record_id": record_id,
                "kind": kind,
                "project_id": project_id,
                "project_name": project_names.get(project_id) if project_id else None,
                "label": label,
                "created_at": created_at,
            })
            if project_id in project_attention:
                project_attention[project_id] += 1

        lifecycle_active = 0
        executing_now = 0
        running_runs_count = 0
        pending_approvals_count = 0

        for project in projects:
            project_id = project["id"]
            lifecycle_row = self.db.one("SELECT status FROM project_lifecycle WHERE project_id=?", (project_id,))
            lifecycle = lifecycle_row["status"] if lifecycle_row else "UNKNOWN"
            if lifecycle == "ACTIVE":
                lifecycle_active += 1

            latest_orchestration = self.db.one(
                "SELECT * FROM orchestrations WHERE project_id=? ORDER BY started_at DESC LIMIT 1", (project_id,)
            )
            running_runs = self.db.all(
                "SELECT r.*,w.workunit_type FROM runs r JOIN workunits w ON w.workunit_id=r.workunit_id "
                "WHERE w.project_id=? AND r.runtime_status='RUNNING' ORDER BY r.started_at DESC", (project_id,)
            )
            running_run = running_runs[0] if running_runs else None
            running_runs_count += len(running_runs)
            executing_job = self.db.one(
                "SELECT job_id FROM distributed_jobs WHERE project_id=? AND status IN ('LEASED','RUNNING') "
                "ORDER BY updated_at DESC LIMIT 1", (project_id,)
            )
            queued_job = self.db.one(
                "SELECT job_id FROM distributed_jobs WHERE project_id=? AND status='READY' "
                "ORDER BY updated_at DESC LIMIT 1", (project_id,)
            )
            if running_run or (latest_orchestration and latest_orchestration["status"] == "RUNNING") or executing_job:
                activity = "EXECUTING"
                executing_now += 1
            elif latest_orchestration and latest_orchestration["status"] == "PAUSED":
                activity = "PAUSED"
            elif queued_job:
                activity = "QUEUED"
            else:
                activity = "IDLE"

            phase = None
            if latest_orchestration:
                phase = self.db.one(
                    "SELECT * FROM phase_executions WHERE orchestration_id=? "
                    "ORDER BY phase_index DESC,started_at DESC LIMIT 1",
                    (latest_orchestration["orchestration_id"],),
                )

            actor = None
            if phase:
                event = self.db.one(
                    "SELECT actor_id FROM phase_stage_events WHERE phase_execution_id=? "
                    "ORDER BY created_at DESC,event_id DESC LIMIT 1",
                    (phase["phase_execution_id"],),
                )
                if event:
                    actor = event["actor_id"]
            if not actor and running_run:
                actor = running_run["executor_actor_id"]
            actor = actor or "SYSTEM"

            latest_event = self.db.one(
                "SELECT event_id,action,timestamp FROM audit_events WHERE project_id=? "
                "ORDER BY timestamp DESC,event_id DESC LIMIT 1", (project_id,)
            )
            domain = self.db.one(
                "SELECT b.domain_revision_id,r.semantic_version,p.domain_id "
                "FROM project_domain_bindings b "
                "JOIN domain_package_revisions r ON r.revision_id=b.domain_revision_id "
                "JOIN domain_packages p ON p.package_id=r.package_id WHERE b.project_id=?",
                (project_id,),
            )

            pending = self.db.all(
                "SELECT proposal_id,action,created_at FROM proposals "
                "WHERE project_id=? AND status='PENDING_APPROVAL' ORDER BY created_at", (project_id,)
            )
            pending_approvals_count += len(pending)
            for row in pending:
                add_attention(project_id, "PENDING_APPROVAL", row["proposal_id"], row["action"], row["created_at"])

            for row in self.db.all(
                "SELECT failure_id,failure_class,severity,created_at FROM failures "
                "WHERE project_id=? AND status!='RESOLVED' ORDER BY created_at", (project_id,)
            ):
                add_attention(project_id, "FAILURE", row["failure_id"],
                              f"{row['failure_class']} · {row['severity']}", row["created_at"])

            for row in self.db.all(
                "SELECT r.proposal_id,r.action,r.created_at FROM phase_recovery_proposals r "
                "JOIN phase_execution_protocols p ON p.phase_execution_id=r.phase_execution_id "
                "WHERE p.project_id=? AND r.status='WAITING_HUMAN' ORDER BY r.created_at", (project_id,)
            ):
                add_attention(project_id, "WAITING_HUMAN", row["proposal_id"], row["action"], row["created_at"])

            for row in self.db.all(
                "SELECT change_set_id,status,branch,created_at FROM github_change_sets "
                "WHERE project_id=? AND status IN ('STALE','VERIFICATION_FAILED') ORDER BY created_at", (project_id,)
            ):
                add_attention(project_id, "GITHUB_CHANGESET", row["change_set_id"],
                              f"{row['status']} · {row['branch']}", row["created_at"])

            project_rows.append({
                "project_id": project_id,
                "project_name": project["name"],
                "lifecycle": lifecycle,
                "execution_activity": activity,
                "domain": {
                    "domain_id": domain["domain_id"] if domain else project.get("domain_id"),
                    "revision_id": domain["domain_revision_id"] if domain else None,
                    "semantic_version": domain["semantic_version"] if domain else None,
                },
                "orchestration_id": latest_orchestration["orchestration_id"] if latest_orchestration else None,
                "phase_execution_id": phase["phase_execution_id"] if phase else None,
                "phase_label": phase["phase_id"] if phase else None,
                "current_actor": actor,
                "running_run_id": running_run["run_id"] if running_run else None,
                "latest_event_at": latest_event["timestamp"] if latest_event else None,
                "attention_count": 0,
            })

            for run in running_runs:
                run_event = self.db.one(
                    "SELECT event_id,action,timestamp FROM audit_events WHERE project_id=? AND run_id=? "
                    "ORDER BY timestamp DESC,event_id DESC LIMIT 1", (project_id, run["run_id"])
                )
                run_phase = self.db.one(
                    "SELECT phase_execution_id,phase_id FROM phase_executions WHERE run_id=? "
                    "ORDER BY started_at DESC LIMIT 1", (run["run_id"],)
                )
                live_runs.append({
                    "run_id": run["run_id"],
                    "project_id": project_id,
                    "project_name": project["name"],
                    "workunit_type": run["workunit_type"],
                    "phase_execution_id": run_phase["phase_execution_id"] if run_phase else None,
                    "phase_label": run_phase["phase_id"] if run_phase else None,
                    "status": run["runtime_status"],
                    "started_at": run["started_at"],
                    "actor": run["executor_actor_id"] or "SYSTEM",
                    "latest_event_action": run_event["action"] if run_event else None,
                    "latest_event_at": run_event["timestamp"] if run_event else None,
                })

        if core_health != "HEALTHY":
            add_attention(None, "SYSTEM_HEALTH", "core-health", core_health, utcnow())

        for row in project_rows:
            row["attention_count"] = project_attention.get(row["project_id"], 0)

        recent_activity = []
        if project_ids:
            placeholders = ",".join("?" for _ in project_ids)
            for row in self.db.all(
                "SELECT event_id,project_id,actor_id,action,resource_type,resource_id,reason_code,timestamp "
                f"FROM audit_events WHERE project_id IN ({placeholders}) "
                "ORDER BY timestamp DESC,event_id DESC LIMIT 20", tuple(project_ids)
            ):
                recent_activity.append({
                    "event_id": row["event_id"],
                    "project_id": row["project_id"],
                    "project_name": project_names.get(row["project_id"]),
                    "actor_id": row["actor_id"],
                    "action": row["action"],
                    "resource_type": row["resource_type"],
                    "resource_id": row["resource_id"],
                    "reason_code": row["reason_code"],
                    "timestamp": row["timestamp"],
                })

        return {
            "generated_at": utcnow(),
            "build_sha": build_sha,
            "scope": {"mode": "ALL_AUTHORIZED", "label": "All authorized projects", "project_count": len(projects)},
            "query_status": "COMPLETE",
            "kpis": {
                "total_projects": len(projects),
                "lifecycle_active": lifecycle_active,
                "executing_now": executing_now,
                "running_runs": running_runs_count,
                "pending_approvals": pending_approvals_count,
                "attention_required": len(attention_items),
                "core_health": core_health if core_health in {"HEALTHY", "DEGRADED", "UNHEALTHY", "UNKNOWN"} else "UNKNOWN",
            },
            "executing_projects": sorted(
                [row for row in project_rows if row["execution_activity"] == "EXECUTING"],
                key=lambda row: (row["project_name"], row["project_id"]),
            ),
            "live_runs": sorted(live_runs, key=lambda row: row["started_at"], reverse=True),
            "attention": sorted(attention_items, key=lambda row: (row["created_at"] or "", row["attention_id"]), reverse=True),
            "recent_activity": recent_activity,
        }

    def projects_index(self, actor_id: str, *, build_sha: str) -> dict[str, Any]:
        """Authorized read-only projection for the global Projects index."""
        projects = self.runtime.tenancy.list_accessible_projects(actor_id)
        rows: list[dict[str, Any]] = []
        complete = True

        for project in projects:
            project_id = project["id"]
            lifecycle_row = self.db.one(
                "SELECT status FROM project_lifecycle WHERE project_id=?",
                (project_id,),
            )
            lifecycle = lifecycle_row["status"] if lifecycle_row else None
            if lifecycle not in {"ACTIVE", "ARCHIVING", "ARCHIVED"}:
                lifecycle = None
                complete = False

            tenant = self.db.one(
                "SELECT name FROM tenants WHERE tenant_id=?",
                (project["tenant_id"],),
            )
            workspace = self.db.one(
                "SELECT name FROM workspaces WHERE workspace_id=?",
                (project["workspace_id"],),
            )
            if tenant is None or workspace is None:
                complete = False

            domain = self.db.one(
                "SELECT b.domain_revision_id,r.revision_number,r.semantic_version,"
                "r.status AS revision_status,p.package_id,p.domain_id,p.name AS domain_name "
                "FROM project_domain_bindings b "
                "JOIN domain_package_revisions r ON r.revision_id=b.domain_revision_id "
                "JOIN domain_packages p ON p.package_id=r.package_id "
                "WHERE b.project_id=?",
                (project_id,),
            )

            latest_orchestration = self.db.one(
                "SELECT orchestration_id,status FROM orchestrations "
                "WHERE project_id=? ORDER BY started_at DESC LIMIT 1",
                (project_id,),
            )
            running_runs = int(self.db.one(
                "SELECT COUNT(*) n FROM runs r JOIN workunits w ON w.workunit_id=r.workunit_id "
                "WHERE w.project_id=? AND r.runtime_status='RUNNING'",
                (project_id,),
            )["n"])
            executing_jobs = int(self.db.one(
                "SELECT COUNT(*) n FROM distributed_jobs "
                "WHERE project_id=? AND status IN ('LEASED','RUNNING')",
                (project_id,),
            )["n"])
            ready_jobs = int(self.db.one(
                "SELECT COUNT(*) n FROM distributed_jobs "
                "WHERE project_id=? AND status='READY'",
                (project_id,),
            )["n"])
            active_jobs = executing_jobs + ready_jobs

            if running_runs or (
                latest_orchestration and latest_orchestration["status"] == "RUNNING"
            ) or executing_jobs:
                activity = "EXECUTING"
            elif latest_orchestration and latest_orchestration["status"] == "PAUSED":
                activity = "PAUSED"
            elif ready_jobs:
                activity = "QUEUED"
            else:
                activity = "IDLE"

            pending_approvals = self.db.all(
                "SELECT proposal_id FROM proposals "
                "WHERE project_id=? AND status='PENDING_APPROVAL'",
                (project_id,),
            )
            attention_ids = {
                f"PENDING_APPROVAL:{row['proposal_id']}" for row in pending_approvals
            }
            attention_ids.update(
                f"FAILURE:{row['failure_id']}"
                for row in self.db.all(
                    "SELECT failure_id FROM failures "
                    "WHERE project_id=? AND status!='RESOLVED'",
                    (project_id,),
                )
            )
            attention_ids.update(
                f"WAITING_HUMAN:{row['proposal_id']}"
                for row in self.db.all(
                    "SELECT r.proposal_id FROM phase_recovery_proposals r "
                    "JOIN phase_execution_protocols p "
                    "ON p.phase_execution_id=r.phase_execution_id "
                    "WHERE p.project_id=? AND r.status='WAITING_HUMAN'",
                    (project_id,),
                )
            )
            attention_ids.update(
                f"GITHUB_CHANGESET:{row['change_set_id']}"
                for row in self.db.all(
                    "SELECT change_set_id FROM github_change_sets "
                    "WHERE project_id=? AND status IN ('STALE','VERIFICATION_FAILED')",
                    (project_id,),
                )
            )

            latest_event = self.db.one(
                "SELECT action,timestamp FROM audit_events "
                "WHERE project_id=? ORDER BY timestamp DESC,event_id DESC LIMIT 1",
                (project_id,),
            )

            rows.append({
                "project_id": project_id,
                "name": project["name"],
                "scope": {
                    "tenant_id": project["tenant_id"],
                    "tenant_name": tenant["name"] if tenant else None,
                    "workspace_id": project["workspace_id"],
                    "workspace_name": workspace["name"] if workspace else None,
                },
                "lifecycle": lifecycle,
                "domain": {
                    "bound": domain is not None,
                    "package_id": domain["package_id"] if domain else None,
                    "domain_id": domain["domain_id"] if domain else project.get("domain_id"),
                    "domain_name": domain["domain_name"] if domain else None,
                    "revision_id": domain["domain_revision_id"] if domain else None,
                    "revision_number": domain["revision_number"] if domain else None,
                    "semantic_version": domain["semantic_version"] if domain else None,
                    "revision_status": domain["revision_status"] if domain else None,
                },
                "execution_activity": activity,
                "running_runs": running_runs,
                "active_jobs": active_jobs,
                "pending_approvals": len(pending_approvals),
                "attention_required": len(attention_ids),
                "latest_event": {
                    "action": latest_event["action"],
                    "timestamp": latest_event["timestamp"],
                } if latest_event else None,
                "created_at": project["created_at"],
            })

        rows.sort(key=lambda row: (row["name"].lower(), row["project_id"]))

        return {
            "generated_at": utcnow(),
            "build_sha": build_sha,
            "query_status": "COMPLETE" if complete else "PARTIAL",
            "scope": {
                "mode": "ALL_AUTHORIZED",
                "label": "All authorized projects",
                "project_count": len(rows),
            },
            "projects": rows,
        }

    def operations_approvals(self, actor_id: str, *, build_sha: str) -> dict[str, Any]:
        """Authorized cross-project pending approval inbox and decision history."""
        projects = self.runtime.tenancy.list_accessible_projects(actor_id)
        pending: list[dict[str, Any]] = []
        decisions: list[dict[str, Any]] = []

        for project in projects:
            project_id = project["id"]
            can_review = True
            try:
                self.runtime.tenancy.require_project_access(actor_id, project_id, "REVIEW")
            except (AuthorityDenied, NotFound):
                can_review = False
            can_approve = True
            try:
                self.runtime.tenancy.require_project_access(actor_id, project_id, "APPROVE")
            except (AuthorityDenied, NotFound):
                can_approve = False
            if not can_review and not can_approve:
                continue

            tenant = self.db.one("SELECT name FROM tenants WHERE tenant_id=?", (project["tenant_id"],))
            workspace = self.db.one("SELECT name FROM workspaces WHERE workspace_id=?", (project["workspace_id"],))
            scope = {
                "tenant_id": project["tenant_id"],
                "tenant_name": tenant["name"] if tenant else None,
                "workspace_id": project["workspace_id"],
                "workspace_name": workspace["name"] if workspace else None,
            }

            for row in self.db.all(
                "SELECT * FROM proposals WHERE project_id=? AND status='PENDING_APPROVAL' "
                "ORDER BY created_at,proposal_id",
                (project_id,),
            ):
                item = _parsed(row, ("resource_refs", "frozen_payload"))
                item.update({
                    "project_name": project["name"],
                    "scope": scope,
                    "can_approve": can_approve,
                    "approval_history": [
                        _parsed(history, ("scope", "conditions"))
                        for history in self.db.all(
                            "SELECT * FROM approvals WHERE proposal_id=? "
                            "ORDER BY created_at,approval_id",
                            (row["proposal_id"],),
                        )
                    ],
                })
                pending.append(item)

            for history in self.db.all(
                "SELECT a.*,p.action,p.status AS proposal_status,p.proposer_actor_id,"
                "p.required_approval_policy,p.created_at AS proposal_created_at "
                "FROM approvals a JOIN proposals p ON p.proposal_id=a.proposal_id "
                "WHERE a.project_id=? ORDER BY a.created_at DESC,a.approval_id DESC",
                (project_id,),
            ):
                item = _parsed(history, ("scope", "conditions"))
                item.update({
                    "project_name": project["name"],
                    "scope_context": scope,
                })
                decisions.append(item)

        pending.sort(key=lambda row: (row["created_at"], row["proposal_id"]))
        decisions.sort(key=lambda row: (row["created_at"], row["approval_id"]), reverse=True)
        return {
            "generated_at": utcnow(),
            "build_sha": build_sha,
            "query_status": "COMPLETE",
            "scope": {
                "mode": "ALL_AUTHORIZED",
                "label": "All authorized projects",
                "project_count": len(projects),
            },
            "pending": pending,
            "decisions": decisions,
        }

    def operations_runs(self, actor_id: str, *, build_sha: str) -> dict[str, Any]:
        """Authorized cross-project Runs projection for Global Operations."""
        projects = self.runtime.tenancy.list_accessible_projects(actor_id)
        rows: list[dict[str, Any]] = []
        complete = True

        for project in projects:
            project_id = project["id"]
            tenant = self.db.one(
                "SELECT name FROM tenants WHERE tenant_id=?",
                (project["tenant_id"],),
            )
            workspace = self.db.one(
                "SELECT name FROM workspaces WHERE workspace_id=?",
                (project["workspace_id"],),
            )
            if tenant is None or workspace is None:
                complete = False

            for run_row in self.db.all(
                "SELECT r.*,w.workunit_type,w.status AS workunit_status "
                "FROM runs r JOIN workunits w ON w.workunit_id=r.workunit_id "
                "WHERE w.project_id=? ORDER BY r.started_at DESC,r.run_id DESC",
                (project_id,),
            ):
                run = _parsed(
                    run_row,
                    ("input_revision_ids", "exit_metadata", "produced_revision_ids", "evidence_ids"),
                )
                phase = self.db.one(
                    "SELECT phase_execution_id,orchestration_id,phase_id,status "
                    "FROM phase_executions WHERE run_id=? "
                    "ORDER BY started_at DESC,phase_execution_id DESC LIMIT 1",
                    (run["run_id"],),
                )
                latest_event = self.db.one(
                    "SELECT event_id,action,timestamp FROM audit_events "
                    "WHERE project_id=? AND run_id=? "
                    "ORDER BY timestamp DESC,event_id DESC LIMIT 1",
                    (project_id, run["run_id"]),
                )
                rows.append({
                    "run_id": run["run_id"],
                    "project_id": project_id,
                    "project_name": project["name"],
                    "scope": {
                        "tenant_id": project["tenant_id"],
                        "tenant_name": tenant["name"] if tenant else None,
                        "workspace_id": project["workspace_id"],
                        "workspace_name": workspace["name"] if workspace else None,
                    },
                    "workunit_id": run["workunit_id"],
                    "workunit_type": run["workunit_type"],
                    "workunit_status": run["workunit_status"],
                    "phase": {
                        "phase_execution_id": phase["phase_execution_id"] if phase else None,
                        "orchestration_id": phase["orchestration_id"] if phase else None,
                        "phase_id": phase["phase_id"] if phase else None,
                        "status": phase["status"] if phase else None,
                    },
                    "attempt_number": run["attempt_number"],
                    "executor_actor_id": run["executor_actor_id"],
                    "runtime_status": run["runtime_status"],
                    "started_at": run["started_at"],
                    "finished_at": run["finished_at"],
                    "input_revision_ids": run["input_revision_ids"] or [],
                    "produced_revision_ids": run["produced_revision_ids"] or [],
                    "evidence_ids": run["evidence_ids"] or [],
                    "checkpoint_id": run["checkpoint_id"],
                    "correlation_id": run["correlation_id"],
                    "latest_event": {
                        "event_id": latest_event["event_id"],
                        "action": latest_event["action"],
                        "timestamp": latest_event["timestamp"],
                    } if latest_event else None,
                })

        rows.sort(
            key=lambda row: (row["started_at"] or "", row["run_id"]),
            reverse=True,
        )
        return {
            "generated_at": utcnow(),
            "build_sha": build_sha,
            "query_status": "COMPLETE" if complete else "PARTIAL",
            "scope": {
                "mode": "ALL_AUTHORIZED",
                "label": "All authorized projects",
                "project_count": len(projects),
            },
            "runs": rows,
        }

    def access_summary(self, actor_id: str, *, build_sha: str) -> dict[str, Any]:
        """Authorized read projection for System -> Access."""
        actor = self.db.one(
            "SELECT actor_id,actor_type,principal_id,status FROM actors WHERE actor_id=?",
            (actor_id,),
        )
        if not actor or actor["status"] != "ACTIVE":
            raise AuthorityDenied("Actor is not active")

        def can(callable_):
            try:
                callable_()
                return True
            except (AuthorityDenied, NotFound):
                return False

        tenants: list[dict[str, Any]] = []
        tenant_rows = self.db.all(
            "SELECT t.tenant_id,t.name,t.status,t.created_by_actor_id,t.created_at,"
            "m.role AS actor_role,m.status AS actor_membership_status "
            "FROM tenants t JOIN tenant_memberships m ON m.tenant_id=t.tenant_id "
            "WHERE m.actor_id=? AND m.status='ACTIVE' "
            "ORDER BY t.name,t.tenant_id",
            (actor_id,),
        )
        visible_tenant_ids: set[str] = set()
        for row in tenant_rows:
            tenant_id = row["tenant_id"]
            visible_tenant_ids.add(tenant_id)
            manageable = can(
                lambda tenant_id=tenant_id: self.runtime.tenancy.require_tenant_access(
                    actor_id, tenant_id, "MANAGE_MEMBERS"
                )
            )
            members = []
            if manageable:
                members = [
                    dict(item) for item in self.db.all(
                        "SELECT actor_id,role,status,created_at "
                        "FROM tenant_memberships WHERE tenant_id=? "
                        "ORDER BY status,role,actor_id",
                        (tenant_id,),
                    )
                ]
            tenants.append({
                "tenant_id": tenant_id,
                "name": row["name"],
                "status": row["status"],
                "actor_role": row["actor_role"],
                "actor_membership_status": row["actor_membership_status"],
                "can_manage_members": manageable,
                "can_manage_workspaces": can(
                    lambda tenant_id=tenant_id: self.runtime.tenancy.require_tenant_access(
                        actor_id, tenant_id, "MANAGE_WORKSPACE"
                    )
                ),
                "members": members,
                "created_by_actor_id": row["created_by_actor_id"],
                "created_at": row["created_at"],
            })

        workspaces: list[dict[str, Any]] = []
        for row in self.db.all(
            "SELECT w.workspace_id,w.tenant_id,w.name,w.status,w.created_by_actor_id,w.created_at,"
            "t.name AS tenant_name FROM workspaces w "
            "JOIN tenants t ON t.tenant_id=w.tenant_id "
            "WHERE w.status='ACTIVE' ORDER BY t.name,w.name,w.workspace_id"
        ):
            workspace_id = row["workspace_id"]
            if not can(
                lambda workspace_id=workspace_id: self.runtime.tenancy.require_workspace_access(
                    actor_id, workspace_id, "VIEW"
                )
            ):
                continue
            direct = self.db.one(
                "SELECT role,status FROM workspace_memberships "
                "WHERE workspace_id=? AND actor_id=?",
                (workspace_id, actor_id),
            )
            tenant_membership = self.db.one(
                "SELECT role,status FROM tenant_memberships "
                "WHERE tenant_id=? AND actor_id=?",
                (row["tenant_id"], actor_id),
            )
            manageable = can(
                lambda workspace_id=workspace_id: self.runtime.tenancy.require_workspace_access(
                    actor_id, workspace_id, "MANAGE_MEMBERS"
                )
            )
            members = []
            if manageable:
                members = [
                    dict(item) for item in self.db.all(
                        "SELECT actor_id,role,status,created_at "
                        "FROM workspace_memberships WHERE workspace_id=? "
                        "ORDER BY status,role,actor_id",
                        (workspace_id,),
                    )
                ]
            inherited = bool(
                not direct
                and tenant_membership
                and tenant_membership["status"] == "ACTIVE"
                and tenant_membership["role"] in {"OWNER", "ADMIN"}
            )
            workspaces.append({
                "workspace_id": workspace_id,
                "workspace_name": row["name"],
                "tenant_id": row["tenant_id"],
                "tenant_name": row["tenant_name"],
                "status": row["status"],
                "actor_role": direct["role"] if direct else (
                    tenant_membership["role"] if inherited else None
                ),
                "role_source": "WORKSPACE" if direct else (
                    "TENANT_INHERITED" if inherited else None
                ),
                "can_manage_members": manageable,
                "can_manage_projects": can(
                    lambda workspace_id=workspace_id: self.runtime.tenancy.require_workspace_access(
                        actor_id, workspace_id, "MANAGE_PROJECT"
                    )
                ),
                "members": members,
                "created_by_actor_id": row["created_by_actor_id"],
                "created_at": row["created_at"],
            })
            visible_tenant_ids.add(row["tenant_id"])

        projects: list[dict[str, Any]] = []
        for project in self.runtime.tenancy.list_accessible_projects(actor_id):
            project_id = project["id"]
            scope = self.runtime.tenancy.scope_for_project(project_id)
            if not scope:
                continue
            direct = self.db.one(
                "SELECT role,status FROM project_memberships "
                "WHERE project_id=? AND actor_id=?",
                (project_id, actor_id),
            )
            workspace_membership = self.db.one(
                "SELECT role,status FROM workspace_memberships "
                "WHERE workspace_id=? AND actor_id=?",
                (scope.workspace_id, actor_id),
            )
            tenant_membership = self.db.one(
                "SELECT role,status FROM tenant_memberships "
                "WHERE tenant_id=? AND actor_id=?",
                (scope.tenant_id, actor_id),
            )
            if direct and direct["status"] == "ACTIVE":
                actor_role = direct["role"]
                role_source = "PROJECT"
            elif workspace_membership and workspace_membership["status"] == "ACTIVE":
                actor_role = workspace_membership["role"]
                role_source = "WORKSPACE_INHERITED"
            elif tenant_membership and tenant_membership["status"] == "ACTIVE":
                actor_role = tenant_membership["role"]
                role_source = "TENANT_INHERITED"
            else:
                actor_role = None
                role_source = None
            manageable = can(
                lambda project_id=project_id: self.runtime.tenancy.require_project_access(
                    actor_id, project_id, "MANAGE_MEMBERS"
                )
            )
            members = []
            if manageable:
                members = [
                    dict(item) for item in self.db.all(
                        "SELECT actor_id,role,status,created_at "
                        "FROM project_memberships WHERE project_id=? "
                        "ORDER BY status,role,actor_id",
                        (project_id,),
                    )
                ]
            workspace = self.db.one(
                "SELECT name FROM workspaces WHERE workspace_id=?",
                (scope.workspace_id,),
            )
            tenant = self.db.one(
                "SELECT name FROM tenants WHERE tenant_id=?",
                (scope.tenant_id,),
            )
            projects.append({
                "project_id": project_id,
                "project_name": project["name"],
                "tenant_id": scope.tenant_id,
                "tenant_name": tenant["name"] if tenant else None,
                "workspace_id": scope.workspace_id,
                "workspace_name": workspace["name"] if workspace else None,
                "actor_role": actor_role,
                "role_source": role_source,
                "can_manage_members": manageable,
                "members": members,
            })

        return {
            "generated_at": utcnow(),
            "build_sha": build_sha,
            "query_status": "COMPLETE",
            "actor": dict(actor),
            "roles": {
                "tenant": sorted(TENANT_ROLE_PERMISSIONS),
                "workspace": sorted(WORKSPACE_ROLE_PERMISSIONS),
                "project": sorted(PROJECT_ROLE_PERMISSIONS),
            },
            "tenants": tenants,
            "workspaces": workspaces,
            "projects": projects,
        }

    def project_create_options(self, actor_id: str, *, build_sha: str) -> dict[str, Any]:
        """Authorized choices for the bounded Create Project workflow."""
        # Validate actor status through the public tenancy read contract.
        self.runtime.tenancy.memberships_for_actor(actor_id)

        scopes: list[dict[str, Any]] = []
        tenant_ids: set[str] = set()
        for row in self.db.all(
            "SELECT w.workspace_id,w.name AS workspace_name,w.tenant_id,"
            "t.name AS tenant_name FROM workspaces w "
            "JOIN tenants t ON t.tenant_id=w.tenant_id "
            "WHERE w.status='ACTIVE' AND t.status='ACTIVE' "
            "ORDER BY t.name,t.tenant_id,w.name,w.workspace_id"
        ):
            try:
                self.runtime.tenancy.require_workspace_access(
                    actor_id, row["workspace_id"], "MANAGE_PROJECT"
                )
            except (AuthorityDenied, NotFound):
                continue
            scopes.append({
                "tenant_id": row["tenant_id"],
                "tenant_name": row["tenant_name"],
                "workspace_id": row["workspace_id"],
                "workspace_name": row["workspace_name"],
            })
            tenant_ids.add(row["tenant_id"])

        domains: list[dict[str, Any]] = []
        if tenant_ids:
            placeholders = ",".join("?" for _ in tenant_ids)
            for row in self.db.all(
                "SELECT p.tenant_id,p.package_id,p.domain_id,p.name AS domain_name,"
                "r.revision_id,r.revision_number,r.semantic_version,r.payload_hash,"
                "r.published_at FROM domain_package_revisions r "
                "JOIN domain_packages p ON p.package_id=r.package_id "
                f"WHERE p.tenant_id IN ({placeholders}) AND p.status='ACTIVE' "
                "AND r.status='PUBLISHED' "
                "ORDER BY p.tenant_id,p.name,p.package_id,r.revision_number,r.revision_id",
                tuple(sorted(tenant_ids)),
            ):
                domains.append(dict(row))

        return {
            "generated_at": utcnow(),
            "build_sha": build_sha,
            "query_status": "COMPLETE",
            "scopes": scopes,
            "published_domain_revisions": domains,
            "contract": {
                "project_id": "SERVER_GENERATED",
                "domain_binding": "OPTIONAL_PUBLISHED_IMMUTABLE",
                "success_destination": "/app/projects/:projectId/overview",
            },
        }

    def summary(self, project_id: str) -> dict[str, Any]:
        project = self._project(project_id)
        orchestrations = self.orchestrations(project_id)
        failures = self.failures(project_id)
        approvals = self.pending_approvals(project_id)
        workunits = [dict(r) for r in self.db.all("SELECT * FROM workunits WHERE project_id=? ORDER BY workunit_id", (project_id,))]
        distributed = self.distributed(project_id)
        audit_count = self.db.one("SELECT COUNT(*) n FROM audit_events WHERE project_id=?", (project_id,))["n"]
        status = orchestrations[0]["status"] if orchestrations else ("ATTENTION" if failures or approvals else "READY")
        return {
            "product_version": "0.8.2",
            "project": project,
            "project_lifecycle": self.runtime.project_governance.status(project_id),
            "name_history": self.runtime.project_governance.name_history(project_id),
            "domain_binding": self.runtime.domains.project_binding(project_id),
            "process": self.runtime.process.process(project_id),
            "status": status,
            "orchestrations": orchestrations,
            "workunits": workunits,
            "runs": self.runs(project_id),
            "distributed": distributed,
            "approvals": approvals,
            "failures": failures,
            "failure_graph": self.failure_graph(project_id),
            "frontier": self.runtime.knowledge.get_validity_frontier(project_id),
            "audit_count": audit_count,
            "metrics": {
                "pending_approvals": len(approvals),
                "open_failures": len([f for f in failures if f["status"] != "RESOLVED"]),
                "active_jobs": len([j for j in distributed["jobs"] if j["status"] in {"READY", "LEASED", "RUNNING"}]),
                "phase_executions": sum(len(o["phases"]) for o in orchestrations),
            },
        }
