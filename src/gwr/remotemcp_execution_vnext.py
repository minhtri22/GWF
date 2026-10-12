from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping, Sequence

from .errors import AuthorityDenied, GateBlocked, InvalidTransition, ValidationError
from .utils import canonical_json, content_hash


P5_SCHEMA_VERSION = "GWF-VNEXT-P5-CHATGPT-WEB-REMOTEMCP-EXECUTION-ENVIRONMENT-v1"
ENVIRONMENT_TYPE = "CHATGPT_WEB_REMOTEMCP"
CANONICAL_PLUGIN = "remote-mcp-v2-web-clean"
LEGACY_PLUGIN = "remote-mcp-v2-web"
CANONICAL_TRANSPORT = "APP_BACKED"

PROTECTED_ORDER = {"FRESH": 0, "RESERVED": 1, "EXPOSED": 2}
RESULT_STATUSES = {
    "OPERATIONAL_SUCCEEDED",
    "OPERATIONAL_FAILED",
    "BLOCKED",
    "CANCELLED",
    "UNRESOLVED_PROVENANCE",
}
INFRA_ACTIONS = {
    "device_pair_begin",
    "device_revoke",
    "device_restart",
    "project_register_on_device",
    "project_bind_device",
    "root_widening",
    "replacement_device_identity",
    "replacement_project_identity",
}
CROSS_BOUNDARY_FORBIDDEN = {
    "CREATE_SCIENTIFIC_FAIL",
    "CREATE_SCIENTIFIC_PASS",
    "ADMIT_EVIDENCE",
    "REWRITE_TERMINAL_ADJUDICATION",
    "CREATE_REPLACEMENT_G2E_ATTEMPT",
    "PM_DIRECT_DISPATCH",
}
_SECRET_KEYS = {
    "lease_token",
    "pairing_secret",
    "pairing_token",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "password",
    "connector_secret",
}
_SECRET_MARKERS = (
    "pairing_secret=",
    "pairing_token=",
    "access_token=",
    "refresh_token=",
    "api_key=",
    "authorization: bearer ",
    "bearer ",
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

PLACEMENT_REQUIRED = {
    "placement_id",
    "revision",
    "work_assignment_id",
    "work_assignment_revision",
    "work_assignment_frozen_hash",
    "executor_binding_id",
    "executor_binding_resolved_payload_hash",
    "execution_environment_id",
    "worker_context_ref",
    "device_id",
    "device_key_fingerprint_sha256",
    "route_generation",
    "project_id",
    "project_binding_generation",
    "task_id",
    "repository_or_source_ref",
    "base_commit_or_source_digest",
    "branch_ref",
    "worktree_ref_or_explicit_non_git_qualification",
    "content_hash",
}
RESULT_REQUIRED = {
    "g2e_execution_attempt_exact_ref",
    "work_assignment_exact_ref",
    "executor_binding_exact_ref",
    "execution_environment_ref",
    "worker_context_ref",
    "placement_exact_ref",
    "device_id",
    "device_key_fingerprint_sha256",
    "route_generation",
    "project_id",
    "project_binding_generation",
    "task_id",
    "worktree_or_source_state_ref",
    "proxy_job_id",
    "node_job_id",
    "submitted_argv_sha256",
    "terminal_event_id",
    "terminal_state",
    "exit_code",
    "stdout_ref_and_digest",
    "stderr_ref_and_digest",
    "artifact_refs_and_digests",
    "checkpoint_ref_if_any",
    "environment_attestation_ref",
    "protected_resource_state",
    "operational_status",
    "independently_retrievable",
}


def _sha(value: Any, field: str) -> str:
    text = str(value or "")
    if not _SHA256.fullmatch(text):
        raise ValidationError(f"{field} must be a lowercase SHA-256 digest")
    return text


def _require_exact_ref(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    required = {"object_id", "revision_id", "content_hash"}
    if set(value) != required:
        raise ValidationError(f"{field} must contain exactly object_id/revision_id/content_hash")
    if not value.get("object_id") or not value.get("revision_id"):
        raise ValidationError(f"{field} identity incomplete")
    _sha(value.get("content_hash"), f"{field}.content_hash")
    return dict(value)


def _reject_secrets(value: Any, *, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            lower = str(key).lower()
            if lower in _SECRET_KEYS and item not in (None, "", [], {}):
                raise ValidationError(f"Secret/capability material forbidden at {path}.{key}")
            _reject_secrets(item, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_secrets(item, path=f"{path}[{index}]")
    elif isinstance(value, str):
        low = value.lower()
        if any(marker in low for marker in _SECRET_MARKERS):
            raise ValidationError(f"Secret/capability material forbidden at {path}")


def _subset(requested: Sequence[str], allowed: Sequence[str], field: str) -> set[str]:
    req = {str(x) for x in requested}
    allow = {str(x) for x in allowed}
    if not req.issubset(allow):
        raise AuthorityDenied(f"{field} exceeds governed authority")
    return req


def _same(actual: Any, expected: Any, field: str) -> None:
    if actual != expected:
        raise ValidationError(f"{field} mismatch")


def _protected_not_backward(previous: str, current: str) -> None:
    if previous not in PROTECTED_ORDER or current not in PROTECTED_ORDER:
        raise ValidationError("Unknown protected-resource state")
    if PROTECTED_ORDER[current] < PROTECTED_ORDER[previous]:
        raise InvalidTransition("Protected-resource state cannot move backward")


def argv_sha256(argv: Sequence[str]) -> str:
    _reject_secrets(list(argv), path="argv")
    return hashlib.sha256(canonical_json(list(argv)).encode("utf-8")).hexdigest()


class RemoteMCPExecutionEnvironmentVNext:
    """Pure P5 contract adapter core.

    This class validates and normalizes already-observed runtime facts. It does
    not call RemoteMCP, pair devices, restart nodes, submit jobs, or perform
    network/subprocess execution.
    """

    def validate_session_binding(self, binding: Mapping[str, Any]) -> dict[str, Any]:
        if not binding.get("available", False):
            raise GateBlocked("PLUGIN_SESSION_BINDING_FAILURE")
        if binding.get("plugin_identity") == LEGACY_PLUGIN:
            raise GateBlocked("Legacy Web route is forbidden for canonical P5")
        _same(binding.get("plugin_identity"), CANONICAL_PLUGIN, "plugin_identity")
        _same(binding.get("transport"), CANONICAL_TRANSPORT, "transport")
        return {
            "environment_type": ENVIRONMENT_TYPE,
            "plugin_identity": CANONICAL_PLUGIN,
            "transport": CANONICAL_TRANSPORT,
        }

    def validate_worker_context(
        self,
        context: Mapping[str, Any],
        *,
        executor_agent_projection_hash: str,
        material_identity_substitution: bool = False,
    ) -> dict[str, Any]:
        _reject_secrets(context, path="worker_context")
        if not context.get("worker_context_ref"):
            raise ValidationError("worker_context_ref is required")
        _sha(executor_agent_projection_hash, "executor_agent_projection_hash")
        _same(
            context.get("agent_identity_projection_hash"),
            executor_agent_projection_hash,
            "agent_identity_projection_hash",
        )
        if material_identity_substitution:
            raise InvalidTransition("Material worker identity substitution requires governed replacement")
        return dict(context)

    def validate_placement(
        self,
        placement: Mapping[str, Any],
        *,
        expected: Mapping[str, Any],
        approved_project_root: str,
        active_placement_count: int = 0,
        git_backed_mutable: bool = True,
    ) -> dict[str, Any]:
        missing = PLACEMENT_REQUIRED - set(placement)
        if missing:
            raise ValidationError(f"Placement missing fields: {sorted(missing)}")
        _reject_secrets(placement, path="placement")
        if active_placement_count > 0:
            raise InvalidTransition("At most one active placement revision per WorkAssignment dispatch")
        for field in (
            "work_assignment_id",
            "work_assignment_revision",
            "work_assignment_frozen_hash",
            "executor_binding_id",
            "executor_binding_resolved_payload_hash",
            "execution_environment_id",
            "worker_context_ref",
            "device_id",
            "device_key_fingerprint_sha256",
            "route_generation",
            "project_id",
            "project_binding_generation",
            "task_id",
            "repository_or_source_ref",
            "base_commit_or_source_digest",
            "branch_ref",
            "worktree_ref_or_explicit_non_git_qualification",
        ):
            if field in expected:
                _same(placement.get(field), expected[field], field)
        _sha(placement["work_assignment_frozen_hash"], "work_assignment_frozen_hash")
        _sha(placement["executor_binding_resolved_payload_hash"], "executor_binding_resolved_payload_hash")
        _sha(placement["device_key_fingerprint_sha256"], "device_key_fingerprint_sha256")
        if placement.get("project_root") != approved_project_root:
            raise GateBlocked("BLOCKED_ON_MANAGED_PROJECT_EXPOSURE_OR_EXPLICIT_DEDICATED_NODE_GATE")
        if placement.get("task_device_override") is not None:
            raise ValidationError("Task cannot override project-to-device placement")
        if placement.get("task_project_override") is not None:
            raise ValidationError("Task cannot override project identity")
        if git_backed_mutable:
            if not placement.get("base_commit_or_source_digest") or not placement.get(
                "worktree_ref_or_explicit_non_git_qualification"
            ):
                raise ValidationError("Git-backed execution requires exact base/worktree binding")
        canonical = dict(placement)
        supplied_hash = canonical.pop("content_hash")
        computed = content_hash(canonical)
        _same(supplied_hash, computed, "placement.content_hash")
        return dict(placement)

    def validate_route_generation(
        self,
        *,
        previous: int,
        current: int,
        authorized_restart_recovery: bool = False,
        same_device_and_fingerprint_verified: bool = False,
    ) -> None:
        if current == previous:
            return
        if not (authorized_restart_recovery and same_device_and_fingerprint_verified):
            raise InvalidTransition("Route-generation change requires authorized verified recovery")

    def validate_lease_observation(
        self,
        observation: Mapping[str, Any],
        *,
        expected_task_id: str,
        current_epoch: int,
    ) -> dict[str, Any]:
        _reject_secrets(observation, path="lease_observation")
        _same(observation.get("task_id"), expected_task_id, "lease.task_id")
        if int(observation.get("lease_epoch", -1)) < int(current_epoch):
            raise InvalidTransition("Stale lease epoch")
        return dict(observation)

    def validate_authority(
        self,
        *,
        requested_actions: Sequence[str],
        work_assignment_actions: Sequence[str],
        executor_binding_actions: Sequence[str],
        governance_profile_actions: Sequence[str],
        environment_capabilities: Sequence[str],
        placement_policy_actions: Sequence[str],
        human_action_actions: Sequence[str],
        technical_capabilities: Sequence[str] = (),
        connector_account_permissions: Sequence[str] = (),
        worker_prompt_claimed_actions: Sequence[str] = (),
    ) -> set[str]:
        effective = (
            set(work_assignment_actions)
            & set(executor_binding_actions)
            & set(governance_profile_actions)
            & set(environment_capabilities)
            & set(placement_policy_actions)
            & set(human_action_actions)
        )
        requested = set(requested_actions)
        if not requested.issubset(effective):
            raise AuthorityDenied("Requested actions exceed effective P5 authority intersection")
        if requested - effective and (
            set(technical_capabilities)
            or set(connector_account_permissions)
            or set(worker_prompt_claimed_actions)
        ):
            raise AuthorityDenied("Technical/account/prompt capability is not authority")
        return requested

    def assert_infrastructure_action(
        self,
        action: str,
        *,
        explicit_infrastructure_authorization: bool = False,
        dedicated_node_gate: bool = False,
        active_jobs: int = 0,
        explicit_active_job_restart_confirmation: bool = False,
    ) -> None:
        if action not in INFRA_ACTIONS:
            return
        if not explicit_infrastructure_authorization:
            raise AuthorityDenied("Ordinary worker authority cannot perform infrastructure action")
        if action in {"device_pair_begin", "device_revoke", "replacement_device_identity"} and not dedicated_node_gate:
            raise AuthorityDenied("Pair/replacement requires an explicit dedicated-node gate")
        if action == "device_restart" and active_jobs > 0 and not explicit_active_job_restart_confirmation:
            raise AuthorityDenied("Restart with active jobs requires explicit confirmation")

    def validate_job_submission(
        self,
        submission: Mapping[str, Any],
        *,
        placement: Mapping[str, Any],
        current_lease_epoch: int,
        ephemeral_lease_present: bool,
        active_mutating_jobs: int,
        scientific_observability_lost: bool = False,
    ) -> dict[str, Any]:
        _reject_secrets(submission, path="job_submission")
        if not ephemeral_lease_present:
            raise AuthorityDenied("Current task lease is required for routed job submission")
        _same(submission.get("task_id"), placement["task_id"], "job.task_id")
        _same(submission.get("project_id"), placement["project_id"], "job.project_id")
        _same(submission.get("device_id"), placement["device_id"], "job.device_id")
        _same(int(submission.get("lease_epoch", -1)), int(current_lease_epoch), "job.lease_epoch")
        _sha(submission.get("submitted_argv_sha256"), "submitted_argv_sha256")
        if submission.get("mutating", False) and active_mutating_jobs > 0:
            raise InvalidTransition("Second active mutating job in the same task/worktree is forbidden")
        if scientific_observability_lost and submission.get("semantic_duplicate", False):
            raise InvalidTransition("Observability loss cannot authorize scientific duplicate submission")
        if not submission.get("task_scoped_routed", False):
            raise ValidationError("Gateway-local compatibility command cannot prove routed execution")
        return dict(submission)

    def reconcile_job(
        self,
        observation: Mapping[str, Any],
        *,
        placement: Mapping[str, Any],
        expected_proxy_job_id: str,
        expected_argv_sha256: str,
    ) -> dict[str, Any]:
        _reject_secrets(observation, path="job_observation")
        _same(observation.get("proxy_job_id"), expected_proxy_job_id, "proxy_job_id")
        _same(observation.get("task_id"), placement["task_id"], "job.task_id")
        _same(observation.get("project_id"), placement["project_id"], "job.project_id")
        _same(observation.get("device_id"), placement["device_id"], "job.device_id")
        _same(observation.get("submitted_argv_sha256"), expected_argv_sha256, "submitted_argv_sha256")
        if not observation.get("node_job_id"):
            return {
                "state": "UNRESOLVED_PROVENANCE",
                "may_resubmit": False,
                "execution_proven": False,
            }
        if observation.get("terminal", False) and not observation.get("terminal_event_id"):
            raise ValidationError("Terminal job requires terminal_event_id")
        return {
            "state": observation.get("state"),
            "may_resubmit": False,
            "execution_proven": True,
            "node_job_id": observation["node_job_id"],
        }

    def assert_relaunch_allowed(
        self,
        *,
        observability_lost: bool,
        existing_job_may_exist: bool,
        explicit_scientific_relaunch_authorization: bool,
        reconciliation_terminal: bool,
    ) -> None:
        if observability_lost and existing_job_may_exist and not reconciliation_terminal:
            raise InvalidTransition("Existing job identity must be reconciled before replacement")
        if not explicit_scientific_relaunch_authorization:
            raise AuthorityDenied("Scientific relaunch requires explicit authorization")

    def validate_checkpoint(
        self,
        checkpoint: Mapping[str, Any],
        *,
        expected_refs: Mapping[str, Any],
        previous_protected_state: str,
    ) -> dict[str, Any]:
        _reject_secrets(checkpoint, path="checkpoint")
        for field in (
            "g2e_execution_attempt_exact_ref",
            "work_assignment_exact_ref",
            "executor_binding_exact_ref",
            "placement_exact_ref",
            "source_state_ref",
        ):
            if field not in checkpoint:
                raise ValidationError(f"Checkpoint missing {field}")
            _same(checkpoint[field], expected_refs[field], f"checkpoint.{field}")
        _sha(checkpoint.get("semantic_state_digest"), "checkpoint.semantic_state_digest")
        _protected_not_backward(previous_protected_state, checkpoint.get("protected_resource_state"))
        return dict(checkpoint)

    def validate_recovery(
        self,
        previous: Mapping[str, Any],
        current: Mapping[str, Any],
        *,
        governed_rebind: bool = False,
        authorized_restart_recovery: bool = False,
    ) -> None:
        material_fields = (
            "device_id",
            "device_key_fingerprint_sha256",
            "project_id",
            "project_binding_generation",
            "task_id",
            "repository_or_source_ref",
            "base_commit_or_source_digest",
            "branch_ref",
            "worktree_ref_or_explicit_non_git_qualification",
        )
        changed = [field for field in material_fields if previous.get(field) != current.get(field)]
        if changed and not governed_rebind:
            raise InvalidTransition(f"Material recovery identity changed without governed rebind: {changed}")
        self.validate_route_generation(
            previous=int(previous["route_generation"]),
            current=int(current["route_generation"]),
            authorized_restart_recovery=authorized_restart_recovery,
            same_device_and_fingerprint_verified=(
                previous.get("device_id") == current.get("device_id")
                and previous.get("device_key_fingerprint_sha256")
                == current.get("device_key_fingerprint_sha256")
            ),
        )
        _protected_not_backward(
            previous.get("protected_resource_state", "FRESH"),
            current.get("protected_resource_state", "FRESH"),
        )

    def validate_result_envelope(
        self,
        envelope: Mapping[str, Any],
        *,
        expected: Mapping[str, Any],
        observed_digests: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        missing = RESULT_REQUIRED - set(envelope)
        if missing:
            raise ValidationError(f"ExecutionResultEnvelope missing fields: {sorted(missing)}")
        _reject_secrets(envelope, path="result_envelope")
        if envelope["operational_status"] not in RESULT_STATUSES:
            raise ValidationError("Unknown operational result status")
        if not envelope.get("independently_retrievable", False):
            raise ValidationError("Terminal result must be independently retrievable")
        if not envelope.get("node_job_id"):
            raise ValidationError("Materialized terminal result requires node_job_id")
        for field in (
            "g2e_execution_attempt_exact_ref",
            "work_assignment_exact_ref",
            "executor_binding_exact_ref",
        ):
            _require_exact_ref(envelope[field], field)
        for field, value in expected.items():
            if field in envelope:
                _same(envelope[field], value, field)
        _sha(envelope["submitted_argv_sha256"], "submitted_argv_sha256")
        for field in ("stdout_ref_and_digest", "stderr_ref_and_digest"):
            item = envelope[field]
            if not isinstance(item, Mapping) or not item.get("ref"):
                raise ValidationError(f"{field} requires ref + digest")
            _sha(item.get("digest"), f"{field}.digest")
        for item in envelope["artifact_refs_and_digests"]:
            if not isinstance(item, Mapping) or not item.get("ref"):
                raise ValidationError("artifact ref is required")
            _sha(item.get("digest"), "artifact.digest")
        if observed_digests:
            for key, expected_digest in observed_digests.items():
                if key == "stdout":
                    _same(envelope["stdout_ref_and_digest"]["digest"], expected_digest, "stdout.digest")
                elif key == "stderr":
                    _same(envelope["stderr_ref_and_digest"]["digest"], expected_digest, "stderr.digest")
                else:
                    matches = [
                        item for item in envelope["artifact_refs_and_digests"] if item.get("ref") == key
                    ]
                    if not matches or matches[0].get("digest") != expected_digest:
                        raise ValidationError(f"Artifact digest mismatch for {key}")
        return dict(envelope)

    def candidate_evidence_projection(self, envelope: Mapping[str, Any]) -> dict[str, Any]:
        if envelope.get("operational_status") not in RESULT_STATUSES:
            raise ValidationError("Invalid operational envelope")
        return {
            "admission_state": "CANDIDATE",
            "scientific_verdict": None,
            "source": "P5_EXECUTION_RESULT_ENVELOPE",
            "runtime_status": envelope.get("operational_status"),
            "envelope_hash": content_hash(dict(envelope)),
        }

    def assert_cross_boundary_action(self, action: str) -> None:
        if action in CROSS_BOUNDARY_FORBIDDEN:
            raise AuthorityDenied(f"P5 adapter cannot perform cross-boundary action: {action}")

    def validate_qualification_scope(self, scope: Mapping[str, Any]) -> None:
        required_true = {"synthetic_only", "zero_science_only"}
        required_false = {
            "real_project_execution",
            "protected_evidence_consumption",
            "p6_route_import",
            "mission_control_refactor",
        }
        if any(not scope.get(key, False) for key in required_true):
            raise GateBlocked("P5 qualification must be synthetic/zero-science only")
        if any(scope.get(key, False) for key in required_false):
            raise GateBlocked("P5 qualification scope exceeds frozen contract")
