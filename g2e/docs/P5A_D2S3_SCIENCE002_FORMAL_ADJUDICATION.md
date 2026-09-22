# G2E P5A D2-S3 — Science-002 Formal Adjudication

## Status

**Scientific verdict:** INVALID  
**Terminal class:** TERMINAL_INVALID_INFRASTRUCTURE_PROTOCOL_FAILURE  
**Scientific attempt consumed:** TRUE  
**Retry budget:** 0  
**Replacement attempt authorized:** FALSE  
**D2-S3 status:** FORMALLY CLOSED / NO RETRY

## 1. Bound Science-002 report

- file: `P5A_D2S3_SCIENTIFIC_EXECUTION_REPORT.json`
- SHA256:
  `09e71058bd9e9b4b4fd2e5c4f5f0c412c228932fa183d08dc7d6df4d0fc5e712`
- source HEAD:
  `31994ea87f1b737ef6d0e87cb73d31189ffc26db`
- attempt:
  `p5a-d2s3-p5-fx-001-attempt-001`
- execution config:
  `df5308888eac7fa0b876f2cd68a51d0f2dd80a1b7c6d556cb04c854067b86e81`
- R2 report SHA256:
  `b24af8e5261ba8e5a90605e7a9b9d63c0025f37650f9a4e657cdaafd76b0545e`
- R2 evidence SHA256:
  `87f18cf15f06eb1bc3e0a9e28f76e3208b2c082c3cd458221242d65db7b8cc28`

## 2. Observed execution facts

The report establishes:

- runner exit code = 2;
- verifier exit code = 0;
- durable attempt consumption = true;
- `turn/start` request sent = true;
- `turn/start` accepted = true;
- turn id present;
- turn terminal = false;
- turn timeout = false;
- infrastructure/protocol failure = true;
- result absent;
- authority violation = false;
- evidence integrity valid = 1;
- attempt attribution valid = 1;
- mutation scope valid = 1;
- executor_completed = null;
- result_schema_valid = null;
- result_values_correct = null.

The exact VHDX was dismounted successfully and verified detached.

## 3. Frozen decision-rule application

The preregistered D2-S3 scientific rule states:

- PASS requires all six scientific metrics = 1;
- FAIL requires an attributable structurally valid execution with substantive task metric failure;
- missing/conflicting/infrastructure evidence is INVALID.

Science-002 cannot be PASS because executor completion and result metrics are absent.

Science-002 cannot be substantive FAIL because the executor did not reach terminal completion and no
result was produced for task-level adjudication.

The verifier explicitly identifies `infrastructure_or_protocol_failure=true`.

Therefore the only admissible verdict is:

`INVALID`

with terminal reason:

`TERMINAL_INVALID_INFRASTRUCTURE_PROTOCOL_FAILURE`.

Verifier exit code 0 means verification completed successfully; it is not a scientific PASS.

## 4. Attempt-consumption consequence

The frozen consumption boundary is the durable marker created immediately before the sole
`turn/start` transport write.

Science-002 crossed that boundary.

The report records:

- `scientific_attempt_consumed=true`;
- `turn_start_request_sent=true`;
- `turn_start_accepted=true`;
- retry budget = 0;
- replacement attempt authorized = false.

Therefore:

- D2-S3 MUST NOT be rerun;
- no wrapper/runner repair may authorize another D2-S3 attempt;
- no timeout extension, event-loop repair, protocol patch, alternate harness, or second model turn may
  be applied to this attempt;
- Science-001 remains pre-dispatch INVALID evidence and does not alter Science-002 consumption.

## 5. Capability consequence

D2-S3 does not produce qualifying functional evidence for:

- `repository_read`;
- `repository_write`.

The D2-S3 structural official-harness qualification remains valid only at its previously qualified
structural/control-plane scope.

No functional capability promotion or runtime-adapter admission is authorized from Science-002.

## 6. Root-cause boundary

The top-level report is sufficient for the scientific verdict but not for exact mechanism attribution.

The diagnostic `Empty:` is not sufficient evidence to conclude whether the non-terminal path arose
from:

- local RPC queue/reader behavior;
- an unexpected server request;
- an App Server termination/transport condition;
- a notification-consumption bug;
- another protocol/runner mechanism.

No mechanism is selected here.

## 7. Formal close

D2-S3 is formally closed as:

`TERMINAL_INVALID_INFRASTRUCTURE_PROTOCOL_FAILURE / ATTEMPT_CONSUMED / NO_RETRY`.

A future scientific attempt, if justified, must use a new successor study identity and a new attempt
identity after an evidence-only post-closure protocol decomposition. It must not be presented as a
retry or repair of D2-S3.
