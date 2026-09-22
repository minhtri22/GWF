# GWF — DG-P6 Lifecycle + Validity Mapping Specification

## 1. Status and authorization boundary

**Item:** DG-P6 — Lifecycle + validity mapping  
**Wave:** 2 — Minimal Documentation Kernel  
**Specification state:** FROZEN FOR DOCUMENT QA  
**Implementation state:** NOT_STARTED  
**HARD dependencies:** DG-P4 + DG-P5  
**Exact dependency base:** DG-P5 formal-close HEAD `58a4cf5f0ca33ca8e15513eb07234dc575b097bc`

The user explicitly authorized DG-P6 pre-implementation specification / dependency qualification only.

This document answers the central design question:

> How should document lifecycle and documentation `BLOCKED` semantics map onto existing GWF Artifact/Revision/Gate state without introducing a conflicting global KnowledgeKernel validity model?

This document does **not** authorize implementation code, migration, DG-W2 closure, Wave 3, DG-P7/P8, GAC, Reference Acquisition, or G2E.

## 2. Exact dependency evidence

DG-P5 is formally closed on the exact base used here:

- DG-P5 final formal-close HEAD: `58a4cf5f0ca33ca8e15513eb07234dc575b097bc`
- final exact-head workflow: `35585295768` PASS
- final evidence artifact: `10632085985`
- artifact digest: `sha256:a357ba058012ace76d52e5749b83a537759fcfd4215aa74c6355ee722c5ce4a5`

Exact inspected governing/runtime blobs:

| Artifact | Exact Git blob |
| --- | --- |
| `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` | `e50d0f17433c6f0ec57f987278a0d24a7bbd4610` |
| `docs/IMPLEMENTATION_7_WAVES_PLAN.md` | `33b3c91af37dba3da8335cecb0ee6d913da53a98` |
| `src/gwr/db.py` | `b9825998757423822ab7ffb22bd37dd202f3e30d` |
| `src/gwr/knowledge.py` | `4f848c2be53451df01b9b91d2705ae3c59aa7bf7` |
| `src/gwr/decision.py` | `bc1320f428bf9279232a7dab0817f3fd71834b5d` |
| `src/gwr/document_facade.py` | `e5af15059c9c0718da0c4a898cb600966ce5204f` |
| `src/gwr/document_qa.py` | `6179e6d756e52d663eddf107e6355873ddda29f6` |
| `src/gwr/runtime.py` | `68e49c4749773b4518a184888e3b8816e905758a` |
| `docs/Finding_checklist.md` | `d54f484d450cb23e1fbfdc747ef63724d16c21d9` |
| `LINEAGE.md` | `92c788a26e88bdb5abf2e7d9fe18348f56043aec` |

Governing specification §§11–12 requires:

- lifecycle and validity are separate;
- lifecycle vocabulary includes at least `DRAFT / IN_REVIEW / ACTIVE / DEPRECATED / SUPERSEDED / ARCHIVED`;
- validity vocabulary includes conceptual `UNVERIFIED / VALID / STALE / BLOCKED`;
- a new revision never inherits `VALID`;
- `BLOCKED` means a known unresolved finding or governance violation prevents clean use.

## 3. Existing state inventory

### 3.1 Artifact lifecycle storage already exists

The existing `artifacts` table already stores:

```text
artifact_id
...
current_revision_id
lifecycle_status
version
```

`KnowledgeKernel.create_artifact(..., lifecycle_status="ACTIVE")` already writes this field.

Therefore DG-P6 does not need a second document lifecycle table or a new lifecycle column.

### 3.2 Revision validity storage already exists

The existing `revisions` table already stores:

```text
status
validity_state
```

The current kernel-wide validity vocabulary is:

```text
VALID
STALE
DIRTY
FAILED
UNVERIFIED
SUPERSEDED
```

This vocabulary is used by generic KnowledgeKernel, WorkUnit readiness, Gate evaluation, impact propagation, recovery and checkpoint logic.

### 3.3 Existing operational BLOCKED already exists at gate/workunit level

