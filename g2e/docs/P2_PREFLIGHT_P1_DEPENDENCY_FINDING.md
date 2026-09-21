# G2E P2 Preflight — P1 Dependency Finding

## Status

**BLOCKING SEMANTIC FINDING — P2 adjudicator must not open until remediated.**

## Baseline

- P1 qualified implementation: `2fc077f8bc84f8dbdb42c180b3edc7af9418a6c1`
- P1 qualification: workflow `35564563403` / job `106223715948` — PASS
- current branch before finding: `2691b9fe0dd5ec525f73e3bf2d7f97842a39f303`

## P2-F01 — HIGH — OPEN — ProofObligation does not bind exact adjudication rule identity

PRD-03 requires metrics/decision rules to freeze at `PROOF_FROZEN`. PRD-05 requires adjudication to use only the frozen ProofObligation and admitted evidence and prohibits post-outcome threshold/decision semantic mutation.

P1 currently stores:

- `metric_ids`;
- `decision_thresholds`;

but has no exact `DecisionRule` object/ref describing comparator/expression/missing-data decision semantics.

Therefore two different deterministic adjudication rules can consume the same P1 ProofObligation hash. That makes no-rescue unverifiable.

### Required remediation

Before P2 adjudicator implementation:

1. add canonical `DecisionRule` schema with deterministic PASS/FAIL expressions and missing-metric behavior;
2. add required exact `decision_rule_ref` to `ProofObligation`;
3. add fail-closed schema fixtures;
4. requalify P1 exact schema implementation;
5. only then open P2 adjudicator/core implementation.

No executor/runtime/GWF/GAC work is authorized.

## Verdict

`OPEN = 0`

**PASS — P2 adjudicator dependency is now satisfied by P1.1 qualification.**
