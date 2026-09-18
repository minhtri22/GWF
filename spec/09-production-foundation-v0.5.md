# GWR v0.5 — Production Foundation Contract

## 1. Scope

v0.5 hardens the v0.4 research runtime without changing its scientific semantics. It introduces a production-storage boundary, deterministic schema migrations, content-addressed object storage, provider failover provenance, and structured observability. The existing research Domain Package and PASS / FAIL / PIVOT / checkpoint / recovery semantics remain authoritative.

The development benchmark in `benchmarks/research_reliability.yaml` is the semantic regression oracle for this milestone. Production-foundation changes MUST NOT change its expected outcomes.

## 2. Persistence contract

`create_database(target)` is the persistence entry point.

Supported targets:

- SQLite file path or `sqlite:///...` for local/development execution.
- `postgresql://...` / `postgres://...` for the PostgreSQL backend.

Repository-level invariants remain unchanged across backends:

- revision content is immutable;
- audit events are append-only;
- proposal/approval hashes are authoritative;
- optimistic version checks remain mandatory where specified;
- checkpoint/recovery state survives process restart.

The PostgreSQL implementation requires `psycopg>=3`. v0.5 contains the backend and DDL/guard contract, but the packaged QA environment did not contain a PostgreSQL server or installable psycopg driver, so live PostgreSQL integration remains an explicit open gate.

## 3. Migration contract

Migrations are ordered, checksummed, idempotently recorded in `schema_migrations`, and MUST fail if an already-applied migration ID is presented with a different checksum.

Migration `0001_v05_production_foundation` introduces:

- `schema_migrations`;
- `object_refs`;
- `provider_events`.

Legacy v0.4 state MUST remain readable after migration and existing project IDs/artifacts MUST be preserved.

## 4. Object-store contract

Large evidence blobs are separated from authoritative relational metadata.

`LocalContentAddressedStore` is the reference implementation:

- key = SHA-256(content);
- atomic write;
- deduplication by content hash;
- read-time integrity verification;
- sidecar metadata;
- database reference in `object_refs`.

The local CAS is development/single-node storage. A production deployment may replace it with an S3-compatible implementation while preserving the same hash/integrity contract.

## 5. Retrieval-provider failover

`ProviderFailoverChain` executes providers in deterministic order. Every attempt records:

- provider ID;
- outcome;
- latency;
- error if any;
- whether the final result is degraded/failover-derived.

A secondary-provider success MUST NOT erase the primary-provider failure. Attempt provenance is persisted in `provider_events` when a database is supplied.

## 6. Observability

Runtime code emits structured events through an observer interface. The packaged reference sink is JSONL.

Minimum correlation fields are domain-specific where applicable, but emitted events are designed to carry project/run/work-unit/failure context rather than free-form logs only.

Research orchestration emits lifecycle events for start/resume, phase start/pass, pause, and completion.

A later OpenTelemetry exporter may replace or complement JSONL without changing runtime semantics.

## 7. Development-data foundation

v0.5 consumes the controlled data foundation introduced before platform hardening:

- pinned public UCI-derived development snapshots for Iris, Wine, and Breast Cancer Wisconsin (Diagnostic);
- deterministic synthetic fixtures for positive effect, null effect, insufficient sample/PIVOT, target leakage, confounding, missingness, and schema drift;
- immutable SHA-256 manifests and a registry;
- a six-case end-to-end research benchmark plus four data-quality fault cases.

These datasets validate runtime behavior and reproducibility. They are not a substitute for an external real-world product pilot.

## 8. v0.5 exit gates

The milestone passes when all of the following hold:

1. Existing kernel/research tests remain green.
2. Migration from a legacy schema preserves state.
3. Content-addressed object write/read verifies the same SHA-256.
4. Provider failover retains attempt provenance.
5. Structured observability produces parseable events.
6. The complete controlled research benchmark preserves expected PASS / FAIL / PIVOT outcomes.
7. PostgreSQL backend contract is present and fails explicitly when its required driver is unavailable.

Live PostgreSQL integration is a release blocker for calling the persistence layer production-validated, but not for the v0.5 code/contract milestone in this constrained QA environment.
