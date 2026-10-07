# GWF — DG-P8 Typed Document Relations Specification

## 1. Status and authorization boundary

**Item:** DG-P8 — Typed document relations  
**Wave:** 3 — Semantic Documentation Governance  
**Specification state:** FROZEN FOR DOCUMENT QA  
**Implementation state:** NOT_STARTED  
**Authorization state:** PRE-IMPLEMENTATION SPECIFICATION / DEPENDENCY QUALIFICATION ONLY

DG-P7 is formally closed. This document qualifies how governed document semantic relations map onto existing GWF trace primitives.

It does **not** authorize implementation code, schema migration, DG-P9 binding semantics, DG-P10+, DG-W3 closure, GAC, Reference Acquisition or G2E.

## 2. Exact dependency evidence

DG-P8 starts from exact DG-P7 formal-close state:

- DG-P7 final formal-close HEAD: `cf143d959b338e8d77811f5b2b79789ccbbb20aa`
- DG-P7 final exact-head workflow: `35611830804` PASS
- final SQLite evidence artifact: `10644398017`
- SQLite digest: `sha256:fba2d1bfc994670522ea27cd1bcb7eeb2c346132ee8802d5ee0ba53693af6945`
- final PostgreSQL evidence artifact: `10644037882`
- PostgreSQL digest: `sha256:f3740de876167d21252e2bf1937dc0650a36dbc923323f059c194aed1756e23c`

Relevant exact blobs at the dependency base:

| Artifact | Exact Git blob |
| --- | --- |
| `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` | `e50d0f17433c6f0ec57f987278a0d24a7bbd4610` |
| `docs/IMPLEMENTATION_7_WAVES_PLAN.md` | `2c2ff42bfbbd119ff1b5f23edf04082078e639b8` |
| `src/gwr/db.py` | `b9825998757423822ab7ffb22bd37dd202f3e30d` |
| `src/gwr/knowledge.py` | `2c4ae7f406031613c1bd885aa90b80b3f6f93606` |
| `src/gwr/domain.py` | `387f98b47575bc889e9bf88057fd010af2dce853` |
| `src/gwr/migrations.py` | `89dafb2e59c52f1b89f4cf8f0fc20e952f8064b2` |
| `domains/research.workflow.yaml` | `2226702e8451f85d16b90e398258e65936f0b981` |

## 3. Central semantic question

DG-P8 asks:

> Can typed governed-document relations reuse existing `PRIM-TRACE / trace_links` as their canonical semantic store, or does TraceLink represent a lower-level operational/provenance projection that must remain distinct?

The answer frozen by this specification is:

```text
DocumentRelation
    = governed semantic declaration

TraceLink
    = revision-level operational/provenance trace
      used by existing impact traversal
```

They are related, but they are not semantically identical.

## 4. Existing TraceLink semantics

Current `trace_links` schema is:

```text
trace_id
project_id
source_revision_id
target_kind
target_id
relation_type
strength
invalidates_on_upstream_supersede
propagation_rule
created_at
```

Existing behavior establishes that TraceLink:

1. starts from an exact `source_revision_id`, not a logical document;
2. may point to several generic target kinds;
3. is append-only in practice with no ACTIVE/RETIRED lifecycle;
4. has no optimistic relation version;
5. has no proposal/approval mutation provenance fields;
6. has no logical-target binding mode;
7. has no target revision/hash field separate from target identity;
8. drives generic impact traversal only when `target_kind='REVISION'`;
9. reduces operational propagation to `strength`, `invalidates_on_upstream_supersede`, and `propagation_rule`;
10. is already used for execution/provenance relations such as `PRODUCED_BY` and research-domain trace types.

Existing `compute_impact()` treats TraceLink operationally:

- HARD + invalidating -> `MARK_STALE`;
- SOFT -> `MARK_DIRTY`;
- otherwise -> `KEEP`.

That behavior is useful but is not sufficient to encode the complete documentation relation contract.

## 5. Why TraceLink cannot be the canonical DocumentRelation store

### 5.1 Source identity mismatch