`DecisionKernel.evaluate_gate()` already produces:

- `PASS`
- `FAIL`
- `BLOCKED`

for generic adjudication.

WorkUnit readiness also blocks any input whose kernel validity is not the required `VALID`.

Therefore `BLOCKED` already has an operational meaning in GWF without being a persisted revision-validity value.

### 3.4 P5 provides exact-revision QA and finding evidence

DG-P5 provides:

- `document_qa_record` Evidence;
- exact current revision binding;
- immutable QA status `PASS / FAIL / NOT_EVALUATED`;
- governed `document_findings`;
- finding lifecycle;
- effective versus expired/review-due waiver visibility.

This is sufficient evidence input for P6 validity reconciliation.

## 4. Architecture verdict

### 4.1 No schema migration

**DG-P6 does not justify a new table or column.**

Reuse:

```text
document lifecycle
    -> Artifact.lifecycle_status

persisted revision validity
    -> Revision.validity_state

QA / finding evidence
    -> DG-P5 PRIM-EVIDENCE + document_findings

operational blocking
    -> derived document-effective validity
       + existing non-VALID kernel behavior
       + existing Gate/WorkUnit BLOCKED behavior
```

### 4.2 Do not add BLOCKED to KnowledgeKernel.VALIDITY

DG-P6 explicitly rejects adding `BLOCKED` to the global kernel-wide `VALIDITY` set.

Reason:

- `VALIDITY` is shared by every artifact type;
- `DIRTY`, `FAILED`, `STALE` and `SUPERSEDED` already have generic meanings;
- adding a documentation-specific state would silently alter Gate, WorkUnit, checkpoint, impact and recovery semantics for every domain;
- the specification's `BLOCKED` meaning is a document-governance **effective state**, not necessarily a new storage enum.

## 5. Three separate state dimensions

P6 freezes three non-interchangeable dimensions.

### 5.1 Artifact lifecycle

Stored in:

```text
artifacts.lifecycle_status
```

Meaning: whether the logical document participates in current project state and how it is being retired.

### 5.2 Kernel revision validity

Stored in:

```text
revisions.validity_state
```

Meaning: generic kernel validity used by WorkUnits, Gates, impact propagation and recovery.

### 5.3 Document-effective validity

Computed, not stored separately:

```text
UNVERIFIED
VALID
STALE
BLOCKED
```

Meaning: documentation-governance projection for the current governed document revision.

The same document may therefore be:

```text
lifecycle = ACTIVE
kernel validity = UNVERIFIED
effective validity = BLOCKED
```

without semantic contradiction.

## 6. Document lifecycle vocabulary

For `governed_document`, P6 reserves:

```text
DRAFT
IN_REVIEW
ACTIVE
DEPRECATED
SUPERSEDED
ARCHIVED
```

Existing P4 documents created as `ACTIVE` remain valid legacy/current inputs; P6 must not bulk rewrite them.

P6 implementation may expose an optional initial lifecycle argument for new governed documents, but the default must remain `ACTIVE` for P4 compatibility.

## 7. Lifecycle transition contract

### 7.1 P6-executable transitions

The bounded P6 public lifecycle service may execute:

```text
DRAFT -> IN_REVIEW
IN_REVIEW -> DRAFT
IN_REVIEW -> ACTIVE
ACTIVE -> DEPRECATED
DEPRECATED -> ACTIVE
```

Rationale:

- these transitions can be represented faithfully by existing Artifact state;
- they do not require authority-claim transfer or typed relation retirement;
- lifecycle and validity remain separate.

### 7.2 P6-recognized but deferred transitions

P6 recognizes `SUPERSEDED` and `ARCHIVED` as lifecycle values but must **not** claim safe public transition semantics for them yet.

The following are fail-closed in P6:

```text
ACTIVE -> SUPERSEDED
ACTIVE -> ARCHIVED
DEPRECATED -> ARCHIVED
SUPERSEDED -> ARCHIVED
```

until later governance can prove:

