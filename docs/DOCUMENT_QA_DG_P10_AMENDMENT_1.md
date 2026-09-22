# GWF — DG-P10 Amendment 1 QA

## 1. QA identity

**Subject amendment:** `docs/DG_P10_AMENDMENT_1_DOCUMENT_MUTATION_POLICY.md`  
**Amendment commit:** `a124ebdc74f69a71121d88e2eb510bb3637abe50`  
**Amendment blob:** `1a5bda28c1caf9d57601e2ad5112f63edb4c3379`  
**Reconciled DG-P10 spec commit:** `54ca635bcb322902a28f4a987af19c37e14b59ae`  
**Reconciled DG-P10 spec blob:** `2aeec0ff251567e784372ffb700d11c37fa9a037`  
**Amended Documentation Integrity spec blob:** `c1b863784b3ca4bbada7020017818c2340fe5d3b`  
**Implementation executed during QA:** NO

## 2. QA question

Does the amended §14 policy introduce a serious governance regression that should block DG-P10 implementation?

**Verdict: NO unresolved serious regression.**

The amendment changes the authority model materially, but each high-risk interaction is explicitly bounded and fail-closed.

DG-P10 implementation may proceed under the amended contract.

## 3. Recovery AUTO compatibility

**Risk:** CRITICAL if document AUTO were interpreted as broadening v0.8.2 recovery AUTO.

Existing runtime semantics freeze `recovery_mode` in `phase_execution_protocols`, while v0.8.2 limits AUTO recovery to LOW-risk, non-normative recovery inside retry budget.

The amendment explicitly reuses only the **effective mode value/snapshot**, not recovery semantics.

Document mutation authority is a separate policy decision.

**Verdict: PASS. Recovery authority is not broadened.**

## 4. GOV/FROZEN protection

**Risk:** CRITICAL if AUTO could bypass frozen governance.

The amended matrix gives `GOV/FROZEN`:

```text
BLOCK_REQUIRES_EXPLICIT_USER_AUTHORIZATION
```

for both AUTO and HUMAN_APPROVE.

No caller boolean can unlock it.

Any later implementation of the unlock must use attributable human/user authorization bound to the exact document, base revision and intended change.

P10 itself may record BLOCK but may not implement a hidden bypass.

**Verdict: PASS.**

## 5. AUTO scope containment

AUTO is not project-global.

It is valid only when:

- an active PhaseExecution exists;
- its persisted protocol mode is AUTO;
- document enrollment metadata identifies an owner phase/workunit;
- current execution scope matches that owner;
- no stronger lock applies.

Unknown/different ownership falls to human approval.

**Verdict: PASS.**

## 6. HUMAN_APPROVE preservation

An effective HUMAN_APPROVE PhaseExecution never becomes AUTO because of change class or path.

The policy produces `REQUIRE_HUMAN_APPROVAL`.

**Verdict: PASS.**

## 7. Change class versus authority

The previous conservative rule:

```text
NORMATIVE+ => always human approval
```

is intentionally superseded.

The amended contract separates:

```text
what changed?       -> change class
who may mutate?     -> role/state + active workflow mode + ownership + locks
```

Therefore an owned mutable PHASE document may receive a NORMATIVE change under AUTO, while an EDITORIAL change to GOV/FROZEN remains blocked.

This is consistent with the user-authorized workflow model and does not weaken frozen governance.

**Verdict: PASS.**

## 8. Pre-commit identity correction

The first P10 qualification assumed an exact candidate commit/blob before the candidate was committed.

That is incompatible with agent-generated documents.

The amended contract correctly freezes pre-commit identity as:

- exact base Revision/Artifact/source;
- proposed active path;
- proposed content SHA-256;
- next version;
- expected archive path;
- PhaseExecution/mode snapshot.

Post-write exact commit/blob is resolved only after DG-P11 executes the SHA-safe source change.

**Verdict: PASS.**

## 9. Version/archive lineage

The physical contract is deterministic:

```text
docs/<scope>/<name>.vN.md
        ↓
docs/<scope>/archive/<name>.vN.md
docs/<scope>/<name>.vN+1.md
```

The archive preserves exact old bytes, cannot be overwritten and cannot be revised in place.

The new active document links to the archived previous version.

Stable GWF Artifact/Revision identity remains canonical; physical paths are human-readable projections.

**Verdict: PASS.**

## 10. P10/P11 boundary

A serious scope error would be P10 directly executing the three-path repository mutation.

The amended contract forbids that.

P10 produces classification Evidence, mutation-authority decision and deterministic lineage plan.

DG-P11 owns the concrete SHA-safe DocumentChangeSet:

- CREATE archive;
- CREATE next active version;
- DELETE prior active version.

**Verdict: PASS.**

## 11. Legacy-layout safety

Existing flat-layout GWF/project documents are not silently moved, enrolled or granted AUTO authority.

Enrollment/migration requires a later explicit operation.

**Verdict: PASS.**

## 12. Persistence/schema impact

No new table or migration is required.

P10 reuses:

- current Revision payload for enrolled role/state/version/owner metadata;
- existing `phase_execution_protocols.recovery_mode` snapshot as mode input;
- PRIM-EVIDENCE for `document_change_classification`;
- existing Artifact/Revision identity.

**Verdict: PASS.**

## 13. Specialized policy ownership

The amendment does not absorb later programs:

- DG-P11 — concrete DocumentChangeSet/source mutation;
- DG-P12+ — dependency/impact propagation;
- DG-P15 — append-only validation and authority supersession execution;
- DG-P16 — generated-document provenance.

**Verdict: PASS.**

## 14. Finding adjudication

- F-131 CRITICAL — AUTO/recovery semantic collision: resolved by configuration-only inheritance.
- F-132 HIGH — unconditional NORMATIVE+ human floor conflicts workflow authority: superseded by orthogonal authority matrix.
- F-133 HIGH — future candidate commit/blob cannot exist pre-commit: resolved by proposed path/content digest.
- F-134 HIGH — AUTO ownership could become project-global: resolved by owner phase/workunit scope.
- F-135 CRITICAL — GOV/FROZEN AUTO bypass: rejected; explicit user authorization is mandatory.
- F-136 HIGH — physical archive could replace canonical identity: rejected; Artifact/Revision remains canonical.
- F-137 HIGH — P10 could execute multi-path source mutation and preempt P11: rejected; P10 plan-only.
- F-138 MEDIUM — legacy flat docs could be silently migrated: rejected; explicit enrollment required.
- F-139 HIGH — mutable project/domain configuration could change authority mid-phase: rejected; persisted PhaseExecution protocol snapshot is authoritative.
- F-140 HIGH — boolean/caller assertion could impersonate user authorization: rejected; no such bypass is allowed.
- F-141 HIGH — archive overwrite/in-place correction could rewrite history: rejected; archive is immutable and corrections are new records.

All amendment findings are resolved at specification level.

## 15. Serious-impact adjudication

```text
unresolved CRITICAL findings = 0
unresolved HIGH findings     = 0
Finding OPEN                 = 0
schema migration required    = NO
recovery semantics changed   = NO
GOV/FROZEN weakened          = NO
P10/P11 boundary violated    = NO
legacy auto-migration        = NO
```

**AMENDMENT QA: PASS**

The user's conditional authorization is satisfied: bounded DG-P10 implementation may proceed from the exact amended qualification HEAD after this QA package is committed.
