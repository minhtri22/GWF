from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import quote

from .canonical import CanonicalModel, ExactRef, Provenance, canonical_hash, canonical_json
from .engine import evaluate_goal, transition_protected_resource
from .schema_registry import schema_model
from .schemas import (
    Adjudication,
    AttemptState,
    BackendQualificationStatus,
    ClaimResolution,
    EvidenceCapsule,
    EvidenceLifecycle,
    EvidenceRecord,
    ExecutionAttemptEnvelope,
    ExecutionResult,
    ExternalReferencePolicy,
    FreshnessState,
    GoalClosureContract,
    GoalContract,
    GoalVerdict,
    LibraryCapability,
    LibraryCapabilityManifest,
    LibraryExecutionStatus,
    LibraryPublicationContract,
    LibraryQueryContract,
    LibraryQueryExecution,
    LibrarySnapshot,
    PackageExternalReference,
    PackageManifest,
    PackageMember,
    PackageSeal,
    ProtectedResource,
    RuntimeCapability,
    RuntimeCapabilityManifest,
    RuntimeMode,
    SynthesisResult,
)


RUNTIME_ID = "g2e-standalone"
RUNTIME_VERSION = "0.1"


class StandaloneRuntimeError(RuntimeError):
    pass


class ObjectConflictError(StandaloneRuntimeError):
    pass


class UnsupportedCapabilityError(StandaloneRuntimeError):
    pass


class PackageVerificationError(StandaloneRuntimeError):
    pass


