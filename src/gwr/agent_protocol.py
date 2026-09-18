from __future__ import annotations

from typing import Any

from .errors import AuthorityDenied, InvalidTransition, NotFound, ValidationError
from .utils import canonical_json, content_hash, parse_json, uid, utcnow


STAGES = ["LOAD", "PREFLIGHT", "PLAN", "EXECUTE", "VERIFY", "HANDOFF", "COMPLETE"]


class AgentExecutionProtocolService:
    """Observable, persistent protocol for one agent-executed phase.

    The service records operational state only: skill, preflight, plan, checklist,
    events, problems, recovery decisions and handoff. It never stores or exposes
    hidden model chain-of-thought.
    """

    def __init__(self, db, governance, project_governance, domain=None):
        self.db = db
        self.gov = governance
        self.projects = project_governance
        self.domain = domain

    def bootstrap_domain_skills(self) -> list[dict[str, Any]]:
        """Materialize declarative domain skill contracts into immutable registry revisions.

        The runtime never resolves a SKILL.md file path during execution. A workunit is
        bound to an exact skill revision/hash once the domain package is loaded.
        """
        if self.domain is None:
            return []
        contracts = self.domain.data.get("skill_contracts", {}) or {}
        bound = []
        with self.db.tx():
            for workunit in self.domain.workunits():
                skill_ref = workunit.get("skill_ref")
                if not skill_ref:
                    continue
                contract = contracts.get(skill_ref)
                if not contract:
                    raise ValidationError(f"Missing domain skill contract {skill_ref}")
                public_skill_id = str(contract.get("skill_id") or skill_ref)
                skill_id = f"{self.domain.domain_id}:{public_skill_id}"
                package = self.db.one("SELECT * FROM skill_packages WHERE skill_id=?", (skill_id,))
                if not package:
                    package_id = uid("skillpkg")
                    self.db.conn.execute(
                        "INSERT INTO skill_packages VALUES(?,?,?,?,?,?)",
                        (package_id, skill_id, public_skill_id.replace("-", " ").title(),
                         f"Domain-pinned skill for {self.domain.domain_id}", "SYSTEM", utcnow()),
                    )
                    package = self.db.one("SELECT * FROM skill_packages WHERE skill_package_id=?", (package_id,))
                payload = {
                    "skill_id": skill_id,
                    "version": str(contract["version"]),
                    "markdown": str(contract["markdown"]),
                    "tool_requirements": list(contract.get("tool_requirements", []) or []),
                    "qa_contract": dict(contract.get("qa_contract", {}) or {}),
                }
                skill_hash = content_hash(payload)
                revision = self.db.one(
                    "SELECT * FROM skill_revisions WHERE skill_package_id=? AND content_hash=? ORDER BY revision_number DESC LIMIT 1",
                    (package["skill_package_id"], skill_hash),
                )
                if not revision:
                    revno = self.db.one(
                        "SELECT COALESCE(MAX(revision_number),0)+1 n FROM skill_revisions WHERE skill_package_id=?",
                        (package["skill_package_id"],),
                    )["n"]
                    revision_id = uid("skillrev")
                    self.db.conn.execute(
                        "INSERT INTO skill_revisions VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (revision_id, package["skill_package_id"], int(revno), payload["version"], payload["markdown"],
                         skill_hash, canonical_json(payload["tool_requirements"]), canonical_json(payload["qa_contract"]),
                         "SYSTEM", utcnow()),
                    )
                    revision = self.db.one("SELECT * FROM skill_revisions WHERE skill_revision_id=?", (revision_id,))
                binding = self.db.one(
                    "SELECT * FROM domain_skill_bindings WHERE domain_id=? AND workunit_type=?",
                    (self.domain.domain_id, workunit["id"]),
                )
                required_tools = canonical_json(payload["tool_requirements"])
                qa_contract = canonical_json(payload["qa_contract"])
                if binding:
                    self.db.conn.execute(
                        "UPDATE domain_skill_bindings SET skill_revision_id=?,skill_hash=?,required_tools=?,qa_contract=?,created_at=? "
                        "WHERE binding_id=?",
                        (revision["skill_revision_id"], skill_hash, required_tools, qa_contract, utcnow(), binding["binding_id"]),
                    )
                    binding_id = binding["binding_id"]
                else:
                    binding_id = uid("skillbind")
                    self.db.conn.execute(
                        "INSERT INTO domain_skill_bindings VALUES(?,?,?,?,?,?,?,?)",
                        (binding_id, self.domain.domain_id, workunit["id"], revision["skill_revision_id"], skill_hash,
                         required_tools, qa_contract, utcnow()),
                    )
                bound.append({
                    "binding_id": binding_id,
                    "workunit_type": workunit["id"],
                    "skill_ref": skill_ref,
                    "skill_revision_id": revision["skill_revision_id"],
                    "skill_hash": skill_hash,
                    "required_tools": payload["tool_requirements"],
                    "qa_contract": payload["qa_contract"],
                })
        return bound

    def resolve_skill_revision(self, workunit_type: str) -> dict[str, Any]:
        if self.domain is None:
            raise ValidationError("Domain skill resolution is unavailable")
        row = self.db.one(
            "SELECT * FROM domain_skill_bindings WHERE domain_id=? AND workunit_type=?",
            (self.domain.domain_id, workunit_type),
        )
        if not row:
            raise NotFound(f"No pinned skill binding for {workunit_type}")
        revision = self.db.one("SELECT * FROM skill_revisions WHERE skill_revision_id=?", (row["skill_revision_id"],))
        if not revision:
            raise NotFound("Pinned skill revision not found")
        if revision["content_hash"] != row["skill_hash"]:
            raise InvalidTransition("Pinned skill hash mismatch")
        item = dict(row)
        item["required_tools"] = parse_json(item["required_tools"], [])
        item["qa_contract"] = parse_json(item["qa_contract"], {})
        item["version"] = revision["version"]
        item["markdown"] = revision["markdown"]
        return item

    def set_project_defaults(self, project_id: str, actor_id: str, *, recovery_mode: str | None = None, retry_budget: int | None = None) -> dict[str, Any]:
        self.projects.require_mutable(project_id)
        scope = self.projects.tenancy.scope_for_project(project_id)
        if scope:
            self.projects.tenancy.require_project_access(actor_id, project_id, "MANAGE_MEMBERS")
        elif actor_id != "SYSTEM":
            self.gov.authorize(actor_id, "PROPOSE", {"project_id": project_id, "action": "MANAGE_PROJECT"})
        if recovery_mode is not None and recovery_mode not in {"AUTO", "HUMAN_APPROVE"}:
            raise ValidationError("recovery_mode must be AUTO or HUMAN_APPROVE")
        if retry_budget is not None and int(retry_budget) < 0:
            raise ValidationError("retry_budget must be >= 0")
        existing = self.db.one("SELECT * FROM project_agent_protocol_settings WHERE project_id=?", (project_id,))
        now = utcnow()
        with self.db.tx():
            if existing:
                self.db.conn.execute(
                    "UPDATE project_agent_protocol_settings SET recovery_mode=?,retry_budget=?,updated_by_actor_id=?,updated_at=? WHERE project_id=?",
                    (recovery_mode, retry_budget, actor_id, now, project_id),
                )
            else:
                self.db.conn.execute(
                    "INSERT INTO project_agent_protocol_settings VALUES(?,?,?,?,?)",
                    (project_id, recovery_mode, retry_budget, actor_id, now),
                )
            self.gov.append_audit(
                project_id, actor_id, "PROJECT_AGENT_PROTOCOL_DEFAULTS_UPDATED", "Project", project_id,
                metadata={"recovery_mode": recovery_mode, "retry_budget": retry_budget},
            )
        return self.project_defaults(project_id)

    def project_defaults(self, project_id: str) -> dict[str, Any]:
        row = self.db.one("SELECT * FROM project_agent_protocol_settings WHERE project_id=?", (project_id,))
        return dict(row) if row else {"project_id": project_id, "recovery_mode": None, "retry_budget": None}

    def resolve_recovery_config(
        self,
        project_id: str,
        workunit_type: str,
        *,
        requested_mode: str | None = None,
        requested_retry_budget: int | None = None,
    ) -> dict[str, Any]:
        domain_cfg = (self.domain.data.get("agent_protocol", {}) if self.domain else {}) or {}
        phase_cfg = (self.domain.workunit(workunit_type).get("agent_protocol", {}) if self.domain and self.domain.workunit(workunit_type) else {}) or {}
        project_cfg = self.project_defaults(project_id)
        mode = requested_mode or phase_cfg.get("recovery_mode") or project_cfg.get("recovery_mode") or domain_cfg.get("default_recovery_mode", "AUTO")
        domain_minimum = domain_cfg.get("minimum_recovery_mode", "AUTO")
        phase_minimum = phase_cfg.get("minimum_recovery_mode", "AUTO")
        minimum = "HUMAN_APPROVE" if "HUMAN_APPROVE" in {domain_minimum, phase_minimum} else "AUTO"
        if minimum == "HUMAN_APPROVE":
            mode = "HUMAN_APPROVE"
        if mode not in {"AUTO", "HUMAN_APPROVE"}:
            raise ValidationError("Effective recovery_mode must be AUTO or HUMAN_APPROVE")
        budget = requested_retry_budget
        if budget is None:
            budget = phase_cfg.get("retry_budget")
        if budget is None:
            budget = project_cfg.get("retry_budget")
        if budget is None:
            budget = domain_cfg.get("default_retry_budget", 2)
        budget = int(budget)
        if budget < 0:
            raise ValidationError("Effective retry_budget must be >= 0")
        return {
            "recovery_mode": mode,
            "retry_budget": budget,
            "domain_minimum": minimum,
            "source": {
                "requested": requested_mode,
                "phase": phase_cfg.get("recovery_mode"),
                "project": project_cfg.get("recovery_mode"),
                "domain_default": domain_cfg.get("default_recovery_mode", "AUTO"),
                "domain_minimum": domain_minimum,
                "phase_minimum": phase_minimum,
            },
        }

    def bind_previous_handoff(self, phase_execution_id: str, previous_phase_execution_id: str | None, actor_id: str) -> dict[str, Any]:
        phase = self._phase(phase_execution_id)
        self.projects.require_mutable(phase["project_id"])
        existing = self.db.one("SELECT * FROM phase_handoff_links WHERE phase_execution_id=?", (phase_execution_id,))
        if existing:
            return dict(existing)
        previous_handoff_id = None
        handoff_hash = None
        event_type = "PREVIOUS_HANDOFF_NOT_REQUIRED"
        metadata: dict[str, Any] = {}
        if previous_phase_execution_id:
            previous = self.db.one(
                "SELECT h.*,p.status protocol_status FROM phase_handoffs h "
                "JOIN phase_execution_protocols p ON p.phase_execution_id=h.phase_execution_id "
                "WHERE h.phase_execution_id=? ORDER BY h.created_at DESC LIMIT 1",
                (previous_phase_execution_id,),
            )
            if not previous or previous["protocol_status"] != "COMPLETED":
                raise InvalidTransition("Required previous handoff is missing or protocol is incomplete")
            payload = parse_json(previous["structured_payload"], {})
            calculated = content_hash(payload)
            if calculated != previous["payload_hash"]:
                raise InvalidTransition("Previous handoff hash mismatch")
            previous_handoff_id = previous["handoff_id"]
            handoff_hash = previous["payload_hash"]
            event_type = "PREVIOUS_HANDOFF_VERIFIED"
            metadata = {
                "previous_phase_execution_id": previous_phase_execution_id,
                "previous_handoff_id": previous_handoff_id,
                "handoff_hash": handoff_hash,
            }
        with self.db.tx():
            self.db.conn.execute(
                "INSERT INTO phase_handoff_links VALUES(?,?,?,?,?)",
                (phase_execution_id, previous_phase_execution_id, previous_handoff_id, handoff_hash, utcnow()),
            )
            self._event(phase_execution_id, "LOAD", event_type, actor_id, "Previous handoff verified" if previous_phase_execution_id else "No previous handoff required", metadata)
        return dict(self.db.one("SELECT * FROM phase_handoff_links WHERE phase_execution_id=?", (phase_execution_id,)))

    def previous_handoff(self, phase_execution_id: str) -> dict[str, Any] | None:
        link = self.db.one("SELECT * FROM phase_handoff_links WHERE phase_execution_id=?", (phase_execution_id,))
        if not link:
            return None
        item = dict(link)
        if item.get("previous_handoff_id"):
            handoff = self.db.one("SELECT * FROM phase_handoffs WHERE handoff_id=?", (item["previous_handoff_id"],))
            if handoff:
                item["handoff"] = dict(handoff)
                item["handoff"]["structured_payload"] = parse_json(item["handoff"]["structured_payload"], {})
        return item

    def _phase(self, phase_execution_id: str):
        row = self.db.one(
            "SELECT p.*,o.project_id FROM phase_executions p JOIN orchestrations o "
            "ON o.orchestration_id=p.orchestration_id WHERE p.phase_execution_id=?",
            (phase_execution_id,),
        )
        if not row:
            raise NotFound("Phase execution not found")
        return row

    def _protocol(self, phase_execution_id: str):
        row = self.db.one("SELECT * FROM phase_execution_protocols WHERE phase_execution_id=?", (phase_execution_id,))
        if not row:
            raise NotFound("Agent execution protocol not found")
        return row

    def _event(self, phase_execution_id: str, stage: str, event_type: str, actor_id: str, message: str = "", metadata=None):
        eid = uid("phaseevt")
        self.db.conn.execute(
            "INSERT INTO phase_stage_events VALUES(?,?,?,?,?,?,?,?)",
            (eid, phase_execution_id, stage, event_type, actor_id, message, canonical_json(metadata or {}), utcnow()),
        )
        return eid

    def create_skill_package(self, skill_id: str, name: str, actor_id: str, *, description: str = "") -> str:
        if not skill_id or not name:
            raise ValidationError("skill_id and name are required")
        if self.db.one("SELECT 1 FROM skill_packages WHERE skill_id=?", (skill_id,)):
            raise ValidationError("Skill package already exists")
        sid = uid("skillpkg")
        self.db.conn.execute(
            "INSERT INTO skill_packages VALUES(?,?,?,?,?,?)",
            (sid, skill_id, name, description, actor_id, utcnow()),
        )
        self.db.conn.commit()
        return sid

    def add_skill_revision(self, skill_package_id: str, version: str, markdown: str, actor_id: str, *, tool_requirements=None, qa_contract=None) -> str:
        if not markdown.strip():
            raise ValidationError("SKILL.md content is required")
        pkg = self.db.one("SELECT * FROM skill_packages WHERE skill_package_id=?", (skill_package_id,))
        if not pkg:
            raise NotFound("Skill package not found")
        revno = self.db.one(
            "SELECT COALESCE(MAX(revision_number),0)+1 n FROM skill_revisions WHERE skill_package_id=?",
            (skill_package_id,),
        )["n"]
        rid = uid("skillrev")
        payload = {
            "skill_id": pkg["skill_id"], "version": version, "markdown": markdown,
            "tool_requirements": tool_requirements or [], "qa_contract": qa_contract or {},
        }
        self.db.conn.execute(
            "INSERT INTO skill_revisions VALUES(?,?,?,?,?,?,?,?,?,?)",
            (rid, skill_package_id, int(revno), version, markdown, content_hash(payload),
             canonical_json(tool_requirements or []), canonical_json(qa_contract or {}), actor_id, utcnow()),
        )
        self.db.conn.commit()
        return rid

    def create_protocol(
        self,
        phase_execution_id: str,
        skill_revision_id: str,
        actor_id: str,
        *,
        recovery_mode: str | None = None,
        retry_budget: int | None = None,
        enforce_domain_binding: bool = False,
    ) -> str:
        phase = self._phase(phase_execution_id)
        self.projects.require_mutable(phase["project_id"])
        self.gov.authorize(actor_id, "EXECUTE", {"project_id": phase["project_id"]})
        skill = self.db.one("SELECT * FROM skill_revisions WHERE skill_revision_id=?", (skill_revision_id,))
        if not skill:
            raise NotFound("Skill revision not found")
        binding = None
        if enforce_domain_binding:
            binding = self.resolve_skill_revision(phase["phase_id"])
            if binding["skill_revision_id"] != skill_revision_id or binding["skill_hash"] != skill["content_hash"]:
                raise InvalidTransition("Phase skill revision does not match the domain-pinned binding")
        effective = self.resolve_recovery_config(
            phase["project_id"], phase["phase_id"],
            requested_mode=recovery_mode, requested_retry_budget=retry_budget,
        )
        existing = self.db.one("SELECT * FROM phase_execution_protocols WHERE phase_execution_id=?", (phase_execution_id,))
        if existing:
            return existing["protocol_id"]
        pid = uid("protocol")
        with self.db.tx():
            self.db.conn.execute(
                "INSERT INTO phase_execution_protocols VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (pid, phase_execution_id, phase["project_id"], skill_revision_id, skill["content_hash"], effective["recovery_mode"],
                 "LOAD", "RUNNING", int(effective["retry_budget"]), 0, utcnow(), utcnow()),
            )
            self._event(
                phase_execution_id, "LOAD", "SKILL_LOADED", actor_id, "Skill revision loaded",
                {
                    "skill_revision_id": skill_revision_id,
                    "skill_hash": skill["content_hash"],
                    "domain_binding_enforced": bool(enforce_domain_binding),
                    "required_tools": binding["required_tools"] if binding else parse_json(skill["tool_requirements"], []),
                    "qa_contract": binding["qa_contract"] if binding else parse_json(skill["qa_contract"], {}),
                    "recovery": effective,
                },
            )
        return pid

    def record_preflight(self, phase_execution_id: str, checks: list[dict[str, Any]], actor_id: str) -> dict[str, Any]:
        protocol = self._protocol(phase_execution_id)
        if protocol["current_stage"] not in {"LOAD", "PREFLIGHT"}:
            raise InvalidTransition("Preflight must occur before planning")
        normalized = []
        ok = True
        for idx, check in enumerate(checks):
            passed = bool(check.get("pass"))
            ok = ok and passed
            normalized.append({
                "index": idx,
                "name": str(check.get("name") or f"check_{idx+1}"),
                "pass": passed,
                "detail": str(check.get("detail") or ""),
            })
        if not normalized:
            raise ValidationError("At least one preflight check is required")
        pfid = uid("preflight")
        status = "PASS" if ok else "BLOCKED"
        with self.db.tx():
            self.db.conn.execute(
                "INSERT INTO phase_preflights VALUES(?,?,?,?,?,?,?)",
                (pfid, phase_execution_id, status, canonical_json(normalized), content_hash(normalized), actor_id, utcnow()),
            )
            self.db.conn.execute(
                "UPDATE phase_execution_protocols SET current_stage='PREFLIGHT',status=?,updated_at=? WHERE phase_execution_id=?",
                ("RUNNING" if ok else "BLOCKED", utcnow(), phase_execution_id),
            )
            self._event(phase_execution_id, "PREFLIGHT", f"PREFLIGHT_{status}", actor_id,
                        "Preflight passed" if ok else "Preflight blocked", {"checks": normalized})
        return {"preflight_id": pfid, "status": status, "checks": normalized}

    def create_plan(self, phase_execution_id: str, objective: str, steps: list[dict[str, Any]], actor_id: str, *, reason: str = "INITIAL_PLAN") -> str:
        protocol = self._protocol(phase_execution_id)
        pre = self.db.one("SELECT * FROM phase_preflights WHERE phase_execution_id=? ORDER BY created_at DESC LIMIT 1", (phase_execution_id,))
        if not pre or pre["status"] != "PASS":
            raise InvalidTransition("NO PREFLIGHT PASS -> NO PLAN")
        if protocol["status"] == "WAITING_HUMAN":
            raise InvalidTransition("Protocol is waiting for human decision")
        if not objective.strip() or not steps:
            raise ValidationError("Plan objective and steps are required")
        revno = self.db.one("SELECT COALESCE(MAX(revision_number),0)+1 n FROM phase_plans WHERE phase_execution_id=?", (phase_execution_id,))["n"]
        normalized = []
        for idx, step in enumerate(steps, start=1):
            normalized.append({
                "step_index": idx,
                "title": str(step.get("title") or f"Step {idx}"),
                "description": str(step.get("description") or ""),
                "expected_output": step.get("expected_output"),
                "expected_evidence": step.get("expected_evidence"),
            })
        plan_id = uid("plan")
        plan_hash = content_hash({"objective": objective, "steps": normalized})
        with self.db.tx():
            self.db.conn.execute(
                "INSERT INTO phase_plans VALUES(?,?,?,?,?,?,?,?,?)",
                (plan_id, phase_execution_id, int(revno), objective, canonical_json(normalized), plan_hash,
                 reason, actor_id, utcnow()),
            )
            for step in normalized:
                self.db.conn.execute(
                    "INSERT INTO phase_checklist_items VALUES(?,?,?,?,?,?,?,?)",
                    (uid("check"), plan_id, phase_execution_id, step["step_index"], step["title"], "PENDING", "", utcnow()),
                )
            self.db.conn.execute(
                "UPDATE phase_execution_protocols SET current_stage='PLAN',status='RUNNING',updated_at=? WHERE phase_execution_id=?",
                (utcnow(), phase_execution_id),
            )
            self._event(phase_execution_id, "PLAN", "PLAN_FROZEN", actor_id, f"Plan revision {revno} frozen",
                        {"plan_id": plan_id, "plan_hash": plan_hash, "reason": reason})
        return plan_id

    def start_execution(self, phase_execution_id: str, actor_id: str):
        protocol = self._protocol(phase_execution_id)
        latest = self.db.one("SELECT * FROM phase_plans WHERE phase_execution_id=? ORDER BY revision_number DESC LIMIT 1", (phase_execution_id,))
        if not latest:
            raise InvalidTransition("NO PLAN -> NO EXECUTION")
        if protocol["status"] == "WAITING_HUMAN":
            raise InvalidTransition("Protocol is waiting for human approval")
        with self.db.tx():
            self.db.conn.execute(
                "UPDATE phase_execution_protocols SET current_stage='EXECUTE',status='RUNNING',updated_at=? WHERE phase_execution_id=?",
                (utcnow(), phase_execution_id),
            )
            self._event(phase_execution_id, "EXECUTE", "EXECUTION_STARTED", actor_id, "Plan execution started",
                        {"plan_id": latest["plan_id"], "revision_number": latest["revision_number"]})

    def update_step(self, phase_execution_id: str, step_index: int, status: str, actor_id: str, *, note: str = ""):
        if status not in {"PENDING", "RUNNING", "PASS", "FAIL", "SKIPPED"}:
            raise ValidationError("Invalid checklist status")
        protocol = self._protocol(phase_execution_id)
        if protocol["current_stage"] not in {"EXECUTE", "VERIFY"}:
            raise InvalidTransition("Checklist steps may only change during execution/verification")
        plan = self.db.one("SELECT * FROM phase_plans WHERE phase_execution_id=? ORDER BY revision_number DESC LIMIT 1", (phase_execution_id,))
        row = self.db.one("SELECT * FROM phase_checklist_items WHERE plan_id=? AND step_index=?", (plan["plan_id"], int(step_index)))
        if not row:
            raise NotFound("Plan step not found")
        with self.db.tx():
            self.db.conn.execute(
                "UPDATE phase_checklist_items SET status=?,note=?,updated_at=? WHERE checklist_item_id=?",
                (status, note, utcnow(), row["checklist_item_id"]),
            )
            self._event(phase_execution_id, "EXECUTE", f"STEP_{status}", actor_id, row["title"],
                        {"step_index": int(step_index), "note": note})

    def record_problem(self, phase_execution_id: str, actor_id: str, *, code: str, summary: str, detail: str, affected_step: int | None = None, severity: str = "MEDIUM") -> str:
        protocol = self._protocol(phase_execution_id)
        if protocol["current_stage"] not in {"PREFLIGHT", "PLAN", "EXECUTE", "VERIFY"}:
            raise InvalidTransition("Problems may only be recorded during active protocol stages")
        problem_id = uid("problem")
        with self.db.tx():
            self.db.conn.execute(
                "INSERT INTO phase_problem_records VALUES(?,?,?,?,?,?,?,?,?,?)",
                (problem_id, phase_execution_id, affected_step, code, summary, detail, severity, "OPEN", actor_id, utcnow()),
            )
            self.db.conn.execute(
                "UPDATE phase_execution_protocols SET status='ISSUE',updated_at=? WHERE phase_execution_id=?",
                (utcnow(), phase_execution_id),
            )
            self._event(phase_execution_id, protocol["current_stage"], "PROBLEM_RECORDED", actor_id, summary,
                        {"problem_id": problem_id, "code": code, "affected_step": affected_step, "severity": severity})
        return problem_id

    def propose_recovery(self, problem_id: str, actor_id: str, *, action: str, target_step: int | None = None, rationale: str = "", plan_patch=None, risk_class: str = "LOW", normative_change: bool = False) -> dict[str, Any]:
        problem = self.db.one(
            "SELECT p.*,x.recovery_mode,x.retry_budget,x.retry_count,x.project_id,x.current_stage "
            "FROM phase_problem_records p JOIN phase_execution_protocols x ON x.phase_execution_id=p.phase_execution_id "
            "WHERE p.problem_id=?",
            (problem_id,),
        )
        if not problem:
            raise NotFound("Problem not found")
        if problem["status"] != "OPEN":
            raise InvalidTransition("Problem is not open")
        if risk_class not in {"LOW", "MEDIUM", "HIGH"}:
            raise ValidationError("risk_class must be LOW, MEDIUM or HIGH")
        auto_allowed = (
            problem["recovery_mode"] == "AUTO"
            and risk_class == "LOW"
            and not normative_change
            and int(problem["retry_count"]) < int(problem["retry_budget"])
        )
        status = "AUTO_APPROVED" if auto_allowed else "WAITING_HUMAN"
        rid = uid("recoveryprop")
        payload = {
            "action": action, "target_step": target_step, "rationale": rationale,
            "plan_patch": plan_patch or [], "risk_class": risk_class, "normative_change": normative_change,
        }
        with self.db.tx():
            self.db.conn.execute(
                "INSERT INTO phase_recovery_proposals VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (rid, problem_id, problem["phase_execution_id"], action, target_step, canonical_json(plan_patch or []),
                 rationale, risk_class, 1 if normative_change else 0, status, utcnow()),
            )
            self.db.conn.execute(
                "UPDATE phase_execution_protocols SET status=?,updated_at=? WHERE phase_execution_id=?",
                ("RUNNING" if auto_allowed else "WAITING_HUMAN", utcnow(), problem["phase_execution_id"]),
            )
            self._event(problem["phase_execution_id"], problem["current_stage"],
                        "RECOVERY_AUTO_APPROVED" if auto_allowed else "RECOVERY_WAITING_HUMAN",
                        actor_id, rationale or action, {"proposal_id": rid, **payload})
        return {"proposal_id": rid, "status": status, "auto_allowed": auto_allowed, "payload_hash": content_hash(payload)}

    def decide_recovery(self, proposal_id: str, actor_id: str, decision: str, *, reason: str = "") -> str:
        proposal = self.db.one(
            "SELECT r.*,p.phase_execution_id,x.project_id FROM phase_recovery_proposals r "
            "JOIN phase_problem_records p ON p.problem_id=r.problem_id "
            "JOIN phase_execution_protocols x ON x.phase_execution_id=p.phase_execution_id WHERE r.proposal_id=?",
            (proposal_id,),
        )
        if not proposal:
            raise NotFound("Recovery proposal not found")
        if proposal["status"] != "WAITING_HUMAN":
            raise InvalidTransition("Recovery proposal is not waiting for human")
        actor = self.gov._actor(actor_id)
        if actor["actor_type"] != "HUMAN":
            raise AuthorityDenied("Recovery decision requires HUMAN actor")
        self.gov.authorize(actor_id, "APPROVE", {"project_id": proposal["project_id"]})
        if decision not in {"APPROVED", "REJECTED"}:
            raise ValidationError("decision must be APPROVED or REJECTED")
        did = uid("recoverydec")
        with self.db.tx():
            self.db.conn.execute(
                "INSERT INTO phase_recovery_decisions VALUES(?,?,?,?,?,?)",
                (did, proposal_id, actor_id, decision, reason, utcnow()),
            )
            self.db.conn.execute(
                "UPDATE phase_recovery_proposals SET status=? WHERE proposal_id=?",
                ("HUMAN_APPROVED" if decision == "APPROVED" else "REJECTED", proposal_id),
            )
            self.db.conn.execute(
                "UPDATE phase_execution_protocols SET status=?,updated_at=? WHERE phase_execution_id=?",
                ("RUNNING" if decision == "APPROVED" else "BLOCKED", utcnow(), proposal["phase_execution_id"]),
            )
            self._event(proposal["phase_execution_id"], "EXECUTE", f"RECOVERY_{decision}", actor_id, reason,
                        {"proposal_id": proposal_id, "decision_id": did})
        return did

    def apply_recovery(self, proposal_id: str, actor_id: str) -> dict[str, Any]:
        proposal = self.db.one(
            "SELECT r.*,p.phase_execution_id,p.problem_id,x.retry_count,x.retry_budget FROM phase_recovery_proposals r "
            "JOIN phase_problem_records p ON p.problem_id=r.problem_id "
            "JOIN phase_execution_protocols x ON x.phase_execution_id=p.phase_execution_id WHERE r.proposal_id=?",
            (proposal_id,),
        )
        if not proposal:
            raise NotFound("Recovery proposal not found")
        if proposal["status"] not in {"AUTO_APPROVED", "HUMAN_APPROVED"}:
            raise InvalidTransition("Recovery proposal is not approved")
        if int(proposal["retry_count"]) >= int(proposal["retry_budget"]):
            raise InvalidTransition("Retry budget exhausted")
        new_plan_id = None
        patch = parse_json(proposal["plan_patch"], []) or []
        if patch:
            latest = self.db.one("SELECT * FROM phase_plans WHERE phase_execution_id=? ORDER BY revision_number DESC LIMIT 1", (proposal["phase_execution_id"],))
            steps = parse_json(latest["steps_json"], [])
            by_index = {int(x["step_index"]): dict(x) for x in steps}
            for item in patch:
                idx = int(item["step_index"])
                if idx not in by_index:
                    raise ValidationError("Plan patch references unknown step", details={"step_index": idx})
                by_index[idx].update({k: v for k, v in item.items() if k != "step_index"})
            new_plan_id = self.create_plan(
                proposal["phase_execution_id"], latest["objective"], [by_index[i] for i in sorted(by_index)], actor_id,
                reason=f"RECOVERY:{proposal_id}",
            )
        with self.db.tx():
            self.db.conn.execute(
                "UPDATE phase_problem_records SET status='RECOVERY_APPLIED' WHERE problem_id=?",
                (proposal["problem_id"],),
            )
            self.db.conn.execute(
                "UPDATE phase_recovery_proposals SET status='APPLIED' WHERE proposal_id=?",
                (proposal_id,),
            )
            self.db.conn.execute(
                "UPDATE phase_execution_protocols SET current_stage='EXECUTE',status='RUNNING',retry_count=retry_count+1,updated_at=? WHERE phase_execution_id=?",
                (utcnow(), proposal["phase_execution_id"]),
            )
            self._event(proposal["phase_execution_id"], "EXECUTE", "RECOVERY_APPLIED", actor_id, proposal["action"],
                        {"proposal_id": proposal_id, "target_step": proposal["target_step"], "new_plan_id": new_plan_id})
        return {"proposal_id": proposal_id, "status": "APPLIED", "new_plan_id": new_plan_id}

    def verify(self, phase_execution_id: str, actor_id: str, *, qa_result: str, detail: str = ""):
        protocol = self._protocol(phase_execution_id)
        if protocol["current_stage"] != "EXECUTE":
            raise InvalidTransition("Verification follows execution")
        if qa_result not in {"PASS", "FAIL"}:
            raise ValidationError("qa_result must be PASS or FAIL")
        plan = self.db.one("SELECT * FROM phase_plans WHERE phase_execution_id=? ORDER BY revision_number DESC LIMIT 1", (phase_execution_id,))
        incomplete = self.db.one(
            "SELECT COUNT(*) n FROM phase_checklist_items WHERE plan_id=? AND status NOT IN ('PASS','SKIPPED')",
            (plan["plan_id"],),
        )["n"]
        if qa_result == "PASS" and incomplete:
            raise InvalidTransition("NO CHECKLIST COMPLETION -> NO QA PASS", details={"incomplete": int(incomplete)})
        with self.db.tx():
            self.db.conn.execute(
                "UPDATE phase_execution_protocols SET current_stage='VERIFY',status=?,updated_at=? WHERE phase_execution_id=?",
                ("RUNNING" if qa_result == "PASS" else "ISSUE", utcnow(), phase_execution_id),
            )
            self._event(phase_execution_id, "VERIFY", f"QA_{qa_result}", actor_id, detail, {"incomplete": int(incomplete)})
        return {"status": qa_result, "incomplete": int(incomplete)}

    def write_handoff(self, phase_execution_id: str, actor_id: str, handoff: dict[str, Any]) -> str:
        protocol = self._protocol(phase_execution_id)
        last_qa = self.db.one(
            "SELECT * FROM phase_stage_events WHERE phase_execution_id=? AND stage='VERIFY' AND event_type='QA_PASS' ORDER BY created_at DESC LIMIT 1",
            (phase_execution_id,),
        )
        if not last_qa:
            raise InvalidTransition("NO QA PASS -> NO HANDOFF")
        hid = uid("handoff")
        body = {
            "what_was_done": handoff.get("what_was_done", ""),
            "what_was_not_done": handoff.get("what_was_not_done", ""),
            "assumptions": handoff.get("assumptions", []),
            "known_limitations": handoff.get("known_limitations", []),
            "open_questions": handoff.get("open_questions", []),
            "risks": handoff.get("risks", []),
            "next_phase": handoff.get("next_phase"),
            "next_phase_prerequisites": handoff.get("next_phase_prerequisites", []),
            "artifact_refs": handoff.get("artifact_refs", []),
            "evidence_refs": handoff.get("evidence_refs", []),
            "checkpoint_id": handoff.get("checkpoint_id"),
        }
        with self.db.tx():
            self.db.conn.execute(
                "INSERT INTO phase_handoffs VALUES(?,?,?,?,?,?,?)",
                (hid, phase_execution_id, canonical_json(body), content_hash(body), actor_id, utcnow(), handoff.get("markdown", "")),
            )
            self.db.conn.execute(
                "UPDATE phase_execution_protocols SET current_stage='HANDOFF',status='RUNNING',updated_at=? WHERE phase_execution_id=?",
                (utcnow(), phase_execution_id),
            )
            self._event(phase_execution_id, "HANDOFF", "HANDOFF_WRITTEN", actor_id, body["what_was_done"],
                        {"handoff_id": hid, "handoff_hash": content_hash(body)})
        return hid

    def complete(self, phase_execution_id: str, actor_id: str):
        protocol = self._protocol(phase_execution_id)
        handoff = self.db.one("SELECT * FROM phase_handoffs WHERE phase_execution_id=? ORDER BY created_at DESC LIMIT 1", (phase_execution_id,))
        if not handoff:
            raise InvalidTransition("NO HANDOFF -> NO PHASE COMPLETE")
        with self.db.tx():
            self.db.conn.execute(
                "UPDATE phase_execution_protocols SET current_stage='COMPLETE',status='COMPLETED',updated_at=? WHERE phase_execution_id=?",
                (utcnow(), phase_execution_id),
            )
            self._event(phase_execution_id, "COMPLETE", "PROTOCOL_COMPLETED", actor_id, "Agent execution protocol completed",
                        {"handoff_id": handoff["handoff_id"]})

    def inspect(self, phase_execution_id: str) -> dict[str, Any]:
        protocol = self._protocol(phase_execution_id)
        plans = []
        for p in self.db.all("SELECT * FROM phase_plans WHERE phase_execution_id=? ORDER BY revision_number", (phase_execution_id,)):
            item = dict(p)
            item["steps"] = parse_json(item.pop("steps_json"), [])
            item["checklist"] = [dict(x) for x in self.db.all(
                "SELECT * FROM phase_checklist_items WHERE plan_id=? ORDER BY step_index", (p["plan_id"],)
            )]
            plans.append(item)
        problems = []
        for p in self.db.all("SELECT * FROM phase_problem_records WHERE phase_execution_id=? ORDER BY created_at", (phase_execution_id,)):
            item = dict(p)
            item["recoveries"] = []
            for r in self.db.all("SELECT * FROM phase_recovery_proposals WHERE problem_id=? ORDER BY created_at", (p["problem_id"],)):
                rr = dict(r)
                rr["plan_patch"] = parse_json(rr["plan_patch"], [])
                rr["decisions"] = [dict(d) for d in self.db.all(
                    "SELECT * FROM phase_recovery_decisions WHERE proposal_id=? ORDER BY created_at", (r["proposal_id"],)
                )]
                item["recoveries"].append(rr)
            problems.append(item)
        handoffs = []
        for h in self.db.all("SELECT * FROM phase_handoffs WHERE phase_execution_id=? ORDER BY created_at", (phase_execution_id,)):
            item = dict(h)
            item["structured_payload"] = parse_json(item["structured_payload"], {})
            handoffs.append(item)
        events = []
        for e in self.db.all("SELECT * FROM phase_stage_events WHERE phase_execution_id=? ORDER BY created_at,event_id", (phase_execution_id,)):
            item = dict(e); item["metadata"] = parse_json(item["metadata"], {}); events.append(item)
        preflights = []
        for p in self.db.all("SELECT * FROM phase_preflights WHERE phase_execution_id=? ORDER BY created_at", (phase_execution_id,)):
            item = dict(p); item["checks"] = parse_json(item["checks_json"], []); preflights.append(item)
        completed_stages = len({e["stage"] for e in events if e["event_type"] in {
            "SKILL_LOADED", "PREFLIGHT_PASS", "PLAN_FROZEN", "EXECUTION_STARTED", "QA_PASS", "HANDOFF_WRITTEN", "PROTOCOL_COMPLETED"
        }})
        latest_plan = plans[-1] if plans else None
        total_steps = len(latest_plan["checklist"]) if latest_plan else 0
        done_steps = len([x for x in latest_plan["checklist"] if x["status"] in {"PASS", "SKIPPED"}]) if latest_plan else 0
        waiting = any(r["status"] == "WAITING_HUMAN" for p in problems for r in p["recoveries"])
        issue = any(p["status"] == "OPEN" for p in problems)
        if protocol["status"] == "COMPLETED":
            attention = "COMPLETE"
        elif waiting:
            attention = "WAITING_FOR_YOU"
        elif issue:
            attention = "NEEDS_ATTENTION"
        else:
            attention = "AI_WORKING"
        return {
            "protocol": dict(protocol),
            "previous_handoff": self.previous_handoff(phase_execution_id),
            "project_defaults": self.project_defaults(protocol["project_id"]),
            "attention": attention,
            "stage_progress": {"completed": completed_stages, "total": len(STAGES)},
            "plan_progress": {"completed": done_steps, "total": total_steps},
            "preflights": preflights,
            "plans": plans,
            "problems": problems,
            "handoffs": handoffs,
            "events": events,
        }
