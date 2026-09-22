# G2E P5A D2-S3 — Release-Coherent Instrument Successor

## Status

PREREGISTERED / ZERO-SCIENCE / NEW-INSTRUMENT-SUCCESSOR

Predecessor D2-S2 is formal-closed at the preturn instrument boundary by
`P5A_D2S2_BINARY_COMPONENT_LINEAGE_ADJUDICATION.md`.

## 1. Successor identity

- study: `p5a-d2s3-release-coherent-instrument-successor`
- attempt: `p5a-d2s3-p5-fx-001-attempt-001`
- scientific fixture: unchanged P5-FX-001
- scientific attempt: NOT AUTHORIZED
- model turn: NOT AUTHORIZED

D2-S3 is a new successor because the executable instrument identity must change.
It does not reuse the D2-S2 attempt identity.

## 2. Frozen scientific semantics

Unchanged fixture identities:

- `input.json` SHA256:
  `a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6`
- `TASK.md` SHA256:
  `4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e`

No task/result/model/retry semantics may change in D2-S3 without a separate amendment.

## 3. Candidate source/release lineage

Candidate upstream release:

- repository: `openai/codex`
- tag: `rust-v0.153.4`
- annotated tag object:
  `042fb41b7c813ac7999105e886b2b7aa715b5081`
- tagged source commit:
  `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`

Frozen source blobs:

- `codex-rs/windows-sandbox-rs/src/setup.rs`:
  `5daaa8d60dd3c29d15bf7a5e6e9447da0b19d89f`
- `codex-rs/windows-sandbox-rs/src/bin/setup_main/win.rs`:
  `1d9340c6db26d6d10c1b3edecb1c9fecc908ef1d`
- `codex-rs/windows-sandbox-rs/src/helper_materialization.rs`:
  `7532d191ead69f010f17ef48a8e0b90d2bca3e71`

Exact-tag code search must remain zero-hit for:

- `interactive-provision`;
- `InteractiveProvision`.

The tagged source contract is:

- elevated orchestrator payload: `SetupMode::Full`;
- helper accepts `Full`, `ProvisionOnly`, `ReadAclsOnly`.

## 4. Candidate official assets

### Codex archive

`codex-x86_64-pc-windows-msvc.exe.zip`

- release asset ID: `545043433`
- size: `104174469`
- archive SHA256:
  `c016b0e6968b78586919c720d2685a03712f6d5f11bcd9d6f92c91eb8c41ba16`

Expected extracted executable:

`codex-x86_64-pc-windows-msvc.exe`

- size: `295408944`
- SHA256:
  `444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b`

### Setup-helper archive

`codex-windows-sandbox-setup-x86_64-pc-windows-msvc.exe.zip`

- release asset ID: `545043423`
- size: `5562782`
- archive SHA256:
  `256c4deb16946a01a52156e8fd619baec38743ff482741767ab5fdb4079e97cb`

Expected extracted helper:

`codex-windows-sandbox-setup-x86_64-pc-windows-msvc.exe`

- size: `15413040`
- SHA256:
  `0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4`

## 5. Gate S3-I0 — official-release asset coherence audit

This is the only open gate.

It runs in CI and may:

1. download the two exact GitHub release ZIP assets;
2. verify exact archive size and SHA256;
3. extract each archive into an ephemeral CI directory;
4. locate exactly one expected executable;
5. verify extracted size and SHA256;
6. scan binary ASCII for:
   - `interactive-provision`
   - `full`
   - `provision-only`
   - `read-acls-only`;
7. emit a deterministic JSON report.

It MUST NOT:

- invoke either executable;
- run App Server;
- invoke Windows sandbox setup;
- access any model;
- touch the user's machine;
- authorize scientific execution.

## 6. S3-I0 adjudication

S3-I0 PASS requires all of the following:

- both archive hashes match official GitHub release metadata;
- both extracted binary hashes match official release metadata;
- Codex official binary does **not** contain `interactive-provision`;
- helper official binary does **not** contain `interactive-provision`;
- both contain `full` and `provision-only`;
- helper contains `read-acls-only`;
- the source-tag contract remains as frozen above.

If any binary contains `interactive-provision`, or any digest differs, verdict is:

`OFFICIAL_RELEASE_PROVENANCE_INCOHERENT`

and D2-S3 MUST STOP before local staging.

If PASS, verdict is:

`OFFICIAL_RELEASE_COHERENT_LOCAL_STAGING_REQUIRED`

Only then may a separate local staging gate be opened.

## 7. Future local staging boundary

If S3-I0 passes, local staging must create an isolated package outside global Codex installation:

`g2e/.local/P5A-D2S3-INSTRUMENT/package/`

with:

- `bin/codex.exe`;
- `codex-resources/codex-windows-sandbox-setup.exe`.

The global `%LOCALAPPDATA%\Programs\OpenAI\Codex` installation must not be modified.

## 8. Mandatory VHDX hygiene

Any later D2-S3 VHDX execution must obey
`P5A_D2S2_EPHEMERAL_VHDX_CLEANUP_CONTRACT.md`:

- exact VHDX detach in `finally`;
- verify detached before exit;
- release drive letter on PASS/BLOCKED/exception;
- preserve VHDX/report/evidence files.

## 9. No-rescue rule

D2-S3 must not be tuned until it passes.

Any observed failure is adjudicated before another successor/amendment is created.
