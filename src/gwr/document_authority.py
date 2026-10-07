from __future__ import annotations

import re
from typing import Any

from .errors import NotFound, StaleVersion, ValidationError
from .utils import canonical_json, parse_json, uid, utcnow


CLAIM_MODES = {"PRIMARY", "COMPOSED"}
CLAIM_STATUSES = {"ACTIVE", "RETIRED"}
EFFECTIVE_LIFECYCLES = {"ACTIVE", "DEPRECATED"}
NORMALIZED_TOKEN = re.compile(r"^[a-z0-9][a-z0-9._:/-]{0,199}$")

PRIMARY_ACTION = "DECLARE_DOCUMENT_AUTHORITY"
COMPOSED_ACTION = "DECLARE_COMPOSED_DOCUMENT_AUTHORITY"
RETIRE_ACTION = "RETIRE_DOCUMENT_AUTHORITY"


class DocumentAuthorityService:
    """DG-P7 logical-document authority claim registry and collision QA."""

    def __init__(self, db, knowledge, document_qa, governance, project_governance):
        self.db = db
        self.knowledge = knowledge
        self.document_qa = document_qa
        self.gov = governance
        self.project_governance = project_governance

    @staticmethod
    def _normalize_token(value: str, field: str) -> str:
        raw = str(value or "").strip()
        try:
            raw.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValidationError(f"{field} must be ASCII") from exc
        normalized = raw.lower()
        if not NORMALIZED_TOKEN.fullmatch(normalized):
            raise ValidationError(
                f"Invalid {field}",
                details={"value": raw, "allowed": "a-z 0-9 . _ : - /; length 1..200; alphanumeric first"},
            )
        if "//" in normalized:
            raise ValidationError(f"{field} contains an empty path component")
        return normalized

    def _document(self, document_id: str, *, project_id: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
        artifact = self.knowledge.get_artifact(document_id)
        if artifact["artifact_type"] != "governed_document":
            raise ValidationError("Authority owner must be a governed document")
        if project_id is not None and artifact["project_id"] != project_id:
            raise ValidationError("Authority owner belongs to a different project")
        revision_id = artifact.get("current_revision_id")
        if not revision_id:
            raise ValidationError("Authority owner has no current revision")
        revision = self.knowledge.get_revision(revision_id)
        return artifact, revision

    def _claim(self, claim_id: str) -> dict[str, Any]:
        row = self.db.one("SELECT * FROM document_authority_claims WHERE claim_id=?", (claim_id,))
        if not row:
            raise NotFound("Document authority claim not found")
        return dict(row)

    def get_claim(self, claim_id: str) -> dict[str, Any]:
        return self._claim(claim_id)

    def list_claims(self, *, project_id: str | None = None, document_id: str | None = None) -> list[dict[str, Any]]:
        if document_id is not None:
            return [
                dict(row)
                for row in self.db.all(
                    "SELECT * FROM document_authority_claims WHERE document_id=? ORDER BY created_at,claim_id",
                    (document_id,),
                )
            ]
        if project_id is not None:
            return [
                dict(row)
                for row in self.db.all(
                    "SELECT * FROM document_authority_claims WHERE project_id=? ORDER BY created_at,claim_id",
                    (project_id,),
                )
            ]
        raise ValidationError("project_id or document_id is required")

    def _effective_claims(self, project_id: str, authority_scope: str, authority_key: str) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self.db.all(
                "SELECT c.*,a.lifecycle_status,a.artifact_type "
                "FROM document_authority_claims c "
                "JOIN artifacts a ON a.artifact_id=c.document_id "
                "WHERE c.project_id=? AND c.authority_scope=? AND c.authority_key=? "
                "AND c.status='ACTIVE' AND a.artifact_type='governed_document' "
                "AND a.lifecycle_status IN ('ACTIVE','DEPRECATED') "
                "ORDER BY c.created_at,c.claim_id",
                (project_id, authority_scope, authority_key),
            )
        ]

    def effective_claims(self, project_id: str, authority_scope: str, authority_key: str) -> list[dict[str, Any]]:
        scope = self._normalize_token(authority_scope, "authority_scope")
        key = self._normalize_token(authority_key, "authority_key")
        return self._effective_claims(project_id, scope, key)

    def _lock_collision_domain(self, project_id: str) -> None:
        # SQLite's Database.tx() uses BEGIN IMMEDIATE. PostgreSQL needs an
        # explicit serialization point because the schema intentionally has no
        # UNIQUE(scope,key) constraint (COMPOSED ownership and observable invalid
        # imports both require duplicate rows to be representable).
        if getattr(self.db, "backend_name", "") == "postgresql":
            row = self.db.conn.execute("SELECT id FROM projects WHERE id=? FOR UPDATE", (project_id,)).fetchone()
            if not row:
                raise NotFound("Project not found")

    @staticmethod
    def _proposal_payload(row) -> dict[str, Any]:
        return parse_json(row["frozen_payload"], {})

    def _approved_proposal(self, proposal_id: str, expected_action: str):
        proposal = self.gov.require_approved(proposal_id)
        if proposal["action"] != expected_action:
            raise ValidationError(
                "Proposal action mismatch",
                details={"expected": expected_action, "actual": proposal["action"]},
            )
        approval = self.db.one(
            "SELECT * FROM approvals WHERE proposal_id=? AND decision='APPROVED' ORDER BY created_at DESC LIMIT 1",
            (proposal_id,),
        )
        if not approval:
            raise ValidationError("Approved authority proposal lacks approval evidence")
        return proposal, approval

    def _authorize_commit(self, actor_id: str, project_id: str) -> None:
        self.project_governance.require_mutable(project_id)
        self.gov.authorize(
            actor_id,
            "CREATE_REVISION",
            {"project_id": project_id, "artifact_type": "governed_document"},
        )

    def prepare_primary_claim(
        self,
        document_id: str,
        authority_scope: str,
        authority_key: str,
        actor_id: str,
        *,
        required_approval_policy: str = "normative_research_change",
        idempotency_key: str | None = None,
    ) -> str:
        artifact, revision = self._document(document_id)
        scope = self._normalize_token(authority_scope, "authority_scope")
        key = self._normalize_token(authority_key, "authority_key")
        if not self.gov.domain.approval_policy(required_approval_policy):
            raise ValidationError("Unknown authority approval policy")
        payload = {
            "schema": "DG-P7-AUTHORITY-GRANT-v1",
            "project_id": artifact["project_id"],
            "document_id": document_id,
            "granted_revision_id": revision["revision_id"],
            "authority_scope": scope,
            "authority_key": key,
            "mode": "PRIMARY",
        }
        return self.gov.prepare_proposal(
            artifact["project_id"],
            actor_id,
            PRIMARY_ACTION,
            [{"kind": "DOCUMENT_AUTHORITY", "document_id": document_id, "scope": scope, "key": key}],
            payload,
            required_approval_policy=required_approval_policy,
            idempotency_key=idempotency_key,
        )

    def prepare_composed_claims(
        self,
        project_id: str,
        authority_scope: str,
        authority_key: str,
        members: list[dict[str, str]],
        actor_id: str,
        *,
        composition_rule_id: str = "explicit-composition",
        composition_rule_version: str = "1",
        required_approval_policy: str = "normative_research_change",
        idempotency_key: str | None = None,
    ) -> str:
        self.project_governance.require_mutable(project_id)
        scope = self._normalize_token(authority_scope, "authority_scope")
        key = self._normalize_token(authority_key, "authority_key")
        if not isinstance(members, list) or len(members) < 2:
            raise ValidationError("COMPOSED authority requires at least two members")
        if not self.gov.domain.approval_policy(required_approval_policy):
            raise ValidationError("Unknown authority approval policy")

        frozen_members: list[dict[str, str]] = []
        seen_documents: set[str] = set()
        seen_roles: set[str] = set()
        for member in members:
            if not isinstance(member, dict):
                raise ValidationError("Composition member must be an object")
            document_id = str(member.get("document_id") or "").strip()
            role = self._normalize_token(member.get("role") or "", "composition_role")
            if document_id in seen_documents:
                raise ValidationError("Composition document appears more than once")
            if role in seen_roles:
                raise ValidationError("Composition roles must be unique")
            artifact, revision = self._document(document_id, project_id=project_id)
            seen_documents.add(document_id)
            seen_roles.add(role)
            frozen_members.append(
                {
                    "document_id": document_id,
                    "granted_revision_id": revision["revision_id"],
                    "role": role,
                }
            )
        frozen_members.sort(key=lambda x: x["document_id"])
        payload = {
            "schema": "DG-P7-AUTHORITY-GRANT-v1",
            "project_id": project_id,
            "authority_scope": scope,
            "authority_key": key,
            "mode": "COMPOSED",
            "composition_rule": {
                "id": self._normalize_token(composition_rule_id, "composition_rule_id"),
                "version": str(composition_rule_version or "").strip(),
            },
            "members": frozen_members,
        }
        if not payload["composition_rule"]["version"]:
            raise ValidationError("composition_rule_version is required")
        return self.gov.prepare_proposal(
            project_id,
            actor_id,
            COMPOSED_ACTION,
            [
                {
                    "kind": "DOCUMENT_AUTHORITY_COMPOSITION",
                    "scope": scope,
                    "key": key,
                    "document_ids": [m["document_id"] for m in frozen_members],
                }
            ],
            payload,
            required_approval_policy=required_approval_policy,
            idempotency_key=idempotency_key,
        )

    def _insert_claim(
        self,
        *,
        project_id: str,
        document_id: str,
        scope: str,
        key: str,
        mode: str,
        granted_revision_id: str,
        grant_proposal_id: str,
        composition_role: str | None = None,
        composition_policy_ref: str | None = None,
        composition_policy_hash: str | None = None,
    ) -> str:
        if mode not in CLAIM_MODES:
            raise ValidationError("Invalid authority claim mode")
        claim_id = uid("claim")
        now = utcnow()
        self.db.conn.execute(
            "INSERT INTO document_authority_claims VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                claim_id,
                project_id,
                document_id,
                scope,
                key,
                mode,
                composition_role,
                composition_policy_ref,
                composition_policy_hash,
                "ACTIVE",
                granted_revision_id,
                grant_proposal_id,
                None,
                0,
                now,
                now,
                None,
            ),
        )
        return claim_id

    def _composition_contract(self, claim: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
        ref = claim.get("composition_policy_ref")
        expected_hash = claim.get("composition_policy_hash")
        if not ref or not expected_hash:
            return None, "COMPOSITION_POLICY_MISSING"
        proposal = self.db.one("SELECT * FROM proposals WHERE proposal_id=?", (ref,))
        if not proposal:
            return None, "COMPOSITION_PROPOSAL_MISSING"
        if proposal["action"] != COMPOSED_ACTION:
            return None, "COMPOSITION_ACTION_MISMATCH"
        if proposal["status"] not in {"APPROVED", "COMMITTED"}:
            return None, "COMPOSITION_NOT_APPROVED"
        if proposal["payload_hash"] != expected_hash:
            return None, "COMPOSITION_HASH_MISMATCH"
        return self._proposal_payload(proposal), None

    def _collision_state(self, project_id: str, scope: str, key: str) -> dict[str, Any]:
        claims = self._effective_claims(project_id, scope, key)
        claim_ids = [c["claim_id"] for c in claims]
        document_ids = sorted({c["document_id"] for c in claims})
        if not claims:
            return {"collision": False, "reason": "NO_EFFECTIVE_OWNER", "claims": [], "claim_ids": [], "document_ids": []}

        primary = [c for c in claims if c["mode"] == "PRIMARY"]
        if len(claims) == 1 and len(primary) == 1:
            return {
                "collision": False,
                "reason": "SINGLE_PRIMARY",
                "claims": claims,
                "claim_ids": claim_ids,
                "document_ids": document_ids,
            }
        if primary:
            return {
                "collision": True,
                "reason": "PRIMARY_OR_MIXED_MULTIPLE_OWNERS",
                "claims": claims,
                "claim_ids": claim_ids,
                "document_ids": document_ids,
            }
        if any(c["mode"] != "COMPOSED" for c in claims):
            return {
                "collision": True,
                "reason": "UNKNOWN_AUTHORITY_MODE",
                "claims": claims,
                "claim_ids": claim_ids,
                "document_ids": document_ids,
            }

        refs = {c["composition_policy_ref"] for c in claims}
        hashes = {c["composition_policy_hash"] for c in claims}
        if len(refs) != 1 or len(hashes) != 1:
            return {
                "collision": True,
                "reason": "COMPOSITION_POLICY_DIVERGENCE",
                "claims": claims,
                "claim_ids": claim_ids,
                "document_ids": document_ids,
            }
        payload, error = self._composition_contract(claims[0])
        if error:
            return {
                "collision": True,
                "reason": error,
                "claims": claims,
                "claim_ids": claim_ids,
                "document_ids": document_ids,
            }
        if (
            payload.get("project_id") != project_id
            or payload.get("authority_scope") != scope
            or payload.get("authority_key") != key
            or payload.get("mode") != "COMPOSED"
        ):
            return {
                "collision": True,
                "reason": "COMPOSITION_SCOPE_MISMATCH",
                "claims": claims,
                "claim_ids": claim_ids,
                "document_ids": document_ids,
            }

        expected_members = payload.get("members") or []
        expected = {m.get("document_id"): m.get("role") for m in expected_members if isinstance(m, dict)}
        actual = {c["document_id"]: c["composition_role"] for c in claims}
        if len(actual) != len(claims):
            reason = "COMPOSITION_DUPLICATE_MEMBER"
        elif len(expected) != len(expected_members):
            reason = "COMPOSITION_PROPOSAL_MEMBER_INVALID"
        elif expected != actual:
            reason = "COMPOSITION_MEMBER_SET_OR_ROLE_MISMATCH"
        else:
            reason = None

        return {
            "collision": reason is not None,
            "reason": reason or "VALID_COMPOSITION",
            "claims": claims,
            "claim_ids": claim_ids,
            "document_ids": document_ids,
        }

    def inspect_collision(self, project_id: str, authority_scope: str, authority_key: str) -> dict[str, Any]:
        scope = self._normalize_token(authority_scope, "authority_scope")
        key = self._normalize_token(authority_key, "authority_key")
        result = self._collision_state(project_id, scope, key)
        return {
            **result,
            "project_id": project_id,
            "authority_scope": scope,
            "authority_key": key,
        }

    def apply_approved_grant(self, proposal_id: str, actor_id: str) -> dict[str, Any]:
        proposal = self.gov.require_approved(proposal_id)
        if proposal["action"] not in {PRIMARY_ACTION, COMPOSED_ACTION}:
            raise ValidationError("Proposal is not a DG-P7 authority grant")
        approval = self.db.one(
            "SELECT * FROM approvals WHERE proposal_id=? AND decision='APPROVED' ORDER BY created_at DESC LIMIT 1",
            (proposal_id,),
        )
        if not approval:
            raise ValidationError("Approved authority proposal lacks approval evidence")
        payload = self._proposal_payload(proposal)
        project_id = payload.get("project_id")
        self._authorize_commit(actor_id, project_id)

        scope = self._normalize_token(payload.get("authority_scope"), "authority_scope")
        key = self._normalize_token(payload.get("authority_key"), "authority_key")
        created: list[str] = []
        with self.db.tx():
            self._lock_collision_domain(project_id)
            if proposal["action"] == PRIMARY_ACTION:
                document_id = payload.get("document_id")
                artifact, revision = self._document(document_id, project_id=project_id)
                if payload.get("mode") != "PRIMARY":
                    raise ValidationError("PRIMARY proposal payload mode mismatch")
                if revision["revision_id"] != payload.get("granted_revision_id"):
                    raise ValidationError("Authority grant revision is no longer current")
                created.append(
                    self._insert_claim(
                        project_id=project_id,
                        document_id=document_id,
                        scope=scope,
                        key=key,
                        mode="PRIMARY",
                        granted_revision_id=revision["revision_id"],
                        grant_proposal_id=proposal_id,
                    )
                )
            else:
                if payload.get("mode") != "COMPOSED":
                    raise ValidationError("COMPOSED proposal payload mode mismatch")
                members = payload.get("members") or []
                if len(members) < 2:
                    raise ValidationError("COMPOSED proposal lacks members")
                for member in members:
                    document_id = member.get("document_id")
                    artifact, revision = self._document(document_id, project_id=project_id)
                    if revision["revision_id"] != member.get("granted_revision_id"):
                        raise ValidationError("Composition member revision is no longer current")
                    created.append(
                        self._insert_claim(
                            project_id=project_id,
                            document_id=document_id,
                            scope=scope,
                            key=key,
                            mode="COMPOSED",
                            granted_revision_id=revision["revision_id"],
                            grant_proposal_id=proposal_id,
                            composition_role=self._normalize_token(member.get("role"), "composition_role"),
                            composition_policy_ref=proposal_id,
                            composition_policy_hash=proposal["payload_hash"],
                        )
                    )

            collision = self._collision_state(project_id, scope, key)
            if collision["collision"]:
                raise ValidationError(
                    "Authority grant would introduce duplicate authority",
                    details={
                        "reason": collision["reason"],
                        "scope": scope,
                        "key": key,
                        "claim_ids": collision["claim_ids"],
                    },
                )
            for claim_id in created:
                self.gov.append_audit(
                    project_id,
                    actor_id,
                    "DOCUMENT_AUTHORITY_GRANTED",
                    "DocumentAuthorityClaim",
                    claim_id,
                    after_version="0",
                    proposal_id=proposal_id,
                    approval_id=approval["approval_id"],
                    reason_code=payload.get("mode") or proposal["action"],
                    metadata={"scope": scope, "key": key},
                )
            self.db.conn.execute("UPDATE proposals SET status='COMMITTED' WHERE proposal_id=?", (proposal_id,))
        return {
            "project_id": project_id,
            "claim_ids": created,
            "authority_scope": scope,
            "authority_key": key,
            "mode": payload.get("mode"),
            "collision": False,
        }

    def prepare_retirement(
        self,
        claim_id: str,
        actor_id: str,
        *,
        expected_version: int,
        required_approval_policy: str = "normative_research_change",
        idempotency_key: str | None = None,
    ) -> str:
        claim = self._claim(claim_id)
        if claim["status"] != "ACTIVE":
            raise ValidationError("Only ACTIVE authority claim can be retired")
        if claim["version"] != expected_version:
            raise StaleVersion(
                "Authority claim version mismatch",
                details={"expected": expected_version, "actual": claim["version"]},
            )
        if not self.gov.domain.approval_policy(required_approval_policy):
            raise ValidationError("Unknown authority approval policy")
        payload = {
            "schema": "DG-P7-AUTHORITY-RETIRE-v1",
            "project_id": claim["project_id"],
            "claim_id": claim_id,
            "document_id": claim["document_id"],
            "authority_scope": claim["authority_scope"],
            "authority_key": claim["authority_key"],
            "expected_version": expected_version,
        }
        return self.gov.prepare_proposal(
            claim["project_id"],
            actor_id,
            RETIRE_ACTION,
            [{"kind": "DOCUMENT_AUTHORITY_CLAIM", "claim_id": claim_id}],
            payload,
            required_approval_policy=required_approval_policy,
            idempotency_key=idempotency_key,
        )

    def apply_approved_retirement(self, proposal_id: str, actor_id: str) -> dict[str, Any]:
        proposal, approval = self._approved_proposal(proposal_id, RETIRE_ACTION)
        payload = self._proposal_payload(proposal)
        project_id = payload.get("project_id")
        self._authorize_commit(actor_id, project_id)
        claim_id = payload.get("claim_id")
        expected_version = int(payload.get("expected_version"))
        with self.db.tx():
            self._lock_collision_domain(project_id)
            claim = self._claim(claim_id)
            if claim["project_id"] != project_id:
                raise ValidationError("Retirement proposal project mismatch")
            if claim["version"] != expected_version:
                raise StaleVersion(
                    "Authority claim version mismatch",
                    details={"expected": expected_version, "actual": claim["version"]},
                )
            if claim["status"] != "ACTIVE":
                raise ValidationError("Only ACTIVE authority claim can be retired")
            new_version = expected_version + 1
            now = utcnow()
            cur = self.db.conn.execute(
                "UPDATE document_authority_claims "
                "SET status='RETIRED',retired_by_proposal_id=?,version=?,updated_at=?,retired_at=? "
                "WHERE claim_id=? AND version=?",
                (proposal_id, new_version, now, now, claim_id, expected_version),
            )
            if cur.rowcount != 1:
                raise StaleVersion("Authority claim changed concurrently")
            self.gov.append_audit(
                project_id,
                actor_id,
                "DOCUMENT_AUTHORITY_RETIRED",
                "DocumentAuthorityClaim",
                claim_id,
                before_version=str(expected_version),
                after_version=str(new_version),
                proposal_id=proposal_id,
                approval_id=approval["approval_id"],
                reason_code="EXPLICIT_RETIREMENT",
                metadata={"scope": claim["authority_scope"], "key": claim["authority_key"]},
            )
            self.db.conn.execute("UPDATE proposals SET status='COMMITTED' WHERE proposal_id=?", (proposal_id,))
        return self.get_claim(claim_id)

    def apply_approved_proposal(self, proposal_id: str, actor_id: str) -> dict[str, Any]:
        row = self.db.one("SELECT action FROM proposals WHERE proposal_id=?", (proposal_id,))
        if not row:
            raise NotFound("Proposal not found")
        if row["action"] in {PRIMARY_ACTION, COMPOSED_ACTION}:
            return self.apply_approved_grant(proposal_id, actor_id)
        if row["action"] == RETIRE_ACTION:
            return self.apply_approved_retirement(proposal_id, actor_id)
        raise ValidationError("Proposal action is not owned by DG-P7 authority service")

    def scan_authority_key(
        self,
        project_id: str,
        authority_scope: str,
        authority_key: str,
        actor_id: str,
    ) -> dict[str, Any]:
        scope = self._normalize_token(authority_scope, "authority_scope")
        key = self._normalize_token(authority_key, "authority_key")
        collision = self._collision_state(project_id, scope, key)
        if not collision["collision"]:
            return {
                "project_id": project_id,
                "authority_scope": scope,
                "authority_key": key,
                "collision": False,
                "reason": collision["reason"],
                "qa_records": [],
                "finding_refs": [],
            }

        details = {
            "reason": collision["reason"],
            "scope": scope,
            "key": key,
            "claim_ids": collision["claim_ids"],
            "document_ids": collision["document_ids"],
        }
        qa_records: list[str] = []
        finding_refs: list[str] = []
        for document_id in collision["document_ids"]:
            artifact, revision = self._document(document_id, project_id=project_id)
            source_hash = str((revision["structured_payload"].get("source_identity") or {}).get("content_sha256") or "")
            if not source_hash:
                raise ValidationError("Authority QA requires source content SHA-256")
            result = self.document_qa.create_qa_record(
                project_id,
                document_id,
                revision["revision_id"],
                actor_id,
                qa_policy_ref={
                    "policy_id": "dg-p7-authority-collision",
                    "policy_version": "1",
                    "policy_hash": "DG-P7-AUTHORITY-COLLISION-v1",
                },
                validator_executions=[
                    {
                        "validator_id": "gwr-authority-collision",
                        "validator_version": "1",
                        "config_hash": "DG-P7-AUTHORITY-COLLISION-v1",
                        "subject_hash": source_hash,
                        "execution_status": "SUCCEEDED",
                        "content_status": "FINDINGS",
                        "findings": [
                            {
                                "finding_class": "DUPLICATE_AUTHORITY",
                                "rule_id": "DG-P7-DUPLICATE-AUTHORITY",
                                "message": canonical_json(details),
                                "severity": "CRITICAL",
                                "issue_key": f"{scope}:{key}",
                                "required_fix": "RETIRE_OR_RECOMPOSE_AUTHORITY",
                            }
                        ],
                        "started_at": utcnow(),
                        "finished_at": utcnow(),
                    }
                ],
            )
            qa_records.append(result["qa_record_id"])
            finding_refs.extend(result["finding_refs"])
        return {
            "project_id": project_id,
            "authority_scope": scope,
            "authority_key": key,
            "collision": True,
            "reason": collision["reason"],
            "qa_records": qa_records,
            "finding_refs": finding_refs,
            "claim_ids": collision["claim_ids"],
            "document_ids": collision["document_ids"],
        }
