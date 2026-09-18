# GWR v0.8.2 — Project Governance & Observable Agent Execution Protocol

## Objective

v0.8.2 makes project lifecycle and agent execution observable and governable without exposing hidden model chain-of-thought.

The runtime persists operational facts: skill revision, preflight checks, frozen plan, checklist progress, tool/worker events, problems, recovery proposals/decisions, QA, handoff and completion.

## Project governance

Project identity remains immutable. Rename changes only display metadata and appends project_name_history plus audit.

Lifecycle:

ACTIVE -> ARCHIVING -> ARCHIVED -> ACTIVE

Archived and archiving projects are read-only for new proposals, artifacts, revisions, WorkUnits, runs and distributed enqueue. Active work blocks direct archive. drain=true enters ARCHIVING; refresh_archive finalizes ARCHIVED after active orchestration/run/job counts reach zero.

## Agent execution protocol

Every protocol is bound to one PhaseExecution and one immutable SkillRevision.

Stages:

LOAD -> PREFLIGHT -> PLAN -> EXECUTE -> VERIFY -> HANDOFF -> COMPLETE

Hard invariants:

- no preflight PASS -> no plan;
- no plan -> no execution;
- problem must be persisted before retry/replan;
- AUTO recovery is allowed only for LOW-risk, non-normative recovery inside retry budget;
- HUMAN_APPROVE mode pauses before recovery;
- HUMAN actor approval is required for waiting recovery;
- incomplete checklist cannot receive QA PASS;
- no QA PASS -> no handoff;
- no handoff -> no protocol completion.

## Skill contract

Skill packages contain immutable revisions with SKILL.md markdown, content hash, tool requirements and QA contract. The runtime stores the exact skill_revision_id and skill_hash used by each PhaseExecution.

## Recovery modes

AUTO:
- problem is recorded first;
- recovery proposal is persisted;
- only LOW risk, non-normative recovery within retry budget can auto-approve;
- recovery application is separately recorded.

HUMAN_APPROVE:
- problem and recovery proposal are persisted;
- protocol status becomes WAITING_HUMAN;
- no retry/replan can apply until a HUMAN actor with approval authority records APPROVED.

## Observable UI

The Phase Inspector exposes:

- breathing activity indicator for active AI work;
- current protocol stage;
- frozen plan and checklist progress;
- operational event log;
- recorded problems before retry;
- AUTO/HUMAN recovery mode;
- human recovery approval controls;
- retry count and attention state.

This is operational trace, not private reasoning or chain-of-thought.

## Exit gate

The entire v0.8.1 regression chain must remain PASS. Dedicated v0.8.2 tests run on SQLite and PostgreSQL 17. Project governance, AUTO/HUMAN recovery, issue-before-retry, QA/handoff gates, UAT build markers, JavaScript syntax and Python compileall must pass.
