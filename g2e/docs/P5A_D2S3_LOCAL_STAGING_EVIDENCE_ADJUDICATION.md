# G2E P5A D2-S3 — Local Staging Evidence Adjudication

## Status

**Cleanup:** PASS  
**D2-S3 instrument staging:** PASS  
**Next gate:** D2-S3 PLATFORM NO-TURN PREFLIGHT  
**turn/start:** NOT AUTHORIZED  
**Scientific attempt:** NOT AUTHORIZED / NOT CONSUMED  
**Model turn:** NOT EXECUTED

## 1. Bound cleanup evidence

Artifact:

- file: `P5A_D2S2_VHDX_CLEANUP_20260922T082151420Z.json`
- SHA256:
  `d5a70d7a6d2b057405fa858b0951cbb3c24712026d538bb516ba81e783d20adf`
- schema: `G2E-P5A-D2S2-VHDX-CLEANUP-v1`
- status: `CLEANUP_PASS`
- evidence preserved: true
- VHDX deleted: false
- turn-start request sent: false
- scientific attempt consumed: false

All three historical targets existed and were detached after cleanup:

- predecessor: attached_after=false
- A1: attached_after=false
- A2: attached_after=false

No cleanup error was reported.

## 2. Bound D2-S3 staging evidence

Artifact:

- file: `P5A_D2S3_INSTRUMENT_STAGING_REPORT.json`
- SHA256:
  `21dedde191d144ad561af7e78903fce73990d8ffbb6d8bb701a34eb95e336c76`
- schema: `G2E-P5A-D2S3-INSTRUMENT-STAGING-v1`
- status: `STAGING_PASS_PLATFORM_PREFLIGHT_GATE_REQUIRED`
- release tag: `rust-v0.153.4`
- source commit:
  `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`
- global installation modified: false
- executables invoked: false
- turn-start request sent: false
- scientific attempt consumed: false

Staged Codex:

- final SHA256:
  `444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b`
- size: `295408944`
- `interactive-provision=false`
- `full=true`
- `provision-only=true`

Staged setup helper:

- final SHA256:
  `0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4`
- size: `15413040`
- `interactive-provision=false`
- `full=true`
- `provision-only=true`
- `read-acls-only=true`

Final package layout:

- `package/bin/codex.exe`
- `package/codex-resources/codex-windows-sandbox-setup.exe`

Temporary staging data was removed successfully.

## 3. Adjudication

The local staging evidence satisfies the exact post-S3-I0 staging contract.

The next admissible operation is a no-turn platform preflight against this exact staged instrument.
The preflight may start App Server, inspect Windows sandbox readiness, execute the sandbox setup RPC if
required, inspect MCP/apps/auth/profile state, and create a thread.

It MUST NOT send `turn/start`, access the task with a model turn, create `result.json`, or consume the
D2-S3 scientific attempt.

Any VHDX used by the preflight must be detached and verified detached in a `finally` path.
