from __future__ import annotations

from typing import Any

from .errors import InvalidTransition, StaleVersion, ValidationError


DOCUMENT_ARTIFACT_TYPE = "governed_document"
DOCUMENT_LIFECYCLE_STATES = {
    "DRAFT",
    "IN_REVIEW",
    "ACTIVE",
    "DEPRECATED",
    "SUPERSEDED",
    "ARCHIVED",
}
P6_ALLOWED_LIFECYCLE_TRANSITIONS = {
    ("DRAFT", "IN_REVIEW"),
    ("IN_REVIEW", "DRAFT"),
    ("IN_REVIEW", "ACTIVE"),
    ("ACTIVE", "DEPRECATED"),
    ("DEPRECATED", "ACTIVE"),
}


class DocumentLifecycleValidityService:
    """DG-P6 lifecycle transitions and evidence-derived validity projection."""

    def __init__(self, db, knowledge, document_qa, governance, project_governance):
        self.db = db
        self.knowledge = knowledge
        self.document_qa = document_qa
        self.gov = governance
        self.project_governance = project_governance

    def _document(self, document_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        artifact = self.knowledge.get_artifact(document_id)
        if artifact["artifact_type"] != DOCUMENT_ARTIFACT_TYPE:
            raise ValidationError("Artifact is not a governed document")
        if artifact["lifecycle_status"] not in DOCUMENT_LIFECYCLE_STATES:
            raise ValidationError(
                "Governed document has invalid lifecycle state",
                details={"lifecycle_state": artifact["lifecycle_status"]},
            )
        revision_id = artifact.get("current_revision_id")
        if not revision_id:
            raise ValidationError("Governed document has no current revision")
        revision = self.knowledge.get_revision(revision_id)
        if revision["artifact_id"] != document_id:
            raise ValidationError("Current revision does not belong to governed document")
        return artifact, revision

    def transition_lifecycle(
        self,
        document_id: str,
        target_state: str,
        actor_id: str,
        *,
        expected_artifact_version: int,
    ) -> dict[str, Any]:
        artifact, revision = self._document(document_id)
        self.project_governance.require_mutable(artifact["project_id"])
        self.gov.authorize(
            actor_id,
            "CREATE_REVISION",
            {"project_id": artifact["project_id"], "artifact_type": DOCUMENT_ARTIFACT_TYPE},
        )

        target = str(target_state or "").strip().upper()
        if target not in DOCUMENT_LIFECYCLE_STATES:
            raise ValidationError("Invalid document lifecycle state", details={"target_state": target})
        current = artifact["lifecycle_status"]
        if artifact["version"] != expected_artifact_version:
            raise StaleVersion(
                "Artifact version mismatch",
                details={"expected": expected_artifact_version, "actual": artifact["version"]},
            )
        if (current, target) not in P6_ALLOWED_LIFECYCLE_TRANSITIONS:
            raise InvalidTransition(
                "Document lifecycle transition is not executable in DG-P6",
                details={"from": current, "to": target},
            )

        new_version = expected_artifact_version + 1
        cur = self.db.conn.execute(
            "UPDATE artifacts SET lifecycle_status=?,version=? WHERE artifact_id=? AND version=?",
            (target, new_version, document_id, expected_artifact_version),
        )
        if cur.rowcount != 1:
            raise StaleVersion("Document artifact changed concurrently")

        audit_event_id = self.gov.append_audit(
            artifact["project_id"],
            actor_id,
            "DOCUMENT_LIFECYCLE_TRANSITION",
            "Artifact",
            document_id,
            before_version=current,
            after_version=target,
            reason_code=f"{current}_TO_{target}",
            metadata={
                "artifact_version_before": expected_artifact_version,
                "artifact_version_after": new_version,
                "current_revision_id": revision["revision_id"],
            },
        )
        self.db.conn.commit()
        return {
            "document_id": document_id,
            "lifecycle_state": target,
            "artifact_version": new_version,
            "current_revision_id": revision["revision_id"],
            "audit_event_id": audit_event_id,
        }

    def _latest_exact_qa(self, document_id: str) -> dict[str, Any] | None:
        return self.document_qa.get_current_qa_status(document_id)

    def inspect_document_state(self, document_id: str) -> dict[str, Any]:
        artifact, revision = self._document(document_id)
        kernel = revision["validity_state"]
        qa = self._latest_exact_qa(document_id)
        active_findings = self.document_qa.list_active_findings_for_revision(revision["revision_id"])

        blockers: list[str] = []
        if revision["status"] != "CURRENT":
            blockers.append("CURRENT_REVISION_STATUS_INCONSISTENT")
        if kernel == "SUPERSEDED":
            blockers.append("CURRENT_REVISION_KERNEL_SUPERSEDED")
        if kernel == "FAILED":
            blockers.append("KERNEL_FAILED")
        if qa and qa.get("overall_status") == "FAIL":
            blockers.append("QA_FAIL")
        for finding in active_findings:
            blockers.append(f"FINDING_{finding['status']}:{finding['finding_id']}")

        if blockers:
            effective = "BLOCKED"
            reason = blockers[0]
        elif kernel in {"STALE", "DIRTY"}:
            effective = "STALE"
            reason = f"KERNEL_{kernel}"
        elif qa and qa.get("overall_status") == "PASS" and kernel in {"UNVERIFIED", "VALID"}:
            effective = "VALID"
            reason = "EXACT_QA_PASS_NO_BLOCKERS"
        else:
            effective = "UNVERIFIED"
            if qa and qa.get("overall_status") == "NOT_EVALUATED":
                reason = "QA_NOT_EVALUATED"
            elif qa is None:
                reason = "QA_MISSING"
            else:
                reason = "NOT_CURRENTLY_VERIFIED"

        return {
            "document_id": document_id,
            "revision_id": revision["revision_id"],
            "lifecycle_state": artifact["lifecycle_status"],
            "artifact_version": artifact["version"],
            "kernel_validity_state": kernel,
            "effective_validity_state": effective,
            "qa_record_id": qa.get("qa_record_id") if qa else None,
            "blocker_codes": blockers,
            "reconciliation_reason": reason,
        }

    def reconcile_document_validity(self, document_id: str) -> dict[str, Any]:
        artifact, _ = self._document(document_id)
        self.project_governance.require_mutable(artifact["project_id"])
        state = self.inspect_document_state(document_id)

        kernel = state["kernel_validity_state"]
        effective = state["effective_validity_state"]
        target = None

        if effective == "VALID" and kernel == "UNVERIFIED":
            target = "VALID"
        elif effective in {"UNVERIFIED", "BLOCKED"} and kernel == "VALID":
            target = "UNVERIFIED"

        transition = None
        if target is not None:
            transition = self.knowledge.set_validity_system_audited(
                state["revision_id"],
                target,
                reason_code=f"DOCUMENT_{effective}:{state['reconciliation_reason']}",
                actor_id="SYSTEM",
            )
            state = self.inspect_document_state(document_id)

        state["kernel_transition"] = transition
        return state
