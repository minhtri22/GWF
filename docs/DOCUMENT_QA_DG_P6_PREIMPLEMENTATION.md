# GWF — DG-P6 Pre-Implementation Document QA

## 1. QA identity

**Subject:** `docs/DG_P6_LIFECYCLE_VALIDITY_MAPPING_SPEC.md`  
**Subject commit:** `29d3f987f4d23a752563c1e61c5df4e9dd964979`  
**Subject blob:** `155a0c81c291568dbf7d2ba942a9386484f2dd14`  
**Dependency base:** DG-P5 final formal-close HEAD `58a4cf5f0ca33ca8e15513eb07234dc575b097bc`  
**Dependency final exact-head workflow:** `35585295768` PASS  
**Dependency final artifact:** `10632085985`  
**Artifact digest:** `sha256:a357ba058012ace76d52e5749b83a537759fcfd4215aa74c6355ee722c5ce4a5`  
**QA type:** pre-implementation lifecycle/validity dependency qualification  
**Implementation executed:** NO

This QA binds only the exact DG-P6 specification blob above.

## 2. Governing requirement verification

Documentation Integrity §§11–12 requires:

- lifecycle and validity remain separate;
- lifecycle vocabulary includes DRAFT, IN_REVIEW, ACTIVE, DEPRECATED, SUPERSEDED, ARCHIVED;
- validity vocabulary conceptually includes UNVERIFIED, VALID, STALE, BLOCKED;
- a new revision never inherits VALID;
- BLOCKED represents known unresolved finding/governance violation preventing clean use.

The 7-wave plan additionally requires BLOCKED to be mapped without prematurely adding a conflicting global validity state.

## 3. Existing primitive fit matrix

| Requirement | Existing primitive | Fit | Verdict |
| --- | --- | --- | --- |
| logical document lifecycle | `Artifact.lifecycle_status` | strong | reuse |
| lifecycle optimistic concurrency | `Artifact.version` | strong | reuse |
| revision persisted validity | `Revision.validity_state` | strong | reuse |
| new revision starts unverified | KnowledgeKernel create_revision | exact | reuse |
| stale/dirty impact state | KnowledgeKernel impact propagation | exact/compatible | preserve |
| exact QA status | DG-P5 QA Evidence | exact | reuse |
| active finding blocker | DG-P5 DocumentFinding | exact | reuse |
| operational block | Gate/WorkUnit non-VALID behavior | compatible | reuse |
| transition/history attribution | Audit | strong | reuse |
| document-specific BLOCKED storage | none | not required | derive, do not store globally |

## 4. Schema qualification

PASS.

Existing schema already contains the two required persistent state axes:

```text
Artifact.lifecycle_status
Revision.validity_state
```

P5 supplies QA/finding evidence.

No new table, column or migration is justified.

A dedicated `document_lifecycle`, `document_validity` or `document_state` table would duplicate existing authoritative state.

## 5. Global BLOCKED-state compatibility QA

PASS.

Current kernel validity vocabulary is shared across all artifact types:

```text
VALID
STALE
DIRTY
FAILED
UNVERIFIED
SUPERSEDED
```

Adding BLOCKED globally would modify semantics consumed by generic WorkUnit, Gate, impact, recovery and checkpoint logic.

The frozen P6 design instead defines:

```text
document effective BLOCKED
    -> document-layer projection
    -> persisted kernel state must not remain VALID
    -> generic execution therefore remains blocked
```

This preserves KnowledgeKernel compatibility while satisfying documentation governance semantics.

## 6. Effective-state precedence QA

The frozen precedence:

```text
BLOCKED > STALE > VALID > UNVERIFIED
```

is deterministic and fail-closed.

BLOCKED comes from known finding/governance failure.

STALE/DIRTY remains distinct from known finding failure.

VALID requires exact PASS QA and no blockers.

UNVERIFIED remains the absence of current successful adjudication.

## 7. QA/finding mapping QA

PASS.

- no exact current QA -> UNVERIFIED;
- exact current QA NOT_EVALUATED -> UNVERIFIED;
- exact current QA FAIL -> BLOCKED;
- OPEN finding -> BLOCKED;
- RESOLVED_PENDING_VERIFY finding -> BLOCKED;
- ineffective expired/review-due waiver -> BLOCKED;
- exact current PASS + zero blocking findings -> eligible for VALID reconciliation;
- effective waiver does not silently convert immutable FAIL QA into PASS.

The last rule correctly preserves the governing requirement that waiver-to-clean-PASS is policy-controlled rather than automatic.

## 8. STALE / DIRTY / FAILED compatibility QA

PASS.

P6 does not replace generic kernel semantics:

- STALE remains STALE;
- DIRTY projects to document-effective STALE;
- FAILED projects to document-effective BLOCKED;
- reconciliation must not erase these facts merely because a later QA record looks clean.

In particular, P6 may promote only:

```text
UNVERIFIED -> VALID
```

from exact clean QA.

It may not use QA alone to clear STALE/DIRTY/FAILED.

## 9. Generic execution safety QA

PASS.

Existing generic execution already requires kernel VALID for clean readiness/gates.

Therefore any effective document BLOCKED state must ensure the persisted revision is not VALID.

For a later FAIL/finding discovered on a revision currently persisted VALID, P6 must demote the kernel state to UNVERIFIED and audit the reason.

No new Gate result/state is necessary.

## 10. Lifecycle storage and transition QA

