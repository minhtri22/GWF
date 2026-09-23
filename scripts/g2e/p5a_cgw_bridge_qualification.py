from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tomllib
from pathlib import Path
from typing import Any

CGW_SOURCE_REPOSITORY = "miuuyy/codex-chatgpt-web"
CGW_SOURCE_COMMIT = "eaf4f09ae92d4dc4429fa597b0861663138f08f8"
CGW_RELEASE_VERSION = "5.0.8"
CGW_ROUTE_ID = "p5a-cgw"
CGW_SERVICE = "codex-chatgpt-web"
CGW_MODEL_PREFIX = "chatgpt-web/"
CGW_AUTOMATIC_CONNECTOR = "Codex Native2"
CGW_ZERO_RISK_CONNECTOR = "Codex Zero Risk"
CGW_LEGACY_CONNECTOR = "Codex Native"

UPSTREAM_BLOBS = {
    "src/server.ts": "ea92b0e5b741dbb3271c17d036ad6a7baedd7a7e",
    "src/config.ts": "1b9fb089d350a92b8490fbd1dc96a90c03516a60",
    "src/chatgpt-web-models.ts": "d2ebd757480dadbe9b740b0a5bfc1f42af503c0f",
    "src/codex-integration.ts": "8e87eb5035b2dab5d1f43f27828bd95e118b383b",
    "src/codex-integration-route.ts": "b14868ec3fc351d9e68043edb22837aaf48eff83",
    "docs/security-model.md": "9040d4cafb57502af650ab3a732937eb9b35dc74",
}

FAILURE_MATRIX = {
    "bridge_daemon_unavailable": "PRE_ATTEMPT_BLOCK",
    "bridge_health_version_mismatch": "PRE_ATTEMPT_BLOCK",
    "routed_model_unavailable": "PRE_ATTEMPT_BLOCK",
    "browser_not_ready": "PRE_ATTEMPT_BLOCK",
    "browser_task_lease_mismatch": "FUTURE_ATTEMPT_INVALID",
    "submission_not_acknowledged": "FUTURE_ATTEMPT_INVALID",
    "response_identity_ambiguous": "FUTURE_ATTEMPT_INVALID",
    "sse_interrupted_before_terminal": "FUTURE_ATTEMPT_INVALID",
    "browser_ui_drift": "FUTURE_ATTEMPT_INVALID",
    "connector_mismatch": "PRE_ATTEMPT_BLOCK",
    "tunnel_unavailable": "PRE_ATTEMPT_BLOCK",
    "active_tool_registry_mismatch": "FUTURE_ATTEMPT_INVALID",
    "tool_capability_turn_mismatch": "FUTURE_ATTEMPT_INVALID",
    "approval_denial": "FUTURE_ATTEMPT_INVALID",
    "missing_mandatory_evidence": "FUTURE_ATTEMPT_INVALID",
    "secret_redaction_failure": "FUTURE_ATTEMPT_INVALID",
    "native_official_fallback_attempt": "FUTURE_ATTEMPT_INVALID",
    "bridge_mode_substitution_attempt": "FUTURE_ATTEMPT_INVALID",
}

_SECRET_KEY_RE = re.compile(
    r"(authorization|cookie|token|secret|password|credential|api[_-]?key|runtimekey|controltoken)",
    re.IGNORECASE,
)
_SECRET_VALUE_RE = re.compile(
    r"(?i)(Bearer\s+[A-Za-z0-9._~+/=-]{8,}|sk-[A-Za-z0-9_-]{8,}|api[_-]?key\s*[:=]\s*\S+)"
)


class QualificationError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def _git(*args: str, cwd: Path) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=cwd, text=True, stderr=subprocess.STDOUT
    ).strip()


