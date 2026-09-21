from __future__ import annotations

from typing import Any

from .errors import ValidationError


DOCUMENT_ARTIFACT_TYPE = "governed_document"
DOCUMENT_LOGICAL_KEY_PREFIX = "gwr:document:"
DOCUMENT_REVISION_SCHEMA = "DG-P4-DOCUMENT-REVISION-v1"


class DocumentFacadeService:
    """Identity/provenance facade over the existing Artifact/Revision kernel."""

    def __init__(self, knowledge, github):
        self.knowledge = knowledge
        self.github = github

    @staticmethod
    def _document_key(value: str) -> str:
        key = str(value or "").strip()
        if not key:
            raise ValidationError("document_key is required")
        if len(key) > 200:
            raise ValidationError("document_key is too long")
        if "/" in key or "\\" in key:
            raise ValidationError("document_key must be path-independent")
        if key in {".", ".."}:
            raise ValidationError("document_key is invalid")
        return key

    @staticmethod
    def _title(value: str) -> str:
        title = str(value or "").strip()
        if not title:
            raise ValidationError("document title is required")
        return title

    @staticmethod
    def _require_exact_expectations(
        expected_repository_id: str | int | None,
        expected_commit_sha: str | None,
        expected_blob_sha: str | None,
    ) -> None:
        if expected_repository_id is None or not expected_commit_sha or not expected_blob_sha:
            raise ValidationError(
                "Exact repository, commit and blob expectations are required for governed document identity"
            )

    def _resolve_source(
        self,
        project_id: str,
        binding_id: str,
        actor_id: str,
        *,
        ref_kind: str,
        ref_value: str,
        path: str,
        expected_repository_id: str | int | None,
        expected_commit_sha: str | None,
        expected_blob_sha: str | None,
    ) -> dict[str, Any]:
        self._require_exact_expectations(
            expected_repository_id,
            expected_commit_sha,
            expected_blob_sha,
        )
        return self.github.resolve_blob_revision(
            project_id,
            binding_id,
            actor_id,
            ref_kind=ref_kind,
            ref_value=ref_value,
            path=path,
            expected_repository_id=expected_repository_id,
            expected_commit_sha=expected_commit_sha,
            expected_blob_sha=expected_blob_sha,
        )

    @staticmethod
    def _payload(document_key: str, title: str, source: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema": DOCUMENT_REVISION_SCHEMA,
            "document_key": document_key,
            "title": title,
            "storage_locator": {
                "provider": source["provider"],
                "repository_id": source["repository_id"],
                "repository_full_name_at_resolution": source["repository_full_name_at_resolution"],
                "path": source["path_locator"],
            },
            "source_identity": {
                "commit_sha": source["resolved_commit_sha"],
                "blob_sha": source["blob_sha"],
                "content_sha256": source["content_sha256"],
                "content_size_bytes": source["content_size_bytes"],
            },
            "source_resolved_at": source["resolved_at"],
        }

    @staticmethod
    def _key_from_artifact(artifact: dict[str, Any]) -> str:
        logical_key = str(artifact.get("logical_key") or "")
        if not logical_key.startswith(DOCUMENT_LOGICAL_KEY_PREFIX):
            raise ValidationError("governed_document artifact has invalid logical key")
        key = logical_key[len(DOCUMENT_LOGICAL_KEY_PREFIX):]
        if not key:
            raise ValidationError("governed_document artifact has empty document key")
        return key

    def register_document(
        self,
        project_id: str,
        binding_id: str,
        actor_id: str,
        *,
        document_key: str,
        title: str,
        ref_kind: str,
        ref_value: str,
        path: str,
        expected_repository_id: str | int | None,
        expected_commit_sha: str | None,
        expected_blob_sha: str | None,
    ) -> dict[str, Any]:
        key = self._document_key(document_key)
        normalized_title = self._title(title)
        source = self._resolve_source(
            project_id,
            binding_id,
            actor_id,
            ref_kind=ref_kind,
            ref_value=ref_value,
            path=path,
            expected_repository_id=expected_repository_id,
            expected_commit_sha=expected_commit_sha,
            expected_blob_sha=expected_blob_sha,
        )
        document_id = self.knowledge.create_artifact(
            project_id,
            DOCUMENT_ARTIFACT_TYPE,
            DOCUMENT_LOGICAL_KEY_PREFIX + key,
            actor_id,
        )
        revision = self.knowledge.create_revision(
            document_id,
            self._payload(key, normalized_title, source),
            actor_id,
            expected_artifact_version=0,
        )
        return {
            "document_id": document_id,
            "revision_id": revision["revision_id"],
            "artifact_version": 1,
            "source_identity": {
                "repository_id": source["repository_id"],
                "commit_sha": source["resolved_commit_sha"],
                "blob_sha": source["blob_sha"],
                "content_sha256": source["content_sha256"],
            },
        }

    def revise_document(
        self,
        project_id: str,
        document_id: str,
        binding_id: str,
        actor_id: str,
        *,
        expected_artifact_version: int,
        ref_kind: str,
        ref_value: str,
        path: str,
        expected_repository_id: str | int | None,
        expected_commit_sha: str | None,
        expected_blob_sha: str | None,
        title: str | None = None,
    ) -> dict[str, Any]:
        artifact = self.knowledge.get_artifact(document_id)
        if artifact["project_id"] != project_id:
            raise ValidationError("Document does not belong to project")
        if artifact["artifact_type"] != DOCUMENT_ARTIFACT_TYPE:
            raise ValidationError("Artifact is not a governed document")
        key = self._key_from_artifact(artifact)
        current = self.knowledge.get_current_revision(document_id)
        current_title = str(current["structured_payload"].get("title") or "")
        normalized_title = self._title(title if title is not None else current_title)
        source = self._resolve_source(
            project_id,
            binding_id,
            actor_id,
            ref_kind=ref_kind,
            ref_value=ref_value,
            path=path,
            expected_repository_id=expected_repository_id,
            expected_commit_sha=expected_commit_sha,
            expected_blob_sha=expected_blob_sha,
        )
        revision = self.knowledge.create_revision(
            document_id,
            self._payload(key, normalized_title, source),
            actor_id,
            expected_artifact_version=expected_artifact_version,
        )
        updated = self.knowledge.get_artifact(document_id)
        return {
            "document_id": document_id,
            "revision_id": revision["revision_id"],
            "artifact_version": updated["version"],
            "source_identity": {
                "repository_id": source["repository_id"],
                "commit_sha": source["resolved_commit_sha"],
                "blob_sha": source["blob_sha"],
                "content_sha256": source["content_sha256"],
            },
        }

    def get_document(self, document_id: str) -> dict[str, Any]:
        artifact = self.knowledge.get_artifact(document_id)
        if artifact["artifact_type"] != DOCUMENT_ARTIFACT_TYPE:
            raise ValidationError("Artifact is not a governed document")
        revision = self.knowledge.get_current_revision(document_id)
        payload = revision["structured_payload"]
        return {
            "document_id": artifact["artifact_id"],
            "document_key": self._key_from_artifact(artifact),
            "artifact_version": artifact["version"],
            "current_revision_id": revision["revision_id"],
            "title": payload["title"],
            "storage_locator": dict(payload["storage_locator"]),
            "source_identity": dict(payload["source_identity"]),
        }