A governed document relation belongs to a logical document and normally persists across ordinary content revisions until explicitly retired.

TraceLink belongs to one exact source revision.

Using TraceLink canonically would force one of two invalid behaviors:

- silently duplicate every relation whenever the source document gets a new revision; or
- let an old source revision continue to masquerade as the current logical relation owner.

P8 rejects both.

### 5.2 Missing relation lifecycle

Document relations require explicit current state:

```text
ACTIVE -> RETIRED
```

TraceLink has no status, retirement identity, optimistic version, or retirement provenance.

Deleting old TraceLinks would destroy history.

Leaving them forever active would make retired semantic relations indistinguishable from current ones.

### 5.3 Missing proposal/approval governance

A typed semantic relation changes governed graph state.

TraceLink has Audit on creation but no direct Proposal/Approval linkage and no bounded relation-state mutation contract.

P8 must reuse Proposal/Approval/Audit for governed relation creation/retirement without redefining generic trace creation semantics.

### 5.4 Relation semantics exceed strength/propagation fields

The required documentation relation types are not reducible to one generic HARD/SOFT propagation axis.

Examples:

- `REFERENCES`: referential break matters; target semantic change does not automatically stale the source.
- `MUST_ALIGN_WITH`: stored direction is explicit, but default review obligation is bidirectional.
- `SUPERSEDES`: changes authority/lifecycle semantics and cannot be represented as merely `MARK_STALE`.
- `VALIDATES`: evidence meaning depends on exact target identity and may never float.
- `GENERATED_FROM`: reproducibility requires exact target revision/hash.

Blindly mapping these to HARD/SOFT TraceLinks would change their meaning.

### 5.5 Missing binding semantics

DG-P9 owns:

```text
LOGICAL_CURRENT
PINNED_REVISION
```

TraceLink currently contains neither concept.

P8 must not silently choose one.

In particular, P8 must not make `VALIDATES` or `GENERATED_FROM` operational through a floating generic trace.

### 5.6 Existing trace type registry is domain-operational

The current research domain declares trace types such as:

- `derived_from`;
- `evaluates`;
- `falsifies_or_supports`;
- `reproduces`;
- `reports`.

These are domain execution/research trace semantics.

The documentation relation vocabulary is cross-domain core governance state.

Adding documentation relation meaning directly into domain trace definitions would make core document governance depend on one domain package.

## 6. What P8 does reuse from PRIM-TRACE

P8 **does** reuse TraceLink as a lower-level operational substrate concept.

Frozen integration boundary:

```text
canonical DocumentRelation
        ↓
future binding resolution (DG-P9)
        ↓
future relation-specific impact qualification
        ↓
optional resolved TraceLink projection
        ↓
existing generic impact/provenance machinery where semantically valid
```

Therefore:

- P8 does not replace `trace_links`;
- P8 does not migrate existing TraceLinks;
- P8 does not reinterpret existing TraceLinks as document relations;
- P8 does not create TraceLinks merely because a DocumentRelation exists;
- later phases may project only relation types whose resolved semantics have an explicit safe mapping.

No reverse inference is allowed:

```text
TraceLink != implicit DocumentRelation
```

## 7. Required relation vocabulary

P8 freezes the cross-domain document relation vocabulary:

```text
DEPENDS_ON
REFERENCES
MUST_ALIGN_WITH
SUPERSEDES
DERIVED_FROM
VALIDATES
IMPLEMENTS
GENERATED_FROM
```

No Markdown link or generic trace type automatically becomes one of these relations.

## 8. Direction contract

Every relation is stored with explicit direction:

```text
source_document_id
        -- relation_type -->
target_kind + target_ref
```

Direction semantics:

### DEPENDS_ON

Source correctness materially depends on target.

P8 stores the declaration only. Later impact logic may require review/staleness when a bound target changes.

### REFERENCES

Source cites/navigates to target.

Target disappearance may become a referential finding; target semantic change does not automatically invalidate source.

### MUST_ALIGN_WITH

Stored edge has source/target identity for deterministic relation identity.

Default semantic obligation is pairwise/bidirectional review when either side materially changes.

