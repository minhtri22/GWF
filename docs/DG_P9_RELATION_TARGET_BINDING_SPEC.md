# GWF — DG-P9 Relation Target Binding Specification

## 1. Status and authorization boundary

**Item:** DG-P9 — Logical-current vs pinned-revision binding  
**Wave:** 3 — Semantic Documentation Governance  
**Specification state:** FROZEN FOR DOCUMENT QA  
**Implementation state:** NOT_STARTED  
**Authorization state:** PRE-IMPLEMENTATION SPECIFICATION / DEPENDENCY QUALIFICATION ONLY

DG-P8 is formally closed. This specification qualifies target-binding semantics for canonical document_relations.

It does not authorize schema migration, runtime implementation, TraceLink projection, impact propagation, validity mutation, DG-P10+, DG-W3 closure, GAC, Reference Acquisition or G2E.

## 2. Exact dependency evidence

DG-P9 starts from exact DG-P8 final formal-close state:

- DG-P8 final formal-close HEAD: 4a93e564adf52ae0dfdffabefaef32d431bbef6d
- DG-P8 final exact-head workflow: 35622798852 PASS
- final SQLite evidence artifact: 10650208254
- SQLite digest: sha256:f956a6481a689fb01be862cec1c700981b7f3e289e5fa5e72c5b4bcae4580613
- final PostgreSQL evidence artifact: 10649124278
- PostgreSQL digest: sha256:807c84a3188190c90db1b8b73de116575f088db2192247414422086dd222468e

Relevant exact dependency blobs:

| Artifact | Git blob |
| --- | --- |
| docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md | e50d0f17433c6f0ec57f987278a0d24a7bbd4610 |
| docs/IMPLEMENTATION_7_WAVES_PLAN.md | 0d8f388bc745223e62d7074b0318f376e3842198 |
| docs/DG_P8_TYPED_DOCUMENT_RELATIONS_SPEC.md | d6996951522caa061b29f94d1b1f4f579251adaa |
| src/gwr/document_relation.py | dcdd4e3b3862477766bd21b1142eed6219429c61 |
| src/gwr/knowledge.py | 2c4ae7f406031613c1bd885aa90b80b3f6f93606 |
| src/gwr/db.py | b9825998757423822ab7ffb22bd37dd202f3e30d |
| src/gwr/migrations.py | 791e985ae972343e5fb4c9a0163be55edf9627a0 |

## 3. Central semantic question

DG-P9 asks:

> When a semantic DocumentRelation points to a target, does the relation follow the target's current logical state, or does it bind to one exact immutable target state?

The two legal binding modes are:

~~~text
LOGICAL_CURRENT
PINNED_REVISION
~~~

They are not interchangeable.

The governing rule is:

> A relation may float only when its meaning is intentionally "follow the current governed target". Any relation whose evidence, provenance, derivation, or supersession meaning depends on exact target identity must be pinned.

## 4. Binding is part of DocumentRelation semantics

P9 rejects a separate binding subsystem.

Binding belongs to the same canonical semantic relation because changing binding changes what the relation means.

Therefore the minimal persistence decision is:

~~~text
existing document_relations
        +
target_binding_mode
target_revision_or_hash
~~~

No new P9 table is justified.

Explicitly rejected:

~~~text
document_relation_bindings
document_binding_events
document_binding_resolutions
document_binding_cache
document_trace_bindings
~~~

Historical attribution continues to reuse Proposal/Approval/Audit.

## 5. Future migration boundary

If P9 implementation is later authorized, the bounded migration may only extend document_relations with:

~~~text
target_binding_mode         nullable during P8 legacy transition
target_revision_or_hash     nullable when mode = LOGICAL_CURRENT
~~~

Conceptual migration ID:

~~~text
0011_v086_dg_p9_relation_binding
~~~

No trace_links schema change is justified.

No automatic backfill/default is allowed.

## 6. Legacy P8 relation handling

P8 relations already exist without binding fields.

P9 must not silently interpret them as LOGICAL_CURRENT or PINNED_REVISION.

After the future migration, target_binding_mode = NULL means:

~~~text
legacy semantic relation exists
but target binding is UNBOUND / NOT OPERATIONALLY RESOLVED
~~~