- authority ownership is safely transferred/retired (DG-P7);
- inbound/outbound governed dependencies are safely handled (DG-P8 and later impact semantics);
- archival correction policy is known where required.

P6 must not use the absence of later-wave data as evidence that archival/supersession is safe.

### 7.3 Artifact lifecycle SUPERSEDED is not Revision.status SUPERSEDED

Existing revision creation automatically sets the previous immutable revision:

```text
Revision.status = SUPERSEDED
Revision.validity_state = SUPERSEDED
```

This is revision lineage.

It is **not** equivalent to:

```text
Artifact.lifecycle_status = SUPERSEDED
```

which means the logical document itself has been retired by another authority-bearing document.

P6 must not conflate these two meanings.

### 7.4 Lifecycle concurrency and audit

A lifecycle mutation must:

- require exact current `artifact.version`;
- increment `artifact.version`;
- fail on stale version;
- preserve `current_revision_id`;
- preserve revision payload/content;
- append an audit event with prior and new lifecycle state;
- reuse existing project mutability and actor authority checks.

P6 must not create a parallel lifecycle event table.

## 8. Validity reconciliation must be derived, not arbitrary

P6 must not expose:

```text
set_document_validity(target_state)
```

because that would let a caller assert `VALID` without exact QA evidence.

The public semantic operation is:

```text
reconcile_document_validity(document_id)
```

It computes state from:

- current document revision;
- existing kernel validity;
- latest exact-revision DocumentQARecord;
- all active findings on that exact revision;
- effective waiver state;
- later governed blockers when those subsystems exist.

The result contains at least:

```text
document_id
revision_id
lifecycle_state
kernel_validity_state
effective_validity_state
qa_record_id
blocker_codes[]
reconciliation_reason
```

## 9. Effective validity precedence

For the **current** governed document revision, P6 freezes this fail-closed precedence:

```text
1. BLOCKED
2. STALE
3. VALID
4. UNVERIFIED
```

### 9.1 BLOCKED

Effective `BLOCKED` if any of the following is true:

- current exact revision has an `OPEN` finding;
- current exact revision has a `RESOLVED_PENDING_VERIFY` finding;
- current exact revision has a `WAIVED` finding whose waiver is no longer effective;
- latest exact QA has `overall_status = FAIL`;
- kernel validity is `FAILED`;
- current-revision structural invariants are internally inconsistent.

A `FAIL` QA remains BLOCKED even if all findings are effectively waived unless an explicit future gate policy authorizes that waiver to produce clean validity.

P6 therefore does not silently reinterpret waiver as PASS.

### 9.2 STALE

If no BLOCKED condition applies, effective `STALE` if kernel validity is:

- `STALE`; or
- `DIRTY`.

For governed documents, generic `DIRTY` projects to documentation `STALE`: review is required before clean validity.

P6 does not remove `DIRTY` from the generic kernel vocabulary.

### 9.3 VALID

Effective `VALID` only when all are true:

- subject is the document's exact current revision;
- latest exact QA exists;
- latest exact QA is `PASS`;
- there are no active/blocking findings on the exact revision;
- kernel validity is not `STALE`, `DIRTY`, `FAILED` or `SUPERSEDED`;
- the current revision is structurally current.

P6 may promote persisted kernel validity:

```text
UNVERIFIED -> VALID
```

only through this reconciliation.

P6 must not automatically promote `STALE` or `DIRTY` to `VALID`; those states require explicit upstream/impact review semantics from later dependency governance.

### 9.4 UNVERIFIED

Effective `UNVERIFIED` when no stronger state applies and:

- no exact current QA exists; or
- latest exact QA is `NOT_EVALUATED`; or
- current revision has not yet been reconciled after creation.

## 10. Kernel storage mapping

P6 freezes the following compatibility mapping:

| Document-effective validity | Kernel `Revision.validity_state` |
| --- | --- |
| `VALID` | `VALID` |
| `STALE` | preserve `STALE` or `DIRTY` |
| `UNVERIFIED` | `UNVERIFIED` |
| `BLOCKED` caused by QA/finding | must not remain `VALID`; normally `UNVERIFIED` |
| `BLOCKED` caused by kernel `FAILED` | preserve `FAILED` |

