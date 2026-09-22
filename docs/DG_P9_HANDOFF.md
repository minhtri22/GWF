# GWF — DG-P9 Relation Target Binding Handoff

## 1. Scope

This handoff records bounded DG-P9 implementation qualification.

DG-P9 adds explicit target binding to canonical `DocumentRelation` state and implements pure target identity resolution.

DG-P10+ remain NOT_STARTED / NOT_AUTHORIZED. DG-W3 remains OPEN / NOT_EXECUTED. GAC remains locked until DG-W4 PASS.

## 2. Frozen input identity

- DG-P8 final formal-close HEAD: `4a93e564adf52ae0dfdffabefaef32d431bbef6d`
- DG-P8 final exact-head workflow: `35622798852` PASS
- DG-P9 authorization HEAD: `52ae1ebded1f9a942cee55d6d2ce061b5bcb8290`
- DG-P9 frozen spec commit: `1a9f8737e36392c8a8db49b93c9371ceee16085f`
- DG-P9 frozen spec blob: `73e1d7c8c01ea954af2a65e1df1942b4f95738f3`
- pre-implementation QA blob: `395b61a7121476296287fa3d085b51d42c7e4adf`

## 3. Implementation identity

- branch: `v0.8.6-dg-p9-implementation`
- qualified implementation HEAD: `91e1ae66c3e50b1ae411090b6e74290ef464c9fe`
- qualified workflow: `35796204999` PASS

SQLite:
- artifact `10724460452`
- digest `sha256:c420cf294ebb841a9ae58e29c5883949df82fa43853a68a03dd533d3d92858e2`

PostgreSQL 17:
- artifact `10723854711`
- digest `sha256:5045b161708a036073a3e508ec50b7cb8e58c727f27efa95dd12b444f1777faa`

## 4. Persistence delivered

Exactly one migration:

```text
0011_v086_dg_p9_relation_binding
```

Only `document_relations` is extended with:

```text
target_binding_mode
target_revision_or_hash
```

No new binding table, cache, event, resolution, trace-binding or projection table exists.

Legacy P8 rows are not backfilled.

## 5. Binding semantics delivered

Legal bound modes:

```text
LOGICAL_CURRENT
PINNED_REVISION
```

Legality matrix is frozen and centrally enforced.

New relations must be born with an explicit legal binding.

Legacy NULL is absence of a P9 decision, not a third mode.

## 6. One-time governed legacy binding

`BIND_DOCUMENT_RELATION` reuses existing governance primitives:

```text
Proposal -> Approval -> optimistic relation.version -> mutation -> Audit
```

Binding is one-time. Rebinding is forbidden.

## 7. DOCUMENT resolution delivered

LOGICAL_CURRENT returns the exact current Revision/content hash snapshot without persisting a pseudo-pin.

PINNED_REVISION verifies Revision ownership and continues to resolve the exact historical Revision after the target advances.

VALIDATES and GENERATED_FROM therefore cannot float.

## 8. External targets

External target kinds remain reserved vocabulary but fail closed for P9 binding/resolution without a qualified target-kind resolver.

No generic external resolver was introduced.

## 9. Side-effect boundary

P9 stops at exact resolved identity.

It does not create/mutate:

- TraceLink;
- ImpactSet;
- Revision validity;
- Evidence;
- findings;
- authority;
- lifecycle;
- source documents.

Relation-aware impact remains later work and is not opened here.

## 10. Qualification evidence

Run `35796204999` passed both backend jobs on exact implementation HEAD:

- D9-F1..D9-F20 SQLite PASS;
- DG-P9 SQLite gate PASS;
- P8/P4/P5/P6/P7/Knowledge/Trace regressions PASS;
- full regression PASS;
- compile PASS;
- D9-F1..D9-F20 PostgreSQL 17 PASS;
- P8 PostgreSQL regression PASS;
- DG-P9 PostgreSQL gate PASS.

## 11. Explicit non-scope

Not implemented:

- DG-P10 change classification;
- DG-P11 DocumentChangeSet;
- DG-P12 relation-aware impact;
- relation-to-TraceLink projection;
- binding cache;
- external target-kind resolvers;
- GAC;
- Reference Acquisition;
- G2E;
- automatic source editing.

## 12. Current formal state

```text
DG-P8                     = PASS / FORMALLY_CLOSED
DG-P9 specification       = FROZEN
DG-P9 implementation      = QUALIFIED
DG-P9 formal close        = PASS
DG-P9 overall             = FORMALLY_CLOSED
DG-P10+                   = NOT_STARTED / NOT_AUTHORIZED
DG-W3                     = OPEN / NOT_EXECUTED
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```

## 13. Exact-handoff requalification

The committed QA/handoff package HEAD `041b59ea3e4a1363df3bd4349aa97424061d6c76` was requalified by workflow `35796638275` with both jobs completed SUCCESS.

SQLite:
- artifact `10724536102`
- digest `sha256:eb7c80441605105b769da0ad227c9434c0d357aec2d67de6cdad2a6dd9e1075f`

PostgreSQL 17:
- artifact `10724685879`
- digest `sha256:a1a5ae14fc6dfc870cb41105b8d3e22cc9402fa032abe405ea0bcdc80c05f0a7`

The workflow HEAD and both artifact HEADs exactly match `041b59ea3e4a1363df3bd4349aa97424061d6c76`.

## 14. Formal-close adjudication

All frozen DG-P9 acceptance, regression, backend-equivalence, provenance and no-later-wave criteria are satisfied.

**DG-P9 status: FORMALLY_CLOSED.**

The documentation-only closure commit must be requalified on its exact HEAD with the same two-backend DG-P9 workflow. That run is validation of the closure state, not authorization for DG-P10.

DG-P10+ remain NOT_STARTED / NOT_AUTHORIZED.
