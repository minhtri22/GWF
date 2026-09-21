# GWF — DG-P8 Implementation QA

## 1. QA identity

**Qualified implementation HEAD:** `e784d7f56c0cfdf25ca453da48d570cd202ad0cc`  
**Initial implementation HEAD:** `2081f730e38dc874c29335f77e441ed794fcb885`  
**Frozen specification commit:** `211308141106481104590b3d55cdc8c19d6b6d8e`  
**Frozen specification blob:** `d6996951522caa061b29f94d1b1f4f579251adaa`  
**Pre-implementation qualification HEAD:** `cf5a268b58bd9f1bb69df2a4bfeed5a2809380b1`  
**Qualified workflow:** `35621561857` PASS

SQLite evidence:
- artifact `10649881388`
- digest `sha256:18b47ce4c730bd66a70de43eb881785281fc141c12a4f72564d4682be618d474`

PostgreSQL 17 evidence:
- artifact `10649322400`
- digest `sha256:62214aecf3fb2347626417ac467f82f32968a576b477ef8a07c387d6d7eaf05b`

## 2. Bounded implementation surface

Implementation changed:

- `src/gwr/migrations.py`
- `src/gwr/document_relation.py`
- `src/gwr/runtime.py`
- `tests/test_dg_p8_relations.py`
- `tools/run_dg_p8_gate.py`
- `.github/workflows/dg-p8-relations.yml`

Compatibility repair changed only:

- `tests/test_dg_p7_authority.py`

Not changed:

- `src/gwr/knowledge.py`
- TraceLink schema/runtime semantics
- DG-P7 authority runtime
- DG-P9+ runtime/schema
- GAC / Reference Acquisition / G2E.

## 3. Persistence QA

PASS.

Exactly one P8 migration was added:

```text
0010_v086_dg_p8_document_relations
        ↓
document_relations
```

The table stores:

- relation identity;
- project;
- logical source document;
- relation type;
- target kind/ref;
- declared invalidation-policy identifier;
- ACTIVE/RETIRED state;
- exact source revision at declaration;
- create/retire proposal provenance;
- exact source revision at retirement;
- optimistic version;
- timestamps.

Indexes support source, target and relation-type lookup.

No P8 node/type/event/projection/finding table was added.

## 4. Semantic/operational graph separation

PASS.

Canonical semantic state:

```text
document_relations
```

Existing operational/provenance state:

```text
trace_links
```

P8 runtime does not call `create_trace_link()`, does not modify `KnowledgeKernel`, and does not create a projection table.

D8-F4 and D8-F18 prove both directions:

- an existing TraceLink does not create a DocumentRelation;
- create/retire DocumentRelation does not create or mutate TraceLinks.

## 5. Relation vocabulary and target kinds

PASS.

Reserved relation types:

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

The runtime rejects values outside these core sets.

## 6. Logical source identity + exact provenance

PASS.

Relation owner is `source_document_id`, not one transient revision.

`created_revision_id` records exact source provenance at declaration.

Declaration apply fails closed if the source revision changed between frozen Proposal and commit.

Later source revision creation:

- does not clone the relation;
- does not retire the relation;
- leaves `created_revision_id` unchanged.

## 7. Target integrity and P9 boundary

PASS.

For `DOCUMENT` targets:

- target must exist;
- target must be `governed_document`;
- target must be in the same project;
- self-document relations are rejected.

For non-document target kinds, P8 stores the stable opaque reference without asserting exact revision/hash binding.

No P8 schema/API field exists for:

```text
target_binding_mode
target_revision_or_hash
LOGICAL_CURRENT
PINNED_REVISION
```

D8-F16/F17 verify `VALIDATES` and `GENERATED_FROM` create neither validation Evidence nor exact reproducibility proof.

## 8. Relation-specific semantic preservation

PASS.

P8 stores relation type distinctly and preserves a declared `invalidation_policy` identifier without executing it.

Default identifiers are relation-specific; for example:

- REFERENCES -> `REFERENTIAL_INTEGRITY_ONLY`;
- DEPENDS_ON -> `REVIEW_ON_TARGET_CHANGE`;
- MUST_ALIGN_WITH -> `BIDIRECTIONAL_REVIEW`;
- VALIDATES / GENERATED_FROM -> `REQUIRES_PINNED_BINDING`;
- SUPERSEDES -> `DECLARATION_ONLY`.

They are metadata only. No generic HARD/SOFT TraceLink mapping is performed.

## 9. Proposal / Approval / Audit governance

PASS.

Relation declaration/retirement uses:

