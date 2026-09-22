# G2E P5A D2-S4 — Science-001 Formal Adjudication

## Status

**Scientific verdict:** INVALID  
**Terminal class:** TERMINAL_INVALID_SERVER_DECLARED_FAILED_TURN  
**Scientific attempt consumed:** TRUE  
**Retry budget:** 0  
**Replacement attempt authorized:** FALSE  
**D2-S4 status:** FORMALLY CLOSED / NO RETRY

## 1. Bound local report

- file: `P5A_D2S4_SCIENTIFIC_EXECUTION_REPORT.json`
- SHA256: `e98ee53c550e13dd42715c63ca6cbf887aa69396f50c90abc6637a54a3dc9536`
- source HEAD: `2f8e42454f87d0dbda0f4dbfa26f384fe822e2cc`
- study: `p5a-d2s4-queue-safe-scientific-successor`
- attempt: `p5a-d2s4-p5-fx-001-attempt-001`
- execution config:
  `5a933057595e051884293a8f11917f95bed422399e55fd246932d09aeb627726`
- runner evidence SHA256:
  `6e1ef9d48bf640a8a285370549771f76048e0280eaf121450f3fa6679c069f5d`
- verification SHA256:
  `bf0e848c1eba9e8c0bf8a74da5fcf96dbe29898ec26d1ef91d21aca13a7be01b`

## 2. Observed execution facts

The report establishes:

- runner exit code = 0;
- verifier exit code = 0;
- scientific attempt consumed = true;
- `turn/start` request sent = true;
- `turn/start` accepted = true;
- turn id present;
- turn terminal = true;
- terminal status = `failed`;
- turn timeout = false;
- infrastructure/protocol failure = true;
- authority violation = false;
- result absent;
- evidence integrity valid = 1;
- attempt attribution valid = 1;
- mutation scope valid = 1;
- executor_completed = null;
- result_schema_valid = null;
- result_values_correct = null.

The exact VHDX was dismounted and verified detached.

## 3. Frozen decision-rule application

The frozen D2-S4 proof inherits the P5-FX-001 rule:

- PASS requires all six scientific metrics = 1;
- FAIL requires an attributable structurally valid execution with substantive task metric failure;
- missing/conflicting/infrastructure evidence is INVALID.

The verifier defines executor completion only for a terminal `completed` turn.

Science-001 reached terminal `failed`, produced no `result.json`, and therefore has no substantive
result-schema/result-value measurement.

Thus:

- PASS is impossible;
- substantive FAIL is not established;
- missing task metrics plus infrastructure/protocol failure require INVALID.

Formal verdict:

`INVALID / TERMINAL_INVALID_SERVER_DECLARED_FAILED_TURN`.

Verifier exit code 0 means verifier execution succeeded; it does not mean scientific PASS.

## 4. Queue-safe successor result

D2-S4 achieved the mechanism-discriminating purpose inherited from D2-S3 decomposition:

- the client did not terminate on an empty one-second poll;
- the runner reached a real terminal notification;
- `turn_timeout=false`;
- runner exit code = 0.

Therefore the D2-S3 mechanism
`UNCAUGHT_QUEUE_EMPTY_IN_RPC_CLIENT_NEXT_MESSAGE`
is not the cause of D2-S4 invalidity.

The next failure layer is downstream: the App Server/turn execution path declared the turn failed.

## 5. Attempt-consumption consequence

The D2-S4 marker was crossed and the sole attempt was consumed.

Retry budget is zero and replacement attempt is not authorized.

Therefore:

- D2-S4 MUST NOT be rerun;
- no timeout extension, queue repair, wrapper repair, alternate harness or second model turn may be
  applied to this attempt;
- any future model-bearing work requires a new successor study and attempt identity.

## 6. Capability consequence

No functional capability promotion is authorized for:

- `repository_read`;
- `repository_write`.

The structural official-harness qualification remains structural-only.

## 7. Root-cause boundary

The top-level report is sufficient for scientific adjudication but not for exact terminal-failure
mechanism attribution.

The following cannot be selected without the existing protocol/stderr evidence:

- model/provider execution failure;
- sandbox/permission enforcement failure;
- malformed task/turn state failure;
- server-internal error;
- tool/item failure;
- transport failure represented as terminal failed;
- another exact App Server failure mechanism.

## 8. Formal close

D2-S4 is formally closed as:

`TERMINAL_INVALID_SERVER_DECLARED_FAILED_TURN / ATTEMPT_CONSUMED / NO_RETRY`.

The next valid step is evidence-only post-closure decomposition of the already-produced D2-S4
protocol, stderr-hash records, runner evidence and verification evidence. No model execution is
authorized by that decomposition.
