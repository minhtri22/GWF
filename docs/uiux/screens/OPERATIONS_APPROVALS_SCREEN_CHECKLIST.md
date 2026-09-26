# Operations Approvals Screen — BPS-M03 Checklist

## Identity

```text
SCREEN_ID        = OPERATIONS_APPROVALS
OWNER            = BPS-M03
ROUTE            = /app/operations/approvals
PROTOCOL         = BPS-QA-FIRST-DEFERRED-UAT-v1 + STRICT_GOVERNANCE for decisions
STATUS           = QA_FINDINGS_CLOSED / CI_PENDING / FINAL_UAT_PENDING
BASE_HEAD        = b9aefed3a77f3953b853d8fb7394638219d155e5
FINAL_UAT        = DEFERRED
```

## Governing sources

- `docs/UI_UX_PRODUCT_ARCHITECTURE_SPEC.md` §14.1, §17.2, §25.3, §26.4, §27.
- `docs/BROWSER_PRODUCT_SURFACE_SPEC.md` §12.
- `src/gwr/governance.py` authenticated approve/reject semantics.
- `src/gwr/api.py` existing Bearer proposal/decision API.
- BPS-M03 Operations route/navigation established by Operations Runs.

## Frozen checklist

### A. Authorized projection

- [x] OA-01 Add authenticated `GET /browser/operations/approvals`.
- [x] OA-02 Include proposals only from actor-visible projects; hidden project/proposal existence is not leaked.
- [x] OA-03 Return pending proposal action, proposer, created time, exact project/scope, resource refs, frozen payload, exact payload hash and approval policy.
- [x] OA-04 Parse structured resource refs/frozen payload server-side without mutating them.
- [x] OA-05 Return decision history with exact proposal hash, approver, decision, scope, conditions and timestamp.
- [x] OA-06 Expose `can_approve` from existing project `APPROVE` authority without inventing a role.
- [x] OA-07 Distinguish complete/empty/error state.

### B. Browser decision bridge — strict

- [x] OA-08 Browser approve uses HttpOnly-session token server-side and invokes `approve_proposal_authenticated`.
- [x] OA-09 Browser reject uses HttpOnly-session token server-side and invokes `reject_proposal_authenticated`.
- [x] OA-10 Both decisions require exact current payload hash; stale/mismatched hash fails closed.
- [x] OA-11 Unauthorized proposal is returned as not-found/non-disclosing.
- [x] OA-12 Reject requires a non-empty operator reason in the browser contract.
- [x] OA-13 Native approval policy checks remain authoritative, including actor type/role/self-approval rules.
- [x] OA-14 Decision response/state is authoritative and auditable; no optimistic browser decision state.
- [x] OA-15 UI never implies that APPROVED automatically means the proposal's underlying governed change was applied.

### C. UI

- [x] OA-16 Promote Approvals subroute to LIVE while Runs remains LIVE.
- [x] OA-17 Pending queue is primary; recent decision history is separately visible.
- [x] OA-18 Selecting a proposal exposes exact project, proposal ID, action, refs, frozen payload, policy and payload hash.
- [x] OA-19 Approve action is shown only when `can_approve=true`.
- [x] OA-20 Reject requires reason input.
- [x] OA-21 Approve/Reject use `ConfirmGovernedAction` with exact proposal ID/hash/project and consequences.
- [x] OA-22 After decision, projection and Home attention are refreshed from backend.
- [x] OA-23 No localStorage/mock/synthetic decision.
- [x] OA-24 Back/Forward/reload/theme/sidebar/session behavior does not regress.

### D. QA

- [x] OA-25 Tests cover authorized pending projection + decision history.
- [x] OA-26 Tests prove hidden proposals absent.
- [x] OA-27 Tests prove viewer can inspect but cannot approve; approver can act according to policy.
- [x] OA-28 Tests cover exact-hash mismatch and reject reason.
- [x] OA-29 Existing Bearer proposal/approve/reject APIs remain valid.
- [x] OA-30 Approval/rejection audit events are preserved.
- [x] OA-31 No schema/new approval semantics introduced.
- [x] OA-32 Findings fixed/rechecked to implementation `FAIL=0 OPEN=0 COUNT=0`.

## QA findings and adjudication

| Finding | Result |
| --- | --- |
| OA-F01 Initial projection exposed frozen proposal payload to project VIEWER; global inbox must be bounded to REVIEW or APPROVE authority | FIXED / RECHECKED |
| OA-F02 Error rendering retained stale counts/inspector and decision history omitted persisted rejection reason | FIXED / RECHECKED |
| OA-F03 Native self-approval policy was preserved by code but not locked by targeted regression | FIXED / RECHECKED |

Deterministic QA: JavaScript parse PASS; all static selectors resolve to unique HTML IDs; exact-hash confirmation and decision-vs-apply boundary are explicit; Reviewer can inspect without deciding; Approver decisions route through authenticated governance kernel; hidden proposals are excluded; rejection reason and decision audit provenance are retained.

```text
TOTAL_IMPLEMENTATION_ITEMS = 32
IMPLEMENTATION_PASS        = 32
IMPLEMENTATION_FAIL        = 0
IMPLEMENTATION_OPEN        = 0
IMPLEMENTATION_COUNT       = 0
QA_FINDINGS_COUNT          = 0
CI_EXECUTION               = PENDING_EXTERNAL_CAPACITY
FINAL_UAT                  = DEFERRED
UNIT_STATE                 = QA_FINDINGS_CLOSED / CI_PENDING / FINAL_UAT_PENDING
```
