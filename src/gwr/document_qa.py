from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .errors import InvalidTransition, NotFound, StaleVersion, ValidationError
from .utils import canonical_json, content_hash, parse_json, uid, utcnow


QA_EVIDENCE_TYPE = "document_qa_record"
VALIDATOR_EVIDENCE_TYPE = "document_validator_execution"

QA_STATUSES = {"PASS", "FAIL", "NOT_EVALUATED"}
FINDING_STATUSES = {"OPEN", "RESOLVED_PENDING_VERIFY", "VERIFIED_RESOLVED", "WAIVED"}
SEVERITIES = {"INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"}
FINDING_CLASSES = {
    "STRUCTURAL_ERROR",
    "BROKEN_REFERENCE",
    "UNRESOLVED_DEPENDENCY",
    "DEPENDENCY_CYCLE",
    "STALE_DEPENDENCY",
    "UNDEFINED_TERM",
    "TERMINOLOGY_DRIFT",
    "SEMANTIC_CONTRADICTION",
    "DUPLICATE_AUTHORITY",
    "INVALID_SUPERSESSION",
    "CHANGE_CLASS_MISMATCH",
    "IMPLEMENTATION_DRIFT",
    "SCHEMA_API_DRIFT",
    "APPEND_ONLY_VIOLATION",
    "RESEARCH_LOCK_VIOLATION",
    "MISSING_PROVENANCE",
    "SECURITY_LEAK",
    "GENERATED_ARTIFACT_DRIFT",
}
NON_WAIVABLE_CLASSES = {"SECURITY_LEAK", "RESEARCH_LOCK_VIOLATION", "DUPLICATE_AUTHORITY"}

VALIDATOR_FINDING_CLASS = {
    "markdownlint-cli2": "STRUCTURAL_ERROR",
    "vale": "TERMINOLOGY_DRIFT",
    "lychee": "BROKEN_REFERENCE",
}

SEVERITY_MAP = {
    "SUGGESTION": "LOW",
    "WARNING": "MEDIUM",
    "ERROR": "HIGH",
}


