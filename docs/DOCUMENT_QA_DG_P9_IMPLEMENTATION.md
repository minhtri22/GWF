# GWF — DG-P9 Implementation QA

## 1. QA identity

**Authorization HEAD:** `52ae1ebded1f9a942cee55d6d2ce061b5bcb8290`  
**Implementation branch:** `v0.8.6-dg-p9-implementation`  
**Qualified implementation HEAD:** `91e1ae66c3e50b1ae411090b6e74290ef464c9fe`  
**Frozen specification commit:** `1a9f8737e36392c8a8db49b93c9371ceee16085f`  
**Frozen specification blob:** `73e1d7c8c01ea954af2a65e1df1942b4f95738f3`  
**Qualified workflow:** `35796204999` PASS

SQLite evidence:
- artifact `10724460452`
- digest `sha256:c420cf294ebb841a9ae58e29c5883949df82fa43853a68a03dd533d3d92858e2`

PostgreSQL 17 evidence:
- artifact `10723854711`
- digest `sha256:5045b161708a036073a3e508ec50b7cb8e58c727f27efa95dd12b444f1777faa`

## 2. Bounded implementation surface

Changed from the authorization HEAD:

- `src/gwr/migrations.py`
- `src/gwr/document_relation.py`
- `src/gwr/runtime.py`
- `tests/test_dg_p8_relations.py`
- `tests/test_dg_p9_binding.py`
- `tools/run_dg_p9_gate.py`
- `.github/workflows/dg-p9-binding.yml`

Not changed:

- frozen DG-P9 specification;
- `src/gwr/knowledge.py`;
- `trace_links` schema/runtime;
- DG-P7 authority runtime;
- DG-P10+ runtime/schema;
- GAC / Reference Acquisition / G2E.

## 3. Persistence QA

PASS.

Exactly one migration was added:

```text
0011_v086_dg_p9_relation_binding
```

It extends only:

```text
document_relations
    + target_binding_mode
    + target_revision_or_hash
```

No P9 table was added. No `trace_links` schema change was made.

Legacy P8 rows remain NULL/UNBOUND because the migration contains no UPDATE/default/backfill.

## 4. Binding legality QA

PASS.

Exactly two bound modes exist:

```text
LOGICAL_CURRENT
PINNED_REVISION
```

Frozen legality is enforced centrally:

- DEPENDS_ON — dual-mode;
- REFERENCES — dual-mode;
- MUST_ALIGN_WITH — LOGICAL_CURRENT only;
- SUPERSEDES — PINNED_REVISION only;
- DERIVED_FROM — PINNED_REVISION only;
- VALIDATES — PINNED_REVISION only;
- IMPLEMENTS — dual-mode;
- GENERATED_FROM — PINNED_REVISION only.

Invalidation policy cannot override this matrix.

## 5. New relation atomic binding

PASS.

New relation declarations require an explicit legal binding in the frozen Proposal payload and are persisted bound in the same relation creation mutation.

A new relation cannot be created with NULL binding through the service.

## 6. Legacy one-time binding

PASS.

Legacy transition is:

```text
UNBOUND
  -> Proposal
  -> Approval
  -> optimistic relation.version check
  -> BIND_DOCUMENT_RELATION
  -> Audit
```

Successful binding increments relation version.

After binding, rebind is rejected. Semantic change requires retire + create.

## 7. Native DOCUMENT resolver

PASS.

LOGICAL_CURRENT resolves at read time through:

```text
target_ref Artifact
  -> Artifact.current_revision_id
  -> exact Revision
  -> Revision.content_hash
```

The current revision is not written back to the relation.

PINNED_REVISION verifies that the exact Revision belongs to the target document and resolves that immutable historical Revision even after the document advances.

Resolution returns exact identity/hash snapshot plus currentness information.

## 8. External target boundary

PASS / fail-closed.

SOURCE_CODE, SCHEMA, API, WORKFLOW, DATASET, STUDY_LOCK and OTHER_ARTIFACT are not treated as verified current/exact identities without an independently qualified resolver.

Opaque caller tokens are not accepted as provenance proof.

No external resolver was introduced.

## 9. Pure resolution / no later-wave side effects

