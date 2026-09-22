# G2E P5A D2-S2 A2 — Setup Evidence Return Adjudication

## Status

**Verdict:** STRUCTURED SETUP FAILURE NOT YET ATTRIBUTABLE / READ-ONLY SANDBOX STATE REQUIRED  
**Scientific result:** NONE  
**Model turn executed:** FALSE  
**Scientific attempt consumed:** FALSE

## 1. Bound evidence-return artifact

Returned file:

- file: `P5A_D2S2_A2_SETUP_EVIDENCE_RETURN_20260922T032009769Z.json`
- SHA256: `6f1f178aac74037ed8ab1661b5b98beef5871f0cde0456237a52afd84fb23ceb`
- schema: `G2E-P5A-D2S2-A2-SETUP-EVIDENCE-RETURN-v1`
- bound A2 report SHA256:
  `2dd26dd7ce3a337307147c4be82da1f653ab76048abf3cba6bca7c0c8555c5d8`
- bound A2 preflight evidence SHA256:
  `984f828c4796b77d7bd125d5e5a8421c04f9b496d9117b6f1f5003d9b8a1e2c3`

Observed setup state:

- readiness before: `updateRequired`
- setup requested: `true`
- setup started: `true`
- setup completed notification: `true`
- setup mode: `elevated`
- setup success: `false`
- error code: `orchestrator_helper_exit_nonzero`
- helper status detail: `Some(1)`
- readiness after: `null`
- App Server exit code: `1`
- downstream MCP/app/auth/profile/thread gates: not reached
- result exists: `false`
- input/task unchanged: `true`
- `turn_start_request_sent=false`
- `scientific_attempt_consumed=false`

## 2. Exact frozen Codex semantics

Frozen Codex identity:

- repository: `openai/codex`
- commit: `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`
- tag lineage: `rust-v0.153.4`

In that exact source, `OrchestratorHelperExitNonzero` is defined as:

helper exited non-zero and no structured report was available.

The frozen setup orchestration attempts to read:

`CODEX_HOME/.sandbox/setup_error.json`

after helper failure. If a valid structured report exists, the surfaced failure should become the specific
`helper_*` code from that report rather than remain `orchestrator_helper_exit_nonzero`.

Therefore the current evidence is sufficient to localize the failure to the helper/report boundary but is
not sufficient to identify the actual helper mechanism.

## 3. Scientific/governance consequence

No A3 repair is authorized yet.

It would be post-hoc mechanism guessing to change:

- sandbox setup mode;
- account/group provisioning;
- firewall semantics;
- ACL semantics;
- helper launch path;
- Codex version;
- authority profile;

before inspecting the already-created frozen A2 sandbox state.

## 4. Next admissible gate

The only admissible next gate is:

`A2_SANDBOX_STATE_READONLY_EVIDENCE_RETURN`

It may inspect only the already-created A2 `CODEX_HOME/.sandbox` state and return:

- directory entry names/types/sizes/hashes;
- existence and sanitized structured content of `setup_error.json`, if present;
- existence/hash/size of `setup_marker.json`, if present;
- metadata and sanitized setup-related tail from existing `sandbox.*.log` files.

It must not invoke Codex/App Server, RPC, diskpart, helper executables, or mutate any A2 artifact.

Only after this evidence is adjudicated may either:

1. a bounded A3 mechanism-specific amendment be preregistered; or
2. the branch be formal-closed as a platform/setup incompatibility for this frozen environment.