PASS with bounded later implementation.

P6 correctly reuses `Artifact.lifecycle_status`.

Lifecycle mutation must use exact `Artifact.version`, increment it and append Audit.

Allowed P6-executable transitions are bounded to cases not requiring future authority/relation semantics:

```text
DRAFT -> IN_REVIEW
IN_REVIEW -> DRAFT
IN_REVIEW -> ACTIVE
ACTIVE -> DEPRECATED
DEPRECATED -> ACTIVE
```

This preserves lifecycle/validity separation.

## 11. Archival and logical supersession QA

PASS by fail-closed deferral.

`SUPERSEDED` and `ARCHIVED` are recognized lifecycle values, but safe transition into them depends on authority/dependency semantics not yet implemented.

P6 therefore rejects public archival/logical-supersession transitions rather than assuming missing DG-P7/P8 data means there are no blockers.

This is not technical debt: it is an explicit dependency gate.

## 12. Revision SUPERSEDED versus document SUPERSEDED

PASS.

Existing KnowledgeKernel automatically marks an old revision as:

```text
Revision.status = SUPERSEDED
Revision.validity_state = SUPERSEDED
```

when a new revision is created.

That is revision lineage only.

P6 explicitly forbids interpreting it as:

```text
Artifact.lifecycle_status = SUPERSEDED
```

This prevents accidental retirement of a logical document when only one revision was replaced.

## 13. Arbitrary validity setter QA

The existing `set_validity_system(revision_id, state)` is a generic internal setter and is not evidence-based adjudication.

P6 correctly avoids exposing a public `set_document_validity(target_state)`.

The P6 public semantic operation must be derived reconciliation:

```text
reconcile_document_validity(document_id)
```

with audit.

This protects VALID from being caller-asserted without exact QA evidence.

## 14. Exact-revision invalidation QA

PASS.

Existing P4/P5 behavior already provides:

```text
R1 VALID
    ↓ create R2
R1 revision lineage -> SUPERSEDED
R2 kernel validity -> UNVERIFIED
QA(R1) remains historical
QA(R1) does not validate R2
```

P6 maps this behavior directly and does not introduce a second invalidation store.

## 15. P4 compatibility QA

PASS.

Existing P4 governed documents may be:

```text
lifecycle = ACTIVE
validity = UNVERIFIED
```

This is allowed because lifecycle and validity are intentionally independent.

P6 must not bulk rewrite existing documents merely to force a DRAFT-first lifecycle.

An optional initial lifecycle field may be added later while preserving ACTIVE as the compatibility default.

## 16. Fixture adequacy

D6-F1 through D6-F20 cover:

- lifecycle/validity independence;
- new-revision UNVERIFIED;
- no VALID inheritance;
- exact PASS promotion;
- no-QA and NOT_EVALUATED behavior;
- active finding BLOCKED;
- fail-closed waiver semantics;
- STALE/DIRTY/FAILED projection;
- global VALIDITY immutability;
- generic execution safety;
- lifecycle concurrency/audit;
- invalid archival transition;
- logical versus revision supersession;
- no authority/relation side effects;
- zero migration;
- P5 regression.

**Fixture verdict: PASS.**

## 17. Finding adjudication

- F-73 — global BLOCKED enum collision risk: resolved by derived effective validity.
- F-74 — lifecycle and validity conflation risk: resolved by separate Artifact lifecycle and Revision validity axes.
- F-75 — arbitrary validity assertion risk: resolved by evidence-derived reconciliation only.
- F-76 — STALE/DIRTY overwrite risk: resolved by prohibiting QA-only clearing.
- F-77 — waiver-to-PASS ambiguity: resolved fail-closed absent explicit policy.
- F-78 — premature archive/supersession risk: resolved by dependency-gated deferral.
- F-79 — revision SUPERSEDED versus logical document SUPERSEDED ambiguity: resolved by explicit semantic separation.
- F-80 — lifecycle mutation concurrency/history risk: resolved via Artifact.version + Audit.
- F-81 — P4 ACTIVE+UNVERIFIED compatibility risk: resolved by no bulk migration and independent axes.
- F-82 — roadmap frontier carried the DG-P5 handoff run instead of the later final closure run: resolved by updating plan state to exact formal-close HEAD/run.

All are specification/document-state resolved. None implies runtime implementation has occurred.

## 18. Scope QA

PASS.

The frozen P6 specification does not authorize:

- schema migration;
- global BLOCKED validity enum;
- DG-P7 authority;
- DG-P8 document relation storage;
- semantic authority transfer;
- archive/supersession execution;
- DocumentChangeSet;
- GAC;
- Reference Acquisition;
- G2E;
- automatic source edits.

## 19. Document QA verdict

```text
DG-P4 dependency                      = PASS
DG-P5 dependency                      = PASS
lifecycle -> Artifact.lifecycle       = PASS
validity -> Revision.validity_state   = PASS
BLOCKED -> derived effective state    = PASS
global VALIDITY extension             = REJECTED
new schema/migration                  = REJECTED
exact-revision invalidation reuse     = PASS
generic Gate/WorkUnit compatibility   = PASS
archive/supersession dependency gate  = PASS
D6-F1..D6-F20                         = ADEQUATE
findings F-73..F-82                   = RESOLVED
OPEN                                  = 0
```

**DG-P6 PRE-IMPLEMENTATION QUALIFICATION: PASS**

Implementation remains NOT_STARTED.
