# GWF — DG-P9 Implementation QA

## 1. QA identity

**Qualified implementation HEAD:** `9ffd64a1e9b98ea307ed8f9682b88e26570dc208`  
**Frozen specification commit:** `1a9f8737e36392c8a8db49b93c9371ceee16085f`  
**Frozen specification blob:** `73e1d7c8c01ea954af2a65e1df1942b4f95738f3`  
**Pre-implementation qualification HEAD:** `52ae1ebded1f9a942cee55d6d2ce061b5bcb8290`  
**Pre-implementation QA blob:** `395b61a7121476296287fa3d085b51d42c7e4adf`  
**Qualified workflow:** `35628998000` PASS

SQLite evidence:
- artifact `10653386409`
- digest `sha256:651c9a59f77d83176cbc452d39a9beebf17c27e2390ef83a96aee85ed29ea160`

PostgreSQL 17 evidence:
- artifact `10653461137`
- digest `sha256:aff7462c949ce6645bd0edc4ea130cbce884ac424a72234fc79ad8b9dc7b8ae4`

## 2. Bounded implementation surface

Implementation changed:

- `src/gwr/migrations.py`
- `src/gwr/document_relation.py`
- `src/gwr/runtime.py`
- `tests/test_dg_p9_relations.py`
- `tools/run_dg_p9_gate.py`
- `.github/workflows/dg-p9-binding.yml`

Compatibility requalification changed only historical P8 fixtures in:

- `tests/test_dg_p8_relations.py`

Finding bookkeeping changed:

- `docs/Finding_checklist.md`

Not changed:

- `src/gwr/knowledge.py`;
- TraceLink schema/runtime semantics;
- impact semantics;
- Revision validity semantics;
- P7 authority semantics;
- lifecycle semantics;
- DG-P10+ runtime/schema;
- GAC / Reference Acquisition / G2E.

## 3. Persistence QA

PASS.

Exactly one DG-P9 migration was added:

```text
0011_v086_dg_p9_relation_binding
```

It only extends the existing canonical table:

```text
document_relations
    + target_binding_mode
    + target_revision_or_hash
```

No binding table, event table, resolution table, cache table, projection table or TraceLink schema change was introduced.

The migration contains no default and no UPDATE/backfill statement. Existing P8 rows therefore retain NULL binding fields.

## 4. Binding-mode semantics

PASS.

The runtime exposes exactly two bound modes:

```text
LOGICAL_CURRENT
PINNED_REVISION
```

NULL is accepted only as legacy absence in rows created before DG-P9. New relation declaration does not infer a default: an explicit legal binding is required and is frozen atomically in the declaration Proposal.

## 5. Frozen legality matrix

PASS.

The implementation enforces the frozen matrix without consulting or weakening it through `invalidation_policy`:

| Relation | LOGICAL_CURRENT | PINNED_REVISION |
| --- | --- | --- |
| DEPENDS_ON | allowed | allowed |
| REFERENCES | allowed | allowed |
| MUST_ALIGN_WITH | required | forbidden |
| SUPERSEDES | forbidden | required |
| DERIVED_FROM | forbidden | required |
| VALIDATES | forbidden | required |
| IMPLEMENTS | allowed | allowed |
| GENERATED_FROM | forbidden | required |

D9 fixtures reject forbidden combinations.

## 6. Legacy one-time binding governance

PASS.

Legacy P8 rows with `target_binding_mode IS NULL` may receive exactly one governed binding through:

```text
BIND_DOCUMENT_RELATION
        ↓
frozen Proposal
        ↓
Approval
        ↓
project serialization / exact expected version
        ↓
one-time binding mutation
        ↓
relation.version + 1
        ↓
Audit
```

The frozen Proposal contains relation ID, expected relation version, relation type, target kind/ref, requested binding mode and requested exact identity.

Apply rechecks frozen relation fields and optimistic version. A bound relation cannot be rebound in place.

## 7. New relation atomic binding

PASS.

Post-DG-P9 relation creation requires binding at declaration time.

No new ACTIVE relation can be created through the service with NULL binding. The binding is included in the frozen declaration Proposal and persisted atomically with the relation row.

This is distinct from the one-time legacy bind path.

## 8. Native DOCUMENT resolver

PASS.

For `LOGICAL_CURRENT`:

```text
target Artifact
    -> current_revision_id
    -> exact Revision
    -> immutable content_hash
```

