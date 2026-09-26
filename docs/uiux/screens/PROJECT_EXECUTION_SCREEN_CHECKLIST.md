# Project Execution — BPS-M05-A Checklist

## Identity

```text
SCREEN_ID        = PROJECT_EXECUTION
OWNER            = BPS-M05
ROUTE            = /app/projects/:projectId/execution
PROTOCOL         = BPS-QA-FIRST-DEFERRED-UAT-v1
STATUS           = CHECKLIST_FROZEN / IMPLEMENTATION_PENDING
BASE_HEAD        = 8dcef0c606ed98f60bb6bb7b0c3517d263b4e539
FINAL_UAT        = DEFERRED
```

## Governing sources

- `AGENTS.md`
- `docs/BPS_QA_FIRST_DEFERRED_UAT.md`
- `docs/BPS_MODULE_EXECUTION_MODEL.md` — BPS-M05 Execution + Recovery.
- `docs/UI_UX_PRODUCT_ARCHITECTURE_SPEC.md` §9 and normative §34A.4.
- `docs/BROWSER_PRODUCT_SURFACE_SPEC.md` §10 and §11.
- `src/gwr/process_inspector.py` authoritative process/phase read model.
- `src/gwr/agent_protocol.py` persisted LOAD→PREFLIGHT→PLAN→EXECUTE→VERIFY→HANDOFF→COMPLETE protocol.
- `src/gwr/decision.py`, `src/gwr/execution.py`, `src/gwr/research_orchestrator.py`.
- existing `/product/*` process/phase/event APIs as compatibility source, not browser-cookie contract.

## Scope and boundary

M05-A is read-only. It makes the project Execution route LIVE and exposes current persisted v0.2→v0.8.3 execution state.

It MUST NOT add recovery/approval/protocol mutations. Those remain M05-B strict actions.

The browser must not expose hidden model chain-of-thought. Persisted plans, checklists, protocol events, problems, recovery proposals and handoffs are operational records and may be shown only as stored authoritative state.

## Frozen checklist

### A. Authorized browser execution projection

- [ ] PE-01 Add cookie-authenticated `GET /browser/projects/{project_id}/execution`.
- [ ] PE-02 Unknown/unauthorized project is non-disclosing 404.
- [ ] PE-03 Projection is exact-project scoped and server-side aggregated.
- [ ] PE-04 Return generated_at, exact build SHA and COMPLETE/PARTIAL status.
- [ ] PE-05 Return exact project identity/context needed by the M04 project header without duplicating global truth.
- [ ] PE-06 Return orchestration history in authoritative persisted order.
- [ ] PE-07 For each orchestration return ID/status/generation/research outcome/pivot count/current phase/start/update/terminal checkpoint.
- [ ] PE-08 Return full phase execution history per orchestration with exact generation/index/status/run/workunit/failure/checkpoint identities.
- [ ] PE-09 Phase labels/order come from persisted Domain execution state; no generic hard-coded research phase flow.
- [ ] PE-10 Successful zero-orchestration state is distinct from unavailable/partial.

### B. Selected phase detail

- [ ] PE-11 Add cookie-authenticated exact-project phase detail endpoint.
- [ ] PE-12 Phase detail rejects phase IDs outside the requested/authorized project with non-disclosing 404.
- [ ] PE-13 Return exact phase execution identity/status/generation/timestamps/outcome.
- [ ] PE-14 Return exact WorkUnit ID/type/status/version.
- [ ] PE-15 Return WorkUnit input revision IDs, output contracts and preconditions.
- [ ] PE-16 Return required gates/authorities and executor selector.
- [ ] PE-17 Return execution/retry/recovery policies and resource conflict keys.
- [ ] PE-18 Return Run ID/attempt/executor/runtime status/start/finish/correlation/checkpoint.
- [ ] PE-19 Return Run input revision IDs, produced revision IDs, evidence IDs and exit metadata.
- [ ] PE-20 Return Gate ID/type/policy/scope/required inputs/evidence/result/violation codes/evaluated refs.
- [ ] PE-21 Gate result is preserved exactly as persisted; PASS/FAIL/BLOCKED is not inferred.
- [ ] PE-22 Return related Decisions with exact decision type/source gates/source failure/target/reason/actor/time.
- [ ] PE-23 Decision type is never normalized beyond persisted CONTINUE|RETRY|REVISE_CURRENT|REVISE_UPSTREAM|REPLAN|ESCALATE|ABORT|WAIT.
- [ ] PE-24 Return related FailureRecord identity/class/stage/ref/revision/failed gate/evidence/severity/signature/root/resume/status.
- [ ] PE-25 Return related RecoveryPlan identities/status/resume target and exact invalidation/required-action sets.
- [ ] PE-26 Return relevant LoopGuard state without inventing retry budget semantics.
- [ ] PE-27 Return Checkpoint full persisted state: active/completed workunits, stages, valid/dirty/stale revisions, blocking failures, pending decisions/approvals, resume candidates and runtime metadata.
- [ ] PE-28 Return persisted ImpactSet/PIVOT-linked state when attributable to this phase/failure; do not infer document impact.
- [ ] PE-29 Return exact input/output/evidence identities only; Project Library owns rich artifact/evidence exploration.

