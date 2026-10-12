from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from .errors import AuthorityDenied, InvalidTransition, NotFound, ValidationError
from .utils import canonical_json, content_hash, parse_json, uid, utcnow


P4_SCHEMA_VERSION = "GWF-VNEXT-P4-PM-WORKASSIGNMENT-PROTOCOL-v1"

PM_ROLE_CLASSES = {"WORKER", "QA_REVIEWER"}
PROPOSAL_STATES = {
    "DRAFT",
    "FROZEN",
    "SUBMITTED",
    "REJECTED",
    "ESCALATED",
    "AUTHORIZED_MATERIALIZED",
    "SUPERSEDED",
}
ACTIVE_WORK_ASSIGNMENT_STATES = {
    "FROZEN",
    "AUTHORIZED",
    "DISPATCHED",
    "RUNNING",
    "VERIFYING",
}
PM_FORBIDDEN_ACTIONS = {
    "CREATE_AUTHORITY",
    "EXPAND_AUTHORITY",
    "EXPAND_BUDGET",
    "EXPOSE_PROTECTED_RESOURCE_PAYLOAD",
    "CONSUME_PROTECTED_RESOURCE",
    "DIRECT_DISPATCH_EXECUTOR",
    "CREATE_SCIENTIFIC_VERDICT",
    "ADMIT_EVIDENCE",
    "CREATE_RELEASE_ACCEPTANCE",
    "OVERRIDE_G2E_AGENT_BINDING",
    "OVERRIDE_GWF_EXECUTOR_BINDING",
    "MUTATE_FROZEN_WORK_ASSIGNMENT",
    "MUTATE_FROZEN_PROOF_OBLIGATION",
    "MUTATE_FROZEN_GOVERNANCE_PROFILE",
    "DOWNGRADE_PROFILE_TO_ESCAPE",
    "REINTERPRET_TERMINAL_LINEAGE",
    "SILENT_WORKER_SUBSTITUTION",
    "SILENT_QA_SUBSTITUTION",
    "INFER_INDEPENDENCE_FROM_PROVIDER_MODEL",
    "TREAT_OPERATIONAL_COMPLETION_AS_EVIDENCE",
    "BYPASS_HUMAN_ACTION_REQUEST",
    "SELF_RESOLVE_HUMAN_ACTION_REQUEST",
    "REQUEST_CAPABILITY_BEYOND_PROFILE",
    "REQUEST_PROTECTED_ACCESS_BEFORE_AUTHORIZATION",
    "ELEVATE_EXPLORATORY_TO_CONFIRMATORY",
    "CHANGE_FROZEN_THRESHOLD_METRIC_SEED",
    "USE_UI_STATE_AS_AUTHORITY",
    "REDEFINE_WORK_ASSIGNMENT",
    "CREATE_REPLACEMENT_G2E_ATTEMPT",
    "USE_MODEL_STRENGTH_AS_AUTHORITY",
    "BYPASS_P1_P2_P3_LOCKS",
}

_FORBIDDEN_PROTECTED_KEYS = {
    "payload",
    "raw_payload",
    "evidence_payload",
    "raw_evidence",
    "secret",
    "password",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "bearer",
}
_EXACT_REF_KEYS = {"object_id", "revision_id", "content_hash"}


def _require_sha256(value: Any, field: str) -> str:
    text = str(value or "")
    if not re.fullmatch(r"[0-9a-f]{64}", text):
        raise ValidationError(f"{field} must be a SHA-256 hex digest")
    return text


def _validate_exact_ref(ref: Mapping[str, Any] | None, field: str, *, required: bool = True) -> dict[str, Any] | None:
    if ref is None:
        if required:
            raise ValidationError(f"{field} is required")
        return None
    if set(ref) != _EXACT_REF_KEYS:
        raise ValidationError(f"{field} must contain exactly object_id/revision_id/content_hash")
    if not ref.get("object_id") or not ref.get("revision_id"):
        raise ValidationError(f"{field} identity is incomplete")
    _require_sha256(ref.get("content_hash"), f"{field}.content_hash")
    return dict(ref)


