# P5A-CGW P5-FX-001 — Final adjudication

## Verdict

**INVALID — SPENT**

Attempt:

`p5a-cgw-v4-p5-fx-001-attempt-001`

was consumed under the frozen durable-marker rule.

## Frozen execution facts

- durable marker exists;
- `turn/start` request was sent;
- `turn/start` was accepted;
- turn timed out;
- no terminal completion was observed;
- no `result.json` exists;
- live MCP/browser route evidence was not admitted;
- evidence integrity metric is 0;
- mutation-scope and attempt-attribution metrics are 1.

## Why this is not PASS

PASS requires all six original P5-FX-001 metrics to equal 1 plus admitted route evidence.

Observed:

- `executor_completed = null`;
- `result_schema_valid = null`;
- `result_values_correct = null`;
- `mutation_scope_valid = 1`;
- `attempt_attribution_valid = 1`;
- `evidence_integrity_valid = 0`.

Therefore PASS is impossible.

## Why this is not substantive FAIL

The frozen FAIL rule requires a structurally valid attributable **completed execution** with a substantive task metric equal to 0.

This execution never reached terminal-completed state. The task-result metrics are `null`, not substantive zeroes. Therefore this run cannot be interpreted as task/model failure.

## Why INVALID

The frozen INVALID rule covers infrastructure/protocol/authority/evidence failure, timeout, terminal failure without admitted result, missing live MCP roundtrip, or missing metrics.

The consumed run satisfies multiple INVALID conditions:

- timeout after accepted turn/start;
- `turn_terminal = false`;
- infrastructure/protocol failure flag true;
- no admitted live MCP roundtrip;
- no result;
- evidence integrity invalid.

## Governance closure

- attempt is spent;
- retry budget remains 0;
- do not rerun V4-002;
- do not rearm the same attempt;
- do not authorize a replacement under V2R6;
- preserve V4-001 and V4-002 evidence roots;
- V2R6 functional qualification is formally closed as `SPENT_INVALID`.

Any future continuation requires a new preregistered attempt or a separately governed infrastructure study. It must not be presented as a retry of this consumed attempt.
