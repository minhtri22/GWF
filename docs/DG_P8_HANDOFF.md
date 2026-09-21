# GWF — DG-P8 Typed Document Relations Handoff

## 1. Scope

This handoff records bounded DG-P8 implementation qualification.

DG-P8 implements canonical typed semantic document relations while deliberately leaving the existing TraceLink operational/provenance graph unchanged.

DG-P9+ remain NOT_STARTED / NOT_AUTHORIZED. DG-W3 remains OPEN / NOT_EXECUTED.

## 2. Frozen input identity

- DG-P7 final formal-close HEAD: `cf143d959b338e8d77811f5b2b79789ccbbb20aa`
- DG-P8 frozen spec commit: `211308141106481104590b3d55cdc8c19d6b6d8e`
- DG-P8 frozen spec blob: `d6996951522caa061b29f94d1b1f4f579251adaa`
- DG-P8 pre-implementation qualification HEAD: `cf5a268b58bd9f1bb69df2a4bfeed5a2809380b1`
- pre-implementation QA blob: `65d08b4290db84d03e45ba01c6c12f2142006c54`

## 3. Implementation identity

- initial implementation HEAD: `2081f730e38dc874c29335f77e441ed794fcb885`
- qualified implementation HEAD: `e784d7f56c0cfdf25ca453da48d570cd202ad0cc`
- qualified workflow: `35621561857` PASS

SQLite evidence:
- artifact `10649881388`
- digest `sha256:18b47ce4c730bd66a70de43eb881785281fc141c12a4f72564d4682be618d474`

PostgreSQL evidence:
- artifact `10649322400`
- digest `sha256:62214aecf3fb2347626417ac467f82f32968a576b477ef8a07c387d6d7eaf05b`

## 4. Persistence delivered

Exactly one migration:

```text
0010_v086_dg_p8_document_relations
```

Exactly one P8 canonical table:

```text
document_relations
```

No relation-node/type/event/projection/finding table exists.

## 5. Graph-layer separation delivered

```text
document_relations
    -> canonical semantic declaration graph

trace_links
    -> existing exact-revision operational/provenance graph
```

P8 does not infer semantic relations from TraceLinks and does not project semantic relations into TraceLinks.

`KnowledgeKernel` and TraceLink schema/runtime were not modified.

## 6. Relation declaration

An approved declaration records:

- logical source document;
- exact current source revision at declaration;
- relation type;
- target kind/ref;
- declared invalidation-policy identifier;
- proposal identity;
- Audit.

Proposal apply fails if the source revision changed after proposal freeze.

## 7. Relation retirement

```text
ACTIVE -> RETIRED
```

Retirement is:

- proposal-backed;
- approval-backed;
- optimistic-versioned;
- exact-current-source-revision-bound;
- audited;
- historical-row preserving.

## 8. P8/P9 boundary delivered

P8 contains no:

```text
target_binding_mode
target_revision_or_hash
LOGICAL_CURRENT
PINNED_REVISION
```

Therefore a P8 `VALIDATES` or `GENERATED_FROM` declaration is not by itself exact Evidence/provenance.

No P9 table or runtime was created.

## 9. P7 boundary delivered

P8 `SUPERSEDES` is declaration-only.

It does not mutate:

- authority claims;
- PRIMARY/COMPOSED ownership;
- Artifact lifecycle;
- P6 validity.

## 10. Backend serialization

SQLite uses existing `BEGIN IMMEDIATE`.

PostgreSQL uses a project-row `FOR UPDATE` serialization point for declaration/retirement duplicate/current-state checks.

D8 and bounded gates passed on both backends.

## 11. Negative evidence and repair

Run `35621370994` on `2081f730...` is preserved.

P8 fixtures/gates passed on both backends, but the SQLite targeted regression failed because historical D7-F20 asserted that `document_relations` must not exist.

Repair `e784d7f5...` changed only that regression to the durable P7 invariant: P7 operations must not mutate relation rows if the downstream table exists.

No P8 runtime/spec/schema change was made by the repair.

## 12. Qualification evidence

Run `35621561857` passed:

- D8-F1..D8-F20 SQLite;
- bounded SQLite P8 gate;
- Knowledge/Trace/P4/P5/P6/P7 regressions;
- full repository regression;
- compile;
- D8-F1..D8-F20 PostgreSQL 17;
- bounded PostgreSQL P8 gate.

## 13. Explicit non-scope

DG-P8 did not implement:

- DG-P9 binding modes;
- exact target revision/hash binding;
- relation-to-TraceLink projection;
- DG-P10 change classification;
- DG-P11 DocumentChangeSet;
- automatic authority/lifecycle supersession effects;
- GAC;
- Reference Acquisition;
- G2E;
- automatic source editing.

## 14. Formal-close criterion

DG-P8 is implementation-qualified at `e784d7f56c0cfdf25ca453da48d570cd202ad0cc`.

Formal close requires:

1. commit implementation QA/handoff/finding/plan/lineage package;
2. rerun the same two-backend P8 workflow on that exact handoff HEAD;
3. require D8/gates on both backends and SQLite regressions/full suite/compile to PASS;
4. record exact workflow/artifact identities;
5. commit formal-close state;
6. rerun the same workflow on the final closure HEAD.

DG-P9+ remain unopened and DG-W3 remains OPEN throughout this close.
