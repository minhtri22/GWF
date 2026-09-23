from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

V4_REPOSITORY = "miuuyy/codex-chatgpt-web"
V4_TAG = "v4.0.7"
V4_TAG_OBJECT = "425092367f5cbfa33a071e460dbd72215bf0b9fa"
V4_SOURCE_COMMIT = "b59d7dc51b84fb1f465ff1d00f5207f3b2b4a494"
V4_VERSION = "4.0.7"

V4_WINDOWS_LAUNCHER_ASSET_SHA256 = "90f47feaa5c6c17612ac9bee6a49b11b65e0241b046b7380e2c5219792a55354"
V4_WINDOWS_RUNTIME_ZIP_SHA256 = "49f51bed4b85c7d5d54707b09791fa8360f653f97532e0dc16aceeb04d1dd611"

V4_BLOBS = {
    "src/server.ts": "af4cd5c3886f119f35efa4fc0e28bd2ecfc48530",
    "src/config.ts": "1444c64ab66282e72411585392e3d242773a971a",
    "src/chatgpt-web-models.ts": "dae14ce18737d4bdd7206b3df453b20f30a073ea",
    "src/codex-integration.ts": "ca7210f0922972ac46bbed94107f5dd65cbc224f",
    "src/codex-integration-route.ts": "19841e3e0db5f5dfb62007d3669eb1f8adea2798",
    "docs/security-model.md": "cb1e4db10e462df3cb8040b83207982f6efa833a",
    "docs/release-validation.md": "85b1fc9bbee7ec7e1b949e2fdc15cde44f1affd3",
    "src/version.ts": "328cfba86faf2cccb9e98f35439abdeb5cfb5e5f",
    "package.json": "dee8af97f29d83a2959708538949a4d2e705b2ab",
    "launcher/package.json": "bae08e5855a6af0ca3e050fca3eccbccdc7cef1e",
}

EXISTING_Q0B_FILE_SHA256 = "b91f425a1b92ea0c4cf2d5f1179ecd413cc04b5ac6285034dfd975b446efc2ff"
EXISTING_Q0B_INTERNAL_SHA256 = "551d6c90c48c0761880d937257189b626d586772030558e34a516d4d80d6a68e"
EXISTING_CGW_BINARY_SHA256 = "ac152ad499b1f41b2cafe94a3d05f5d4e4d3cd7ddbb417b9c60b118b08bc3cbb"
EXISTING_CODEX_BINARY_SHA256 = "a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8"


class QualificationError(ValueError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )


def _git(*args: str, cwd: Path) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=cwd, text=True, stderr=subprocess.STDOUT
    ).strip()


def _require_fragment(text: str, fragment: str, code: str) -> None:
    if fragment not in text:
        raise QualificationError(f"{code}:{fragment}")


