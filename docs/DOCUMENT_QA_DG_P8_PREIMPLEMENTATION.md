# GWF — DG-P8 Pre-Implementation Document QA

## 1. QA identity

**Item:** DG-P8 — Typed document relations  
**Subject:** `docs/DG_P8_TYPED_DOCUMENT_RELATIONS_SPEC.md`  
**Subject commit:** `211308141106481104590b3d55cdc8c19d6b6d8e`  
**Subject blob:** `d6996951522caa061b29f94d1b1f4f579251adaa`  
**Dependency base:** DG-P7 final formal-close HEAD `cf143d959b338e8d77811f5b2b79789ccbbb20aa`  
**Dependency final exact-head workflow:** `35611830804` PASS  
**SQLite artifact:** `10644398017`  
**SQLite digest:** `sha256:fba2d1bfc994670522ea27cd1bcb7eeb2c346132ee8802d5ee0ba53693af6945`  
**PostgreSQL artifact:** `10644037882`  
**PostgreSQL digest:** `sha256:f3740de876167d21252e2bf1937dc0650a36dbc923323f059c194aed1756e23c`  
**QA type:** pre-implementation semantic/dependency qualification  
**Implementation executed:** NO

## 2. Governing requirement verification

Documentation Integrity §10 requires:

- explicit relation direction;
- typed document semantics;
- minimum relation vocabulary;
- semantic meaning not inferred from hyperlink syntax;
- explicit target-kind semantics;
- later distinction between logical-current and pinned-revision binding;
- relation semantics, not link syntax, to drive invalidation.

The Wave-3 roadmap additionally requires existing `trace_links` to be evaluated before new graph storage is admitted.

## 3. Existing TraceLink fit analysis

Current `trace_links` stores:

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

Current KnowledgeKernel behavior confirms:

- source is an exact Revision;
- impact traversal only follows `target_kind='REVISION'`;
- HARD invalidating links map to `MARK_STALE`;
- SOFT links map to `MARK_DIRTY`;
- informational links remain KEEP;
- TraceLink already serves execution/research provenance and impact semantics.

**Verdict:** TraceLink is a revision-level operational/provenance primitive, not a complete logical-document relation registry.

## 4. Source identity compatibility QA

PASS.

Document relation ownership is logical-document state.

A relation should persist across ordinary source revisions until explicit retirement.

TraceLink's `source_revision_id` cannot represent that lifetime without either:

1. cloning relations on every source revision; or
2. keeping an obsolete revision as the apparent semantic owner.

Both are rejected.

P8 therefore reuses existing governed-document Artifact identity for the semantic source and preserves exact declaration revision separately as provenance.

## 5. Relation lifecycle compatibility QA

PASS.

Typed document relations require:

```text
ACTIVE -> RETIRED
```

plus optimistic current-state version and retirement provenance.

TraceLink has no lifecycle/version/retirement fields.

Deleting TraceLinks would destroy history; treating every historical TraceLink as current would corrupt relation state.

Therefore TraceLink cannot be canonical current-state persistence.

## 6. Relation-semantic compatibility QA

PASS.

The following governing semantics are not reducible to generic HARD/SOFT propagation:

- `REFERENCES`: broken reference matters, semantic target change does not automatically stale source;
- `MUST_ALIGN_WITH`: stored direction but default bidirectional review obligation;
- `SUPERSEDES`: authority/lifecycle semantics, not generic stale propagation;
- `VALIDATES`: exact evidentiary identity required;
- `GENERATED_FROM`: exact reproducibility identity required.

A blanket mapping into `strength/invalidates/propagation_rule` would be semantically incorrect.

## 7. PRIM-TRACE reuse verdict

**PARTIAL REUSE / PROJECTION SUBSTRATE ONLY.**

Frozen layering:

```text
document_relations
    = canonical governed semantic graph

trace_links
    = resolved operational/provenance graph
```

P8 does not replace or reinterpret TraceLinks.

P8 also does not create TraceLinks.

Future projection is permitted only after:

- DG-P9 qualifies target binding;
- a later relation-specific mapping proves the projection safe.

No reverse inference is allowed from TraceLink to DocumentRelation.

## 8. Minimal persistence qualification

PASS.

Exactly one new canonical current-state table is justified:

```text
document_relations
```

The table must represent:

- logical source document;
- relation type;
- target kind/ref;
- relation lifecycle;
- relation invalidation-policy declaration;
- exact source revision at declaration;
- proposal/retirement provenance;
- optimistic version.

Rejected P8 persistence:

```text
document_relation_nodes
document_relation_types
document_relation_events
document_trace_projection
document_relation_findings
```

The semantic type set is core code vocabulary, not a DB registry.

## 9. Required relation vocabulary QA

PASS.

Reserved types:

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

Direction is explicit for each relation.

No Markdown link or generic TraceLink creates one implicitly.

## 10. Target-kind QA

PASS.

Reserved target kinds:

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

For DOCUMENT, target_ref is logical governed-document identity in the same project.

