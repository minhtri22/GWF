from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence

from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import parse_json

from .canonical import CanonicalModel, ExactRef, Provenance, canonical_hash
from .engine import transition_protected_resource
from .gwf_domain import G2E_GWF_DOMAIN_ID
from .schemas import (
    AttemptState,
    EvidenceLifecycle,
    EvidenceRecord,
    ExecutionAttemptEnvelope,
    ExecutionResult,
    FreshnessState,
    ProtectedResource,
    RuntimeCapability,
    RuntimeCapabilityManifest,
    RuntimeMode,
    SCHEMA_REGISTRY,
)


GWF_ADAPTER_MAPPING_VERSION = "g2e-gwf-p4-v1"
GWF_RUNTIME_ID = "g2e-gwf"
GWF_RUNTIME_VERSION = "0.8.5"
CANONICAL_ARTIFACT_TYPE = "g2e_canonical_object"
GENERIC_WORKUNIT_TYPE = "g2e_execute_proof"
GWF_EVIDENCE_TYPE = "g2e_candidate_evidence"


class GWFAdapterError(RuntimeError):
    pass


class GWFMappingConflictError(GWFAdapterError):
    pass


class UnsupportedGWFMappingVersion(GWFAdapterError):
    pass


@dataclass(frozen=True)
class GWFMappingRef:
    schema_kind: str
    g2e_ref: ExactRef
    gwf_artifact_id: str
    gwf_revision_id: str
    gwf_revision_hash: str


