from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "scripts" / "g2e" / "p5a_cgw_v4_source_contract_qualification.py"
FIXTURE = ROOT / "tests" / "g2e" / "fixtures" / "P5A_CGW_LOCAL_ZERO_MODEL_ADMISSION_V4_EXISTING.json"


def load():
    spec = importlib.util.spec_from_file_location("p5a_cgw_v4", MODULE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def source_pass_fixture(m):
    return {
        "schema": "G2E-P5A-CGW-V4-SOURCE-CONTRACT-QUALIFICATION-v1",
        "status": "V4_SOURCE_CONTRACT_PASS",
        "source_commit": m.V4_SOURCE_COMMIT,
        "version": m.V4_VERSION,
    }


def test_existing_fixture_is_exact_original_evidence():
    m = load()
    assert m.sha256_bytes(FIXTURE.read_bytes()) == m.EXISTING_Q0B_FILE_SHA256
    report = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert report["evidence_sha256"] == m.EXISTING_Q0B_INTERNAL_SHA256
    unsigned = dict(report)
    unsigned.pop("evidence_sha256")
    assert m.canonical_sha256(unsigned) == m.EXISTING_Q0B_INTERNAL_SHA256


def test_readjudication_passes_only_after_v4_source_pass():
    m = load()
    result = m.readjudicate_existing_q0b(FIXTURE, source_pass_fixture(m))
    assert result["status"] == "Q0B_PASS_UNDER_CORRECTED_V4_TARGET"
    assert result["model_turn_executed"] is False
    assert result["runtime_mutated"] is False
    assert result["scientific_attempt_created"] is False
    assert result["scientific_attempt_consumed"] is False
    assert result["functional_attempt_authorized"] is False
    assert result["comparative_ab_authorized"] is False
    assert "NO_REPRODUCIBLE_BUILD_EQUIVALENCE_CLAIM" in result["provenance_strength"]


def test_v5_only_projected_fields_are_explicitly_ignored():
    m = load()
    result = m.readjudicate_existing_q0b(FIXTURE, source_pass_fixture(m))
    assert result["ignored_old_projection_fields_not_source_backed_in_v4"] == [
        "bridge_config.automatic_connector",
        "bridge_config.manual_connector",
        "bridge_config.browser_interaction_mode",
    ]


def test_readjudication_rejects_source_not_qualified():
    m = load()
    with pytest.raises(m.QualificationError, match="V4_SOURCE_NOT_QUALIFIED"):
        m.readjudicate_existing_q0b(FIXTURE, {"status": "FAIL"})


def test_any_evidence_byte_mutation_fails_closed(tmp_path):
    m = load()
    raw = bytearray(FIXTURE.read_bytes())
    raw[-2] = 32
    candidate = tmp_path / "mutated.json"
    candidate.write_bytes(bytes(raw))
    with pytest.raises(m.QualificationError, match="Q0B_FILE_SHA256_MISMATCH"):
        m.readjudicate_existing_q0b(candidate, source_pass_fixture(m))


def test_constants_freeze_v4_not_v5():
    m = load()
    assert m.V4_VERSION == "4.0.7"
    assert m.V4_SOURCE_COMMIT == "b59d7dc51b84fb1f465ff1d00f5207f3b2b4a494"
    source = MODULE.read_text(encoding="utf-8")
    assert "V4_SOURCE_CONTRACT_PASS" in source
    assert 'V4_VERSION = "4.0.7"' in source
