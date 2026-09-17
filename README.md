# Governed Workflow Runtime (GWF)

GWF is a domain-neutral governed workflow runtime with artifact lineage/validity, execution/checkpoint/resume, failure recovery, gates, authority, approval and audit semantics.

Current milestone: **v0.5.1r1 PostgreSQL Equivalence Gate**. v0.6 Identity/Multi-tenancy remains blocked until the live PostgreSQL gate passes.

## Repository bootstrap

The complete v0.5.1r1 source tree is stored losslessly under `bundle/` as a checksummed `source.tar.gz` split into base64 parts. This is a connector-friendly bootstrap representation; GitHub Actions reconstructs and extracts the source before running the gate.

```bash
bash tools/bootstrap_source.sh
```

The bundle contains 116 source/config/test/data/spec/doc files. `bundle/MANIFEST.json` records every file SHA-256 plus the archive SHA-256.

## PostgreSQL gate

The workflow `.github/workflows/postgres-gate.yml` runs against a real PostgreSQL 17 service container and requires all of the following before v0.6 may start:

- the same 41 regression tests pass on SQLite and PostgreSQL;
- all 6 research reliability cases run on both backends;
- close/reopen during workflow preserves state/evidence/checkpoint;
- SQLite/PostgreSQL semantic snapshots are equivalent;
- final gate emits `v06_unblocked=true`.

No live PostgreSQL PASS is claimed until that workflow produces the required evidence.
