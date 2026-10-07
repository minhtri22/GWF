from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from .errors import AuthorityDenied, InvalidTransition, NotFound, ValidationError
from .utils import canonical_json, parse_json


P3_G2E_MAPPING_VERSION = "gwf-vnext-p3-g2e-bridge-v1"
G2E_IDENTITY_FIELDS = ("agent_app", "provider_ref", "model_ref", "harness_ref", "transport_ref")
ACTIVE_ASSIGNMENT_STATES = {"FROZEN", "AUTHORIZED", "DISPATCHED", "RUNNING", "VERIFYING", "COMPLETED"}
FRESHNESS_STATES = ("FRESH", "RESERVED", "EXPOSED")
TERMINAL_ADJUDICATION_VERDICTS = {"PASS", "FAIL", "INVALID", "UNRESOLVED"}
IMPORTABLE_RUNTIME_CATEGORY = "canonical_core"
SELECTIVE_PORT_CATEGORY = "reusable_adapter"


@dataclass(frozen=True)
class G2EExactRef:
    object_id: str
    revision_id: str
    content_hash: str

    @classmethod
    def parse(cls, value: Mapping[str, Any]) -> "G2EExactRef":
        if not isinstance(value, Mapping):
            raise ValidationError("G2E exact ref must be an object")
        object_id = value.get("object_id")
        revision_id = value.get("revision_id")
        content_hash = value.get("content_hash")
        if not isinstance(object_id, str) or not object_id:
            raise ValidationError("G2E exact ref requires object_id")
        if not isinstance(revision_id, str) or not revision_id:
            raise ValidationError("G2E exact ref requires revision_id")
        if not isinstance(content_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", content_hash):
            raise ValidationError("G2E exact ref requires lowercase SHA-256 content_hash")
        return cls(object_id, revision_id, content_hash)

    def to_dict(self) -> dict[str, str]:
        return {
            "object_id": self.object_id,
            "revision_id": self.revision_id,
            "content_hash": self.content_hash,
        }

    def token(self) -> str:
        return f"{self.object_id}@{self.revision_id}#{self.content_hash}"


def g2e_bridge_ref(schema_kind: str, exact_ref: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(schema_kind, str) or not schema_kind:
        raise ValidationError("schema_kind is required")
    ref = G2EExactRef.parse(exact_ref)
    return {
        "system": "G2E",
        "schema_kind": schema_kind,
        "exact_ref": ref.to_dict(),
    }


def _bridge_ref(value: Mapping[str, Any], expected_kind: str | None = None) -> tuple[str, G2EExactRef]:
    if not isinstance(value, Mapping) or value.get("system") != "G2E":
        raise ValidationError("Expected G2E bridge reference")
    kind = value.get("schema_kind")
    if not isinstance(kind, str) or not kind:
        raise ValidationError("G2E bridge reference requires schema_kind")
    if expected_kind is not None and kind != expected_kind:
        raise ValidationError(
            "G2E bridge reference schema kind mismatch",
            details={"expected": expected_kind, "actual": kind},
        )
    return kind, G2EExactRef.parse(value.get("exact_ref") or {})


def _same_bridge_ref(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    try:
        lk, lr = _bridge_ref(left)
        rk, rr = _bridge_ref(right)
    except ValidationError:
        return False
    return lk == rk and lr == rr


def _payload_sha256(payload: Any) -> str:
    # This digest is for external evidence payload integrity only.  It is NOT a
    # G2E canonical object hash and must never be used as one.
    normalized = unicodedata.normalize("NFC", json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _exact_mapping_ref(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValidationError("Mapping ref must be an object")
    if not value.get("kind") or not value.get("id"):
        raise ValidationError("Mapping ref requires kind and id")
    return {"kind": str(value["kind"]), "id": str(value["id"])}


class G2EGWFBridgeVNext:
    """Provider-neutral P3 reconciliation layer.

    It validates G2E canonical foreign identities against GWF vNext governed
    runtime objects.  It deliberately does not import G2E runtime code, execute
    providers, admit scientific evidence, or create scientific verdicts.
    """

    def __init__(self, runtime):
        self.runtime = runtime
        self.db = runtime.db
        self.vnext = runtime.vnext_governance

    # ------------------------------------------------------------------
    # Canonical identity / mapping
    # ------------------------------------------------------------------
    @staticmethod
    def mapping_record(
        project_id: str,
        schema_kind: str,
        g2e_exact_ref: Mapping[str, Any],
        gwf_mapping_ref: Mapping[str, Any],
        gwf_content_hash: str,
        *,
        active: bool = True,
        mapping_version: str = P3_G2E_MAPPING_VERSION,
    ) -> dict[str, Any]:
        ref = G2EExactRef.parse(g2e_exact_ref)
        if mapping_version != P3_G2E_MAPPING_VERSION:
            raise ValidationError("Unsupported G2E/GWF mapping version")
        if not isinstance(gwf_content_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", gwf_content_hash):
            raise ValidationError("GWF mapping content hash must be SHA-256")
        return {
            "mapping_version": mapping_version,
            "mapping_scope": {"project_id": project_id, "mapping_version": mapping_version},
            "schema_kind": schema_kind,
            "g2e_exact_ref": ref.to_dict(),
            "gwf_mapping_ref": _exact_mapping_ref(gwf_mapping_ref),
            "gwf_content_hash": gwf_content_hash,
            "hash_domains": {"g2e": "G2E_CANONICAL", "gwf": "GWF_RUNTIME"},
            "active": bool(active),
        }

    @staticmethod
    def validate_mapping_record(record: Mapping[str, Any]) -> bool:
        if record.get("mapping_version") != P3_G2E_MAPPING_VERSION:
            raise ValidationError("Unsupported G2E/GWF mapping version")
        scope = record.get("mapping_scope") or {}
        if scope.get("mapping_version") != P3_G2E_MAPPING_VERSION or not scope.get("project_id"):
            raise ValidationError("Invalid mapping scope")
        if not record.get("schema_kind"):
            raise ValidationError("Mapping requires schema_kind")
        G2EExactRef.parse(record.get("g2e_exact_ref") or {})
        _exact_mapping_ref(record.get("gwf_mapping_ref") or {})
        domains = record.get("hash_domains") or {}
        if domains != {"g2e": "G2E_CANONICAL", "gwf": "GWF_RUNTIME"}:
            raise ValidationError("G2E/GWF hash domains must remain explicit and distinct")
        if not re.fullmatch(r"[0-9a-f]{64}", str(record.get("gwf_content_hash") or "")):
            raise ValidationError("Invalid GWF runtime hash")
        return True

    @classmethod
    def assert_mapping_uniqueness(cls, records: Sequence[Mapping[str, Any]]) -> bool:
        seen: dict[tuple[str, str, str, str], tuple[str, str]] = {}
        for item in records:
            cls.validate_mapping_record(item)
            if not item.get("active", True):
                continue
            scope = item["mapping_scope"]
            ref = G2EExactRef.parse(item["g2e_exact_ref"])
            key = (scope["project_id"], scope["mapping_version"], item["schema_kind"], ref.token())
            target = (item["gwf_mapping_ref"]["kind"], item["gwf_mapping_ref"]["id"])
            previous = seen.get(key)
            if previous is not None and previous != target:
                raise ValidationError("Conflicting active GWF mirrors for one G2E exact ref")
            seen[key] = target
        return True

    @staticmethod
    def assert_hash_domain_separation(g2e_exact_ref: Mapping[str, Any], gwf_content_hash: str, *, semantic_substitution: bool = False) -> bool:
        G2EExactRef.parse(g2e_exact_ref)
        if not re.fullmatch(r"[0-9a-f]{64}", str(gwf_content_hash or "")):
            raise ValidationError("Invalid GWF runtime hash")
        if semantic_substitution:
            raise ValidationError("GWF content hash cannot substitute for G2E canonical hash")
        return True

    # ------------------------------------------------------------------
    # Proof / attempt / WorkAssignment bridge
    # ------------------------------------------------------------------
    def _assignment(self, work_assignment_id: str):
        row = self.db.one("SELECT * FROM work_assignments WHERE work_assignment_id=?", (work_assignment_id,))
        if not row:
            raise NotFound("WorkAssignment not found")
        return row

    @staticmethod
    def _find_origin(origin_refs: Sequence[Mapping[str, Any]], schema_kind: str) -> list[G2EExactRef]:
        refs: list[G2EExactRef] = []
        for item in origin_refs:
            if isinstance(item, Mapping) and item.get("system") == "G2E" and item.get("schema_kind") == schema_kind:
                refs.append(_bridge_ref(item, schema_kind)[1])
        return refs

    def validate_work_assignment_bridge(
        self,
        work_assignment_id: str,
        proof_ref: Mapping[str, Any],
        attempt_ref: Mapping[str, Any],
        *,
        protected_resource_refs: Sequence[Mapping[str, Any]] = (),
        independence_requirements: Mapping[str, Any] | None = None,
    ) -> bool:
        row = self._assignment(work_assignment_id)
        expected_proof = G2EExactRef.parse(proof_ref)
        expected_attempt = G2EExactRef.parse(attempt_ref)
        origins = parse_json(row["origin_refs"], [])
        proofs = self._find_origin(origins, "proof_obligation")
        attempts = self._find_origin(origins, "execution_attempt_envelope")
        if proofs != [expected_proof]:
            raise ValidationError("WorkAssignment must bind exactly one exact G2E ProofObligation ref")
        if attempts != [expected_attempt]:
            raise ValidationError("WorkAssignment must bind exactly one exact G2E ExecutionAttempt ref")

        current_constraints = parse_json(row["protected_resource_constraints"], [])
        expected_tokens = {
            _bridge_ref(item, "protected_resource")[1].token()
            for item in protected_resource_refs
        }
        actual_tokens = {
            _bridge_ref(item, "protected_resource")[1].token()
            for item in current_constraints
            if isinstance(item, Mapping) and item.get("system") == "G2E" and item.get("schema_kind") == "protected_resource"
        }
        if expected_tokens != actual_tokens:
            raise ValidationError("Protected resource exact refs are not preserved in WorkAssignment")

        if independence_requirements is not None:
            mirror = parse_json(row["independence_requirements"], {}) if row["independence_requirements"] else {}
            required = set(independence_requirements.get("required_dimensions") or [])
            mirrored = set(mirror.get("required_dimensions") or [])
            if not required.issubset(mirrored):
                raise ValidationError("GWF independence requirements weaken G2E IndependencePolicy")

        # One frozen/authorized/active dispatch mapping per G2E attempt.
        for other in self.db.all("SELECT * FROM work_assignments WHERE project_id=?", (row["project_id"],)):
            if other["work_assignment_id"] == work_assignment_id or other["state"] not in ACTIVE_ASSIGNMENT_STATES:
                continue
            other_origins = parse_json(other["origin_refs"], [])
            other_attempts = self._find_origin(other_origins, "execution_attempt_envelope")
            if expected_attempt in other_attempts:
                raise InvalidTransition("One G2E ExecutionAttempt cannot map to multiple active WorkAssignments")
        return True

    @staticmethod
    def assert_runtime_retry_does_not_create_attempt(original_attempt_id: str, candidate_attempt_id: str, *, runtime_retry: bool) -> bool:
        if runtime_retry and original_attempt_id != candidate_attempt_id:
            raise InvalidTransition("GWF runtime retry cannot create a replacement G2E attempt")
        return True

    # ------------------------------------------------------------------
    # AgentBinding / ExecutorBinding reconciliation
    # ------------------------------------------------------------------
    def _executor_binding(self, executor_binding_id: str):
        row = self.db.one("SELECT * FROM executor_bindings WHERE executor_binding_id=?", (executor_binding_id,))
        if not row:
            raise NotFound("ExecutorBinding not found")
        return row

    @staticmethod
    def _agent_manifest_capabilities(manifest: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
        result: dict[str, Mapping[str, Any]] = {}
        for cap in manifest.get("capabilities") or []:
            cid = cap.get("capability_id") if isinstance(cap, Mapping) else None
            if not cid or cid in result:
                raise ValidationError("AgentCapabilityManifest capability IDs must be unique and non-empty")
            result[str(cid)] = cap
        return result

    def validate_agent_executor_binding(
        self,
        work_assignment_id: str,
        executor_binding_id: str,
        attempt: Mapping[str, Any],
        agent_binding: Mapping[str, Any] | None,
        agent_manifest: Mapping[str, Any] | None,
        *,
        qualification_grant_used_for_dispatch: bool = False,
    ) -> bool:
        row = self._assignment(work_assignment_id)
        executor = self._executor_binding(executor_binding_id)
        if executor["work_assignment_id"] != work_assignment_id:
            raise ValidationError("ExecutorBinding does not belong to WorkAssignment")

        agent_backed = bool(attempt.get("agent_binding_ref") or any(attempt.get(k) is not None for k in G2E_IDENTITY_FIELDS))
        if agent_backed and agent_binding is None:
            raise ValidationError("Agent-backed G2E attempt requires AgentBinding")
        if not agent_backed and agent_binding is not None:
            raise ValidationError("Non-agent G2E attempt cannot invent an AgentBinding")

        if agent_binding is None:
            if qualification_grant_used_for_dispatch:
                raise AuthorityDenied("QualificationAuthorityGrant cannot authorize operational dispatch")
            return True
        if agent_manifest is None:
            raise ValidationError("AgentBinding requires exact AgentCapabilityManifest")

        attempt_id = attempt.get("attempt_id")
        if not attempt_id or agent_binding.get("resolved_attempt_id") != attempt_id:
            raise ValidationError("AgentBinding resolved_attempt_id mismatch")

        binding_ref = agent_binding.get("exact_ref")
        if not binding_ref or attempt.get("agent_binding_ref") != binding_ref:
            raise ValidationError("ExecutionAttempt does not bind the exact AgentBinding ref")

        manifest_ref = agent_manifest.get("exact_ref")
        if not manifest_ref or agent_binding.get("capability_manifest_ref") != manifest_ref:
            raise ValidationError("AgentBinding capability manifest ref mismatch")

        gwf_cap_ref = parse_json(executor["capability_manifest_ref"], {})
        if gwf_cap_ref != manifest_ref:
            raise ValidationError("ExecutorBinding must map the exact G2E AgentCapabilityManifest")

        env_ref = parse_json(executor["execution_environment_ref"], {})
        env = self.db.one(
            "SELECT * FROM execution_environments WHERE execution_environment_id=?",
            (env_ref.get("execution_environment_id"),),
        )
        if not env:
            raise NotFound("ExecutionEnvironmentRef cannot be resolved")
        environment_cap_ref = parse_json(env["capability_manifest_ref"], {})
        if environment_cap_ref == manifest_ref:
            raise ValidationError("Execution-environment capability manifest cannot substitute for AgentCapabilityManifest")

        g2e_mode = agent_binding.get("binding_mode")
        gwf_mode = executor["binding_mode"]
        if g2e_mode not in {"DYNAMIC", "FROZEN"}:
            raise ValidationError("Invalid G2E AgentBinding mode")
        if g2e_mode == "FROZEN" and gwf_mode != "FROZEN":
            raise ValidationError("G2E FROZEN AgentBinding requires GWF FROZEN ExecutorBinding")

        identity = parse_json(executor["agent_identity"], {})
        expected_identity = {k: agent_binding.get(k) for k in G2E_IDENTITY_FIELDS if agent_binding.get(k) is not None}
        if set(identity) != set(expected_identity):
            raise ValidationError("ExecutorBinding agent_identity is not an exact non-widening G2E projection")
        for key, value in expected_identity.items():
            if identity.get(key) != value:
                raise ValidationError("ExecutorBinding agent identity mismatch", details={"dimension": key})

        for key in G2E_IDENTITY_FIELDS:
            attempt_value = attempt.get(key)
            binding_value = agent_binding.get(key)
            if attempt_value is not None and attempt_value != binding_value:
                raise ValidationError("ExecutionAttempt and AgentBinding identity mismatch", details={"dimension": key})

        required = set(agent_binding.get("required_capability_ids") or [])
        capabilities = self._agent_manifest_capabilities(agent_manifest)
        for cid in required:
            cap = capabilities.get(cid)
            if not cap or cap.get("available") is not True or not cap.get("qualification_refs"):
                raise ValidationError("Required G2E agent capability is not qualified", details={"capability_id": cid})

        gwf_required = set(parse_json(row["required_capabilities"], []))
        if not required.issubset(gwf_required):
            raise ValidationError("GWF WorkAssignment drops required G2E agent capability")

        expected_equivalence = agent_binding.get("equivalence_policy_ref")
        actual_equivalence = parse_json(executor["equivalence_policy_ref"], {}) if executor["equivalence_policy_ref"] else None
        if expected_equivalence != actual_equivalence:
            raise ValidationError("ExecutorBinding equivalence policy does not preserve G2E policy")

        auth_ref = parse_json(executor["authority_envelope_ref"], {})
        auth_id = auth_ref.get("authority_envelope_id")
        if not auth_id:
            raise ValidationError("ExecutorBinding requires AuthorityEnvelope")
        effective = self.vnext.effective_authority(auth_id)
        semantic_ceiling = set(agent_binding.get("authority_scope") or [])
        if not set(effective["allow_actions"]).issubset(semantic_ceiling):
            raise AuthorityDenied("GWF effective authority exceeds G2E AgentBinding authority_scope")

        if qualification_grant_used_for_dispatch or agent_binding.get("qualification_authority_ref") and agent_binding.get("operational_use_of_qualification_grant"):
            raise AuthorityDenied("QualificationAuthorityGrant is qualification-only")
        return True

    @staticmethod
    def validate_material_substitution(
        original_binding: Mapping[str, Any],
        candidate_binding: Mapping[str, Any],
        *,
        material_dimensions: Sequence[str],
        same_attempt_id: bool,
    ) -> bool:
        changed = [
            dim for dim in material_dimensions
            if original_binding.get(dim) != candidate_binding.get(dim)
        ]
        if changed and same_attempt_id:
            raise InvalidTransition(
                "Material agent substitution requires a new G2E ExecutionAttempt",
                details={"changed_dimensions": changed},
            )
        return True

    # ------------------------------------------------------------------
    # Protected resources
    # ------------------------------------------------------------------
    @staticmethod
    def protected_resource_transition(old: str, new: str, *, uncertain_access_recovery: bool = False) -> str:
        if old not in FRESHNESS_STATES or new not in FRESHNESS_STATES:
            raise ValidationError("Unknown protected-resource freshness state")
        if uncertain_access_recovery:
            return "EXPOSED"
        if old == new:
            return new
        allowed = {("FRESH", "RESERVED"), ("RESERVED", "EXPOSED")}
        if (old, new) not in allowed:
            raise InvalidTransition("Protected-resource freshness transition is not admissible")
        return new

    @staticmethod
    def validate_protected_access(*, freshness_state: str, durable_reservation: bool, access_started: bool) -> bool:
        if freshness_state not in FRESHNESS_STATES:
            raise ValidationError("Unknown freshness state")
        if access_started and (freshness_state != "RESERVED" or not durable_reservation):
            raise AuthorityDenied("Protected access requires durable reservation before access begins")
        return True

    # ------------------------------------------------------------------
    # Evidence bridge
    # ------------------------------------------------------------------
    @staticmethod
    def validate_candidate_evidence(
        evidence: Mapping[str, Any],
        *,
        expected_attempt_ref: Mapping[str, Any],
        payload: Any,
        admission_policy: Mapping[str, Any],
    ) -> bool:
        if evidence.get("lifecycle") != "CANDIDATE":
            raise ValidationError("Runtime bridge may emit only CANDIDATE evidence")
        producer = evidence.get("producer_attempt_ref")
        if producer != expected_attempt_ref:
            raise ValidationError("Evidence producer attempt mismatch")
        source_class = evidence.get("source_class")
        if source_class not in set(admission_policy.get("accepted_source_classes") or []):
            raise ValidationError("Evidence source class is not admitted by frozen policy")
        digest = evidence.get("payload_digest")
        if digest != _payload_sha256(payload):
            raise ValidationError("Evidence payload digest mismatch")
        allowed_freshness = set(admission_policy.get("allowed_freshness_states") or [])
        state = evidence.get("freshness_state")
        if allowed_freshness and state not in allowed_freshness:
            raise ValidationError("Evidence freshness state violates admission policy")
        required_independence = set(admission_policy.get("independence_requirements") or [])
        actual_independence = set(evidence.get("independence_satisfied") or [])
        if not required_independence.issubset(actual_independence):
            raise ValidationError("Evidence independence requirements are not satisfied")
        if admission_policy.get("require_attempt_linkage") is True and producer is None:
            raise ValidationError("Evidence admission policy requires attempt linkage")
        return True

    @staticmethod
    def validate_adjudication_inputs(evidence_records: Sequence[Mapping[str, Any]]) -> bool:
        if not evidence_records:
            raise ValidationError("Adjudication requires admitted evidence")
        for item in evidence_records:
            if item.get("lifecycle") != "ADMITTED":
                raise ValidationError("Adjudication may consume only ADMITTED G2E evidence")
        return True

    @staticmethod
    def validate_adjudication_mirror(
        adjudication: Mapping[str, Any],
        *,
        semantic_authority: str,
        existing_verdict: str | None = None,
    ) -> bool:
        verdict = adjudication.get("verdict")
        if semantic_authority != "G2E":
            raise AuthorityDenied("Only G2E semantic authority may create an Adjudication verdict")
        if verdict not in TERMINAL_ADJUDICATION_VERDICTS:
            raise ValidationError("Invalid G2E Adjudication verdict")
        if existing_verdict is not None and existing_verdict != verdict:
            raise InvalidTransition("Terminal G2E Adjudication verdict is immutable")
        return True

    @staticmethod
    def operational_state_to_scientific_claim(state: str) -> None:
        raise AuthorityDenied(
            "GWF operational state cannot emit scientific evidence admission or verdict",
            details={"operational_state": state},
        )

    # ------------------------------------------------------------------
    # Independence / revision / recovery
    # ------------------------------------------------------------------
    @staticmethod
    def validate_independence(policy: Mapping[str, Any], observation: Mapping[str, Any]) -> bool:
        required = list(policy.get("required_dimensions") or [])
        for dim in required:
            value = observation.get(dim)
            if value is not True:
                raise ValidationError("Frozen independence dimension is not satisfied", details={"dimension": dim})
        return True

    @staticmethod
    def validate_normative_revision(
        *,
        change_class: str,
        outcome_exposed: bool,
        reuses_old_exact_identity: bool,
    ) -> bool:
        if change_class not in {"EDITORIAL", "NORMATIVE"}:
            raise ValidationError("Unknown change class")
        if change_class == "NORMATIVE" and reuses_old_exact_identity:
            if outcome_exposed:
                raise InvalidTransition("Normative post-outcome change requires successor lineage")
            raise InvalidTransition("Normative pre-outcome change requires a new exact revision and refreeze")
        return True

    @staticmethod
    def validate_checkpoint(
        expected_refs: Sequence[Mapping[str, Any]],
        observed_refs: Sequence[Mapping[str, Any]],
        *,
        uncertain_protected_access: bool = False,
    ) -> str:
        expected = sorted(canonical_json(item) for item in expected_refs)
        observed = sorted(canonical_json(item) for item in observed_refs)
        if expected != observed:
            raise ValidationError("Checkpoint G2E exact refs mismatch")
        return "EXPOSED" if uncertain_protected_access else "UNCHANGED"

    # ------------------------------------------------------------------
    # Source-classification firewall
    # ------------------------------------------------------------------
    @staticmethod
    def assert_source_import_allowed(category: str, *, mode: str = "runtime_import") -> bool:
        if category == IMPORTABLE_RUNTIME_CATEGORY and mode == "runtime_import":
            return True
        if category == SELECTIVE_PORT_CATEGORY and mode == "selective_port":
            return True
        raise AuthorityDenied(
            "G2E source category is not authorized for this import mode",
            details={"category": category, "mode": mode},
        )
