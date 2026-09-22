# G2E P5A D2-S2 — Binary Component Lineage Adjudication

## Status

**Verdict:** PRETURN INSTRUMENT COMPONENT SKEW CONFIRMED  
**Scientific result:** NONE  
**Model turn executed:** FALSE  
**Scientific attempt consumed:** FALSE  
**D2-S2:** FORMAL-CLOSE AT PRETURN INSTRUMENT BOUNDARY  
**A3 repair of existing package:** NOT AUTHORIZED

## 1. Bound local lineage evidence

Returned artifact:

- file: `P5A_D2S2_A2_BINARY_COMPONENT_LINEAGE_20260922T035253594Z.json`
- SHA256:
  `a159435e2b7ccc60926a630f30eba2b6374dc4958d1326a161bf255adf0aa3b5`
- schema: `G2E-P5A-D2S2-A2-BINARY-COMPONENT-LINEAGE-v1`

Observed `codex.exe`:

- path resolves lexically from:
  `%LOCALAPPDATA%\Programs\OpenAI\Codex\bin\codex.exe`
- canonical path:
  `%USERPROFILE%\.codex\packages\standalone\releases\0.153.4-x86_64-pc-windows-msvc\bin\codex.exe`
- size: `309166080`
- SHA256:
  `a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8`
- ASCII mode markers:
  - `interactive-provision=true`
  - `full=true`
  - `provision-only=true`
  - `read-acls-only=false`

Observed resolved setup helper:

- only one existing candidate;
- resolver type: `canonical-package-resources`;
- path under the same canonical `0.153.4-x86_64-pc-windows-msvc` release directory;
- size: `15413040`;
- SHA256:
  `0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4`;
- markers:
  - `interactive-provision=false`
  - `full=true`
  - `provision-only=true`
  - `read-acls-only=true`

The lineage artifact records:

- `turn_start_request_sent=false`;
- `scientific_attempt_consumed=false`.

## 2. Official release comparison

GitHub release:

- tag: `rust-v0.153.4`;
- annotated tag object: `042fb41b7c813ac7999105e886b2b7aa715b5081`;
- tagged commit:
  `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`;
- publication: `2026-09-04T23:25:48Z`.

Official release asset:

`codex-windows-sandbox-setup-x86_64-pc-windows-msvc.exe`

- size: `15413040`;
- SHA256:
  `0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4`.

This matches the selected local helper exactly.

Official release asset:

`codex-x86_64-pc-windows-msvc.exe`

- size: `295408944`;
- SHA256:
  `444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b`.

This does **not** match the selected local `codex.exe` in either size or SHA256.

## 3. Exact source-tag comparison

Exact tagged source `rust-v0.153.4` / commit
`3d2ee51ca2d5db578f328aa75e20aa22c0197c9a` has:

- `windows-sandbox-rs/src/setup.rs` orchestrator `SetupMode`:
  - `Full`
  - `ProvisionOnly`
- elevated setup payload uses `SetupMode::Full`;
- setup helper parser `src/bin/setup_main/win.rs` accepts:
  - `Full`
  - `ProvisionOnly`
  - `ReadAclsOnly`.

GitHub code search scoped to `ref:rust-v0.153.4` returns zero occurrences for:

- `interactive-provision`;
- `InteractiveProvision`.

Current upstream source contains `interactive-provision`, but that is outside the frozen release tag.

## 4. Mechanism adjudication

The helper itself is not a random stale or contaminated sidecar: its bytes match the official
`rust-v0.153.4` release asset exactly.

The local `codex.exe`, however, does not match the official x86_64 Windows release executable for the
same tag, despite living under a directory labelled `0.153.4`.

Therefore the local runtime is a mixed-distribution / component-incoherent instrument:

- official `rust-v0.153.4` setup helper;
- non-official-release-byte `codex.exe` under the same nominal version directory.

That is sufficient to explain the observed protocol incompatibility:

- orchestrator emitted `interactive-provision`;
- official release helper rejected it because that variant is absent from the frozen helper protocol.

## 5. Governance consequence

D2-S2 is formal-closed at the preturn instrument boundary.

It is not scientifically valid to:

- replace only the helper with a newer one;
- patch accepted helper modes;
- rewrite `interactive-provision` to `full`;
- mutate the globally installed Codex package in place;
- retry D2-S2 after such a repair.

Those actions would be outcome-informed rescue of a failed instrument stack.

## 6. Successor direction

A new successor may be opened only as a new instrument-qualified study.

The successor should stage a complete source/release-coherent Codex bundle outside the user's global
installation and freeze all executable components before any platform or scientific qualification.

Recommended successor identity:

- study: `p5a-d2s3-release-coherent-instrument-successor`;
- attempt: `p5a-d2s3-p5-fx-001-attempt-001`.

The successor may reuse the frozen P5-FX-001 task/input semantics, but must not reuse D2-S2's instrument
identity or scientific attempt identity.

## 7. Resource hygiene

All successor VHDX execution must obey
`P5A_D2S2_EPHEMERAL_VHDX_CLEANUP_CONTRACT.md`:

- detach exact VHDX in `finally`;
- verify detached;
- preserve VHDX/evidence files;
- release transient drive letter on every exit path.
