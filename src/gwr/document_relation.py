from __future__ import annotations

from typing import Any

from .errors import NotFound, StaleVersion, ValidationError
from .utils import parse_json, uid, utcnow


RELATION_TYPES = {
    "DEPENDS_ON",
    "REFERENCES",
    "MUST_ALIGN_WITH",
    "SUPERSEDES",
    "DERIVED_FROM",
    "VALIDATES",
    "IMPLEMENTS",
    "GENERATED_FROM",
}

TARGET_KINDS = {
    "DOCUMENT",
    "SOURCE_CODE",
    "SCHEMA",
    "API",
    "WORKFLOW",
    "DATASET",
    "STUDY_LOCK",
    "OTHER_ARTIFACT",
}

RELATION_STATUSES = {"ACTIVE", "RETIRED"}

BINDING_MODES = {"LOGICAL_CURRENT", "PINNED_REVISION"}

BINDING_LEGALITY = {
    "DEPENDS_ON": {"LOGICAL_CURRENT", "PINNED_REVISION"},
    "REFERENCES": {"LOGICAL_CURRENT", "PINNED_REVISION"},
    "MUST_ALIGN_WITH": {"LOGICAL_CURRENT"},
    "SUPERSEDES": {"PINNED_REVISION"},
    "DERIVED_FROM": {"PINNED_REVISION"},
    "VALIDATES": {"PINNED_REVISION"},
    "IMPLEMENTS": {"LOGICAL_CURRENT", "PINNED_REVISION"},
    "GENERATED_FROM": {"PINNED_REVISION"},
}

DEFAULT_INVALIDATION_POLICIES = {
    "DEPENDS_ON": "REVIEW_ON_TARGET_CHANGE",
    "REFERENCES": "REFERENTIAL_INTEGRITY_ONLY",
    "MUST_ALIGN_WITH": "BIDIRECTIONAL_REVIEW",
    "SUPERSEDES": "DECLARATION_ONLY",
    "DERIVED_FROM": "REVIEW_ON_TARGET_CHANGE",
    "VALIDATES": "REQUIRES_PINNED_BINDING",
    "IMPLEMENTS": "REVIEW_ON_NORMATIVE_CHANGE",
    "GENERATED_FROM": "REQUIRES_PINNED_BINDING",
}

DECLARE_ACTION = "DECLARE_DOCUMENT_RELATION"
RETIRE_ACTION = "RETIRE_DOCUMENT_RELATION"
BIND_ACTION = "BIND_DOCUMENT_RELATION"