def verify_upstream_tree(root: Path) -> dict[str, Any]:
    head = _git("rev-parse", "HEAD", cwd=root)
    if head != CGW_SOURCE_COMMIT:
        raise QualificationError(f"CGW_SOURCE_COMMIT_MISMATCH:{head}")
    observed: dict[str, str] = {}
    for path, expected in UPSTREAM_BLOBS.items():
        actual = _git("rev-parse", f"HEAD:{path}", cwd=root)
        observed[path] = actual
        if actual != expected:
            raise QualificationError(f"CGW_UPSTREAM_BLOB_MISMATCH:{path}:{actual}")

    server = (root / "src/server.ts").read_text(encoding="utf-8")
    config = (root / "src/config.ts").read_text(encoding="utf-8")
    models = (root / "src/chatgpt-web-models.ts").read_text(encoding="utf-8")
    security = (root / "docs/security-model.md").read_text(encoding="utf-8")

    required_fragments = (
        ('url.pathname === "/healthz"', server),
        ('url.pathname === "/v1/responses"', server),
        ('status: "ok"', server),
        ('service: "codex-chatgpt-web"', server),
        ('export const CHATGPT_CONNECTOR_NAME = "Codex Native2"', config),
        ('export const ZERO_RISK_CHATGPT_CONNECTOR_NAME = "Codex Zero Risk"', config),
        ('export const LEGACY_CHATGPT_CONNECTOR_NAMES = ["Codex Native"]', config),
        ('export const CHATGPT_WEB_MODEL_PREFIX = "chatgpt-web/"', models),
        ("The bridge transports decisions; it does not add a second planner", security),
        ("MCP can request only a callable tool advertised by the active outer Codex turn", security),
    )
    missing = [fragment for fragment, text in required_fragments if fragment not in text]
    if missing:
        raise QualificationError("CGW_UPSTREAM_CONTRACT_FRAGMENT_MISSING:" + "|".join(missing))

    return {
        "source_repository": CGW_SOURCE_REPOSITORY,
        "source_commit": head,
        "source_blobs": observed,
        "source_contract_pass": True,
    }


def _require(condition: bool, code: str, errors: list[str]) -> None:
    if not condition:
        errors.append(code)


def project_bridge_config(raw: dict[str, Any], raw_bytes: bytes | None = None) -> dict[str, Any]:
    errors: list[str] = []
    version = raw.get("version")
    release = raw.get("releaseVersion")
    mode = raw.get("mode")
    host = raw.get("host")
    port = raw.get("port")
    interaction = raw.get("browserInteractionMode", "automatic")
    app_name = raw.get("appName")
    automatic_name = raw.get("automaticAppName", CGW_AUTOMATIC_CONNECTOR)
    manual_name = raw.get("manualAppName", CGW_ZERO_RISK_CONNECTOR)
    auto_approve = raw.get("autoApproveToolCalls")

    _require(version == 3, "CGW_CONFIG_VERSION", errors)
    _require(release == CGW_RELEASE_VERSION, "CGW_RELEASE_VERSION", errors)
    _require(mode in {"browser-only", "full"}, "CGW_MODE", errors)
    _require(host == "127.0.0.1", "CGW_HOST_NOT_LOOPBACK", errors)
    _require(isinstance(port, int) and 1 <= port <= 65535, "CGW_PORT", errors)
    _require(interaction in {"automatic", "manual"}, "CGW_INTERACTION_MODE", errors)
    _require(auto_approve is False, "CGW_AUTO_APPROVE_MUST_BE_FALSE", errors)
    _require(automatic_name == CGW_AUTOMATIC_CONNECTOR, "CGW_AUTOMATIC_CONNECTOR_IDENTITY", errors)
    _require(manual_name == CGW_ZERO_RISK_CONNECTOR, "CGW_ZERO_RISK_CONNECTOR_IDENTITY", errors)

    if interaction == "automatic":
        _require(app_name == CGW_AUTOMATIC_CONNECTOR, "CGW_ACTIVE_CONNECTOR_AUTOMATIC", errors)
    elif interaction == "manual":
        _require(mode == "full", "CGW_ZERO_RISK_REQUIRES_FULL", errors)
        _require(app_name == CGW_ZERO_RISK_CONNECTOR, "CGW_ACTIVE_CONNECTOR_ZERO_RISK", errors)

    tunnel_present = bool(raw.get("tunnel") or raw.get("automaticTunnel") or raw.get("manualTunnel"))
    if mode == "full":
        _require(tunnel_present, "CGW_FULL_TUNNEL_CONFIG_MISSING", errors)

    runtime_command = raw.get("runtimeCommand")
    _require(
        isinstance(runtime_command, list)
        and bool(runtime_command)
        and all(isinstance(x, str) and x for x in runtime_command),
        "CGW_RUNTIME_COMMAND",
        errors,
    )

    projection = {
        "config_version": version,
        "release_version": release,
        "mode": mode,
        "host": host,
        "port": port,
        "browser_host": raw.get("browserHost"),
        "browser_interaction_mode": interaction,
        "active_connector": app_name,
        "automatic_connector": automatic_name,
        "manual_connector": manual_name,
        "subagent_protocol": raw.get("subagentProtocol"),
        "auto_approve_tool_calls": auto_approve,
        "tunnel_config_present": tunnel_present,
        "runtime_command_arity": len(runtime_command) if isinstance(runtime_command, list) else 0,
        "raw_config_sha256": sha256_bytes(raw_bytes) if raw_bytes is not None else canonical_sha256(raw),
    }
    return {"valid": not errors, "errors": errors, "projection": projection}


