# BPS QA-First Deferred-UAT Protocol

## Status

```text
PROTOCOL_ID        = BPS-QA-FIRST-DEFERRED-UAT-v1
APPROVED           = USER_APPROVED
APPROVAL_DATE      = 2026-09-26
APPLIES_TO         = Browser Product Surface implementation
SUPERSEDES         = per-screen mandatory user UAT in BPS-SCREEN-FAST-LANE-v1
FINAL_USER_UAT     = ONE INTEGRATED PRODUCT UAT AFTER IMPLEMENTATION + QA CLOSE
```

This protocol changes the delivery cadence, not the product authority model.

Backend-before-UI, authoritative state, security, tenancy, exact identity, no-fake-data, no-fake-action, immutable revision/binding, and strict-governance triggers remain unchanged.

## 1. User-approved execution model

Implementation now proceeds continuously:

```text
READ RELEVANT DOCUMENTS
        ↓
FREEZE SCREEN / WORKFLOW CHECKLIST
        ↓
IMPLEMENT
        ↓
ASSISTANT QA
        ↓
RECORD FINDINGS
        ↓
FIX FINDINGS
        ↓
RE-QA
        ↓
CHECKLIST COUNT = 0
        ↓
FREEZE AS QA_CLOSED
        ↓
NEXT SCREEN / WORKFLOW / MODULE
        ↓
...
        ↓
ALL IMPLEMENTATION CHECKLISTS COUNT = 0
        ↓
CROSS-SCREEN / CROSS-WORKFLOW INTEGRATION QA
        ↓
INTEGRATION CHECKLIST COUNT = 0
        ↓
HAND OFF ONE FINAL PRODUCT UAT TO USER
```

The user is not required to stop after every screen to provide P/F acceptance.

## 2. Per-screen / per-workflow loop

Every implementation unit executes:

1. reread the governing documents relevant to that exact surface/workflow;
2. write a bounded checklist before product-code mutation;
3. implement only documented/qualified behavior;
4. run assistant-owned QA against the checklist;
5. record every defect/gap as an explicit finding;
6. fix findings;
7. rerun affected QA;
8. repeat until `FAIL=0`, `OPEN=0`, `COUNT=0`;
9. mark the unit `QA_CLOSED / FINAL_UAT_PENDING`;
10. continue immediately to the next legal unit.

No ordinary user UAT occurs at step 9.

## 3. Required QA content

QA remains at least equivalent to the existing QA1→QA6 discipline:

- **QA1 Scope completeness** — every frozen requirement implemented; later blocked capability not pulled forward.
- **QA2 Functional correctness** — positive/negative behavior matches qualified semantics.
- **QA3 Authoritative-state correctness** — backend/database remains product truth; refresh/re-entry reconstructs state.
- **QA4 Governance/security correctness** — authorization, tenancy, revision/hash/version, lifecycle and secret boundaries preserved.
- **QA5 Automated QA/regression** — targeted tests plus required affected/full subsystem gates; SQLite/PostgreSQL where the qualified contract requires them.
- **QA6 UI/UX conformance** — approved information architecture/visual baseline, shell parity, loading/empty/error/partial states, exact IDs, no fake controls.

A unit does not advance merely because code exists.

## 4. Finding discipline

Each active unit maintains a finding checklist.

Every finding is one of:

```text
OPEN
FIXED_PENDING_RECHECK
PASS
DEFERRED_BLOCKED   # only when governing docs explicitly make it future-gated
```

For the active implemented scope, completion requires:

```text
FAIL  = 0
OPEN  = 0
COUNT = 0
```

A future-gated item may be recorded as `DEFERRED_BLOCKED` only when it is outside the currently authorized product scope; it must not be hidden by marking it PASS.

## 5. Unit completion state

Before final user UAT, use:

```text
QA_CLOSED / FINAL_UAT_PENDING
```

rather than requiring `SCREEN_PASS` from the user.

Historical screens that already received user UAT remain valid historical evidence and are not rewritten.

## 6. Final integrated UAT

User UAT happens only after:

