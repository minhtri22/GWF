from __future__ import annotations

from typing import Any

from .errors import NotFound
from .utils import parse_json


def _parse(row, fields=()):
    if row is None:
        return None
    out = dict(row)
    for f in fields:
        if f in out:
            out[f] = parse_json(out[f], None)
    return out


class ProcessInspectorService:
    """Chronological process read model assembled from authoritative runtime records."""

    def __init__(self, runtime):
        self.runtime = runtime
        self.db = runtime.db

    def process(self, project_id: str) -> dict[str, Any]:
        project = self.db.one("SELECT * FROM projects WHERE id=?", (project_id,))
        if not project:
            raise NotFound("Project not found")
        orchestrations = []
        for o in self.db.all("SELECT * FROM orchestrations WHERE project_id=? ORDER BY started_at DESC", (project_id,)):
            item = _parse(o, ("metadata",))
            phases = [
                _parse(p, ("metadata",))
                for p in self.db.all("SELECT * FROM phase_executions WHERE orchestration_id=? ORDER BY started_at,phase_execution_id", (o["orchestration_id"],))
            ]
            item["phases"] = phases
            item["current_phase"] = next((p for p in reversed(phases) if p["status"] in {"RUNNING","PAUSED"}), phases[-1] if phases else None)
            orchestrations.append(item)
        latest = orchestrations[0] if orchestrations else None
        current = latest.get("current_phase") if latest else None
        protocol = None
        if current and self.db.one("SELECT 1 FROM phase_execution_protocols WHERE phase_execution_id=?", (current["phase_execution_id"],)):
            protocol = self.runtime.agent_protocol.inspect(current["phase_execution_id"])
        return {
            "project_id": project_id,
            "status": latest["status"] if latest else "READY",
            "current_phase": current,
            "current_agent_protocol": protocol,
            "attention": protocol["attention"] if protocol else ("COMPLETE" if latest and latest["status"] == "COMPLETED" else "IDLE"),
            "orchestrations": orchestrations,
            "domain_binding": self.runtime.domains.project_binding(project_id),
            "project_lifecycle": self.runtime.project_governance.status(project_id),
        }

    def phases(self, orchestration_id: str) -> list[dict[str, Any]]:
        if not self.db.one("SELECT 1 FROM orchestrations WHERE orchestration_id=?", (orchestration_id,)):
            raise NotFound("Orchestration not found")
        return [
            _parse(r, ("metadata",))
            for r in self.db.all("SELECT * FROM phase_executions WHERE orchestration_id=? ORDER BY started_at,phase_execution_id", (orchestration_id,))
        ]

    def phase_detail(self, phase_execution_id: str) -> dict[str, Any]:
        phase = self.db.one(
            "SELECT p.*,o.project_id FROM phase_executions p JOIN orchestrations o "
            "ON o.orchestration_id=p.orchestration_id WHERE p.phase_execution_id=?",
            (phase_execution_id,),
        )
        if not phase:
            raise NotFound("Phase execution not found")
        phase_d = _parse(phase, ("metadata",))
        run = _parse(self.db.one("SELECT * FROM runs WHERE run_id=?", (phase["run_id"],)) if phase["run_id"] else None,
                     ("input_revision_ids","exit_metadata","produced_revision_ids","evidence_ids"))
        workunit = _parse(self.db.one("SELECT * FROM workunits WHERE workunit_id=?", (phase["workunit_id"],)) if phase["workunit_id"] else None,
                          ("input_revision_ids","output_contracts","preconditions","required_gates","required_authorities","executor_selector","execution_policy","retry_policy","recovery_policy","resource_conflict_keys"))
        evidence = []
        if run:
            for eid in run.get("evidence_ids") or []:
                row = self.db.one("SELECT * FROM evidence WHERE evidence_id=?", (eid,))
                if row:
                    evidence.append(_parse(row, ("subject_refs","structured_payload","freshness_metadata")))
        artifacts = []
        if run:
            for rid in run.get("produced_revision_ids") or []:
                row = self.db.one(
                    "SELECT r.*,a.artifact_type,a.logical_key FROM revisions r JOIN artifacts a "
                    "ON a.artifact_id=r.artifact_id WHERE r.revision_id=?",
                    (rid,),
                )
                if row:
                    artifacts.append(_parse(row, ("structured_payload",)))
        gates = [
            _parse(g, ("scope","required_inputs","required_evidence","violation_codes","evaluated_refs"))
            for g in self.db.all("SELECT * FROM gates WHERE project_id=? ORDER BY evaluated_at", (phase["project_id"],))
            if phase["run_id"] and phase["run_id"] in (parse_json(g["evaluated_refs"], []) or [])
               or phase["workunit_id"] and phase["workunit_id"] in str(g["scope"])
        ]
        failure = _parse(self.db.one("SELECT * FROM failures WHERE failure_id=?", (phase["failure_id"],)) if phase["failure_id"] else None, ("evidence_ids",))
        checkpoint = _parse(self.db.one("SELECT * FROM checkpoints WHERE checkpoint_id=?", (phase["checkpoint_id"],)) if phase["checkpoint_id"] else None,
                            ("active_workunit_ids","completed_workunit_ids","current_stage_labels","valid_revision_ids","dirty_revision_ids","stale_revision_ids","blocking_failure_ids","pending_decision_ids","pending_approval_ids","resume_candidates","runtime_metadata"))
        agent_protocol = None
        if self.db.one("SELECT 1 FROM phase_execution_protocols WHERE phase_execution_id=?", (phase_execution_id,)):
            agent_protocol = self.runtime.agent_protocol.inspect(phase_execution_id)
        return {
            "phase": phase_d,
            "workunit": workunit,
            "run": run,
            "inputs": self._input_revisions(run),
            "outputs": artifacts,
            "evidence": evidence,
            "gates": gates,
            "failure": failure,
            "checkpoint": checkpoint,
            "events": self.phase_events(phase_execution_id),
            "agent_protocol": agent_protocol,
        }

    def _input_revisions(self, run):
        out = []
        if not run:
            return out
        for rid in run.get("input_revision_ids") or []:
            row = self.db.one(
                "SELECT r.*,a.artifact_type,a.logical_key FROM revisions r JOIN artifacts a "
                "ON a.artifact_id=r.artifact_id WHERE r.revision_id=?",
                (rid,),
            )
            if row:
                out.append(_parse(row, ("structured_payload",)))
        return out

    def phase_events(self, phase_execution_id: str) -> list[dict[str, Any]]:
        phase = self.db.one(
            "SELECT p.*,o.project_id FROM phase_executions p JOIN orchestrations o "
            "ON o.orchestration_id=p.orchestration_id WHERE p.phase_execution_id=?",
            (phase_execution_id,),
        )
        if not phase:
            raise NotFound("Phase execution not found")
        events = []
        events.append({"timestamp": phase["started_at"], "event": "PHASE_STARTED", "ref": phase["phase_id"], "source": "phase"})
        if phase["run_id"]:
            run = self.db.one("SELECT * FROM runs WHERE run_id=?", (phase["run_id"],))
            if run:
                events.append({"timestamp": run["started_at"], "event": "RUN_STARTED", "ref": run["run_id"], "source": "run"})
                if run["finished_at"]:
                    events.append({"timestamp": run["finished_at"], "event": f"RUN_{run['runtime_status']}", "ref": run["run_id"], "source": "run"})
            for a in self.db.all("SELECT * FROM audit_events WHERE project_id=? AND run_id=? ORDER BY timestamp", (phase["project_id"], phase["run_id"])):
                events.append({"timestamp": a["timestamp"], "event": a["action"], "ref": a["resource_id"], "source": "audit", "reason": a["reason_code"]})
        if phase["failure_id"]:
            f = self.db.one("SELECT * FROM failures WHERE failure_id=?", (phase["failure_id"],))
            if f:
                events.append({"timestamp": f["created_at"], "event": "FAILURE_RECORDED", "ref": f["failure_id"], "source": "failure", "reason": f["failure_class"]})
        if phase["checkpoint_id"]:
            c = self.db.one("SELECT * FROM checkpoints WHERE checkpoint_id=?", (phase["checkpoint_id"],))
            if c:
                events.append({"timestamp": c["created_at"], "event": "CHECKPOINT_CREATED", "ref": c["checkpoint_id"], "source": "checkpoint"})
        if phase["finished_at"]:
            events.append({"timestamp": phase["finished_at"], "event": f"PHASE_{phase['status']}", "ref": phase["phase_id"], "source": "phase"})
        events.sort(key=lambda e: (e.get("timestamp") or "", e["event"], e["ref"] or ""))
        return events
