# G2E P5A D2-S3 — Scientific Execution Macro Specification

## Status

PREREGISTERED / ZERO-SCIENCE UNTIL ONE AUTHORIZED LOCAL DISPATCH

## 1. Identity

- study: p5a-d2s3-release-coherent-instrument-successor
- attempt: p5a-d2s3-p5-fx-001-attempt-001
- permission profile: g2e_p5a_d2s3
- fixture: P5-FX-001
- retry budget: zero

## 2. Exact instrument

- release tag: rust-v0.153.4
- source commit: 3d2ee51ca2d5db578f328aa75e20aa22c0197c9a
- Codex SHA256: 444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b
- helper SHA256: 0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4
- frozen turn protocol source blob: 9629a784102d9d16a93b5a2646a35ca5948b74a6

Global Codex installation is not an admissible D2-S3 scientific instrument.

## 3. Frozen task

- input SHA256: a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6
- TASK.md SHA256: 4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e
- pre-task payload: input.json and TASK.md
- only permitted task output: result.json
- optional NTFS support metadata: System Volume Information directory
- network: denied to task sandbox
- interactive approval: denied
- allowed reads: input.json, TASK.md
- allowed write: result.json only

Result JSON must contain exactly count, sum, sorted_unique_values, input_sha256 as frozen in P5-FX-001.

## 4. R2 authorization evidence

Bound top-level R2 report SHA256:
b24af8e5261ba8e5a90605e7a9b9d63c0025f37650f9a4e657cdaafd76b0545e

Bound Python R2 evidence SHA256:
87f18cf15f06eb1bc3e0a9e28f76e3208b2c082c3cd458221242d65db7b8cc28

Before scientific dispatch, the local runner MUST parse that exact evidence and require:

- correct D2-S3 study/attempt/profile/harness identities;
- preturn_gate_pass=true;
- windows_sandbox_readiness_after=ready;
- MCP/apps counts all zero;
- auth_ready/profile_present/profile_allowed=true;
- non-empty thread_id;
- empty instruction_sources;
- no driver_exception;
- no unexpected_server_requests;
- turn_start_request_sent=false;
- scientific_attempt_consumed=false;
- result_exists=false;
- input_unchanged=true and task_unchanged=true;
- exact payload set and no unexpected root entry.

Failure of any condition blocks dispatch without consuming the scientific attempt.

## 5. Successor structural qualification

The old Codex D1 manifest is not reusable because harness_ref is material and binds a337b743....

Before local dispatch, CI must execute the read-only D1 discovery probe on the official 444a3f... binary:

- codex --version;
- codex app-server --help;
- version-matched generate-json-schema;
- required protocol token inventory;
- initialize/initialized handshake.

No thread/start or model turn is permitted in that structural qualification.

A new AgentCapabilityManifest must bind the exact official harness. Functional repository_read and
repository_write remain unavailable until the D2-S3 scientific result is separately adjudicated.

## 6. D2-S3 ProofObligation and P1.5 admission

A new prospective ProofObligation must preserve the P5-FX-001 fixture, metrics and decision semantics
while replacing the old-harness proposition with the exact D2-S3 official-harness identity.

Metrics remain:

- executor_completed
- result_schema_valid
- result_values_correct
- mutation_scope_valid
- attempt_attribution_valid
- evidence_integrity_valid

PASS requires all six equal 1. Substantive zero in result_schema_valid, result_values_correct or
mutation_scope_valid is the FAIL path. Missing/conflicting metrics or infrastructure/authority failure
is INVALID. The verifier does not assign the scientific verdict.

P1.5 must qualify a new exact authority policy, qualification grant, final AgentBinding and locked
ExecutionAttemptEnvelope for the D2-S3 attempt.

## 7. Turn-start protocol

Exactly one scientific request is allowed. It must use the frozen v2 TurnStartParams surface:

- threadId = thread created in the same fresh scientific session
- input = one text UserInput containing exact TASK.md text
- cwd = isolated scientific volume root
- approvalPolicy = never

The permission profile is bound prospectively at thread/start and must remain active for the thread.
The exact official stable generated TurnStartParams schema does not expose turn-level permissions.
Therefore scientific turn/start MUST omit both permissions and sandboxPolicy and inherit the already
validated thread profile.

The official generated TurnStartParams schema must be checked on CI before authorization.

## 8. Attempt-consumption boundary

The runner writes one durable TURN_START_SENT.marker immediately before the sole turn/start transport
write. Marker creation prospectively consumes the single attempt, even if the subsequent write is
rejected or transport fails. This conservative boundary removes ambiguity and forbids retry.

No code path may create a second marker or send a second turn/start.

## 9. Fresh local scientific root

Use only:

g2e/.local/P5A-D2S3-SCIENCE-001/

with fresh 128 MiB expandable NTFS VHDX:

P5A-D2S3-SCIENCE-001-TASK.vhdx

The root must be absent before execution.

## 10. In-run pre-dispatch checks

The one local execution performs its own fresh control-plane checks before the marker:

initialize -> readiness -> conditional setup -> readiness -> MCP -> apps -> auth -> profile -> thread/start

Only after these pass may the marker be written and turn/start sent.

Thus local operation remains one invocation without weakening pre-dispatch validation.

## 11. Scientific collection

After the sole turn begins, collect without rescue:

- thread id and turn id;
- turn terminal status;
- timeout state;
- sanitized protocol hashes;
- unexpected server requests / approval requests;
- command/MCP/web activity flags;
- input/task post hashes;
- result presence/hash/size;
- workspace post inventory.

Turn wall-clock timeout remains 90 seconds. No automatic retry.

## 12. Independent verifier

The independent verifier must:

- verify exact identities and marker linkage;
- verify input/TASK unchanged;
- verify closed mutation scope;
- parse result.json strictly if present;
- require exactly four frozen keys;
- independently recompute count, sum, sorted unique values and canonical input SHA256;
- emit the six frozen metrics plus authority/infrastructure adjudication inputs;
- never assign PASS/FAIL/INVALID itself.

## 13. Resource hygiene

Every scientific VHDX path must pass through finally:

- inspect exact image;
- dismount if attached;
- verify Attached=false;
- preserve VHDX and evidence;
- fail top-level collection status if detach verification fails.

## 14. Macro qualification

One macro workflow must PASS all of the following before local scientific execution:

- bounded diff;
- Python compilation;
- static single-dispatch/no-retry QA;
- Windows PowerShell 5.1 wrapper parse;
- official release archive/binary hash verification;
- official-harness D1 structural discovery PASS;
- generated TurnStartParams schema compatibility PASS;
- deterministic successor manifest/proof/P1.5 admission PASS;
- negative admission fixtures PASS;
- R2 authorization predicate unit tests PASS;
- independent verifier tests PASS;
- P1/P1.4/P1.5/P2/P3/P4 regressions PASS.

Only after an exact lock may exactly one local scientific execution be authorized.
