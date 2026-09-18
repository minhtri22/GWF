# Governed Workflow Runtime v0.5.1 — PostgreSQL Equivalence Gate

This package is the v0.5 Production Foundation plus a strict live-PostgreSQL gate that must pass before v0.6 Identity / Multi-tenancy begins.

## Current status

**Canonical v0.5.1r1 source import: COMPLETE (116/116 files). Live PostgreSQL gate: PASS. v0.6: UNBLOCKED (not yet started).**

Verified here:

- SQLite tests: **41/41 PASS**
- Research reliability benchmark: **6/6 expected semantics PASS**
- Implementation QA: **PASS**

Not yet verified here:

- 41 tests on a real PostgreSQL instance
- 6 research cases on PostgreSQL
- mid-workflow PostgreSQL restart persistence
- SQLite/PostgreSQL semantic equivalence

The execution environment used to build this package has no PostgreSQL server, no psycopg driver, no external DSN, and cannot install the missing packages. The package does not claim a false PASS.

## Close the gate

```bash
pip install 'psycopg[binary]>=3'
export GWR_TEST_DATABASE_URL='postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require'
export PYTHONPATH=src
python tools/run_v051_gate.py --out evidence/v0.5.1/live_postgres_gate
```

Read `docs/V0.5.1_POSTGRES_GATE.md` and `docs/HANDOFF_V0.5.1.md`.

## v0.5.1r1 PostgreSQL gate hardening

The local sandbox cannot reach a PostgreSQL service, so this package still does not claim the live gate is closed. It now includes a real PostgreSQL preflight and `.github/workflows/postgres-gate.yml`, which runs the full gate against a PostgreSQL 17 service container on GitHub Actions. See `docs/V0.5.1R1_GATE_HARDENING.md`.
