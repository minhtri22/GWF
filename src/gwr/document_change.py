from __future__ import annotations

import hashlib
import re
from typing import Any

from .errors import InvalidTransition, StaleVersion, ValidationError


CHANGE_CLASSES = ("EDITORIAL", "CLARIFICATION", "NORMATIVE", "STRUCTURAL", "SUPERSESSION")
CHANGE_RANK = {name: i for i, name in enumerate(CHANGE_CLASSES)}
TRIGGER_FLOORS = {
    "SEMANTIC_RULE_CHANGE": "NORMATIVE",
    "REQUIREMENT_CHANGE": "NORMATIVE",
    "INVARIANT_CHANGE": "NORMATIVE",
    "THRESHOLD_CHANGE": "NORMATIVE",
    "PROTOCOL_CHANGE": "NORMATIVE",
    "ARCHITECTURE_CONTRACT_CHANGE": "NORMATIVE",
    "REQUIRED_BEHAVIOR_CHANGE": "NORMATIVE",
    "DOCUMENT_DECOMPOSITION_CHANGE": "STRUCTURAL",
    "DOCUMENT_IDENTITY_CHANGE": "STRUCTURAL",
    "RELATION_TOPOLOGY_CHANGE": "STRUCTURAL",
    "DEPENDENCY_TOPOLOGY_CHANGE": "STRUCTURAL",
    "AUTHORITY_OWNERSHIP_CHANGE": "STRUCTURAL",
    "AUTHORITY_REPLACEMENT": "SUPERSESSION",
}
DOCUMENT_ROLES = {"GOV", "PHASE"}
DOCUMENT_STATES = {"MUTABLE", "FROZEN"}
QA_STATUSES = {"EVALUATED", "NOT_EVALUATED"}
POLICY_VERSION = "DG-P10-AMEND1-v1"
_ACTIVE_VERSION_RE = re.compile(r"^(?P<stem>.+)\.v(?P<version>[1-9][0-9]*)\.md$")


def _safe_repo_path(value: str) -> str:
    path = str(value or "").strip().replace("\\", "/")
    if not path or path.startswith("/") or ".." in path.split("/"):
        raise ValidationError("Unsafe governed document path", details={"path": path})
    return path


def normalize_document_governance(metadata: dict[str, Any] | None, path: str) -> dict[str, Any] | None:
    if metadata is None:
        return None
    if not isinstance(metadata, dict):
        raise ValidationError("document_governance must be an object")
    safe_path = _safe_repo_path(path)
    parts = safe_path.split("/")
    if "archive" in parts:
        raise ValidationError("Archive copy cannot be enrolled as the active governed document")
    if len(parts) != 3 or parts[0] != "docs":
        raise ValidationError("Enrolled governed documents must live directly under docs/gov or docs/<phase-id>")

    role = str(metadata.get("document_role") or "").upper()
    state = str(metadata.get("governance_state") or "").upper()
    owner = str(metadata.get("owner_phase_id_or_workunit_type") or "").strip()
    if role not in DOCUMENT_ROLES:
        raise ValidationError("document_role must be GOV or PHASE")
    if state not in DOCUMENT_STATES:
        raise ValidationError("governance_state must be MUTABLE or FROZEN")
    if not owner:
        raise ValidationError("owner_phase_id_or_workunit_type is required")

    folder = parts[1]
    if role == "GOV" and folder != "gov":
        raise ValidationError("GOV document must live under docs/gov")
    if role == "PHASE" and folder in {"gov", "archive"}:
        raise ValidationError("PHASE document must live under docs/<phase-id>")

    match = _ACTIVE_VERSION_RE.fullmatch(parts[2])
    if not match:
        raise ValidationError("Active governed document filename must end with .vN.md")
    path_version = int(match.group("version"))
    try:
        version = int(metadata.get("document_version"))
    except (TypeError, ValueError):
        raise ValidationError("document_version must be a positive integer")
    if version < 1 or version != path_version:
        raise ValidationError(
            "document_version must match the active filename version",
            details={"metadata_version": version, "path_version": path_version},
        )

    previous_revision_id = metadata.get("previous_revision_id")
    previous_archive_path = metadata.get("previous_archive_path")
    if version == 1 and (previous_revision_id or previous_archive_path):
        raise ValidationError("Version 1 cannot claim previous revision/archive lineage")
    if version > 1 and bool(previous_revision_id) != bool(previous_archive_path):
        raise ValidationError("Previous revision ID and archive path must be present together")

    return {
        "document_role": role,
        "governance_state": state,
        "owner_phase_id_or_workunit_type": owner,
        "document_version": version,
        "phase_id": None if role == "GOV" else folder,
        "previous_revision_id": previous_revision_id,
        "previous_archive_path": previous_archive_path,
    }