1. all currently authorized screens/workflows/modules are implemented;
2. every implementation checklist has `COUNT=0`;
3. shared-shell regression findings are closed;
4. cross-screen/workflow integration QA is complete;
5. the final integration checklist has `COUNT=0`;
6. the assistant has prepared one coherent product UAT package.

The final UAT should cover end-to-end product journeys rather than isolated implementation trivia.

Minimum current-product journeys include, where implemented:

```text
login/session
Home -> Projects
Projects -> Project
Project -> Overview
Project -> Execution / Recovery
Project -> Governance / Configuration / Access
Operations -> Run / Approval / Audit / Runtime
Research Packages -> Project
Project -> Library / Documents / Relations
System -> GitHub / Access / Diagnostics / Settings
Back / Forward / refresh / theme / sidebar / actor / attention
```

The final UAT also verifies meaningful error/unavailable/authorization states.

## 7. Final-UAT failure handling

If final UAT finds defects:

```text
UAT finding
   ↓
record finding
   ↓
fix affected implementation
   ↓
rerun affected unit QA
   ↓
rerun integration QA affected by the change
   ↓
all affected checklist counts = 0
   ↓
return only the necessary UAT scope
```

A failed observation is never silently converted to PASS.

## 8. Strict-governance boundary remains

Deferred user UAT does **not** authorize bypassing strict governance.

Before implementation, leave ordinary browser Fast Lane whenever work requires:

- backend/database schema change;
- new or changed authority/authentication/security semantics;
- scientific/evidence semantic change;
- change to an already-qualified API contract;
- a new destructive or authoritative mutation;
- cross-tenant/cross-project authorization change;
- weakening a frozen backend invariant;
- unexplained regression in a qualified backend subsystem.

For those units, the assistant performs the necessary governance/spec/contract/atomicity review and QA before implementation continues.

The user does not need to perform per-screen UAT merely because strict governance was required. User input is requested only when there is an actual product/semantic decision that cannot be resolved from the governing documents.

## 9. Dependency handling

Do not create fake intermediate surfaces merely to preserve a nominal module number.

If a documented workflow depends on a not-yet-LIVE destination or prerequisite:

1. record the dependency;
2. continue with other unblocked work;
3. implement the prerequisite at its proper governed boundary;
4. return to the blocked workflow;
5. enable it only when the end-to-end documented path is real.

Topological product dependency correctness outranks cosmetic module ordering.

## 10. Reporting to the user

During implementation, normal progress reports should be concise and need not request UAT.

The final handoff must provide:

- exact implementation HEAD;
- implemented screen/workflow/module inventory;
- per-unit checklist summary;
- findings opened/fixed;
- explicit remaining future-blocked capability;
- automated/regression/integration QA evidence;
- final global `FAIL / OPEN / COUNT`;
- one final UAT checklist / one-click entry path.

The target state before asking the user to UAT is:

```text
IMPLEMENTATION_COMPLETE = true
QA_FAIL                 = 0
QA_OPEN                 = 0
QA_COUNT                = 0
INTEGRATION_COUNT       = 0
FINAL_USER_UAT          = READY
```


## 11. External QA-runner capacity rule

An external runner that has not started because it is `queued` / capacity-blocked is **not PASS** and must never be reported as PASS.

It is also not an implementation finding because no product/test result exists yet.

When all assistant-owned review, deterministic static checks, test definitions and finding repairs are complete, but the exact-head external runner remains capacity-blocked, the unit may advance with:

```text
IMPLEMENTATION_FINDINGS_FAIL = 0
IMPLEMENTATION_FINDINGS_OPEN = 0
IMPLEMENTATION_FINDINGS_COUNT = 0
CI_EXECUTION = PENDING_EXTERNAL_CAPACITY
UNIT_STATE = QA_FINDINGS_CLOSED / CI_PENDING / FINAL_UAT_PENDING
```

Constraints:

1. the pending CI identity/run is recorded;
2. no queued test is called PASS;
3. a later CI failure immediately reopens the affected unit;
4. all deferred automated executions must PASS, and any failure must be repaired/retested, before integrated QA can reach `COUNT=0`;
5. final user UAT is forbidden while any mandatory CI execution remains pending.

This rule prevents external infrastructure capacity from serially blocking implementation while preserving QA authority.
