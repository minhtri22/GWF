from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import ApprovalMismatch, AuthorityDenied, InvalidTransition, NotFound, ValidationError
from .utils import canonical_json, content_hash, parse_json, uid, utcnow


TRANSITION_DISPOSITIONS = {
    "AUTO_ALLOWED",
    "HUMAN_APPROVAL_REQUIRED",
    "FORBIDDEN",
    "SUCCESSOR_REQUIRED",
}
WORK_ASSIGNMENT_STATES = {
    "PROPOSED",
    "FROZEN",
    "AUTHORIZED",
    "DISPATCHED",
    "RUNNING",
    "VERIFYING",
    "COMPLETED",
    "BLOCKED",
    "CANCELLED",
}
EXECUTOR_BINDING_MODES = {"DYNAMIC", "FROZEN"}
EXECUTOR_BINDING_STATES = {"PROPOSED", "RESOLVED", "FROZEN", "INVALIDATED", "RELEASED"}
HUMAN_ACTION_STATES = {"PENDING", "RESOLVED", "REJECTED", "EXPIRED", "CANCELLED"}
BUDGET_ENFORCEMENT = {"HARD", "ADVISORY"}


@dataclass(frozen=True)
class GovernanceProfileRef:
    domain_id: str
    profile_id: str
    profile_version: str
    profile_hash: str

    def to_dict(self) -> dict[str, str]:
        return {
            "domain_id": self.domain_id,
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "profile_hash": self.profile_hash,
        }


