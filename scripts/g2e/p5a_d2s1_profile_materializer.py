from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
from pathlib import Path, PureWindowsPath


STUDY_ID = "p5a-d2s1-permission-profile-successor"
ATTEMPT_ID = "p5a-d2s1-p5-fx-001-attempt-001"
PROFILE_ID = "g2e_p5a_d2s1"

BASELINE_SHA = "dfc8e438b8b4d91582a97809bc402862a07d29f7"
PREDECESSOR_CLOSURE_SHA = "d6610cb2d996a85bd194b9796490fb206fd95ec5"

HARNESS_SHA256 = "a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8"
INPUT_SHA256 = "a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6"
TASK_SHA256 = "4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e"

CODEX_RELEASE_TAG = "rust-v0.153.4"
CODEX_RELEASE_COMMIT = "3d2ee51ca2d5db578f328aa75e20aa22c0197c9a"
THREAD_START_SCHEMA_SHA256 = "792e2f32e37cece971bd616664ea2053741acbed4e9c92e9d1766427718f2ecd"
TURN_START_SCHEMA_SHA256 = "a3835e8c1e942e4b358e1a670939b89918b16c4d13105a579899892b7ade6dea"

CANONICAL_WINDOWS_WORKSPACE = (
    r"D:\WORK\RESEARCH\4.GWF\g2e\.local\P5A-D2S1\execution\P5-FX-001"
)