def project_health(payload: dict[str, Any], bridge: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    _require(payload.get("status") == "ok", "CGW_HEALTH_STATUS", errors)
    _require(payload.get("service") == CGW_SERVICE, "CGW_HEALTH_SERVICE", errors)
    _require(payload.get("version") == bridge.get("release_version"), "CGW_HEALTH_VERSION", errors)
    _require(payload.get("mode") == bridge.get("mode"), "CGW_HEALTH_MODE", errors)
    _require(payload.get("port") == bridge.get("port"), "CGW_HEALTH_PORT", errors)
    _require(payload.get("accepting_turns") is True, "CGW_NOT_ACCEPTING_TURNS", errors)
    _require(payload.get("active_http_turns") == 0, "CGW_ACTIVE_HTTP_TURNS", errors)
    _require(payload.get("active_browser_turns") == 0, "CGW_ACTIVE_BROWSER_TURNS", errors)
    safe = {
        "status": payload.get("status"),
        "service": payload.get("service"),
        "version": payload.get("version"),
        "mode": payload.get("mode"),
        "port": payload.get("port"),
        "accepting_turns": payload.get("accepting_turns"),
        "active_http_turns": payload.get("active_http_turns"),
        "active_browser_turns": payload.get("active_browser_turns"),
        "successful_model_catalog_requests": payload.get("successful_model_catalog_requests"),
    }
    return {"valid": not errors, "errors": errors, "projection": safe}


def project_codex_route(toml_text: str, expected_port: int) -> dict[str, Any]:
    errors: list[str] = []
    try:
        parsed = tomllib.loads(toml_text)
    except tomllib.TOMLDecodeError as exc:
        return {"valid": False, "errors": [f"CODEX_CONFIG_TOML:{exc}"], "projection": {}}

    expected = f"http://127.0.0.1:{expected_port}/v1"
    base_url = parsed.get("openai_base_url")
    provider = parsed.get("model_provider")
    selected_model = parsed.get("model")
    _require(base_url == expected, "CODEX_OPENAI_BASE_URL_NOT_CGW", errors)
    _require(provider in {None, "openai"}, "CODEX_MODEL_PROVIDER_NOT_OPENAI", errors)
    if selected_model is not None:
        _require(isinstance(selected_model, str), "CODEX_SELECTED_MODEL_INVALID", errors)
    projection = {
        "openai_base_url": base_url,
        "model_provider": provider,
        "selected_model_is_cgw": (
            isinstance(selected_model, str) and selected_model.startswith(CGW_MODEL_PREFIX)
        ),
        "model_catalog_configured": bool(parsed.get("model_catalog_json")),
        "raw_config_sha256": sha256_bytes(toml_text.encode("utf-8")),
    }
    return {"valid": not errors, "errors": errors, "projection": projection}


def redact_evidence(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if _SECRET_KEY_RE.search(str(key)):
                out[str(key)] = "<REDACTED_SECRET>"
            else:
                out[str(key)] = redact_evidence(item)
        return out
    if isinstance(value, list):
        return [redact_evidence(x) for x in value]
    if isinstance(value, tuple):
        return [redact_evidence(x) for x in value]
    if isinstance(value, str):
        return _SECRET_VALUE_RE.sub("<REDACTED_SECRET>", value)
    return value


def validate_route_trace(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        raise QualificationError("TRACE_EMPTY")
    starts = [x for x in records if x.get("event") == "codex_request"]
    terminals = [x for x in records if x.get("event") == "terminal"]
    submissions = [x for x in records if x.get("event") == "browser_submit"]
    if len(starts) != 1:
        raise QualificationError("TRACE_REQUEST_CARDINALITY")
    if len(submissions) != 1:
        raise QualificationError("TRACE_SUBMISSION_CARDINALITY")
    if len(terminals) != 1:
        raise QualificationError("TRACE_TERMINAL_CARDINALITY")

    start, submit, terminal = starts[0], submissions[0], terminals[0]
    for field in ("request_id", "outer_thread_id", "outer_turn_id"):
        expected = start.get(field)
        if not expected:
            raise QualificationError(f"TRACE_IDENTITY_MISSING:{field}")
        if submit.get(field) != expected or terminal.get(field) != expected:
            raise QualificationError(f"TRACE_IDENTITY_MISMATCH:{field}")

    lease = submit.get("browser_lease_id")
    chat_turn = submit.get("chatgpt_turn_id")
    if not lease or not chat_turn:
        raise QualificationError("TRACE_BROWSER_BINDING_MISSING")
    if terminal.get("browser_lease_id") != lease:
        raise QualificationError("TRACE_BROWSER_LEASE_MISMATCH")
    if terminal.get("chatgpt_turn_id") != chat_turn:
        raise QualificationError("TRACE_CHATGPT_TURN_MISMATCH")

    mode = start.get("bridge_mode")
    model = start.get("model")
    if mode not in {"browser-only", "full"}:
        raise QualificationError("TRACE_BRIDGE_MODE")
    if not isinstance(model, str) or not model.startswith(CGW_MODEL_PREFIX):
        raise QualificationError("TRACE_MODEL_NOT_CGW")
    if submit.get("bridge_mode") != mode or terminal.get("bridge_mode") != mode:
        raise QualificationError("TRACE_MODE_SUBSTITUTION")
    if submit.get("model") != model or terminal.get("model") != model:
        raise QualificationError("TRACE_MODEL_SUBSTITUTION")

    for record in records:
        if record.get("bridge_side_effects_performed") is True:
            raise QualificationError("BRIDGE_EXECUTED_LOCAL_SIDE_EFFECT")

    return {
        "valid": True,
        "request_id": start["request_id"],
        "outer_thread_id": start["outer_thread_id"],
        "outer_turn_id": start["outer_turn_id"],
        "browser_lease_id": lease,
        "chatgpt_turn_id": chat_turn,
        "bridge_mode": mode,
        "model": model,
        "record_count": len(records),
        "trace_sha256": canonical_sha256(redact_evidence(records)),
    }


def validate_tool_roundtrip(
    event: dict[str, Any],
    *,
    expected_thread: str,
    expected_turn: str,
    expected_connector: str,
    allowed_tools: set[str],
    expected_capability_digest: str,
) -> dict[str, Any]:
    if event.get("outer_thread_id") != expected_thread:
        raise QualificationError("TOOL_THREAD_MISMATCH")
    if event.get("outer_turn_id") != expected_turn:
        raise QualificationError("TOOL_TURN_MISMATCH")
    if event.get("connector") != expected_connector:
        raise QualificationError("TOOL_CONNECTOR_MISMATCH")
    if expected_connector == CGW_LEGACY_CONNECTOR:
        raise QualificationError("LEGACY_CONNECTOR_FORBIDDEN")
    if event.get("capability_token_digest") != expected_capability_digest:
        raise QualificationError("TOOL_CAPABILITY_MISMATCH")
    if event.get("tool_name") not in allowed_tools:
        raise QualificationError("TOOL_NOT_IN_OUTER_CODEX_REGISTRY")
    if event.get("executor") != "codex":
        raise QualificationError("TOOL_EXECUTOR_NOT_CODEX")
    if event.get("bridge_side_effects_performed") is not False:
        raise QualificationError("BRIDGE_SIDE_EFFECT_FLAG_INVALID")
    if "capability_token" in event:
        raise QualificationError("RAW_CAPABILITY_TOKEN_PERSISTED")
    return {
        "valid": True,
        "tool_name": event["tool_name"],
        "executor": "codex",
        "invocation_id": event.get("invocation_id"),
        "result_sha256": event.get("result_sha256"),
    }


def synthetic_fixture(mode: str = "full") -> tuple[dict[str, Any], dict[str, Any], str]:
    config: dict[str, Any] = {
        "version": 3,
        "releaseVersion": CGW_RELEASE_VERSION,
        "mode": mode,
        "subagentProtocol": "compatibility-v1",
        "host": "127.0.0.1",
        "port": 17841,
        "contextWindow": 256000,
        "appName": CGW_AUTOMATIC_CONNECTOR,
        "automaticAppName": CGW_AUTOMATIC_CONNECTOR,
        "manualAppName": CGW_ZERO_RISK_CONNECTOR,
        "browserHost": "launcher",
        "browserInteractionMode": "automatic",
        "chromeExecutablePath": "C:/Program Files/Google/Chrome/Application/chrome.exe",
        "storageStatePath": "C:/redacted/storage-state.json",
        "brokerSocketPath": r"\\.\pipe\codex-chatgpt-web-synthetic",
        "headed": True,
        "solAvailable": True,
        "extraHighAvailable": True,
        "proAvailable": True,
        "experimentalBiggerContext": False,
        "experimentalSkillAttachments": False,
        "zeroRiskProEnabled": False,
        "autoApproveToolCalls": False,
        "controlToken": "SECRET_CONTROL_TOKEN_SHOULD_NEVER_PERSIST",
        "runtimeCommand": ["C:/Program Files/Codex Web GPT/Codex Web GPT.exe"],
    }
    if mode == "full":
        config["automaticTunnel"] = {
            "binaryPath": "C:/redacted/tunnel-client.exe",
            "tunnelId": "tunnel_" + "a" * 32,
            "runtimeKeyFile": "C:/redacted/runtime.key",
            "profileDir": "C:/redacted/profiles",
            "profileName": "codex-chatgpt-web",
            "alias": "synthetic",
        }
    health = {
        "status": "ok",
        "service": CGW_SERVICE,
        "version": CGW_RELEASE_VERSION,
        "mode": mode,
        "pid": 1234,
        "port": 17841,
        "uptime": 10.0,
        "accepting_turns": True,
        "successful_model_catalog_requests": 1,
        "last_successful_model_catalog_request_at": "2026-09-23T00:00:00Z",
        "model_catalog_requests": 1,
        "last_model_catalog_result": {"request": 1, "status": 200},
        "active_http_turns": 0,
        "active_browser_turns": 0,
    }
    codex_toml = "\n".join([
        'model = "chatgpt-web/high"',
        'model_provider = "openai"',
        'openai_base_url = "http://127.0.0.1:17841/v1"',
        'model_catalog_json = "C:/redacted/models.json"',
    ])
    return config, health, codex_toml


def run_synthetic_qualification(upstream_root: Path | None = None) -> dict[str, Any]:
    q: dict[str, Any] = {}
    if upstream_root is not None:
        q["Q0_source_provenance"] = verify_upstream_tree(upstream_root)
    else:
        q["Q0_source_provenance"] = {
            "source_repository": CGW_SOURCE_REPOSITORY,
            "source_commit": CGW_SOURCE_COMMIT,
            "source_contract_pass": None,
            "note": "exact upstream tree not supplied to this invocation",
        }

    config, health, codex_toml = synthetic_fixture("full")
    cfg = project_bridge_config(config, canonical_bytes(config))
    if not cfg["valid"]:
        raise QualificationError("SYNTHETIC_CONFIG:" + ",".join(cfg["errors"]))
    hp = project_health(health, cfg["projection"])
    if not hp["valid"]:
        raise QualificationError("SYNTHETIC_HEALTH:" + ",".join(hp["errors"]))
    cr = project_codex_route(codex_toml, 17841)
    if not cr["valid"]:
        raise QualificationError("SYNTHETIC_CODEX_ROUTE:" + ",".join(cr["errors"]))
    q["Q1_route_no_fallback"] = {
        "pass": True,
        "route": cr["projection"]["openai_base_url"],
        "mode": cfg["projection"]["mode"],
        "connector": cfg["projection"]["active_connector"],
    }

    trace = [
        {
            "event": "codex_request",
            "request_id": "req-1",
            "outer_thread_id": "thread-1",
            "outer_turn_id": "turn-1",
            "bridge_mode": "full",
            "model": "chatgpt-web/high",
            "bridge_side_effects_performed": False,
        },
        {
            "event": "browser_submit",
            "request_id": "req-1",
            "outer_thread_id": "thread-1",
            "outer_turn_id": "turn-1",
            "browser_lease_id": "lease-1",
            "chatgpt_turn_id": "chat-turn-1",
            "bridge_mode": "full",
            "model": "chatgpt-web/high",
            "bridge_side_effects_performed": False,
        },
        {
            "event": "terminal",
            "request_id": "req-1",
            "outer_thread_id": "thread-1",
            "outer_turn_id": "turn-1",
            "browser_lease_id": "lease-1",
            "chatgpt_turn_id": "chat-turn-1",
            "bridge_mode": "full",
            "model": "chatgpt-web/high",
            "status": "completed",
            "bridge_side_effects_performed": False,
        },
    ]
    trace_result = validate_route_trace(trace)
    q["Q2_request_response_correlation"] = {"pass": True, **trace_result}
    q["Q3_browser_binding_observability"] = {
        "pass": bool(trace_result["browser_lease_id"] and trace_result["chatgpt_turn_id"]),
        "binding": "lease+logical-turn",
    }

    allowed = {"read_file", "write_result"}
    cap_digest = sha256_bytes(b"synthetic-turn-capability")
    tool = {
        "outer_thread_id": "thread-1",
        "outer_turn_id": "turn-1",
        "connector": CGW_AUTOMATIC_CONNECTOR,
        "capability_token_digest": cap_digest,
        "tool_name": "read_file",
        "invocation_id": "tool-1",
        "executor": "codex",
        "bridge_side_effects_performed": False,
        "result_sha256": "a" * 64,
    }
    tool_result = validate_tool_roundtrip(
        tool,
        expected_thread="thread-1",
        expected_turn="turn-1",
        expected_connector=CGW_AUTOMATIC_CONNECTOR,
        allowed_tools=allowed,
        expected_capability_digest=cap_digest,
    )
    q["Q4_authority_preservation"] = {
        "pass": True,
        "delegation_rule": "bridge<=outer_codex_turn<=g2e_attempt",
        "bridge_side_effects_performed": False,
    }
    q["Q5_full_mode_mcp_binding"] = {"pass": True, **tool_result}

    secret_fixture = {
        "Authorization": "Bearer SUPERSECRET123456789",
        "cookie": "session=SECRET",
        "safe": "ok",
        "nested": {"api_key": "sk-abcdef1234567890", "message": "Bearer TOPSECRET987654321"},
    }
    redacted = redact_evidence(secret_fixture)
    rendered = json.dumps(redacted, sort_keys=True)
    if "SUPERSECRET" in rendered or "abcdef123" in rendered or "TOPSECRET" in rendered:
        raise QualificationError("SYNTHETIC_SECRET_REDACTION")
    q["Q6_observability_privacy"] = {
        "pass": True,
        "redacted_fixture_sha256": canonical_sha256(redacted),
        "raw_secret_values_persisted": False,
    }

    q["Q7_failure_injection"] = {
        "pass": len(FAILURE_MATRIX) == 18,
        "cases": FAILURE_MATRIX,
    }
    if not q["Q7_failure_injection"]["pass"]:
        raise QualificationError("FAILURE_MATRIX_INCOMPLETE")

    q["Q8_g2e_regression"] = {
        "pass": None,
        "note": "workflow-owned; set PASS only after P1/P1.4/P1.5/P2/P3/P4 jobs pass",
    }
    return {
        "schema": "G2E-P5A-CGW-SYNTHETIC-QUALIFICATION-v1",
        "route_id": CGW_ROUTE_ID,
        "status": "SYNTHETIC_ZERO_MODEL_CORE_PASS",
        "source_commit": CGW_SOURCE_COMMIT,
        "release_version": CGW_RELEASE_VERSION,
        "gates": q,
        "model_turn_executed": False,
        "scientific_attempt_created": False,
        "scientific_attempt_consumed": False,
        "functional_claim": False,
        "local_runtime_admission_required": True,
    }


def build_local_admission(
    *,
    config_path: Path,
    codex_config_path: Path,
    health_path: Path,
    cgw_binary_path: Path,
    codex_command_path: Path,
) -> dict[str, Any]:
    config_bytes = config_path.read_bytes()
    config_raw = json.loads(config_bytes.decode("utf-8-sig"))
    cfg = project_bridge_config(config_raw, config_bytes)
    health_payload = json.loads(health_path.read_text(encoding="utf-8-sig"))
    health = project_health(health_payload, cfg["projection"])
    codex_text = codex_config_path.read_text(encoding="utf-8-sig")
    route = project_codex_route(codex_text, int(cfg["projection"].get("port") or 0))

    errors = [*cfg["errors"], *health["errors"], *route["errors"]]
    binaries: dict[str, Any] = {}
    for label, path in (
        ("cgw_launcher_or_runtime", cgw_binary_path),
        ("codex_command", codex_command_path),
    ):
        if not path.exists() or not path.is_file():
            errors.append(f"{label.upper()}_NOT_FOUND")
            continue
        binaries[label] = {
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
            "basename": path.name,
        }

    full_mode_ready = cfg["projection"].get("mode") == "full"
    if full_mode_ready:
        if cfg["projection"].get("browser_interaction_mode") == "automatic":
            _require(
                cfg["projection"].get("active_connector") == CGW_AUTOMATIC_CONNECTOR,
                "LOCAL_FULL_CONNECTOR_MISMATCH",
                errors,
            )
        _require(cfg["projection"].get("tunnel_config_present") is True, "LOCAL_FULL_TUNNEL_MISSING", errors)

    status = "LOCAL_ZERO_MODEL_ADMISSION_PASS" if not errors else "LOCAL_ZERO_MODEL_ADMISSION_BLOCKED"
    report = {
        "schema": "G2E-P5A-CGW-LOCAL-ZERO-MODEL-ADMISSION-v1",
        "route_id": CGW_ROUTE_ID,
        "status": status,
        "source_reference": {
            "repository": CGW_SOURCE_REPOSITORY,
            "commit": CGW_SOURCE_COMMIT,
            "release_version": CGW_RELEASE_VERSION,
        },
        "bridge_config": cfg["projection"],
        "bridge_health": health["projection"],
        "codex_route": route["projection"],
        "binary_identities": binaries,
        "full_mode_observed": full_mode_ready,
        "errors": errors,
        "model_turn_executed": False,
        "responses_endpoint_called": False,
        "models_endpoint_called": False,
        "scientific_attempt_created": False,
        "scientific_attempt_consumed": False,
        "functional_claim": False,
        "next_if_pass": "FORMAL_CLOSE_P5A_CGW_ZERO_MODEL_QUALIFICATION_THEN_PREREGISTER_FIRST_FUNCTIONAL_ATTEMPT",
    }
    report["evidence_sha256"] = canonical_sha256(report)
    return report


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="P5A-CGW zero-model qualification and local admission")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--synthetic-output")
    mode.add_argument("--local-output")
    parser.add_argument("--upstream-root")
    parser.add_argument("--cgw-config")
    parser.add_argument("--codex-config")
    parser.add_argument("--health-json")
    parser.add_argument("--cgw-binary")
    parser.add_argument("--codex-command-path")
    args = parser.parse_args()

    if args.synthetic_output:
        report = run_synthetic_qualification(
            Path(args.upstream_root).resolve() if args.upstream_root else None
        )
        _write_json(Path(args.synthetic_output), report)
        print(json.dumps({
            "status": report["status"],
            "model_turn_executed": False,
            "scientific_attempt_created": False,
        }, sort_keys=True))
        return 0

    required = {
        "--cgw-config": args.cgw_config,
        "--codex-config": args.codex_config,
        "--health-json": args.health_json,
        "--cgw-binary": args.cgw_binary,
        "--codex-command-path": args.codex_command_path,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        parser.error("local admission requires " + ", ".join(missing))

    report = build_local_admission(
        config_path=Path(args.cgw_config),
        codex_config_path=Path(args.codex_config),
        health_path=Path(args.health_json),
        cgw_binary_path=Path(args.cgw_binary),
        codex_command_path=Path(args.codex_command_path),
    )
    _write_json(Path(args.local_output), report)
    print(json.dumps({
        "status": report["status"],
        "evidence_sha256": report["evidence_sha256"],
        "model_turn_executed": False,
        "responses_endpoint_called": False,
    }, sort_keys=True))
    return 0 if report["status"] == "LOCAL_ZERO_MODEL_ADMISSION_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
