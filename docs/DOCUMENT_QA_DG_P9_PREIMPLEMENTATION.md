# GWF — DG-P9 Pre-Implementation Document QA

## 1. QA identity

**Item:** DG-P9 — Logical-current vs pinned-revision binding  
**Subject:** docs/DG_P9_RELATION_TARGET_BINDING_SPEC.md  
**Subject commit:** 1a9f8737e36392c8a8db49b93c9371ceee16085f  
**Subject blob:** 73e1d7c8c01ea954af2a65e1df1942b4f95738f3  
**Dependency base:** DG-P8 final formal-close HEAD 4a93e564adf52ae0dfdffabefaef32d431bbef6d  
**Dependency final exact-head workflow:** 35622798852 PASS  
**Final SQLite artifact:** 10650208254  
**Final PostgreSQL artifact:** 10649124278  
**QA type:** pre-implementation semantic/dependency qualification  
**Implementation executed:** NO

## 2. Governing requirement verification

Documentation Integrity §10 requires two semantically distinct target-binding modes:

~~~text
LOGICAL_CURRENT
PINNED_REVISION
~~~

It explicitly requires VALIDATES never to float and requires exact identity for GENERATED_FROM.

The roadmap requires DG-P9 to establish this distinction after DG-P8 and before relation-aware impact work.

## 3. Persistence-fit verdict

PASS.

Binding is part of the semantic meaning of an existing document_relations row.

A separate binding table would split one relation's canonical meaning across two current-state stores.

The minimal future persistence change is therefore:

~~~text
extend document_relations
    + target_binding_mode
    + target_revision_or_hash
~~~

No new P9 table is justified.

No trace_links schema change is justified.

## 4. Legacy P8 compatibility QA

PASS.

Existing P8 rows were created before binding semantics existed.

They must not be silently defaulted to either mode.

Frozen rule:

~~~text
target_binding_mode = NULL
    means
P8 semantic relation exists
but P9 binding is not yet resolved
~~~

NULL is transitional absence, not a third legal binding mode.

## 5. Binding immutability QA

PASS.

Legacy rows may receive one explicit governed binding.

After binding, mode/pin are immutable.

Rebinding would rewrite historical graph meaning and is therefore forbidden.

A semantic binding change requires retire-old + create-new relation.

## 6. Relation-type legality QA

PASS.

Frozen matrix:

| Relation | LOGICAL_CURRENT | PINNED_REVISION |
| --- | --- | --- |
| DEPENDS_ON | ALLOWED | ALLOWED |
| REFERENCES | ALLOWED | ALLOWED |
| MUST_ALIGN_WITH | ONLY | FORBIDDEN |
| SUPERSEDES | FORBIDDEN | REQUIRED |
| DERIVED_FROM | FORBIDDEN | REQUIRED |
| VALIDATES | FORBIDDEN | REQUIRED |
| IMPLEMENTS | ALLOWED | ALLOWED |
| GENERATED_FROM | FORBIDDEN | REQUIRED |

This prevents invalidation_policy from being used as a back door to weaken identity semantics.

## 7. VALIDATES non-floating proof

PASS.

VALIDATES is evidence for one exact target state.

For DOCUMENT target:

~~~text
target_ref = governed document Artifact ID
target_revision_or_hash = exact Revision ID
resolver returns Revision.content_hash
~~~

When the target gets a new revision, the old relation remains historical evidence for the old revision only.

No automatic copy, float, or new Evidence is allowed.

## 8. GENERATED_FROM exactness proof

PASS.

GENERATED_FROM is PINNED_REVISION only.

For DOCUMENT target, immutable Revision ID plus immutable revision content hash establishes exact identity.

For non-document targets, a qualified target-kind resolver must prove an immutable identity/digest.

An unverified caller-provided opaque token is insufficient.

## 9. DERIVED_FROM exactness QA

PASS.

DERIVED_FROM is pinned because derivational provenance must preserve which target state was actually used.

A later target revision can be compared against the pin by future impact logic.

Floating would erase origin identity.

## 10. SUPERSEDES exactness QA

PASS.

SUPERSEDES is pinned because the source replaces one exact prior target state.

It must not float to a revision created after the supersession declaration.

P9 still performs no authority or lifecycle mutation.

## 11. MUST_ALIGN_WITH currentness QA

PASS.

MUST_ALIGN_WITH is LOGICAL_CURRENT only.

Its semantic obligation is continuing alignment with the current governed target.

Pinning to historical state could incorrectly show clean alignment after the target contract advances.

## 12. Dual-mode relation QA

PASS.

DEPENDS_ON, REFERENCES and IMPLEMENTS support both modes because each has legitimate current-following and version-scoped interpretations.

Mode remains explicit; no default is inferred from relation type.

## 13. Native DOCUMENT resolution QA

PASS.

Existing Artifact/Revision primitives are sufficient.

