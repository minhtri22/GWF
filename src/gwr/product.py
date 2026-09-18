from __future__ import annotations

from typing import Any

from .errors import NotFound
from .utils import parse_json


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
            "product_version": "0.8.1",
            "project": project,
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