class VNextGovernanceService:
    """Provider-neutral implementation of the GWF vNext P1 governance contracts.

    This service deliberately does not contain Codex, ChatGPT, RemoteMCP, G2E,
    research-mode, software-release, or browser-specific execution behavior.
    """

    def __init__(self, db, governance):
        self.db = db
        self.governance = governance

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------
    def _project(self, project_id: str):
        row = self.db.one("SELECT * FROM projects WHERE id=?", (project_id,))
        if not row:
            raise NotFound("Project not found")
        return row

    def _reject_secret_material(self, payload: Any, *, path: str = "root"):
        if isinstance(payload, dict):
            for key, value in payload.items():
                lowered = str(key).lower()
                if lowered == "secret_connection_ref":
                    if value is not None and not isinstance(value, str):
                        raise ValidationError("secret_connection_ref must be an opaque string reference")
                    continue
                if any(token in lowered for token in ("password", "api_key", "apikey", "access_token", "refresh_token", "bearer", "credential_secret")):
                    if value not in (None, "", [], {}):
                        raise ValidationError("Raw secret material is forbidden", details={"path": f"{path}.{key}"})
                self._reject_secret_material(value, path=f"{path}.{key}")
        elif isinstance(payload, (list, tuple)):
            for index, value in enumerate(payload):
                self._reject_secret_material(value, path=f"{path}[{index}]")

    def _audit(self, project_id: str, actor_id: str, action: str, resource_type: str, resource_id: str, *, reason_code="OK", metadata=None):
        self.governance.append_audit(
            project_id,
            actor_id,
            action,
            resource_type,
            resource_id,
            reason_code=reason_code,
            metadata=metadata or {},
        )

    # ------------------------------------------------------------------
    # Governance profiles
    # ------------------------------------------------------------------
    def register_profile_definition(
        self,
        domain_id: str,
        profile_id: str,
        version: str,
        policy: dict[str, Any],
        transition_edges: list[dict[str, Any]],
        *,
        actor_id: str = "SYSTEM",
    ) -> GovernanceProfileRef:
        payload = {
            "domain_id": domain_id,
            "profile_id": profile_id,
            "version": version,
            "policy": policy,
            "transition_edges": transition_edges,
        }
        self._reject_secret_material(payload)
        ph = content_hash(payload)
        existing = self.db.one(
            "SELECT * FROM governance_profile_definitions WHERE domain_id=? AND profile_id=? AND profile_version=?",
            (domain_id, profile_id, version),
        )
        if existing:
            if existing["profile_hash"] != ph:
                raise ValidationError("Profile version already exists with different content")
            return GovernanceProfileRef(domain_id, profile_id, version, ph)
        self.db.conn.execute(
            "INSERT INTO governance_profile_definitions VALUES(?,?,?,?,?,?,?,?,?)",
            (
                uid("gprof"),
                domain_id,
                profile_id,
                version,
                canonical_json(policy),
                canonical_json(transition_edges),
                ph,
                actor_id,
                utcnow(),
            ),
        )
        self.db.conn.commit()
        return GovernanceProfileRef(domain_id, profile_id, version, ph)

    def resolve_profile_ref(self, ref: GovernanceProfileRef | dict[str, Any]):
        if isinstance(ref, GovernanceProfileRef):
            data = ref.to_dict()
        else:
            data = dict(ref)
        row = self.db.one(
            "SELECT * FROM governance_profile_definitions WHERE domain_id=? AND profile_id=? AND profile_version=?",
            (data["domain_id"], data["profile_id"], data["profile_version"]),
        )
        if not row or row["profile_hash"] != data["profile_hash"]:
            raise NotFound("Exact GovernanceProfileRef cannot be resolved")
        return row

    def bind_project_profile(self, project_id: str, ref: GovernanceProfileRef | dict[str, Any], *, actor_id: str = "SYSTEM"):
        self._project(project_id)
        row = self.resolve_profile_ref(ref)
        self.db.conn.execute(
            "INSERT INTO project_governance_profiles(project_id,domain_id,profile_id,profile_version,profile_hash,bound_by_actor_id,bound_at) "
            "VALUES(?,?,?,?,?,?,?) "
            "ON CONFLICT(project_id) DO UPDATE SET domain_id=excluded.domain_id,profile_id=excluded.profile_id,"
            "profile_version=excluded.profile_version,profile_hash=excluded.profile_hash,bound_by_actor_id=excluded.bound_by_actor_id,bound_at=excluded.bound_at",
            (
                project_id,
                row["domain_id"],
                row["profile_id"],
                row["profile_version"],
                row["profile_hash"],
                actor_id,
                utcnow(),
            ),
        )
        self._audit(project_id, actor_id, "BIND_GOVERNANCE_PROFILE", "GovernanceProfile", row["definition_id"])
        self.db.conn.commit()

    def current_profile_ref(self, project_id: str) -> GovernanceProfileRef:
        row = self.db.one("SELECT * FROM project_governance_profiles WHERE project_id=?", (project_id,))
        if not row:
            raise NotFound("Project has no active GovernanceProfileRef")
        ref = GovernanceProfileRef(row["domain_id"], row["profile_id"], row["profile_version"], row["profile_hash"])
        self.resolve_profile_ref(ref)
        return ref

    # ------------------------------------------------------------------
    # Governance transition
    # ------------------------------------------------------------------
    def propose_transition(
        self,
        project_id: str,
        subject_ref: dict[str, Any],
        from_profile_ref: GovernanceProfileRef | dict[str, Any],
        to_profile_ref: GovernanceProfileRef | dict[str, Any],
        proposer_actor_id: str,
        reason_codes: list[str],
        *,
        evidence_refs: list[dict[str, Any]] | None = None,
        requested_authority_delta: dict[str, Any] | None = None,
        requested_budget_delta: dict[str, Any] | None = None,
    ) -> str:
        self._project(project_id)
        source = self.resolve_profile_ref(from_profile_ref)
        target = self.resolve_profile_ref(to_profile_ref)
        self.governance.authorize(proposer_actor_id, "PROPOSE", {"project_id": project_id, "resource_type": "GovernanceTransition"})
        payload = {
            "project_id": project_id,
            "subject_ref": subject_ref,
            "from_profile_ref": GovernanceProfileRef(source["domain_id"], source["profile_id"], source["profile_version"], source["profile_hash"]).to_dict(),
            "to_profile_ref": GovernanceProfileRef(target["domain_id"], target["profile_id"], target["profile_version"], target["profile_hash"]).to_dict(),
            "proposer_actor_id": proposer_actor_id,
            "reason_codes": list(reason_codes),
            "evidence_refs": evidence_refs or [],
            "requested_authority_delta": requested_authority_delta,
            "requested_budget_delta": requested_budget_delta,
        }
        self._reject_secret_material(payload)
        tid = uid("gtrans")
        ph = content_hash(payload)
        self.db.conn.execute(
            "INSERT INTO governance_transition_proposals VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                tid,
                project_id,
                canonical_json(subject_ref),
                canonical_json(payload["from_profile_ref"]),
                canonical_json(payload["to_profile_ref"]),
                proposer_actor_id,
                canonical_json(reason_codes),
                canonical_json(evidence_refs or []),
                canonical_json(requested_authority_delta) if requested_authority_delta is not None else None,
                canonical_json(requested_budget_delta) if requested_budget_delta is not None else None,
                "FROZEN",
                None,
                None,
                None,
                ph,
                utcnow(),
                None,
                None,
            ),
        )
        self._audit(project_id, proposer_actor_id, "PROPOSE_GOVERNANCE_TRANSITION", "GovernanceTransitionProposal", tid)
        self.db.conn.commit()
        return tid

    def evaluate_transition(self, transition_id: str) -> str:
        row = self.db.one("SELECT * FROM governance_transition_proposals WHERE transition_id=?", (transition_id,))
        if not row:
            raise NotFound("GovernanceTransitionProposal not found")
        source_ref = parse_json(row["from_profile_ref"], {})
        target_ref = parse_json(row["to_profile_ref"], {})
        source = self.resolve_profile_ref(source_ref)
        self.resolve_profile_ref(target_ref)
        edges = parse_json(source["transition_edges"], [])
        matches = []
        for edge in edges:
            target = edge.get("target_profile_ref") or {}
            if (
                target.get("domain_id") == target_ref.get("domain_id")
                and target.get("profile_id") == target_ref.get("profile_id")
                and target.get("profile_version") == target_ref.get("profile_version")
                and target.get("profile_hash") == target_ref.get("profile_hash")
            ):
                matches.append(edge)
        if len(matches) != 1:
            raise InvalidTransition("Unknown or ambiguous governance transition edge")
        disposition = matches[0].get("disposition")
        if disposition not in TRANSITION_DISPOSITIONS:
            raise ValidationError("Invalid governance transition disposition")
        self.db.conn.execute(
            "UPDATE governance_transition_proposals SET state='EVALUATED',disposition=?,evaluated_at=? WHERE transition_id=?",
            (disposition, utcnow(), transition_id),
        )
        self.db.conn.commit()
        return disposition

    # ------------------------------------------------------------------
    # Authority envelopes
    # ------------------------------------------------------------------
    def create_authority_envelope(
        self,
        project_id: str,
        parent_authority_ref: dict[str, Any],
        subject_actor_or_role_ref: dict[str, Any],
        resource_selectors: list[Any],
        allow_actions: list[str],
        deny_actions: list[str],
        *,
        conditions: list[Any] | None = None,
        expires_at: str | None = None,
        actor_id: str = "SYSTEM",
    ) -> str:
        self._project(project_id)
        allow = sorted(set(allow_actions))
        deny = sorted(set(deny_actions))
        resources = list(resource_selectors)
        conds = list(conditions or [])
        parent_id = parent_authority_ref.get("authority_envelope_id") if isinstance(parent_authority_ref, dict) else None
        if parent_id:
            parent = self.db.one("SELECT * FROM authority_envelopes WHERE authority_envelope_id=?", (parent_id,))
            if not parent:
                raise NotFound("Parent AuthorityEnvelope not found")
            parent_allow = set(parse_json(parent["allow_actions"], []))
            parent_resources = set(canonical_json(x) for x in parse_json(parent["resource_selectors"], []))
            if not set(allow).issubset(parent_allow):
                raise AuthorityDenied("Child AuthorityEnvelope cannot add parent-absent ALLOW action")
            if not set(canonical_json(x) for x in resources).issubset(parent_resources):
                raise AuthorityDenied("Child AuthorityEnvelope cannot widen parent resource scope")
        payload = {
            "parent_authority_ref": parent_authority_ref,
            "subject_actor_or_role_ref": subject_actor_or_role_ref,
            "resource_selectors": resources,
            "allow_actions": allow,
            "deny_actions": deny,
            "conditions": conds,
            "expires_at": expires_at,
        }
        self._reject_secret_material(payload)
        eid = uid("authenv")
        ph = content_hash(payload)
        self.db.conn.execute(
            "INSERT INTO authority_envelopes VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                eid,
                project_id,
                canonical_json(parent_authority_ref),
                canonical_json(subject_actor_or_role_ref),
                canonical_json(resources),
                canonical_json(allow),
                canonical_json(deny),
                canonical_json(conds),
                expires_at,
                ph,
                utcnow(),
            ),
        )
        self._audit(project_id, actor_id, "CREATE_AUTHORITY_ENVELOPE", "AuthorityEnvelope", eid)
        self.db.conn.commit()
        return eid

    def effective_authority(self, authority_envelope_id: str) -> dict[str, Any]:
        row = self.db.one("SELECT * FROM authority_envelopes WHERE authority_envelope_id=?", (authority_envelope_id,))
        if not row:
            raise NotFound("AuthorityEnvelope not found")
        allow = set(parse_json(row["allow_actions"], []))
        deny = set(parse_json(row["deny_actions"], []))
        resources = list(parse_json(row["resource_selectors"], []))
        conditions = list(parse_json(row["conditions"], []))
        expiries = [row["expires_at"]] if row["expires_at"] else []
        parent_ref = parse_json(row["parent_authority_ref"], {})
        parent_id = parent_ref.get("authority_envelope_id") if isinstance(parent_ref, dict) else None
        if parent_id:
            parent = self.effective_authority(parent_id)
            allow &= set(parent["allow_actions"])
            deny |= set(parent["deny_actions"])
            parent_resources = {canonical_json(x): x for x in parent["resource_selectors"]}
            resources = [x for x in resources if canonical_json(x) in parent_resources]
            conditions = list(parent["conditions"]) + conditions
            if parent.get("expires_at"):
                expiries.append(parent["expires_at"])
        allow -= deny
        return {
            "allow_actions": sorted(allow),
            "deny_actions": sorted(deny),
            "resource_selectors": resources,
            "conditions": conditions,
            "expires_at": min(expiries) if expiries else None,
        }

    # ------------------------------------------------------------------
    # Budget envelopes and runtime usage ledger
    # ------------------------------------------------------------------
    def create_budget_envelope(
        self,
        project_id: str,
        limits: list[dict[str, Any]],
        *,
        parent_budget_ref: dict[str, Any] | None = None,
        actor_id: str = "SYSTEM",
    ) -> str:
        self._project(project_id)
        normalized = []
        seen = set()
        for item in limits:
            dimension = item.get("dimension")
            unit = item.get("unit")
            enforcement = item.get("enforcement")
            ceiling = item.get("ceiling")
            if not dimension or not unit or enforcement not in BUDGET_ENFORCEMENT or not isinstance(ceiling, (int, float)) or ceiling < 0:
                raise ValidationError("Invalid budget limit")
            if dimension in seen:
                raise ValidationError("Duplicate budget dimension")
            seen.add(dimension)
            normalized.append({"dimension": dimension, "unit": unit, "ceiling": ceiling, "enforcement": enforcement})
        parent_id = (parent_budget_ref or {}).get("budget_envelope_id")
        if parent_id:
            parent = self.effective_budget(parent_id)
            pmap = {x["dimension"]: x for x in parent["limits"]}
            for item in normalized:
                if item["dimension"] in pmap:
                    p = pmap[item["dimension"]]
                    if item["unit"] != p["unit"]:
                        raise ValidationError("Budget unit mismatch with parent")
                    if item["ceiling"] > p["ceiling"]:
                        raise AuthorityDenied("Child BudgetEnvelope cannot increase inherited ceiling")
        payload = {"parent_budget_ref": parent_budget_ref, "limits": normalized}
        self._reject_secret_material(payload)
        bid = uid("budget")
        ph = content_hash(payload)
        self.db.conn.execute(
            "INSERT INTO budget_envelopes VALUES(?,?,?,?,?,?,?)",
            (bid, project_id, canonical_json(parent_budget_ref) if parent_budget_ref is not None else None, canonical_json(normalized), ph, actor_id, utcnow()),
        )
        self._audit(project_id, actor_id, "CREATE_BUDGET_ENVELOPE", "BudgetEnvelope", bid)
        self.db.conn.commit()
        return bid

    def effective_budget(self, budget_envelope_id: str) -> dict[str, Any]:
        row = self.db.one("SELECT * FROM budget_envelopes WHERE budget_envelope_id=?", (budget_envelope_id,))
        if not row:
            raise NotFound("BudgetEnvelope not found")
        own = {x["dimension"]: dict(x) for x in parse_json(row["limits"], [])}
        pref = parse_json(row["parent_budget_ref"], {}) if row["parent_budget_ref"] else {}
        parent_id = pref.get("budget_envelope_id") if isinstance(pref, dict) else None
        if parent_id:
            parent = self.effective_budget(parent_id)
            merged = {x["dimension"]: dict(x) for x in parent["limits"]}
            for dimension, item in own.items():
                if dimension in merged:
                    if item["unit"] != merged[dimension]["unit"]:
                        raise ValidationError("Budget unit mismatch")
                    merged[dimension]["ceiling"] = min(merged[dimension]["ceiling"], item["ceiling"])
                    if item["enforcement"] == "HARD":
                        merged[dimension]["enforcement"] = "HARD"
                else:
                    merged[dimension] = item
            own = merged
        return {"limits": [own[k] for k in sorted(own)]}

    def record_budget_usage(self, budget_envelope_id: str, dimension: str, amount: float) -> float:
        if amount < 0:
            raise ValidationError("Budget usage amount must be non-negative")
        effective = self.effective_budget(budget_envelope_id)
        match = next((x for x in effective["limits"] if x["dimension"] == dimension), None)
        if not match:
            raise ValidationError("Budget dimension not defined")
        row = self.db.one(
            "SELECT consumed FROM budget_usage WHERE budget_envelope_id=? AND dimension=?",
            (budget_envelope_id, dimension),
        )
        consumed = float(row["consumed"]) if row else 0.0
        proposed = consumed + float(amount)
        if match["enforcement"] == "HARD" and proposed > float(match["ceiling"]):
            raise AuthorityDenied("Hard budget ceiling exceeded")
        self.db.conn.execute(
            "INSERT INTO budget_usage(budget_envelope_id,dimension,unit,consumed,updated_at) VALUES(?,?,?,?,?) "
            "ON CONFLICT(budget_envelope_id,dimension) DO UPDATE SET consumed=excluded.consumed,updated_at=excluded.updated_at",
            (budget_envelope_id, dimension, match["unit"], proposed, utcnow()),
        )
        self.db.conn.commit()
        return proposed

    # ------------------------------------------------------------------
    # Execution environments
    # ------------------------------------------------------------------
    def register_execution_environment(
        self,
        environment_type: str,
        adapter_id: str,
        adapter_version: str,
        adapter_hash: str,
        capability_manifest_ref: dict[str, Any],
        *,
        transport_class: str | None = None,
        locality_class: str | None = None,
        secret_connection_ref: str | None = None,
        actor_id: str = "SYSTEM",
    ) -> str:
        payload = {
            "environment_type": environment_type,
            "adapter_id": adapter_id,
            "adapter_version": adapter_version,
            "adapter_hash": adapter_hash,
            "capability_manifest_ref": capability_manifest_ref,
            "transport_class": transport_class,
            "locality_class": locality_class,
            "secret_connection_ref": secret_connection_ref,
        }
        self._reject_secret_material(payload)
        if not adapter_hash or len(adapter_hash) != 64:
            raise ValidationError("adapter_hash must be a SHA-256 hex digest")
        eid = uid("execenv")
        self.db.conn.execute(
            "INSERT INTO execution_environments VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                eid,
                environment_type,
                adapter_id,
                adapter_version,
                adapter_hash,
                canonical_json(capability_manifest_ref),
                transport_class,
                locality_class,
                secret_connection_ref,
                utcnow(),
            ),
        )
        self.db.conn.commit()
        return eid

    # ------------------------------------------------------------------
    # Work assignments
    # ------------------------------------------------------------------
    def create_work_assignment(
        self,
        project_id: str,
        origin_refs: list[dict[str, Any]],
        objective: dict[str, Any],
        agent_role_ref: dict[str, Any],
        required_capabilities: list[str],
        execution_environment_constraints: dict[str, Any],
        authority_envelope_ref: dict[str, Any],
        budget_envelope_ref: dict[str, Any],
        expected_outputs: list[dict[str, Any]],
        completion_contract: dict[str, Any],
        *,
        revision: int = 1,
        protected_resource_constraints: list[dict[str, Any]] | None = None,
        independence_requirements: dict[str, Any] | None = None,
        proposer_actor_id: str,
    ) -> str:
        self._project(project_id)
        self.governance.authorize(proposer_actor_id, "PROPOSE", {"project_id": project_id, "resource_type": "WorkAssignment"})
        payload = {
            "project_id": project_id,
            "origin_refs": origin_refs,
            "objective": objective,
            "agent_role_ref": agent_role_ref,
            "required_capabilities": sorted(set(required_capabilities)),
            "execution_environment_constraints": execution_environment_constraints,
            "authority_envelope_ref": authority_envelope_ref,
            "budget_envelope_ref": budget_envelope_ref,
            "protected_resource_constraints": protected_resource_constraints or [],
            "expected_outputs": expected_outputs,
            "completion_contract": completion_contract,
            "independence_requirements": independence_requirements,
            "revision": revision,
        }
        self._reject_secret_material(payload)
        aid = uid("wa")
        self.db.conn.execute(
            "INSERT INTO work_assignments("
            "work_assignment_id,revision,project_id,origin_refs,objective,agent_role_ref,"
            "required_capabilities,execution_environment_constraints,executor_binding_id,"
            "authority_envelope_ref,budget_envelope_ref,protected_resource_constraints,"
            "expected_outputs,completion_contract,independence_requirements,state,"
            "frozen_payload_hash,proposer_actor_id,created_at,frozen_at"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                aid,
                revision,
                project_id,
                canonical_json(origin_refs),
                canonical_json(objective),
                canonical_json(agent_role_ref),
                canonical_json(sorted(set(required_capabilities))),
                canonical_json(execution_environment_constraints),
                None,
                canonical_json(authority_envelope_ref),
                canonical_json(budget_envelope_ref),
                canonical_json(protected_resource_constraints or []),
                canonical_json(expected_outputs),
                canonical_json(completion_contract),
                canonical_json(independence_requirements) if independence_requirements is not None else None,
                "PROPOSED",
                None,
                proposer_actor_id,
                utcnow(),
                None,
            ),
        )
        self._audit(project_id, proposer_actor_id, "PROPOSE_WORK_ASSIGNMENT", "WorkAssignment", aid)
        self.db.conn.commit()
        return aid

    def _assignment(self, work_assignment_id: str):
        row = self.db.one("SELECT * FROM work_assignments WHERE work_assignment_id=?", (work_assignment_id,))
        if not row:
            raise NotFound("WorkAssignment not found")
        return row

    def _assignment_normative_payload(self, row) -> dict[str, Any]:
        return {
            "work_assignment_id": row["work_assignment_id"],
            "revision": row["revision"],
            "project_id": row["project_id"],
            "origin_refs": parse_json(row["origin_refs"], []),
            "objective": parse_json(row["objective"], {}),
            "agent_role_ref": parse_json(row["agent_role_ref"], {}),
            "required_capabilities": parse_json(row["required_capabilities"], []),
            "execution_environment_constraints": parse_json(row["execution_environment_constraints"], {}),
            "authority_envelope_ref": parse_json(row["authority_envelope_ref"], {}),
            "budget_envelope_ref": parse_json(row["budget_envelope_ref"], {}),
            "protected_resource_constraints": parse_json(row["protected_resource_constraints"], []),
            "expected_outputs": parse_json(row["expected_outputs"], []),
            "completion_contract": parse_json(row["completion_contract"], {}),
            "independence_requirements": parse_json(row["independence_requirements"], None) if row["independence_requirements"] else None,
        }

    def freeze_work_assignment(self, work_assignment_id: str, actor_id: str) -> str:
        row = self._assignment(work_assignment_id)
        if row["state"] != "PROPOSED":
            raise InvalidTransition("Only PROPOSED WorkAssignment can be frozen")
        payload = self._assignment_normative_payload(row)
        ph = content_hash(payload)
        self.db.conn.execute(
            "UPDATE work_assignments SET state='FROZEN',frozen_payload_hash=?,frozen_at=? WHERE work_assignment_id=?",
            (ph, utcnow(), work_assignment_id),
        )
        self._audit(row["project_id"], actor_id, "FREEZE_WORK_ASSIGNMENT", "WorkAssignment", work_assignment_id)
        self.db.conn.commit()
        return ph

    def authorize_work_assignment(self, work_assignment_id: str, actor_id: str, expected_hash: str):
        row = self._assignment(work_assignment_id)
        if row["state"] != "FROZEN":
            raise InvalidTransition("Only FROZEN WorkAssignment can be authorized")
        if row["frozen_payload_hash"] != expected_hash:
            raise ApprovalMismatch("WorkAssignment frozen payload hash mismatch")
        recomputed = content_hash(self._assignment_normative_payload(row))
        if recomputed != expected_hash:
            raise ApprovalMismatch("WorkAssignment normative payload changed after freeze")
        self.governance.authorize(actor_id, "APPROVE", {"project_id": row["project_id"], "resource_type": "WorkAssignment"})
        self.db.conn.execute(
            "UPDATE work_assignments SET state='AUTHORIZED',authorized_by_actor_id=?,authorized_at=? WHERE work_assignment_id=?",
            (actor_id, utcnow(), work_assignment_id),
        )
        self._audit(row["project_id"], actor_id, "AUTHORIZE_WORK_ASSIGNMENT", "WorkAssignment", work_assignment_id)
        self.db.conn.commit()

    def dispatch_work_assignment(self, work_assignment_id: str, executor_binding_id: str, actor_id: str):
        row = self._assignment(work_assignment_id)
        if row["state"] != "AUTHORIZED":
            raise InvalidTransition("WorkAssignment must be AUTHORIZED before dispatch")
        binding = self.db.one("SELECT * FROM executor_bindings WHERE executor_binding_id=?", (executor_binding_id,))
        if not binding or binding["work_assignment_id"] != work_assignment_id:
            raise ValidationError("ExecutorBinding does not belong to WorkAssignment")
        if binding["status"] not in {"RESOLVED", "FROZEN"}:
            raise InvalidTransition("ExecutorBinding must be resolved before dispatch")
        self.db.conn.execute(
            "UPDATE work_assignments SET state='DISPATCHED',executor_binding_id=?,dispatched_at=? WHERE work_assignment_id=?",
            (executor_binding_id, utcnow(), work_assignment_id),
        )
        self._audit(row["project_id"], actor_id, "DISPATCH_WORK_ASSIGNMENT", "WorkAssignment", work_assignment_id)
        self.db.conn.commit()

    def mark_assignment_running(self, work_assignment_id: str, actor_id: str):
        row = self._assignment(work_assignment_id)
        if row["state"] != "DISPATCHED":
            raise InvalidTransition("Only DISPATCHED WorkAssignment can run")
        self.db.conn.execute("UPDATE work_assignments SET state='RUNNING' WHERE work_assignment_id=?", (work_assignment_id,))
        self._audit(row["project_id"], actor_id, "RUN_WORK_ASSIGNMENT", "WorkAssignment", work_assignment_id)
        self.db.conn.commit()

    def mark_assignment_completed(self, work_assignment_id: str, actor_id: str):
        row = self._assignment(work_assignment_id)
        if row["state"] not in {"RUNNING", "VERIFYING"}:
            raise InvalidTransition("WorkAssignment is not completable")
        self.db.conn.execute("UPDATE work_assignments SET state='COMPLETED' WHERE work_assignment_id=?", (work_assignment_id,))
        self._audit(row["project_id"], actor_id, "COMPLETE_WORK_ASSIGNMENT", "WorkAssignment", work_assignment_id)
        self.db.conn.commit()

    def mark_assignment_operational_failure(self, work_assignment_id: str, actor_id: str, failure_code: str):
        row = self._assignment(work_assignment_id)
        if row["state"] not in {"DISPATCHED", "RUNNING", "VERIFYING"}:
            raise InvalidTransition("WorkAssignment is not in an operational state")
        self.db.conn.execute("UPDATE work_assignments SET state='BLOCKED' WHERE work_assignment_id=?", (work_assignment_id,))
        self._audit(row["project_id"], actor_id, "BLOCK_WORK_ASSIGNMENT_OPERATIONAL", "WorkAssignment", work_assignment_id, reason_code=failure_code)
        self.db.conn.commit()

    # ------------------------------------------------------------------
    # Executor bindings
    # ------------------------------------------------------------------
    def create_executor_binding(
        self,
        work_assignment_id: str,
        binding_mode: str,
        agent_role_ref: dict[str, Any],
        agent_identity: dict[str, Any],
        execution_environment_ref: dict[str, Any],
        capability_manifest_ref: dict[str, Any],
        material_identity_dimensions: list[str],
        authority_envelope_ref: dict[str, Any],
        budget_envelope_ref: dict[str, Any],
        *,
        equivalence_policy_ref: dict[str, Any] | None = None,
    ) -> str:
        if binding_mode not in EXECUTOR_BINDING_MODES:
            raise ValidationError("Invalid ExecutorBinding mode")
        assignment = self._assignment(work_assignment_id)
        if assignment["state"] not in {"FROZEN", "AUTHORIZED"}:
            raise InvalidTransition("ExecutorBinding requires frozen or authorized WorkAssignment")
        env_id = execution_environment_ref.get("execution_environment_id")
        env = self.db.one("SELECT * FROM execution_environments WHERE execution_environment_id=?", (env_id,))
        if not env:
            raise NotFound("ExecutionEnvironmentRef cannot be resolved")
        payload = {
            "work_assignment_id": work_assignment_id,
            "binding_mode": binding_mode,
            "agent_role_ref": agent_role_ref,
            "agent_identity": agent_identity,
            "execution_environment_ref": execution_environment_ref,
            "capability_manifest_ref": capability_manifest_ref,
            "material_identity_dimensions": sorted(set(material_identity_dimensions)),
            "equivalence_policy_ref": equivalence_policy_ref,
            "authority_envelope_ref": authority_envelope_ref,
            "budget_envelope_ref": budget_envelope_ref,
        }
        self._reject_secret_material(payload)
        bid = uid("execbind")
        ph = content_hash(payload)
        state = "FROZEN" if binding_mode == "FROZEN" else "RESOLVED"
        self.db.conn.execute(
            "INSERT INTO executor_bindings VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                bid,
                work_assignment_id,
                binding_mode,
                canonical_json(agent_role_ref),
                canonical_json(agent_identity),
                canonical_json(execution_environment_ref),
                canonical_json(capability_manifest_ref),
                canonical_json(sorted(set(material_identity_dimensions))),
                canonical_json(equivalence_policy_ref) if equivalence_policy_ref is not None else None,
                canonical_json(authority_envelope_ref),
                canonical_json(budget_envelope_ref),
                utcnow(),
                state,
                ph,
                None,
            ),
        )
        self.db.conn.execute("UPDATE work_assignments SET executor_binding_id=? WHERE work_assignment_id=?", (bid, work_assignment_id))
        self.db.conn.commit()
        return bid

    def substitute_executor_binding(self, executor_binding_id: str, new_agent_identity: dict[str, Any]):
        row = self.db.one("SELECT * FROM executor_bindings WHERE executor_binding_id=?", (executor_binding_id,))
        if not row:
            raise NotFound("ExecutorBinding not found")
        assignment = self._assignment(row["work_assignment_id"])
        if assignment["state"] in {"DISPATCHED", "RUNNING", "VERIFYING", "COMPLETED"}:
            raise InvalidTransition("Resolved ExecutorBinding is immutable after dispatch")
        if row["binding_mode"] == "FROZEN":
            raise InvalidTransition("Frozen ExecutorBinding cannot be substituted")
        raise InvalidTransition("Resolved ExecutorBinding cannot mutate; create a new authorized binding")

    # ------------------------------------------------------------------
    # Human action requests
    # ------------------------------------------------------------------
    def create_human_action_request(
        self,
        project_id: str,
        action_kind: str,
        subject_ref: dict[str, Any],
        frozen_payload: dict[str, Any],
        required_authority_action: str,
        approver_constraints: dict[str, Any],
        reason_codes: list[str],
        *,
        proposal_ref: dict[str, Any] | None = None,
        expires_at: str | None = None,
        actor_id: str = "SYSTEM",
    ) -> str:
        self._project(project_id)
        self._reject_secret_material(frozen_payload)
        rid = uid("har")
        ph = content_hash(frozen_payload)
        self.db.conn.execute(
            "INSERT INTO human_action_requests VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                rid,
                project_id,
                action_kind,
                canonical_json(subject_ref),
                canonical_json(proposal_ref) if proposal_ref is not None else None,
                canonical_json(frozen_payload),
                ph,
                required_authority_action,
                canonical_json(approver_constraints),
                canonical_json(reason_codes),
                expires_at,
                "PENDING",
                None,
                actor_id,
                utcnow(),
            ),
        )
        self._audit(project_id, actor_id, "CREATE_HUMAN_ACTION_REQUEST", "HumanActionRequest", rid)
        self.db.conn.commit()
        return rid

    def resolve_human_action_request(self, request_id: str, approval_id: str, expected_hash: str):
        row = self.db.one("SELECT * FROM human_action_requests WHERE human_action_request_id=?", (request_id,))
        if not row:
            raise NotFound("HumanActionRequest not found")
        if row["state"] != "PENDING":
            raise InvalidTransition("HumanActionRequest is not pending")
        if row["frozen_payload_hash"] != expected_hash:
            raise ApprovalMismatch("HumanActionRequest frozen payload hash mismatch")
        if content_hash(parse_json(row["frozen_payload"], {})) != expected_hash:
            raise ApprovalMismatch("HumanActionRequest payload changed")
        approval = self.db.one("SELECT * FROM approvals WHERE approval_id=?", (approval_id,))
        if not approval or approval["decision"] != "APPROVED":
            raise ApprovalMismatch("Authoritative approval is missing")
        if approval["project_id"] != row["project_id"]:
            raise ApprovalMismatch("Approval project mismatch")
        self.db.conn.execute(
            "UPDATE human_action_requests SET state='RESOLVED',resolution_ref=? WHERE human_action_request_id=?",
            (canonical_json({"approval_id": approval_id}), request_id),
        )
        self.db.conn.commit()

    # ------------------------------------------------------------------
    # Effective policy
    # ------------------------------------------------------------------
    def compile_effective_policy(
        self,
        project_id: str,
        base_gwf_authority: dict[str, Any],
        governance_profile_ref: GovernanceProfileRef | dict[str, Any],
        project_overlays: dict[str, Any],
        authority_envelope_id: str,
        budget_envelope_id: str,
        resolved_human_action_refs: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        profile = self.resolve_profile_ref(governance_profile_ref)
        authority = self.effective_authority(authority_envelope_id)
        budget = self.effective_budget(budget_envelope_id)
        profile_policy = parse_json(profile["policy"], {})
        result = {
            "effective_authority": {"base": base_gwf_authority, "envelope": authority},
            "effective_budget": budget,
            "autonomy_policy": profile_policy.get("autonomy_policy", {}),
            "mutation_policy": profile_policy.get("mutation_policy", {}),
            "protected_resource_policy": profile_policy.get("protected_resource_policy", {}),
            "lineage_policy": profile_policy.get("lineage_policy", {}),
            "approval_policy": profile_policy.get("approval_policy", {}),
            "retry_recovery_policy": profile_policy.get("retry_recovery_policy", {}),
            "claim_permission_policy": profile_policy.get("claim_permission_policy", {}),
            "project_overlays": project_overlays,
            "resolved_human_action_refs": resolved_human_action_refs or [],
            "provenance": {
                "project_id": project_id,
                "profile_ref": GovernanceProfileRef(profile["domain_id"], profile["profile_id"], profile["profile_version"], profile["profile_hash"]).to_dict(),
                "authority_envelope_id": authority_envelope_id,
                "budget_envelope_id": budget_envelope_id,
            },
        }
        self._reject_secret_material(result)
        result["compiled_hash"] = content_hash(result)
        self.db.conn.execute(
            "INSERT INTO effective_governance_policies VALUES(?,?,?,?,?)",
            (uid("egp"), project_id, result["compiled_hash"], canonical_json(result), utcnow()),
        )
        self.db.conn.commit()
        return result
