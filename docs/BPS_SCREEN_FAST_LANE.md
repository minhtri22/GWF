# BPS Screen Fast Lane

## Status

```text
PROTOCOL_ID = BPS-SCREEN-FAST-LANE-v1
APPROVED    = USER_APPROVED
DATE        = 2026-09-23
APPLIES_TO  = Browser Product Surface screen implementation
```

This protocol supersedes per-module heavy formal-close/UAT ceremony for ordinary browser product work. It does not weaken backend, authority, security, evidence, or scientific semantics.

## One-screen loop

Every screen executes exactly:

```text
READ RELEVANT DOCUMENTS
        ↓
WRITE SCREEN CHECKLIST
        ↓
IMPLEMENT
        ↓
SELF-QA AGAINST CHECKLIST
        ↓
CHECKLIST COUNT = 0
        ↓
USER FINAL UAT
explicit P / F answers
        ↓
SCREEN_PASS
        ↓
NEXT SCREEN
```

Rules:

1. Before touching screen code, reread the documents relevant to that screen.
2. Produce a bounded checklist derived from those documents before implementation.
3. Do not silently add requirements that are unsupported by the governing documents.
4. Implement only the current screen plus minimal shared UI plumbing needed by that screen.
5. The assistant owns ordinary defect discovery and correction.
6. Before user handoff, every checklist item must be PASS and `COUNT=0`.
7. User UAT is final visual/operator acceptance for that screen and is answered with explicit `P` or `F`.
8. A screen with any `F` remains open; repair only the affected scope, self-QA again, then repeat UAT.
9. After all requested UAT items are `P`, mark `SCREEN_PASS` and move immediately to the next screen.
10. No separate PRE_LOCAL/formal-close commit is required per ordinary screen.

## What remains strict

Immediately leave Fast Lane and use the stricter governance path if a screen requires any of:

- backend/database schema change;
- new or changed authority/authentication/security semantics;
- scientific/evidence semantics;
- changing an already-qualified API contract;
- a new destructive or authoritative mutation;
- cross-tenant/cross-project authorization changes;
- weakening a frozen backend invariant;
- unexplained regression in a qualified backend subsystem.

Pure browser/layout/navigation/composition/read-projection work remains in Fast Lane.

## Shared-component rule

A later screen may improve a shared browser component used by an earlier passed screen without opening a governance amendment. The assistant must recheck the impacted earlier-screen checklist items before handoff. If behavior changes materially, include those affected observations in the current screen UAT.

## UAT rule

UAT questions must be concrete observable statements and use:

```text
P = PASS
F = FAIL
```

The user is not asked to run developer diagnostics unless a real local-environment issue prevents browser UAT.

## Completion model

`SCREEN_PASS` is the browser delivery unit.

Modules such as BPS-M01…M10 remain useful for architecture and ownership, but they are no longer mandatory formal-close boundaries for ordinary screen work.

Cross-screen/end-to-end integration is still checked after the relevant screens exist.