P8 does not implement that propagation yet.

### SUPERSEDES

Source declares replacement of target.

P8 records the typed assertion only.

P8 does **not** transfer/retire P7 authority claims and does not mutate document lifecycle. Operational supersession is later governance work.

### DERIVED_FROM

Source is derived or summarized from target state.

P8 records the declaration; later propagation may stale the source when the bound target changes.

### VALIDATES

Source claims validation of target.

P8 reserves and stores the semantic relation type but **does not treat it as valid evidence** until DG-P9 establishes an exact pinned binding.

### IMPLEMENTS

Source describes implementation of a normative target.

P8 records the directed semantic relation only.

### GENERATED_FROM

Source is reproducibly generated from target.

P8 reserves and stores the semantic relation type but **does not treat it as reproducible provenance** until DG-P9 establishes exact pinned identity.

## 9. Target kinds

P8 freezes the target-kind vocabulary from the governing specification:

```text
DOCUMENT
SOURCE_CODE
SCHEMA
API
WORKFLOW
DATASET
STUDY_LOCK
OTHER_ARTIFACT
```

For `DOCUMENT`:

- `target_ref` is the target logical governed-document Artifact ID;
- source and target must belong to the same project at P8.

For non-document kinds:

- `target_ref` is a stable opaque governed reference;
- P8 does not claim exact revision/hash semantics;
- P9 or a later adapter must qualify exact binding before any consumer treats the relation as pinned evidence.

## 10. P8/P9 separation

P8 owns:

- relation identity;
- relation type;
- source logical document;
- target kind/logical reference;
- explicit direction;
- relation lifecycle;
- declaration provenance;
- optional governed invalidation-policy identifier.

DG-P9 owns:

- `LOGICAL_CURRENT`;
- `PINNED_REVISION`;
- exact target revision/hash;
- legality of binding modes per relation type;
- the rule that `VALIDATES` cannot float;
- exact identity for `GENERATED_FROM`.

P8 therefore must **not** add or interpret:

```text
target_binding_mode
target_revision_or_hash
```

A P8 relation is a governed semantic declaration, not yet a resolved operational dependency.

No P8 consumer may use a relation row alone as proof of exact validation, exact generation provenance, or impact propagation.

## 11. Minimal persistence decision

Semantic-fit analysis justifies exactly one new canonical current-state table:

```text
document_relations
```

Conceptual columns:

```text
relation_id
project_id
source_document_id
relation_type
target_kind
target_ref
invalidation_policy
status                       ACTIVE | RETIRED
created_revision_id
create_proposal_id
retired_revision_id          nullable
retired_by_proposal_id       nullable
version
created_at
updated_at
retired_at                   nullable
```

Required lookup indexes should support:

- `(project_id, source_document_id, status)`;
- `(project_id, target_kind, target_ref, status)`;
- `(project_id, relation_type, status)`.

No other P8 table is justified.

Explicitly rejected:

```text
document_relation_nodes table
document_relation_types table
document_relation_events table
document_trace_projection table
document_relation_findings table
```

The required relation type set is a reserved core semantic vocabulary, not a mutable DB registry.

## 12. Why a new table is not an unjustified duplicate graph

The system has two distinct graph layers:

### Semantic governance graph

Canonical governed statements:

```text
logical document
    -- typed semantic relation -->
logical governed target
```

Owned by `document_relations`.

### Operational trace graph

Resolved revision/provenance/impact edges:

```text
exact revision
    -- operational trace -->
resolved target
```

Owned by existing `trace_links`.

The semantic graph answers:

> What relationship has governance declared?

The trace graph answers:

> What exact operational dependency/provenance edge is available to execution/impact machinery?

Collapsing them would lose either logical relation lifetime or exact operational identity.

Keeping them distinct is therefore semantic separation, not duplicate authority.

## 13. Relation lifecycle

P8 relation lifecycle is:

```text
ACTIVE -> RETIRED
```

Rules:

