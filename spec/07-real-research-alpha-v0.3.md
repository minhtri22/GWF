# v0.3 Real Research Alpha

## Objective
Replace the synthetic acceptance executor with concrete research adapters and execute a real, bounded computational replication through the 17-phase governed workflow.

## Adapters
- `PaperWebRetriever`: live HTTP retrieval probe plus provenance-stamped cache fallback.
- `BinomialCoverageExperimentRunner`: exact finite-sample binomial coverage calculation for Wilson and Wald 95% confidence intervals.
- `StatisticalVerifier`: precommitted MAE thresholds plus an exact paired sign test over the fixed design grid.
- `RealResearchExecutor`: maps the adapters into all 17 research phases and emits structured artifacts/evidence only.

## Real hypothesis
For `n ∈ {10,20,40}` and `p = 0.01,...,0.99`, the 95% Wilson score interval will have at least 20% lower mean absolute coverage error from nominal 0.95 than the 95% Wald interval, with lower MAE at every tested n and paired sign-test `p < 0.05`.

This is intentionally a replication hypothesis. The statistical-method claim is prior art; v0.3 tests whether the runtime can execute a real evidence-bearing research cycle without presenting established prior work as novel.

## Failure and recovery path
The first experiment plan intentionally begins with a minimal three-point pilot grid. The protocol has already committed to a minimum of nine pilot parameter points. The pilot therefore detects a real protocol/plan mismatch (`pilot_degenerate`). The runtime:

1. records `FailureRecord`;
2. confirms `experiment_plan` as the root;
3. computes the affected subgraph;
4. creates `RecoveryPlan` and checkpoint;
5. resumes at phase 06;
6. revises only the experiment plan/affected descendants;
7. reruns preflight and pilot;
8. continues to main experiment.

The run also attempts a genuine live HTTP literature probe. If the host blocks outbound Python HTTP, `source_unavailable` is recorded, checkpointed and retried using the provenance-stamped source cache.

## Scientific decision semantics
`PASS` is protocol-scoped, not a claim of universal truth. The fixed p-grid is a designed evaluation set rather than a random sample from a population of p values. The sign test is therefore secondary; the primary decision is the precommitted deterministic coverage-error threshold.
