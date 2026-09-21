# GWF Governed Artifact Catalog — Reconciled Packing / Implementation Handoff

## 1. Purpose

This handoff supersedes the **planning interpretation** of the original packing handoff after reconciliation with the Documentation Governance implementation frontier and the revised 7-wave plan. The original pack commits remain historical evidence.

This branch remains documentation-only. Do not implement GAC here.

## 2. Lineage

Original package:

- branch: `docs/governed-artifact-catalog-pack`
- original base: `docs/reference-agent-interop-specs`
- original planning base: `f9a638310e095f760b3755583d230d2e65f50f45`
- original pack head before reconciliation: `194c66c3c215ddcc46a6e26dca32e3fb6eda04c5`

Reconciliation finding commit:

- `4ccdecaea6bf3520d2c58552ae1fc4bea548db22`

Implementation frontier consulted:

- DG-P0 final handoff head: `ef322ff0618b83fbfaef40b096cb43f5193d8db0`
- DG-P0 exact-head workflow: `35560831581` — PASS

No DG-P0 code is copied into this documentation branch.

## 3. Frozen ownership model

1. Existing GWF Artifact/Revision/ObjectRef remain canonical payload identity/storage.
2. GAC owns governed catalog membership, publication, cross-project discovery, query execution semantics, scope/access intersection, and optional search adapter boundary.
3. Documentation Governance owns DocumentRecord/DocumentRevision, document validity/lifecycle/QA/findings/dependency semantics.
4. Reference Acquisition owns external retrieval/session/canonical-source provenance and research-side curation.
5. G2E owns Evidence Library domain semantics such as ClaimSignature, applicability, independence, reuse and synthesis.
6. **Shared Library** is the consumer-facing capability built on GAC; it is not another canonical database.
7. Catalog search results remain discovery candidates, not evidence admission.
8. Search backends remain derived/disposable projections.

## 4. Exact roadmap integration

### Earliest GAC implementation gate

```text
DG-P0 PASS
   ↓
Wave 1–4 Documentation Governance
   ↓
DG-W4 PASS
   ↓
GAC-P0 contract qualification
   ↓
GAC-P1 metadata catalog
   ↓
GAC-P2A ObjectRef subjects
   ↓
GAC-P4A generic cross-project pilot
   ↓
DG-GAC-W5
```

DG-P0 alone does **not** authorize GAC.

### Research Shared Library bridge

```text
GAC-P1
   +
RA-P0 / RA-P1
   ↓
RA-P1C Governed Catalog discovery bridge
   ↓
CatalogQueryExecution + catalog snapshot + exact CatalogEntry IDs
   ↓
research reference registry
   ↓
prior-art / novelty interpretation
```

GAC query failure/partial execution must not become a valid “zero matches” conclusion.

### External immutable-reference publication

```text
GAC-P1 + RA-P1
      ↓
GAC-P2B
```

ObjectRef publication does not wait for Reference Acquisition; external immutable-reference publication does.

## 5. Conditional non-blocking work

- **GAC-P3 optional search adapters**: open only when deterministic metadata query is insufficient; not required for minimum Shared Library readiness.
- **GAC-P4B G2E consumer fixture**: open after the G2E Evidence Library Adapter/semantic contract is frozen; not required for GAC core qualification.

## 6. Current implementation frontier

The reconciled 7-wave plan records:

```text
DG-P0 PASS
   ↓
documentation reconciliation
   ↓
DG-P1 next planned
   ↓
STOP
```

DG-P1 is not authorized merely by this handoff.

## 7. Required pre-GAC implementation reconciliation

Before future GAC code:

- re-read exact DG-W4 APIs/evidence;
- re-read KnowledgeKernel/DB/ObjectRef/tenancy state;
- compare exact catalog contracts against then-current GWF primitives;
- create compatibility findings before code if any assumptions drifted;
- revalidate any external search adapter only when GAC-P3 is actually opened;
- re-read the G2E adapter contract only for the G2E-specific consumer fixture.

## 8. Clean handoff criteria

- [x] shared Library ownership unambiguous;
- [x] no second artifact/document/reference registry;
- [x] exact DG-W4 dependency defined;
- [x] Reference Acquisition↔GAC provenance defined;
- [x] GAC-P2 split by real dependencies;
- [x] generic cross-project pilot independent of G2E semantics;
- [x] optional search does not block core readiness;
- [x] 7-wave plan revised without adding an eighth wave;
- [x] DG-P0 status corrected;
- [x] implementation remains stopped.

## 9. Stop

**PACK RECONCILED / IMPLEMENTATION DEFERRED.**
