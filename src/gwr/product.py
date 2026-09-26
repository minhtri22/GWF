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

    def operations_audit(self, actor_id: str, *, build_sha: str) -> dict[str, Any]:
        """Authorized cross-project append-only audit projection."""
        projects = self.runtime.tenancy.list_accessible_projects(actor_id)
        events: list[dict[str, Any]] = []
        complete = True

        for project in projects:
            tenant = self.db.one("SELECT name FROM tenants WHERE tenant_id=?", (project["tenant_id"],))
            workspace = self.db.one("SELECT name FROM workspaces WHERE workspace_id=?", (project["workspace_id"],))
            if tenant is None or workspace is None:
                complete = False
            for row in self.db.all(
                "SELECT * FROM audit_events WHERE project_id=? "
                "ORDER BY timestamp DESC,event_id DESC",
                (project["id"],),
            ):
                item = dict(row)
                item.update({
                    "project_name": project["name"],
                    "scope": {
                        "tenant_id": project["tenant_id"],
                        "tenant_name": tenant["name"] if tenant else None,
                        "workspace_id": project["workspace_id"],
                        "workspace_name": workspace["name"] if workspace else None,
                    },
                })
                events.append(item)

        events.sort(key=lambda row: (row["timestamp"], row["event_id"]), reverse=True)
        return {
            "generated_at": utcnow(),
            "build_sha": build_sha,
            "query_status": "COMPLETE" if complete else "PARTIAL",
            "scope": {
                "mode": "ALL_AUTHORIZED",
                "label": "All authorized projects",
                "project_count": len(projects),
            },
            "events": events,
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

    def operations_runtime(self, actor_id: str, *, build_sha: str) -> dict[str, Any]:
        """Authorized cross-project distributed-runtime projection."""
        projects = self.runtime.tenancy.list_accessible_projects(actor_id)
        jobs: list[dict[str, Any]] = []
        referenced_worker_ids: set[str] = set()
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
            scope = {
                "tenant_id": project["tenant_id"],
                "tenant_name": tenant["name"] if tenant else None,
                "workspace_id": project["workspace_id"],
                "workspace_name": workspace["name"] if workspace else None,
            }

            for job_row in self.db.all(
                "SELECT j.*,w.workunit_type,w.status AS workunit_status,"
                "w.resource_conflict_keys FROM distributed_jobs j "
                "JOIN workunits w ON w.workunit_id=j.workunit_id "
                "WHERE j.project_id=? ORDER BY j.created_at DESC,j.job_id DESC",
                (project_id,),
            ):
                job = dict(job_row)
                attempts: list[dict[str, Any]] = []
                for attempt_row in self.db.all(
                    "SELECT attempt_id,job_id,attempt_number,worker_id,run_id,status,"
                    "started_at,heartbeat_at,lease_expires_at,finished_at,error_code "
                    "FROM job_attempts WHERE job_id=? "
                    "ORDER BY attempt_number,attempt_id",
                    (job["job_id"],),
                ):
                    attempt = dict(attempt_row)
                    referenced_worker_ids.add(attempt["worker_id"])
                    run_status = None
                    if attempt.get("run_id"):
                        run = self.db.one(
                            "SELECT runtime_status FROM runs WHERE run_id=?",
                            (attempt["run_id"],),
                        )
                        run_status = run["runtime_status"] if run else None
                    attempt["run_status"] = run_status
                    attempts.append(attempt)

                lease_worker_id = job.get("lease_worker_id")
                if lease_worker_id:
                    referenced_worker_ids.add(lease_worker_id)

                events = [
                    _parsed(row, ("metadata",))
                    for row in self.db.all(
                        "SELECT event_id,project_id,job_id,worker_id,event_type,metadata,created_at "
                        "FROM scheduler_events WHERE job_id=? "
                        "ORDER BY created_at,event_id",
                        (job["job_id"],),
                    )
                ]

                jobs.append({
                    "job_id": job["job_id"],
                    "project_id": project_id,
                    "project_name": project["name"],
                    "scope": scope,
                    "workunit_id": job["workunit_id"],
                    "workunit_type": job["workunit_type"],
                    "workunit_status": job["workunit_status"],
                    "resource_conflict_keys": parse_json(job["resource_conflict_keys"], []) or [],
                    "status": job["status"],
                    "priority": job["priority"],
                    "required_resources": parse_json(job["required_resources"], {}) or {},
                    "required_capabilities": parse_json(job["required_capabilities"], []) or [],
                    "available_at": job["available_at"],
                    "attempt_count": job["attempt_count"],
                    "max_attempts": job["max_attempts"],
                    "last_error": job["last_error"],
                    "created_at": job["created_at"],
                    "updated_at": job["updated_at"],
                    "lease": {
                        "worker_id": lease_worker_id,
                        "has_token": bool(job.get("lease_token")),
                        "expires_at": job.get("lease_expires_at"),
                    },
                    "attempts": attempts,
                    "scheduler_events": events,
                })

        jobs.sort(key=lambda row: (row["created_at"], row["job_id"]), reverse=True)

        workers: list[dict[str, Any]] = []
        for worker_id in sorted(referenced_worker_ids):
            row = self.db.one(
                "SELECT worker_id,actor_id,status,capabilities,resources_total,"
                "heartbeat_ttl_seconds,last_heartbeat_at,registered_at "
                "FROM worker_nodes WHERE worker_id=?",
                (worker_id,),
            )
            if not row:
                complete = False
                continue
            item = _parsed(row, ("capabilities", "resources_total"))
            workers.append(item)
        workers.sort(key=lambda row: (row["registered_at"], row["worker_id"]))

        return {
            "generated_at": utcnow(),
            "build_sha": build_sha,
            "query_status": "COMPLETE" if complete else "PARTIAL",
            "scope": {
                "mode": "ALL_AUTHORIZED",
                "label": "All authorized projects",
                "project_count": len(projects),
            },
            "jobs": jobs,
            "workers": workers,
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
                "actor_membership_status": direct["status"] if direct else (
                    tenant_membership["status"] if inherited else None
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
                actor_membership_status = direct["status"]
                role_source = "PROJECT"
            elif workspace_membership and workspace_membership["status"] == "ACTIVE":
                actor_role = workspace_membership["role"]
                actor_membership_status = workspace_membership["status"]
                role_source = "WORKSPACE_INHERITED"
            elif tenant_membership and tenant_membership["status"] == "ACTIVE":
                actor_role = tenant_membership["role"]
                actor_membership_status = tenant_membership["status"]
                role_source = "TENANT_INHERITED"
            else:
                actor_role = None
                actor_membership_status = None
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
                "actor_membership_status": actor_membership_status,
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

    def project_overview(self, actor_id: str, project_id: str, *, build_sha: str) -> dict[str, Any]:
        """Authorized minimal read projection for one project Overview."""
        self.runtime.tenancy.require_project_access(actor_id, project_id, "VIEW")
        project = self._project(project_id)
        scope = self.runtime.tenancy.scope_for_project(project_id)
        if not scope:
            raise NotFound("Project not found")

        complete = True
        tenant = self.db.one(
            "SELECT name FROM tenants WHERE tenant_id=? AND status='ACTIVE'",
            (scope.tenant_id,),
        )
        workspace = self.db.one(
            "SELECT name FROM workspaces WHERE workspace_id=? AND status='ACTIVE'",
            (scope.workspace_id,),
        )
        if tenant is None or workspace is None:
            complete = False

        lifecycle_row = self.db.one(
            "SELECT * FROM project_lifecycle WHERE project_id=?",
            (project_id,),
        )
        lifecycle = dict(lifecycle_row) if lifecycle_row else None
        if lifecycle is None or lifecycle.get("status") not in {"ACTIVE", "ARCHIVING", "ARCHIVED"}:
            complete = False

        domain_binding = self.db.one(
            "SELECT domain_revision_id,bound_by_actor_id,bound_at "
            "FROM project_domain_bindings WHERE project_id=?",
            (project_id,),
        )
        domain_row = self.db.one(
            "SELECT b.domain_revision_id,b.bound_by_actor_id,b.bound_at,"
            "r.revision_number,r.semantic_version,r.payload_hash,r.status AS revision_status,"
            "p.package_id,p.domain_id,p.name AS domain_name "
            "FROM project_domain_bindings b "
            "JOIN domain_package_revisions r ON r.revision_id=b.domain_revision_id "
            "JOIN domain_packages p ON p.package_id=r.package_id "
            "WHERE b.project_id=?",
            (project_id,),
        )
        if domain_binding and not domain_row:
            complete = False
        domain = dict(domain_row) if domain_row else {
            "domain_revision_id": domain_binding["domain_revision_id"] if domain_binding else None,
            "bound_by_actor_id": domain_binding["bound_by_actor_id"] if domain_binding else None,
            "bound_at": domain_binding["bound_at"] if domain_binding else None,
            "revision_number": None,
            "semantic_version": None,
            "payload_hash": None,
            "revision_status": None,
            "package_id": None,
            "domain_id": project.get("domain_id"),
            "domain_name": None,
        }

        orchestration_row = self.db.one(
            "SELECT orchestration_id,domain_id,status,current_phase_id,generation,"
            "research_outcome,pivot_count,started_at,updated_at,terminal_checkpoint_id,metadata "
            "FROM orchestrations WHERE project_id=? "
            "ORDER BY started_at DESC,orchestration_id DESC LIMIT 1",
            (project_id,),
        )
        orchestration = dict(orchestration_row) if orchestration_row else None

        phase = None
        if orchestration:
            phase_row = self.db.one(
                "SELECT phase_execution_id,orchestration_id,phase_id,phase_index,generation,"
                "workunit_id,run_id,status,decision_outcome,failure_id,checkpoint_id,"
                "started_at,finished_at "
                "FROM phase_executions WHERE orchestration_id=? "
                "ORDER BY CASE WHEN status IN ('RUNNING','PAUSED') THEN 0 ELSE 1 END,"
                "phase_index DESC,started_at DESC,phase_execution_id DESC LIMIT 1",
                (orchestration["orchestration_id"],),
            )
            phase = dict(phase_row) if phase_row else None

        running_run_row = self.db.one(
            "SELECT r.run_id,r.workunit_id,r.attempt_number,r.executor_actor_id,"
            "r.started_at,r.finished_at,r.runtime_status,w.workunit_type,w.status AS workunit_status "
            "FROM runs r JOIN workunits w ON w.workunit_id=r.workunit_id "
            "WHERE w.project_id=? AND r.runtime_status='RUNNING' "
            "ORDER BY r.started_at DESC,r.run_id DESC LIMIT 1",
            (project_id,),
        )
        active_run = dict(running_run_row) if running_run_row else None

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
        if active_run or (orchestration and orchestration["status"] == "RUNNING") or executing_jobs:
            execution_activity = "EXECUTING"
        elif orchestration and orchestration["status"] == "PAUSED":
            execution_activity = "PAUSED"
        elif ready_jobs:
            execution_activity = "QUEUED"
        else:
            execution_activity = "IDLE"

        current_actor = None
        current_actor_source = None
        if phase:
            actor_event = self.db.one(
                "SELECT actor_id,event_type,stage,created_at FROM phase_stage_events "
                "WHERE phase_execution_id=? "
                "ORDER BY created_at DESC,event_id DESC LIMIT 1",
                (phase["phase_execution_id"],),
            )
            if actor_event:
                current_actor = actor_event["actor_id"]
                current_actor_source = {
                    "kind": "PHASE_EVENT",
                    "event_type": actor_event["event_type"],
                    "stage": actor_event["stage"],
                    "at": actor_event["created_at"],
                }
        if current_actor is None and active_run:
            current_actor = active_run["executor_actor_id"]
            current_actor_source = {
                "kind": "RUN_EXECUTOR",
                "run_id": active_run["run_id"],
                "at": active_run["started_at"],
            }
        if current_actor is None:
            current_actor = "SYSTEM"
            current_actor_source = {"kind": "FALLBACK"}

        approvals = [
            dict(row)
            for row in self.db.all(
                "SELECT proposal_id,action,proposer_actor_id,payload_hash,"
                "required_approval_policy,created_at FROM proposals "
                "WHERE project_id=? AND status='PENDING_APPROVAL' "
                "ORDER BY created_at,proposal_id",
                (project_id,),
            )
        ]

        failures = []
        for failure_row in self.db.all(
            "SELECT failure_id,failure_class,detected_stage,detected_ref,root_ref,"
            "resume_candidate,severity,status,created_at FROM failures "
            "WHERE project_id=? AND status!='RESOLVED' "
            "ORDER BY created_at,failure_id",
            (project_id,),
        ):
            item = dict(failure_row)
            item["recoveries"] = [
                dict(row)
                for row in self.db.all(
                    "SELECT recovery_id,resume_target,status,created_at "
                    "FROM recoveries WHERE failure_id=? "
                    "ORDER BY created_at,recovery_id",
                    (failure_row["failure_id"],),
                )
            ]
            failures.append(item)

        handoff_row = self.db.one(
            "SELECT h.handoff_id,h.phase_execution_id,h.payload_hash,h.actor_id,h.created_at,"
            "p.phase_id,o.orchestration_id "
            "FROM phase_handoffs h "
            "JOIN phase_executions p ON p.phase_execution_id=h.phase_execution_id "
            "JOIN orchestrations o ON o.orchestration_id=p.orchestration_id "
            "WHERE o.project_id=? ORDER BY h.created_at DESC,h.handoff_id DESC LIMIT 1",
            (project_id,),
        )
        latest_handoff = dict(handoff_row) if handoff_row else None

        recent_activity = [
            dict(row)
            for row in self.db.all(
                "SELECT event_id,actor_id,action,resource_type,resource_id,reason_code,timestamp "
                "FROM audit_events WHERE project_id=? "
                "ORDER BY timestamp DESC,event_id DESC LIMIT 12",
                (project_id,),
            )
        ]

        github_bindings = []
        for row in self.db.all(
            "SELECT b.binding_id,b.connection_id,b.repository_full_name,b.default_branch,"
            "b.write_policy,b.allowed_branches,b.created_by_actor_id,b.created_at,"
            "c.status AS connection_status,c.capabilities "
            "FROM github_repository_bindings b "
            "LEFT JOIN plugin_connections c ON c.connection_id=b.connection_id "
            "WHERE b.project_id=? ORDER BY b.created_at,b.binding_id",
            (project_id,),
        ):
            item = dict(row)
            if item["connection_status"] is None:
                complete = False
            item["allowed_branches"] = parse_json(item["allowed_branches"], []) or []
            item["capabilities"] = parse_json(item["capabilities"], []) or []
            github_bindings.append(item)

        frontier = self.runtime.knowledge.get_validity_frontier(project_id)
        validity_frontier = {
            "valid_count": len(frontier.get("valid") or []),
            "non_valid_count": len(frontier.get("non_valid") or []),
            "valid_revision_ids": list(frontier.get("valid") or []),
            "non_valid": list(frontier.get("non_valid") or []),
        }

        status_counts = {
            row["status"]: int(row["n"])
            for row in self.db.all(
                "SELECT status,COUNT(*) n FROM distributed_jobs "
                "WHERE project_id=? GROUP BY status ORDER BY status",
                (project_id,),
            )
        }
        recent_jobs = [
            {
                "job_id": row["job_id"],
                "workunit_id": row["workunit_id"],
                "status": row["status"],
                "lease_worker_id": row["lease_worker_id"],
                "lease_expires_at": row["lease_expires_at"],
                "attempt_count": row["attempt_count"],
                "max_attempts": row["max_attempts"],
                "last_error": row["last_error"],
                "updated_at": row["updated_at"],
            }
            for row in self.db.all(
                "SELECT job_id,workunit_id,status,lease_worker_id,lease_expires_at,"
                "attempt_count,max_attempts,last_error,updated_at "
                "FROM distributed_jobs WHERE project_id=? "
                "ORDER BY updated_at DESC,job_id DESC LIMIT 6",
                (project_id,),
            )
        ]

        return {
            "generated_at": utcnow(),
            "build_sha": build_sha,
            "query_status": "COMPLETE" if complete else "PARTIAL",
            "project": {
                "project_id": project_id,
                "name": project["name"],
                "created_at": project["created_at"],
                "scope": {
                    "tenant_id": scope.tenant_id,
                    "tenant_name": tenant["name"] if tenant else None,
                    "workspace_id": scope.workspace_id,
                    "workspace_name": workspace["name"] if workspace else None,
                },
            },
            "lifecycle": lifecycle,
            "execution_activity": execution_activity,
            "domain": domain,
            "current_orchestration": orchestration,
            "current_phase": phase,
            "active_run": active_run,
            "current_actor": current_actor,
            "current_actor_source": current_actor_source,
            "approvals": {
                "pending_count": len(approvals),
                "pending": approvals,
            },
            "failures": {
                "open_count": len(failures),
                "open": failures,
            },
            "latest_handoff": latest_handoff,
            "recent_activity": recent_activity,
            "github": {
                "binding_count": len(github_bindings),
                "bindings": github_bindings,
            },
            "validity_frontier": validity_frontier,
            "distributed": {
                "active_jobs": sum(status_counts.get(x, 0) for x in ("READY", "LEASED", "RUNNING")),
                "status_counts": status_counts,
                "recent_jobs": recent_jobs,
            },
            "document_governance": {
                "status": "UNAVAILABLE",
                "maturity": "BPS-M09_PENDING",
                "reason": "Document browser governance is not LIVE yet; no health is inferred.",
            },
        }

    def project_execution(self, actor_id: str, project_id: str, *, build_sha: str) -> dict[str, Any]:
        """Authorized project execution index without browser-local execution truth."""
        self.runtime.tenancy.require_project_access(actor_id, project_id, "VIEW")
        overview = self.project_overview(actor_id, project_id, build_sha=build_sha)

        orchestrations: list[dict[str, Any]] = []
        for row in self.db.all(
            "SELECT orchestration_id,project_id,domain_id,status,current_phase_id,generation,"
            "research_outcome,pivot_count,started_at,updated_at,terminal_checkpoint_id "
            "FROM orchestrations WHERE project_id=? "
            "ORDER BY started_at DESC,orchestration_id DESC",
            (project_id,),
        ):
            item = dict(row)
            metadata = parse_json(item.pop("metadata"), {}) or {}
            item["history"] = list(metadata.get("history") or [])
            phases = [
                dict(phase)
                for phase in self.db.all(
                    "SELECT phase_execution_id,orchestration_id,phase_id,phase_index,generation,"
                    "workunit_id,run_id,status,decision_outcome,failure_id,checkpoint_id,"
                    "started_at,finished_at "
                    "FROM phase_executions WHERE orchestration_id=? "
                    "ORDER BY started_at,phase_index,phase_execution_id",
                    (row["orchestration_id"],),
                )
            ]
            current = next(
                (phase for phase in reversed(phases) if phase["status"] in {"RUNNING", "PAUSED"}),
                phases[-1] if phases else None,
            )
            item["current_phase_execution_id"] = (
                current["phase_execution_id"] if current else None
            )
            item["phases"] = phases
            orchestrations.append(item)

        return {
            "generated_at": utcnow(),
            "build_sha": build_sha,
            "query_status": overview["query_status"],
            "project": overview["project"],
            "lifecycle": overview["lifecycle"],
            "execution_activity": overview["execution_activity"],
            "domain": overview["domain"],
            "orchestrations": orchestrations,
        }

    @staticmethod
    def _execution_scope_contains(value: Any, identities: set[str]) -> bool:
        if isinstance(value, dict):
            return any(
                ProjectDashboardService._execution_scope_contains(child, identities)
                for child in value.values()
            )
        if isinstance(value, list):
            return any(
                ProjectDashboardService._execution_scope_contains(child, identities)
                for child in value
            )
        return isinstance(value, str) and value in identities

    def project_phase_execution(
        self,
        actor_id: str,
        project_id: str,
        phase_execution_id: str,
        *,
        build_sha: str,
    ) -> dict[str, Any]:
        """Authorized minimal browser projection for one persisted phase execution."""
        self.runtime.tenancy.require_project_access(actor_id, project_id, "VIEW")
        owner = self.db.one(
            "SELECT o.project_id FROM phase_executions p "
            "JOIN orchestrations o ON o.orchestration_id=p.orchestration_id "
            "WHERE p.phase_execution_id=?",
            (phase_execution_id,),
        )
        if not owner or owner["project_id"] != project_id:
            raise NotFound("Phase execution not found")

        source = self.runtime.process.phase_detail(phase_execution_id)
        phase = source["phase"] or {}
        workunit = source["workunit"] or None
        run = source["run"] or None
        complete = True
        if phase.get("workunit_id") and not workunit:
            complete = False
        if phase.get("run_id") and not run:
            complete = False
        if phase.get("failure_id") and not source.get("failure"):
            complete = False

        shaped_workunit = None
        if workunit:
            shaped_workunit = {
                key: workunit.get(key)
                for key in (
                    "workunit_id",
                    "project_id",
                    "workunit_type",
                    "input_revision_ids",
                    "output_contracts",
                    "preconditions",
                    "required_gates",
                    "required_authorities",
                    "executor_selector",
                    "execution_policy",
                    "retry_policy",
                    "recovery_policy",
                    "resource_conflict_keys",
                    "status",
                    "version",
                )
            }

        shaped_run = None
        if run:
            shaped_run = {
                key: run.get(key)
                for key in (
                    "run_id",
                    "workunit_id",
                    "attempt_number",
                    "executor_actor_id",
                    "input_revision_ids",
                    "started_at",
                    "finished_at",
                    "runtime_status",
                    "exit_metadata",
                    "produced_revision_ids",
                    "evidence_ids",
                    "checkpoint_id",
                    "correlation_id",
                )
            }

        gates = []
        for gate in source.get("gates") or []:
            gates.append({
                key: gate.get(key)
                for key in (
                    "gate_id",
                    "project_id",
                    "gate_type",
                    "scope",
                    "required_inputs",
                    "required_evidence",
                    "policy_version",
                    "result",
                    "violation_codes",
                    "evaluated_refs",
                    "evaluated_at",
                )
            })
        gate_ids = {gate["gate_id"] for gate in gates if gate.get("gate_id")}

        identities = {
            str(value)
            for value in (
                phase_execution_id,
                phase.get("orchestration_id"),
                phase.get("workunit_id"),
                phase.get("run_id"),
                phase.get("failure_id"),
                phase.get("checkpoint_id"),
            )
            if value
        }
        identities.update(gate_ids)

        decisions = []
        for row in self.db.all(
            "SELECT * FROM decisions WHERE project_id=? ORDER BY created_at,decision_id",
            (project_id,),
        ):
            item = _parsed(row, ("scope", "source_gate_ids", "reason_codes"))
            source_failure_id = item.get("source_failure_id")
            source_gate_ids = set(item.get("source_gate_ids") or [])
            related = bool(
                (source_failure_id and source_failure_id in identities)
                or source_gate_ids.intersection(gate_ids)
                or self._execution_scope_contains(item.get("scope"), identities)
            )
            if related:
                decisions.append({
                    key: item.get(key)
                    for key in (
                        "decision_id",
                        "project_id",
                        "scope",
                        "source_gate_ids",
                        "source_failure_id",
                        "decision_type",
                        "target_ref",
                        "reason_codes",
                        "created_at",
                        "created_by",
                    )
                })

        failure = source.get("failure")
        shaped_failure = None
        recoveries: list[dict[str, Any]] = []
        loopguard = None
        if failure:
            shaped_failure = {
                key: failure.get(key)
                for key in (
                    "failure_id",
                    "project_id",
                    "scope_id",
                    "failure_class",
                    "detected_stage",
                    "detected_ref",
                    "detected_revision_id",
                    "failed_gate_id",
                    "evidence_ids",
                    "root_ref",
                    "root_revision_id",
                    "root_status",
                    "resume_candidate",
                    "severity",
                    "signature",
                    "status",
                    "created_at",
                    "resolved_at",
                )
            }
            for row in self.db.all(
                "SELECT * FROM recoveries WHERE failure_id=? ORDER BY created_at,recovery_id",
                (failure["failure_id"],),
            ):
                recoveries.append(_parsed(
                    row,
                    (
                        "keep_valid_refs",
                        "invalidate_refs",
                        "mark_stale_refs",
                        "required_revision_actions",
                        "required_workunits",
                        "required_retests",
                        "required_approvals",
                    ),
                ))
            row = self.db.one(
                "SELECT * FROM loopguards "
                "WHERE project_id=? AND scope=? AND failure_signature=?",
                (project_id, failure["scope_id"], failure["signature"]),
            )
            loopguard = _parsed(row, ("budget",)) if row else None

        checkpoint = source.get("checkpoint")
        checkpoint_id = phase.get("checkpoint_id") or ((run or {}).get("checkpoint_id"))
        if checkpoint is None and checkpoint_id:
            checkpoint = _parsed(
                self.db.one(
                    "SELECT * FROM checkpoints WHERE checkpoint_id=? AND project_id=?",
                    (checkpoint_id, project_id),
                ),
                (
                    "active_workunit_ids",
                    "completed_workunit_ids",
                    "current_stage_labels",
                    "valid_revision_ids",
                    "dirty_revision_ids",
                    "stale_revision_ids",
                    "blocking_failure_ids",
                    "pending_decision_ids",
                    "pending_approval_ids",
                    "resume_candidates",
                    "runtime_metadata",
                ),
            )
        if checkpoint_id and checkpoint is None:
            complete = False
        if checkpoint:
            checkpoint = {
                key: checkpoint.get(key)
                for key in (
                    "checkpoint_id",
                    "project_id",
                    "scope_id",
                    "created_at",
                    "last_event_id",
                    "active_workunit_ids",
                    "completed_workunit_ids",
                    "current_stage_labels",
                    "valid_revision_ids",
                    "dirty_revision_ids",
                    "stale_revision_ids",
                    "blocking_failure_ids",
                    "pending_decision_ids",
                    "pending_approval_ids",
                    "resume_candidates",
                    "runtime_metadata",
                )
            }

        output_revision_ids = set((run or {}).get("produced_revision_ids") or [])
        impacts = []
        for row in self.db.all(
            "SELECT * FROM impacts WHERE project_id=? ORDER BY calculated_at,impact_id",
            (project_id,),
        ):
            trigger_type = row["trigger_type"]
            trigger_id = row["trigger_id"]
            attributable = bool(
                (
                    failure
                    and trigger_type == "OPERATIONAL_FAILURE"
                    and trigger_id == failure["failure_id"]
                )
                or (
                    trigger_type == "PIVOT"
                    and trigger_id in output_revision_ids
                )
            )
            if attributable:
                impacts.append(_parsed(row, ("affected_nodes", "reason_codes")))

        protocol = None
        if source.get("agent_protocol"):
            inspected = source["agent_protocol"]
            raw_protocol = inspected.get("protocol") or {}
            previous = inspected.get("previous_handoff")
            shaped_previous = None
            if previous:
                shaped_previous = {
                    key: previous.get(key)
                    for key in (
                        "phase_execution_id",
                        "previous_phase_execution_id",
                        "previous_handoff_id",
                        "handoff_hash",
                        "verified_at",
                    )
                }
                previous_handoff = previous.get("handoff")
                if previous_handoff:
                    shaped_previous["handoff"] = {
                        key: previous_handoff.get(key)
                        for key in (
                            "handoff_id",
                            "phase_execution_id",
                            "structured_payload",
                            "payload_hash",
                            "actor_id",
                            "created_at",
                            "markdown",
                        )
                    }

            plans = []
            for plan in inspected.get("plans") or []:
                plans.append({
                    "plan_id": plan.get("plan_id"),
                    "phase_execution_id": plan.get("phase_execution_id"),
                    "revision_number": plan.get("revision_number"),
                    "objective": plan.get("objective"),
                    "steps": plan.get("steps") or [],
                    "plan_hash": plan.get("plan_hash"),
                    "reason": plan.get("reason"),
                    "actor_id": plan.get("actor_id"),
                    "created_at": plan.get("created_at"),
                    "checklist": [
                        {
                            key: item.get(key)
                            for key in (
                                "checklist_item_id",
                                "plan_id",
                                "phase_execution_id",
                                "step_index",
                                "title",
                                "status",
                                "note",
                                "updated_at",
                            )
                        }
                        for item in (plan.get("checklist") or [])
                    ],
                })

            problems = []
            for problem in inspected.get("problems") or []:
                problems.append({
                    **{
                        key: problem.get(key)
                        for key in (
                            "problem_id",
                            "phase_execution_id",
                            "affected_step",
                            "code",
                            "summary",
                            "detail",
                            "severity",
                            "status",
                            "actor_id",
                            "created_at",
                        )
                    },
                    "recoveries": [
                        {
                            **{
                                key: proposal.get(key)
                                for key in (
                                    "proposal_id",
                                    "problem_id",
                                    "phase_execution_id",
                                    "action",
                                    "target_step",
                                    "plan_patch",
                                    "rationale",
                                    "risk_class",
                                    "normative_change",
                                    "status",
                                    "created_at",
                                )
                            },
                            "decisions": [
                                {
                                    key: decision.get(key)
                                    for key in (
                                        "decision_id",
                                        "proposal_id",
                                        "actor_id",
                                        "decision",
                                        "reason",
                                        "created_at",
                                    )
                                }
                                for decision in (proposal.get("decisions") or [])
                            ],
                        }
                        for proposal in (problem.get("recoveries") or [])
                    ],
                })

            protocol = {
                "protocol": {
                    key: raw_protocol.get(key)
                    for key in (
                        "protocol_id",
                        "phase_execution_id",
                        "project_id",
                        "skill_revision_id",
                        "skill_hash",
                        "recovery_mode",
                        "current_stage",
                        "status",
                        "retry_budget",
                        "retry_count",
                        "created_at",
                        "updated_at",
                    )
                },
                "previous_handoff": shaped_previous,
                "project_defaults": inspected.get("project_defaults"),
                "attention": inspected.get("attention"),
                "stage_progress": inspected.get("stage_progress"),
                "plan_progress": inspected.get("plan_progress"),
                "preflights": [
                    {
                        "preflight_id": item.get("preflight_id"),
                        "phase_execution_id": item.get("phase_execution_id"),
                        "status": item.get("status"),
                        "checks": item.get("checks") or [],
                        "checks_hash": item.get("checks_hash"),
                        "actor_id": item.get("actor_id"),
                        "created_at": item.get("created_at"),
                    }
                    for item in (inspected.get("preflights") or [])
                ],
                "plans": plans,
                "problems": problems,
                "handoffs": [
                    {
                        key: item.get(key)
                        for key in (
                            "handoff_id",
                            "phase_execution_id",
                            "structured_payload",
                            "payload_hash",
                            "actor_id",
                            "created_at",
                            "markdown",
                        )
                    }
                    for item in (inspected.get("handoffs") or [])
                ],
                "events": [
                    {
                        key: item.get(key)
                        for key in (
                            "event_id",
                            "phase_execution_id",
                            "stage",
                            "event_type",
                            "actor_id",
                            "message",
                            "metadata",
                            "created_at",
                        )
                    }
                    for item in (inspected.get("events") or [])
                ],
            }

        return {
            "generated_at": utcnow(),
            "build_sha": build_sha,
            "query_status": "COMPLETE" if complete else "PARTIAL",
            "project_id": project_id,
            "phase": {
                key: phase.get(key)
                for key in (
                    "phase_execution_id",
                    "orchestration_id",
                    "phase_id",
                    "phase_index",
                    "generation",
                    "workunit_id",
                    "run_id",
                    "status",
                    "decision_outcome",
                    "failure_id",
                    "checkpoint_id",
                    "started_at",
                    "finished_at",
                )
            },
            "workunit": shaped_workunit,
            "run": shaped_run,
            "gates": gates,
            "decisions": decisions,
            "failure": shaped_failure,
            "recoveries": recoveries,
            "loopguard": loopguard,
            "checkpoint": checkpoint,
            "impacts": impacts,
            "events": source.get("events") or [],
            "agent_protocol": protocol,
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
