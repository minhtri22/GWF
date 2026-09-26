# Project Recovery Decision — BPS-M05-B Checklist

## Identity

```text
WORKFLOW_ID       = PROJECT_RECOVERY_DECISION
OWNER             = BPS-M05
ROUTE             = /app/projects/:projectId/execution
PROTOCOL          = BPS-QA-FIRST-DEFERRED-UAT-v1 + STRICT_MUTATION_BOUNDARY
STATUS            = QA_FINDINGS_CLOSED / CI_PENDING / FINAL_UAT_PENDING
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

- [x] PR-01 Phase projection marks each protocol recovery proposal with a source-backed human-decision capability.
- [x] PR-02 Capability uses the same governance `APPROVE` authorization path as runtime policy, not role-name inference.
- [x] PR-03 `can_decide=true` only when proposal status is exactly `WAITING_HUMAN`, actor is HUMAN and APPROVE authorization succeeds.
- [x] PR-04 Allowed decisions are exactly `APPROVED` and `REJECTED`.
- [x] PR-05 Existing decision history remains read-only and authoritative.
- [x] PR-06 AUTO_APPROVED/HUMAN_APPROVED/REJECTED/APPLIED proposals never expose a decision control.

### B. Browser mutation contract

- [x] PR-07 Add cookie-authenticated nested decision endpoint under exact project + phase + proposal identity.
- [x] PR-08 Missing/unauthorized project is non-disclosing.
- [x] PR-09 Phase must belong to the exact project.
- [x] PR-10 Proposal must belong to the exact phase and project; cross-phase/cross-project proposal IDs are rejected without mutation.
- [x] PR-11 Endpoint delegates the state transition to `AgentExecutionProtocolService.decide_recovery()`; no duplicate browser mutation semantics.
- [x] PR-12 Service remains the final HUMAN + APPROVE authority boundary.
- [x] PR-13 Decision input is exact `APPROVED | REJECTED`; invalid values fail through existing validation semantics.
- [x] PR-14 Optional human reason is persisted unchanged; browser does not invent a reason.
- [x] PR-15 Duplicate/replayed decision after proposal leaves WAITING_HUMAN fails and does not create a second decision.
- [x] PR-16 Browser endpoint returns exact proposal/decision identity and resulting persisted status.

### C. Governed UI

- [x] PR-17 WAITING_HUMAN proposal visibly distinguishes action, target step, risk class, normative-change flag and rationale.
- [x] PR-18 Authorized human sees Approve and Reject controls only on decision-eligible proposals.
- [x] PR-19 Unauthorized/non-human actor sees truthful decision-required state without mutation buttons.
- [x] PR-20 Optional reason input is explicit and is not auto-populated.
- [x] PR-21 Approve requires governed confirmation showing exact project/phase/proposal and consequence.
- [x] PR-22 Reject requires governed confirmation showing exact project/phase/proposal and consequence.
- [x] PR-23 Confirmation cancel performs no request and no state mutation.
- [x] PR-24 UI prevents concurrent duplicate submission while one recovery decision is in flight.
- [x] PR-25 Successful decision invalidates stale phase/Home data and reconstructs state from backend.
- [x] PR-26 Failed decision leaves authoritative state intact and shows explicit error.
- [x] PR-27 No Apply recovery / retry / verify / handoff / complete action is introduced.

### D. QA

- [x] PR-28 Test APPROVED path persists one decision, HUMAN_APPROVED proposal and RUNNING protocol status.
- [x] PR-29 Test REJECTED path persists one decision, REJECTED proposal and BLOCKED protocol status.
- [x] PR-30 Test non-HUMAN actor denial.
- [x] PR-31 Test actor lacking APPROVE denial and `can_decide=false`.
- [x] PR-32 Test cross-project and cross-phase proposal binding rejection.
- [x] PR-33 Test duplicate/replay rejection without duplicate decision row.
- [x] PR-34 Test invalid decision value is rejected.
- [x] PR-35 Existing Bearer recovery-decision route remains unchanged/compatible.
- [x] PR-36 No schema, authority-policy, retry, recovery-application or protocol-stage semantics are changed.
- [x] PR-37 Findings are recorded/fixed/rechecked until implementation `FAIL=0 OPEN=0 COUNT=0`.

## QA findings and adjudication

| Finding | Class | Observation | Correction | State |
| --- | --- | --- | --- | --- |
| PR-F01 | authority boundary | initial product projection had proposal state but no source-backed indication whether the current human could decide | derive capability by invoking the same governance `APPROVE` authorization path, gated by HUMAN actor type and exact WAITING_HUMAN status | PASS |
| PR-F02 | identity binding | Bearer decision API accepts proposal ID directly; browser product requires stronger route-context binding | add nested project + phase + proposal browser endpoint and reject any cross-phase/cross-project mismatch before mutation | PASS |
| PR-F03 | UI governance | recovery proposal was previously dumped as raw JSON, so human decision context/action consequence was not explicit | render exact proposal fields, optional blank reason, authority state and governed confirmation for Approve/Reject | PASS |
| PR-F04 | scope control | service exposes `apply_recovery`, but it has no equivalent qualified HUMAN browser authority contract | keep Apply/retry/verify/handoff/complete absent from M05-B; browser opens decision only | PASS |
| PR-F05 | stale state | a successful decision changes protocol/attention state and could leave phase/Home projections stale | invalidate phase/Overview/Home caches, reconstruct phase from backend and refresh Home attention after mutation | PASS |
| PR-F06 | regression contract | M05-A static test still listed Approve/Reject among forbidden controls after M05-B authorization | narrow the historical regression to actions that remain forbidden: Apply/Retry/Verify/Handoff/Complete | PASS |
| PR-F07 | QA coverage | cross-phase/cross-project checks did not by themselves prove unauthorized-project non-disclosure | add a separately owned hidden project and assert browser mutation returns 404 with zero decision rows | PASS |
| PR-F08 | UI request safety | cancel/no-request and decision-only transport needed direct source assertions | add static UI regression proving confirmation precedes POST, cancel returns early, duplicate-submit guard exists, and mutation function contains no apply/verify/handoff/complete path | PASS |

Deterministic assistant QA on implementation HEAD `f30cf12150b4945626e03650d0f385c5be2f2e0a`:

- `web/app.js` syntax parse: PASS;
- duplicate HTML IDs: 0;
- missing static `$("#id")` targets: 0;
- capability is true only for WAITING_HUMAN + HUMAN + full governance APPROVE authorization;
- allowed browser decisions are exactly APPROVED and REJECTED;
- nested mutation endpoint is cookie-authenticated and validates exact project, phase and proposal ownership;
- endpoint delegates the transition to `AgentExecutionProtocolService.decide_recovery()`; browser does not duplicate transition semantics;
- source service remains the final HUMAN + APPROVE authority boundary;
- optional reason is passed exactly as typed and defaults to blank rather than fabricated prose;
- confirmation occurs before the request; cancel returns before any mutation state/request;
- concurrent duplicate submission is guarded by `projectRecoveryMutation`;
- UI never emits Apply recovery, verify, handoff, complete or retry mutation paths;
- successful decision reconstructs phase state from backend and refreshes Home attention;
- failed decision leaves current authoritative detail intact and renders explicit error;
- tests cover APPROVED, REJECTED, no-APPROVE viewer, non-HUMAN actor, cross-phase, cross-project, unauthorized-project, invalid decision, replay/no duplicate and Bearer compatibility.

Exact-head GitHub Actions at adjudication time are queued across the shared workflow set. No queued workflow is counted as PASS.

```text
TOTAL_IMPLEMENTATION_ITEMS = 37
IMPLEMENTATION_PASS        = 37
IMPLEMENTATION_FAIL        = 0
IMPLEMENTATION_OPEN        = 0
IMPLEMENTATION_COUNT       = 0

QA_FINDINGS_FAIL           = 0
QA_FINDINGS_OPEN           = 0
QA_FINDINGS_COUNT          = 0

CI_EXECUTION               = PENDING_EXTERNAL_CAPACITY
TARGETED_RUNTIME_EXECUTION = PENDING_EXTERNAL_EXECUTION
FINAL_UAT                  = DEFERRED
UNIT_STATE                 = QA_FINDINGS_CLOSED / CI_PENDING / FINAL_UAT_PENDING
```