No new global kernel state is introduced.

If reconciliation discovers that a revision currently persisted as `VALID` is effectively BLOCKED because of a later exact QA/finding, it must demote kernel validity to `UNVERIFIED` and audit the reason.

If a revision is already `STALE`, `DIRTY` or `FAILED`, reconciliation must not erase that stronger existing kernel fact merely to fit document projection.

## 11. Compatibility with existing Gate and WorkUnit behavior

Generic WorkUnit readiness already requires `VALID`.

Generic Gate evaluation already returns `BLOCKED` for non-required validity states except explicit failure semantics that produce `FAIL`.

Therefore:

```text
document effective BLOCKED
        ↓
kernel revision MUST NOT be VALID
        ↓
generic WorkUnit cannot become READY
        ↓
generic Gate cannot clean-PASS on that revision
```

This provides operational blocking without adding `BLOCKED` to `KnowledgeKernel.VALIDITY`.

P6 does not automatically create a Gate row for every validity reconciliation.

## 12. Exact-revision QA invalidation

P5 already proves:

```text
QA(R1) does not validate R2
```

P6 binds this into validity semantics:

1. R1 may reconcile to `VALID`.
2. DG-P4 creates R2.
3. KnowledgeKernel creates R2 as `UNVERIFIED`.
4. R1 becomes revision-lineage `SUPERSEDED`.
5. R2 has no current QA and therefore effective `UNVERIFIED`.
6. no parent `VALID` state transfers.

This satisfies the DG-W2 exact-revision invalidation requirement without a second document-validity store.

## 13. Lifecycle and validity separation examples

All of the following are valid combinations:

```text
ACTIVE + UNVERIFIED
ACTIVE + VALID
ACTIVE + STALE
ACTIVE + BLOCKED

DRAFT + UNVERIFIED
IN_REVIEW + VALID
DEPRECATED + VALID
DEPRECATED + STALE
```

Lifecycle never hides validity.

P6 must not automatically change lifecycle when QA changes and must not automatically change validity merely because lifecycle changes.

Operational eligibility for new work is a later policy composition of lifecycle + effective validity; P6 does not redefine authority semantics before DG-P7.

## 14. Bounded implementation delta authorized by this specification only after a later explicit implementation gate

If implementation is separately authorized, the bounded delta may include:

1. a document lifecycle/validity service over existing Artifact/Revision/P5 state;
2. validated governed-document lifecycle vocabulary;
3. optimistic lifecycle transitions using existing `artifact.version`;
4. audited validity reconciliation;
5. read-model fields in DocumentFacade such as:
   - `lifecycle_state`;
   - `kernel_validity_state`;
   - `effective_validity_state`;
   - blocker codes;
6. optional initial lifecycle for document registration with default `ACTIVE`;
7. bounded internal KnowledgeKernel support needed to perform an audited derived validity update.

It may not include a new schema table or global `BLOCKED` validity state.

## 15. KnowledgeKernel safety requirements

P6 implementation must preserve:

- `VALIDITY={"VALID","STALE","DIRTY","FAILED","UNVERIFIED","SUPERSEDED"}` unchanged;
- WorkUnit readiness behavior;
- DecisionKernel Gate semantics;
- generic impact propagation;
- checkpoint/recovery state interpretation;
- existing `set_validity_system()` behavior for legacy callers.

Document validity reconciliation must not use `set_validity_system()` as an unaudited public authority to assert arbitrary clean state.

A bounded audited internal update path may be added while preserving existing callers.

## 16. Frozen fixture matrix

### D6-F1 — lifecycle and validity are independent

An `ACTIVE` document with a new revision is allowed to be effective `UNVERIFIED`.

### D6-F2 — new revision begins UNVERIFIED

A new governed-document revision is persisted `UNVERIFIED`.

### D6-F3 — parent VALID never transfers