@dataclass(frozen=True)
class CandidateEvidenceSpec:
    source_class: str
    payload: Mapping[str, Any]
    object_id: str | None = None
    subject_refs: tuple[ExactRef, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    resource_refs: tuple[str, ...] = ()
    freshness_state: FreshnessState | None = None


@dataclass(frozen=True)
class LocalExecutionOutcome:
    action_summary: str
    evidence: tuple[CandidateEvidenceSpec, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    resource_identity: str | None = None


@dataclass(frozen=True)
class LocalExecutionReport:
    final_attempt: ExecutionAttemptEnvelope
    execution_result: ExecutionResult
    candidate_evidence: tuple[EvidenceRecord, ...]
    evidence_payloads: Mapping[str, Mapping[str, Any]]


@dataclass(frozen=True)
class RecoveryReport:
    exposed_resources: tuple[str, ...]
    preempted_attempts: tuple[str, ...]


@dataclass(frozen=True)
class PackageVerificationResult:
    manifest: PackageManifest
    seal: PackageSeal
    member_count: int


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _model_file_bytes(model: CanonicalModel) -> bytes:
    return canonical_json(model.model_dump(mode="json")).encode("utf-8")


def _json_file_bytes(value: Any) -> bytes:
    if isinstance(value, CanonicalModel):
        value = value.model_dump(mode="json")
    return canonical_json(value).encode("utf-8")


def _safe_component(value: str) -> str:
    return quote(value, safe="-_.")


def _attempt_immutable_fingerprint(attempt: ExecutionAttemptEnvelope) -> str:
    payload = attempt.model_dump(
        mode="json",
        exclude={"content_hash", "revision_id", "provenance", "state"},
    )
    return canonical_hash(payload)


class StandaloneStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "g2e.sqlite3"
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS objects (
                    schema_kind TEXT NOT NULL,
                    object_id TEXT NOT NULL,
                    revision_id TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY (object_id, revision_id)
                );
                CREATE INDEX IF NOT EXISTS idx_objects_hash
                    ON objects(content_hash);

                CREATE TABLE IF NOT EXISTS attempt_ledger (
                    attempt_id TEXT PRIMARY KEY,
                    current_object_id TEXT NOT NULL,
                    current_revision_id TEXT NOT NULL,
                    current_hash TEXT NOT NULL,
                    state TEXT NOT NULL,
                    proof_object_id TEXT NOT NULL,
                    proof_revision_id TEXT NOT NULL,
                    proof_hash TEXT NOT NULL,
                    immutable_fingerprint TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS execution_results (
                    attempt_id TEXT PRIMARY KEY,
                    result_object_id TEXT NOT NULL,
                    result_revision_id TEXT NOT NULL,
                    result_hash TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS adjudications (
                    attempt_id TEXT PRIMARY KEY,
                    adjudication_object_id TEXT NOT NULL,
                    adjudication_revision_id TEXT NOT NULL,
                    adjudication_hash TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS protected_current (
                    resource_id TEXT PRIMARY KEY,
                    current_revision_id TEXT NOT NULL,
                    current_hash TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    identity_ref TEXT NOT NULL,
                    freshness_state TEXT NOT NULL,
                    reuse_allowed INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS resource_reservations (
                    resource_id TEXT PRIMARY KEY,
                    attempt_id TEXT NOT NULL,
                    status TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS evidence_payloads (
                    object_id TEXT NOT NULL,
                    revision_id TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY (object_id, revision_id)
                );

                CREATE TABLE IF NOT EXISTS library_publications (
                    publication_id TEXT PRIMARY KEY,
                    subject_object_id TEXT NOT NULL,
                    subject_revision_id TEXT NOT NULL,
                    subject_hash TEXT NOT NULL,
                    subject_kind TEXT NOT NULL,
                    source_claim_resolution TEXT,
                    source_package_seal_hash TEXT,
                    publication_scope TEXT NOT NULL,
                    metadata_namespace TEXT NOT NULL,
                    metadata_schema_version TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    active INTEGER NOT NULL,
                    withdraw_reason TEXT
                );

                CREATE TABLE IF NOT EXISTS library_snapshots (
                    snapshot_ref TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS runtime_events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    subject_id TEXT,
                    payload_json TEXT NOT NULL
                );
                """
            )

    def _event_conn(
        self,
        conn: sqlite3.Connection,
        event_type: str,
        subject_id: str | None,
        payload: Mapping[str, Any],
    ) -> None:
        conn.execute(
            "INSERT INTO runtime_events(event_type, subject_id, payload_json) VALUES (?,?,?)",
            (event_type, subject_id, canonical_json(dict(payload))),
        )

    def _put_object_conn(self, conn: sqlite3.Connection, obj: CanonicalModel) -> None:
        kind = obj.schema_kind
        model = schema_model(kind)
        payload_json = canonical_json(obj.model_dump(mode="json"))
        model.parse_authoritative(json.loads(payload_json))
        row = conn.execute(
            "SELECT content_hash, payload_json FROM objects WHERE object_id=? AND revision_id=?",
            (obj.object_id, obj.revision_id),
        ).fetchone()
        if row is not None:
            if row["content_hash"] == obj.content_hash and row["payload_json"] == payload_json:
                return
            raise ObjectConflictError(
                f"conflicting canonical revision: {obj.object_id}@{obj.revision_id}"
            )
        conn.execute(
            """
            INSERT INTO objects(schema_kind, object_id, revision_id, content_hash, payload_json)
            VALUES (?,?,?,?,?)
            """,
            (kind, obj.object_id, obj.revision_id, obj.content_hash, payload_json),
        )

    def put(self, obj: CanonicalModel) -> None:
        self.put_many((obj,))

    def put_many(self, objects: Sequence[CanonicalModel]) -> None:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            for obj in objects:
                self._put_object_conn(conn, obj)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def object_count(self) -> int:
        with self._connect() as conn:
            return int(conn.execute("SELECT COUNT(*) AS n FROM objects").fetchone()["n"])

    def _load_ref_conn(
        self,
        conn: sqlite3.Connection,
        ref: ExactRef,
        expected_kind: str | None = None,
    ) -> CanonicalModel:
        row = conn.execute(
            """
            SELECT schema_kind, payload_json, content_hash
            FROM objects
            WHERE object_id=? AND revision_id=?
            """,
            (ref.object_id, ref.revision_id),
        ).fetchone()
        if row is None:
            raise KeyError(f"canonical object not found: {ref.object_id}@{ref.revision_id}")
        if row["content_hash"] != ref.content_hash:
            raise ObjectConflictError("exact reference hash mismatch")
        if expected_kind is not None and row["schema_kind"] != expected_kind:
            raise ObjectConflictError(
                f"schema kind mismatch: expected={expected_kind} actual={row['schema_kind']}"
            )
        return schema_model(row["schema_kind"]).parse_authoritative(
            json.loads(row["payload_json"])
        )

    def load_ref(self, ref: ExactRef, expected_kind: str | None = None) -> CanonicalModel:
        with self._connect() as conn:
            return self._load_ref_conn(conn, ref, expected_kind)

    def load(self, schema_kind: str, object_id: str, revision_id: str) -> CanonicalModel:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT content_hash FROM objects
                WHERE schema_kind=? AND object_id=? AND revision_id=?
                """,
                (schema_kind, object_id, revision_id),
            ).fetchone()
            if row is None:
                raise KeyError(f"object not found: {schema_kind}:{object_id}@{revision_id}")
            return self._load_ref_conn(
                conn,
                ExactRef(
                    object_id=object_id,
                    revision_id=revision_id,
                    content_hash=row["content_hash"],
                ),
                schema_kind,
            )

    _ATTEMPT_TRANSITIONS = {
        AttemptState.CREATED: {AttemptState.PREFLIGHT, AttemptState.CANCELLED},
        AttemptState.PREFLIGHT: {AttemptState.LOCKED, AttemptState.CANCELLED},
        AttemptState.LOCKED: {
            AttemptState.RUNNING,
            AttemptState.CANCELLED,
            AttemptState.PREEMPTED,
        },
        AttemptState.RUNNING: {
            AttemptState.COMPLETED,
            AttemptState.EXECUTOR_FAILED,
            AttemptState.CANCELLED,
            AttemptState.TIMED_OUT,
            AttemptState.PREEMPTED,
        },
    }

    def _persist_attempt_conn(
        self, conn: sqlite3.Connection, attempt: ExecutionAttemptEnvelope
    ) -> None:
        self._put_object_conn(conn, attempt)
        row = conn.execute(
            "SELECT * FROM attempt_ledger WHERE attempt_id=?",
            (attempt.attempt_id,),
        ).fetchone()
        fingerprint = _attempt_immutable_fingerprint(attempt)
        if row is None:
            if attempt.state != AttemptState.CREATED:
                raise StandaloneRuntimeError("new attempt must begin in CREATED")
            conn.execute(
                """
                INSERT INTO attempt_ledger(
                    attempt_id,current_object_id,current_revision_id,current_hash,state,
                    proof_object_id,proof_revision_id,proof_hash,immutable_fingerprint
                ) VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (
                    attempt.attempt_id,
                    attempt.object_id,
                    attempt.revision_id,
                    attempt.content_hash,
                    attempt.state.value,
                    attempt.proof_ref.object_id,
                    attempt.proof_ref.revision_id,
                    attempt.proof_ref.content_hash,
                    fingerprint,
                ),
            )
        else:
            if row["immutable_fingerprint"] != fingerprint:
                raise StandaloneRuntimeError(
                    "attempt semantic/runtime assignment changed under same attempt_id"
                )
            current_ref = ExactRef(
                object_id=row["current_object_id"],
                revision_id=row["current_revision_id"],
                content_hash=row["current_hash"],
            )
            if current_ref == attempt.exact_ref():
                return
            current_state = AttemptState(row["state"])
            allowed = self._ATTEMPT_TRANSITIONS.get(current_state, set())
            if attempt.state not in allowed:
                raise StandaloneRuntimeError(
                    f"illegal attempt transition {current_state.value}->{attempt.state.value}"
                )
            conn.execute(
                """
                UPDATE attempt_ledger
                SET current_object_id=?,current_revision_id=?,current_hash=?,state=?
                WHERE attempt_id=?
                """,
                (
                    attempt.object_id,
                    attempt.revision_id,
                    attempt.content_hash,
                    attempt.state.value,
                    attempt.attempt_id,
                ),
            )
        self._event_conn(
            conn,
            "ATTEMPT_STATE",
            attempt.attempt_id,
            {
                "state": attempt.state.value,
                "attempt_ref": attempt.exact_ref().model_dump(mode="json"),
            },
        )

    def persist_attempt(self, attempt: ExecutionAttemptEnvelope) -> None:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            self._persist_attempt_conn(conn, attempt)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def current_attempt(self, attempt_id: str) -> ExecutionAttemptEnvelope:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT current_object_id,current_revision_id,current_hash FROM attempt_ledger WHERE attempt_id=?",
                (attempt_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"attempt not found: {attempt_id}")
            return self._load_ref_conn(
                conn,
                ExactRef(
                    object_id=row["current_object_id"],
                    revision_id=row["current_revision_id"],
                    content_hash=row["current_hash"],
                ),
                "execution_attempt_envelope",
            )

    def record_execution_result(self, result: ExecutionResult) -> None:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            attempt = self._load_ref_conn(
                conn, result.attempt_ref, "execution_attempt_envelope"
            )
            if result.executor_state != attempt.state:
                raise StandaloneRuntimeError(
                    "ExecutionResult state does not match exact attempt envelope"
                )
            self._put_object_conn(conn, result)
            existing = conn.execute(
                "SELECT * FROM execution_results WHERE attempt_id=?",
                (attempt.attempt_id,),
            ).fetchone()
            if existing is not None:
                same = (
                    existing["result_object_id"] == result.object_id
                    and existing["result_revision_id"] == result.revision_id
                    and existing["result_hash"] == result.content_hash
                )
                if same:
                    conn.commit()
                    return
                raise StandaloneRuntimeError("attempt already has a different ExecutionResult")
            conn.execute(
                """
                INSERT INTO execution_results(
                    attempt_id,result_object_id,result_revision_id,result_hash
                ) VALUES (?,?,?,?)
                """,
                (
                    attempt.attempt_id,
                    result.object_id,
                    result.revision_id,
                    result.content_hash,
                ),
            )
            self._event_conn(
                conn,
                "EXECUTION_RESULT",
                attempt.attempt_id,
                {"result_ref": result.exact_ref().model_dump(mode="json")},
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def record_adjudication(self, adjudication: Adjudication) -> None:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            attempt = self._load_ref_conn(
                conn, adjudication.attempt_ref, "execution_attempt_envelope"
            )
            self._put_object_conn(conn, adjudication)
            existing = conn.execute(
                "SELECT * FROM adjudications WHERE attempt_id=?",
                (attempt.attempt_id,),
            ).fetchone()
            if existing is not None:
                same = (
                    existing["adjudication_object_id"] == adjudication.object_id
                    and existing["adjudication_revision_id"] == adjudication.revision_id
                    and existing["adjudication_hash"] == adjudication.content_hash
                )
                if same:
                    conn.commit()
                    return
                raise StandaloneRuntimeError(
                    "terminal adjudication already exists for attempt"
                )
            conn.execute(
                """
                INSERT INTO adjudications(
                    attempt_id,adjudication_object_id,adjudication_revision_id,adjudication_hash
                ) VALUES (?,?,?,?)
                """,
                (
                    attempt.attempt_id,
                    adjudication.object_id,
                    adjudication.revision_id,
                    adjudication.content_hash,
                ),
            )
            self._event_conn(
                conn,
                "ADJUDICATION_RECORDED",
                attempt.attempt_id,
                {
                    "adjudication_ref": adjudication.exact_ref().model_dump(mode="json"),
                    "verdict": adjudication.verdict.value,
                },
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def load_adjudication(self, attempt_id: str) -> Adjudication:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM adjudications WHERE attempt_id=?",
                (attempt_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"adjudication not found for attempt: {attempt_id}")
            return self._load_ref_conn(
                conn,
                ExactRef(
                    object_id=row["adjudication_object_id"],
                    revision_id=row["adjudication_revision_id"],
                    content_hash=row["adjudication_hash"],
                ),
                "adjudication",
            )

    def _persist_protected_conn(
        self, conn: sqlite3.Connection, resource: ProtectedResource
    ) -> None:
        self._put_object_conn(conn, resource)
        row = conn.execute(
            "SELECT * FROM protected_current WHERE resource_id=?",
            (resource.object_id,),
        ).fetchone()
        if row is None:
            if resource.freshness_state == FreshnessState.RESERVED:
                raise StandaloneRuntimeError(
                    "initial protected resource cannot appear RESERVED without reservation"
                )
            conn.execute(
                """
                INSERT INTO protected_current(
                    resource_id,current_revision_id,current_hash,resource_type,identity_ref,
                    freshness_state,reuse_allowed
                ) VALUES (?,?,?,?,?,?,?)
                """,
                (
                    resource.object_id,
                    resource.revision_id,
                    resource.content_hash,
                    resource.resource_type,
                    resource.identity_ref,
                    resource.freshness_state.value,
                    int(resource.reuse_allowed),
                ),
            )
        else:
            if row["resource_type"] != resource.resource_type or row["identity_ref"] != resource.identity_ref:
                raise StandaloneRuntimeError(
                    "protected resource identity changed under same resource ID"
                )
            current = FreshnessState(row["freshness_state"])
            target = resource.freshness_state
            allowed = {
                FreshnessState.FRESH: {FreshnessState.FRESH, FreshnessState.RESERVED, FreshnessState.EXPOSED},
                FreshnessState.RESERVED: {FreshnessState.RESERVED, FreshnessState.EXPOSED},
                FreshnessState.EXPOSED: {FreshnessState.EXPOSED},
            }
            if target not in allowed[current]:
                raise StandaloneRuntimeError(
                    f"protected freshness cannot move backward {current.value}->{target.value}"
                )
            current_ref = ExactRef(
                object_id=resource.object_id,
                revision_id=row["current_revision_id"],
                content_hash=row["current_hash"],
            )
            if current_ref == resource.exact_ref():
                return
            conn.execute(
                """
                UPDATE protected_current
                SET current_revision_id=?,current_hash=?,freshness_state=?,reuse_allowed=?
                WHERE resource_id=?
                """,
                (
                    resource.revision_id,
                    resource.content_hash,
                    target.value,
                    int(resource.reuse_allowed),
                    resource.object_id,
                ),
            )
        self._event_conn(
            conn,
            "PROTECTED_RESOURCE_STATE",
            resource.object_id,
            {
                "freshness_state": resource.freshness_state.value,
                "resource_ref": resource.exact_ref().model_dump(mode="json"),
            },
        )

    def persist_protected_resource(self, resource: ProtectedResource) -> None:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            self._persist_protected_conn(conn, resource)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def current_protected_resource(self, resource_id: str) -> ProtectedResource:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT current_revision_id,current_hash FROM protected_current WHERE resource_id=?",
                (resource_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"protected resource not found: {resource_id}")
            return self._load_ref_conn(
                conn,
                ExactRef(
                    object_id=resource_id,
                    revision_id=row["current_revision_id"],
                    content_hash=row["current_hash"],
                ),
                "protected_resource",
            )

    def reserve_resource_for_attempt(
        self,
        resource_id: str,
        attempt_id: str,
        *,
        provenance: Provenance,
        revision_id: str,
    ) -> ProtectedResource:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            attempt_row = conn.execute(
                "SELECT state FROM attempt_ledger WHERE attempt_id=?",
                (attempt_id,),
            ).fetchone()
            if attempt_row is None or AttemptState(attempt_row["state"]) != AttemptState.LOCKED:
                raise StandaloneRuntimeError(
                    "protected reservation requires LOCKED attempt"
                )
            row = conn.execute(
                "SELECT current_revision_id,current_hash FROM protected_current WHERE resource_id=?",
                (resource_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"protected resource not found: {resource_id}")
            current = self._load_ref_conn(
                conn,
                ExactRef(
                    object_id=resource_id,
                    revision_id=row["current_revision_id"],
                    content_hash=row["current_hash"],
                ),
                "protected_resource",
            )
            existing = conn.execute(
                "SELECT * FROM resource_reservations WHERE resource_id=?",
                (resource_id,),
            ).fetchone()
            if existing is not None and existing["status"] in {"RESERVED", "REUSE_EXPOSED"}:
                raise StandaloneRuntimeError("protected resource already reserved")

            if current.freshness_state == FreshnessState.FRESH:
                updated = transition_protected_resource(
                    current,
                    "RESERVE",
                    revision_id=revision_id,
                    provenance=provenance,
                )
                status = "RESERVED"
                self._persist_protected_conn(conn, updated)
            elif current.freshness_state == FreshnessState.EXPOSED and current.reuse_allowed:
                updated = current
                status = "REUSE_EXPOSED"
            else:
                raise StandaloneRuntimeError(
                    "protected resource is not available for reservation"
                )

            conn.execute(
                """
                INSERT INTO resource_reservations(resource_id,attempt_id,status)
                VALUES (?,?,?)
                ON CONFLICT(resource_id) DO UPDATE SET
                  attempt_id=excluded.attempt_id,status=excluded.status
                """,
                (resource_id, attempt_id, status),
            )
            self._event_conn(
                conn,
                "PROTECTED_RESOURCE_RESERVED",
                resource_id,
                {"attempt_id": attempt_id, "status": status},
            )
            conn.commit()
            return updated
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def expose_resource_for_attempt(
        self,
        resource_id: str,
        attempt_id: str,
        *,
        provenance: Provenance,
        revision_id: str,
    ) -> ProtectedResource:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            reservation = conn.execute(
                "SELECT * FROM resource_reservations WHERE resource_id=?",
                (resource_id,),
            ).fetchone()
            if reservation is None or reservation["attempt_id"] != attempt_id:
                raise StandaloneRuntimeError("resource is not reserved by this attempt")
            row = conn.execute(
                "SELECT current_revision_id,current_hash FROM protected_current WHERE resource_id=?",
                (resource_id,),
            ).fetchone()
            current = self._load_ref_conn(
                conn,
                ExactRef(
                    object_id=resource_id,
                    revision_id=row["current_revision_id"],
                    content_hash=row["current_hash"],
                ),
                "protected_resource",
            )
            if reservation["status"] == "REUSE_EXPOSED":
                updated = current
            else:
                updated = transition_protected_resource(
                    current,
                    "EXPOSE",
                    revision_id=revision_id,
                    provenance=provenance,
                )
                self._persist_protected_conn(conn, updated)
            conn.execute(
                "UPDATE resource_reservations SET status='EXPOSED' WHERE resource_id=?",
                (resource_id,),
            )
            self._event_conn(
                conn,
                "PROTECTED_RESOURCE_EXPOSED",
                resource_id,
                {"attempt_id": attempt_id},
            )
            conn.commit()
            return updated
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def put_evidence_payload(
        self, evidence: EvidenceRecord, payload: Mapping[str, Any]
    ) -> None:
        if evidence.payload_digest is None:
            raise StandaloneRuntimeError("evidence payload digest is missing")
        payload_json = canonical_json(dict(payload))
        if canonical_hash(dict(payload)) != evidence.payload_digest:
            raise StandaloneRuntimeError("evidence payload does not match EvidenceRecord digest")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evidence_payloads(object_id,revision_id,content_hash,payload_json)
                VALUES (?,?,?,?)
                ON CONFLICT(object_id,revision_id) DO UPDATE SET
                  content_hash=excluded.content_hash,payload_json=excluded.payload_json
                """,
                (
                    evidence.object_id,
                    evidence.revision_id,
                    evidence.content_hash,
                    payload_json,
                ),
            )

    def load_evidence_payload(self, evidence: EvidenceRecord) -> Mapping[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT content_hash,payload_json FROM evidence_payloads
                WHERE object_id=? AND revision_id=?
                """,
                (evidence.object_id, evidence.revision_id),
            ).fetchone()
            if row is None:
                raise KeyError(f"evidence payload not found: {evidence.object_id}")
            if row["content_hash"] != evidence.content_hash:
                raise StandaloneRuntimeError("evidence payload record binds stale evidence revision")
            payload = json.loads(row["payload_json"])
            if canonical_hash(payload) != evidence.payload_digest:
                raise StandaloneRuntimeError("stored evidence payload digest mismatch")
            return payload

    def events(self) -> tuple[Mapping[str, Any], ...]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT seq,event_type,subject_id,payload_json FROM runtime_events ORDER BY seq"
            ).fetchall()
            return tuple(
                {
                    "seq": row["seq"],
                    "event_type": row["event_type"],
                    "subject_id": row["subject_id"],
                    "payload": json.loads(row["payload_json"]),
                }
                for row in rows
            )

    def recover(self, *, provenance: Provenance) -> RecoveryReport:
        exposed: list[str] = []
        preempted: list[str] = []
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            reservations = conn.execute(
                "SELECT resource_id,attempt_id,status FROM resource_reservations WHERE status='RESERVED'"
            ).fetchall()
            for reservation in reservations:
                row = conn.execute(
                    "SELECT current_revision_id,current_hash FROM protected_current WHERE resource_id=?",
                    (reservation["resource_id"],),
                ).fetchone()
                current = self._load_ref_conn(
                    conn,
                    ExactRef(
                        object_id=reservation["resource_id"],
                        revision_id=row["current_revision_id"],
                        content_hash=row["current_hash"],
                    ),
                    "protected_resource",
                )
                if current.freshness_state == FreshnessState.RESERVED:
                    updated = transition_protected_resource(
                        current,
                        "RECOVERY_UNCERTAIN_ACCESS",
                        revision_id=current.revision_id + ".recovery",
                        provenance=provenance,
                    )
                    self._persist_protected_conn(conn, updated)
                    exposed.append(current.object_id)
                conn.execute(
                    "UPDATE resource_reservations SET status='EXPOSED_RECOVERY' WHERE resource_id=?",
                    (reservation["resource_id"],),
                )

            attempt_rows = conn.execute(
                """
                SELECT * FROM attempt_ledger
                WHERE state IN (?,?)
                """,
                (AttemptState.LOCKED.value, AttemptState.RUNNING.value),
            ).fetchall()
            for row in attempt_rows:
                current = self._load_ref_conn(
                    conn,
                    ExactRef(
                        object_id=row["current_object_id"],
                        revision_id=row["current_revision_id"],
                        content_hash=row["current_hash"],
                    ),
                    "execution_attempt_envelope",
                )
                recovered = _revise_attempt(
                    current,
                    AttemptState.PREEMPTED,
                    current.revision_id + ".recovery",
                    provenance,
                )
                self._persist_attempt_conn(conn, recovered)
                preempted.append(current.attempt_id)

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
        return RecoveryReport(tuple(sorted(exposed)), tuple(sorted(preempted)))


def _revise_attempt(
    attempt: ExecutionAttemptEnvelope,
    state: AttemptState,
    revision_id: str,
    provenance: Provenance,
) -> ExecutionAttemptEnvelope:
    data = attempt.model_dump(mode="python", exclude={"content_hash"})
    data.update(
        {
            "revision_id": revision_id,
            "provenance": provenance,
            "state": state,
        }
    )
    return ExecutionAttemptEnvelope.sealed(**data)


class LocalExecutorFacade:
    def __init__(self, store: StandaloneStore):
        self.store = store

    def execute(
        self,
        initial_attempt: ExecutionAttemptEnvelope,
        runner: Callable[[], LocalExecutionOutcome],
        *,
        provenance: Provenance,
        protected_resource_ids: Sequence[str] = (),
    ) -> LocalExecutionReport:
        if initial_attempt.state != AttemptState.CREATED:
            raise StandaloneRuntimeError("local execution requires CREATED attempt")

        self.store.persist_attempt(initial_attempt)
        preflight = _revise_attempt(
            initial_attempt,
            AttemptState.PREFLIGHT,
            initial_attempt.revision_id + ".preflight",
            provenance,
        )
        self.store.persist_attempt(preflight)
        locked = _revise_attempt(
            preflight,
            AttemptState.LOCKED,
            preflight.revision_id + ".locked",
            provenance,
        )
        self.store.persist_attempt(locked)

        for index, resource_id in enumerate(protected_resource_ids, start=1):
            self.store.reserve_resource_for_attempt(
                resource_id,
                locked.attempt_id,
                provenance=provenance,
                revision_id=f"reserved-{locked.attempt_id}-{index}",
            )

        running = _revise_attempt(
            locked,
            AttemptState.RUNNING,
            locked.revision_id + ".running",
            provenance,
        )
        self.store.persist_attempt(running)

        started_at = _utc_now()
        outcome: LocalExecutionOutcome | None = None
        technical_error_class: str | None = None
        technical_error_reason: str | None = None
        terminal_state = AttemptState.COMPLETED
        try:
            outcome = runner()
            if not isinstance(outcome, LocalExecutionOutcome):
                raise TypeError("local runner must return LocalExecutionOutcome")
        except Exception as exc:
            terminal_state = AttemptState.EXECUTOR_FAILED
            technical_error_class = type(exc).__name__
            technical_error_reason = str(exc)

        # Exposure is durable before any successful outcome is returned to caller.
        for index, resource_id in enumerate(protected_resource_ids, start=1):
            self.store.expose_resource_for_attempt(
                resource_id,
                running.attempt_id,
                provenance=provenance,
                revision_id=f"exposed-{running.attempt_id}-{index}",
            )

        final_attempt = _revise_attempt(
            running,
            terminal_state,
            running.revision_id + "." + terminal_state.value.lower(),
            provenance,
        )
        self.store.persist_attempt(final_attempt)
        ended_at = _utc_now()

        candidate_records: list[EvidenceRecord] = []
        payloads: dict[str, Mapping[str, Any]] = {}
        artifact_refs: tuple[str, ...] = ()
        resource_identity: str | None = None
        action_summary = "local execution failed"

        if outcome is not None:
            artifact_refs = outcome.artifact_refs
            resource_identity = outcome.resource_identity
            action_summary = outcome.action_summary
            for index, spec in enumerate(outcome.evidence, start=1):
                object_id = spec.object_id or f"evidence-{final_attempt.attempt_id}-{index}"
                freshness = spec.freshness_state
                if freshness is None and protected_resource_ids:
                    freshness = FreshnessState.EXPOSED
                payload = dict(spec.payload)
                record = EvidenceRecord.sealed(
                    object_id=object_id,
                    revision_id="candidate-r1",
                    provenance=provenance,
                    source_class=spec.source_class,
                    lifecycle=EvidenceLifecycle.CANDIDATE,
                    producer_attempt_ref=final_attempt.exact_ref(),
                    subject_refs=spec.subject_refs,
                    artifact_refs=spec.artifact_refs,
                    resource_refs=spec.resource_refs,
                    payload_digest=canonical_hash(payload),
                    freshness_state=freshness,
                )
                self.store.put(record)
                self.store.put_evidence_payload(record, payload)
                candidate_records.append(record)
                payloads[record.object_id] = payload

        result = ExecutionResult.sealed(
            object_id=f"execution-result-{final_attempt.attempt_id}",
            revision_id="r1",
            provenance=provenance,
            attempt_ref=final_attempt.exact_ref(),
            executor_state=terminal_state,
            started_at=started_at,
            ended_at=ended_at,
            action_summary=action_summary,
            artifact_refs=artifact_refs,
            candidate_evidence_refs=tuple(r.exact_ref() for r in candidate_records),
            resource_identity=resource_identity,
            technical_error_class=technical_error_class,
            technical_error_reason=technical_error_reason,
            redaction_metadata={"mode": "standalone-local"},
        )
        self.store.record_execution_result(result)
        return LocalExecutionReport(
            final_attempt=final_attempt,
            execution_result=result,
            candidate_evidence=tuple(candidate_records),
            evidence_payloads=payloads,
        )


class StandaloneEvidenceLibrary:
    def __init__(self, store: StandaloneStore):
        self.store = store

    def capability_manifest(
        self,
        *,
        provenance: Provenance,
        qualification_status: BackendQualificationStatus = BackendQualificationStatus.UNQUALIFIED,
        evidence_refs: Sequence[str] = (),
    ) -> LibraryCapabilityManifest:
        caps = tuple(
            LibraryCapability(
                capability_id=capability,
                status=qualification_status,
                evidence_refs=tuple(evidence_refs),
                supported_subject_kinds=("evidence_capsule", "synthesis_result"),
                supported_query_modes=("exact_metadata",),
            )
            for capability in (
                "publish",
                "withdraw",
                "query",
                "snapshot",
                "provenance",
                "integrity",
            )
        )
        return LibraryCapabilityManifest.sealed(
            object_id="standalone-library-capabilities",
            revision_id="r1",
            provenance=provenance,
            backend_id="g2e-standalone-library",
            backend_type="STANDALONE",
            adapter_version="0.1",
            runtime_version=RUNTIME_VERSION,
            supported_schema_versions=("1.0",),
            capabilities=caps,
            security_access_model="single_user_local_filesystem",
            exact_backend_revision=None,
        )

    @staticmethod
    def require_capability(
        manifest: LibraryCapabilityManifest, capability_id: str
    ) -> None:
        cap = next(
            (c for c in manifest.capabilities if c.capability_id == capability_id),
            None,
        )
        if cap is None or cap.status != BackendQualificationStatus.QUALIFIED:
            raise UnsupportedCapabilityError(
                f"BACKEND_CAPABILITY_UNSUPPORTED:{capability_id}"
            )

    def publish_capsule(
        self,
        capsule: EvidenceCapsule,
        contract: LibraryPublicationContract,
        metadata: Mapping[str, Any],
    ) -> str:
        if contract.subject_ref != capsule.exact_ref():
            raise StandaloneRuntimeError("publication contract subject mismatch")
        if contract.source_package_type != capsule.source_package_type:
            raise StandaloneRuntimeError("publication source package type mismatch")
        if contract.source_package_seal_hash != capsule.source_package_seal_hash:
            raise StandaloneRuntimeError("publication source package seal mismatch")

        publication_id = "pub-" + canonical_hash(
            {
                "subject": capsule.exact_ref().model_dump(mode="json"),
                "scope": contract.publication_scope,
                "metadata_namespace": contract.metadata_namespace,
                "metadata_schema_version": contract.metadata_schema_version,
                "metadata": dict(metadata),
            }
        )[:24]

        conn = self.store._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            self.store._put_object_conn(conn, capsule)
            self.store._put_object_conn(conn, contract)
            existing = conn.execute(
                "SELECT * FROM library_publications WHERE publication_id=?",
                (publication_id,),
            ).fetchone()
            payload = (
                capsule.object_id,
                capsule.revision_id,
                capsule.content_hash,
                capsule.schema_kind,
                capsule.source_claim_resolution.value,
                capsule.source_package_seal_hash,
                contract.publication_scope,
                contract.metadata_namespace,
                contract.metadata_schema_version,
                canonical_json(dict(metadata)),
            )
            if existing is None:
                conn.execute(
                    """
                    INSERT INTO library_publications(
                        publication_id,subject_object_id,subject_revision_id,subject_hash,
                        subject_kind,source_claim_resolution,source_package_seal_hash,
                        publication_scope,metadata_namespace,metadata_schema_version,
                        metadata_json,active,withdraw_reason
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,1,NULL)
                    """,
                    (publication_id, *payload),
                )
            else:
                comparable = (
                    existing["subject_object_id"],
                    existing["subject_revision_id"],
                    existing["subject_hash"],
                    existing["subject_kind"],
                    existing["source_claim_resolution"],
                    existing["source_package_seal_hash"],
                    existing["publication_scope"],
                    existing["metadata_namespace"],
                    existing["metadata_schema_version"],
                    existing["metadata_json"],
                )
                if comparable != payload:
                    raise ObjectConflictError("publication ID collision")
                conn.execute(
                    "UPDATE library_publications SET active=1,withdraw_reason=NULL WHERE publication_id=?",
                    (publication_id,),
                )
            self.store._event_conn(
                conn,
                "LIBRARY_PUBLISHED",
                publication_id,
                {"subject_ref": capsule.exact_ref().model_dump(mode="json")},
            )
            conn.commit()
            return publication_id
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def withdraw_publication(self, publication_id: str, reason: str) -> None:
        with self.store._connect() as conn:
            row = conn.execute(
                "SELECT publication_id FROM library_publications WHERE publication_id=?",
                (publication_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"publication not found: {publication_id}")
            conn.execute(
                "UPDATE library_publications SET active=0,withdraw_reason=? WHERE publication_id=?",
                (reason, publication_id),
            )

    def _snapshot_rows(self) -> list[dict[str, Any]]:
        with self.store._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM library_publications
                WHERE active=1 ORDER BY publication_id
                """
            ).fetchall()
            return [
                {
                    "publication_id": row["publication_id"],
                    "subject_object_id": row["subject_object_id"],
                    "subject_revision_id": row["subject_revision_id"],
                    "subject_hash": row["subject_hash"],
                    "subject_kind": row["subject_kind"],
                    "source_claim_resolution": row["source_claim_resolution"],
                    "source_package_seal_hash": row["source_package_seal_hash"],
                    "publication_scope": row["publication_scope"],
                    "metadata_namespace": row["metadata_namespace"],
                    "metadata_schema_version": row["metadata_schema_version"],
                    "metadata": json.loads(row["metadata_json"]),
                }
                for row in rows
            ]

    def get_catalog_snapshot(self, *, provenance: Provenance) -> LibrarySnapshot:
        rows = self._snapshot_rows()
        snapshot_ref = canonical_hash(rows)
        with self.store._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO library_snapshots(snapshot_ref,payload_json)
                VALUES (?,?)
                """,
                (snapshot_ref, canonical_json(rows)),
            )
        snapshot = LibrarySnapshot.sealed(
            object_id=f"library-snapshot-{snapshot_ref[:16]}",
            revision_id="r1",
            provenance=provenance,
            backend_id="g2e-standalone-library",
            backend_version="0.1",
            snapshot_ref=snapshot_ref,
            subject_refs=tuple(
                ExactRef(
                    object_id=row["subject_object_id"],
                    revision_id=row["subject_revision_id"],
                    content_hash=row["subject_hash"],
                )
                for row in rows
            ),
        )
        self.store.put(snapshot)
        return snapshot

    def _load_snapshot_rows(self, snapshot_ref: str) -> list[dict[str, Any]]:
        with self.store._connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM library_snapshots WHERE snapshot_ref=?",
                (snapshot_ref,),
            ).fetchone()
            if row is None:
                raise StandaloneRuntimeError("SNAPSHOT_MISMATCH")
            return list(json.loads(row["payload_json"]))

    @staticmethod
    def _matches(row: Mapping[str, Any], payload: Mapping[str, Any]) -> bool:
        supported = {"subject_type", "object_id", "source_claim_resolution", "metadata"}
        unknown = set(payload) - supported
        if unknown:
            raise UnsupportedCapabilityError(
                "BACKEND_CAPABILITY_UNSUPPORTED:" + ",".join(sorted(unknown))
            )
        if "subject_type" in payload and row["subject_kind"] != payload["subject_type"]:
            return False
        if "object_id" in payload and row["subject_object_id"] != payload["object_id"]:
            return False
        if (
            "source_claim_resolution" in payload
            and row["source_claim_resolution"] != payload["source_claim_resolution"]
        ):
            return False
        if "metadata" in payload:
            expected = payload["metadata"]
            if not isinstance(expected, Mapping):
                raise StandaloneRuntimeError("QUERY_FAILED:metadata filter must be object")
            for key, value in expected.items():
                if row["metadata"].get(key) != value:
                    return False
        return True

    def query_candidates(
        self,
        contract: LibraryQueryContract,
        *,
        provenance: Provenance,
        snapshot_ref: str | None = None,
        execution_id: str | None = None,
    ) -> LibraryQueryExecution:
        self.store.put(contract)
        resolved_snapshot = snapshot_ref
        try:
            if resolved_snapshot is None:
                resolved_snapshot = self.get_catalog_snapshot(
                    provenance=provenance
                ).snapshot_ref
            rows = self._load_snapshot_rows(resolved_snapshot)
            matched = [
                row
                for row in rows
                if self._matches(row, contract.query_payload)
            ]
            refs = tuple(
                ExactRef(
                    object_id=row["subject_object_id"],
                    revision_id=row["subject_revision_id"],
                    content_hash=row["subject_hash"],
                )
                for row in matched
            )
            status = LibraryExecutionStatus.SUCCEEDED
            complete = True
            reason = None
        except Exception as exc:
            refs = ()
            status = LibraryExecutionStatus.FAILED
            complete = False
            reason = f"QUERY_FAILED:{type(exc).__name__}:{exc}"
            resolved_snapshot = resolved_snapshot or "UNAVAILABLE"

        object_id = execution_id or (
            f"library-query-execution-{contract.object_id}-"
            f"{canonical_hash({'snapshot': resolved_snapshot, 'query': contract.content_hash})[:12]}"
        )
        execution = LibraryQueryExecution.sealed(
            object_id=object_id,
            revision_id="r1",
            provenance=provenance,
            query_ref=contract.exact_ref(),
            backend_id="g2e-standalone-library",
            backend_version="0.1",
            snapshot_ref=resolved_snapshot,
            status=status,
            complete=complete,
            result_subject_refs=refs,
            ranking_backend_version=None,
            reason=reason,
        )
        self.store.put(execution)
        return execution

    def replay_query(
        self,
        prior_execution: LibraryQueryExecution,
        contract: LibraryQueryContract,
        *,
        provenance: Provenance,
    ) -> LibraryQueryExecution:
        return self.query_candidates(
            contract,
            provenance=provenance,
            snapshot_ref=prior_execution.snapshot_ref,
            execution_id=f"{prior_execution.object_id}-replay",
        )

    def resolve_subject(self, publication_id: str) -> CanonicalModel:
        with self.store._connect() as conn:
            row = conn.execute(
                "SELECT * FROM library_publications WHERE publication_id=?",
                (publication_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"publication not found: {publication_id}")
            return self.store._load_ref_conn(
                conn,
                ExactRef(
                    object_id=row["subject_object_id"],
                    revision_id=row["subject_revision_id"],
                    content_hash=row["subject_hash"],
                ),
            )

    def get_provenance_ancestors(self, subject_ref: ExactRef) -> tuple[ExactRef, ...]:
        subject = self.store.load_ref(subject_ref)
        if isinstance(subject, EvidenceCapsule):
            return tuple(subject.provenance_ancestor_refs)
        if isinstance(subject, SynthesisResult):
            return tuple(subject.source_provenance_closure)
        return ()

    def verify_subject_integrity(self, subject_ref: ExactRef) -> bool:
        self.store.load_ref(subject_ref)
        return True


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".partial")
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _fsync_dir(path: Path) -> None:
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def export_goal_result_package(
    destination: str | Path,
    *,
    goal: GoalContract,
    goal_closure: GoalClosureContract,
    claim_graph: CanonicalModel,
    proofs: Sequence[CanonicalModel],
    proof_dependencies: Sequence[CanonicalModel],
    evidence: Sequence[EvidenceRecord],
    adjudications: Sequence[Adjudication],
    claim_resolutions: Mapping[str, ClaimResolution],
    reproducibility_manifest: Mapping[str, Any],
    package_lineage: Sequence[Mapping[str, Any]],
    provenance: Provenance,
    imported_refs: Sequence[ExactRef] = (),
    synthesis_result: SynthesisResult | None = None,
    external_reference_policy: ExternalReferencePolicy = ExternalReferencePolicy.OFFLINE_ONLY,
    external_references: Sequence[PackageExternalReference] = (),
    framework_version: str = "g2e-p3",
    runtime_id: str = RUNTIME_ID,
    runtime_version: str = RUNTIME_VERSION,
    external_resolver: Callable[[PackageExternalReference], bytes | None] | None = None,
    authorized_stop: bool = False,
) -> PackageVerificationResult:
    if goal_closure.goal_contract_ref != goal.exact_ref():
        raise StandaloneRuntimeError("GoalClosureContract does not bind exact Goal")
    if goal_closure.claim_graph_ref != claim_graph.exact_ref():
        raise StandaloneRuntimeError("GoalClosureContract does not bind exact ClaimGraph")
    for claim_id in goal_closure.terminal_claim_ids:
        resolution = claim_resolutions.get(claim_id, ClaimResolution.UNKNOWN)
        if resolution == ClaimResolution.UNKNOWN:
            raise StandaloneRuntimeError(
                f"terminal Claim lacks terminal resolution: {claim_id}"
            )
    final_verdict = evaluate_goal(
        goal_closure,
        claim_resolutions,
        can_progress=False,
        authorized_stop=authorized_stop,
    )

    destination = Path(destination)
    if destination.exists():
        raise StandaloneRuntimeError("package destination already exists")
    partial = destination.with_name("." + destination.name + ".partial")
    if partial.exists():
        shutil.rmtree(partial)
    partial.mkdir(parents=True)

    files: dict[str, bytes] = {
        "GOAL.json": _json_file_bytes(goal),
        "GOAL_CLOSURE.json": _json_file_bytes(goal_closure),
        "CLAIM_GRAPH.json": _json_file_bytes(claim_graph),
        "PROOF_GRAPH.json": _json_file_bytes(
            {
                "proofs": [
                    p.model_dump(mode="json")
                    for p in sorted(proofs, key=lambda x: x.object_id)
                ],
                "dependencies": [
                    p.model_dump(mode="json")
                    for p in sorted(
                        proof_dependencies,
                        key=lambda x: (x.schema_kind, x.object_id),
                    )
                ],
            }
        ),
        "EVIDENCE_GRAPH.json": _json_file_bytes(
            [e.model_dump(mode="json") for e in sorted(evidence, key=lambda x: x.object_id)]
        ),
        "DECISION_LEDGER.json": _json_file_bytes(
            [a.model_dump(mode="json") for a in sorted(adjudications, key=lambda x: x.object_id)]
        ),
        "PACKAGE_LINEAGE.json": _json_file_bytes(list(package_lineage)),
        "FINAL_VERDICT.json": _json_file_bytes(
            {
                "goal_ref": goal.exact_ref().model_dump(mode="json"),
                "goal_closure_ref": goal_closure.exact_ref().model_dump(mode="json"),
                "verdict": final_verdict.value,
            }
        ),
        "REPRODUCIBILITY_MANIFEST.json": _json_file_bytes(dict(reproducibility_manifest)),
        "library/IMPORTS.json": _json_file_bytes(
            [ref.model_dump(mode="json") for ref in imported_refs]
        ),
    }

    for claim in sorted(claim_graph.claims, key=lambda c: c.object_id):
        component = _safe_component(claim.object_id)
        files[f"claims/{component}/CONTRACT.json"] = _json_file_bytes(claim)
        files[f"claims/{component}/RESOLUTION.json"] = _json_file_bytes(
            {
                "claim_ref": claim.exact_ref().model_dump(mode="json"),
                "resolution": claim_resolutions.get(
                    claim.object_id, claim.resolution
                ).value,
            }
        )
        refs = []
        for record in evidence:
            if claim.exact_ref() in record.subject_refs:
                refs.append(record.exact_ref().model_dump(mode="json"))
        files[f"claims/{component}/evidence/REFS.json"] = _json_file_bytes(refs)

    if synthesis_result is not None:
        files["synthesis/SYNTHESIS_RESULT.json"] = _json_file_bytes(synthesis_result)

    for relative, data in files.items():
        _atomic_write(partial / relative, data)

    members = tuple(
        PackageMember(
            path=relative,
            sha256=_sha256_bytes(data),
            size=len(data),
        )
        for relative, data in sorted(files.items())
    )
    manifest = PackageManifest.sealed(
        object_id=f"package-manifest-{goal.object_id}",
        revision_id="r1",
        provenance=provenance,
        members=members,
        external_reference_policy=external_reference_policy,
        external_references=tuple(external_references),
    )
    manifest_bytes = _model_file_bytes(manifest)
    _atomic_write(partial / "PACKAGE_MANIFEST.json", manifest_bytes)

    seal = PackageSeal.sealed(
        object_id=f"package-seal-{goal.object_id}",
        revision_id="r1",
        provenance=provenance,
        manifest_ref=manifest.exact_ref(),
        manifest_file_sha256=_sha256_bytes(manifest_bytes),
        framework_version=framework_version,
        runtime_id=runtime_id,
        runtime_version=runtime_version,
    )
    _atomic_write(partial / "PACKAGE_SEAL.json", _model_file_bytes(seal))
    _fsync_dir(partial)

    verification = verify_goal_result_package(
        partial, external_resolver=external_resolver
    )
    os.replace(partial, destination)
    _fsync_dir(destination.parent)
    return verification


def verify_goal_result_package(
    package_dir: str | Path,
    *,
    external_resolver: Callable[[PackageExternalReference], bytes | None] | None = None,
) -> PackageVerificationResult:
    package_dir = Path(package_dir)
    manifest_path = package_dir / "PACKAGE_MANIFEST.json"
    seal_path = package_dir / "PACKAGE_SEAL.json"
    if not manifest_path.is_file() or not seal_path.is_file():
        raise PackageVerificationError("manifest/seal missing")

    manifest_bytes = manifest_path.read_bytes()
    seal_bytes = seal_path.read_bytes()
    try:
        manifest = PackageManifest.parse_authoritative(json.loads(manifest_bytes))
        seal = PackageSeal.parse_authoritative(json.loads(seal_bytes))
    except Exception as exc:
        raise PackageVerificationError(f"manifest/seal canonical validation failed: {exc}") from exc

    if seal.manifest_ref != manifest.exact_ref():
        raise PackageVerificationError("seal does not bind exact manifest")
    if seal.manifest_file_sha256 != _sha256_bytes(manifest_bytes):
        raise PackageVerificationError("manifest file SHA-256 mismatch")

    expected_paths = {member.path for member in manifest.members}
    for member in manifest.members:
        path = package_dir / member.path
        if not path.is_file():
            raise PackageVerificationError(f"package member missing: {member.path}")
        data = path.read_bytes()
        if len(data) != member.size:
            raise PackageVerificationError(f"package member size mismatch: {member.path}")
        if _sha256_bytes(data) != member.sha256:
            raise PackageVerificationError(f"package member hash mismatch: {member.path}")

    actual_paths = {
        str(path.relative_to(package_dir)).replace(os.sep, "/")
        for path in package_dir.rglob("*")
        if path.is_file()
    }
    classified = expected_paths | {
        "PACKAGE_MANIFEST.json",
        "PACKAGE_SEAL.json",
    } | set(manifest.non_authoritative_paths)
    extras = sorted(actual_paths - classified)
    if extras:
        raise PackageVerificationError(
            "unclassified package content: " + ",".join(extras)
        )

    for ref in manifest.external_references:
        must_resolve = (
            manifest.external_reference_policy
            == ExternalReferencePolicy.REQUIRE_RESOLUTION
            or ref.required_online_resolution
        )
        should_try = (
            must_resolve
            or (
                manifest.external_reference_policy
                == ExternalReferencePolicy.VERIFY_WHEN_AVAILABLE
                and external_resolver is not None
            )
        )
        if not should_try:
            continue
        if external_resolver is None:
            raise PackageVerificationError(
                f"external reference resolver required: {ref.ref_id}"
            )
        data = external_resolver(ref)
        if data is None:
            if must_resolve:
                raise PackageVerificationError(
                    f"external reference unresolved: {ref.ref_id}"
                )
            continue
        if ref.expected_sha256 is not None and _sha256_bytes(data) != ref.expected_sha256:
            raise PackageVerificationError(
                f"external reference hash mismatch: {ref.ref_id}"
            )

    return PackageVerificationResult(manifest, seal, len(manifest.members))


class StandaloneRuntime:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.store = StandaloneStore(self.root)
        self.executor = LocalExecutorFacade(self.store)
        self.library = StandaloneEvidenceLibrary(self.store)

    def capability_manifest(
        self,
        *,
        provenance: Provenance,
        qualification_refs: Sequence[str] = (),
    ) -> RuntimeCapabilityManifest:
        capabilities = (
            RuntimeCapability(
                capability_id="canonical_persistence",
                available=True,
                qualification_refs=tuple(qualification_refs),
            ),
            RuntimeCapability(
                capability_id="atomic_persistence",
                available=True,
                qualification_refs=tuple(qualification_refs),
            ),
            RuntimeCapability(
                capability_id="restart_recovery",
                available=True,
                qualification_refs=tuple(qualification_refs),
            ),
            RuntimeCapability(
                capability_id="attempt_ledger",
                available=True,
                qualification_refs=tuple(qualification_refs),
            ),
            RuntimeCapability(
                capability_id="protected_resource_ledger",
                available=True,
                qualification_refs=tuple(qualification_refs),
            ),
            RuntimeCapability(
                capability_id="local_executor_facade",
                available=True,
                qualification_refs=tuple(qualification_refs),
            ),
            RuntimeCapability(
                capability_id="result_package",
                available=True,
                qualification_refs=tuple(qualification_refs),
            ),
            RuntimeCapability(
                capability_id="evidence_library",
                available=True,
                qualification_refs=tuple(qualification_refs),
            ),
            RuntimeCapability(
                capability_id="multi_user_approval",
                available=False,
                qualification_refs=tuple(qualification_refs),
                limitations=("standalone authority mode is single_user",),
            ),
            RuntimeCapability(
                capability_id="separation_of_duty",
                available=False,
                qualification_refs=tuple(qualification_refs),
                limitations=("requires external runtime/provider",),
            ),
        )
        return RuntimeCapabilityManifest.sealed(
            object_id="standalone-runtime-capabilities",
            revision_id="r1",
            provenance=provenance,
            runtime_id=RUNTIME_ID,
            runtime_version=RUNTIME_VERSION,
            runtime_mode=RuntimeMode.STANDALONE,
            authority_mode="single_user",
            persistence_backend="sqlite+filesystem",
            supported_schema_versions=("1.0",),
            capabilities=capabilities,
            security_assumptions=(
                "local user controls runtime directory permissions",
                "secrets are resolved outside canonical objects",
            ),
        )

    def require_capabilities(
        self,
        manifest: RuntimeCapabilityManifest,
        required: Sequence[str],
    ) -> None:
        available = {
            cap.capability_id: cap.available for cap in manifest.capabilities
        }
        missing = [cap for cap in required if available.get(cap) is not True]
        if missing:
            raise UnsupportedCapabilityError(
                "RUNTIME_CAPABILITY_UNAVAILABLE:" + ",".join(sorted(missing))
            )

    def recover(self, *, provenance: Provenance) -> RecoveryReport:
        return self.store.recover(provenance=provenance)