LOGICAL_CURRENT resolves:

~~~text
target Artifact
  -> current_revision_id
  -> exact Revision
  -> immutable content_hash
~~~

PINNED_REVISION verifies that the pinned Revision exists and belongs to exactly the target Artifact.

No new resolver persistence is needed.

## 14. Resolution snapshot / TOCTOU QA

PASS.

A LOGICAL_CURRENT resolver result must expose exact current Revision ID, content hash and target Artifact version at resolution time.

That result is a read snapshot only.

P9 does not promise the target remains current for a later separate operation.

A downstream governed consumer must freeze the exact resolved identity in its own scope.

## 15. External target fail-closed QA

PASS.

Core GWF currently has no single generic exact/current resolver for SOURCE_CODE, SCHEMA, API, WORKFLOW, DATASET, STUDY_LOCK or OTHER_ARTIFACT.

Therefore P9 may not claim those bindings resolved without an independently qualified target-kind resolver.

No opaque caller assertion becomes exact provenance merely because it was stored.

## 16. TraceLink boundary QA

PASS.

Existing TraceLink:

- remains revision-level operational/provenance state;
- is not binding evidence;
- cannot backfill a relation;
- cannot prove VALIDATES/GENERATED_FROM exactness.

P9 resolution stops at exact target identity.

No TraceLink projection is authorized.

## 17. Zero propagation-side-effect QA

PASS.

Binding or resolving a relation must not:

- create TraceLink;
- create ImpactSet;
- mutate Revision validity;
- create Evidence;
- create DocumentFinding;
- mutate authority/lifecycle;
- edit source documents.

A LOGICAL_CURRENT target revision change changes only the next resolver result.

Relation-aware review/staleness remains DG-P12+ work.

## 18. No binding-cache QA

PASS.

Persisting the latest LOGICAL_CURRENT resolution would risk converting a float into stale pseudo-pin state.

No canonical binding cache table is justified.

Consumers requiring attributable snapshots must persist them in their own governed artifact/evidence/change-set context.

## 19. Frozen fixture adequacy

D9-F1 through D9-F20 cover:

- mode distinction;
- no legacy backfill;
- one-time governed binding;
- no rebind;
- per-relation legality;
- pinned target ownership integrity;
- current DOCUMENT resolution;
- historical pin resolution;
- VALIDATES no-float;
- GENERATED_FROM exactness;
- external resolver fail-closed;
- zero TraceLink/impact/validity side effects;
- no later-wave state.

**Fixture verdict: ADEQUATE.**

## 20. Finding adjudication

- F-105 — roadmap/finding snapshot still cited P8 handoff evidence rather than final closure evidence: resolved.
- F-106 — binding could be split into a second current-state table: rejected; extend document_relations.
- F-107 — silent legacy default/backfill risk: resolved by NULL-as-unbound transition and explicit governed binding.
- F-108 — relation-type binding ambiguity: resolved by frozen legality matrix.
- F-109 — VALIDATES/GENERATED_FROM float risk: resolved by PINNED-only exactness.
- F-110 — derivation/supersession historical identity loss: resolved by PINNED-only DERIVED_FROM/SUPERSEDES.
- F-111 — MUST_ALIGN_WITH historical pin false-clean risk: resolved by LOGICAL_CURRENT-only.
- F-112 — rebinding historical meaning risk: resolved by one-time binding + no-rebind.
- F-113 — external resolver provenance overclaim risk: resolved by fail-closed qualified-resolver requirement.
- F-114 — LOGICAL_CURRENT TOCTOU/implicit persistence risk: resolved by pure exact snapshot + no cache.
- F-115 — TraceLink/propagation shortcut risk: resolved by zero-side-effect resolver boundary.

All are specification/document-state resolved.

No runtime implementation has occurred.

## 21. Document QA verdict

~~~text
DG-P8 dependency                         PASS
LOGICAL_CURRENT / PINNED distinction     PASS
relation legality matrix                 PASS
VALIDATES pinned-only                    PASS
GENERATED_FROM pinned-only               PASS
DERIVED_FROM pinned-only                 PASS
SUPERSEDES pinned-only                   PASS
MUST_ALIGN_WITH current-only             PASS
DEPENDS/REFERENCES/IMPLEMENTS dual mode  PASS
legacy auto-backfill                     REJECTED
one-time governed bind                   PASS
rebind                                   REJECTED
new P9 table                             REJECTED
document_relations extension             JUSTIFIED
native DOCUMENT resolver                 PASS
external resolver without qualification  REJECTED
TraceLink projection                     REJECTED
resolver side effects                    NONE
D9-F1..D9-F20                            ADEQUATE
DG-P10+ opened                           NO
implementation                           NOT_STARTED
Finding OPEN                             0
~~~

**DG-P9 PRE-IMPLEMENTATION QUALIFICATION: PASS**