The resolver returns an exact read snapshot containing relation ID, binding mode, target document ID, Artifact version, resolved Revision ID, content hash, timestamp, currentness and current Revision ID.

It does not persist the resolved current Revision back into the relation.

For `PINNED_REVISION`, admission and resolution verify that the Revision exists and belongs to exactly `target_ref`.

Historical pins remain resolvable after a newer target revision becomes current.

## 9. VALIDATES / GENERATED_FROM exactness

PASS.

`VALIDATES` is pinned-only. A later target revision does not alter the stored pin and is not automatically validated.

`GENERATED_FROM` is pinned-only. For DOCUMENT targets, exact Revision identity plus immutable Revision content hash supplies the qualified exact identity.

No Evidence is created by either relation declaration, binding or resolution.

## 10. External resolver fail-closed boundary

PASS.

No new external target-kind resolver was authorized or implemented.

`SOURCE_CODE`, `SCHEMA`, `API`, `WORKFLOW`, `DATASET`, `STUDY_LOCK` and `OTHER_ARTIFACT` binding attempts fail closed because core GWF lacks an independently qualified resolver for those kinds.

An opaque caller token is not accepted as verified exact provenance.

## 11. Resolution side-effect boundary

PASS.

DG-P9 binding/resolution does not:

- create or mutate TraceLinks;
- create ImpactSets;
- mutate Revision validity;
- create Evidence;
- create DocumentFinding;
- mutate P7 authority;
- mutate lifecycle;
- edit source documents;
- run dependency propagation;
- persist a LOGICAL_CURRENT resolution cache.

The resolver stops at exact target identity.

## 12. P8 compatibility finding

F-116 was discovered during implementation review before qualification outcome observation.

Historical D8-F13 and D8-F16 asserted that P9 fields did not exist in relation rows. That was a valid phase-bound P8 assertion but not a durable P8 invariant after the explicitly authorized additive DG-P9 migration.

The bounded compatibility change preserves the durable P8 invariant:

- legacy P8 rows remain representable with NULL binding;
- P8 operations do not manufacture Evidence or TraceLinks;
- DocumentRelation and TraceLink remain distinct graph layers.

The frozen D9 matrix, runtime semantics and migration were not weakened to obtain PASS.

F-116 is RESOLVED and Finding OPEN remains 0.

## 13. Frozen fixture and regression evidence

Workflow `35628998000` passed on exact implementation HEAD `9ffd64a1e9b98ea307ed8f9682b88e26570dc208`.

SQLite:

- D9-F1..D9-F20: PASS;
- bounded DG-P9 gate: PASS;
- P8 / Knowledge / Trace / Execution / Decision / Persistence / P4 / P5 / P6 / P7 regressions: PASS;
- full repository regression: PASS;
- compile: PASS.

PostgreSQL 17:

- D9-F1..D9-F20: PASS;
- bounded DG-P9 gate: PASS;
- backend evidence assertion: PASS.

## 14. No later-wave admission

PASS.

DG-P9 implementation creates no:

- DG-P10 change classification;
- DG-P11 DocumentChangeSet;
- DG-P12 relation-aware impact execution;
- TraceLink projection;
- DG-W3 closure;
- GAC state;
- Reference Acquisition state;
- G2E state.

## 15. Implementation QA verdict

```text
frozen DG-P9 spec preserved               PASS
migration 0011                            PASS
new P9 table                              NONE
legacy automatic backfill                 NONE
explicit new-relation binding             PASS
one-time legacy bind                      PASS
Proposal / Approval / Audit               PASS
optimistic relation version               PASS
rebind                                    REJECTED
legality matrix                           PASS
DOCUMENT current resolver                 PASS
DOCUMENT pinned ownership                 PASS
historical pin resolution                 PASS
VALIDATES no-float                        PASS
GENERATED_FROM exactness                  PASS
external unqualified resolver             FAIL_CLOSED
binding cache                             NONE
TraceLink projection                      NONE
impact / validity / Evidence side effects NONE
D9-F1..D9-F20 SQLite                      PASS
D9-F1..D9-F20 PostgreSQL 17               PASS
P8 / Knowledge / Trace regressions        PASS
full repository regression                PASS
compile                                   PASS
Finding OPEN                              0
DG-P10+ opened                            NO
DG-W3 closed                              NO
```

**DG-P9 IMPLEMENTATION QUALIFICATION: PASS**