For other kinds, P8 preserves stable reference identity without claiming exact revision/hash binding.

## 11. P8/P9 boundary QA

PASS.

P8 owns semantic relation identity and lifecycle only.

DG-P9 exclusively owns:

```text
LOGICAL_CURRENT
PINNED_REVISION
target_revision_or_hash
binding legality per relation type
```

P8 must not add or interpret those fields.

Therefore:

- a P8 `VALIDATES` declaration is not current validation evidence;
- a P8 `GENERATED_FROM` declaration is not exact reproducibility evidence;
- no P8 relation is projected into TraceLink or impact machinery.

This is an explicit dependency boundary, not technical debt.

## 12. SUPERSEDES authority/lifecycle boundary

PASS.

P8 `SUPERSEDES` is a typed semantic assertion only.

It does not:

- retire DG-P7 claims;
- grant authority;
- mutate document lifecycle;
- archive/supersede a logical document;
- silently create impact propagation.

Later governance must execute those effects explicitly.

## 13. Mutation-governance reuse QA

PASS.

P8 can reuse:

- ProjectGovernance mutability checks;
- Governance actor authorization;
- Proposal / Approval;
- Audit.

No relation-event/history subsystem is necessary.

Relation tuple changes are modeled as retire-old + create-new.

## 14. Duplicate declaration / graph-cycle QA

PASS.

Exact duplicate ACTIVE relation tuples are service-level invalid and should fail closed.

A DB uniqueness rule is not frozen because:

- historical RETIRED rows coexist;
- P9 adds binding identity later;
- graph cycles must remain observable rather than being hidden by schema shortcuts.

Cycle semantics remain a QA concern, not a reason to overload TraceLink.

## 15. No-inference QA

PASS.

No semantic relation may be inferred solely from:

- Markdown hyperlink;
- file path;
- heading;
- text mention;
- README navigation;
- existing TraceLink;
- shared authority scope;
- repository adjacency.

Automated systems may propose relation mutations, not silently create canonical relations.

## 16. P5/P6 reuse boundary

PASS.

P8 does not create a relation-finding subsystem.

Future structural relation validators may reuse existing P5 classes such as:

- `BROKEN_REFERENCE`;
- `UNRESOLVED_DEPENDENCY`;
- `DEPENDENCY_CYCLE`;
- `INVALID_SUPERSESSION`.

Those findings can flow through existing P6 validity semantics.

P8 qualification does not authorize those validators yet.

## 17. Fixture adequacy

D8-F1 through D8-F20 cover:

- direction;
- relation vocabulary;
- no Markdown/TraceLink inference;
- logical source lifetime;
- exact creation provenance;
- source-revision continuity;
- retirement/versioning;
- exact duplicate rejection;
- self-relation rejection;
- target integrity;
- external target preservation;
- relation-semantic distinction;
- no P7/lifecycle side effect;
- P9 binding non-preemption;
- no TraceLink projection;
- exactly one P8 table;
- no later-wave side effects.

**Fixture verdict: ADEQUATE.**

## 18. Finding adjudication

- F-95 — roadmap used handoff evidence rather than final DG-P7 closure run: resolved by exact final-run verification and frontier update.
- F-96 — TraceLink/document-relation semantic conflation: resolved by semantic-vs-operational layering.
- F-97 — source Revision versus logical-document lifetime mismatch: resolved by logical Artifact source + exact creation Revision provenance.
- F-98 — missing relation lifecycle in TraceLink: resolved by bounded `document_relations` current-state persistence.
- F-99 — generic strength/propagation semantic loss: resolved by prohibiting blanket relation-to-TraceLink mapping.
- F-100 — DG-P9 binding preemption risk: resolved by excluding binding mode/revision/hash from P8.
- F-101 — duplicate graph subsystem risk: resolved by one semantic table and no nodes/types/events/projection tables.
- F-102 — implicit relation inference risk: resolved by explicit governed declaration only.
- F-103 — SUPERSEDES side-effect preemption risk: resolved by declaration-only P8 boundary.

All are specification/document-state resolved.

No runtime implementation has occurred.

## 19. Document QA verdict

```text
DG-P7 dependency                       PASS
TraceLink inventory                    PASS
TraceLink as canonical relation store  REJECTED
TraceLink projection substrate         ACCEPTED / DEFERRED
logical source identity                PASS
relation lifecycle                     PASS
typed semantics                        PASS
direction explicit                     PASS
target-kind vocabulary                 PASS
Markdown/Trace inference               REJECTED
document_relations table               JUSTIFIED / EXACTLY ONE
additional P8 graph tables             REJECTED
P8/P9 separation                       PASS
P7 authority/lifecycle side effects    EXCLUDED
D8-F1..D8-F20                          ADEQUATE
DG-P9+ opened                          NO
implementation                         NOT_STARTED
Finding OPEN                           0
```

**DG-P8 PRE-IMPLEMENTATION QUALIFICATION: PASS**