def verify_v4_source_contract(root: Path) -> dict[str, Any]:
    head = _git("rev-parse", "HEAD", cwd=root)
    if head != V4_SOURCE_COMMIT:
        raise QualificationError(f"V4_SOURCE_COMMIT_MISMATCH:{head}")

    observed: dict[str, str] = {}
    for path, expected in V4_BLOBS.items():
        actual = _git("rev-parse", f"HEAD:{path}", cwd=root)
        observed[path] = actual
        if actual != expected:
            raise QualificationError(f"V4_SOURCE_BLOB_MISMATCH:{path}:{actual}")

    server = (root / "src/server.ts").read_text(encoding="utf-8")
    config = (root / "src/config.ts").read_text(encoding="utf-8")
    models = (root / "src/chatgpt-web-models.ts").read_text(encoding="utf-8")
    route = (root / "src/codex-integration-route.ts").read_text(encoding="utf-8")
    security = (root / "docs/security-model.md").read_text(encoding="utf-8")
    release_validation = (root / "docs/release-validation.md").read_text(encoding="utf-8")
    version = (root / "src/version.ts").read_text(encoding="utf-8")
    package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    launcher_package = json.loads((root / "launcher/package.json").read_text(encoding="utf-8"))

    _require_fragment(version, 'export const VERSION = "4.0.7";', "V4_VERSION_SOURCE")
    if package.get("version") != V4_VERSION:
        raise QualificationError("V4_PACKAGE_VERSION")
    if launcher_package.get("version") != V4_VERSION:
        raise QualificationError("V4_LAUNCHER_PACKAGE_VERSION")

    for fragment in (
        'hostname: config.host',
        'url.pathname === "/healthz"',
        'status: "ok"',
        'service: "codex-chatgpt-web"',
        'version: VERSION',
        'mode: config.mode',
        'accepting_turns: !draining',
        'active_http_turns',
        'active_browser_turns',
        'url.pathname === "/v1/responses"',
    ):
        _require_fragment(server, fragment, "V4_SERVER_CONTRACT")

    for fragment in (
        'export type RuntimeMode = "browser-only" | "full";',
        'export const CHATGPT_CONNECTOR_NAME = "Codex Native2";',
        'export const LEGACY_CHATGPT_CONNECTOR_NAMES = ["Codex Native"] as const;',
        'releaseVersion: string;',
        'host: "127.0.0.1";',
        'mode: RuntimeMode;',
        'appName: string;',
        'autoApproveToolCalls: boolean;',
        'controlToken: string;',
        'runtimeCommand: string[];',
        'tunnel?: TunnelConfig;',
    ):
        _require_fragment(config, fragment, "V4_CONFIG_CONTRACT")

    _require_fragment(models, 'export const CHATGPT_WEB_MODEL_PREFIX = "chatgpt-web/";', "V4_MODEL_PREFIX")

    for fragment in (
        '"openai_base_url"',
        'openai_base_url = ${JSON.stringify(installedUrl)}',
        'Rerun with --replace-codex-route to replace it reversibly.',
    ):
        _require_fragment(route, fragment, "V4_ROUTE_CONTRACT")

    for fragment in (
        "It extracts `cwd`, workspace roots, sandbox policy, and the tool registry only from the native",
        "A user-authored `<environment_context>` is not",
        "It creates a random, turn-scoped token",
        "MCP can request only a tool advertised by the active outer Codex turn.",
        "Codex remains responsible",
        "The bridge transports decisions; it does not add a second planner, semantic router, or fallback",
        "The pre-v4 `Codex Native` connector is treated as legacy and is never selected as a fallback.",
        "Responses and health listeners bind to `127.0.0.1` only.",
        "UI drift fails the turn; it never chooses another model, starts another transport, or returns a fabricated success.",
    ):
        _require_fragment(security, fragment, "V4_AUTHORITY_CONTRACT")

    for fragment in (
        "CI proves that the runtime builds, the launcher starts, and native packages pass their smoke",
        "It does not prove an authenticated ChatGPT session, a live",
        "MCP connector, or a complete Codex turn.",
    ):
        _require_fragment(release_validation, fragment, "V4_RELEASE_LIMITATION")

    return {
        "schema": "G2E-P5A-CGW-V4-SOURCE-CONTRACT-QUALIFICATION-v1",
        "status": "V4_SOURCE_CONTRACT_PASS",
        "repository": V4_REPOSITORY,
        "tag": V4_TAG,
        "tag_object": V4_TAG_OBJECT,
        "source_commit": head,
        "version": V4_VERSION,
        "source_blobs": observed,
        "contract": {
            "loopback_health_and_responses_surface": True,
            "health_reports_version_mode_idle_state": True,
            "connector_codex_native2": True,
            "legacy_connector_no_fallback": True,
            "chatgpt_web_model_namespace": True,
            "codex_route_ownership": True,
            "outer_codex_turn_is_local_execution_authority": True,
            "turn_scoped_mcp_capability": True,
            "active_outer_turn_tool_registry_bounds_mcp": True,
            "bridge_is_not_second_planner_or_fallback": True,
            "browser_ui_drift_fails_closed": True,
        },
        "release_assets": {
            "windows_launcher_sha256": V4_WINDOWS_LAUNCHER_ASSET_SHA256,
            "windows_runtime_zip_sha256": V4_WINDOWS_RUNTIME_ZIP_SHA256,
        },
        "limitations": {
            "authenticated_chatgpt_session_proven_by_source_ci": False,
            "live_mcp_connector_proven_by_source_ci": False,
            "complete_codex_turn_proven_by_source_ci": False,
            "installed_executable_reproducible_build_equivalence_proven": False,
            "binding_policy": (
                "exact source/tag contract + config/health self-identification + "
                "exact installed executable fingerprint under trusted local-user boundary"
            ),
        },
        "model_turn_executed": False,
        "runtime_mutated": False,
        "scientific_attempt_created": False,
    }


