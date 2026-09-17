# Governed Workflow Runtime (GWF)

GWF is a domain-neutral governed workflow runtime with artifact lineage/validity, execution/checkpoint/resume, failure recovery, gates, authority, approval and audit semantics.

Current milestone: **v0.5.1r1 PostgreSQL Equivalence Gate**. v0.6 Identity/Multi-tenancy remains blocked until the live PostgreSQL gate passes.

## Repository status

The GitHub connector has write access to this private repository and the PostgreSQL gate workflow is being wired here. The authoritative v0.5.1r1 implementation package remains the previously QA'd release artifact; this repository must not claim source import or PostgreSQL equivalence PASS until the checked-in source and CI evidence are complete.

Local evidence from v0.5.1r1:

- SQLite regression suite: **41/41 PASS**
- Research reliability benchmark: **6/6 expected semantics**
- Kernel/implementation QA: **PASS**
- Live PostgreSQL equivalence: **NOT YET PASSED**

## PostgreSQL release gate

The intended CI gate runs PostgreSQL 17 and must prove all of the following before v0.6 may start:

- the same 41 regression tests pass on SQLite and PostgreSQL;
- all 6 research reliability cases run on both backends;
- close/reopen during workflow preserves state/evidence/checkpoint;
- SQLite/PostgreSQL semantic snapshots are equivalent;
- final gate emits `v06_unblocked=true`.

No live PostgreSQL PASS is claimed until CI produces the required evidence.