UNBOUND is not a third legal binding mode. It is absence of a P9 decision.

Consequences:

- no impact consumer may treat an unbound relation as resolved;
- no TraceLink may be created from it;
- no validation/reproducibility claim may rely on it;
- binding requires an explicit governed mutation.

## 7. One-time binding and immutability

For a legacy P8 row, P9 may later authorize one explicit binding completion:

~~~text
UNBOUND
   ↓
LOGICAL_CURRENT
or
PINNED_REVISION
~~~

The binding mutation must be Proposal/Approval/Audit-backed and optimistic-versioned.

Once bound:

- target_binding_mode is immutable;
- target_revision_or_hash is immutable;
- rebinding is forbidden;
- semantic change requires retire-old relation + create-new relation.

This preserves historical meaning.

## 8. Post-P9 relation creation rule

After P9 is implemented, newly created relations must be bound atomically with relation declaration.

A new ACTIVE relation may not be committed with a NULL binding.

The legacy one-time bind path exists only for relations created before P9.

## 9. Binding legality matrix

The following matrix is frozen.

| Relation type | LOGICAL_CURRENT | PINNED_REVISION | Rationale |
| --- | --- | --- | --- |
| DEPENDS_ON | ALLOWED | ALLOWED | dependency may intentionally follow current contract or one fixed version |
| REFERENCES | ALLOWED | ALLOWED | navigation may follow current target; historical citation may pin |
| MUST_ALIGN_WITH | REQUIRED / ONLY | FORBIDDEN | alignment obligation must follow current governed target rather than silently remain aligned to history |
| SUPERSEDES | FORBIDDEN | REQUIRED | supersession must identify the exact target state being replaced and must never float to a later revision |
| DERIVED_FROM | FORBIDDEN | REQUIRED | derivation must preserve which target state the source was derived from; later target change is compared against the pin |
| VALIDATES | FORBIDDEN | REQUIRED | validation is evidence for one exact target state; it must never float |
| IMPLEMENTS | ALLOWED | ALLOWED | implementation may track a current normative contract or explicitly implement a versioned contract |
| GENERATED_FROM | FORBIDDEN | REQUIRED | reproducibility requires exact immutable target identity |

No caller may override this matrix through an invalidation policy.

## 10. LOGICAL_CURRENT semantics

LOGICAL_CURRENT means:

> Resolve the stable logical target reference to its current exact target identity at read time.

For target_kind=DOCUMENT:

~~~text
target_ref = governed_document Artifact ID
        ↓
Artifact.current_revision_id
        ↓
exact Revision
        ↓
Revision.content_hash
~~~

The relation row stores:

~~~text
target_binding_mode = LOGICAL_CURRENT
target_revision_or_hash = NULL
~~~

The current revision ID is not written back into the relation.

When the target document receives a new revision, the next resolution returns the new current revision.

That floating behavior is intentional.

## 11. LOGICAL_CURRENT is identity resolution, not validity adjudication

Resolution answers:

> Which exact target state is current for this logical target?

It does not answer:

- whether the target Revision is VALID;
- whether the target lifecycle is acceptable;
- whether the source should become STALE;
- whether QA should run;
- whether impact propagation should occur.

P9 does not mutate validity.

## 12. LOGICAL_CURRENT resolution snapshot

A resolution result for DOCUMENT must expose an exact snapshot:

~~~text
relation_id
binding_mode
target_document_id
target_artifact_version
resolved_revision_id
resolved_content_hash
resolved_at
is_current = true
~~~

The snapshot is a read result, not canonical persistence.

A downstream consumer that requires stable execution semantics must freeze the returned exact identity inside its own governed scope/change set.

P9 does not guarantee that a later separate read still sees the same current revision.

## 13. PINNED_REVISION semantics

PINNED_REVISION means:

> The relation is permanently bound to one exact immutable target identity.

For target_kind=DOCUMENT:

~~~text
target_ref
    = governed_document Artifact ID

target_revision_or_hash
    = exact Revision ID
~~~

Admission must verify:

1. Revision exists;
2. Revision.artifact_id == target_ref;
3. target belongs to the same project;
4. Revision identity is immutable.

Resolution additionally returns the Revision content_hash.

