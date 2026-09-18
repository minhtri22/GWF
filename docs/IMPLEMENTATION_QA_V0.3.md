# Implementation QA — GWR v0.3 Real Research Alpha

## Final QA result
**PASS**

## Test evidence
- Pytest: **25/25 PASS**
- Python compileall: **PASS**
- Overall line coverage: **87%**
- `real_research.py` line coverage: **92%**
- Kernel implementation QA: **19/19 canonical primitives mapped**, 22 schema tables, 38 required API/service methods checked, 0 errors.
- Research domain validation: **17 phases, 19 artifact types, 17 gate types, 52 failure types, 0 errors, 0 warnings.**
- v0.3 real-run QA: **PASS, 0 errors.**

## Real run evidence
- terminal status: `COMPLETED`
- research outcome: `PASS`
- lineage generation: `1`
- phase executions: `21`
- checkpoints: `58`
- gates: `18`
- failures: `2`, both resolved
- semantic recovery plans: `1`
- current artifacts: `18`
- audit events: `340`

### Failure/recovery evidence
1. `source_unavailable` — live Python HTTP literature probe failed in the QA environment; runtime checkpointed and retried with the provenance-stamped cache. Resolved.
2. `pilot_degenerate` — initial three-point pilot violated the precommitted minimum pilot-grid size. Root confirmed at `experiment_plan`; affected subgraph invalidated; RecoveryPlan created; resume occurred at phase 06; generation incremented to 1; rerun passed. Resolved.

## Scientific computation evidence
Primary exact grid: 297 `(n,p)` design points.

Verifier output:
- relative Wilson MAE reduction vs Wald: `0.8810606206638314`
- Wilson lower MAE for every tested n: `true`
- positive pointwise improvements: `230`
- negative: `30`
- ties: `37`
- exact two-sided sign-test p-value: `2.307106511082338e-39`
- precommitted minimum relative reduction: `0.20`
- verifier verdict: `PASS`

## QA boundaries
This QA proves the packaged runtime, orchestration, recovery and exact computational experiment behaved as specified in this environment. It does not establish production readiness, universal superiority of one interval under every decision criterion, or independent external replication.
