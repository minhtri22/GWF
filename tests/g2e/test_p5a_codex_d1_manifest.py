from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from g2e import AgentCapabilityManifest, AgentProfileAvailability


ROOT = Path(__file__).resolve().parents[2]
MATERIALIZER = ROOT / "scripts" / "g2e" / "p5a_materialize_codex_d1_manifest.py"
EVIDENCE = ROOT / "g2e" / "docs" / "P5A_CODEX_D1_EVIDENCE.json"
SPEC = ROOT / "g2e" / "docs" / "P5A_CODEX_D1_MANIFEST_QUALIFICATION.md"


def _load_materializer():
    spec = importlib.util.spec_from_file_location("p5a_manifest_materializer", MATERIALIZER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_manifest_spec_freezes_d1_only_scope():
    text = SPEC.read_text(encoding="utf-8")
    assert "PASS / structural surface only" in text
    assert "**D2:** NOT AUTHORIZED" in text
    assert "Codex runtime adapter:** NOT AUTHORIZED" in text
    assert "repository_read" in text
    assert "available=false" in text


def test_materializer_binds_exact_d1_evidence():
    module = _load_materializer()
    evidence = module.load_d1_evidence(EVIDENCE)
    assert evidence["status"] == "PASS"
    assert evidence["original_discovery"]["sha256"] == module.DISCOVERY_SHA256
    assert evidence["repaired_adjudication"]["file_sha256"] == module.ADJUDICATION_SHA256
    assert evidence["harness"]["executable_sha256"] == module.EXECUTABLE_SHA256


def test_manifest_is_canonical_and_exactly_reparseable():
    module = _load_materializer()
    evidence = module.load_d1_evidence(EVIDENCE)
    manifest = module.build_manifest(evidence)
    reparsed = AgentCapabilityManifest.parse_authoritative(manifest.model_dump(mode="json"))
    assert reparsed == manifest
    assert manifest.content_hash == manifest.computed_content_hash()


def test_only_structural_capabilities_are_available():
    module = _load_materializer()
    manifest = module.build_manifest(module.load_d1_evidence(EVIDENCE))
    actual = {c.capability_id: c for c in manifest.capabilities}
    assert set(actual) == set(module.STRUCTURAL_CAPABILITIES) | set(module.FUNCTIONAL_UNQUALIFIED)
    for capability_id in module.STRUCTURAL_CAPABILITIES:
        cap = actual[capability_id]
        assert cap.available is True
        assert cap.qualification_refs
        assert "D1 structural surface only" in cap.limitations[0]
    for capability_id in module.FUNCTIONAL_UNQUALIFIED:
        cap = actual[capability_id]
        assert cap.available is False
        assert cap.qualification_refs == ()
        assert "D2" in cap.limitations[0]


def test_manifest_identity_and_global_flags_are_conservative():
    module = _load_materializer()
    manifest = module.build_manifest(module.load_d1_evidence(EVIDENCE))
    assert manifest.agent_app == "codex"
    assert manifest.profile_version == "g2e-p5a-d1-v1"
    assert manifest.harness_ref == f"sha256:{module.EXECUTABLE_SHA256}"
    assert manifest.exact_harness_revision == module.EXECUTABLE_SHA256
    assert manifest.provider_ref is None
    assert manifest.model_ref is None
    assert manifest.transport_ref == "app-server-stdio"
    assert manifest.availability == AgentProfileAvailability.AVAILABLE
    assert manifest.max_authority_scope == ()
    assert manifest.credential_ref_classes == ()
    assert manifest.external_session_attribution is True
    assert manifest.interruption_supported is False
    assert manifest.artifact_extraction_supported is False
    assert manifest.structured_output_supported is False
    assert manifest.status_normalization_supported is False


def test_materialization_is_deterministic(tmp_path: Path):
    module = _load_materializer()
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    m1 = module.materialize(EVIDENCE, first)
    m2 = module.materialize(EVIDENCE, second)
    assert m1 == m2
    assert first.read_bytes() == second.read_bytes()


def test_materializer_has_no_runtime_execution_path():
    source = MATERIALIZER.read_text(encoding="utf-8")
    forbidden = (
        "subprocess",
        "thread/start",
        "turn/start",
        "ExecutionAttemptEnvelope",
        "AgentBinding",
        "requests.",
        "httpx.",
    )
    for token in forbidden:
        assert token not in source