The relation does not need to duplicate that hash in persistence because Revision content is immutable and revision ID already names the exact state.

## 14. Pinned historical state remains resolvable

A pinned target Revision may later become SUPERSEDED.

That does not invalidate the pin.

Resolution returns:

~~~text
resolved_revision_id = pinned revision
resolved_content_hash = immutable content hash
is_current = false
current_revision_id = newer revision
~~~

This distinction is essential for historical evidence/provenance.

P9 itself does not mark the source stale or invalid.

## 15. VALIDATES exactness

VALIDATES is PINNED_REVISION only.

For DOCUMENT targets:

~~~text
VALIDATES(source evidence document)
        ↓
exact target Revision ID
        ↓
exact target content hash
~~~

If the target later receives a new Revision:

- old VALIDATES relation remains historical evidence for the old Revision;
- it does not validate the new Revision;
- resolver reports the pin as not-current;
- P9 does not create a new VALIDATES relation;
- P9 does not copy Evidence;
- P9 does not float.

This directly satisfies the governing rule that a VALIDATES edge must never float to a later unvalidated revision.

## 16. GENERATED_FROM exactness

GENERATED_FROM is PINNED_REVISION only.

Its exact target identity must be sufficient for reproducibility.

For DOCUMENT targets, exact Revision ID plus immutable Revision content hash satisfies P9 identity binding.

For non-document targets, a qualified resolver must provide an immutable version/digest/hash.

A caller-provided opaque string is not sufficient proof by itself.

## 17. DERIVED_FROM exactness

DERIVED_FROM is also pinned.

Reason:

- source content was derived from a particular target state;
- preserving exact origin is part of provenance;
- later target change should be detectable by comparing target current state with the pin;
- floating DERIVED_FROM would erase the identity of the state actually used to create the source.

GENERATED_FROM remains stronger because it requires reproducible machine-level exactness, not merely derivational provenance.

## 18. SUPERSEDES exactness

SUPERSEDES is pinned.

A source must not "supersede whatever revision happens to be current later".

The pin identifies the exact prior target state present at the declaration.

P9 still does not transfer authority, retire P7 claims, mutate lifecycle, or archive the target.

## 19. MUST_ALIGN_WITH currentness

MUST_ALIGN_WITH is LOGICAL_CURRENT only.

The relation means the pair must remain aligned with the target's current governed state.

Pinning it to a historical revision could produce a false clean condition after the normative target advances.

Version-specific compatibility should use a relation whose semantics permit pinning, such as a version-scoped DEPENDS_ON or IMPLEMENTS.

## 20. DEPENDS_ON, REFERENCES and IMPLEMENTS dual-mode semantics

### DEPENDS_ON

- LOGICAL_CURRENT: source depends on the current target contract;
- PINNED_REVISION: source depends on an explicitly versioned target.

### REFERENCES

- LOGICAL_CURRENT: navigation/citation follows current logical target;
- PINNED_REVISION: historical/exact citation.

Neither mode alone implies stale propagation; that remains later relation-aware impact work.

### IMPLEMENTS

- LOGICAL_CURRENT: implementation document tracks current normative target;
- PINNED_REVISION: implementation describes one versioned target state.

P9 stores/resolves identity only.

## 21. Target-kind capability matrix

Relation-type legality and target-kind resolver capability are separate constraints.

### DOCUMENT

P9 has a native exact resolver through Artifact/Revision.

Supported:

~~~text
LOGICAL_CURRENT
PINNED_REVISION
~~~

subject to the relation-type legality matrix.

### Non-document kinds

~~~text
SOURCE_CODE
SCHEMA
API
WORKFLOW
DATASET
STUDY_LOCK
OTHER_ARTIFACT
~~~

Current core GWF has no single generic primitive that proves "current" or exact immutable identity for all these kinds.

Therefore P9 must fail closed unless a target-kind resolver is independently qualified.

Rules:

- no caller-asserted opaque token is automatically trusted as exact;
- no LOGICAL_CURRENT external resolution is claimed without a qualified logical-current resolver;
- no PINNED_REVISION external binding is admitted as resolved without a qualified resolver returning an immutable identity/digest;
- adding target-kind resolvers does not require a new binding table.

## 22. Resolver interface contract

A future target-kind resolver must conceptually provide:

