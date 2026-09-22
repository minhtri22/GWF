# GWF — DG-P9 Relation Target Binding Handoff

## 1. Scope

This handoff records bounded DG-P9 implementation qualification.

DG-P9 makes target binding an explicit part of canonical `DocumentRelation` semantics while preserving the separation between semantic relation state and revision-level TraceLink/impact machinery.

DG-P10+ remain NOT_STARTED / NOT_AUTHORIZED. DG-W3 remains OPEN / NOT_EXECUTED. GAC remains locked until DG-W4 PASS.

## 2. Frozen input identity

- DG-P8 final formal-close HEAD: `4a93e564adf52ae0dfdffabefaef32d431bbef6d`
- DG-P9 frozen spec commit: `1a9f8737e36392c8a8db49b93c9371ceee16085f`
- DG-P9 frozen spec blob: `73e1d7c8c01ea954af2a65e1df1942b4f95738f3`
- DG-P9 pre-implementation qualification HEAD: `52ae1ebded1f9a942cee55d6d2ce061b5bcb8290`
- pre-implementation QA blob: `395b61a7121476296287fa3d085b51d42c7e4adf`

## 3. Implementation identity

- qualified implementation HEAD: `9ffd64a1e9b98ea307ed8f9682b88e26570dc208`
- qualified workflow: `35628998000` PASS

SQLite evidence:
- artifact `10653386409`
- digest `sha256:651c9a59f77d83176cbc452d39a9beebf17c27e2390ef83a96aee85ed29ea160`

PostgreSQL 17 evidence:
- artifact `10653461137`
- digest `sha256:aff7462c949ce6645bd0edc4ea130cbce884ac424a72234fc79ad8b9dc7b8ae4`

## 4. Persistence delivered

Exactly one migration:

```text
0011_v086_dg_p9_relation_binding
```

It extends only:

```text
document_relations
    + target_binding_mode
    + target_revision_or_hash
```

No new P9 table exists. No legacy row is automatically backfilled.

## 5. Binding modes delivered

Exactly two bound modes exist:

```text
LOGICAL_CURRENT
PINNED_REVISION
```

NULL remains legacy unbound absence only.

New relation declarations require an explicit legal mode and persist it atomically.

## 6. Legality matrix delivered

```text
DEPENDS_ON      current | pinned
REFERENCES      current | pinned
MUST_ALIGN_WITH current only
SUPERSEDES      pinned only
DERIVED_FROM    pinned only
VALIDATES       pinned only
IMPLEMENTS      current | pinned
GENERATED_FROM  pinned only
```

No invalidation policy can override this matrix.

## 7. Legacy binding delivered

A pre-P9 row may transition once:

```text
UNBOUND(NULL)
    ↓ governed Proposal / Approval
LOGICAL_CURRENT or PINNED_REVISION
    ↓ Audit + version increment
immutable binding
```

Rebinding is forbidden. A semantic binding change requires retire-old relation + create-new relation.

## 8. DOCUMENT resolution delivered

`LOGICAL_CURRENT` resolves the target Artifact's current Revision and immutable content hash at read time without persisting that resolution.

`PINNED_REVISION` resolves the stored exact Revision after verifying Revision ownership by the target document.

A historical pin remains resolvable and reports `is_current=false` after the target advances.

## 9. External target boundary delivered

No external resolver was added.

Non-DOCUMENT target binding fails closed until an independently qualified target-kind resolver exists. Caller-supplied opaque tokens are not accepted as verified exact provenance.

## 10. Zero-side-effect boundary delivered

Binding/resolution creates no:

- TraceLink;
- ImpactSet;
- Evidence;
- DocumentFinding;
- validity mutation;
- authority mutation;
- lifecycle mutation;
- source edit;
- propagation execution;
- binding-resolution cache.

DG-P9 resolves identity only.

## 11. Compatibility finding

F-116 is preserved as implementation evidence.

Two P8 fixtures contained phase-bound assertions that P9 columns must not exist. They were requalified to the durable P8 contract: legacy rows remain NULL-bound and P8 semantics produce no Evidence/TraceLink side effects.

No D9 fixture or runtime threshold/semantic contract was weakened.

Finding OPEN = 0.

## 12. Qualification evidence

Run `35628998000` passed:

- D9-F1..D9-F20 SQLite;
- bounded SQLite DG-P9 gate;
- P8 / Knowledge / Trace and P4-P7 targeted regressions;
- full repository regression;
- compile;
- D9-F1..D9-F20 PostgreSQL 17;
- bounded PostgreSQL DG-P9 gate;
- PostgreSQL evidence assertion.

## 13. Explicit non-scope

DG-P9 did not implement:

- relation-aware impact propagation;
- TraceLink projection;
- automatic staleness/review;
- validity mutation;
- DG-P10 classification;
- DG-P11 DocumentChangeSet;
- DG-P12 impact execution;
- DG-W3 closure;
- GAC;
- Reference Acquisition;
- G2E.

## 14. Formal-close criterion

DG-P9 is implementation-qualified at `9ffd64a1e9b98ea307ed8f9682b88e26570dc208`.

Formal close requires:

1. commit implementation QA/handoff/finding/plan/lineage package;
2. rerun the same two-backend DG-P9 workflow on that exact handoff HEAD;
3. require D9/gates on both backends and SQLite regressions/full suite/compile to PASS;
4. record exact workflow/artifact identities;
5. commit formal-close state;
6. rerun the same workflow on the final closure HEAD.

DG-P10+ remain unopened and DG-W3 remains OPEN throughout this close.


## 15. Exact-handoff qualification

The committed DG-P9 handoff HEAD `5f6ecece5bbb15c36b00a35c7a4dbb6b340e0e4e` was requalified with the same two-backend workflow.

Workflow:
- `35629583197` PASS

SQLite:
- artifact `10653762329`
- digest `sha256:b5151006d5a04a2b925e8a678f36b93e944f760d233a1ab05ebd5ebd60d5a593`

PostgreSQL 17:
- artifact `10653647093`
- digest `sha256:61d498e21dcf0ba3297aec5aa878e0e79a8a1ec9aa9ebe7f54fd54728197d996`

The exact committed handoff HEAD again passed:

- D9-F1..D9-F20 on SQLite;
- bounded SQLite DG-P9 gate;
- P8 / Knowledge / Trace / P4 / P5 / P6 / P7 regressions;
- full repository regression;
- compile;
- D9-F1..D9-F20 on PostgreSQL 17;
- bounded PostgreSQL DG-P9 gate;
- PostgreSQL evidence assertion.

**DG-P9 status: FORMALLY CLOSED.**

DG-P10+ remain NOT_STARTED / NOT_AUTHORIZED. DG-W3 remains OPEN / NOT_EXECUTED. GAC remains locked until DG-W4 PASS.