def _reject_protected_payload(value: Any, *, path: str = "protected_resource_metadata") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).lower() in _FORBIDDEN_PROTECTED_KEYS and item not in (None, "", [], {}):
                raise ValidationError(f"Protected-resource payload is forbidden at {path}.{key}")
            _reject_protected_payload(item, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_protected_payload(item, path=f"{path}[{index}]")


def _sorted_unique(values: Sequence[str]) -> list[str]:
    result = sorted({str(value) for value in values if str(value)})
    if len(result) != len(values):
        raise ValidationError("Capability/action lists must be non-empty and unique")
    return result


class PMWorkAssignmentProtocolVNext:
    """Provider-neutral P4 PM proposal/read-model/handoff protocol.

    The service deliberately has no execution-environment adapter and no
    scientific/evidence authority. Existing P1 WorkAssignment authorization
    and dispatch methods remain the only GWF execution path.
    """

    def __init__(self, db, vnext_governance):
        self.db = db
        self.vnext_governance = vnext_governance
        self._install_schema()

    def _install_schema(self) -> None:
        self.db.conn.executescript(
            """
CREATE TABLE IF NOT EXISTS pm_governed_state_snapshots(
  snapshot_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  state_revision TEXT NOT NULL,
  payload TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pm_plan_revisions(
  plan_id TEXT NOT NULL,
  revision_id TEXT NOT NULL,
  state_snapshot_id TEXT NOT NULL,
  payload TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(plan_id, revision_id)
);
CREATE TABLE IF NOT EXISTS pm_role_requests(
  role_request_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  role_class TEXT NOT NULL,
  payload TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pm_work_assignment_proposals(
  proposal_id TEXT NOT NULL,
  revision_id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  state_snapshot_id TEXT NOT NULL,
  role_request_id TEXT NOT NULL,
  payload TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  state TEXT NOT NULL,
  frozen_hash TEXT,
  materialized_work_assignment_id TEXT UNIQUE,
  created_at TEXT NOT NULL,
  frozen_at TEXT,
  submitted_at TEXT,
  terminal_at TEXT,
  PRIMARY KEY(proposal_id, revision_id)
);
CREATE TABLE IF NOT EXISTS pm_handoff_records(
  handoff_id TEXT PRIMARY KEY,
  revision_id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  state_snapshot_id TEXT NOT NULL,
  payload TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pm_state_project_revision
  ON pm_governed_state_snapshots(project_id, state_revision);
CREATE INDEX IF NOT EXISTS idx_pm_proposal_project_state
  ON pm_work_assignment_proposals(project_id, state);
CREATE INDEX IF NOT EXISTS idx_pm_plan_snapshot
  ON pm_plan_revisions(state_snapshot_id);
"""
        )
        self.db.conn.commit()

    def assert_pm_action_allowed(self, action: str) -> bool:
        if action in PM_FORBIDDEN_ACTIONS:
            raise AuthorityDenied(f"PM action is outside proposal authority: {action}")
        return True

    def _project(self, project_id: str):
        row = self.db.one("SELECT * FROM projects WHERE id=?", (project_id,))
        if not row:
            raise NotFound("Project not found")
        return row

    def _snapshot(self, snapshot_id: str):
        row = self.db.one("SELECT * FROM pm_governed_state_snapshots WHERE snapshot_id=?", (snapshot_id,))
        if not row:
            raise NotFound("PMVisibleGovernedState not found")
        return row

    def _role_request(self, role_request_id: str):
        row = self.db.one("SELECT * FROM pm_role_requests WHERE role_request_id=?", (role_request_id,))
        if not row:
            raise NotFound("PMRoleRequest not found")
        return row

    def _proposal(self, proposal_id: str, revision_id: str):
        row = self.db.one(
            "SELECT * FROM pm_work_assignment_proposals WHERE proposal_id=? AND revision_id=?",
            (proposal_id, revision_id),
        )
        if not row:
            raise NotFound("WorkAssignmentProposal not found")
        return row

    def create_governed_state_snapshot(
        self,
        project_id: str,
        state_revision: str,
        *,
        governance_profile_ref: Mapping[str, Any],
        authority_envelope_ref: Mapping[str, Any],
        budget_envelope_ref: Mapping[str, Any],
        g2e_goal_refs: Sequence[Mapping[str, Any]] = (),
        g2e_claim_refs: Sequence[Mapping[str, Any]] = (),
        g2e_proof_obligation_refs: Sequence[Mapping[str, Any]] = (),
        g2e_execution_attempt_refs: Sequence[Mapping[str, Any]] = (),
        active_work_assignment_refs: Sequence[Mapping[str, Any]] = (),
        human_action_request_refs: Sequence[Mapping[str, Any]] = (),
        resolved_human_action_refs: Sequence[Mapping[str, Any]] = (),
        protected_resource_metadata: Sequence[Mapping[str, Any]] = (),
        allowed_capabilities: Sequence[str] = (),
        policy_digest: str,
    ) -> str:
        self._project(project_id)
        if not state_revision:
            raise ValidationError("state_revision is required")
        _require_sha256(policy_digest, "policy_digest")
        _reject_protected_payload(protected_resource_metadata)
        payload = {
            "schema_version": P4_SCHEMA_VERSION,
            "project_ref": {"project_id": project_id},
            "state_revision": state_revision,
            "governance_profile_ref": dict(governance_profile_ref),
            "authority_envelope_ref": dict(authority_envelope_ref),
            "budget_envelope_ref": dict(budget_envelope_ref),
            "g2e_goal_refs": [dict(x) for x in g2e_goal_refs],
            "g2e_claim_refs": [dict(x) for x in g2e_claim_refs],
            "g2e_proof_obligation_refs": [dict(x) for x in g2e_proof_obligation_refs],
            "g2e_execution_attempt_refs": [dict(x) for x in g2e_execution_attempt_refs],
            "active_work_assignment_refs": [dict(x) for x in active_work_assignment_refs],
            "human_action_request_refs": [dict(x) for x in human_action_request_refs],
            "resolved_human_action_refs": [dict(x) for x in resolved_human_action_refs],
            "protected_resource_metadata": [dict(x) for x in protected_resource_metadata],
            "allowed_capabilities": _sorted_unique(list(allowed_capabilities)),
            "policy_digest": policy_digest,
        }
        snapshot_id = uid("pmstate")
        ph = content_hash(payload)
        self.db.conn.execute(
            "INSERT INTO pm_governed_state_snapshots VALUES(?,?,?,?,?,?)",
            (snapshot_id, project_id, state_revision, canonical_json(payload), ph, utcnow()),
        )
        self.db.conn.commit()
        return snapshot_id

    def create_plan_revision(
        self,
        plan_id: str,
        revision_id: str,
        state_snapshot_id: str,
        *,
        objective_summary: Mapping[str, Any],
        dependency_refs: Sequence[Mapping[str, Any]],
        proposal_refs: Sequence[Mapping[str, Any]],
        created_by_pm_identity_ref: Mapping[str, Any],
    ) -> str:
        if not plan_id or not revision_id:
            raise ValidationError("plan_id and revision_id are required")
        self._snapshot(state_snapshot_id)
        payload = {
            "plan_id": plan_id,
            "revision_id": revision_id,
            "state_snapshot_id": state_snapshot_id,
            "objective_summary": dict(objective_summary),
            "dependency_refs": [dict(x) for x in dependency_refs],
            "proposal_refs": [dict(x) for x in proposal_refs],
            "created_by_pm_identity_ref": dict(created_by_pm_identity_ref),
        }
        ph = content_hash(payload)
        self.db.conn.execute(
            "INSERT INTO pm_plan_revisions VALUES(?,?,?,?,?,?)",
            (plan_id, revision_id, state_snapshot_id, canonical_json(payload), ph, utcnow()),
        )
        self.db.conn.commit()
        return ph

    def create_role_request(
        self,
        project_id: str,
        role_class: str,
        *,
        source_obligation_ref: Mapping[str, Any],
        required_capabilities: Sequence[str],
        authority_ceiling_ref: Mapping[str, Any],
        budget_ceiling_ref: Mapping[str, Any],
        execution_environment_class_request: str,
        expected_outputs: Sequence[Mapping[str, Any]],
        independence_requirements: Mapping[str, Any] | None = None,
    ) -> str:
        self._project(project_id)
        if role_class not in PM_ROLE_CLASSES:
            raise ValidationError("Unknown PM role class")
        if not execution_environment_class_request:
            raise ValidationError("Execution-environment class request is required")
        if role_class == "QA_REVIEWER":
            required_dimensions = list((independence_requirements or {}).get("required_dimensions") or [])
            if not required_dimensions:
                raise ValidationError("QA role request requires explicit independence dimensions")
        payload = {
            "project_id": project_id,
            "role_class": role_class,
            "source_obligation_ref": dict(source_obligation_ref),
            "required_capabilities": _sorted_unique(list(required_capabilities)),
            "authority_ceiling_ref": dict(authority_ceiling_ref),
            "budget_ceiling_ref": dict(budget_ceiling_ref),
            "execution_environment_class_request": execution_environment_class_request,
            "expected_outputs": [dict(x) for x in expected_outputs],
            "independence_requirements": dict(independence_requirements or {}),
        }
        role_request_id = uid("pmrole")
        ph = content_hash(payload)
        self.db.conn.execute(
            "INSERT INTO pm_role_requests VALUES(?,?,?,?,?,?)",
            (role_request_id, project_id, role_class, canonical_json(payload), ph, utcnow()),
        )
        self.db.conn.commit()
        return role_request_id

    def create_work_assignment_proposal(
        self,
        project_id: str,
        state_snapshot_id: str,
        role_request_id: str,
        *,
        proposal_id: str | None = None,
        revision_id: str = "r1",
        source_goal_ref: Mapping[str, Any] | None,
        source_claim_ref: Mapping[str, Any] | None,
        source_proof_obligation_ref: Mapping[str, Any],
        source_execution_attempt_ref: Mapping[str, Any],
        objective: Mapping[str, Any],
        requested_execution_environment_class: str,
        requested_capabilities: Sequence[str],
        requested_authority_scope: Mapping[str, Any],
        requested_budget: Sequence[Mapping[str, Any]],
        authority_envelope_ref: Mapping[str, Any],
        budget_envelope_ref: Mapping[str, Any],
        protected_resource_constraints: Sequence[Mapping[str, Any]],
        required_human_action_refs: Sequence[Mapping[str, Any]],
        expected_outputs: Sequence[Mapping[str, Any]],
        handoff_contract: Mapping[str, Any],
    ) -> tuple[str, str]:
        self._project(project_id)
        snapshot = self._snapshot(state_snapshot_id)
        if snapshot["project_id"] != project_id:
            raise ValidationError("Proposal snapshot belongs to a different project")
        role = self._role_request(role_request_id)
        if role["project_id"] != project_id:
            raise ValidationError("Role request belongs to a different project")
        _validate_exact_ref(source_goal_ref, "source_goal_ref", required=False)
        _validate_exact_ref(source_claim_ref, "source_claim_ref", required=False)
        _validate_exact_ref(source_proof_obligation_ref, "source_proof_obligation_ref")
        _validate_exact_ref(source_execution_attempt_ref, "source_execution_attempt_ref")
        if not requested_execution_environment_class:
            raise ValidationError("Execution-environment class request is required")
        _reject_protected_payload(protected_resource_constraints, path="protected_resource_constraints")
        role_payload = parse_json(role["payload"], {})
        if requested_execution_environment_class != role_payload["execution_environment_class_request"]:
            raise ValidationError("Proposal cannot silently substitute execution-environment class")
        if set(requested_capabilities) != set(role_payload["required_capabilities"]):
            raise ValidationError("Proposal cannot silently substitute requested capabilities")
        pid = proposal_id or uid("wapprop")
        payload = {
            "schema_version": P4_SCHEMA_VERSION,
            "proposal_id": pid,
            "revision_id": revision_id,
            "state_snapshot_id": state_snapshot_id,
            "governed_state_revision": snapshot["state_revision"],
            "project_ref": {"project_id": project_id},
            "source_goal_ref": dict(source_goal_ref) if source_goal_ref else None,
            "source_claim_ref": dict(source_claim_ref) if source_claim_ref else None,
            "source_proof_obligation_ref": dict(source_proof_obligation_ref),
            "source_execution_attempt_ref": dict(source_execution_attempt_ref),
            "objective": dict(objective),
            "role_request_ref": {
                "role_request_id": role_request_id,
                "content_hash": role["content_hash"],
                "role_class": role["role_class"],
            },
            "requested_execution_environment_class": requested_execution_environment_class,
            "requested_capabilities": _sorted_unique(list(requested_capabilities)),
            "requested_authority_scope": dict(requested_authority_scope),
            "requested_budget": [dict(x) for x in requested_budget],
            "authority_envelope_ref": dict(authority_envelope_ref),
            "budget_envelope_ref": dict(budget_envelope_ref),
            "protected_resource_constraints": [dict(x) for x in protected_resource_constraints],
            "required_human_action_refs": [dict(x) for x in required_human_action_refs],
            "expected_outputs": [dict(x) for x in expected_outputs],
            "handoff_contract": dict(handoff_contract),
        }
        ph = content_hash(payload)
        self.db.conn.execute(
            "INSERT INTO pm_work_assignment_proposals("
            "proposal_id,revision_id,project_id,state_snapshot_id,role_request_id,payload,"
            "content_hash,state,frozen_hash,materialized_work_assignment_id,created_at,frozen_at,submitted_at,terminal_at"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                pid,
                revision_id,
                project_id,
                state_snapshot_id,
                role_request_id,
                canonical_json(payload),
                ph,
                "DRAFT",
                None,
                None,
                utcnow(),
                None,
                None,
                None,
            ),
        )
        self.db.conn.commit()
        return pid, ph

    def validate_proposal_integrity(self, proposal_id: str, revision_id: str) -> dict[str, Any]:
        row = self._proposal(proposal_id, revision_id)
        payload = parse_json(row["payload"], {})
        if content_hash(payload) != row["content_hash"]:
            raise ValidationError("Proposal payload hash mismatch")
        if payload.get("proposal_id") != proposal_id or payload.get("revision_id") != revision_id:
            raise ValidationError("Proposal identity drift")
        if payload.get("state_snapshot_id") != row["state_snapshot_id"]:
            raise ValidationError("Proposal snapshot identity drift")
        role_ref = payload.get("role_request_ref") or {}
        if role_ref.get("role_request_id") != row["role_request_id"]:
            raise ValidationError("Proposal role-request identity drift")
        role = self._role_request(row["role_request_id"])
        if role_ref.get("content_hash") != role["content_hash"] or role_ref.get("role_class") != role["role_class"]:
            raise ValidationError("Proposal role request was silently substituted")
        if row["frozen_hash"] and row["frozen_hash"] != row["content_hash"]:
            raise ValidationError("Frozen proposal hash mismatch")
        return payload

    def freeze_proposal(self, proposal_id: str, revision_id: str) -> str:
        row = self._proposal(proposal_id, revision_id)
        if row["state"] != "DRAFT":
            raise InvalidTransition("Only DRAFT proposal may be frozen")
        self.validate_proposal_integrity(proposal_id, revision_id)
        self.db.conn.execute(
            "UPDATE pm_work_assignment_proposals SET state='FROZEN',frozen_hash=content_hash,frozen_at=? "
            "WHERE proposal_id=? AND revision_id=?",
            (utcnow(), proposal_id, revision_id),
        )
        self.db.conn.commit()
        return row["content_hash"]

    def submit_proposal(self, proposal_id: str, revision_id: str, expected_hash: str) -> None:
        row = self._proposal(proposal_id, revision_id)
        if row["state"] != "FROZEN":
            raise InvalidTransition("Only FROZEN proposal may be submitted")
        if row["frozen_hash"] != expected_hash or row["content_hash"] != expected_hash:
            raise ValidationError("Submitted proposal hash mismatch")
        self.validate_proposal_integrity(proposal_id, revision_id)
        self.db.conn.execute(
            "UPDATE pm_work_assignment_proposals SET state='SUBMITTED',submitted_at=? "
            "WHERE proposal_id=? AND revision_id=?",
            (utcnow(), proposal_id, revision_id),
        )
        self.db.conn.commit()

    def mark_rejected(self, proposal_id: str, revision_id: str) -> None:
        row = self._proposal(proposal_id, revision_id)
        if row["state"] not in {"FROZEN", "SUBMITTED", "ESCALATED"}:
            raise InvalidTransition("Proposal cannot be rejected from current state")
        self.db.conn.execute(
            "UPDATE pm_work_assignment_proposals SET state='REJECTED',terminal_at=? "
            "WHERE proposal_id=? AND revision_id=?",
            (utcnow(), proposal_id, revision_id),
        )
        self.db.conn.commit()

    def mark_escalated(self, proposal_id: str, revision_id: str) -> None:
        row = self._proposal(proposal_id, revision_id)
        if row["state"] != "SUBMITTED":
            raise InvalidTransition("Only SUBMITTED proposal may be escalated")
        self.db.conn.execute(
            "UPDATE pm_work_assignment_proposals SET state='ESCALATED' WHERE proposal_id=? AND revision_id=?",
            (proposal_id, revision_id),
        )
        self.db.conn.commit()

    def supersede_proposal(self, proposal_id: str, revision_id: str, successor_revision_id: str) -> None:
        row = self._proposal(proposal_id, revision_id)
        if row["state"] in {"AUTHORIZED_MATERIALIZED", "REJECTED", "SUPERSEDED"}:
            raise InvalidTransition("Terminal proposal revision cannot be superseded")
        successor = self._proposal(proposal_id, successor_revision_id)
        if successor["revision_id"] == revision_id:
            raise ValidationError("Successor revision must differ")
        self.db.conn.execute(
            "UPDATE pm_work_assignment_proposals SET state='SUPERSEDED',terminal_at=? "
            "WHERE proposal_id=? AND revision_id=?",
            (utcnow(), proposal_id, revision_id),
        )
        self.db.conn.commit()

    def _validate_authority_scope(self, authority_envelope_ref: Mapping[str, Any], requested_scope: Mapping[str, Any]) -> None:
        authority_id = authority_envelope_ref.get("authority_envelope_id")
        if not authority_id:
            raise ValidationError("authority_envelope_ref is required")
        effective = self.vnext_governance.effective_authority(str(authority_id))
        requested_actions = set(requested_scope.get("allow_actions") or [])
        if not requested_actions.issubset(set(effective["allow_actions"])):
            raise AuthorityDenied("Requested authority exceeds active AuthorityEnvelope")
        effective_resources = {canonical_json(x) for x in effective["resource_selectors"]}
        requested_resources = {canonical_json(x) for x in requested_scope.get("resource_selectors") or []}
        if not requested_resources.issubset(effective_resources):
            raise AuthorityDenied("Requested resource scope exceeds active AuthorityEnvelope")

    def _validate_budget(self, budget_envelope_ref: Mapping[str, Any], requested_budget: Sequence[Mapping[str, Any]]) -> None:
        budget_id = budget_envelope_ref.get("budget_envelope_id")
        if not budget_id:
            raise ValidationError("budget_envelope_ref is required")
        effective = self.vnext_governance.effective_budget(str(budget_id))
        limits = {item["dimension"]: item for item in effective["limits"]}
        for item in requested_budget:
            dimension = item.get("dimension")
            amount = item.get("amount")
            if dimension not in limits or not isinstance(amount, (int, float)) or amount < 0:
                raise ValidationError("Invalid requested budget")
            if float(amount) > float(limits[dimension]["ceiling"]):
                raise AuthorityDenied("Requested budget exceeds active BudgetEnvelope")

    def materialization_payload(
        self,
        proposal_id: str,
        revision_id: str,
        *,
        current_state_revision: str,
        protected_access_authorized: bool = False,
    ) -> dict[str, Any]:
        row = self._proposal(proposal_id, revision_id)
        if row["state"] != "SUBMITTED":
            raise InvalidTransition("Only SUBMITTED proposal can enter GWF materialization")
        payload = self.validate_proposal_integrity(proposal_id, revision_id)
        snapshot = self._snapshot(row["state_snapshot_id"])
        if snapshot["state_revision"] != current_state_revision:
            raise InvalidTransition("Proposal is stale against current governed-state revision")
        snapshot_payload = parse_json(snapshot["payload"], {})
        allowed_capabilities = set(snapshot_payload.get("allowed_capabilities") or [])
        requested_capabilities = set(payload["requested_capabilities"])
        if not requested_capabilities.issubset(allowed_capabilities):
            raise AuthorityDenied("Requested capability exceeds active governed profile")
        self._validate_authority_scope(payload["authority_envelope_ref"], payload["requested_authority_scope"])
        self._validate_budget(payload["budget_envelope_ref"], payload["requested_budget"])
        if payload["protected_resource_constraints"] and not protected_access_authorized:
            raise AuthorityDenied("Protected-resource access is not authorized")
        resolved_har = {
            canonical_json(x)
            for x in snapshot_payload.get("resolved_human_action_refs") or []
        }
        required_har = {canonical_json(x) for x in payload.get("required_human_action_refs") or []}
        if not required_har.issubset(resolved_har):
            raise AuthorityDenied("Required HumanActionRequest is unresolved")
        role = self._role_request(row["role_request_id"])
        role_payload = parse_json(role["payload"], {})
        role_class = role["role_class"]
        if payload["requested_execution_environment_class"] != role_payload["execution_environment_class_request"]:
            raise ValidationError("Execution-environment class substitution detected")
        if set(payload["requested_capabilities"]) != set(role_payload["required_capabilities"]):
            raise ValidationError("Role/capability substitution detected")
        if role_class == "QA_REVIEWER":
            required_dimensions = list((role_payload.get("independence_requirements") or {}).get("required_dimensions") or [])
            if not required_dimensions:
                raise ValidationError("QA independence requirements are missing")
        origin_refs = []
        for schema_kind, ref in (
            ("goal", payload.get("source_goal_ref")),
            ("claim", payload.get("source_claim_ref")),
            ("proof_obligation", payload["source_proof_obligation_ref"]),
            ("execution_attempt_envelope", payload["source_execution_attempt_ref"]),
        ):
            if ref:
                origin_refs.append({"system": "G2E", "schema_kind": schema_kind, "exact_ref": dict(ref)})
        return {
            "project_id": row["project_id"],
            "origin_refs": origin_refs,
            "objective": payload["objective"],
            "agent_role_ref": {"role": role_class},
            "required_capabilities": payload["requested_capabilities"],
            "execution_environment_constraints": {
                "environment_class": payload["requested_execution_environment_class"],
                "provider_neutral": True,
            },
            "authority_envelope_ref": payload["authority_envelope_ref"],
            "budget_envelope_ref": payload["budget_envelope_ref"],
            "protected_resource_constraints": payload["protected_resource_constraints"],
            "expected_outputs": payload["expected_outputs"],
            "completion_contract": payload["handoff_contract"],
            "independence_requirements": role_payload.get("independence_requirements") or None,
        }

    def record_materialization(
        self,
        proposal_id: str,
        revision_id: str,
        work_assignment_id: str,
        *,
        current_state_revision: str,
        protected_access_authorized: bool = False,
    ) -> None:
        expected = self.materialization_payload(
            proposal_id,
            revision_id,
            current_state_revision=current_state_revision,
            protected_access_authorized=protected_access_authorized,
        )
        assignment = self.db.one(
            "SELECT * FROM work_assignments WHERE work_assignment_id=?",
            (work_assignment_id,),
        )
        if not assignment:
            raise NotFound("WorkAssignment not found")
        if assignment["project_id"] != expected["project_id"]:
            raise ValidationError("WorkAssignment project mismatch")
        if assignment["state"] not in {"AUTHORIZED", "DISPATCHED", "RUNNING", "VERIFYING", "COMPLETED", "BLOCKED"}:
            raise AuthorityDenied("GWF-authorized WorkAssignment is required before materialization record")
        actual = {
            "project_id": assignment["project_id"],
            "origin_refs": parse_json(assignment["origin_refs"], []),
            "objective": parse_json(assignment["objective"], {}),
            "agent_role_ref": parse_json(assignment["agent_role_ref"], {}),
            "required_capabilities": parse_json(assignment["required_capabilities"], []),
            "execution_environment_constraints": parse_json(assignment["execution_environment_constraints"], {}),
            "authority_envelope_ref": parse_json(assignment["authority_envelope_ref"], {}),
            "budget_envelope_ref": parse_json(assignment["budget_envelope_ref"], {}),
            "protected_resource_constraints": parse_json(assignment["protected_resource_constraints"], []),
            "expected_outputs": parse_json(assignment["expected_outputs"], []),
            "completion_contract": parse_json(assignment["completion_contract"], {}),
            "independence_requirements": (
                parse_json(assignment["independence_requirements"], {})
                if assignment["independence_requirements"]
                else None
            ),
        }
        if canonical_json(actual) != canonical_json(expected):
            raise ValidationError("Authorized WorkAssignment does not match frozen PM proposal")
        existing = self.db.one(
            "SELECT proposal_id,revision_id FROM pm_work_assignment_proposals "
            "WHERE materialized_work_assignment_id=?",
            (work_assignment_id,),
        )
        if existing and (existing["proposal_id"], existing["revision_id"]) != (proposal_id, revision_id):
            raise InvalidTransition("One WorkAssignment cannot materialize multiple proposal revisions")
        self.db.conn.execute(
            "UPDATE pm_work_assignment_proposals "
            "SET state='AUTHORIZED_MATERIALIZED',materialized_work_assignment_id=?,terminal_at=? "
            "WHERE proposal_id=? AND revision_id=?",
            (work_assignment_id, utcnow(), proposal_id, revision_id),
        )
        self.db.conn.commit()

    def create_handoff_record(
        self,
        project_id: str,
        revision_id: str,
        state_snapshot_id: str,
        *,
        current_state_revision: str,
        pm_plan_ref: Mapping[str, Any],
        proposal_refs: Sequence[Mapping[str, Any]],
        unresolved_human_action_refs: Sequence[Mapping[str, Any]],
        active_work_assignment_refs: Sequence[Mapping[str, Any]],
        next_allowed_action: str,
    ) -> tuple[str, str]:
        snapshot = self._snapshot(state_snapshot_id)
        if snapshot["project_id"] != project_id:
            raise ValidationError("Handoff snapshot project mismatch")
        if snapshot["state_revision"] != current_state_revision:
            raise InvalidTransition("Recovery/handoff must bind current governed-state revision")
        canonical_proposals: list[dict[str, Any]] = []
        for ref in proposal_refs:
            pid = ref.get("proposal_id")
            rid = ref.get("revision_id")
            row = self._proposal(str(pid), str(rid))
            if row["project_id"] != project_id:
                raise ValidationError("Handoff proposal project mismatch")
            if ref.get("content_hash") != row["content_hash"]:
                raise ValidationError("Handoff cannot silently change proposal identity")
            canonical_proposals.append(
                {"proposal_id": pid, "revision_id": rid, "content_hash": row["content_hash"]}
            )
        payload = {
            "revision_id": revision_id,
            "state_snapshot_id": state_snapshot_id,
            "governed_state_revision": current_state_revision,
            "pm_plan_ref": dict(pm_plan_ref),
            "proposal_refs": canonical_proposals,
            "unresolved_human_action_refs": [dict(x) for x in unresolved_human_action_refs],
            "active_work_assignment_refs": [dict(x) for x in active_work_assignment_refs],
            "next_allowed_action": next_allowed_action,
        }
        handoff_id = uid("pmhandoff")
        ph = content_hash(payload)
        self.db.conn.execute(
            "INSERT INTO pm_handoff_records VALUES(?,?,?,?,?,?,?)",
            (handoff_id, revision_id, project_id, state_snapshot_id, canonical_json(payload), ph, utcnow()),
        )
        self.db.conn.commit()
        return handoff_id, ph