~~~text
resolve_logical_current(target_ref)
        -> exact immutable target identity + evidence

resolve_pinned(target_ref, requested_exact_identity)
        -> verified exact immutable identity + evidence
~~~

For DOCUMENT this is native Artifact/Revision lookup.

Resolver evidence may be provider-specific, but the canonical relation stores only its binding mode and exact pinned identity where applicable.

P9 pre-implementation qualification does not authorize any new external resolver.

## 23. No default/backfill semantics

Migration must not perform NULL -> LOGICAL_CURRENT or NULL -> PINNED_REVISION based on relation type.

Even when a relation type has only one legal mode, legacy binding still requires explicit governed mutation because exact pinned identity may need selection and verification.

This is particularly critical for VALIDATES, GENERATED_FROM, DERIVED_FROM and SUPERSEDES.

## 24. Binding governance

A legacy binding completion is a semantic mutation and must reuse:

~~~text
ProjectGovernance.require_mutable
        ↓
Governance actor authorization
        ↓
frozen Proposal payload/hash
        ↓
Approval
        ↓
one-time relation binding mutation
        ↓
relation.version increment
        ↓
Audit
~~~

Conceptual action:

~~~text
BIND_DOCUMENT_RELATION
~~~

No separate binding-history table is necessary.

## 25. Binding proposal exactness

A binding proposal must freeze:

- relation ID;
- expected relation version;
- relation type;
- target kind/ref;
- requested binding mode;
- requested exact target identity for PINNED_REVISION;
- resolver evidence reference when required.

At apply time, all frozen relation fields/version must still match.

If not, fail closed.

## 26. No rebind

After binding:

~~~text
LOGICAL_CURRENT -> PINNED_REVISION   FORBIDDEN
PINNED_REVISION -> LOGICAL_CURRENT   FORBIDDEN
PIN A -> PIN B                       FORBIDDEN
~~~

Change requires retire old relation then create a new relation with the new binding.

## 27. Interaction with TraceLink

P9 does not create, update, delete, or infer trace_links.

Frozen boundary:

~~~text
DocumentRelation
        ↓
P9 pure binding resolution
        ↓
exact resolved target identity
        ↓
STOP
~~~

Future:

~~~text
resolved relation binding
        ↓
DG-P12 relation-aware impact qualification
        ↓
optional operational traversal/projection
~~~

P9 may not shortcut that future gate.

## 28. Existing TraceLink is not binding evidence

No existing TraceLink may:

- backfill a P8 relation binding;
- prove a VALIDATES pin;
- prove GENERATED_FROM reproducibility;
- infer LOGICAL_CURRENT;
- replace target-kind resolver evidence.

TraceLink and relation binding remain distinct primitives.

## 29. Resolution has no propagation side effects

Calling a P9 resolver must be pure with respect to governed state.

It must not:

- create TraceLink;
- create ImpactSet;
- mutate Revision validity;
- create Evidence;
- create DocumentFinding;
- retire/rewrite relation state;
- update authority;
- update lifecycle;
- auto-edit source documents.

A LOGICAL_CURRENT target moving from R1 to R2 changes the next resolver output only.

Any downstream review/stale effect is DG-P12+ work.

## 30. No binding cache persistence

P9 does not justify a binding-resolution cache table.

LOGICAL_CURRENT is deliberately dynamic.

Persisting its most recent resolution as canonical state would risk turning a float into a stale pseudo-pin.

Consumers that need an attributable snapshot must record the exact resolved identity in their own governed artifact/change set/evidence, not mutate the relation.

## 31. Migration/backward-compatibility decision

Pre-implementation persistence verdict:

~~~text
new table                         NO
extend document_relations        YES
target_binding_mode              YES
target_revision_or_hash          YES
trace_links schema change        NO
binding cache                    NO
~~~

A future implementation migration should be additive and preserve all P8 rows.

P8 rows remain semantically valid declarations but operationally unbound until explicit binding.

## 32. Frozen fixture matrix

### D9-F1 — binding modes are distinct

Only LOGICAL_CURRENT and PINNED_REVISION are legal bound modes.

### D9-F2 — no legacy auto-backfill

A pre-P9 P8 relation remains binding NULL after migration and cannot be resolved operationally.