class DocumentChangeClassificationService:
    """DG-P10 classification + document mutation authority + lineage planning.

    This service deliberately does not write repository content and does not create a
    new GWF Revision. DG-P11 owns the concrete multi-path DocumentChangeSet.
    """

    def __init__(self, db, knowledge, execution, governance, project_governance, agent_protocol):
        self.db = db
        self.knowledge = knowledge
        self.execution = execution
        self.gov = governance
        self.projects = project_governance
        self.agent_protocol = agent_protocol

    @staticmethod
    def _class(value: str, field: str) -> str:
        value = str(value or "").upper()
        if value not in CHANGE_RANK:
            raise ValidationError(f"{field} must be one of {', '.join(CHANGE_CLASSES)}")
        return value

    @staticmethod
    def _base_source(revision: dict[str, Any]) -> dict[str, Any]:
        payload = revision["structured_payload"]
        locator = payload.get("storage_locator") or {}
        source = payload.get("source_identity") or {}
        required = {
            "provider": locator.get("provider"),
            "repository_id": locator.get("repository_id"),
            "path": locator.get("path"),
            "commit_sha": source.get("commit_sha"),
            "blob_sha": source.get("blob_sha"),
            "content_sha256": source.get("content_sha256"),
        }
        if any(v in (None, "") for v in required.values()):
            raise ValidationError("Current governed document lacks exact P4 source identity")
        return required

    def _phase_context(self, project_id: str, phase_execution_id: str | None) -> dict[str, Any] | None:
        if not phase_execution_id:
            return None
        row = self.db.one(
            "SELECT pep.recovery_mode,pep.status protocol_status,pe.phase_id,pe.status phase_status,"
            "w.workunit_type,o.project_id "
            "FROM phase_execution_protocols pep "
            "JOIN phase_executions pe ON pe.phase_execution_id=pep.phase_execution_id "
            "JOIN orchestrations o ON o.orchestration_id=pe.orchestration_id "
            "LEFT JOIN workunits w ON w.workunit_id=pe.workunit_id "
            "WHERE pep.phase_execution_id=?",
            (phase_execution_id,),
        )
        if not row:
            raise ValidationError("PhaseExecution has no persisted Agent Execution Protocol")
        if row["project_id"] != project_id:
            raise ValidationError("PhaseExecution does not belong to document project")
        if row["phase_status"] != "RUNNING" or row["protocol_status"] in {"COMPLETED", "CANCELLED"}:
            raise InvalidTransition("Document AUTO authority requires an active PhaseExecution")
        mode = str(row["recovery_mode"] or "").upper()
        if mode not in {"AUTO", "HUMAN_APPROVE"}:
            raise ValidationError("Persisted PhaseExecution mode is invalid")
        return {
            "phase_execution_id": phase_execution_id,
            "phase_id": row["phase_id"],
            "workunit_type": row["workunit_type"],
            "workflow_mutation_mode": mode,
            "protocol_status": row["protocol_status"],
        }

    @staticmethod
    def _lineage(current_path: str, governance: dict[str, Any], proposed_path: str, proposed_content: str) -> dict[str, Any]:
        current_path = _safe_repo_path(current_path)
        proposed_path = _safe_repo_path(proposed_path)
        parts = current_path.split("/")
        match = _ACTIVE_VERSION_RE.fullmatch(parts[-1])
        if not match:
            raise ValidationError("Current active path is not versioned")
        current_version = int(match.group("version"))
        next_version = current_version + 1
        next_name = f"{match.group('stem')}.v{next_version}.md"
        expected_proposed = "/".join(parts[:-1] + [next_name])
        archive_path = "/".join(parts[:-1] + ["archive", parts[-1]])
        previous_link = f"archive/{parts[-1]}"
        if governance["document_version"] != current_version:
            raise ValidationError("Current governance version disagrees with active path")
        if proposed_path != expected_proposed:
            raise ValidationError(
                "Proposed active path must be the deterministic next version",
                details={"expected": expected_proposed, "actual": proposed_path},
            )
        if f"({previous_link})" not in proposed_content:
            raise ValidationError(
                "New active document must contain a human-readable link to the previous archived version",
                details={"required_link": previous_link},
            )
        return {
            "current_active_path": current_path,
            "current_document_version": current_version,
            "next_active_path": expected_proposed,
            "next_document_version": next_version,
            "expected_archive_path": archive_path,
            "previous_version_link": previous_link,
            "proposed_content_sha256": hashlib.sha256(proposed_content.encode("utf-8")).hexdigest(),
        }

    def _qa_refs(self, project_id: str, refs: list[str], status: str) -> list[str]:
        refs = list(refs or [])
        if status == "EVALUATED" and not refs:
            raise ValidationError("EVALUATED classification requires attributable QA evidence")
        for ref in refs:
            row = self.db.one("SELECT project_id,evidence_type FROM evidence WHERE evidence_id=?", (ref,))
            if not row or row["project_id"] != project_id:
                raise ValidationError("QA evidence reference is missing or outside project", details={"evidence_id": ref})
            if row["evidence_type"] not in {"document_qa_record", "document_validator_execution"}:
                raise ValidationError("QA evidence type is not admissible for DG-P10", details={"evidence_id": ref})
        return refs

    def classify(
        self,
        document_id: str,
        actor_id: str,
        *,
        expected_artifact_version: int,
        proposed_active_path: str,
        proposed_content: str,
        declared_change_class: str,
        declared_triggers: list[str] | None = None,
        qa_status: str,
        qa_review_refs: list[str] | None = None,
        qa_escalation_classes: list[str] | None = None,
        ambiguity_status: str = "CLEAR",
        phase_execution_id: str | None = None,
    ) -> dict[str, Any]:
        artifact = self.knowledge.get_artifact(document_id)
        if artifact["artifact_type"] != "governed_document":
            raise ValidationError("Artifact is not a governed document")
        project_id = artifact["project_id"]
        self.projects.require_mutable(project_id)
        self.gov.authorize(
            actor_id,
            "CREATE_REVISION",
            {"project_id": project_id, "artifact_type": "governed_document"},
        )
        if artifact["version"] != expected_artifact_version:
            raise StaleVersion(
                "Artifact version mismatch",
                details={"expected": expected_artifact_version, "actual": artifact["version"]},
            )
        revision = self.knowledge.get_current_revision(document_id)
        metadata = normalize_document_governance(
            revision["structured_payload"].get("document_governance"),
            revision["structured_payload"].get("storage_locator", {}).get("path"),
        )
        if metadata is None:
            raise ValidationError("Legacy/un-enrolled document requires explicit enrollment before DG-P10 AUTO policy")

        qa_status = str(qa_status or "").upper()
        if qa_status not in QA_STATUSES:
            raise ValidationError("qa_status must be EVALUATED or NOT_EVALUATED")
        qa_refs = self._qa_refs(project_id, qa_review_refs or [], qa_status)
        declared = self._class(declared_change_class, "declared_change_class")
        triggers = [str(x).upper() for x in (declared_triggers or [])]
        unknown = [x for x in triggers if x not in TRIGGER_FLOORS]
        if unknown:
            raise ValidationError("Unknown DG-P10 trigger", details={"triggers": unknown})
        escalations = [self._class(x, "qa_escalation_class") for x in (qa_escalation_classes or [])]

        candidates = [declared] + [TRIGGER_FLOORS[x] for x in triggers] + escalations
        ambiguity = str(ambiguity_status or "CLEAR").upper()
        if declared == "CLARIFICATION" and ambiguity != "CLEAR":
            candidates.append("NORMATIVE")
        effective = max(candidates, key=lambda x: CHANGE_RANK[x])

        base_source = self._base_source(revision)
        lineage = self._lineage(
            base_source["path"], metadata, proposed_active_path, proposed_content
        )
        phase = self._phase_context(project_id, phase_execution_id)
        owner = metadata["owner_phase_id_or_workunit_type"]
        owner_match = bool(
            phase
            and owner in {str(phase.get("phase_id") or ""), str(phase.get("workunit_type") or "")}
        )
        mode = phase["workflow_mutation_mode"] if phase else None

        role = metadata["document_role"]
        state = metadata["governance_state"]
        if qa_status != "EVALUATED":
            decision = "BLOCK_NOT_EVALUATED"
        elif role == "GOV" and state == "FROZEN":
            decision = "BLOCK_REQUIRES_EXPLICIT_USER_AUTHORIZATION"
        elif role == "PHASE" and state == "FROZEN":
            decision = "REQUIRE_HUMAN_APPROVAL_OR_LOCK_RELEASE"
        elif mode == "HUMAN_APPROVE":
            decision = "REQUIRE_HUMAN_APPROVAL"
        elif mode == "AUTO" and owner_match:
            decision = "ALLOW_AUTO"
        else:
            decision = "REQUIRE_HUMAN_APPROVAL"

        payload = {
            "schema": "DG-P10-CHANGE-CLASSIFICATION-v2",
            "classification_policy_version": POLICY_VERSION,
            "project_id": project_id,
            "document_id": document_id,
            "base_revision_id": revision["revision_id"],
            "expected_artifact_version": expected_artifact_version,
            "base_source_identity": base_source,
            "document_governance": metadata,
            "lineage_plan": lineage,
            "phase_context": phase,
            "declared_change_class": declared,
            "declared_triggers": triggers,
            "qa_review_refs": qa_refs,
            "qa_escalation_classes": escalations,
            "adjudication_status": qa_status,
            "ambiguity_status": ambiguity,
            "effective_change_class": effective,
            "governance_rank": CHANGE_RANK[effective],
            "workflow_mutation_mode": mode,
            "owner_scope_match": owner_match,
            "mutation_authority_decision": decision,
        }
        subject_refs = {
            "document_id": document_id,
            "base_revision_id": revision["revision_id"],
            "base_content_hash": revision["content_hash"],
            "proposed_active_path": lineage["next_active_path"],
            "proposed_content_sha256": lineage["proposed_content_sha256"],
            "next_document_version": lineage["next_document_version"],
            "expected_archive_path": lineage["expected_archive_path"],
            "phase_execution_id": phase_execution_id,
        }
        evidence_id = self.execution.add_evidence(
            project_id,
            "document_change_classification",
            actor_id,
            subject_refs,
            payload,
            trust_class="AUTHORITATIVE",
        )
        return {
            "classification_evidence_id": evidence_id,
            "effective_change_class": effective,
            "adjudication_status": qa_status,
            "workflow_mutation_mode": mode,
            "mutation_authority_decision": decision,
            "lineage_plan": lineage,
            "base_revision_id": revision["revision_id"],
            "artifact_version": artifact["version"],
            "owner_scope_match": owner_match,
        }
