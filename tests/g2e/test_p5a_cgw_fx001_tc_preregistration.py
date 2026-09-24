from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "g2e" / "config" / "P5A_CGW_FX001_TC_EXECUTION_CONFIG.json"
LOCK = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_TC_PREREGISTRATION_LOCK.json"
PREREG = ROOT / "g2e" / "docs" / "P5A_CGW_FX001_TC_PREREGISTRATION.md"


def canonical_sha256(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def test_transport_corrected_config_is_exact_and_dispatch_withheld():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    lock = json.loads(LOCK.read_text(encoding="utf-8"))

    assert cfg["study_id"] == "p5a-cgw-v4-p5-fx-001-transport-corrected-qualification"
    assert cfg["attempt_id"] == "p5a-cgw-v4-p5-fx-001-tc-attempt-001"
    assert cfg["route"]["model_slug"] == "chatgpt-web/high"
    assert cfg["route"]["bridge_mode"] == "full"
    assert cfg["route"]["connector"] == "Codex Native2"
    assert cfg["transport_contract"]["scientific_absolute_turn_deadline_ms"] is None
    assert cfg["authorization"]["live_dispatch_authorized"] is False
    assert lock["authorization"]["live_dispatch_authorized"] is False
    assert lock["status"] == "PREREGISTERED_DISPATCH_WITHHELD"


def test_preregistration_hash_is_frozen():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    assert canonical_sha256(cfg) == "6b88011e0bc6ba0164a0e6f4230bb1fb8be6037d7513f348c15d39ea726816f7"
    assert lock["execution_config_canonical_sha256"] == canonical_sha256(cfg)


def test_new_study_is_not_a_retry_or_rearm():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    lock = json.loads(LOCK.read_text(encoding="utf-8"))

    assert cfg["provenance"]["not_a_retry"] is True
    assert cfg["provenance"]["spent_predecessor_attempt"] == "p5a-cgw-v4-p5-fx-001-attempt-001"
    assert lock["predecessor"]["rerun_forbidden"] is True
    assert lock["predecessor"]["rearm_forbidden"] is True
    assert cfg["consumption"]["retry_budget"] == 0


def test_task_and_route_are_unchanged_except_transport_harness_contract():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert cfg["task"]["input_sha256"] == "a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6"
    assert cfg["task"]["task_sha256"] == "4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e"
    assert cfg["task"]["expected_result_sha256"] == "6dd3ebce33677409bec596309e061cc421bfa38b3160c5b577ffe5f7fbc9980d"
    assert cfg["task"]["network_allowed"] is False
    assert cfg["task"]["allowed_mutation"] == "result.json only"


def test_signal_classes_are_not_conflated():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    classes = cfg["signal_classes"]
    assert classes["route_invalidity"] == "evidence_integrity_failure"
    assert classes["unexpected_server_request"] == "protocol_failure"
    assert classes["prohibited_tool_or_network"] == "scope_violation"
    assert "positive evidence" in classes["authority_violation"]


def test_preregistration_firewall_is_zero_science():
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    assert all(v is False for v in lock["firewall"].values())
    text = PREREG.read_text(encoding="utf-8")
    assert "live dispatch: **withheld**" in text