def _assert(condition: bool, code: str) -> None:
    if not condition:
        raise QualificationError(code)


def readjudicate_existing_q0b(report_path: Path, source_qualification: dict[str, Any]) -> dict[str, Any]:
    _assert(source_qualification.get("status") == "V4_SOURCE_CONTRACT_PASS", "V4_SOURCE_NOT_QUALIFIED")
    raw = report_path.read_bytes()
    _assert(sha256_bytes(raw) == EXISTING_Q0B_FILE_SHA256, "Q0B_FILE_SHA256_MISMATCH")
    report = json.loads(raw.decode("utf-8"))

    internal = report.get("evidence_sha256")
    _assert(internal == EXISTING_Q0B_INTERNAL_SHA256, "Q0B_INTERNAL_SHA256_FIELD_MISMATCH")
    unsigned = dict(report)
    unsigned.pop("evidence_sha256", None)
    _assert(canonical_sha256(unsigned) == internal, "Q0B_INTERNAL_SHA256_RECOMPUTE_MISMATCH")

    _assert(report.get("schema") == "G2E-P5A-CGW-LOCAL-ZERO-MODEL-ADMISSION-v1", "Q0B_SCHEMA")
    _assert(report.get("route_id") == "p5a-cgw", "Q0B_ROUTE_ID")
    _assert(report.get("status") == "LOCAL_ZERO_MODEL_ADMISSION_BLOCKED", "Q0B_ORIGINAL_STATUS")
    _assert(report.get("errors") == ["CGW_RELEASE_VERSION"], "Q0B_BLOCKER_NOT_VERSION_ONLY")

    source_ref = report.get("source_reference") or {}
    _assert(source_ref.get("repository") == V4_REPOSITORY, "Q0B_SOURCE_REPOSITORY")
    _assert(source_ref.get("release_version") == "5.0.8", "Q0B_EXPECTED_OLD_TARGET")
    _assert(source_ref.get("commit") == "eaf4f09ae92d4dc4429fa597b0861663138f08f8", "Q0B_EXPECTED_OLD_SOURCE_COMMIT")

    cfg = report.get("bridge_config") or {}
    health = report.get("bridge_health") or {}
    route = report.get("codex_route") or {}
    binaries = report.get("binary_identities") or {}

    _assert(cfg.get("config_version") == 3, "Q0B_V4_CONFIG_VERSION")
    _assert(cfg.get("release_version") == V4_VERSION, "Q0B_V4_CONFIG_RELEASE")
    _assert(cfg.get("mode") == "full", "Q0B_V4_MODE")
    _assert(cfg.get("host") == "127.0.0.1", "Q0B_V4_HOST")
    _assert(cfg.get("port") == 17841, "Q0B_V4_PORT")
    _assert(cfg.get("active_connector") == "Codex Native2", "Q0B_V4_CONNECTOR")
    _assert(cfg.get("auto_approve_tool_calls") is False, "Q0B_V4_AUTO_APPROVE")
    _assert(cfg.get("tunnel_config_present") is True, "Q0B_V4_TUNNEL")
    _assert(cfg.get("runtime_command_arity") == 2, "Q0B_V4_RUNTIME_COMMAND")

    _assert(health.get("status") == "ok", "Q0B_V4_HEALTH_STATUS")
    _assert(health.get("service") == "codex-chatgpt-web", "Q0B_V4_HEALTH_SERVICE")
    _assert(health.get("version") == V4_VERSION, "Q0B_V4_HEALTH_VERSION")
    _assert(health.get("mode") == "full", "Q0B_V4_HEALTH_MODE")
    _assert(health.get("port") == 17841, "Q0B_V4_HEALTH_PORT")
    _assert(health.get("accepting_turns") is True, "Q0B_V4_ACCEPTING_TURNS")
    _assert(health.get("active_http_turns") == 0, "Q0B_V4_HTTP_NOT_IDLE")
    _assert(health.get("active_browser_turns") == 0, "Q0B_V4_BROWSER_NOT_IDLE")

    _assert(route.get("openai_base_url") == "http://127.0.0.1:17841/v1", "Q0B_V4_CODEX_ROUTE")
    _assert(route.get("selected_model_is_cgw") is True, "Q0B_V4_SELECTED_MODEL")

    cgw_binary = binaries.get("cgw_launcher_or_runtime") or {}
    codex_binary = binaries.get("codex_command") or {}
    _assert(cgw_binary.get("sha256") == EXISTING_CGW_BINARY_SHA256, "Q0B_CGW_BINARY_IDENTITY")
    _assert(cgw_binary.get("size") == 223980032, "Q0B_CGW_BINARY_SIZE")
    _assert(codex_binary.get("sha256") == EXISTING_CODEX_BINARY_SHA256, "Q0B_CODEX_BINARY_IDENTITY")
    _assert(codex_binary.get("size") == 309166080, "Q0B_CODEX_BINARY_SIZE")

    for key in (
        "model_turn_executed",
        "models_endpoint_called",
        "responses_endpoint_called",
        "scientific_attempt_created",
        "scientific_attempt_consumed",
        "functional_claim",
    ):
        _assert(report.get(key) is False, f"Q0B_ZERO_MODEL_FIREWALL:{key}")

    return {
        "schema": "G2E-P5A-CGW-V4-Q0B-READJUDICATION-v1",
        "status": "Q0B_PASS_UNDER_CORRECTED_V4_TARGET",
        "route_id": "p5a-cgw",
        "original_evidence": {
            "file_sha256": EXISTING_Q0B_FILE_SHA256,
            "internal_evidence_sha256": EXISTING_Q0B_INTERNAL_SHA256,
            "original_status": "LOCAL_ZERO_MODEL_ADMISSION_BLOCKED",
            "original_blocker": "CGW_RELEASE_VERSION",
        },
        "corrected_target": {
            "release_version": V4_VERSION,
            "source_commit": V4_SOURCE_COMMIT,
            "source_contract_status": source_qualification["status"],
        },
        "admitted_local_runtime": {
            "cgw_binary_sha256": EXISTING_CGW_BINARY_SHA256,
            "codex_binary_sha256": EXISTING_CODEX_BINARY_SHA256,
            "bridge_release_version": V4_VERSION,
            "bridge_mode": "full",
            "active_connector": "Codex Native2",
            "host": "127.0.0.1",
            "port": 17841,
            "health_status": "ok",
            "accepting_turns": True,
            "idle": True,
            "codex_openai_base_url": "http://127.0.0.1:17841/v1",
            "selected_model_is_cgw": True,
        },
        "ignored_old_projection_fields_not_source_backed_in_v4": [
            "bridge_config.automatic_connector",
            "bridge_config.manual_connector",
            "bridge_config.browser_interaction_mode",
        ],
        "provenance_strength": (
            "EXACT_V4_SOURCE_CONTRACT_PLUS_RUNTIME_SELF_IDENTIFICATION_PLUS_LOCAL_BINARY_FINGERPRINT; "
            "NO_REPRODUCIBLE_BUILD_EQUIVALENCE_CLAIM"
        ),
        "model_turn_executed": False,
        "runtime_mutated": False,
        "scientific_attempt_created": False,
        "scientific_attempt_consumed": False,
        "functional_attempt_authorized": False,
        "comparative_ab_authorized": False,
        "next": "FORMAL_CLOSE_P5A_CGW_ZERO_MODEL_QUALIFICATION",
    }


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-root", required=True)
    parser.add_argument("--source-output", required=True)
    parser.add_argument("--existing-q0b")
    parser.add_argument("--readjudication-output")
    args = parser.parse_args()

    source = verify_v4_source_contract(Path(args.upstream_root).resolve())
    write_json(Path(args.source_output), source)

    summary: dict[str, Any] = {
        "source_status": source["status"],
        "model_turn_executed": False,
        "runtime_mutated": False,
    }

    if args.existing_q0b or args.readjudication_output:
        if not args.existing_q0b or not args.readjudication_output:
            parser.error("--existing-q0b and --readjudication-output must be supplied together")
        readjudication = readjudicate_existing_q0b(Path(args.existing_q0b), source)
        write_json(Path(args.readjudication_output), readjudication)
        summary["readjudication_status"] = readjudication["status"]

    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