```text
Project mutability check
        ↓
existing actor authorization
        ↓
frozen Proposal payload/hash
        ↓
required Approval
        ↓
document_relations mutation
        ↓
Audit
```

Runtime dispatcher adds only:

- `DECLARE_DOCUMENT_RELATION`;
- `RETIRE_DOCUMENT_RELATION`.

Existing proposal dispatch remains intact.

## 10. Duplicate/current-state concurrency

PASS.

Exact ACTIVE duplicate tuple:

```text
(project,
 source_document,
 relation_type,
 target_kind,
 target_ref)
```

is rejected at service level.

The DB intentionally has no unique constraint over the tuple because historical RETIRED rows must coexist and DG-P9 may later extend operational identity.

Serialization:

- SQLite: existing `BEGIN IMMEDIATE`;
- PostgreSQL: project-row `SELECT ... FOR UPDATE`.

Graph cycles remain representable state; P8 does not silently prohibit them.

## 11. Relation retirement

PASS.

Lifecycle:

```text
ACTIVE -> RETIRED
```

Retirement requires:

- approved frozen retirement proposal;
- exact expected relation version;
- exact current source revision frozen in proposal;
- optimistic update;
- append-only Audit.

Stale version fails closed.

Historical row remains queryable.

## 12. P7 authority/lifecycle isolation

PASS.

D8-F15 verifies a `SUPERSEDES` relation does not:

- retire a DG-P7 authority claim;
- grant authority;
- change source/target Artifact lifecycle.

P8 relation semantics remain declaration-only.

## 13. No inference / no later-wave side effects

PASS.

No relation is created from Markdown links or existing TraceLinks.

P8 mutation creates no:

- P9 relation binding;
- P10 change classification;
- P11 change set;
- GAC state;
- automatic source edit;
- TraceLink projection.

## 14. Frozen fixture evidence

D8-F1..D8-F20: **20/20 PASS on SQLite**.

D8-F1..D8-F20: **20/20 PASS on PostgreSQL 17**.

Bounded relation gate: PASS on both backends.

Targeted regressions PASS:

- Knowledge / Trace;
- Execution / Decision;
- Persistence;
- DG-P4;
- DG-P5;
- DG-P6;
- DG-P7.

Full repository regression: PASS.

Compile: PASS.

## 15. Negative run and compatibility repair

Initial workflow:

- run `35621370994`
- HEAD `2081f730e38dc874c29335f77e441ed794fcb885`
- overall result: FAIL.

Important component evidence from that run:

- D8-F1..D8-F20 SQLite: PASS;
- SQLite P8 bounded gate: PASS;
- D8-F1..D8-F20 PostgreSQL: PASS;
- PostgreSQL P8 bounded gate: PASS.

Failure occurred only in historical D7-F20 regression.

D7-F20 encoded:

> `document_relations` table must not exist.

That assertion was correct at the P7 closure frontier but is not a durable P7 invariant once the explicitly authorized P8 migration legitimately creates that table.

The durable P7 invariant is:

> P7 authority operations must not create or mutate relation state.

Bounded repair commit:

`e784d7f56c0cfdf25ca453da48d570cd202ad0cc`

changed only `tests/test_dg_p7_authority.py`:

- if `document_relations` exists, snapshot its row count;
- run P7 authority operation;
- require the row count to remain unchanged;
- continue to require P9+/GAC tables absent.

P8 runtime, migration, frozen spec and workflow were unchanged.

Qualified workflow `35621561857` then passed completely.

## 16. Implementation QA verdict

```text
frozen DG-P8 spec preserved               PASS
migration count                           EXACTLY ONE
document_relations                        PASS
extra P8 graph tables                     NONE
TraceLink canonical-store reuse           NO
TraceLink projection                      NONE
relation vocabulary                       PASS
target-kind vocabulary                    PASS
logical source identity                   PASS
exact declaration provenance              PASS
Proposal/Approval/Audit                   PASS
ACTIVE -> RETIRED                         PASS
optimistic concurrency                    PASS
duplicate ACTIVE rejection                PASS
DOCUMENT target integrity                 PASS
P9 binding fields                         NONE
VALIDATES evidence side effect            NONE
GENERATED_FROM proof side effect          NONE
SUPERSEDES P7/lifecycle side effect        NONE
D8-F1..D8-F20 SQLite                      20/20 PASS
D8-F1..D8-F20 PostgreSQL                  20/20 PASS
P4/P5/P6/P7 + Knowledge/Trace regressions PASS
full regression                           PASS
compile                                   PASS
DG-P9+ opened                             NO
DG-W3 closed                              NO
```

**DG-P8 IMPLEMENTATION QUALIFICATION: PASS**
