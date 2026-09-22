# G2E P5A D2-S2 A2 — Windows Sandbox Setup Helper Blocker Adjudication

## Status

**Verdict:** PRETURN_BLOCKED_PLATFORM_DIAGNOSTIC_REQUIRED  
**Scientific result:** NONE  
**Model turn executed:** FALSE  
**Scientific attempt consumed:** FALSE

## 1. Bound A2 report

Returned local report:

- file: `P5A_D2S2_A2_ONECLICK_REPORT.json`
- SHA256: `2dd26dd7ce3a337307147c4be82da1f653ab76048abf3cba6bca7c0c8555c5d8`
- schema: `G2E-P5A-D2S2-A2-ONECLICK-REPORT-v1`
- source HEAD: `17bf616138433f96ee3447e8f846aad430df3771`
- qualified candidate: `70e7992080b1e21dc3626ca98daa029e02c0bca3`
- one-click blob: `c714da50f577fad5e4fdd7b64ede894330459243`
- preflight blob: `8d449867586663195a998ce6eefbcbf8a218030f`
- selected drive: `T:`
- input/task hashes: exact frozen values
- config SHA256:
  `846974f08b25b484e0b13a2c3e30dfb9134bb94b46b54b5fd7365bf54988212e`
- preflight evidence SHA256:
  `984f828c4796b77d7bd125d5e5a8421c04f9b496d9117b6f1f5003d9b8a1e2c3`
- preturn gate: FAIL
- `turn_start_request_sent=false`
- `scientific_attempt_consumed=false`

Observed report diagnostic:

`orchestrator_helper_exit_nonzero: setup helper exited with status Some(1)`

## 2. Classification

A2 cleared the prior config-serialization defect: `config_sha256` is non-null and the local preflight
evidence file was materialized.

The remaining blocker is inside the Windows sandbox setup path. The frozen preflight only enters this path
when `windowsSandbox/readiness` reports `updateRequired`, then calls `windowsSandbox/setupStart`
and waits for `windowsSandbox/setupCompleted`.

The one-click report alone does not preserve enough stage detail to determine whether:

- setup RPC started successfully;
- setup completion notification arrived;
- helper completion mode/success fields;
- readiness-after state;
- exact redacted setup error code/hash;
- any downstream gate was reached.

Therefore no mechanism repair is authorized yet.

## 3. No-rerun / no-rescue boundary

A2 is not rerun. Its local root, VHDX, report, preflight evidence, protocol log, and stderr-hash log remain
historical evidence.

Before any A3 amendment can be designed, a zero-science evidence-return diagnostic must read and verify
the already-created A2 artifacts.

The diagnostic must not:

- invoke Codex or App Server;
- call any RPC;
- mount/detach/modify any VHD/VHDX;
- mutate A2 evidence;
- authorize `turn/start`;
- authorize or consume a scientific attempt.

## 4. Next gate

`A2_WINDOWS_SANDBOX_SETUP_EVIDENCE_RETURN_DIAGNOSTIC`

Only after that evidence is adjudicated may a bounded successor amendment be considered.
