# G2E P5A D2-S3 — Post-Closure Protocol Failure Decomposition

## Status

SPEC-LOCKED / POST-CLOSURE / EVIDENCE-ONLY / NO SCIENTIFIC RETRY

Prerequisite:

`P5A_D2S3_SCIENCE002_FORMAL_ADJUDICATION.md`

## 1. Question

Why did the accepted Science-002 turn fail to reach a terminal state before the runner exited with an
infrastructure/protocol failure?

This program is diagnostic only. It cannot change the closed D2-S3 verdict.

## 2. Allowed evidence

Use only already-produced Science-002 artifacts:

- `evidence/science-002/P5A_D2S3_SCIENTIFIC_RUNNER_EVIDENCE.json`;
- the exact `protocol_file` referenced by that runner evidence;
- the exact `stderr_hash_file` referenced by that runner evidence;
- `evidence/science-002/P5A_D2S3_TURN_START_SENT.marker`;
- `verification/P5A_D2S3_SCIENTIFIC_VERIFICATION.json`;
- the top-level Science-002 report;
- exact frozen source/blobs for the qualified runner/preflight/verifier;
- exact upstream `rust-v0.153.4` protocol source when needed for interpretation.

## 3. Prohibitions

MUST NOT:

- start Codex/App Server;
- send any RPC;
- send `thread/start` or `turn/start`;
- recreate or mount the Science-002 VHDX;
- alter Science-002 evidence;
- modify task/config/timeout/permission/model semantics;
- authorize a replacement D2-S3 attempt;
- infer a mechanism solely from the top-level diagnostic `Empty:`.

## 4. Mechanism classes

Adjudicate exactly one of the following only if directly supported:

1. `CLIENT_QUEUE_OR_READER_FAILURE`
2. `UNEXPECTED_SERVER_REQUEST_PATH`
3. `APP_SERVER_TERMINATION_OR_TRANSPORT_FAILURE`
4. `TURN_NOTIFICATION_MATCHING_OR_CONSUMPTION_FAILURE`
5. `SERVER_NONTERMINAL_TURN_FAILURE`
6. `OTHER_EVIDENCE_IDENTIFIED_MECHANISM`
7. `UNRESOLVED_FROM_EXISTING_EVIDENCE`

## 5. Required checks

At minimum:

- verify runner evidence SHA256 matches
  `ae60858bfd53268fbb43fb5f1166aaa3acd4fe322f23279b139412bb260b8017`;
- verify verification SHA256 matches
  `528b1fd3460c1efdd180dfab703dc264a5102d44fabf887411dc3f1bbc51c418`;
- verify marker/attempt/config linkage;
- inspect `driver_exception` exactly;
- inspect `unexpected_server_requests`;
- inspect `app_server_exit_code`;
- inspect all protocol records after accepted `turn/start`;
- inspect whether a `turn/completed` notification exists but was not consumed/matched;
- inspect stderr hashes/records without reconstructing secrets;
- map the observed failure to exact runner control flow.

## 6. Output

Produce one deterministic decomposition report with:

- evidence hashes;
- exact failure point;
- selected mechanism class;
- supporting protocol records/fields;
- alternative mechanisms ruled out;
- unresolved fields;
- whether a future successor study is scientifically justified;
- what must change prospectively before any new attempt identity is created.

No successor execution is authorized by this decomposition alone.
