from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "scripts" / "g2e" / "p5a_codex_observability.py"
SPEC = ROOT / "g2e" / "docs" / "P5A_CODEX_OBSERVABILITY_QUALIFICATION_SPEC.md"
AMENDMENT = ROOT / "g2e" / "docs" / "P5A_CODEX_OBSERVABILITY_SCOPE_AMENDMENT.md"


def _load():
    spec = importlib.util.spec_from_file_location("p5a_codex_observability", MODULE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _raw(message: dict) -> str:
    return json.dumps(message, separators=(",", ":"), sort_keys=True)


def test_error_notification_preserves_required_mechanism_fields():
    m = _load()
    msg = {
        "method": "error",
        "params": {
            "threadId": "thread-1",
            "turnId": "turn-1",
            "willRetry": False,
            "error": {
                "message": "provider request failed",
                "codexErrorInfo": "rateLimitExceeded",
                "additionalDetails": "request id req-123",
                "misalignment": None,
            },
        },
    }
    raw = _raw(msg)
    rec = m.project_protocol_message(raw, 123.5)
    ev = rec["terminalErrorEvidence"]

    assert rec["method"] == "error"
    assert rec["length"] == len(raw)
    assert rec["rawSha256"] == m.sha256_bytes(raw.encode())
    assert ev["source"] == "errorNotification"
    assert ev["threadId"] == "thread-1"
    assert ev["turnId"] == "turn-1"
    assert ev["willRetry"] is False
    assert ev["error"]["message"]["text"] == "provider request failed"
    assert ev["error"]["codexErrorInfo"] == "rateLimitExceeded"
    assert ev["error"]["additionalDetails"]["text"] == "request id req-123"


def test_structured_codex_error_info_preserves_variant_and_http_status():
    m = _load()
    msg = {
        "method": "error",
        "params": {
            "threadId": "t",
            "turnId": "u",
            "willRetry": True,
            "error": {
                "message": "stream disconnected",
                "codexErrorInfo": {
                    "responseStreamDisconnected": {"httpStatusCode": 503}
                },
                "additionalDetails": None,
            },
        },
    }
    rec = m.project_protocol_message(_raw(msg))
    info = rec["terminalErrorEvidence"]["error"]["codexErrorInfo"]
    assert info == {"responseStreamDisconnected": {"httpStatusCode": 503}}
    assert rec["terminalErrorEvidence"]["willRetry"] is True


def test_secret_and_home_path_redaction_preserves_raw_hash_and_length(monkeypatch):
    m = _load()
    monkeypatch.setenv("USERPROFILE", r"C:\Users\Alice")
    message = (
        r"failed at C:\Users\Alice\project "
        "Authorization: Bearer abcdefghijklmnop "
        "api_key=TOPSECRET123456"
    )
    details = "token=SECRET_TOKEN_VALUE sk-proj-abcdef1234567890"
    msg = {
        "method": "error",
        "params": {
            "threadId": "t",
            "turnId": "u",
            "willRetry": False,
            "error": {
                "message": message,
                "codexErrorInfo": "unauthorized",
                "additionalDetails": details,
            },
        },
    }
    rec = m.project_protocol_message(_raw(msg))
    error = rec["terminalErrorEvidence"]["error"]
    rendered = json.dumps(rec, sort_keys=True)

    assert "Alice" not in error["message"]["text"]
    assert "TOPSECRET123456" not in rendered
    assert "SECRET_TOKEN_VALUE" not in rendered
    assert "sk-proj-abcdef1234567890" not in rendered
    assert "<USER_HOME>" in error["message"]["text"]
    assert error["message"]["redactionApplied"] is True
    assert error["additionalDetails"]["redactionApplied"] is True
    assert error["message"]["rawSha256"] == m.sha256_bytes(message.encode())
    assert error["message"]["rawLength"] == len(message)
    assert error["additionalDetails"]["rawSha256"] == m.sha256_bytes(details.encode())


def test_secret_bearing_structured_keys_are_redacted():
    m = _load()
    msg = {
        "method": "error",
        "params": {
            "threadId": "t",
            "turnId": "u",
            "willRetry": False,
            "error": {
                "message": "bad request",
                "codexErrorInfo": {
                    "other": {
                        "httpStatusCode": 400,
                        "access_token": "DO_NOT_PERSIST",
                    }
                },
                "additionalDetails": None,
            },
        },
    }
    rec = m.project_protocol_message(_raw(msg))
    rendered = json.dumps(rec, sort_keys=True)
    assert "DO_NOT_PERSIST" not in rendered
    assert "<REDACTED_SECRET>" in rendered
    assert "httpStatusCode" in rendered


def test_failed_turn_completed_preserves_turn_error():
    m = _load()
    msg = {
        "method": "turn/completed",
        "params": {
            "threadId": "thread-2",
            "turn": {
                "id": "turn-2",
                "items": [],
                "status": "failed",
                "error": {
                    "message": "sandbox denied",
                    "codexErrorInfo": "sandboxError",
                    "additionalDetails": "write denied",
                    "misalignment": None,
                },
            },
        },
    }
    rec = m.project_protocol_message(_raw(msg))
    ev = rec["terminalErrorEvidence"]
    assert ev["source"] == "turnCompleted"
    assert ev["threadId"] == "thread-2"
    assert ev["turnId"] == "turn-2"
    assert ev["status"] == "failed"
    assert ev["error"]["message"]["text"] == "sandbox denied"
    assert ev["error"]["codexErrorInfo"] == "sandboxError"
    assert ev["error"]["additionalDetails"]["text"] == "write denied"


def test_completed_turn_with_null_error_is_explicitly_preserved():
    m = _load()
    msg = {
        "method": "turn/completed",
        "params": {
            "threadId": "thread-3",
            "turn": {
                "id": "turn-3",
                "items": [],
                "status": "completed",
                "error": None,
            },
        },
    }
    rec = m.project_protocol_message(_raw(msg))
    ev = rec["terminalErrorEvidence"]
    assert ev["status"] == "completed"
    assert ev["error"] is None


def test_misalignment_preserves_classification_without_steer_text():
    m = _load()
    msg = {
        "method": "error",
        "params": {
            "threadId": "t",
            "turnId": "u",
            "willRetry": False,
            "error": {
                "message": "Chat paused",
                "codexErrorInfo": "misalignmentPolicyViolation",
                "additionalDetails": None,
                "misalignment": {
                    "errorType": "policy",
                    "detailedExplanation": "policy explanation",
                    "steer": {"message": "sensitive continuation text"},
                },
            },
        },
    }
    rec = m.project_protocol_message(_raw(msg))
    mis = rec["terminalErrorEvidence"]["error"]["misalignment"]
    rendered = json.dumps(rec, sort_keys=True)
    assert mis["errorType"] == "policy"
    assert mis["detailedExplanation"]["text"] == "policy explanation"
    assert mis["steerPresent"] is True
    assert "sensitive continuation text" not in rendered


def test_unrelated_protocol_message_remains_payload_minimal():
    m = _load()
    msg = {
        "method": "item/completed",
        "params": {
            "threadId": "thread",
            "item": {"id": "x", "text": "DO NOT PERSIST THIS PAYLOAD"},
        },
    }
    rec = m.project_protocol_message(_raw(msg))
    assert rec["method"] == "item/completed"
    assert "terminalErrorEvidence" not in rec
    assert "params" not in rec
    assert "DO NOT PERSIST THIS PAYLOAD" not in json.dumps(rec)


def test_projection_is_deterministic_for_identical_input():
    m = _load()
    raw = _raw(
        {
            "method": "error",
            "params": {
                "threadId": "t",
                "turnId": "u",
                "willRetry": False,
                "error": {
                    "message": "fixed",
                    "codexErrorInfo": "other",
                    "additionalDetails": "fixed details",
                },
            },
        }
    )
    assert m.project_protocol_message(raw, 1.0) == m.project_protocol_message(raw, 1.0)


def test_schema_contract_accepts_required_exact_shape():
    m = _load()
    turn_error = {
        "properties": {
            "message": {"type": "string"},
            "codexErrorInfo": {},
            "additionalDetails": {},
            "misalignment": {},
        },
        "required": ["message"],
    }
    error_schema = {
        "properties": {
            "error": {},
            "threadId": {},
            "turnId": {},
            "willRetry": {},
        },
        "required": ["error", "threadId", "turnId", "willRetry"],
        "definitions": {"TurnError": turn_error},
    }
    turn_schema = {
        "properties": {"threadId": {}, "turn": {}},
        "definitions": {
            "Turn": {
                "properties": {
                    "id": {},
                    "status": {},
                    "error": {},
                }
            },
            "TurnStatus": {"enum": ["completed", "interrupted", "failed", "inProgress"]},
            "TurnError": turn_error,
        },
    }
    m.verify_schema_contract(error_schema, turn_schema)


def test_no_execution_transport_in_observability_component():
    source = MODULE.read_text(encoding="utf-8")
    for token in ("subprocess.", "socket.", "requests.", "turn/start", "thread/start", "app-server"):
        assert token not in source


def test_scope_amendment_keeps_d2s4_closed_but_p5a_open():
    text = " ".join(AMENDMENT.read_text(encoding="utf-8").split())
    assert "P5A Codex adapter:** OPEN" in text
    assert "D2-S4 attempt:** FORMALLY CLOSED / INVALID / CONSUMED / NO RETRY" in text
    assert "NO_MODEL_BEARING_SUCCESSOR_UNTIL_OBSERVABILITY_QUALIFICATION_PASS" in text
    assert "does not itself authorize a model turn" in text.lower()


def test_spec_requires_zero_model_privacy_and_successor_design_only():
    text = " ".join(SPEC.read_text(encoding="utf-8").split())
    assert "ZERO-MODEL" in text
    assert "TurnError.message" in text
    assert "codexErrorInfo" in text
    assert "additionalDetails" in text
    assert "willRetry" in text
    assert "privacy-safe" in text
    assert "design/preregistration" in text
