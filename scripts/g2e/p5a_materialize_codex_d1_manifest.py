from __future__ import annotations

import argparse
import json
from pathlib import Path

from g2e import AgentCapability, AgentCapabilityManifest, AgentProfileAvailability, Provenance


DISCOVERY_SHA256 = "ba098a56be39e996488e5a543af8c373199f8b4cc66f922be6d7bc6386c6e860"
ADJUDICATION_SHA256 = "04035432c5f290dfd7bbcc91feba8865dc86bfae11686a4e44da2f56cb4ac578"
EXECUTABLE_SHA256 = "a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8"
SCHEMA_INVENTORY_DIGEST = "4da66f2fac241c53ec857bf1a5f0f9586a445e39c4b0c4e7b4bdb0b103aa8376"
D1_EVIDENCE_REF = "git:1b499c1005000e576cbd8ac4e869f75b5f3a3f02:g2e/docs/P5A_CODEX_D1_EVIDENCE.json"

STRUCTURAL_CAPABILITIES = (
    "app_server_launch",
    "version_matched_schema_generation",
    "jsonrpc_initialize",
    "thread_lifecycle_surface",
    "turn_stream_surface",
    "external_session_attribution_surface",
    "approval_surface",
    "mcp_surface",
    "skills_surface",
    "thread_fork_surface",
    "turn_steer_surface",
    "command_exec_surface",
)

FUNCTIONAL_UNQUALIFIED = (
    "repository_read",
    "repository_write",
    "shell_execution",
    "test_execution",
    "network_access",
    "side_effect_approval_execution",
    "active_task_cancellation_interruption",
    "completed_task_artifact_extraction",
    "model_task_correctness",
)


def load_d1_evidence(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "G2E-P5A-CODEX-D1-EVIDENCE-v1":
        raise ValueError("unexpected D1 evidence schema")
    if data.get("status") != "PASS":
        raise ValueError("D1 evidence is not PASS")
    original = data.get("original_discovery", {})
    repaired = data.get("repaired_adjudication", {})
    harness = data.get("harness", {})
    if original.get("sha256") != DISCOVERY_SHA256:
        raise ValueError("discovery SHA-256 mismatch")
    if original.get("schema_inventory_digest") != SCHEMA_INVENTORY_DIGEST:
        raise ValueError("schema inventory digest mismatch")
    if repaired.get("file_sha256") != ADJUDICATION_SHA256:
        raise ValueError("repaired adjudication SHA-256 mismatch")
    if repaired.get("verdict") != "PASS" or repaired.get("reason_codes") != []:
        raise ValueError("repaired adjudication is not clean PASS")
    if repaired.get("codex_profile_available_for_d1_surface") is not True:
        raise ValueError("D1 structural profile surface not available")
    if repaired.get("d2_authorized") is not False:
        raise ValueError("D2 must remain unauthorized")
    if repaired.get("runtime_adapter_authorized") is not False:
        raise ValueError("runtime adapter must remain unauthorized")
    if harness.get("executable_sha256") != EXECUTABLE_SHA256:
        raise ValueError("executable SHA-256 mismatch")
    return data


def build_manifest(evidence: dict) -> AgentCapabilityManifest:
    refs = (
        f"sha256:{DISCOVERY_SHA256}",
        f"sha256:{ADJUDICATION_SHA256}",
        f"schema-inventory-sha256:{SCHEMA_INVENTORY_DIGEST}",
        D1_EVIDENCE_REF,
    )

    capabilities = [
        AgentCapability(
            capability_id=capability_id,
            available=True,
            qualification_refs=refs,
            limitations=("D1 structural surface only; functional execution not demonstrated",),
        )
        for capability_id in STRUCTURAL_CAPABILITIES
    ]
    capabilities.extend(
        AgentCapability(
            capability_id=capability_id,
            available=False,
            qualification_refs=(),
            limitations=("D2 or separately preregistered functional probe required",),
        )
        for capability_id in FUNCTIONAL_UNQUALIFIED
    )

    return AgentCapabilityManifest.sealed(
        object_id="agent-capability-manifest-codex-d1",
        revision_id="a337b7433ebb351c-d1-v1",
        provenance=Provenance(
            created_by="g2e-p5a-d1-materializer",
            created_at="2026-09-21T12:05:44.250506Z",
            source_refs=refs,
            derivation="Materialized solely from qualified P5A D1 structural evidence",
        ),
        agent_app="codex",
        profile_version="g2e-p5a-d1-v1",
        harness_ref=f"sha256:{EXECUTABLE_SHA256}",
        exact_harness_revision=EXECUTABLE_SHA256,
        provider_ref=None,
        model_ref=None,
        transport_ref="app-server-stdio",
        availability=AgentProfileAvailability.AVAILABLE,
        capabilities=tuple(capabilities),
        execution_constraints=(
            "d1_structural_only",
            "no_functional_task_executed",
            "d2_required_for_task_execution",
            "exact_executable_sha256_required",
        ),
        max_authority_scope=(),
        credential_ref_classes=(),
        external_session_attribution=True,
        interruption_supported=False,
        artifact_extraction_supported=False,
        structured_output_supported=False,
        status_normalization_supported=False,
        discovery_evidence_refs=refs,
        limitations=(
            "availability applies only to D1 structural App Server surface",
            "reported CLI version string is codex-cli 0.0.0 and is not used as exact harness identity",
            "optional protocol surfaces are schema-presence observations only",
            "functional task execution remains unqualified until D2",
        ),
    )


def materialize(evidence_path: Path, output_path: Path) -> AgentCapabilityManifest:
    evidence = load_d1_evidence(evidence_path)
    manifest = build_manifest(evidence)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Materialize qualified Codex D1 AgentCapabilityManifest")
    parser.add_argument(
        "--evidence",
        default="g2e/docs/P5A_CODEX_D1_EVIDENCE.json",
    )
    parser.add_argument(
        "--output",
        default="P5A_CODEX_AGENT_CAPABILITY_MANIFEST.json",
    )
    args = parser.parse_args()
    manifest = materialize(Path(args.evidence), Path(args.output))
    print(json.dumps({
        "object_id": manifest.object_id,
        "revision_id": manifest.revision_id,
        "content_hash": manifest.content_hash,
        "harness_ref": manifest.harness_ref,
        "output": str(Path(args.output).resolve()),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
