# GWR v0.5 Handoff

## Current state

v0.5 builds on the hardened research alpha and adds a controlled data foundation plus production-foundation abstractions. All packaged tests and QA checks pass in the current environment. The only explicitly open v0.5 infrastructure validation is live PostgreSQL execution.

## How to verify

From the project root:

```bash
python -m venv .venv
# activate the environment, then:
pip install -e ".[dev]"

PYTHONPATH=src python tools/qa_data_foundation.py
PYTHONPATH=src python tools/run_research_benchmark.py --out evidence/v0.5/benchmark_run
PYTHONPATH=src python tools/qa_v05.py
PYTHONPATH=src python tools/run_v05_foundation_acceptance.py
PYTHONPATH=src pytest -q
python -m compileall -q src tools tests
```

## Data benchmark

The package includes 12 registered datasets: three pinned public UCI-derived snapshots and nine deterministic synthetic fixtures. The benchmark contains six end-to-end research cases and four targeted data-quality fault cases.

Do not describe these as an external real-world pilot. They are controlled development/reliability data.

## PostgreSQL handoff gate

In an environment with PostgreSQL and `psycopg>=3`:

1. create an isolated test database;
2. instantiate the runtime with a `postgresql://...` target;
3. apply migrations;
4. run equivalent kernel persistence/governance/checkpoint tests;
5. rerun the complete research benchmark;
6. compare terminal outcomes, artifact validity, approvals, checkpoints and audit invariants against SQLite;
7. test process restart and concurrent optimistic-version conflicts;
8. retain the DB logs and benchmark summary as v0.5.1 evidence.

Until this is done, PostgreSQL is code/contract-ready but not live-validated.

## Open items after v0.5

- S3-compatible `ObjectStore` implementation and failure/retry tests.
- Real secondary scholarly provider wired into the failover chain.
- OpenTelemetry exporter + centralized metrics/tracing backend.
- OIDC/WebAuthn and tenant model (planned for identity/multi-tenancy phase).
- Distributed queue/workers/leases and chaos recovery.
- Larger and domain-diverse datasets plus eventual external pilot data.

## Safety of continuation

Do not weaken the existing semantic acceptance benchmark while implementing platform infrastructure. A storage/provider/observability change that alters the expected PASS / scientific FAIL / PIVOT behavior must be treated as a regression until explained by an explicit domain/protocol revision.
