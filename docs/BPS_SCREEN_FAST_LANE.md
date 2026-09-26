# BPS Screen Fast Lane

## Status

```text
PROTOCOL_ID = BPS-SCREEN-FAST-LANE-v1
APPROVED    = USER_APPROVED / UAT-CADENCE SUPERSEDED
DATE        = 2026-09-23
SUPERSEDED  = 2026-09-26 by BPS-QA-FIRST-DEFERRED-UAT-v1
APPLIES_TO  = Browser Product Surface screen implementation
```

This protocol superseded per-module heavy formal-close/UAT ceremony for ordinary browser product work. Its **per-screen user-UAT cadence is now superseded** by `docs/BPS_QA_FIRST_DEFERRED_UAT.md`.

The retained parts are: screen-bounded implementation, assistant-owned QA/finding repair, strict-governance triggers, shared-component regression discipline, backend authority, and no-fake-state/action rules.

Current execution does **not** stop for user UAT after every screen.

## Current screen/workflow loop

Every ordinary implementation unit now executes:

```text
READ RELEVANT DOCUMENTS
        ↓
WRITE SCREEN / WORKFLOW CHECKLIST
        ↓
IMPLEMENT
        ↓
SELF-QA AGAINST CHECKLIST
        ↓
RECORD FINDINGS
        ↓
FIX + RE-QA
        ↓
CHECKLIST COUNT = 0
        ↓
QA_CLOSED / FINAL_UAT_PENDING
        ↓
NEXT SCREEN / WORKFLOW
```

Rules:

1. Before touching code, reread the documents relevant to the exact surface/workflow.
2. Produce a bounded checklist before implementation.
3. Do not silently add requirements unsupported by governing documents.
4. Implement only qualified/documented behavior plus minimal shared plumbing.
5. The assistant owns ordinary defect discovery, finding capture, repair, and re-QA.
6. A unit advances only with `FAIL=0`, `OPEN=0`, `COUNT=0`.
7. No ordinary per-screen user UAT is required.
8. User UAT is deferred until the currently authorized browser product is implemented and integration QA also reaches `COUNT=0`.
9. Historical screen UAT evidence already collected remains valid and is not rewritten.
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

Final user UAT is governed by `docs/BPS_QA_FIRST_DEFERRED_UAT.md`.

The assistant must first finish implementation, close every per-unit QA/finding checklist, close integration QA, and report global `COUNT=0`. The user is not used as a per-screen defect-discovery loop.

## Completion model

`QA_CLOSED / FINAL_UAT_PENDING` is the implementation delivery state before final user acceptance.

Modules such as BPS-M01…M10 remain useful for architecture and ownership. Cross-screen/end-to-end integration is mandatory before the one final user UAT.

After final integrated UAT passes, the delivered browser product may be marked accepted at the integrated boundary.
