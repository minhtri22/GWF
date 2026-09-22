# G2E P5A D2-S2 A2 — Sandbox State Mechanism Adjudication

## Status

**Verdict:** BINARY-COMPONENT LINEAGE / COHERENCE DIAGNOSTIC REQUIRED  
**Scientific result:** NONE  
**Model turn executed:** FALSE  
**Scientific attempt consumed:** FALSE  
**A3 implementation:** NOT AUTHORIZED

## 1. Bound sandbox-state evidence

Returned artifact:

- file: `P5A_D2S2_A2_SANDBOX_STATE_RETURN_20260922T034154440Z.json`
- SHA256: `f74b1007c8a08268961b4b3286ec150025c1d6183798c689e2a6ce5a0b399be7`
- schema: `G2E-P5A-D2S2-A2-SANDBOX-STATE-RETURN-v1`
- bound setup evidence-return SHA256:
  `6f1f178aac74037ed8ab1661b5b98beef5871f0cde0456237a52afd84fb23ceb`

Observed local sandbox state:

- `.sandbox` exists;
- only one immediate file exists: `sandbox.2026-09-22.log`;
- `setup_error.json` does not exist;
- `setup_marker.json` does not exist;
- the one setup-relevant log line is:

  `helper_request_args_failed: failed to parse payload json: unknown variant interactive-provision, expected one of full, provision-only, read-acls-only`

- `turn_start_request_sent=false`;
- `scientific_attempt_consumed=false`.

## 2. Frozen-source comparison

Frozen Codex source identity:

- repository: `openai/codex`
- commit: `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`
- release lineage: `rust-v0.153.4`

At that exact commit:

1. app-server `windowsSandbox/setupStart(mode=elevated)` resolves to
   `codex_core::windows_sandbox::run_windows_sandbox_setup`;
2. elevated mode resolves to `run_elevated_setup`;
3. `codex-rs/windows-sandbox-rs/src/setup.rs` serializes the elevated
   `ElevationPayload` with `SetupMode::Full`;
4. that orchestrator-side `SetupMode` enum contains only:
   - `Full`
   - `ProvisionOnly`
5. the setup helper parser in
   `codex-rs/windows-sandbox-rs/src/bin/setup_main/win.rs` accepts:
   - `Full`
   - `ProvisionOnly`
   - `ReadAclsOnly`

Thus the frozen source call chain does not explain an emitted payload mode
`interactive-provision`.

## 3. Unfrozen component discovered

The existing G2E qualification froze and hashed `codex.exe`, but it did not freeze/hash
`codex-windows-sandbox-setup.exe`.

At the exact frozen Codex commit,
`helper_materialization::bundled_executable_path_for_exe` resolves helper binaries from locations
adjacent to the running executable or under `codex-resources`, with direct sibling priority.

Therefore the setup helper is an executable component outside the previously frozen single-binary hash
boundary.

## 4. Governance consequence

It is not scientifically valid to repair the mode string, change setup mode, upgrade Codex, or alter
sandbox authority yet.

The next admissible question is whether the actual local executable set is internally coherent:

- exact `codex.exe` hash/version;
- every helper candidate the frozen resolver can choose;
- exact resolved helper candidate;
- helper hash/version;
- mode markers present in each binary.

If the local helper is mismatched, A3 may be a bounded component-coherence repair while preserving
scientific semantics.

If the binaries are coherent but `codex.exe` itself contains behavior inconsistent with its claimed
source lineage, the source/binary provenance contract must be reopened instead.

## 5. Next gate

`A2_BINARY_COMPONENT_LINEAGE_READONLY_DIAGNOSTIC`

No A2 rerun and no A3 implementation before that gate is adjudicated.