After R1 is VALID, creating R2 leaves R2 UNVERIFIED and makes R1 historical/superseded.

### D6-F4 — exact PASS promotes only UNVERIFIED

Exact current QA PASS with no blockers may reconcile current kernel `UNVERIFIED -> VALID`.

### D6-F5 — no exact QA cannot promote

Current revision with no exact QA remains effective and kernel `UNVERIFIED`.

### D6-F6 — NOT_EVALUATED cannot promote

Latest exact QA `NOT_EVALUATED` remains effective `UNVERIFIED`.

### D6-F7 — active finding produces effective BLOCKED

An OPEN or RESOLVED_PENDING_VERIFY finding yields effective `BLOCKED` and kernel validity cannot remain `VALID`.

### D6-F8 — FAIL QA is fail-closed despite waiver

Without an explicit future waiver-pass gate policy, latest exact QA `FAIL` remains effective `BLOCKED` even when its findings have effective waivers.

### D6-F9 — stale dominates clean PASS

Kernel `STALE` remains effective `STALE`; exact QA PASS alone does not clear it.

### D6-F10 — DIRTY projects to STALE

Kernel `DIRTY` maps to document-effective `STALE` without changing global kernel vocabulary.

### D6-F11 — FAILED projects to BLOCKED

Kernel `FAILED` maps to document-effective `BLOCKED` and remains persisted `FAILED`.

### D6-F12 — BLOCKED is not added to kernel VALIDITY

Global `KnowledgeKernel.VALIDITY` remains exactly unchanged.

### D6-F13 — generic execution remains safe

A document-effective BLOCKED revision cannot be seen by generic WorkUnit/Gate logic as `VALID`.

### D6-F14 — legal lifecycle transitions use artifact version

Legal P6 transition sequence enforces exact artifact version, increments version and audits state change.

### D6-F15 — invalid lifecycle transition fails closed

For example `DRAFT -> ARCHIVED` is rejected.

### D6-F16 — direct archival is deferred

`ACTIVE/DEPRECATED -> ARCHIVED` is rejected until later authority/dependency retirement semantics exist.

### D6-F17 — artifact supersession and revision supersession remain distinct

Creating R2 supersedes R1 revision lineage but does not set logical document lifecycle to `SUPERSEDED`.

### D6-F18 — P6 does not create authority/relation state

Lifecycle/validity reconciliation creates no authority claim and no typed document relation.

### D6-F19 — no P6 schema migration

Database table set is unchanged by P6 implementation.

### D6-F20 — P5 semantics remain intact

QA Evidence/finding lifecycle, waiver observability and exact-revision behavior remain unchanged.

## 17. Explicit non-scope

DG-P6 must not implement:

- document authority claims or duplicate-authority detection;
- semantic supersession authority transfer;
- typed document relations;
- dependency graph storage;
- impact propagation rules specific to document relations;
- change classification;
- DocumentChangeSet;
- GAC;
- Reference Acquisition;
- G2E;
- bulk lifecycle migration;
- automatic archive/supersession;
- source mutation or auto-fix.

## 18. Schema decision

```text
new tables      = 0
new columns     = 0
new migrations  = 0

reuse:
Artifact.lifecycle_status
Revision.validity_state
P5 QA Evidence
P5 DocumentFinding
existing Audit
existing Gate / WorkUnit non-VALID blocking semantics
```

## 19. Qualification verdict

```text
document lifecycle storage
    -> REUSE Artifact.lifecycle_status

document persisted validity
    -> REUSE Revision.validity_state

document BLOCKED
    -> DERIVED EFFECTIVE STATE
    -> DO NOT ADD TO GLOBAL VALIDITY

generic operational protection
    -> persisted revision must be non-VALID
    -> existing WorkUnit / Gate blocking remains authoritative

new revision invalidation
    -> existing UNVERIFIED + exact QA identity

schema migration
    -> NOT JUSTIFIED

KnowledgeKernel validity vocabulary
    -> MUST REMAIN UNCHANGED
```

**DG-P6 lifecycle/validity dependency specification is ready for exact document QA.**
