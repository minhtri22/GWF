# GWF — DG-P6 Lifecycle + Validity Mapping Handoff

## 1. Scope

This handoff records bounded DG-P6 implementation qualification.

DG-P6 maps governed-document lifecycle and validity onto existing GWF primitives without a new schema and without adding documentation-specific BLOCKED to the global KnowledgeKernel validity vocabulary.

DG-P7/P8 remain NOT_STARTED. DG-W2 remains OPEN.

## 2. Frozen input identity

- DG-P5 final formal-close HEAD: `58a4cf5f0ca33ca8e15513eb07234dc575b097bc`
- DG-P6 pre-implementation qualification HEAD: `dc14622b8e9ff6b66f643567ff9dda27335c8ab0`
- DG-P6 frozen spec commit: `29d3f987f4d23a752563c1e61c5df4e9dd964979`
- DG-P6 frozen spec blob: `155a0c81c291568dbf7d2ba942a9386484f2dd14`
- pre-implementation QA blob: `fa7222de5063e8ce395fdab8417a9508b3c19585`

## 3. Implementation identity

- initial implementation HEAD: `006c198738ef75a915e54c48a7f8400f728a5b25`
- qualified implementation HEAD: `5f5121db3e505204452946d31de8dedb3ca5e73e`

Implementation surface:

- `src/gwr/document_state.py`
- `src/gwr/knowledge.py`
- `src/gwr/runtime.py`
- `src/gwr/document_facade.py`
- `tests/test_dg_p6_lifecycle_validity.py`
- `tools/run_dg_p6_gate.py`
- `.github/workflows/dg-p6-lifecycle-validity.yml`

No schema/migration file changed.

## 4. Lifecycle mapping delivered

Persistent lifecycle ownership remains:

```text
Artifact.lifecycle_status
```

P6-executable transitions:

```text
DRAFT -> IN_REVIEW
IN_REVIEW -> DRAFT
IN_REVIEW -> ACTIVE
ACTIVE -> DEPRECATED
DEPRECATED -> ACTIVE
```

Every transition uses exact Artifact.version optimistic concurrency and append-only Audit.

Archive/logical-supersession transitions remain fail-closed until later authority/relation dependencies exist.

## 5. Validity mapping delivered

Persistent generic validity remains:

```text
Revision.validity_state
```

Global vocabulary remains unchanged.

Document-effective projection:

```text
BLOCKED > STALE > VALID > UNVERIFIED
```

No document validity table exists.

No global BLOCKED state exists.

## 6. Reconciliation delivered

Public document semantic:

```text
reconcile_document_validity(document_id)
```

not:

```text
set_document_validity(target_state)
```

Reconciliation reads exact P5 QA/finding state and generic kernel state.

It may:

```text
UNVERIFIED -> VALID
VALID -> UNVERIFIED
```

only under frozen P6 rules.

It does not clear STALE/DIRTY/FAILED from QA alone.

## 7. Generic execution compatibility

A document-effective BLOCKED revision cannot remain persisted VALID after reconciliation.

Therefore existing generic WorkUnit/Gate checks remain protective without any kernel-wide enum change.

D6-F13 verifies an existing `prior_art_ready` Gate observes `INPUT_UNVERIFIED` and returns BLOCKED.

## 8. Exact-revision behavior

P4/P5/P6 compose as:

```text
R1 exact QA PASS
        ↓
reconcile R1 VALID
        ↓
create R2
        ↓
R1 revision lineage SUPERSEDED
R2 UNVERIFIED
QA(R1) historical only
logical document lifecycle unchanged
```

No validity inheritance is introduced.

## 9. Qualification evidence

Negative evidence preserved:

- run `35598139354`
- HEAD `006c198738ef75a915e54c48a7f8400f728a5b25`
- failure: D6-F13 fixture referenced nonexistent gate type;
- runtime/spec/schema were not changed by repair.

Qualified evidence:

- run `35598284725`
- HEAD `5f5121db3e505204452946d31de8dedb3ca5e73e`
- conclusion: PASS
- artifact: `10638170391`
- digest: `sha256:891484a4f0d54b85c5101fc7d7944b10b2c10af19a4df88e771ed1718c3b31b5`

Qualification stages:

- D6-F1..D6-F20 PASS;
- zero-migration/global-validity gate PASS;
- Knowledge/Execution/Decision/P4/P5 regressions PASS;
- full repository regression PASS;
- compile PASS.

## 10. Explicit non-scope preserved

DG-P6 did not implement:

- document authority claims;
- duplicate-authority detection;
- typed document relations;
- semantic logical supersession;
- archive execution;
- dependency graph;
- document impact propagation;
- DocumentChangeSet;
- GAC;
- Reference Acquisition;
- G2E.

## 11. Formal-close criterion

DG-P6 is implementation-qualified at `5f5121db3e505204452946d31de8dedb3ca5e73e`.

Formal close requires:

1. commit this implementation-QA/handoff/finding/plan/lineage package;
2. run the exact DG-P6 workflow on that handoff HEAD;
3. require D6-F1..D6-F20, bounded gate, regressions, full suite and compile to PASS;
4. preserve exact workflow/artifact identities;
5. commit formal-close state;
6. re-run exact workflow on the final closure HEAD.

DG-P7/P8 remain unopened and DG-W2 remains OPEN throughout this close.


## 12. Exact-handoff qualification

The committed DG-P6 handoff HEAD `d25454481f0d972c83225e10d3d09b1bb997faf9` was requalified on its exact HEAD.

- exact-head workflow: `35598699495`
- conclusion: **PASS**
- evidence artifact: `10637792150`
- artifact digest: `sha256:370e34264c5ac33dec4c1303a6a8abc5e4e5065a4935fa70e46ae0128b89bfe4`

D6-F1..D6-F20, zero-migration/global-validity gate, targeted Knowledge/Execution/Decision/P4/P5 regressions, full regression and compile all passed again.

**DG-P6 status: FORMALLY CLOSED.**

This does not adjudicate DG-W2. DG-W2 remains OPEN / NOT_EXECUTED. DG-P7/P8 remain NOT_STARTED. GAC remains locked until DG-W4 PASS.