PASS.

Binding resolution does not create or mutate:

- TraceLink;
- ImpactSet;
- Revision validity;
- Evidence;
- DocumentFinding;
- authority;
- lifecycle;
- source documents.

No binding cache or relation-to-TraceLink projection exists.

DG-P10+ remain unopened.

## 10. Frozen fixture and regression evidence

Workflow `35796204999` on exact HEAD `91e1ae66c3e50b1ae411090b6e74290ef464c9fe` completed SUCCESS.

SQLite:
- D9-F1..D9-F20 PASS;
- bounded DG-P9 gate PASS;
- bounded schema/semantic assertions PASS;
- P8 + Knowledge/Trace + P4/P5/P6/P7 regressions PASS;
- full repository regression PASS;
- compile PASS.

PostgreSQL 17:
- D9-F1..D9-F20 PASS;
- P8 regression PASS;
- bounded DG-P9 gate PASS;
- backend equivalence assertions PASS.

No outcome-driven semantic repair was required.

A connector write invocation was rejected before mutation because the connector required `sha` rather than `content_sha`; the retry used the same intended patch and produced no repository state from the rejected call. This is tooling evidence, not a scientific/implementation failure.

## 11. Implementation QA verdict

```text
frozen DG-P9 spec preserved                  PASS
0011 migration                              PASS
document_relations-only persistence         PASS
legacy NULL/no auto-backfill                PASS
new relation born bound                     PASS
BIND_DOCUMENT_RELATION governance           PASS
one-time bind/no-rebind                     PASS
legality matrix                             PASS
DOCUMENT logical-current resolution         PASS
DOCUMENT pinned resolution                  PASS
historical pin preservation                 PASS
external resolver fail-closed               PASS
TraceLink projection                        NONE
impact/validity/Evidence/finding side effect NONE
D9-F1..D9-F20 SQLite                        PASS
D9-F1..D9-F20 PostgreSQL 17                 PASS
P8 regressions                              PASS
P4/P5/P6/P7 + Knowledge/Trace regressions   PASS
full regression                             PASS
compile                                     PASS
DG-P10+ opened                              NO
DG-W3 closed                                NO
Finding OPEN                                0
```

**DG-P9 IMPLEMENTATION QUALIFICATION = PASS**

Formal close is not performed by this QA step.

## 12. Exact-handoff requalification

The committed implementation QA/handoff package at exact HEAD:

`041b59ea3e4a1363df3bd4349aa97424061d6c76`

was requalified without runtime/spec changes by workflow:

`35796638275` — PASS

SQLite exact-head evidence:
- artifact `10724536102`
- digest `sha256:eb7c80441605105b769da0ad227c9434c0d357aec2d67de6cdad2a6dd9e1075f`

PostgreSQL 17 exact-head evidence:
- artifact `10724685879`
- digest `sha256:a1a5ae14fc6dfc870cb41105b8d3e22cc9402fa032abe405ea0bcdc80c05f0a7`

The run HEAD, branch HEAD and both artifact HEADs are identical.

The frozen specification blob remains:
`73e1d7c8c01ea954af2a65e1df1942b4f95738f3`.

## 13. Formal-close adjudication

Formal-close criteria:

- exact committed QA/handoff HEAD requalified — PASS;
- D9-F1..D9-F20 SQLite — PASS;
- bounded SQLite DG-P9 gate — PASS;
- P8/P4/P5/P6/P7/Knowledge/Trace regressions — PASS;
- full repository regression — PASS;
- compile — PASS;
- D9-F1..D9-F20 PostgreSQL 17 — PASS;
- P8 PostgreSQL regression — PASS;
- bounded PostgreSQL DG-P9 gate/equivalence — PASS;
- exact artifact identities/digests available — PASS;
- frozen specification unchanged — PASS;
- implementation finding OPEN count — 0;
- DG-P10+ runtime/schema opened — NO;
- DG-W3 closure attempted — NO.

**DG-P9 FORMAL-CLOSE ADJUDICATION = PASS**

DG-P9 is formally closed by this closure state, subject to the required exact closure-HEAD requalification of the documentation-only close commit.

No DG-P10 authorization is implied.
