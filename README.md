# Governed Workflow Runtime v0.8 — Research Product Alpha

GWR v0.8 turns the verified v0.7 runtime into an operator-facing research product alpha without weakening the distributed execution, identity, provenance, approval or recovery invariants.

## Product surface

- Domain SDK: validate, inspect and scaffold declarative domain packages.
- Product API: dashboard, runs, distributed queue, approvals, failures and recovery graph.
- Authenticated exact-hash approve/reject actions.
- Static GitHub Pages UAT console built from a deterministic research fixture.
- Project/run dashboard with phase history and distributed job state.
- Human approval review panel with payload/hash inspection.
- Failure -> root cause -> recovery -> resume visualization.

## Static UAT versus live product API

The GitHub Pages deployment is intentionally static. GitHub Pages cannot host the FastAPI runtime, so the UAT console uses a pinned demo snapshot and stores simulated approval/rejection actions only in browser local storage. The same UI information model is backed by real authenticated endpoints in src/gwr/api.py for deployment with a runtime server.

## Domain SDK

python tools/gwr_domain.py validate domains/research.workflow.yaml
python tools/gwr_domain.py inspect domains/research.workflow.yaml
python tools/gwr_domain.py scaffold my.domain --out /tmp/my.workflow.yaml

## Gate

export GWR_TEST_DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME
export PYTHONPATH=src
python tools/run_v08_gate.py --out evidence/v0.8/live_gate

v0.8 is accepted only after the full v0.7 regression chain, dedicated SQLite/PostgreSQL product tests, UI build validation and UAT snapshot checks all PASS.
