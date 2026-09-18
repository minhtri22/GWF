# GWR v0.7 — Distributed Runtime

## Objective

v0.7 moves execution ownership out of a single process while preserving the correctness properties proven through v0.6.

The runtime uses a durable database queue and leases. Execution is at-least-once. Authoritative side effects use a separate idempotent effect ledger so repeated delivery cannot create more than one committed GWR effect.

## State model

Distributed job states:

READY -> LEASED -> RUNNING -> SUCCEEDED

Failure paths:

- retryable failure: RUNNING -> READY
- expired lease with budget: LEASED/RUNNING -> READY
- exhausted attempts: LEASED/RUNNING -> FAILED
- work unit returns to READY for infrastructure retry or RECOVERY when retry budget is exhausted.

## Worker ownership

A lease contains a random lease token and expiry. Only the worker holding the current token may start, heartbeat, fail, commit an effect, or finish a job. Expired or superseded tokens are rejected.

Worker heartbeat liveness is advisory. Lease expiry is the authoritative ownership boundary.

## Crash recovery

When a lease expires:

1. active execution run becomes ABANDONED;
2. attempt becomes ABANDONED;
3. work unit becomes READY when retry budget remains;
4. job is requeued and another worker may obtain a new lease.

The previous worker cannot commit after losing its lease.

## Idempotent effects

effect_commits(effect_key) is unique. A repeated delivery with the same job, key, and payload returns the existing result. Payload drift raises IdempotencyConflict.

This provides exactly-once authoritative effect commit, not a claim of exactly-once arbitrary external execution. External providers should receive the same effect/idempotency key when they support it.

## Resource scheduler

Workers publish total CPU, memory and GPU capacity plus capability labels/workunit types. Jobs publish required resources/capabilities. The scheduler only leases fitting jobs and also honors existing GWR resource_conflict_keys globally across active distributed jobs.

## Persistence

Migration 0003_v07_distributed_runtime adds worker_nodes, distributed_jobs, job_attempts, effect_commits and scheduler_events.

All queue, lease, attempt, effect and scheduler state is durable in SQLite/PostgreSQL.

## Exit gate

v0.7 is accepted only if the v0.6 full gate remains PASS; distributed tests pass on SQLite and live PostgreSQL 17; worker crash/requeue is demonstrated; duplicate delivery produces one effect commit; stale lease is rejected; resource scheduling and conflict reservation pass; and compileall passes.
