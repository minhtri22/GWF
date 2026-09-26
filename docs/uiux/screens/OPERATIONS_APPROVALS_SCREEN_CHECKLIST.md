# Operations Approvals Screen — BPS-M03 Checklist

## Identity

```text
SCREEN_ID        = OPERATIONS_APPROVALS
OWNER            = BPS-M03
ROUTE            = /app/operations/approvals
PROTOCOL         = BPS-QA-FIRST-DEFERRED-UAT-v1 + STRICT_GOVERNANCE for decisions
STATUS           = CHECKLIST_FROZEN / IMPLEMENTATION_PENDING
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

- [ ] OA-01 Add authenticated `GET /browser/operations/approvals`.
- [ ] OA-02 Include proposals only from actor-visible projects; hidden project/proposal existence is not leaked.
- [ ] OA-03 Return pending proposal action, proposer, created time, exact project/scope, resource refs, frozen payload, exact payload hash and approval policy.
- [ ] OA-04 Parse structured resource refs/frozen payload server-side without mutating them.
- [ ] OA-05 Return decision history with exact proposal hash, approver, decision, scope, conditions and timestamp.
- [ ] OA-06 Expose `can_approve` from existing project `APPROVE` authority without inventing a role.
- [ ] OA-07 Distinguish complete/empty/error state.

### B. Browser decision bridge — strict

- [ ] OA-08 Browser approve uses HttpOnly-session token server-side and invokes `approve_proposal_authenticated`.
- [ ] OA-09 Browser reject uses HttpOnly-session token server-side and invokes `reject_proposal_authenticated`.
- [ ] OA-10 Both decisions require exact current payload hash; stale/mismatched hash fails closed.
- [ ] OA-11 Unauthorized proposal is returned as not-found/non-disclosing.
- [ ] OA-12 Reject requires a non-empty operator reason in the browser contract.
- [ ] OA-13 Native approval policy checks remain authoritative, including actor type/role/self-approval rules.
- [ ] OA-14 Decision response/state is authoritative and auditable; no optimistic browser decision state.
- [ ] OA-15 UI never implies that APPROVED automatically means the proposal's underlying governed change was applied.

### C. UI

- [ ] OA-16 Promote Approvals subroute to LIVE while Runs remains LIVE.
- [ ] OA-17 Pending queue is primary; recent decision history is separately visible.
- [ ] OA-18 Selecting a proposal exposes exact project, proposal ID, action, refs, frozen payload, policy and payload hash.
- [ ] OA-19 Approve action is shown only when `can_approve=true`.
- [ ] OA-20 Reject requires reason input.
- [ ] OA-21 Approve/Reject use `ConfirmGovernedAction` with exact proposal ID/hash/project and consequences.
- [ ] OA-22 After decision, projection and Home attention are refreshed from backend.
- [ ] OA-23 No localStorage/mock/synthetic decision.
- [ ] OA-24 Back/Forward/reload/theme/sidebar/session behavior does not regress.

### D. QA

- [ ] OA-25 Tests cover authorized pending projection + decision history.
- [ ] OA-26 Tests prove hidden proposals absent.
- [ ] OA-27 Tests prove viewer can inspect but cannot approve; approver can act according to policy.
- [ ] OA-28 Tests cover exact-hash mismatch and reject reason.
- [ ] OA-29 Existing Bearer proposal/approve/reject APIs remain valid.
- [ ] OA-30 Approval/rejection audit events are preserved.
- [ ] OA-31 No schema/new approval semantics introduced.
- [ ] OA-32 Findings fixed/rechecked to implementation `FAIL=0 OPEN=0 COUNT=0`.

## Initial count

```text
TOTAL = 32
PASS  = 0
FAIL  = 0
OPEN  = 32
COUNT = 32
```
