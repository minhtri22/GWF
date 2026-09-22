# G2E P5A D2-S4 — Post-Closure Terminal-Failure Decomposition

## Status

SPEC-LOCKED / POST-CLOSURE / EVIDENCE-ONLY / NO SCIENTIFIC RETRY

Prerequisite:

`P5A_D2S4_SCIENCE001_FORMAL_ADJUDICATION.md`

## 1. Question

Why did the D2-S4 App Server return a terminal turn with status `failed` after accepting the exact
scientific `turn/start`?

This program is diagnostic only. It cannot change the closed D2-S4 verdict.

## 2. Allowed evidence

Use only already-produced D2-S4 Science-001 artifacts:

- top-level scientific report;
- `evidence/science-001/P5A_D2S4_SCIENTIFIC_RUNNER_EVIDENCE.json`;
- exact protocol file referenced by runner evidence;
- exact stderr-hash file referenced by runner evidence, if materialized;
- `evidence/science-001/P5A_D2S4_TURN_START_SENT.marker`;
- `verification/P5A_D2S4_SCIENTIFIC_VERIFICATION.json`;
- exact frozen D2-S4 runner/client/verifier source;
- exact upstream `rust-v0.153.4` protocol source where needed to interpret terminal-failure fields.

## 3. Prohibitions

MUST NOT:

- start Codex/App Server;
- send any RPC;
- send `thread/start` or `turn/start`;
- recreate or mount the D2-S4 VHDX;
- alter D2-S4 evidence;
- modify task/config/timeout/permission/model semantics;
- authorize a replacement D2-S4 attempt.

## 4. Mechanism classes

Select exactly one only when supported by evidence:

1. `MODEL_OR_PROVIDER_EXECUTION_FAILURE`
2. `SANDBOX_OR_PERMISSION_EXECUTION_FAILURE`
3. `SERVER_INTERNAL_TURN_FAILURE`
4. `TOOL_OR_ITEM_EXECUTION_FAILURE`
5. `TURN_STATE_OR_REQUEST_SEMANTIC_FAILURE`
6. `TRANSPORT_FAILURE_REPORTED_AS_TERMINAL_FAILED`
7. `OTHER_EVIDENCE_IDENTIFIED_MECHANISM`
8. `UNRESOLVED_FROM_EXISTING_EVIDENCE`

## 5. Required checks

At minimum:

- verify top-level report SHA256
  `e98ee53c550e13dd42715c63ca6cbf887aa69396f50c90abc6637a54a3dc9536`;
- verify runner evidence SHA256
  `6e1ef9d48bf640a8a285370549771f76048e0280eaf121450f3fa6679c069f5d`;
- verify verification SHA256
  `bf0e848c1eba9e8c0bf8a74da5fcf96dbe29898ec26d1ef91d21aca13a7be01b`;
- verify marker/attempt/config linkage;
- inspect exact `turn/started` and `turn/completed`/failed records;
- inspect terminal turn error/status fields if present;
- inspect all item notifications between start and terminal failure;
- inspect unexpected server requests;
- inspect stderr-hash evidence if materialized;
- distinguish server-declared failure from client observation defects;
- map the observed failure to frozen upstream protocol semantics.

## 6. Output

Produce one deterministic decomposition report containing:

- evidence hashes;
- exact terminal-failure record;
- selected mechanism class;
- supporting protocol fields;
- alternative mechanisms ruled out;
- unresolved fields;
- whether a scientifically distinct successor study is justified;
- exact prospective change required before any new attempt identity.

No successor execution is authorized by this decomposition alone.
