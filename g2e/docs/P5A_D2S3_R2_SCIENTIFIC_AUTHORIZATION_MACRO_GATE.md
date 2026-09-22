# G2E P5A D2-S3 — R2 Preturn Adjudication and Scientific Authorization Macro-Gate

## Status

**R2 underlying platform preflight:** PASS  
**R2 wrapper terminal status:** INVALID due post-evidence optional-property read  
**Scientific attempt consumed:** NO  
**Macro-gate:** ZERO-SCIENCE / SUCCESSOR-ADMISSION + RUNNER-QUALIFICATION

## 1. Bound R2 local report

- schema: `G2E-P5A-D2S3-PLATFORM-NO-TURN-R2-REPORT-v1`
- file SHA256:
  `b24af8e5261ba8e5a90605e7a9b9d63c0025f37650f9a4e657cdaafd76b0545e`
- source HEAD:
  `0f0b836b395079e91add69e049e567b8577d62bb`
- qualified candidate:
  `6e12bb7f92f47819c9970794b961784c9a4ab748`
- one-click blob:
  `046291e068cc3c42bd4dcf200201ad91e38a0eeb`
- Python preflight blob:
  `ecd0af7cd487e14ea1691f4195af1d147efd0fe4`
- preflight evidence SHA256:
  `87f18cf15f06eb1bc3e0a9e28f76e3208b2c082c3cd458221242d65db7b8cc28`

The report records:

- exact input/task/config hashes;
- exact staged Codex/helper hashes;
- `preturn_gate_pass=true`;
- `turn_start_request_sent=false`;
- `scientific_attempt_consumed=false`;
- `result_exists=false`;
- exact task payload plus only `System Volume Information` support metadata;
- no unexpected root entries;
- VHDX detached after cleanup.

## 2. R2 wrapper invalidity

The top-level wrapper failed only while reading optional property `driver_exception` under PowerShell
StrictMode after the Python driver had written its evidence.

Exact driver semantics prove that `preturn_gate_pass=true` can only be written after:

1. App Server initialization;
2. Windows sandbox ready / successful elevated setup when required;
3. MCP count = 0;
4. installed/callable apps = 0;
5. authentication ready;
6. exact permission profile present and allowed;
7. successful `thread/start` with a non-empty thread id;
8. active profile absent or exact-match;
9. instruction sources empty;
10. no unexpected server request.

Any exception before those conditions sets `preturn_gate_pass=false`.

Therefore the wrapper reporting bug does not invalidate the underlying preturn platform evidence and does
not justify another local preflight run.

## 3. Material harness identity boundary

The prior D1/final-admission manifest binds exact harness:

`a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8`

D2-S3 binds official release executable:

`444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b`

Harness identity is a material AgentEquivalence dimension. The old manifest/final admission MUST NOT be
reused by substitution.

## 4. Successor structural qualification

Before D2-S3 science, CI must qualify the exact official binary by:

- downloading exact `rust-v0.153.4` Windows asset;
- verifying archive and executable SHA256;
- running `--version`;
- running `app-server --help`;
- generating version-matched JSON schemas;
- checking required protocol tokens;
- completing only `initialize/initialized`;
- executing no thread, turn, model, task or scientific fixture.

The resulting deterministic structural facts plus the bound R2 preturn evidence materialize a new
D2-S3 structural `AgentCapabilityManifest`.

## 5. Successor scientific semantics

The successor keeps P5-FX-001 scientific semantics unchanged:

- input SHA256:
  `a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6`;
- TASK SHA256:
  `4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e`;
- attempt:
  `p5a-d2s3-p5-fx-001-attempt-001`;
- metrics:
  `executor_completed`,
  `result_schema_valid`,
  `result_values_correct`,
  `mutation_scope_valid`,
  `attempt_attribution_valid`,
  `evidence_integrity_valid`;
- PASS iff all six metrics = 1;
- FAIL iff an attributable structurally valid execution has any substantive task metric
  `result_schema_valid/result_values_correct/mutation_scope_valid = 0`;
- otherwise missing/conflicting/infrastructure evidence is INVALID;
- no network;
- no interactive approval;
- read only `input.json`, `TASK.md`;
- write only `result.json`;
- turn timeout 90 seconds;
- verifier timeout 10 seconds;
- zero automatic retry.

## 6. Composite scientific one-click authorization contract

If and only if the macro-gate qualification PASSes, one local invocation may:

1. verify exact branch/head/lock/blobs;
2. verify exact staged official executable/helper;
3. verify the exact R2 top-level report SHA and exact R2 evidence SHA/content;
4. create one fresh R2-independent scientific VHDX;
5. copy only the frozen task payload;
6. create exact permission profile;
7. re-run fail-closed current platform checks through `thread/start`;
8. STOP if any preturn invariant fails;
9. send exactly one `turn/start` with the frozen TASK text;
10. record attempt-consumption marker immediately after request flush;
11. wait at most 90 seconds for terminal completion;
12. run an independent deterministic verifier;
13. emit runner/verifier/protocol hashes;
14. always detach and verify the VHDX in `finally`.

No automatic retry or rescue is authorized.

## 7. Technical-debt repair

The old R2 wrapper optional-property read may be repaired in this macro-gate using safe property lookup.
That repair is reporting-only and does not authorize or require another R2 local execution.

## 8. Macro-gate PASS

PASS requires, on exact candidate:

- official-harness structural discovery PASS;
- deterministic successor manifest/proof/final admission PASS;
- P1.5 qualification identity validation PASS;
- R2 authorization predicate tests PASS;
- scientific runner/verifier tests PASS;
- Windows PowerShell 5.1 parser/self-tests PASS;
- protected VHDX body has no bypassing `exit`;
- P1/P1.4/P1.5/P2/P3/P4 regressions PASS;
- no scientific `turn/start` executed in CI.

PASS verdict:

`D2S3_SCIENTIFIC_EXECUTION_AUTHORIZED_EXACTLY_ONCE`

Only then may the user perform one local scientific one-click execution.
