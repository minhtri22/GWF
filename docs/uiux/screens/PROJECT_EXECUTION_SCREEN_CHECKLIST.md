# Project Execution — BPS-M05-A Checklist

## Identity

```text
SCREEN_ID        = PROJECT_EXECUTION
OWNER            = BPS-M05
ROUTE            = /app/projects/:projectId/execution
PROTOCOL         = BPS-QA-FIRST-DEFERRED-UAT-v1
STATUS           = QA_FINDINGS_CLOSED / CI_PARTIAL_PENDING / FINAL_UAT_PENDING
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

- [x] PE-01 Add cookie-authenticated `GET /browser/projects/{project_id}/execution`.
- [x] PE-02 Unknown/unauthorized project is non-disclosing 404.
- [x] PE-03 Projection is exact-project scoped and server-side aggregated.
- [x] PE-04 Return generated_at, exact build SHA and COMPLETE/PARTIAL status.
- [x] PE-05 Return exact project identity/context needed by the M04 project header without duplicating global truth.
- [x] PE-06 Return orchestration history in authoritative persisted order.
- [x] PE-07 For each orchestration return ID/status/generation/research outcome/pivot count/current phase/start/update/terminal checkpoint.
- [x] PE-08 Return full phase execution history per orchestration with exact generation/index/status/run/workunit/failure/checkpoint identities.
- [x] PE-09 Phase labels/order come from persisted Domain execution state; no generic hard-coded research phase flow.
- [x] PE-10 Successful zero-orchestration state is distinct from unavailable/partial.

### B. Selected phase detail

- [x] PE-11 Add cookie-authenticated exact-project phase detail endpoint.
- [x] PE-12 Phase detail rejects phase IDs outside the requested/authorized project with non-disclosing 404.
- [x] PE-13 Return exact phase execution identity/status/generation/timestamps/outcome.
- [x] PE-14 Return exact WorkUnit ID/type/status/version.
- [x] PE-15 Return WorkUnit input revision IDs, output contracts and preconditions.
- [x] PE-16 Return required gates/authorities and executor selector.
- [x] PE-17 Return execution/retry/recovery policies and resource conflict keys.
- [x] PE-18 Return Run ID/attempt/executor/runtime status/start/finish/correlation/checkpoint.
- [x] PE-19 Return Run input revision IDs, produced revision IDs, evidence IDs and exit metadata.
- [x] PE-20 Return Gate ID/type/policy/scope/required inputs/evidence/result/violation codes/evaluated refs.
- [x] PE-21 Gate result is preserved exactly as persisted; PASS/FAIL/BLOCKED is not inferred.
- [x] PE-22 Return related Decisions with exact decision type/source gates/source failure/target/reason/actor/time.
- [x] PE-23 Decision type is never normalized beyond persisted CONTINUE|RETRY|REVISE_CURRENT|REVISE_UPSTREAM|REPLAN|ESCALATE|ABORT|WAIT.
- [x] PE-24 Return related FailureRecord identity/class/stage/ref/revision/failed gate/evidence/severity/signature/root/resume/status.
- [x] PE-25 Return related RecoveryPlan identities/status/resume target and exact invalidation/required-action sets.
- [x] PE-26 Return relevant LoopGuard state without inventing retry budget semantics.
- [x] PE-27 Return Checkpoint full persisted state: active/completed workunits, stages, valid/dirty/stale revisions, blocking failures, pending decisions/approvals, resume candidates and runtime metadata.
- [x] PE-28 Return persisted ImpactSet/PIVOT-linked state when attributable to this phase/failure; do not infer document impact.
- [x] PE-29 Return exact input/output/evidence identities only; Project Library owns rich artifact/evidence exploration.

### C. Agent Protocol / handoff read state

- [x] PE-30 When protocol exists, return exact protocol ID/skill revision/hash/recovery mode/stage/status/retry budget/count.
- [x] PE-31 Return project protocol defaults/effective recovery context as persisted/derived by AgentExecutionProtocolService.
- [x] PE-32 Return preflight executions and checks.
- [x] PE-33 Return frozen plan revisions, objective, steps/hash/reason/actor/time.
- [x] PE-34 Return plan checklist item status/note.
- [x] PE-35 Return problem records and recovery proposal/decision state read-only.
- [x] PE-36 Return prior handoff link identity/hash and handoff record.
- [x] PE-37 Return produced handoff identity/hash/actor/time and stored operational payload/Markdown only when part of the persisted protocol record.
- [x] PE-38 Return protocol event timeline with stage/event/actor/message/time.
- [x] PE-39 No UI/API field is labeled or presented as hidden chain-of-thought.

### D. Live events

- [x] PE-40 Add browser-cookie authorized phase event list/stream contracts or an equivalent same-origin bridge.
- [x] PE-41 SSE preserves exact event IDs.
- [x] PE-42 SSE supports Last-Event-ID resume semantics.
- [x] PE-43 SSE phase must belong to the exact authorized project route.
- [x] PE-44 Browser stream failure shows Live stream unavailable and falls back to authoritative GET events.
- [x] PE-45 Reload reconstructs all execution state from backend; no localStorage execution authority.

### E. Execution UI / project workspace integration

- [x] PE-46 Promote project-local Execution nav from Locked to Live.
- [x] PE-47 Keep M04 project header/context intact.
- [x] PE-48 Show orchestration selector/history and phase timeline.
- [x] PE-49 Selecting a phase updates exact phase inspector without changing project route.
- [x] PE-50 Show WorkUnit/Run/Gates/Decisions/Failure-Recovery/Checkpoint as distinct semantic sections.
- [x] PE-51 Show Agent Protocol stage/progress/plan/problem/handoff/event state when present.
- [x] PE-52 Show live-event status separately from persisted execution status.
- [x] PE-53 No recovery/approve/apply/protocol mutation control is exposed in M05-A.
- [x] PE-54 Project Back/Forward, global sidebar, theme, session and route switching do not regress.

### F. QA

- [x] PE-55 Tests prove hidden-project orchestration/phase/event state is absent/non-disclosing.
- [x] PE-56 Tests cover empty project, populated phase, failed/recovery/checkpoint state and protocol-present/protocol-absent cases.
- [x] PE-57 Tests lock cross-project phase-ID rejection.
- [x] PE-58 Tests lock exact decision/gate/failure/checkpoint enums and identities without normalization.
- [x] PE-59 Tests lock SSE event ID + Last-Event-ID semantics under browser session auth.
- [x] PE-60 Tests prove browser execution projection omits reusable secrets and worker lease tokens.
- [x] PE-61 Existing Bearer `/product/*` process/phase/event APIs remain valid.
- [x] PE-62 No schema, role, authority, scientific/evidence or runtime-protocol semantic change.
- [x] PE-63 Findings are recorded/fixed/rechecked until implementation `FAIL=0 OPEN=0 COUNT=0`.
- [x] PE-64 Expose the derived final orchestration report for the exact selected project/orchestration; label it derived and never treat Markdown as source of truth.

## QA findings and adjudication

| Finding | Class | Observation | Correction | State |
| --- | --- | --- | --- | --- |
| PE-F01 | product regression | orchestration history projection popped metadata without selecting metadata | select the persisted metadata column, expose only metadata.history, never raw orchestration metadata | PASS |
| PE-F02 | product architecture | browser final report was coupled to ResearchOrchestrator and failed on generic/software domains | replace browser report with domain-generic derived report from persisted orchestration/phase/gate/decision/failure/checkpoint records; keep research Bearer report unchanged | PASS |
| PE-F03 | checklist coverage | Browser Product Surface §10 final-report requirement was omitted from the original 63-item freeze | add PE-64 prospectively as a checklist coverage correction before closure | PASS |
| PE-F04 | route contract | deeper project URLs could silently reuse Overview/Execution or fall back to Projects index | exact project route parser marks extra path segments invalid and keeps them inside project-local handling | PASS |
| PE-F05 | UI context integrity | Project A content could remain visible briefly under Project B URL while B loaded | shared project-workspace loading state now clears Overview/Execution/locked surfaces before fetch | PASS |
| PE-F06 | live transport | browser SSE originally emitted custom event names while frontend only handled EventSource onmessage | browser SSE now uses default message events while preserving exact event IDs and payload event_type | PASS |
| PE-F07 | live transport | frontend closed EventSource on first error, preventing native Last-Event-ID reconnect | allow native reconnect; only fall back to persisted GET events after bounded retry window | PASS |
| PE-F08 | async race | a phase/project selection made while an earlier request was in flight could be skipped by loading guards | after stale request completion, re-resolve active route/selection and fetch the current project/phase | PASS |
| PE-F09 | QA harness | new fixture initially had placeholder-count mismatches for checkpoints/problem/checklist rows | align every INSERT placeholder count with exact schema; full fixture-schema audit PASS | PASS |
| PE-F10 | completeness semantics | dangling WorkUnit/Run/Failure/Checkpoint identities could otherwise look like authoritative empty state | phase projection marks PARTIAL and preserves the persisted identity instead of fabricating zero | PASS |
| PE-F11 | lineage coverage | initial protocol fixture proved produced handoff but not prior-handoff chain | add persisted previous phase + handoff + exact handoff link/hash and assert returned lineage | PASS |
| PE-F12 | domain semantics | orchestration history coercion via list(...) could corrupt non-list domain metadata | preserve the exact history payload shape; render event list only when it is actually a list | PASS |

Deterministic assistant QA on implementation HEAD `ec79a9cfc03ef9dcf11b967d5977bd68df52a9b2`:

- `web/app.js` syntax parse: PASS;
- duplicate HTML IDs: 0;
- missing static `$("#id")` targets: 0;
- actual route-function evaluation: Overview and Execution exact routes resolve correctly; `/execution/extra` resolves as invalid; `/app/projects/{id}` remains project-local invalid rather than global fallback;
- project loading state clears old Overview and Execution content before a new project response;
- project/phase response races and session replacement are guarded;
- Execution route is LIVE while Library/Governance/Configuration remain locked;
- project execution index returns persisted orchestration history without raw metadata;
- selected phase projection preserves WorkUnit/Run/Gate/Decision/Failure/Recovery/LoopGuard/Checkpoint/ImpactSet identities and enums;
- OPERATIONAL_FAILURE ImpactSet attribution requires exact `trigger_id = failure_id`; PIVOT attribution requires exact produced revision identity;
- protocol projection proves skill identity, preflight, frozen plan/checklist, problems/recovery proposals, previous handoff, produced handoff and protocol events;
- no raw worker lease token or external connection secret is exposed;
- no rich Library artifact/evidence payload is passed through as Execution authority;
- no recovery/approve/apply/protocol mutation control exists in M05-A;
- EventSource stream preserves server event IDs, supports native Last-Event-ID reconnect and bounded GET fallback;
- execution state is never sourced from localStorage;
- final browser report is domain-generic, explicitly `DERIVED_VIEW`, preserves exact `domain_id`/phase labels and states that Markdown is not source of truth;
- fixture INSERT arity matches all referenced runtime/protocol schemas;
- targeted tests cover hidden/cross-project access, zero state, populated phase, protocol present/absent, dangling identities, outage vs zero, SSE resume, generic report and existing Bearer process/phase/event compatibility.

Exact-head GitHub Actions at adjudication time:

- PASS: DG-P0 Document Validator Gate;
- PASS: DG-W1 Wave 1 Requalification Gate;
- PASS: DG-P1 Vale Terminology Gate;
- remaining exact-head workflows: queued/in-progress due shared compute capacity;
- these general workflow signals are not treated as targeted M05 runtime-test proof.

Local/container runtime execution was attempted in an isolated worktree but outbound GitHub DNS is unavailable in the execution container. This is an infrastructure limitation, not a product PASS or FAIL.

```text
TOTAL_IMPLEMENTATION_ITEMS = 64
IMPLEMENTATION_PASS        = 64
IMPLEMENTATION_FAIL        = 0
IMPLEMENTATION_OPEN        = 0
IMPLEMENTATION_COUNT       = 0

QA_FINDINGS_FAIL           = 0
QA_FINDINGS_OPEN           = 0
QA_FINDINGS_COUNT          = 0

CI_EXECUTION               = PARTIAL_SUCCESS / REMAINDER_PENDING_EXTERNAL_CAPACITY
TARGETED_RUNTIME_EXECUTION = PENDING_EXTERNAL_EXECUTION
FINAL_UAT                  = DEFERRED
UNIT_STATE                 = QA_FINDINGS_CLOSED / CI_PARTIAL_PENDING / FINAL_UAT_PENDING
```