### D9-F3 — one-time governed legacy binding

An unbound legacy relation may be explicitly bound once through Proposal/Approval/Audit with optimistic versioning.

### D9-F4 — no rebind

A bound relation cannot change mode or pin in place.

### D9-F5 — DEPENDS_ON dual mode

DEPENDS_ON accepts LOGICAL_CURRENT and PINNED_REVISION.

### D9-F6 — REFERENCES dual mode

REFERENCES accepts LOGICAL_CURRENT and PINNED_REVISION.

### D9-F7 — MUST_ALIGN_WITH current only

PINNED_REVISION is rejected for MUST_ALIGN_WITH.

### D9-F8 — SUPERSEDES pinned only

LOGICAL_CURRENT is rejected for SUPERSEDES.

### D9-F9 — DERIVED_FROM pinned only

LOGICAL_CURRENT is rejected for DERIVED_FROM.

### D9-F10 — VALIDATES pinned only

LOGICAL_CURRENT is rejected for VALIDATES.

### D9-F11 — IMPLEMENTS dual mode

IMPLEMENTS accepts both binding modes.

### D9-F12 — GENERATED_FROM pinned only

LOGICAL_CURRENT is rejected for GENERATED_FROM.

### D9-F13 — pinned DOCUMENT ownership integrity

Pinned Revision must exist and belong to exactly target_ref.

### D9-F14 — logical-current DOCUMENT resolution

Resolver returns exact current Revision ID, immutable content hash and target artifact version without mutating relation state.

### D9-F15 — pinned historical resolution

After target gets a new revision, resolver still returns the pinned historical revision/hash and reports that the pin is not current.

### D9-F16 — VALIDATES never floats

A target revision change does not alter VALIDATES target identity and does not validate the new revision.

### D9-F17 — GENERATED_FROM exactness

Generated relation cannot resolve without a verified exact target identity.

### D9-F18 — external resolver fail-closed

Non-DOCUMENT binding cannot be claimed resolved when no qualified resolver exists.

### D9-F19 — zero TraceLink/impact/validity side effects

Binding and resolution leave TraceLinks, impacts, Evidence, findings and Revision validity unchanged.

### D9-F20 — no later-wave side effects

P9 creates no DG-P10 classification, DG-P11 change set, DG-P12 impact execution, GAC state or automatic source edit.

## 33. Pre-implementation acceptance gate

DG-P9 pre-implementation qualification may PASS only if:

- exact DG-P8 final formal-close dependency is verified;
- LOGICAL_CURRENT and PINNED_REVISION semantics are distinct;
- relation-type legality matrix is frozen;
- VALIDATES is PINNED-only;
- GENERATED_FROM is PINNED-only;
- DERIVED_FROM and SUPERSEDES exactness are frozen;
- MUST_ALIGN_WITH current-only semantics are frozen;
- dual-mode semantics for DEPENDS_ON/REFERENCES/IMPLEMENTS are frozen;
- P8 legacy no-default/backfill rule is frozen;
- binding immutability/no-rebind is frozen;
- native DOCUMENT resolution contract is frozen;
- external target resolution fails closed absent qualified resolver;
- no new P9 table is justified;
- future persistence extension is limited to two binding fields on document_relations;
- no TraceLink projection/propagation is authorized;
- resolver side effects are forbidden;
- D9-F1..D9-F20 are frozen;
- DG-P10+ remain unopened;
- implementation remains NOT_STARTED;
- Finding checklist OPEN = 0.

## 34. Expected post-qualification state

If document QA passes:

~~~text
DG-P8                     = FORMALLY_CLOSED
DG-P9 authorization       = PREIMPLEMENTATION_ONLY
DG-P9 specification       = FROZEN
DG-P9 dependency qualify  = PASS
DG-P9 document QA         = PASS
DG-P9 implementation      = NOT_STARTED
DG-P9 overall             = NOT_YET_PASS
DG-P10+                   = NOT_STARTED / NOT_AUTHORIZED
DG-W3                     = OPEN / NOT_EXECUTED
GAC                       = LOCKED_UNTIL_DG-W4_PASS
~~~

A separate explicit bounded implementation authorization is required before migration 0011, relation-binding runtime code, tests, or workflow are created.
