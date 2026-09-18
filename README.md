# Governed Workflow Runtime v0.7 — Distributed Runtime

GWR v0.7 adds durable multi-worker execution on top of the v0.6 identity/multi-tenancy and v0.5.1 PostgreSQL-verified research runtime.

## New in v0.7

- Database-backed durable job queue.
- Worker registration, capability/resource inventory and heartbeat.
- Lease token + expiry ownership model.
- Worker crash recovery with ABANDONED run/attempt evidence and requeue.
- At-least-once execution with exactly-once authoritative effect commits by effect_key.
- CPU/memory/GPU resource matching and capability labels.
- Global resource_conflict_keys reservation across workers.
- Durable scheduler events and audit.
- Migration 0003_v07_distributed_runtime for SQLite and PostgreSQL.
- Chaos probes for lease loss, crash/retry and duplicate delivery.

## Correctness boundary

v0.7 does not claim arbitrary external side effects are exactly-once. Worker execution may happen more than once after failure. The GWR authoritative effect ledger commits one matching effect_key once; external systems should receive the same idempotency key where supported.

## Gate

Run with PostgreSQL:

export GWR_TEST_DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME
export PYTHONPATH=src
python tools/run_v07_gate.py --out evidence/v0.7/live_gate

The milestone is complete only when V07_GATE.json is PASS and the complete v0.6 regression chain also remains PASS.

See spec/11-distributed-runtime-v0.7.md and docs/HANDOFF_V0.7.md.