@dataclass(frozen=True)
class GWFCandidateEvidenceSpec:
    source_class: str
    payload: Mapping[str, Any]
    object_id: str | None = None
    subject_refs: tuple[ExactRef, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    resource_refs: tuple[str, ...] = ()
    freshness_state: FreshnessState | None = None


@dataclass(frozen=True)
class GWFExecutionOutcome:
    action_summary: str
    evidence: tuple[GWFCandidateEvidenceSpec, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    resource_identity: str | None = None


@dataclass(frozen=True)
class GWFExecutionReport:
    final_attempt: ExecutionAttemptEnvelope
    execution_result: ExecutionResult
    candidate_evidence: tuple[EvidenceRecord, ...]
    evidence_payloads: Mapping[str, Mapping[str, Any]]
    protected_resources: tuple[ProtectedResource, ...]
    gwf_workunit_id: str
    gwf_run_id: str
    gwf_evidence_ids: tuple[str, ...]
    checkpoint_id: str


@dataclass(frozen=True)
class GWFRecoveryReport:
    final_attempt: ExecutionAttemptEnvelope
    protected_resources: tuple[ProtectedResource, ...]
    checkpoint_id: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _to_z(value: str) -> str:
    if value.endswith("Z"):
        return value
    if value.endswith("+00:00"):
        return value[:-6] + "Z"
    return datetime.fromisoformat(value).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _ref_token(ref: ExactRef) -> str:
    return f"{ref.object_id}@{ref.revision_id}#{ref.content_hash}"


def _revise_attempt(
    attempt: ExecutionAttemptEnvelope,
    state: AttemptState,
    revision_id: str,
    provenance: Provenance,
) -> ExecutionAttemptEnvelope:
    data = attempt.model_dump(mode="python", exclude={"content_hash"})
    data.update({"revision_id": revision_id, "state": state, "provenance": provenance})
    return ExecutionAttemptEnvelope.sealed(**data)


class GWFAdapter:
    """P4 base adapter.

    GWF IDs/states remain runtime mappings. Canonical G2E identity and scientific
    verdict semantics are always reconstructed and verified by G2E itself.
    """

    def __init__(
        self,
        runtime: GovernedWorkflowRuntime,
        project_id: str,
        *,
        mapping_version: str = GWF_ADAPTER_MAPPING_VERSION,
        exact_runtime_revision: str | None = None,
    ):
        if mapping_version != GWF_ADAPTER_MAPPING_VERSION:
            raise UnsupportedGWFMappingVersion(
                f"unsupported GWF mapping version: {mapping_version}"
            )
        if runtime.domain.domain_id != G2E_GWF_DOMAIN_ID:
            raise GWFAdapterError(
                f"incompatible GWF domain: {runtime.domain.domain_id}"
            )
        if not runtime.db.one("SELECT 1 FROM projects WHERE id=?", (project_id,)):
            raise GWFAdapterError(f"unknown GWF project: {project_id}")
        self.runtime = runtime
        self.project_id = project_id
        self.mapping_version = mapping_version
        self.exact_runtime_revision = exact_runtime_revision

    def capability_manifest(
        self,
        *,
        provenance: Provenance,
        qualification_refs: Sequence[str] = (),
    ) -> RuntimeCapabilityManifest:
        caps = (
            RuntimeCapability(
                capability_id=f"mapping_version:{self.mapping_version}",
                available=True,
                qualification_refs=tuple(qualification_refs),
            ),
            RuntimeCapability(
                capability_id="canonical_persistence",
                available=True,
                qualification_refs=tuple(qualification_refs),
            ),
            RuntimeCapability(
                capability_id="gwf_authority",
                available=True,
                qualification_refs=tuple(qualification_refs),
            ),
            RuntimeCapability(
                capability_id="gwf_checkpoint_handoff",
                available=True,
                qualification_refs=tuple(qualification_refs),
            ),
            RuntimeCapability(
                capability_id="generic_execution_facade",
                available=True,
                qualification_refs=tuple(qualification_refs),
            ),
            RuntimeCapability(
                capability_id="protected_resource_fail_closed_mapping",
                available=True,
                qualification_refs=tuple(qualification_refs),
            ),
        )
        return RuntimeCapabilityManifest.sealed(
            object_id="gwf-runtime-capabilities",
            revision_id="r1",
            provenance=provenance,
            runtime_id=GWF_RUNTIME_ID,
            runtime_version=GWF_RUNTIME_VERSION,
            runtime_mode=RuntimeMode.GWF,
            authority_mode="gwf-policy-enforced",
            persistence_backend=getattr(self.runtime.db, "backend_name", "unknown"),
            supported_schema_versions=("1.0",),
            capabilities=caps,
            security_assumptions=(
                "GWF credentials remain outside canonical G2E objects",
                "GWF runtime states are not G2E scientific verdicts",
                f"adapter_mapping_version={self.mapping_version}",
            ),
            exact_runtime_revision=self.exact_runtime_revision,
        )

    def require_capabilities(
        self,
        manifest: RuntimeCapabilityManifest,
        required: Sequence[str],
    ) -> None:
        if (
            manifest.runtime_id != GWF_RUNTIME_ID
            or manifest.runtime_version != GWF_RUNTIME_VERSION
            or manifest.runtime_mode != RuntimeMode.GWF
            or manifest.persistence_backend != getattr(self.runtime.db, "backend_name", "unknown")
        ):
            raise GWFAdapterError("RUNTIME_IDENTITY_MISMATCH:g2e-gwf")
        available = {
            cap.capability_id: cap.available for cap in manifest.capabilities
        }
        version_cap = f"mapping_version:{self.mapping_version}"
        if available.get(version_cap) is not True:
            raise UnsupportedGWFMappingVersion(
                f"mapping capability missing: {version_cap}"
            )
        missing = [name for name in required if available.get(name) is not True]
        if missing:
            raise GWFAdapterError(
                "RUNTIME_CAPABILITY_UNAVAILABLE:" + ",".join(sorted(missing))
            )

    @staticmethod
    def _logical_key(schema_kind: str, object_id: str) -> str:
        identity_hash = canonical_hash(
            {"schema_kind": schema_kind, "object_id": object_id}
        )
        return f"g2e:{schema_kind}:{identity_hash}"

    def _wrapper(self, obj: CanonicalModel) -> dict[str, Any]:
        return {
            "mapping_version": self.mapping_version,
            "schema_kind": obj.schema_kind,
            "g2e_exact_ref": obj.exact_ref().model_dump(mode="json"),
            "canonical_object": obj.model_dump(mode="json"),
        }

    def _parse_wrapper(
        self,
        payload: Mapping[str, Any],
        *,
        expected_kind: str | None = None,
        expected_ref: ExactRef | None = None,
    ) -> CanonicalModel:
        if payload.get("mapping_version") != self.mapping_version:
            raise UnsupportedGWFMappingVersion(
                f"unsupported persisted mapping version: {payload.get('mapping_version')}"
            )
        kind = payload.get("schema_kind")
        if not isinstance(kind, str) or kind not in SCHEMA_REGISTRY:
            raise GWFAdapterError(f"unknown G2E schema kind: {kind!r}")
        if expected_kind is not None and kind != expected_kind:
            raise GWFMappingConflictError(
                f"schema kind mismatch: expected={expected_kind} actual={kind}"
            )
        try:
            stored_ref = ExactRef.model_validate(payload.get("g2e_exact_ref"))
            model = SCHEMA_REGISTRY[kind].parse_authoritative(
                payload.get("canonical_object")
            )
        except Exception as exc:
            raise GWFAdapterError(f"invalid canonical G2E mapping: {exc}") from exc
        if model.exact_ref() != stored_ref:
            raise GWFMappingConflictError(
                "persisted GWF wrapper does not bind the reconstructed G2E exact ref"
            )
        if expected_ref is not None and stored_ref != expected_ref:
            raise GWFMappingConflictError(
                "GWF revision maps to the wrong G2E exact ref"
            )
        return model

    def _artifact_for(self, schema_kind: str, object_id: str):
        key = self._logical_key(schema_kind, object_id)
        return self.runtime.db.one(
            "SELECT * FROM artifacts WHERE project_id=? AND logical_key=?",
            (self.project_id, key),
        )

    def persist_canonical(
        self,
        obj: CanonicalModel,
        *,
        actor_id: str = "SYSTEM",
    ) -> GWFMappingRef:
        if obj.schema_kind not in SCHEMA_REGISTRY:
            raise GWFAdapterError(f"unregistered G2E schema kind: {obj.schema_kind}")
        # Re-verify even when the caller already holds a Pydantic instance.
        authoritative = SCHEMA_REGISTRY[obj.schema_kind].parse_authoritative(
            obj.model_dump(mode="json")
        )
        self.runtime.governance.authorize(
            actor_id,
            "CREATE_REVISION",
            {"project_id": self.project_id, "artifact_type": CANONICAL_ARTIFACT_TYPE},
        )
        artifact = self._artifact_for(obj.schema_kind, obj.object_id)
        if artifact is None:
            artifact_id = self.runtime.knowledge.create_artifact(
                self.project_id,
                CANONICAL_ARTIFACT_TYPE,
                self._logical_key(obj.schema_kind, obj.object_id),
                actor_id,
            )
            artifact = self.runtime.knowledge.get_artifact(artifact_id)
        elif artifact["artifact_type"] != CANONICAL_ARTIFACT_TYPE:
            raise GWFMappingConflictError("logical key is bound to incompatible artifact type")

        for row in self.runtime.db.all(
            "SELECT * FROM revisions WHERE artifact_id=? ORDER BY revision_number",
            (artifact["artifact_id"],),
        ):
            wrapper = parse_json(row["structured_payload"], {})
            existing = self._parse_wrapper(wrapper, expected_kind=obj.schema_kind)
            if existing.revision_id != obj.revision_id:
                continue
            if existing.exact_ref() != authoritative.exact_ref():
                raise GWFMappingConflictError(
                    "same G2E object/revision is already mapped with a different canonical hash"
                )
            return GWFMappingRef(
                schema_kind=obj.schema_kind,
                g2e_ref=authoritative.exact_ref(),
                gwf_artifact_id=artifact["artifact_id"],
                gwf_revision_id=row["revision_id"],
                gwf_revision_hash=row["content_hash"],
            )

        wrapper = self._wrapper(authoritative)
        self.runtime.domain.validate_artifact_payload(CANONICAL_ARTIFACT_TYPE, wrapper)
        current = self.runtime.knowledge.get_artifact(artifact["artifact_id"])
        created = self.runtime.knowledge.create_revision(
            artifact["artifact_id"],
            wrapper,
            actor_id,
            expected_artifact_version=current["version"],
        )
        revision = self.runtime.knowledge.get_revision(created["revision_id"])
        self._parse_wrapper(
            revision["structured_payload"],
            expected_kind=obj.schema_kind,
            expected_ref=authoritative.exact_ref(),
        )
        self.runtime.knowledge.set_validity_system(revision["revision_id"], "VALID")
        return GWFMappingRef(
            schema_kind=obj.schema_kind,
            g2e_ref=authoritative.exact_ref(),
            gwf_artifact_id=artifact["artifact_id"],
            gwf_revision_id=revision["revision_id"],
            gwf_revision_hash=revision["content_hash"],
        )

    def load_exact(self, schema_kind: str, ref: ExactRef) -> CanonicalModel:
        artifact = self._artifact_for(schema_kind, ref.object_id)
        if artifact is None:
            raise GWFAdapterError(
                f"no GWF mapping for {schema_kind}:{ref.object_id}"
            )
        found_revision = False
        for row in self.runtime.db.all(
            "SELECT * FROM revisions WHERE artifact_id=? ORDER BY revision_number",
            (artifact["artifact_id"],),
        ):
            wrapper = parse_json(row["structured_payload"], {})
            model = self._parse_wrapper(wrapper, expected_kind=schema_kind)
            if model.revision_id != ref.revision_id:
                continue
            found_revision = True
            if model.exact_ref() != ref:
                raise GWFMappingConflictError(
                    "requested G2E revision exists with a different canonical hash"
                )
            return model
        if found_revision:
            raise GWFMappingConflictError("G2E exact-ref mismatch")
        raise GWFAdapterError(
            f"no mapped G2E revision: {schema_kind}:{ref.object_id}:{ref.revision_id}"
        )

    def mapping_for(self, schema_kind: str, ref: ExactRef) -> GWFMappingRef:
        artifact = self._artifact_for(schema_kind, ref.object_id)
        if artifact is None:
            raise GWFAdapterError("G2E object is not mapped")
        for row in self.runtime.db.all(
            "SELECT * FROM revisions WHERE artifact_id=? ORDER BY revision_number",
            (artifact["artifact_id"],),
        ):
            wrapper = parse_json(row["structured_payload"], {})
            model = self._parse_wrapper(wrapper, expected_kind=schema_kind)
            if model.revision_id == ref.revision_id:
                if model.exact_ref() != ref:
                    raise GWFMappingConflictError("G2E exact-ref mismatch")
                return GWFMappingRef(
                    schema_kind=schema_kind,
                    g2e_ref=ref,
                    gwf_artifact_id=artifact["artifact_id"],
                    gwf_revision_id=row["revision_id"],
                    gwf_revision_hash=row["content_hash"],
                )
        raise GWFAdapterError("G2E revision is not mapped")

    def load_mapping(self, mapping: GWFMappingRef) -> CanonicalModel:
        row = self.runtime.db.one(
            "SELECT * FROM revisions WHERE revision_id=? AND artifact_id=?",
            (mapping.gwf_revision_id, mapping.gwf_artifact_id),
        )
        if not row:
            raise GWFAdapterError("GWF mapping revision not found")
        if row["content_hash"] != mapping.gwf_revision_hash:
            raise GWFMappingConflictError("GWF revision hash changed")
        wrapper = parse_json(row["structured_payload"], {})
        return self._parse_wrapper(
            wrapper,
            expected_kind=mapping.schema_kind,
            expected_ref=mapping.g2e_ref,
        )

    def load_evidence_payload(self, evidence: EvidenceRecord) -> Mapping[str, Any]:
        token = _ref_token(evidence.exact_ref())
        for row in self.runtime.db.all(
            "SELECT * FROM evidence WHERE project_id=? AND evidence_type=? ORDER BY created_at",
            (self.project_id, GWF_EVIDENCE_TYPE),
        ):
            if token not in parse_json(row["subject_refs"], []):
                continue
            payload = parse_json(row["structured_payload"], {})
            if evidence.payload_digest is None:
                raise GWFAdapterError("mapped evidence has no payload digest")
            if canonical_hash(payload) != evidence.payload_digest:
                raise GWFMappingConflictError("GWF evidence payload digest mismatch")
            return payload
        raise GWFAdapterError("GWF evidence payload not found")

    def _checkpoint(
        self,
        scope_id: str,
        refs: Sequence[ExactRef],
    ) -> str:
        metadata = {
            "g2e_mapping_version": self.mapping_version,
            "g2e_refs": [ref.model_dump(mode="json") for ref in refs],
        }
        return self.runtime.execution.create_checkpoint(
            self.project_id,
            scope_id,
            runtime_metadata=metadata,
        )

    def verify_checkpoint(
        self,
        checkpoint_id: str,
        refs: Sequence[ExactRef],
    ) -> None:
        state = self.runtime.execution.reconcile_checkpoint(checkpoint_id)
        metadata = state.get("runtime_metadata", {})
        if metadata.get("g2e_mapping_version") != self.mapping_version:
            raise UnsupportedGWFMappingVersion("checkpoint mapping version mismatch")
        expected = sorted(_ref_token(ref) for ref in refs)
        actual = sorted(
            _ref_token(ExactRef.model_validate(item))
            for item in metadata.get("g2e_refs", [])
        )
        if actual != expected:
            raise GWFMappingConflictError("checkpoint G2E exact-ref set mismatch")

    def execute(
        self,
        initial_attempt: ExecutionAttemptEnvelope,
        runner: Callable[[], GWFExecutionOutcome],
        *,
        provenance: Provenance,
        actor_id: str = "SYSTEM",
        protected_resources: Sequence[ProtectedResource] = (),
    ) -> GWFExecutionReport:
        if initial_attempt.state != AttemptState.CREATED:
            raise GWFAdapterError("GWF execution requires CREATED attempt")

        # The frozen semantic dependencies must already be mapped exactly.
        self.load_exact("proof_obligation", initial_attempt.proof_ref)
        self.load_exact("proof_retry_policy", initial_attempt.retry_policy_ref)

        supplied = {r.exact_ref() for r in protected_resources}
        expected = set(initial_attempt.protected_resource_refs)
        if supplied != expected:
            raise GWFMappingConflictError(
                "protected-resource set does not match frozen ExecutionAttempt"
            )

        self.persist_canonical(initial_attempt, actor_id=actor_id)
        preflight = _revise_attempt(
            initial_attempt,
            AttemptState.PREFLIGHT,
            initial_attempt.revision_id + ".preflight",
            provenance,
        )
        self.persist_canonical(preflight, actor_id=actor_id)
        locked = _revise_attempt(
            preflight,
            AttemptState.LOCKED,
            preflight.revision_id + ".locked",
            provenance,
        )
        locked_mapping = self.persist_canonical(locked, actor_id=actor_id)

        reserved_resources: list[ProtectedResource] = []
        for index, resource in enumerate(protected_resources, start=1):
            self.persist_canonical(resource, actor_id=actor_id)
            reserved = transition_protected_resource(
                resource,
                "RESERVE",
                revision_id=f"reserved-{locked.attempt_id}-{index}",
                provenance=provenance,
            )
            self.persist_canonical(reserved, actor_id=actor_id)
            reserved_resources.append(reserved)

        workunit_id = self.runtime.execution.create_workunit(
            self.project_id,
            GENERIC_WORKUNIT_TYPE,
            [locked_mapping.gwf_revision_id],
            actor_id,
        )
        readiness = self.runtime.execution.prepare_for_execution(workunit_id)
        if readiness["status"] != "READY":
            raise GWFAdapterError(
                "GWF workunit blocked:" + ",".join(readiness["blockers"])
            )
        workunit = self.runtime.db.one(
            "SELECT * FROM workunits WHERE workunit_id=?",
            (workunit_id,),
        )
        run_info = self.runtime.execution.start_run(
            workunit_id,
            actor_id,
            int(workunit["version"]),
            f"g2e:{locked.attempt_id}:{locked.content_hash}",
            f"g2e:{locked.attempt_id}",
        )
        run_id = run_info["run_id"]

        running = _revise_attempt(
            locked,
            AttemptState.RUNNING,
            locked.revision_id + ".running",
            provenance,
        )
        self.persist_canonical(running, actor_id=actor_id)
        gwf_run = self.runtime.db.one("SELECT * FROM runs WHERE run_id=?", (run_id,))
        started_at = _to_z(gwf_run["started_at"])

        outcome: GWFExecutionOutcome | None = None
        technical_error_class: str | None = None
        technical_error_reason: str | None = None
        terminal_state = AttemptState.COMPLETED
        try:
            outcome = runner()
            if not isinstance(outcome, GWFExecutionOutcome):
                raise TypeError("GWF runner must return GWFExecutionOutcome")
        except Exception as exc:
            terminal_state = AttemptState.EXECUTOR_FAILED
            technical_error_class = type(exc).__name__
            technical_error_reason = str(exc)

        exposed_resources: list[ProtectedResource] = []
        for index, resource in enumerate(reserved_resources, start=1):
            exposed = transition_protected_resource(
                resource,
                "EXPOSE",
                revision_id=f"exposed-{running.attempt_id}-{index}",
                provenance=provenance,
            )
            self.persist_canonical(exposed, actor_id=actor_id)
            exposed_resources.append(exposed)

        if terminal_state == AttemptState.COMPLETED:
            self.runtime.execution.finish_run(run_id, "COMPLETED", {})
        else:
            self.runtime.execution.finish_run(
                run_id,
                "FAILED",
                {
                    "failure_class": technical_error_class or "EXECUTOR_FAILED",
                    "reason": technical_error_reason or "executor failed",
                },
            )
        gwf_run = self.runtime.db.one("SELECT * FROM runs WHERE run_id=?", (run_id,))
        ended_at = _to_z(gwf_run["finished_at"])

        final_attempt = _revise_attempt(
            running,
            terminal_state,
            running.revision_id + "." + terminal_state.value.lower(),
            provenance,
        )
        self.persist_canonical(final_attempt, actor_id=actor_id)

        candidate_records: list[EvidenceRecord] = []
        payloads: dict[str, Mapping[str, Any]] = {}
        gwf_evidence_ids: list[str] = []
        artifact_refs: tuple[str, ...] = ()
        resource_identity: str | None = None
        action_summary = "GWF execution failed"

        if outcome is not None:
            artifact_refs = outcome.artifact_refs
            resource_identity = outcome.resource_identity
            action_summary = outcome.action_summary
            for index, spec in enumerate(outcome.evidence, start=1):
                object_id = spec.object_id or f"evidence-{final_attempt.attempt_id}-{index}"
                freshness = spec.freshness_state
                if freshness is None and exposed_resources:
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
                evidence_id = self.runtime.execution.add_evidence(
                    self.project_id,
                    GWF_EVIDENCE_TYPE,
                    actor_id,
                    [_ref_token(record.exact_ref())],
                    payload,
                    trust_class="AUTHORITATIVE",
                    producer_run_id=run_id,
                )
                self.persist_canonical(record, actor_id=actor_id)
                candidate_records.append(record)
                payloads[record.object_id] = payload
                gwf_evidence_ids.append(evidence_id)

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
            agent_app=initial_attempt.agent_app,
            provider_ref=initial_attempt.provider_ref,
            model_ref=initial_attempt.model_ref,
            harness_ref=initial_attempt.harness_ref,
            transport_ref=initial_attempt.transport_ref,
            technical_error_class=technical_error_class,
            technical_error_reason=technical_error_reason,
            redaction_metadata={"mode": "gwf-base-adapter"},
        )
        self.persist_canonical(result, actor_id=actor_id)

        checkpoint_refs = [
            final_attempt.exact_ref(),
            result.exact_ref(),
            *(r.exact_ref() for r in candidate_records),
            *(r.exact_ref() for r in exposed_resources),
        ]
        checkpoint_id = self._checkpoint(final_attempt.attempt_id, checkpoint_refs)
        self.verify_checkpoint(checkpoint_id, checkpoint_refs)

        return GWFExecutionReport(
            final_attempt=final_attempt,
            execution_result=result,
            candidate_evidence=tuple(candidate_records),
            evidence_payloads=payloads,
            protected_resources=tuple(exposed_resources),
            gwf_workunit_id=workunit_id,
            gwf_run_id=run_id,
            gwf_evidence_ids=tuple(gwf_evidence_ids),
            checkpoint_id=checkpoint_id,
        )

    def recover_uncertain_execution(
        self,
        attempt: ExecutionAttemptEnvelope,
        protected_resources: Sequence[ProtectedResource],
        *,
        provenance: Provenance,
        actor_id: str = "SYSTEM",
        gwf_run_id: str | None = None,
    ) -> GWFRecoveryReport:
        if attempt.state not in {AttemptState.LOCKED, AttemptState.RUNNING}:
            raise GWFAdapterError(
                "uncertain recovery requires LOCKED or RUNNING attempt"
            )

        if gwf_run_id is not None:
            row = self.runtime.db.one("SELECT * FROM runs WHERE run_id=?", (gwf_run_id,))
            if row and row["runtime_status"] == "RUNNING":
                self.runtime.execution.finish_run(
                    gwf_run_id,
                    "ABANDONED",
                    {"reason": "G2E_UNCERTAIN_RECOVERY"},
                )

        exposed: list[ProtectedResource] = []
        for index, resource in enumerate(protected_resources, start=1):
            recovered = transition_protected_resource(
                resource,
                "RECOVERY_UNCERTAIN_ACCESS",
                revision_id=f"recovery-exposed-{attempt.attempt_id}-{index}",
                provenance=provenance,
            )
            self.persist_canonical(recovered, actor_id=actor_id)
            exposed.append(recovered)

        final_attempt = _revise_attempt(
            attempt,
            AttemptState.PREEMPTED,
            attempt.revision_id + ".preempted-recovery",
            provenance,
        )
        self.persist_canonical(final_attempt, actor_id=actor_id)
        refs = [
            final_attempt.exact_ref(),
            *(r.exact_ref() for r in exposed),
        ]
        checkpoint_id = self._checkpoint(final_attempt.attempt_id, refs)
        self.verify_checkpoint(checkpoint_id, refs)
        return GWFRecoveryReport(
            final_attempt=final_attempt,
            protected_resources=tuple(exposed),
            checkpoint_id=checkpoint_id,
        )
