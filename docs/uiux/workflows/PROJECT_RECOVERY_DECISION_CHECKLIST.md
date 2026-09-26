# Project Recovery Decision — BPS-M05-B Checklist

## Identity

```text
WORKFLOW_ID       = PROJECT_RECOVERY_DECISION
OWNER             = BPS-M05
ROUTE             = /app/projects/:projectId/execution
PROTOCOL          = BPS-QA-FIRST-DEFERRED-UAT-v1 + STRICT_MUTATION_BOUNDARY
STATUS            = CHECKLIST_FROZEN / IMPLEMENTATION_PENDING
BASE_HEAD         = 623747ba27a8106649bba75b6610e6e697bd1075
FINAL_UAT         = DEFERRED
```

## Source-derived boundary

The qualified human browser action is only the decision on a persisted Agent Protocol recovery proposal whose status is exactly `WAITING_HUMAN`.

`AgentExecutionProtocolService.decide_recovery()` requires:
- persisted proposal status = `WAITING_HUMAN`;
- actor type = `HUMAN`;
- governance action `APPROVE` for the exact project;
- decision exactly `APPROVED | REJECTED`.

The following remain runtime/protocol mechanics and are NOT opened as browser controls in M05-B:
`propose_recovery`, `apply_recovery`, `verify`, `write_handoff`, `complete`, `start_execution`, checklist updates, and v0.2 `apply_recovery_plan`.

## Frozen checklist

### A. Read capability

- [ ] PR-01 Phase projection marks each protocol recovery proposal with a source-backed human-decision capability.
- [ ] PR-02 Capability uses the same governance `APPROVE` authorization path as runtime policy, not role-name inference.
- [ ] PR-03 `can_decide=true` only when proposal status is exactly `WAITING_HUMAN`, actor is HUMAN and APPROVE authorization succeeds.
- [ ] PR-04 Allowed decisions are exactly `APPROVED` and `REJECTED`.
- [ ] PR-05 Existing decision history remains read-only and authoritative.
- [ ] PR-06 AUTO_APPROVED/HUMAN_APPROVED/REJECTED/APPLIED proposals never expose a decision control.

### B. Browser mutation contract

- [ ] PR-07 Add cookie-authenticated nested decision endpoint under exact project + phase + proposal identity.
- [ ] PR-08 Missing/unauthorized project is non-disclosing.
- [ ] PR-09 Phase must belong to the exact project.
- [ ] PR-10 Proposal must belong to the exact phase and project; cross-phase/cross-project proposal IDs are rejected without mutation.
- [ ] PR-11 Endpoint delegates the state transition to `AgentExecutionProtocolService.decide_recovery()`; no duplicate browser mutation semantics.
- [ ] PR-12 Service remains the final HUMAN + APPROVE authority boundary.
- [ ] PR-13 Decision input is exact `APPROVED | REJECTED`; invalid values fail through existing validation semantics.
- [ ] PR-14 Optional human reason is persisted unchanged; browser does not invent a reason.
- [ ] PR-15 Duplicate/replayed decision after proposal leaves WAITING_HUMAN fails and does not create a second decision.
- [ ] PR-16 Browser endpoint returns exact proposal/decision identity and resulting persisted status.

### C. Governed UI

- [ ] PR-17 WAITING_HUMAN proposal visibly distinguishes action, target step, risk class, normative-change flag and rationale.
- [ ] PR-18 Authorized human sees Approve and Reject controls only on decision-eligible proposals.
- [ ] PR-19 Unauthorized/non-human actor sees truthful decision-required state without mutation buttons.
- [ ] PR-20 Optional reason input is explicit and is not auto-populated.
- [ ] PR-21 Approve requires governed confirmation showing exact project/phase/proposal and consequence.
- [ ] PR-22 Reject requires governed confirmation showing exact project/phase/proposal and consequence.
- [ ] PR-23 Confirmation cancel performs no request and no state mutation.
- [ ] PR-24 UI prevents concurrent duplicate submission while one recovery decision is in flight.
- [ ] PR-25 Successful decision invalidates stale phase/Home data and reconstructs state from backend.
- [ ] PR-26 Failed decision leaves authoritative state intact and shows explicit error.
- [ ] PR-27 No Apply recovery / retry / verify / handoff / complete action is introduced.

### D. QA

- [ ] PR-28 Test APPROVED path persists one decision, HUMAN_APPROVED proposal and RUNNING protocol status.
- [ ] PR-29 Test REJECTED path persists one decision, REJECTED proposal and BLOCKED protocol status.
- [ ] PR-30 Test non-HUMAN actor denial.
- [ ] PR-31 Test actor lacking APPROVE denial and `can_decide=false`.
- [ ] PR-32 Test cross-project and cross-phase proposal binding rejection.
- [ ] PR-33 Test duplicate/replay rejection without duplicate decision row.
- [ ] PR-34 Test invalid decision value is rejected.
- [ ] PR-35 Existing Bearer recovery-decision route remains unchanged/compatible.
- [ ] PR-36 No schema, authority-policy, retry, recovery-application or protocol-stage semantics are changed.
- [ ] PR-37 Findings are recorded/fixed/rechecked until implementation `FAIL=0 OPEN=0 COUNT=0`.

## Initial count

```text
TOTAL = 37
PASS  = 0
FAIL  = 0
OPEN  = 37
COUNT = 37
```