- creation adds one ACTIVE semantic declaration;
- relation tuple is immutable after creation;
- changing relation type/source/target/invalidation policy means retire-old + create-new;
- retirement never deletes historical relation state;
- optimistic `version` protects stale retirement;
- exact source revision at relation creation is preserved in `created_revision_id`;
- retirement may record the then-current source revision in `retired_revision_id`;
- later source content revisions do not silently clone or retire a relation.

## 14. Proposal / Approval / Audit reuse

P8 does not create a second relation-governance history system.

Relation creation/retirement must reuse:

```text
ProjectGovernance.require_mutable
        ↓
GovernanceKernel actor authorization
        ↓
frozen Proposal payload/hash
        ↓
required Approval
        ↓
document_relations current-state mutation
        ↓
Audit
```

Conceptual actions:

```text
DECLARE_DOCUMENT_RELATION
RETIRE_DOCUMENT_RELATION
```

P8 does not define P10 change-class semantics.

A later change-class layer may impose stronger approval requirements without changing relation identity.

## 15. No Markdown-link inference

A Markdown hyperlink is not sufficient evidence of a semantic relation.

P8 forbids automatic creation of `document_relations` from:

- Markdown links;
- text mentions;
- filenames;
- headings;
- README navigation;
- existing TraceLinks;
- Git path adjacency;
- shared authority scope.

Automated analysis may propose a relation, but a governed relation requires explicit mutation through the relation service.

## 16. Duplicate relation handling

P8 distinguishes duplicate declaration from semantic graph cycles.

An exact ACTIVE duplicate tuple:

```text
(project_id,
 source_document_id,
 relation_type,
 target_kind,
 target_ref)
```

is not useful and must fail closed at service level.

P8 does not add a DB UNIQUE constraint over this tuple because RETIRED historical rows must coexist and DG-P9 may later add binding identity that changes operational uniqueness.

Graph cycles are representable state and must not be silently prevented merely by schema uniqueness.

Cycle QA/impact semantics are separate governed checks.

## 17. Self-relations

For target kind `DOCUMENT`, a relation whose source and target are the same logical document is invalid for all P8 core relation types.

This is rejected as a structural relation error rather than stored as a meaningful edge.

## 18. Relation-specific invalidation policy

The governing specification allows relation semantics to have default invalidation behavior and, for some relations, an explicit governed override.

P8 stores only an `invalidation_policy` identifier/payload reference sufficient to preserve the declared semantic contract.

P8 does not execute it.

It must not be reduced automatically to existing TraceLink:

```text
strength
invalidates_on_upstream_supersede
propagation_rule
```

Mapping into those fields requires a later qualified projection.

## 19. P7 authority boundary

A P8 `SUPERSEDES` relation does not itself:

- retire a P7 authority claim;
- grant a new authority claim;
- change PRIMARY/COMPOSED ownership;
- change Artifact lifecycle;
- mark a document ARCHIVED/SUPERSEDED.

Those effects require their own later governed program.

Likewise, P7 authority similarity does not infer a P8 relation.

## 20. P5/P6 QA and validity boundary

P8 relation storage itself does not directly mutate document validity.

Structural relation QA may later emit existing P5 finding classes such as:

- `BROKEN_REFERENCE`;
- `UNRESOLVED_DEPENDENCY`;
- `DEPENDENCY_CYCLE`;
- `INVALID_SUPERSESSION`.

P8 does not create a relation-finding subsystem.

Any such finding flows through existing P5/P6 semantics.

P8 pre-implementation qualification does not yet authorize those validators.

## 21. TraceLink projection boundary

P8 implementation, if later authorized, must leave existing `trace_links` unchanged.

No automatic semantic-relation-to-trace projection is permitted in DG-P8.

Projection requires at minimum:

1. a qualified target binding from DG-P9;
2. a relation-type-specific mapping proving whether a generic TraceLink is semantically sound;
3. preservation of semantic relation identity/provenance;
4. proof that projection does not create double propagation or stale orphan TraceLinks.

Some relation types may never map one-to-one to TraceLink.

Examples:

- `REFERENCES` may need referential QA rather than impact propagation;
- `MUST_ALIGN_WITH` needs pairwise review semantics;
- `SUPERSEDES` needs authority/lifecycle governance;
- `VALIDATES` is evidentiary and exact-bound;
- `GENERATED_FROM` is reproducibility provenance.

