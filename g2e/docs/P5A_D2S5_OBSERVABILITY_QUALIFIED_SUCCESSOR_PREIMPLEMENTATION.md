# G2E P5A D2-S5 — Observability-Qualified Functional Successor

## Status

PREREGISTERED / DESIGN-ONLY / MODEL EXECUTION NOT AUTHORIZED

Prerequisites:

- D2-S4 remains formally closed:
  `INVALID / ATTEMPT CONSUMED / NO RETRY`.
- P5A-CODEX-OQ1:
  `CODEX_TERMINAL_ERROR_OBSERVABILITY_QUALIFIED`.
- Exact OQ1 observability blob:
  `b6d3c6fcb671dd166893edd46388c8d69dca9105`.

## 1. Identity

- study:
  `p5a-d2s5-observability-qualified-functional-successor`
- attempt:
  `p5a-d2s5-p5-fx-001-attempt-001`
- permission profile:
  `g2e_p5a_d2s3` reused as the exact previously qualified policy semantics.

This is a new scientific attempt identity. It is not a retry of D2-S4.

## 2. Scientific question

Can the exact official Codex harness complete the frozen P5-FX-001 functional qualification under the
same bounded authority contract, now with prospectively qualified terminal-error observability?

The scientific outcome target is unchanged.

## 3. Frozen task identity

Reuse exactly:

- P5-FX-001 input SHA256:
  `a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6`
- TASK.md SHA256:
  `4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e`
- official Codex SHA256:
  `444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b`
- official setup-helper SHA256:
  `0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4`

The exact P5-FX-001 task/prompt, allowed workspace mutation, independent result computation and
PASS/FAIL task semantics do not change.

## 4. Execution semantics inherited unchanged

D2-S5 MUST preserve:

- isolated NTFS VHDX;
- prestate payload only `input.json` + `TASK.md` plus allowed NTFS support metadata;
- root read authority;
- write authority only to `result.json`;
- network disabled;
- MCP/apps disabled;
- no instruction sources;
- approval policy `never`;
- queue-safe bounded polling semantics from D2-S4;
- turn wall-clock timeout = 90 seconds;
- exactly one durable attempt-consumption marker immediately before exactly one scientific
  `turn/start`;
- retry budget = 0;
- no automatic retry;
- independent verifier;
- protected VHDX cleanup in `finally`.

## 5. Sole prospective measurement change

Bind exact qualified P5A-CODEX-OQ1 component:

`scripts/g2e/p5a_codex_observability.py`

Git blob:

`b6d3c6fcb671dd166893edd46388c8d69dca9105`

The D2-S5 live protocol recorder MUST delegate protocol evidence projection to this exact component.

For `error` and `turn/completed`, primary evidence MUST preserve the OQ1-qualified privacy-safe
terminal error projection:

- `message`;
- `codexErrorInfo`;
- `additionalDetails`;
- `willRetry` when present;
- bounded misalignment fields;
- thread/turn identity;
- terminal status;
- raw protocol hash/length.

No raw credential-bearing protocol payload may be persisted.

Other protocol messages remain payload-minimal.

## 6. Adjudication semantics remain frozen

### PASS

PASS iff the original six P5-FX-001 scientific metrics all equal 1 and evidence is admitted.

### FAIL

FAIL iff execution is attributable/structurally valid and a substantive frozen task metric is 0.

### INVALID

INVALID remains applicable to:

- infrastructure/protocol failure;
- terminal failed execution without result;
- timeout;
- authority violation;
- evidence-integrity failure;
- missing required metric;
- verifier inability.

Observability does not convert a terminal `failed` turn into substantive FAIL or PASS.

Its purpose is mechanism attribution for INVALID outcomes.

## 7. New evidence-admission requirement

If any `error` notification or failed `turn/completed` is observed:

- the terminal-error projection MUST be present;
- its raw hash/length MUST bind to the same protocol record;
- thread/turn identity MUST match the active D2-S5 attempt;
- privacy-redaction metadata MUST be present for text fields.

Failure of this observability contract makes the attempt INVALID due evidence-integrity failure.

## 8. Implementation qualification required before execution

D2-S5 execution is NOT authorized by this preregistration.

A bounded implementation/zero-model macro-gate must first prove:

1. exact OQ1 blob is imported and used by the live recorder;
2. D2-S4 queue-safe behavior remains unchanged;
3. synthetic `error` notification flows through the live `RpcClient` recorder and preserves all
   required OQ1 fields;
4. synthetic `turn/completed(status=failed)` flows through the live recorder and preserves
   `turn.error`;
5. secrets and home paths remain redacted end-to-end;
6. unrelated protocol notifications remain payload-minimal;
7. one marker / one `turn/start` path only;
8. 90-second timeout remains frozen;
9. retry remains zero;
10. independent verifier remains verdict-neutral;
11. new D2-S5 admission/binding/attempt/config identities are deterministic;
12. P1/P1.4/P1.5/P2/P3/P4 regressions PASS;
13. Windows PowerShell 5.1 parser/self-tests PASS;
14. no Codex/model turn occurs in qualification.

Only an exact post-qualification execution lock may authorize one local D2-S5 model-bearing attempt.

## 9. Fresh local identity

Prospective local root:

`g2e/.local/P5A-D2S5-SCIENCE-001`

Any future execution must fail closed if that root already exists.

## 10. No-rescue boundary

After D2-S5's durable marker exists:

- no retry;
- no timeout extension;
- no prompt/task mutation;
- no permission widening;
- no observability mutation;
- no harness/provider substitution.

Any later successor requires a newly justified lineage.

## 11. Current authorization

`D2S5_DESIGN_FROZEN_IMPLEMENTATION_QUALIFICATION_REQUIRED`

Model execution remains:

`NOT AUTHORIZED`.
