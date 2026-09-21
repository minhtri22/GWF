from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

SUPPORTED_SCHEMA_MAJOR = 1
SHA256_RE = r"^[0-9a-f]{64}$"


def _normalize(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, dict):
        return {_normalize(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("NaN/Infinity are forbidden in canonical JSON")
        return value
    return value


def canonical_json(value: Any) -> str:
    """G2E v0.x canonical JSON profile."""
    normalized = _normalize(value)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def schema_major(version: str) -> int:
    try:
        major, minor = version.split(".", 1)
        if not major.isdigit() or not minor.isdigit():
            raise ValueError
        return int(major)
    except (AttributeError, ValueError):
        raise ValueError(f"invalid schema_version: {version!r}") from None


def assert_supported_schema_version(version: str) -> str:
    if schema_major(version) != SUPPORTED_SCHEMA_MAJOR:
        raise ValueError(
            f"unsupported schema major {schema_major(version)}; "
            f"supported={SUPPORTED_SCHEMA_MAJOR}"
        )
    return version


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Provenance(StrictModel):
    created_by: str = Field(min_length=1)
    created_at: str
    source_refs: tuple[str, ...] = ()
    derivation: str | None = None

    @field_validator("created_at")
    @classmethod
    def _utc_rfc3339_z(cls, value: str) -> str:
        if not value.endswith("Z"):
            raise ValueError("created_at must be RFC3339 UTC ending in Z")
        try:
            datetime.fromisoformat(value[:-1] + "+00:00")
        except ValueError:
            raise ValueError("invalid RFC3339 UTC timestamp") from None
        return value


class ExactRef(StrictModel):
    object_id: str = Field(min_length=1)
    revision_id: str = Field(min_length=1)
    content_hash: str = Field(pattern=SHA256_RE)


class CanonicalModel(StrictModel):
    """Base for authoritative G2E objects.

    `sealed()` computes the canonical content hash after normal Pydantic parsing.
    `parse_authoritative()` verifies a persisted object's hash and fails closed.
    """

    schema_version: str = "1.0"
    object_id: str = Field(min_length=1)
    revision_id: str = Field(min_length=1)
    provenance: Provenance
    content_hash: str = Field(pattern=SHA256_RE)

    schema_kind: ClassVar[str] = "canonical"

    @field_validator("schema_version")
    @classmethod
    def _supported_version(cls, value: str) -> str:
        return assert_supported_schema_version(value)

    @model_validator(mode="after")
    def _verify_authoritative_hash(self, info: ValidationInfo) -> "CanonicalModel":
        if info.context and info.context.get("verify_content_hash"):
            expected = self.computed_content_hash()
            if self.content_hash != expected:
                raise ValueError(
                    f"content_hash mismatch: expected={expected} got={self.content_hash}"
                )
        return self

    def canonical_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"content_hash"})

    def computed_content_hash(self) -> str:
        return canonical_hash(self.canonical_payload())

    @classmethod
    def sealed(cls, **data: Any):
        candidate = cls(content_hash="0" * 64, **data)
        return candidate.model_copy(
            update={"content_hash": candidate.computed_content_hash()}
        )

    @classmethod
    def parse_authoritative(cls, data: Any):
        return cls.model_validate(data, context={"verify_content_hash": True})

    def exact_ref(self) -> ExactRef:
        return ExactRef(
            object_id=self.object_id,
            revision_id=self.revision_id,
            content_hash=self.content_hash,
        )