class DocumentRelationService:
    """Canonical semantic document relations with DG-P9 target binding.

    Binding is stored on DocumentRelation itself. Resolution is identity-only:
    it does not create TraceLinks, ImpactSets, Evidence, findings, or mutate
    Revision validity/lifecycle/authority state.
    """

    def __init__(self, db, knowledge, governance, project_governance):
        self.db = db
        self.knowledge = knowledge
        self.gov = governance
        self.project_governance = project_governance

    @staticmethod
    def _enum(value: str, allowed: set[str], field: str) -> str:
        normalized = str(value or "").strip().upper()
        if normalized not in allowed:
            raise ValidationError(
                f"Invalid {field}",
                details={"value": value, "allowed": sorted(allowed)},
            )
        return normalized

    @staticmethod
    def _opaque_ref(value: str, field: str, *, max_length: int = 500) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValidationError(f"{field} is required")
        if len(normalized) > max_length:
            raise ValidationError(f"{field} is too long")
        if "\x00" in normalized:
            raise ValidationError(f"{field} contains NUL")
        return normalized

    def _source_document(
        self,
        document_id: str,
        *,
        project_id: str | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        artifact = self.knowledge.get_artifact(document_id)
        if artifact["artifact_type"] != "governed_document":
            raise ValidationError("Relation source must be a governed document")
        if project_id is not None and artifact["project_id"] != project_id:
            raise ValidationError("Relation source belongs to a different project")
        revision_id = artifact.get("current_revision_id")
        if not revision_id:
            raise ValidationError("Relation source has no current revision")
        revision = self.knowledge.get_revision(revision_id)
        return artifact, revision

    def _validate_target(
        self,
        *,
        project_id: str,
        source_document_id: str,
        target_kind: str,
        target_ref: str,
    ) -> str:
        target_ref = self._opaque_ref(target_ref, "target_ref")
        if target_kind == "DOCUMENT":
            if target_ref == source_document_id:
                raise ValidationError("Self-document relation is not allowed")
            target = self.knowledge.get_artifact(target_ref)
            if target["artifact_type"] != "governed_document":
                raise ValidationError("DOCUMENT target must be a governed document")
            if target["project_id"] != project_id:
                raise ValidationError("DOCUMENT target belongs to a different project")
        return target_ref

    def _validate_binding(
        self,
        *,
        project_id: str,
        relation_type: str,
        target_kind: str,
        target_ref: str,
        binding_mode: str,
        target_revision_or_hash: str | None,
    ) -> tuple[str, str | None]:
        mode = self._enum(binding_mode, BINDING_MODES, "target_binding_mode")
        if mode not in BINDING_LEGALITY[relation_type]:
            raise ValidationError(
                "Binding mode is not legal for relation type",
                details={
                    "relation_type": relation_type,
                    "binding_mode": mode,
                    "allowed": sorted(BINDING_LEGALITY[relation_type]),
                },
            )

        if target_kind != "DOCUMENT":
            raise ValidationError(
                "No qualified target resolver for external target kind",
                details={"target_kind": target_kind, "binding_mode": mode},
            )

        target = self.knowledge.get_artifact(target_ref)
        if target["artifact_type"] != "governed_document":
            raise ValidationError("DOCUMENT target must be a governed document")
        if target["project_id"] != project_id:
            raise ValidationError("DOCUMENT target belongs to a different project")

        if mode == "LOGICAL_CURRENT":
            if target_revision_or_hash not in {None, ""}:
                raise ValidationError(
                    "LOGICAL_CURRENT must not persist target_revision_or_hash"
                )
            return mode, None

        exact = self._opaque_ref(
            target_revision_or_hash,
            "target_revision_or_hash",
        )
        revision = self.knowledge.get_revision(exact)
        if revision["artifact_id"] != target_ref:
            raise ValidationError(
                "Pinned DOCUMENT revision does not belong to target_ref",
                details={
                    "target_ref": target_ref,
                    "revision_id": exact,
                    "revision_artifact_id": revision["artifact_id"],
                },
            )
        return mode, exact

    def _policy(self, relation_type: str, invalidation_policy: str | None) -> str:
        if invalidation_policy is None:
            return DEFAULT_INVALIDATION_POLICIES[relation_type]
        return self._opaque_ref(invalidation_policy, "invalidation_policy", max_length=200)

    def _relation(self, relation_id: str) -> dict[str, Any]:
        row = self.db.one(
            "SELECT * FROM document_relations WHERE relation_id=?",
            (relation_id,),
        )
        if not row:
            raise NotFound("Document relation not found")
        return dict(row)

    def get_relation(self, relation_id: str) -> dict[str, Any]:
        return self._relation(relation_id)

    def list_relations(
        self,
        *,
        project_id: str | None = None,
        source_document_id: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        if source_document_id is not None:
            sql = "SELECT * FROM document_relations WHERE source_document_id=?"
            params: list[Any] = [source_document_id]
        elif project_id is not None:
            sql = "SELECT * FROM document_relations WHERE project_id=?"
            params = [project_id]
        else:
            raise ValidationError("project_id or source_document_id is required")
        if status is not None:
            status = self._enum(status, RELATION_STATUSES, "relation status")
            sql += " AND status=?"
            params.append(status)
        sql += " ORDER BY created_at,relation_id"
        return [dict(row) for row in self.db.all(sql, tuple(params))]

    def _lock_project(self, project_id: str) -> None:
        if getattr(self.db, "backend_name", "") == "postgresql":
            row = self.db.conn.execute(
                "SELECT id FROM projects WHERE id=? FOR UPDATE",
                (project_id,),
            ).fetchone()
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
            "SELECT * FROM approvals WHERE proposal_id=? AND decision='APPROVED' "
            "ORDER BY created_at DESC LIMIT 1",
            (proposal_id,),
        )
        if not approval:
            raise ValidationError("Approved relation proposal lacks approval evidence")
        return proposal, approval

    def _authorize_commit(self, actor_id: str, project_id: str) -> None:
        self.project_governance.require_mutable(project_id)
        self.gov.authorize(
            actor_id,
            "CREATE_REVISION",
            {"project_id": project_id, "artifact_type": "governed_document"},
        )

    def prepare_relation(
        self,
        source_document_id: str,
        relation_type: str,
        target_kind: str,
        target_ref: str,
        actor_id: str,
        *,
        binding_mode: str | None = None,
        target_revision_or_hash: str | None = None,
        invalidation_policy: str | None = None,
        required_approval_policy: str = "normative_research_change",
        idempotency_key: str | None = None,
    ) -> str:
        source, revision = self._source_document(source_document_id)
        relation_type = self._enum(relation_type, RELATION_TYPES, "relation_type")
        target_kind = self._enum(target_kind, TARGET_KINDS, "target_kind")
        target_ref = self._validate_target(
            project_id=source["project_id"],
            source_document_id=source_document_id,
            target_kind=target_kind,
            target_ref=target_ref,
        )
        if binding_mode is None:
            raise ValidationError(
                "New document relation requires explicit target_binding_mode"
            )
        binding_mode, target_revision_or_hash = self._validate_binding(
            project_id=source["project_id"],
            relation_type=relation_type,
            target_kind=target_kind,
            target_ref=target_ref,
            binding_mode=binding_mode,
            target_revision_or_hash=target_revision_or_hash,
        )
        policy = self._policy(relation_type, invalidation_policy)
        if not self.gov.domain.approval_policy(required_approval_policy):
            raise ValidationError("Unknown relation approval policy")
        payload = {
            "schema": "DG-P9-DOCUMENT-RELATION-v1",
            "project_id": source["project_id"],
            "source_document_id": source_document_id,
            "created_revision_id": revision["revision_id"],
            "relation_type": relation_type,
            "target_kind": target_kind,
            "target_ref": target_ref,
            "target_binding_mode": binding_mode,
            "target_revision_or_hash": target_revision_or_hash,
            "invalidation_policy": policy,
        }
        return self.gov.prepare_proposal(
            source["project_id"],
            actor_id,
            DECLARE_ACTION,
            [
                {
                    "kind": "DOCUMENT_RELATION",
                    "source_document_id": source_document_id,
                    "relation_type": relation_type,
                    "target_kind": target_kind,
                    "target_ref": target_ref,
                    "target_binding_mode": binding_mode,
                    "target_revision_or_hash": target_revision_or_hash,
                }
            ],
            payload,
            required_approval_policy=required_approval_policy,
            idempotency_key=idempotency_key,
        )

    def apply_approved_declaration(
        self,
        proposal_id: str,
        actor_id: str,
    ) -> dict[str, Any]:
        proposal, approval = self._approved_proposal(proposal_id, DECLARE_ACTION)
        payload = self._proposal_payload(proposal)
        project_id = payload.get("project_id")
        self._authorize_commit(actor_id, project_id)

        relation_type = self._enum(
            payload.get("relation_type"),
            RELATION_TYPES,
            "relation_type",
        )
        target_kind = self._enum(
            payload.get("target_kind"),
            TARGET_KINDS,
            "target_kind",
        )
        target_ref = self._opaque_ref(payload.get("target_ref"), "target_ref")
        invalidation_policy = self._policy(
            relation_type,
            payload.get("invalidation_policy"),
        )
        source_document_id = self._opaque_ref(
            payload.get("source_document_id"),
            "source_document_id",
        )
        created_revision_id = self._opaque_ref(
            payload.get("created_revision_id"),
            "created_revision_id",
        )

        with self.db.tx():
            self._lock_project(project_id)
            _, current_revision = self._source_document(
                source_document_id,
                project_id=project_id,
            )
            if current_revision["revision_id"] != created_revision_id:
                raise ValidationError(
                    "Relation declaration source revision is no longer current"
                )
            target_ref = self._validate_target(
                project_id=project_id,
                source_document_id=source_document_id,
                target_kind=target_kind,
                target_ref=target_ref,
            )
            binding_mode, target_revision_or_hash = self._validate_binding(
                project_id=project_id,
                relation_type=relation_type,
                target_kind=target_kind,
                target_ref=target_ref,
                binding_mode=payload.get("target_binding_mode"),
                target_revision_or_hash=payload.get("target_revision_or_hash"),
            )
            duplicate = self.db.one(
                "SELECT relation_id FROM document_relations "
                "WHERE project_id=? AND source_document_id=? AND relation_type=? "
                "AND target_kind=? AND target_ref=? AND status='ACTIVE' LIMIT 1",
                (
                    project_id,
                    source_document_id,
                    relation_type,
                    target_kind,
                    target_ref,
                ),
            )
            if duplicate:
                raise ValidationError(
                    "Exact ACTIVE document relation already exists",
                    details={"relation_id": duplicate["relation_id"]},
                )

            relation_id = uid("drel")
            now = utcnow()
            self.db.conn.execute(
                "INSERT INTO document_relations("
                "relation_id,project_id,source_document_id,relation_type,"
                "target_kind,target_ref,invalidation_policy,status,"
                "created_revision_id,create_proposal_id,retired_revision_id,"
                "retired_by_proposal_id,version,created_at,updated_at,retired_at,"
                "target_binding_mode,target_revision_or_hash"
                ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    relation_id,
                    project_id,
                    source_document_id,
                    relation_type,
                    target_kind,
                    target_ref,
                    invalidation_policy,
                    "ACTIVE",
                    created_revision_id,
                    proposal_id,
                    None,
                    None,
                    0,
                    now,
                    now,
                    None,
                    binding_mode,
                    target_revision_or_hash,
                ),
            )
            self.gov.append_audit(
                project_id,
                actor_id,
                "DOCUMENT_RELATION_DECLARED",
                "DocumentRelation",
                relation_id,
                after_version="0",
                proposal_id=proposal_id,
                approval_id=approval["approval_id"],
                reason_code=relation_type,
                metadata={
                    "source_document_id": source_document_id,
                    "target_kind": target_kind,
                    "target_ref": target_ref,
                    "invalidation_policy": invalidation_policy,
                    "target_binding_mode": binding_mode,
                    "target_revision_or_hash": target_revision_or_hash,
                },
            )
            self.db.conn.execute(
                "UPDATE proposals SET status='COMMITTED' WHERE proposal_id=?",
                (proposal_id,),
            )
        return self.get_relation(relation_id)

    def prepare_binding(
        self,
        relation_id: str,
        actor_id: str,
        *,
        expected_version: int,
        binding_mode: str,
        target_revision_or_hash: str | None = None,
        required_approval_policy: str = "normative_research_change",
        idempotency_key: str | None = None,
    ) -> str:
        relation = self._relation(relation_id)
        if relation.get("target_binding_mode") is not None or relation.get(
            "target_revision_or_hash"
        ) is not None:
            raise ValidationError("Document relation is already bound; rebinding is forbidden")
        if relation["version"] != expected_version:
            raise StaleVersion(
                "Document relation version mismatch",
                details={"expected": expected_version, "actual": relation["version"]},
            )
        mode, exact = self._validate_binding(
            project_id=relation["project_id"],
            relation_type=relation["relation_type"],
            target_kind=relation["target_kind"],
            target_ref=relation["target_ref"],
            binding_mode=binding_mode,
            target_revision_or_hash=target_revision_or_hash,
        )
        if not self.gov.domain.approval_policy(required_approval_policy):
            raise ValidationError("Unknown relation approval policy")
        payload = {
            "schema": "DG-P9-DOCUMENT-RELATION-BIND-v1",
            "project_id": relation["project_id"],
            "relation_id": relation_id,
            "source_document_id": relation["source_document_id"],
            "relation_type": relation["relation_type"],
            "target_kind": relation["target_kind"],
            "target_ref": relation["target_ref"],
            "expected_version": expected_version,
            "target_binding_mode": mode,
            "target_revision_or_hash": exact,
        }
        return self.gov.prepare_proposal(
            relation["project_id"],
            actor_id,
            BIND_ACTION,
            [{"kind": "DOCUMENT_RELATION", "relation_id": relation_id}],
            payload,
            required_approval_policy=required_approval_policy,
            idempotency_key=idempotency_key,
        )

    def apply_approved_binding(
        self,
        proposal_id: str,
        actor_id: str,
    ) -> dict[str, Any]:
        proposal, approval = self._approved_proposal(proposal_id, BIND_ACTION)
        payload = self._proposal_payload(proposal)
        project_id = payload.get("project_id")
        self._authorize_commit(actor_id, project_id)

        relation_id = self._opaque_ref(payload.get("relation_id"), "relation_id")
        expected_version = int(payload.get("expected_version"))

        with self.db.tx():
            self._lock_project(project_id)
            relation = self._relation(relation_id)
            if relation["project_id"] != project_id:
                raise ValidationError("Relation binding project mismatch")
            if relation["version"] != expected_version:
                raise StaleVersion(
                    "Document relation version mismatch",
                    details={"expected": expected_version, "actual": relation["version"]},
                )
            if relation.get("target_binding_mode") is not None or relation.get(
                "target_revision_or_hash"
            ) is not None:
                raise ValidationError(
                    "Document relation is already bound; rebinding is forbidden"
                )
            frozen = {
                "source_document_id": payload.get("source_document_id"),
                "relation_type": payload.get("relation_type"),
                "target_kind": payload.get("target_kind"),
                "target_ref": payload.get("target_ref"),
            }
            for field, expected in frozen.items():
                if relation[field] != expected:
                    raise ValidationError(
                        "Frozen relation field changed before binding",
                        details={"field": field, "expected": expected, "actual": relation[field]},
                    )

            mode, exact = self._validate_binding(
                project_id=project_id,
                relation_type=relation["relation_type"],
                target_kind=relation["target_kind"],
                target_ref=relation["target_ref"],
                binding_mode=payload.get("target_binding_mode"),
                target_revision_or_hash=payload.get("target_revision_or_hash"),
            )
            new_version = expected_version + 1
            now = utcnow()
            cur = self.db.conn.execute(
                "UPDATE document_relations SET target_binding_mode=?,"
                "target_revision_or_hash=?,version=?,updated_at=? "
                "WHERE relation_id=? AND version=? "
                "AND target_binding_mode IS NULL AND target_revision_or_hash IS NULL",
                (
                    mode,
                    exact,
                    new_version,
                    now,
                    relation_id,
                    expected_version,
                ),
            )
            if cur.rowcount != 1:
                latest = self._relation(relation_id)
                if latest.get("target_binding_mode") is not None:
                    raise ValidationError(
                        "Document relation is already bound; rebinding is forbidden"
                    )
                raise StaleVersion("Document relation changed concurrently")

            self.gov.append_audit(
                project_id,
                actor_id,
                "DOCUMENT_RELATION_BOUND",
                "DocumentRelation",
                relation_id,
                before_version=str(expected_version),
                after_version=str(new_version),
                proposal_id=proposal_id,
                approval_id=approval["approval_id"],
                reason_code=mode,
                metadata={
                    "source_document_id": relation["source_document_id"],
                    "relation_type": relation["relation_type"],
                    "target_kind": relation["target_kind"],
                    "target_ref": relation["target_ref"],
                    "target_binding_mode": mode,
                    "target_revision_or_hash": exact,
                },
            )
            self.db.conn.execute(
                "UPDATE proposals SET status='COMMITTED' WHERE proposal_id=?",
                (proposal_id,),
            )
        return self.get_relation(relation_id)

    def resolve_target(self, relation_id: str) -> dict[str, Any]:
        relation = self._relation(relation_id)
        mode = relation.get("target_binding_mode")
        if mode is None:
            raise ValidationError("Document relation is UNBOUND and cannot be resolved")
        mode = self._enum(mode, BINDING_MODES, "target_binding_mode")
        if mode not in BINDING_LEGALITY[relation["relation_type"]]:
            raise ValidationError("Stored relation binding violates legality matrix")
        if relation["target_kind"] != "DOCUMENT":
            raise ValidationError(
                "No qualified target resolver for external target kind",
                details={"target_kind": relation["target_kind"], "binding_mode": mode},
            )

        target = self.knowledge.get_artifact(relation["target_ref"])
        if target["artifact_type"] != "governed_document":
            raise ValidationError("DOCUMENT target must be a governed document")
        if target["project_id"] != relation["project_id"]:
            raise ValidationError("DOCUMENT target belongs to a different project")
        current_revision_id = target.get("current_revision_id")
        if not current_revision_id:
            raise ValidationError("DOCUMENT target has no current revision")

        if mode == "LOGICAL_CURRENT":
            if relation.get("target_revision_or_hash") is not None:
                raise ValidationError(
                    "LOGICAL_CURRENT relation contains a persisted exact target"
                )
            resolved = self.knowledge.get_revision(current_revision_id)
            is_current = True
        else:
            exact = self._opaque_ref(
                relation.get("target_revision_or_hash"),
                "target_revision_or_hash",
            )
            resolved = self.knowledge.get_revision(exact)
            if resolved["artifact_id"] != relation["target_ref"]:
                raise ValidationError(
                    "Pinned DOCUMENT revision does not belong to target_ref"
                )
            is_current = exact == current_revision_id

        return {
            "relation_id": relation_id,
            "binding_mode": mode,
            "target_document_id": relation["target_ref"],
            "target_artifact_version": target["version"],
            "resolved_revision_id": resolved["revision_id"],
            "resolved_content_hash": resolved["content_hash"],
            "resolved_at": utcnow(),
            "is_current": is_current,
            "current_revision_id": current_revision_id,
        }

    def prepare_retirement(
        self,
        relation_id: str,
        actor_id: str,
        *,
        expected_version: int,
        required_approval_policy: str = "normative_research_change",
        idempotency_key: str | None = None,
    ) -> str:
        relation = self._relation(relation_id)
        if relation["status"] != "ACTIVE":
            raise ValidationError("Only ACTIVE document relation can be retired")
        if relation["version"] != expected_version:
            raise StaleVersion(
                "Document relation version mismatch",
                details={"expected": expected_version, "actual": relation["version"]},
            )
        _, revision = self._source_document(
            relation["source_document_id"],
            project_id=relation["project_id"],
        )
        if not self.gov.domain.approval_policy(required_approval_policy):
            raise ValidationError("Unknown relation approval policy")
        payload = {
            "schema": "DG-P8-DOCUMENT-RELATION-RETIRE-v1",
            "project_id": relation["project_id"],
            "relation_id": relation_id,
            "source_document_id": relation["source_document_id"],
            "retired_revision_id": revision["revision_id"],
            "expected_version": expected_version,
        }
        return self.gov.prepare_proposal(
            relation["project_id"],
            actor_id,
            RETIRE_ACTION,
            [{"kind": "DOCUMENT_RELATION", "relation_id": relation_id}],
            payload,
            required_approval_policy=required_approval_policy,
            idempotency_key=idempotency_key,
        )

    def apply_approved_retirement(
        self,
        proposal_id: str,
        actor_id: str,
    ) -> dict[str, Any]:
        proposal, approval = self._approved_proposal(proposal_id, RETIRE_ACTION)
        payload = self._proposal_payload(proposal)
        project_id = payload.get("project_id")
        self._authorize_commit(actor_id, project_id)

        relation_id = self._opaque_ref(payload.get("relation_id"), "relation_id")
        expected_version = int(payload.get("expected_version"))
        retired_revision_id = self._opaque_ref(
            payload.get("retired_revision_id"),
            "retired_revision_id",
        )

        with self.db.tx():
            self._lock_project(project_id)
            relation = self._relation(relation_id)
            if relation["project_id"] != project_id:
                raise ValidationError("Relation retirement project mismatch")
            if relation["version"] != expected_version:
                raise StaleVersion(
                    "Document relation version mismatch",
                    details={
                        "expected": expected_version,
                        "actual": relation["version"],
                    },
                )
            if relation["status"] != "ACTIVE":
                raise ValidationError("Only ACTIVE document relation can be retired")
            _, current_revision = self._source_document(
                relation["source_document_id"],
                project_id=project_id,
            )
            if current_revision["revision_id"] != retired_revision_id:
                raise ValidationError(
                    "Relation retirement source revision is no longer current"
                )

            new_version = expected_version + 1
            now = utcnow()
            cur = self.db.conn.execute(
                "UPDATE document_relations SET status='RETIRED',"
                "retired_revision_id=?,retired_by_proposal_id=?,version=?,"
                "updated_at=?,retired_at=? "
                "WHERE relation_id=? AND version=?",
                (
                    retired_revision_id,
                    proposal_id,
                    new_version,
                    now,
                    now,
                    relation_id,
                    expected_version,
                ),
            )
            if cur.rowcount != 1:
                raise StaleVersion("Document relation changed concurrently")
            self.gov.append_audit(
                project_id,
                actor_id,
                "DOCUMENT_RELATION_RETIRED",
                "DocumentRelation",
                relation_id,
                before_version=str(expected_version),
                after_version=str(new_version),
                proposal_id=proposal_id,
                approval_id=approval["approval_id"],
                reason_code="EXPLICIT_RETIREMENT",
                metadata={
                    "source_document_id": relation["source_document_id"],
                    "relation_type": relation["relation_type"],
                    "target_kind": relation["target_kind"],
                    "target_ref": relation["target_ref"],
                    "target_binding_mode": relation.get("target_binding_mode"),
                    "target_revision_or_hash": relation.get("target_revision_or_hash"),
                },
            )
            self.db.conn.execute(
                "UPDATE proposals SET status='COMMITTED' WHERE proposal_id=?",
                (proposal_id,),
            )
        return self.get_relation(relation_id)

    def apply_approved_proposal(
        self,
        proposal_id: str,
        actor_id: str,
    ) -> dict[str, Any]:
        row = self.db.one(
            "SELECT action FROM proposals WHERE proposal_id=?",
            (proposal_id,),
        )
        if not row:
            raise NotFound("Proposal not found")
        if row["action"] == DECLARE_ACTION:
            return self.apply_approved_declaration(proposal_id, actor_id)
        if row["action"] == BIND_ACTION:
            return self.apply_approved_binding(proposal_id, actor_id)
        if row["action"] == RETIRE_ACTION:
            return self.apply_approved_retirement(proposal_id, actor_id)
        raise ValidationError("Proposal action is not owned by document relation service")
