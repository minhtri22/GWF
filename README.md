# Governed Workflow Runtime v0.8.1 — Product Lifecycle & Process Inspector

v0.8.1 closes the pre-UAT lifecycle and observability gaps while preserving every v0.7/v0.8 invariant.

## New in v0.8.1

- Tenant-scoped Domain Package Registry.
- Immutable domain revisions: DRAFT -> VALIDATED -> PUBLISHED.
- Project creation pinned to one published domain revision.
- No silent domain upgrade for existing projects.
- Process Inspector with current phase, complete generation/attempt history and current lineage.
- Phase Inspector with run, inputs, outputs, evidence, gates, failure, checkpoint and chronological events.
- Product APIs for domain lifecycle, process history and per-phase inspection.
- GitHub Pages UAT simulation for Create Domain, Publish Domain, New Project and Phase Inspector.

## Static UAT boundary

GitHub Pages is still non-authoritative. Lifecycle mutations are stored in browser localStorage and clearly marked UAT. Real domain/project lifecycle is separately implemented and tested in FastAPI/PostgreSQL.

## Live gate

export GWR_TEST_DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME
export PYTHONPATH=src
python tools/run_v081_gate.py --out evidence/v0.8.1/live_gate

Acceptance requires the full v0.8 regression chain plus v0.8.1 lifecycle/process tests on SQLite and PostgreSQL 17, UAT build validation and compileall.

See spec/13-product-lifecycle-process-inspector-v0.8.1.md and docs/HANDOFF_V0.8.1.md.
