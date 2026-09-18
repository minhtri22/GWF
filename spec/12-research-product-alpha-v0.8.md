# GWR v0.8 — Research Product Alpha

## Objective

Expose the proven GWR runtime as an operator-facing research product without moving authority, truth, or recovery semantics into the UI.

## Domain SDK

The SDK provides three development operations:

- validate: run the canonical domain package validator and return structured errors/warnings;
- inspect: emit a stable summary of artifacts, workunits, gates, roles and dependency edges;
- scaffold: generate a minimal valid domain package that already satisfies GWR primitive and governance requirements.

The SDK never bypasses the kernel's validate_domain contract.

## Product read model

ProjectDashboardService derives dashboard state from authoritative persisted runtime tables. It does not create a second product database.

The read model exposes:

- project/tenant/workspace identity;
- orchestration and phase history;
- WorkUnits and Runs;
- v0.7 distributed jobs/workers;
- validity frontier;
- pending proposals and approval history;
- failures, recovery plans and failure graph;
- audit event count.

## Human approval UX contract

The live API supports approve and reject. Both require an authenticated session and the exact frozen proposal hash. Rejection writes an approvals row with decision REJECTED and an authenticated audit event.

The GitHub Pages UAT UI is static by design. It displays the same approval information model, but decisions are stored only in browser localStorage and are visibly marked as non-authoritative.

## Failure/recovery visualization

The product read model emits nodes and edges for:

failure -> root cause
failure -> recovery plan -> resume target

The visualization is a derived view. FailureRecord, RecoveryPlan, validity state and checkpoint remain authoritative in the runtime.

## GitHub Pages UAT

web/ contains a dependency-free static operator console. tools/build_uat_site.py validates the pinned UAT fixture and produces a .nojekyll-ready site.

Pages cannot host FastAPI. Therefore the static deployment is a UI/UAT surface, not a fake backend. Live API behavior is independently tested against SQLite and PostgreSQL.

## Exit gate

v0.8 passes only when:

1. complete v0.7 gate remains PASS;
2. v0.8 product tests pass on SQLite and live PostgreSQL;
3. Domain SDK validation/scaffold passes;
4. product dashboard aggregation passes;
5. exact-hash authenticated rejection passes;
6. failure/recovery graph data passes;
7. static UAT build validates required product surfaces;
8. compileall passes.