ISOLATION_OVERRIDES = (
    "mcp_servers={}",
    "features.apps=false",
    "features.plugins=false",
    "features.remote_plugin=false",
    "features.workspace_dependencies=false",
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _toml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _validate_windows_absolute(path: str) -> str:
    p = PureWindowsPath(path)
    if not p.is_absolute() or not p.drive:
        raise ValueError("workspace path must be an absolute Windows path")
    if any(part == ".." for part in p.parts):
        raise ValueError("workspace path must not contain parent traversal")
    return str(p)


def build_config_toml(workspace_root: str = CANONICAL_WINDOWS_WORKSPACE) -> bytes:
    root = _validate_windows_absolute(workspace_root)
    input_path = str(PureWindowsPath(root) / "input.json")
    task_path = str(PureWindowsPath(root) / "TASK.md")
    result_path = str(PureWindowsPath(root) / "result.json")

    lines = [
        f"default_permissions = {_toml_quote(PROFILE_ID)}",
        "",
        "[windows]",
        "sandbox = \"elevated\"",
        "",
        f"[permissions.{PROFILE_ID}]",
        _toml_quote("description") + " = " + _toml_quote(
            "G2E P5A D2-S1 exact fixture/result authority"
        ),
        "",
        f"[permissions.{PROFILE_ID}.filesystem]",
        f"{_toml_quote(input_path)} = {_toml_quote('read')}",
        f"{_toml_quote(task_path)} = {_toml_quote('read')}",
        f"{_toml_quote(result_path)} = {_toml_quote('write')}",
        "",
        f"[permissions.{PROFILE_ID}.network]",
        "enabled = false",
        "",
    ]
    raw = "\n".join(lines).encode("utf-8")

    # Parse with stdlib TOML as an implementation-side fail-closed sanity check.
    parsed = tomllib.loads(raw.decode("utf-8"))
    if parsed.get("default_permissions") != PROFILE_ID:
        raise ValueError("default_permissions selection drift")
    if parsed.get("windows", {}).get("sandbox") != "elevated":
        raise ValueError("windows sandbox mode drift")
    profile = parsed["permissions"][PROFILE_ID]
    if profile.get("extends") is not None:
        raise ValueError("successor profile must not inherit")
    filesystem = profile["filesystem"]
    expected = {
        input_path: "read",
        task_path: "read",
        result_path: "write",
    }
    if filesystem != expected:
        raise ValueError("filesystem authority drift")
    if profile["network"].get("enabled") is not False:
        raise ValueError("network must be disabled")
    return raw


def build_contract(workspace_root: str = CANONICAL_WINDOWS_WORKSPACE) -> dict:
    root = _validate_windows_absolute(workspace_root)
    config_bytes = build_config_toml(root)
    config_sha256 = _sha256_bytes(config_bytes)

    thread_start = {
        "cwd": root,
        "approvalPolicy": "never",
        "permissions": PROFILE_ID,
    }
    turn_start_shape = {
        "threadId": "<runtime-thread-id>",
        "input": [{"type": "text", "text_sha256": TASK_SHA256}],
        "cwd": root,
        "approvalPolicy": "never",
    }

    execution_config = {
        "study_id": STUDY_ID,
        "attempt_id": ATTEMPT_ID,
        "fixture_id": "P5-FX-001",
        "workspace_root": root,
        "input_sha256": INPUT_SHA256,
        "task_sha256": TASK_SHA256,
        "harness_sha256": HARNESS_SHA256,
        "codex_release_tag": CODEX_RELEASE_TAG,
        "codex_release_commit": CODEX_RELEASE_COMMIT,
        "thread_start_schema_sha256": THREAD_START_SCHEMA_SHA256,
        "turn_start_schema_sha256": TURN_START_SCHEMA_SHA256,
        "experimental_api": True,
        "permission_profile_id": PROFILE_ID,
        "default_permission_profile_id": PROFILE_ID,
        "windows_sandbox_mode": "elevated",
        "windows_sandbox_setup_required": True,
        "windows_sandbox_setup_cwd": root,
        "windows_sandbox_readiness_required": "ready",
        "config_toml_sha256": config_sha256,
        "task_read_paths": ["input.json", "TASK.md"],
        "task_write_paths": ["result.json"],
        "runtime_support_read_policy": "exact-harness-support-only-v1",
        "network_allowed": False,
        "interactive_approval_allowed": False,
        "mcp_count_required": 0,
        "installed_app_count_required": 0,
        "thread_start": thread_start,
        "turn_start_shape": turn_start_shape,
        "turn_inherits_thread_permissions": True,
        "startup_timeout_seconds": 12,
        "turn_timeout_seconds": 90,
        "verifier_timeout_seconds": 10,
        "max_invalid_replacement_attempts": 0,
    }

    execution_config_hash = _sha256_bytes(
        json.dumps(
            execution_config,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    )

    return {
        "schema": "G2E-P5A-D2S1-PROFILE-MATERIALIZATION-v1",
        "study_id": STUDY_ID,
        "attempt_id": ATTEMPT_ID,
        "profile_id": PROFILE_ID,
        "default_permissions": PROFILE_ID,
        "windows_sandbox_mode": "elevated",
        "predecessor_closure_sha": PREDECESSOR_CLOSURE_SHA,
        "spec_qa_baseline_sha": BASELINE_SHA,
        "model_turn_executed": False,
        "fresh_outcome_consumed": False,
        "runtime_adapter_authorized": False,
        "scientific_attempt_authorized": False,
        "config_toml_sha256": config_sha256,
        "execution_config": execution_config,
        "execution_config_hash": execution_config_hash,
        "initialize_params": {
            "clientInfo": {
                "name": "g2e_p5a_d2s1_preflight",
                "title": "G2E P5A D2-S1 Preflight",
                "version": "1.0.0",
            },
            "capabilities": {"experimentalApi": True},
        },
        "permission_profile_list_params": {
            "cursor": None,
            "limit": 100,
            "cwd": root,
        },
        "thread_start_params": thread_start,
        "turn_start_shape": turn_start_shape,
        "isolation_overrides": list(ISOLATION_OVERRIDES),
    }


def verify_contract(contract: dict) -> None:
    if contract.get("schema") != "G2E-P5A-D2S1-PROFILE-MATERIALIZATION-v1":
        raise ValueError("schema drift")
    if contract.get("attempt_id") != ATTEMPT_ID:
        raise ValueError("attempt identity drift")
    if contract.get("profile_id") != PROFILE_ID:
        raise ValueError("profile identity drift")
    if contract.get("model_turn_executed") is not False:
        raise ValueError("model turn present during implementation")
    if contract.get("fresh_outcome_consumed") is not False:
        raise ValueError("fresh outcome present during implementation")
    if contract.get("scientific_attempt_authorized") is not False:
        raise ValueError("implementation must not authorize scientific attempt")
    if contract.get("runtime_adapter_authorized") is not False:
        raise ValueError("runtime adapter authorization drift")

    cfg = contract["execution_config"]
    if cfg.get("experimental_api") is not True:
        raise ValueError("experimental API negotiation missing")
    if cfg.get("permission_profile_id") != PROFILE_ID:
        raise ValueError("profile selection drift")
    if cfg.get("default_permission_profile_id") != PROFILE_ID:
        raise ValueError("default permission selection drift")
    if cfg.get("windows_sandbox_mode") != "elevated":
        raise ValueError("windows sandbox mode drift")
    if cfg.get("windows_sandbox_setup_required") is not True:
        raise ValueError("windows sandbox setup requirement drift")
    if cfg.get("windows_sandbox_readiness_required") != "ready":
        raise ValueError("windows sandbox readiness drift")
    if cfg.get("network_allowed") is not False:
        raise ValueError("network authority drift")
    if cfg.get("interactive_approval_allowed") is not False:
        raise ValueError("approval authority drift")
    if cfg.get("max_invalid_replacement_attempts") != 0:
        raise ValueError("retry budget drift")
    if cfg.get("turn_inherits_thread_permissions") is not True:
        raise ValueError("turn permission inheritance drift")

    thread = contract["thread_start_params"]
    if thread.get("permissions") != PROFILE_ID:
        raise ValueError("thread permissions missing")
    if "sandbox" in thread:
        raise ValueError("thread sandbox must be omitted")

    turn = contract["turn_start_shape"]
    for forbidden in ("sandboxPolicy", "permissionProfile", "permissions"):
        if forbidden in turn:
            raise ValueError(f"forbidden turn field: {forbidden}")

    root = cfg["workspace_root"]
    raw = build_config_toml(root)
    if _sha256_bytes(raw) != contract.get("config_toml_sha256"):
        raise ValueError("config.toml hash drift")

    recomputed = _sha256_bytes(
        json.dumps(
            cfg,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    )
    if recomputed != contract.get("execution_config_hash"):
        raise ValueError("execution config hash drift")


def _require_under(path: Path, root: Path) -> Path:
    path = path.resolve()
    root = root.resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"REFUSED_OUTSIDE_LOCAL_ROOT:{path}") from exc
    return path


def materialize(local_root: Path, output_dir: Path, workspace_root: str) -> dict:
    local_root = local_root.resolve()
    output_dir = _require_under(output_dir, local_root)
    output_dir.mkdir(parents=True, exist_ok=False)

    contract = build_contract(workspace_root)
    verify_contract(contract)

    config_bytes = build_config_toml(workspace_root)
    (output_dir / "config.toml").write_bytes(config_bytes)
    (output_dir / "P5A_D2S1_PROFILE_MATERIALIZATION.json").write_text(
        json.dumps(contract, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return contract


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--workspace-root",
        default=CANONICAL_WINDOWS_WORKSPACE,
    )
    args = parser.parse_args()

    contract = materialize(
        Path(args.local_root),
        Path(args.output_dir),
        args.workspace_root,
    )
    print(json.dumps({
        "study_id": contract["study_id"],
        "attempt_id": contract["attempt_id"],
        "profile_id": contract["profile_id"],
        "config_toml_sha256": contract["config_toml_sha256"],
        "execution_config_hash": contract["execution_config_hash"],
        "model_turn_executed": contract["model_turn_executed"],
        "scientific_attempt_authorized": contract["scientific_attempt_authorized"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
