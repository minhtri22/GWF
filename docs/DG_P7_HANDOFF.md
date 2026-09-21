# GWF — DG-P7 Authority Claims Handoff

## 1. Scope

This handoff records bounded DG-P7 implementation qualification.

DG-P7 introduces explicit logical-document source-of-truth claims while preserving existing actor authority, Artifact/Revision identity, P5 QA/finding semantics and P6 validity projection.

DG-P8+ remain NOT_STARTED / NOT_AUTHORIZED. DG-W3 remains OPEN / NOT_EXECUTED.

## 2. Frozen input identity

- DG-W2 formal-close HEAD: `f14abb9d8d8a591558ac6d4624a498eb32164726`
- DG-P7 canonical spec commit: `f226eb8e01b2284381ba0e7cf5527518512c7ce7`
- DG-P7 canonical spec blob: `63d2252314e753b7485f1a0249dc011468be275b`
- DG-P7 pre-implementation qualification HEAD: `7a62d97a8059adb08f0ae7be44a1285d8ee18410`
- pre-implementation QA blob: `178b2939dcba47cebce2e4235f734c38b2cfc6f1`

## 3. Qualified implementation identity

- implementation HEAD: `3f993ac639c8cb3147d0dc8d888c8b5266e54914`
- workflow: `35610704812` PASS

SQLite evidence:
- artifact `10644396006`
- digest `sha256:dd838a1512d649cc1fce18d52b594699ca2e4395a2ca6cac624ba08aefd3d460`

PostgreSQL evidence:
- artifact `10644450806`
- digest `sha256:cdcb6079b3e759286161d653a6e0924988826f8aa715be0400c0ba335cd8f972`

## 4. Persistence delivered

Exactly one migration:

```text
0009_v086_dg_p7_document_authority_claims
```

Exactly one P7 current-state table:

```text
document_authority_claims
```

No authority Artifact, composition table, collision table or later-wave document-relation table exists.

## 5. Semantic ownership

```text
actor action authority
    -> existing PRIM-AUTHORITY / authority_policies

document source-of-truth authority
    -> document_authority_claims

logical owner
    -> existing governed_document Artifact

grant provenance
    -> exact existing Revision

grant/retire authorization
    -> existing Proposal / Approval

mutation history
    -> existing Audit

collision evidence
    -> existing P5 Evidence / DocumentFinding
```

## 6. PRIMARY

PRIMARY is the default one-owner mode.

The clean service rejects a transaction whose resulting effective collision cluster is invalid.

The database remains capable of representing invalid imported/concurrent state for detection and evidence.

## 7. COMPOSED

Valid same-key multi-owner state requires one exact approved frozen composition proposal.

All claims bind:

- same proposal;
- same payload hash;
- exact roles;
- exact member set.

No independent composition subsystem is created.

## 8. Backend serialization

SQLite uses existing `BEGIN IMMEDIATE`.

PostgreSQL serializes claim mutation through a project-row `FOR UPDATE` lock in the same transaction as collision evaluation and write.

D7 passed on both SQLite and live PostgreSQL 17.

## 9. Duplicate-authority detection

Invalid effective clusters can be scanned independently of clean grant paths.

Collision QA emits P5 `DUPLICATE_AUTHORITY` findings on each affected current document revision.

The finding remains non-waivable and P6 projects it to effective BLOCKED.

A non-collision scan does not emit a synthetic PASS QA record.

## 10. Claim lifetime

```text
ACTIVE -> RETIRED
```

Retirement is proposal-backed, approval-backed, optimistic-versioned and audited.

Claims remain attached to the logical document across later content revisions.

## 11. Qualification evidence

Workflow `35610704812` passed:

- D7-F1..D7-F20 on SQLite;
- bounded SQLite authority gate;
- P4/P5/P6 + governance/persistence regressions;
- full repository regression;
- compile;
- D7-F1..D7-F20 on PostgreSQL 17;
- bounded PostgreSQL authority gate.

No repair run was required.

## 12. Explicit non-scope

DG-P7 did not implement:

- DG-P8 typed document relations;
- DG-P9 LOGICAL_CURRENT/PINNED_REVISION;
- DG-P10 change classification;
- DG-P11 DocumentChangeSet;
- DG-P15 source supersession execution;
- graph propagation;
- GAC;
- Reference Acquisition;
- G2E;
- automatic source editing.

## 13. Formal-close criterion

DG-P7 is implementation-qualified at `3f993ac639c8cb3147d0dc8d888c8b5266e54914`.

Formal close requires:

1. commit implementation-QA/handoff/finding/plan/lineage package;
2. rerun the same two-backend DG-P7 workflow on the exact handoff HEAD;
3. require SQLite and PostgreSQL D7/gates plus SQLite regressions/full suite/compile to PASS;
4. record exact run/artifact identities;
5. commit formal-close state;
6. rerun the same workflow on the final closure HEAD.

DG-P8+ and DG-W3 remain unopened throughout this close.
