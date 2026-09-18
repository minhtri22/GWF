# Research Orchestrator v0.2 Contract

## Purpose

Execute the research Domain Package as a persistent, resumable workflow while preserving the kernel separation between knowledge, execution, decision, and governance.

## Mapping to kernels

| Research Orchestrator concept | Kernel owner | Runtime primitive |
|---|---|---|
| Research artifacts and revisions | Knowledge Kernel | Artifact / Revision |
| Artifact dependency and invalidation | Knowledge Kernel | TraceLink / Validity / ImpactSet |
| Phase | Execution Kernel | WorkUnit |
| Phase attempt | Execution Kernel | ExecutionRun |
| Structured proof | Execution Kernel | Evidence |
| Durable pause/resume | Execution Kernel | Checkpoint |
| Completion predicate | Decision Kernel | Gate |
| PASS / FAIL / PIVOT | Research domain + Decision Kernel | DecisionRecord artifact + Decision |
| Operational failure | Decision Kernel | FailureRecord |
| Upstream repair plan | Decision Kernel | RecoveryPlan |
| Retry/pivot cycle cap | Decision Kernel | LoopGuard |
| Research role | Governance Kernel | Actor / Authority |
| Normative change | Governance Kernel | Proposal / Approval |
| Full trail | Governance Kernel | AuditEvent |

## Invariant: scientific FAIL != operational failure

`decision_record.outcome=FAIL` means the current hypothesis revision did not satisfy its precommitted criteria. It remains a valid research result and continues through replication/replay, final report, and handoff.

An operational failure is represented by `FailureRecord` and may cause RETRY, REVISE_CURRENT, REVISE_UPSTREAM, REPLAN, WAIT, ESCALATE, or ABORT.

## Phase execution semantics

For each phase:

1. Resolve current input revisions by artifact type.
2. Require all semantic inputs to be `VALID`.
3. Checkpoint before phases marked `checkpoint_policy.before`.
4. Create WorkUnit and ExecutionRun.
5. Invoke a `ResearchPhaseExecutor`.
6. Persist output revisions and evidence.
7. For normative output: checkpoint → frozen proposal → human approval → exact commit → checkpoint.
8. Complete the runtime run but place the WorkUnit in `VERIFYING`.
9. Evaluate the phase completion gate(s) using structured evidence.
10. Only on `PASS`, promote output revisions to `VALID` and finalize WorkUnit `SUCCEEDED`.
11. Checkpoint after phase success.

`required_gate_types` in the research package are **postcondition/completion gates** in v0.2.

## PASS branch

`phase_12 -> PASS -> skip phase_13 -> phase_14 -> phase_15 -> phase_16 -> terminal checkpoint`.

## FAIL branch

`phase_12 -> FAIL -> skip phase_13 -> phase_14 -> phase_15 -> phase_16 -> terminal checkpoint`.

No `FailureRecord` is created solely because the scientific outcome is FAIL.

## PIVOT branch

`phase_12 -> PIVOT -> phase_13 -> checkpoint -> identify earliest_resume_artifact -> mark target DIRTY -> invalidate affected downstream subgraph -> increment lineage generation -> resume producer phase -> rerun only downstream path -> new phase_12 decision`.

The pivot count is bounded by `loop_policy.decision_cycle_limit`.

## Operational recovery branch

`run/gate failure -> FailureRecord -> Decision -> root confirmation -> ImpactSet -> RecoveryPlan -> apply invalidation -> checkpoint -> resume root producer phase -> regenerate affected subgraph -> resolve FailureRecord after repaired root phase passes`.

Retryable failures keep the same WorkUnit and increment ExecutionRun attempt number.

## Checkpoint contract

Research checkpoint metadata contains at least:

- orchestrator state and next phase,
- generation/outcome/pivot count,
- current artifact revision hashes,
- environment fingerprint when available,
- standard kernel snapshot: valid/dirty/stale revisions, active/completed WorkUnits, blocking failures, pending decisions/approvals, resume candidates.

Resume reconciles the checkpoint with current database truth. The chat transcript is never an authority source.

## Human approval boundary

The orchestrator accepts an `approval_provider` callback for trusted integration. If no external provider is supplied, local test/demo runs may use a configured HUMAN actor. Production deployment must bind approval to authenticated human identity outside model-controlled payloads.

## Report contract

The `final_report` artifact must satisfy both its artifact required fields and the top-level `reporting` requirements, including negative results, failed runs, pivot history, protocol deviations, open questions, claims/evidence matrix, reproduction commands, environment manifest, and exact revision IDs.

## Current v0.2 boundary

The orchestrator is executable and tested, but real research actions are adapter-driven. The included `DeterministicResearchExecutor` is a test harness, not a scientific agent or experiment engine.