## 22. Frozen fixture matrix

### D8-F1 — explicit direction

Relation stores one explicit source document and one target kind/ref.

### D8-F2 — required relation vocabulary

All eight required relation types are reserved core values.

### D8-F3 — no Markdown inference

A Markdown link does not create a relation row.

### D8-F4 — no TraceLink inference

An existing generic TraceLink does not create a DocumentRelation.

### D8-F5 — logical source identity

Relation belongs to logical source document, not one transient source revision.

### D8-F6 — creation provenance exact

Relation records exact source revision and proposal/approval/audit provenance at declaration.

### D8-F7 — new source revision preserves relation identity

Creating a later source revision neither clones nor retires the ACTIVE relation.

### D8-F8 — ACTIVE to RETIRED

Explicit approved retirement preserves the historical row and makes it non-current.

### D8-F9 — stale retirement rejected

Retirement with stale relation version fails closed.

### D8-F10 — exact duplicate ACTIVE relation rejected

Same source/type/target-kind/target-ref cannot be declared twice as separate clean ACTIVE relations.

### D8-F11 — self-document relation rejected

Source document cannot target itself for a core semantic relation.

### D8-F12 — DOCUMENT target integrity

A DOCUMENT target must resolve to an existing governed document in the same project.

### D8-F13 — external target kind preserved

Non-document target kind/ref is stored without pretending that exact revision/hash binding has been proven.

### D8-F14 — relation type semantics remain distinct

REFERENCES is not treated as DEPENDS_ON; MUST_ALIGN_WITH is not reduced to one-way stale propagation.

### D8-F15 — SUPERSEDES has no P7/lifecycle side effect

Declaring SUPERSEDES does not mutate authority claims or document lifecycle.

### D8-F16 — VALIDATES is not evidence before P9 binding

A P8 VALIDATES declaration alone cannot count as current validation of any target revision.

### D8-F17 — GENERATED_FROM is not reproducibility proof before P9 binding

A P8 GENERATED_FROM declaration alone cannot count as exact reproducibility provenance.

### D8-F18 — no TraceLink projection in P8

Creating/retiring a document relation leaves existing `trace_links` unchanged.

### D8-F19 — zero additional P8 graph tables

Only `document_relations` is justified; no nodes/types/events/projection table exists.

### D8-F20 — no later-wave side effects

P8 relation mutation creates no DG-P9 binding, P10 classification, P11 change set, GAC state or automatic source edit.

## 23. Pre-implementation acceptance gate

DG-P8 pre-implementation qualification may PASS only if:

- exact DG-P7 formal-close dependency is verified;
- TraceLink operational semantics are explicitly inventoried;
- source logical-document versus source-revision mismatch is resolved;
- relation lifecycle gap is resolved;
- Proposal/Approval/Audit reuse is frozen;
- required relation types and target kinds are frozen;
- direction semantics are explicit;
- Markdown/TraceLink inference is forbidden;
- P8/P9 boundary is explicit;
- exactly one `document_relations` table is justified;
- no P8 TraceLink projection is authorized;
- P7 authority/lifecycle side effects are excluded;
- D8-F1..D8-F20 are frozen;
- DG-P9+ remain unopened;
- implementation remains NOT_STARTED;
- Finding checklist OPEN = 0.

## 24. Expected post-qualification state

If document QA passes:

```text
DG-P7                     = FORMALLY_CLOSED
DG-P8 authorization       = PREIMPLEMENTATION_ONLY
DG-P8 specification       = FROZEN
DG-P8 dependency qualify  = PASS
DG-P8 document QA         = PASS
DG-P8 implementation      = NOT_STARTED
DG-P8 overall             = NOT_YET_PASS
DG-P9+                    = NOT_STARTED / NOT_AUTHORIZED
DG-W3                     = OPEN / NOT_EXECUTED
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```

A separate explicit bounded implementation authorization is required before any P8 migration/runtime/test/workflow is created.
