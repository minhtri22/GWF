# Governed Workflow Runtime v0.6 — Identity & Multi-tenancy

GWR v0.6 adds a production-facing identity and tenant isolation layer on top of the v0.5.1 PostgreSQL-verified research runtime.

## New in v0.6

- `Tenant -> Workspace -> Project` hierarchy.
- Authoritative tenant/workspace/project memberships and role matrices.
- Scoped project authorization integrated with domain governance.
- OIDC verifier injection + persisted `(provider, issuer, subject) -> actor` binding.
- Signed/revocable runtime sessions with live membership checks.
- Cross-tenant concealment in the FastAPI surface.
- Migration `0002_v06_identity_multitenancy` for SQLite and PostgreSQL.
- Dedicated v0.6 SQLite/PostgreSQL gate while preserving the full v0.5.1 research/restart equivalence gate.

## Compatibility

Legacy v0.5 unscoped projects continue to use `actors.project_scope`. New tenant-scoped projects do **not** trust that legacy field as an isolation boundary.

## Gate

Run locally with a live PostgreSQL instance:

```bash
export GWR_TEST_DATABASE_URL='postgresql://USER:PASSWORD@HOST:5432/DBNAME'
export PYTHONPATH=src
python tools/run_v06_gate.py --out evidence/v0.6/live_gate
```

The milestone is complete only when `V06_GATE.json` is `PASS` on both SQLite and PostgreSQL and the v0.5.1 regression gate remains PASS.

See `spec/10-identity-multitenancy-v0.6.md` and `docs/HANDOFF_V0.6.md`.