### C. Agent Protocol / handoff read state

- [ ] PE-30 When protocol exists, return exact protocol ID/skill revision/hash/recovery mode/stage/status/retry budget/count.
- [ ] PE-31 Return project protocol defaults/effective recovery context as persisted/derived by AgentExecutionProtocolService.
- [ ] PE-32 Return preflight executions and checks.
- [ ] PE-33 Return frozen plan revisions, objective, steps/hash/reason/actor/time.
- [ ] PE-34 Return plan checklist item status/note.
- [ ] PE-35 Return problem records and recovery proposal/decision state read-only.
- [ ] PE-36 Return prior handoff link identity/hash and handoff record.
- [ ] PE-37 Return produced handoff identity/hash/actor/time and stored operational payload/Markdown only when part of the persisted protocol record.
- [ ] PE-38 Return protocol event timeline with stage/event/actor/message/time.
- [ ] PE-39 No UI/API field is labeled or presented as hidden chain-of-thought.

### D. Live events

- [ ] PE-40 Add browser-cookie authorized phase event list/stream contracts or an equivalent same-origin bridge.
- [ ] PE-41 SSE preserves exact event IDs.
- [ ] PE-42 SSE supports Last-Event-ID resume semantics.
- [ ] PE-43 SSE phase must belong to the exact authorized project route.
- [ ] PE-44 Browser stream failure shows Live stream unavailable and falls back to authoritative GET events.
- [ ] PE-45 Reload reconstructs all execution state from backend; no localStorage execution authority.

### E. Execution UI / project workspace integration

- [ ] PE-46 Promote project-local Execution nav from Locked to Live.
- [ ] PE-47 Keep M04 project header/context intact.
- [ ] PE-48 Show orchestration selector/history and phase timeline.
- [ ] PE-49 Selecting a phase updates exact phase inspector without changing project route.
- [ ] PE-50 Show WorkUnit/Run/Gates/Decisions/Failure-Recovery/Checkpoint as distinct semantic sections.
- [ ] PE-51 Show Agent Protocol stage/progress/plan/problem/handoff/event state when present.
- [ ] PE-52 Show live-event status separately from persisted execution status.
- [ ] PE-53 No recovery/approve/apply/protocol mutation control is exposed in M05-A.
- [ ] PE-54 Project Back/Forward, global sidebar, theme, session and route switching do not regress.

### F. QA

- [ ] PE-55 Tests prove hidden-project orchestration/phase/event state is absent/non-disclosing.
- [ ] PE-56 Tests cover empty project, populated phase, failed/recovery/checkpoint state and protocol-present/protocol-absent cases.
- [ ] PE-57 Tests lock cross-project phase-ID rejection.
- [ ] PE-58 Tests lock exact decision/gate/failure/checkpoint enums and identities without normalization.
- [ ] PE-59 Tests lock SSE event ID + Last-Event-ID semantics under browser session auth.
- [ ] PE-60 Tests prove browser execution projection omits reusable secrets and worker lease tokens.
- [ ] PE-61 Existing Bearer `/product/*` process/phase/event APIs remain valid.
- [ ] PE-62 No schema, role, authority, scientific/evidence or runtime-protocol semantic change.
- [ ] PE-63 Findings are recorded/fixed/rechecked until implementation `FAIL=0 OPEN=0 COUNT=0`.

## Initial count

```text
TOTAL = 63
PASS  = 0
FAIL  = 0
OPEN  = 63
COUNT = 63
```