class DocumentQAService:
    """Persistent exact-revision QA and finding lifecycle over existing GWF primitives."""

    def __init__(self, db, domain, knowledge, execution, governance, project_governance):
        self.db = db
        self.domain = domain
        self.knowledge = knowledge
        self.execution = execution
        self.gov = governance
        self.project_governance = project_governance

    def _require_execute(self, project_id: str, actor_id: str) -> None:
        self.project_governance.require_mutable(project_id)
        self.gov.authorize(actor_id, "EXECUTE", {"project_id": project_id})

    def _document_revision(self, document_id: str, revision_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        artifact = self.knowledge.get_artifact(document_id)
        if artifact["artifact_type"] != "governed_document":
            raise ValidationError("Artifact is not a governed document")
        revision = self.knowledge.get_revision(revision_id)
        if revision["artifact_id"] != document_id:
            raise ValidationError("Revision does not belong to governed document")
        return artifact, revision

    @staticmethod
    def _qa_policy(value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValidationError("qa_policy_ref must be an object")
        out = {
            "policy_id": str(value.get("policy_id") or "").strip(),
            "policy_version": str(value.get("policy_version") or "").strip(),
            "policy_hash": str(value.get("policy_hash") or "").strip(),
        }
        if not all(out.values()):
            raise ValidationError("qa_policy_ref requires policy_id, policy_version and policy_hash")
        return out

    @staticmethod
    def _execution_dict(value: Any) -> dict[str, Any]:
        if hasattr(value, "to_dict") and callable(value.to_dict):
            value = value.to_dict()
        if not isinstance(value, dict):
            raise ValidationError("validator execution must be an object")
        return dict(value)

    @staticmethod
    def _severity(value: Any) -> str:
        raw = str(value or "MEDIUM").strip().upper()
        raw = SEVERITY_MAP.get(raw, raw)
        if raw not in SEVERITIES:
            raise ValidationError("Unknown document finding severity", details={"severity": raw})
        return raw

    @staticmethod
    def _location(raw: dict[str, Any]) -> dict[str, Any]:
        location = raw.get("location")
        if location is not None:
            if not isinstance(location, dict):
                raise ValidationError("finding location must be an object")
            line = location.get("line")
            column = location.get("column")
        else:
            line = raw.get("line")
            column = raw.get("column")
        if line is not None and (not isinstance(line, int) or line < 1):
            raise ValidationError("finding line must be a positive integer")
        if column is not None and (not isinstance(column, int) or column < 1):
            raise ValidationError("finding column must be a positive integer")
        return {"line": line, "column": column}

    @staticmethod
    def _fingerprint(finding_class: str, rule_id: str, location: dict[str, Any], issue_key: str) -> str:
        return content_hash(
            {
                "finding_class": finding_class,
                "rule_id": rule_id,
                "location": location,
                "issue_key": issue_key,
            }
        )

    def _normalize_finding(
        self,
        validator_id: str,
        raw: dict[str, Any],
        validator_evidence_id: str,
    ) -> dict[str, Any]:
        finding_class = str(raw.get("finding_class") or VALIDATOR_FINDING_CLASS.get(validator_id) or "").strip().upper()
        if finding_class not in FINDING_CLASSES:
            raise ValidationError(
                "Unknown document finding class",
                details={"finding_class": finding_class, "validator_id": validator_id},
            )
        rule_id = str(raw.get("rule_id") or "").strip()
        if not rule_id:
            raise ValidationError("Document finding rule_id is required")
        description = str(raw.get("description") or raw.get("message") or "").strip()
        if not description:
            raise ValidationError("Document finding description is required")
        location = self._location(raw)
        issue_key = str(raw.get("issue_key") or rule_id).strip()
        required_fix = str(raw.get("required_fix") or "REVIEW_AND_FIX").strip()
        if not issue_key or not required_fix:
            raise ValidationError("Document finding issue_key and required_fix are required")
        return {
            "finding_class": finding_class,
            "severity": self._severity(raw.get("severity")),
            "rule_id": rule_id,
            "location": location,
            "description": description,
            "evidence_refs": [validator_evidence_id],
            "fingerprint": self._fingerprint(finding_class, rule_id, location, issue_key),
            "required_fix": required_fix,
        }

    def _normalize_execution(
        self,
        value: Any,
        document_id: str,
        revision_id: str,
        revision: dict[str, Any],
    ) -> dict[str, Any]:
        raw = self._execution_dict(value)
        validator_id = str(raw.get("validator_id") or "").strip()
        if not validator_id:
            raise ValidationError("validator_id is required")
        execution_status = str(raw.get("execution_status") or "").strip().upper()
        content_status = str(raw.get("content_status") or "").strip().upper()
        if execution_status not in {"SUCCEEDED", "UNAVAILABLE", "TOOL_ERROR"}:
            raise ValidationError("Invalid validator execution_status")
        if content_status not in {"PASS", "FINDINGS", "NOT_EVALUATED"}:
            raise ValidationError("Invalid validator content_status")
        if execution_status != "SUCCEEDED" and content_status != "NOT_EVALUATED":
            raise ValidationError("Failed validator execution must be NOT_EVALUATED")
        if execution_status == "SUCCEEDED" and content_status == "NOT_EVALUATED":
            raise ValidationError("Successful validator execution cannot be NOT_EVALUATED")

        payload = revision["structured_payload"]
        source_identity = payload.get("source_identity") or {}
        storage_locator = payload.get("storage_locator") or {}
        source_hash = str(source_identity.get("content_sha256") or "").strip()
        subject_hash = str(raw.get("subject_hash") or "").strip()
        if not source_hash:
            raise ValidationError("Governed document revision lacks source content SHA-256")
        if subject_hash != source_hash:
            raise ValidationError(
                "Validator execution subject hash does not match governed revision",
                details={"expected": source_hash, "observed": subject_hash},
            )

        findings = raw.get("findings") or []
        if not isinstance(findings, (list, tuple)):
            raise ValidationError("validator findings must be a list")
        if content_status == "PASS" and findings:
            raise ValidationError("PASS validator execution cannot contain findings")
        if content_status == "FINDINGS" and not findings:
            raise ValidationError("FINDINGS validator execution requires findings")
        if content_status == "NOT_EVALUATED":
            findings = []

        return {
            "schema": "DG-P5-VALIDATOR-EXECUTION-v1",
            "validator_id": validator_id,
            "validator_version": raw.get("validator_version"),
            "config_hash": raw.get("config_hash"),
            "execution_status": execution_status,
            "content_status": content_status,
            "error_code": raw.get("error_code"),
            "subject": {
                "document_id": document_id,
                "revision_id": revision_id,
                "source_content_sha256": source_hash,
                "path_locator": storage_locator.get("path"),
            },
            "normalized_findings": [dict(x) for x in findings],
            "started_at": raw.get("started_at") or utcnow(),
            "finished_at": raw.get("finished_at") or utcnow(),
        }

    def _insert_finding(
        self,
        finding_id: str,
        project_id: str,
        qa_record_id: str,
        revision_id: str,
        finding: dict[str, Any],
        actor_id: str,
        created_at: str,
    ) -> None:
        self.db.conn.execute(
            "INSERT INTO document_findings VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                finding_id,
                project_id,
                qa_record_id,
                revision_id,
                finding["finding_class"],
                finding["severity"],
                finding["rule_id"],
                canonical_json(finding["location"]),
                finding["description"],
                canonical_json(finding["evidence_refs"]),
                finding["fingerprint"],
                "OPEN",
                finding["required_fix"],
                None,
                None,
                0,
                created_at,
                created_at,
            ),
        )
        self.gov.append_audit(
            project_id,
            actor_id,
            "DOCUMENT_FINDING_CREATED",
            "DocumentFinding",
            finding_id,
            after_version="0",
            reason_code=finding["finding_class"],
        )

    def create_qa_record(
        self,
        project_id: str,
        document_id: str,
        revision_id: str,
        actor_id: str,
        *,
        qa_policy_ref: dict[str, Any],
        validator_executions: list[Any],
    ) -> dict[str, Any]:
        self._require_execute(project_id, actor_id)
        artifact, revision = self._document_revision(document_id, revision_id)
        if artifact["project_id"] != project_id:
            raise ValidationError("Document does not belong to project")
        policy = self._qa_policy(qa_policy_ref)
        if not isinstance(validator_executions, list) or not validator_executions:
            raise ValidationError("At least one validator execution is required")

        normalized = [
            self._normalize_execution(item, document_id, revision_id, revision)
            for item in validator_executions
        ]
        validator_ids = [uid("ev") for _ in normalized]
        qa_record_id = uid("ev")

        normalized_findings: list[dict[str, Any]] = []
        for evidence_id, execution in zip(validator_ids, normalized):
            if execution["execution_status"] == "SUCCEEDED" and execution["content_status"] == "FINDINGS":
                for raw_finding in execution["normalized_findings"]:
                    normalized_findings.append(
                        self._normalize_finding(execution["validator_id"], raw_finding, evidence_id)
                    )

        finding_ids = [uid("df") for _ in normalized_findings]
        if any(x["execution_status"] != "SUCCEEDED" or x["content_status"] == "NOT_EVALUATED" for x in normalized):
            overall = "NOT_EVALUATED"
        elif normalized_findings:
            overall = "FAIL"
        else:
            overall = "PASS"

        started_at = min(x["started_at"] for x in normalized)
        finished_at = max(x["finished_at"] for x in normalized)
        subject_refs = [{"kind": "DOCUMENT_REVISION", "document_id": document_id, "revision_id": revision_id}]
        qa_payload = {
            "schema": "DG-P5-QA-RECORD-v1",
            "subject": {
                "kind": "DOCUMENT_REVISION",
                "document_id": document_id,
                "exact_subject_id": revision_id,
            },
            "qa_policy_ref": policy,
            "validator_execution_refs": list(validator_ids),
            "finding_refs": list(finding_ids),
            "overall_status": overall,
            "started_at": started_at,
            "finished_at": finished_at,
            "verified_by": actor_id,
            "verified_at": finished_at,
        }

        now = utcnow()
        with self.db.tx():
            for evidence_id, execution in zip(validator_ids, normalized):
                self.execution.add_evidence(
                    project_id,
                    VALIDATOR_EVIDENCE_TYPE,
                    actor_id,
                    subject_refs,
                    execution,
                    trust_class="AUTHORITATIVE",
                    evidence_id=evidence_id,
                    commit=False,
                )
            for finding_id, finding in zip(finding_ids, normalized_findings):
                self._insert_finding(
                    finding_id,
                    project_id,
                    qa_record_id,
                    revision_id,
                    finding,
                    actor_id,
                    now,
                )
            self.execution.add_evidence(
                project_id,
                QA_EVIDENCE_TYPE,
                actor_id,
                subject_refs,
                qa_payload,
                trust_class="AUTHORITATIVE",
                evidence_id=qa_record_id,
                commit=False,
            )

        return {
            "qa_record_id": qa_record_id,
            "validator_execution_refs": validator_ids,
            "finding_refs": finding_ids,
            "overall_status": overall,
        }

    def _evidence(self, evidence_id: str, expected_type: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
        row = self.db.one("SELECT * FROM evidence WHERE evidence_id=?", (evidence_id,))
        if not row:
            raise NotFound("Evidence not found")
        if expected_type and row["evidence_type"] != expected_type:
            raise ValidationError("Evidence has unexpected type")
        return dict(row), parse_json(row["structured_payload"], {})

    def get_qa_record(self, qa_record_id: str) -> dict[str, Any]:
        row, payload = self._evidence(qa_record_id, QA_EVIDENCE_TYPE)
        return {
            "qa_record_id": qa_record_id,
            "project_id": row["project_id"],
            "subject_refs": parse_json(row["subject_refs"], []),
            "content_hash": row["content_hash"],
            "created_at": row["created_at"],
            **payload,
        }

    def list_qa_records_for_revision(self, revision_id: str) -> list[dict[str, Any]]:
        out = []
        for row in self.db.all(
            "SELECT * FROM evidence WHERE evidence_type=? ORDER BY created_at",
            (QA_EVIDENCE_TYPE,),
        ):
            refs = parse_json(row["subject_refs"], [])
            if any(ref.get("kind") == "DOCUMENT_REVISION" and ref.get("revision_id") == revision_id for ref in refs):
                out.append(self.get_qa_record(row["evidence_id"]))
        return out

    def get_current_qa_status(self, document_id: str) -> dict[str, Any] | None:
        artifact = self.knowledge.get_artifact(document_id)
        if artifact["artifact_type"] != "governed_document":
            raise ValidationError("Artifact is not a governed document")
        current = artifact["current_revision_id"]
        rows = self.db.all(
            "SELECT evidence_id FROM evidence WHERE project_id=? AND evidence_type=? ORDER BY created_at DESC",
            (artifact["project_id"], QA_EVIDENCE_TYPE),
        )
        for row in rows:
            qa = self.get_qa_record(row["evidence_id"])
            subject = qa.get("subject") or {}
            if subject.get("document_id") == document_id and subject.get("exact_subject_id") == current:
                return qa
        return None

    def _finding(self, finding_id: str) -> dict[str, Any]:
        row = self.db.one("SELECT * FROM document_findings WHERE finding_id=?", (finding_id,))
        if not row:
            raise NotFound("Document finding not found")
        out = dict(row)
        out["location"] = parse_json(out.pop("location_json"), {})
        out["evidence_refs"] = parse_json(out.pop("evidence_refs_json"), [])
        return out

    def get_finding(self, finding_id: str) -> dict[str, Any]:
        out = self._finding(finding_id)
        out["waiver_effective"] = self._waiver_effective(out) if out["status"] == "WAIVED" else None
        return out

    def list_findings_by_qa(self, qa_record_id: str) -> list[dict[str, Any]]:
        return [
            self.get_finding(row["finding_id"])
            for row in self.db.all(
                "SELECT finding_id FROM document_findings WHERE qa_record_id=? ORDER BY created_at,finding_id",
                (qa_record_id,),
            )
        ]

    def list_active_findings_for_revision(self, revision_id: str) -> list[dict[str, Any]]:
        out = []
        for row in self.db.all(
            "SELECT finding_id FROM document_findings WHERE subject_revision_id=? ORDER BY created_at,finding_id",
            (revision_id,),
        ):
            finding = self.get_finding(row["finding_id"])
            if finding["status"] in {"OPEN", "RESOLVED_PENDING_VERIFY"}:
                out.append(finding)
            elif finding["status"] == "WAIVED" and not finding["waiver_effective"]:
                out.append(finding)
        return out

    def _transition(
        self,
        finding: dict[str, Any],
        actor_id: str,
        expected_version: int,
        new_status: str,
        *,
        resolution_revision_ref: str | None = None,
        waiver_ref: str | None = None,
        reason_code: str,
        proposal_id: str | None = None,
        approval_id: str | None = None,
    ) -> dict[str, Any]:
        if finding["version"] != expected_version:
            raise StaleVersion(
                "Document finding version mismatch",
                details={"expected": expected_version, "actual": finding["version"]},
            )
        new_version = expected_version + 1
        now = utcnow()
        cur = self.db.conn.execute(
            "UPDATE document_findings SET status=?,resolution_revision_ref=?,waiver_ref=?,version=?,updated_at=? "
            "WHERE finding_id=? AND version=?",
            (
                new_status,
                resolution_revision_ref,
                waiver_ref,
                new_version,
                now,
                finding["finding_id"],
                expected_version,
            ),
        )
        if cur.rowcount != 1:
            raise StaleVersion("Document finding changed concurrently")
        self.gov.append_audit(
            finding["project_id"],
            actor_id,
            "DOCUMENT_FINDING_TRANSITION",
            "DocumentFinding",
            finding["finding_id"],
            before_version=str(expected_version),
            after_version=str(new_version),
            proposal_id=proposal_id,
            approval_id=approval_id,
            reason_code=reason_code,
        )
        self.db.conn.commit()
        return self.get_finding(finding["finding_id"])

    def mark_resolved_pending_verify(
        self,
        finding_id: str,
        resolution_revision_ref: str,
        actor_id: str,
        *,
        expected_version: int,
    ) -> dict[str, Any]:
        finding = self._finding(finding_id)
        self._require_execute(finding["project_id"], actor_id)
        if finding["status"] != "OPEN":
            raise InvalidTransition("Only OPEN finding may enter RESOLVED_PENDING_VERIFY")
        origin = self.knowledge.get_revision(finding["subject_revision_id"])
        resolution = self.knowledge.get_revision(resolution_revision_ref)
        if resolution["artifact_id"] != origin["artifact_id"]:
            raise ValidationError("Resolution revision belongs to a different document")
        return self._transition(
            finding,
            actor_id,
            expected_version,
            "RESOLVED_PENDING_VERIFY",
            resolution_revision_ref=resolution_revision_ref,
            reason_code="RESOLUTION_SUBMITTED",
        )

    def reopen_finding(
        self,
        finding_id: str,
        actor_id: str,
        *,
        expected_version: int,
        reason: str = "VERIFICATION_FAILED",
    ) -> dict[str, Any]:
        finding = self._finding(finding_id)
        self._require_execute(finding["project_id"], actor_id)
        if finding["status"] != "RESOLVED_PENDING_VERIFY":
            raise InvalidTransition("Only RESOLVED_PENDING_VERIFY finding may reopen")
        return self._transition(
            finding,
            actor_id,
            expected_version,
            "OPEN",
            reason_code=reason,
        )

    def verify_resolved(
        self,
        finding_id: str,
        verifying_qa_record_id: str,
        actor_id: str,
        *,
        expected_version: int,
    ) -> dict[str, Any]:
        finding = self._finding(finding_id)
        self._require_execute(finding["project_id"], actor_id)
        if finding["status"] != "RESOLVED_PENDING_VERIFY":
            raise InvalidTransition("Finding is not pending verification")
        if verifying_qa_record_id == finding["qa_record_id"]:
            raise ValidationError("Originating QA record cannot verify its own finding")

        verify_row, verify_payload = self._evidence(verifying_qa_record_id, QA_EVIDENCE_TYPE)
        origin_row, _ = self._evidence(finding["qa_record_id"], QA_EVIDENCE_TYPE)
        if verify_row["project_id"] != finding["project_id"]:
            raise ValidationError("Verifying QA belongs to a different project")
        subject = verify_payload.get("subject") or {}
        if subject.get("kind") != "DOCUMENT_REVISION":
            raise ValidationError("Verifying QA must target a document revision")
        if subject.get("exact_subject_id") != finding["resolution_revision_ref"]:
            raise ValidationError("Verifying QA does not target resolution revision")
        if verify_payload.get("overall_status") == "NOT_EVALUATED":
            raise ValidationError("NOT_EVALUATED QA cannot verify finding resolution")
        if verify_row["created_at"] <= origin_row["created_at"]:
            raise ValidationError("Verifying QA must be later than originating QA")

        repeated = self.db.one(
            "SELECT finding_id FROM document_findings WHERE qa_record_id=? AND fingerprint=? LIMIT 1",
            (verifying_qa_record_id, finding["fingerprint"]),
        )
        if repeated:
            raise ValidationError("Finding fingerprint was emitted by verifying QA")

        return self._transition(
            finding,
            actor_id,
            expected_version,
            "VERIFIED_RESOLVED",
            resolution_revision_ref=finding["resolution_revision_ref"],
            reason_code="RESOLUTION_VERIFIED",
        )

    def prepare_waiver(
        self,
        finding_id: str,
        actor_id: str,
        *,
        expected_version: int,
        reason: str,
        scope: dict[str, Any],
        expiration_or_review_condition: dict[str, Any],
        required_approval_policy: str,
        idempotency_key: str | None = None,
    ) -> str:
        finding = self._finding(finding_id)
        if finding["finding_class"] in NON_WAIVABLE_CLASSES:
            raise ValidationError("Document finding class is non-waivable")
        if finding["status"] not in {"OPEN", "RESOLVED_PENDING_VERIFY"}:
            raise InvalidTransition("Finding status cannot be waived")
        if finding["version"] != expected_version:
            raise StaleVersion("Document finding version mismatch")
        if not str(reason or "").strip():
            raise ValidationError("Waiver reason is required")
        if not isinstance(scope, dict) or not scope:
            raise ValidationError("Waiver scope is required")
        if not isinstance(expiration_or_review_condition, dict) or not expiration_or_review_condition:
            raise ValidationError("Waiver expiration/review condition is required")
        if not self.domain.approval_policy(required_approval_policy):
            raise ValidationError("Unknown waiver approval policy")
        payload = {
            "finding_id": finding_id,
            "expected_finding_version": expected_version,
            "reason": str(reason).strip(),
            "scope": scope,
            "expiration_or_review_condition": expiration_or_review_condition,
        }
        return self.gov.prepare_proposal(
            finding["project_id"],
            actor_id,
            "WAIVE_DOCUMENT_FINDING",
            [{"finding_id": finding_id}],
            payload,
            required_approval_policy=required_approval_policy,
            idempotency_key=idempotency_key,
        )

    def apply_approved_waiver(
        self,
        finding_id: str,
        proposal_id: str,
        actor_id: str,
        *,
        expected_version: int,
    ) -> dict[str, Any]:
        finding = self._finding(finding_id)
        self._require_execute(finding["project_id"], actor_id)
        if finding["finding_class"] in NON_WAIVABLE_CLASSES:
            raise ValidationError("Document finding class is non-waivable")
        if finding["status"] not in {"OPEN", "RESOLVED_PENDING_VERIFY"}:
            raise InvalidTransition("Finding status cannot be waived")
        proposal = self.gov.require_approved(proposal_id)
        if proposal["project_id"] != finding["project_id"] or proposal["action"] != "WAIVE_DOCUMENT_FINDING":
            raise ValidationError("Approved proposal does not authorize this finding waiver")
        payload = parse_json(proposal["frozen_payload"], {})
        if payload.get("finding_id") != finding_id or payload.get("expected_finding_version") != expected_version:
            raise ValidationError("Waiver proposal does not match finding/version")
        approval = self.db.one(
            "SELECT * FROM approvals WHERE proposal_id=? AND decision='APPROVED' ORDER BY created_at DESC LIMIT 1",
            (proposal_id,),
        )
        if not approval:
            raise ValidationError("Approved waiver proposal lacks approval evidence")
        return self._transition(
            finding,
            actor_id,
            expected_version,
            "WAIVED",
            resolution_revision_ref=finding.get("resolution_revision_ref"),
            waiver_ref=approval["approval_id"],
            reason_code="WAIVER_APPROVED",
            proposal_id=proposal_id,
            approval_id=approval["approval_id"],
        )

    @staticmethod
    def _parse_time(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _waiver_effective(self, finding: dict[str, Any]) -> bool:
        if finding.get("status") != "WAIVED" or not finding.get("waiver_ref"):
            return False
        approval = self.db.one("SELECT * FROM approvals WHERE approval_id=?", (finding["waiver_ref"],))
        if not approval or approval["decision"] != "APPROVED":
            return False
        proposal = self.db.one("SELECT * FROM proposals WHERE proposal_id=?", (approval["proposal_id"],))
        if not proposal or proposal["status"] not in {"APPROVED", "COMMITTED"}:
            return False
        payload = parse_json(proposal["frozen_payload"], {})
        condition = payload.get("expiration_or_review_condition") or {}
        if not isinstance(condition, dict) or not condition:
            return False
        now = datetime.now(timezone.utc)
        for key in ("expires_at", "review_due_at"):
            value = condition.get(key)
            if value and now >= self._parse_time(str(value)):
                return False
        return True

    def finding_transition_history(self, finding_id: str) -> list[dict[str, Any]]:
        self._finding(finding_id)
        return [
            dict(row)
            for row in self.db.all(
                "SELECT * FROM audit_events WHERE resource_type='DocumentFinding' AND resource_id=? ORDER BY timestamp",
                (finding_id,),
            )
        ]
