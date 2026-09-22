# GWR v0.2 — Handoff

> **Current handoff rule:** for any BPS/UI/UX work, this historical handoff is not sufficient by itself. The receiving agent MUST read root `AGENTS.md` before any modification, then resolve the current plan, UI/UX spec/QA, Browser Product Surface spec, and active slice authorization by exact identity.

## Delivered

v0.2 contains a working Research Orchestrator on top of the governed runtime kernel.

Core additions:

- `src/gwr/research_orchestrator.py`
  - 17-phase driver,
  - postcondition gate enforcement,
  - PASS/FAIL/PIVOT branching,
  - checkpoint/resume,
  - retry,
  - root/impact/recovery routing,
  - pivot lineage generations,
  - report generation,
  - trusted approval callback surface.
- `src/gwr/research_demo.py`
  - deterministic executor for repeatable acceptance tests only.
- `domains/research.workflow.yaml`
  - v0.2 research domain contract.
- new persistence:
  - `orchestrations`,
  - `phase_executions`.
- `tools/run_research_demo.py`, `tools/run_resume_demo.py`, `tools/qa_v02.py`.
- 22 automated tests and complete evidence bundle.

## Verified behaviors

- 17-phase PASS flow: PASS.
- Scientific FAIL path continues to report/handoff: PASS.
- PIVOT creates new lineage generation and resumes affected subgraph: PASS.
- Retryable runtime error resumes same WorkUnit with next attempt: PASS.
- Upstream failure recovery creates ImpactSet + RecoveryPlan and resumes root producer phase: PASS.
- Process-style checkpoint resume: PASS.
- Missing human approval pauses instead of silently committing: PASS.
- External exact-hash approval then resume: PASS.
- Gate predicate cannot pass from free-form/empty assertions: PASS.
- Full regression suite: 22/22 tests PASS.
- Line coverage: 87%.

## Product-readiness statement

This package is a **working reference/alpha runtime**, not production-ready and not a complete autonomous research product.

The orchestration state machine is executable. What remains is primarily integration, security, independent verification, multi-user operations, and real domain execution.

## Open issues / next work

### P0. Real research adapters

Replace `DeterministicResearchExecutor` with adapters that can actually perform each phase:

- literature/web/paper retrieval,
- formalization/model reasoning,
- repository/environment setup,
- dataset construction,
- experiment runner,
- statistics/analysis runner,
- adversarial reviewer,
- report generator.

Each adapter must emit structured artifacts/evidence matching the domain contract rather than prose-only completion claims.

### P0. Independent gate verification

v0.2 requires structured `pass_if` assertions, which is stronger than free-form parsing, but an executor can still assert a predicate itself. Production gates should bind important predicates to independent/verifiable evidence adapters: test runner, dataset validator, statistical checker, provenance checker, citation validator, etc.

### P0. Authenticated human approval

The approval callback is an integration seam, not an authenticated UI. Production requires OIDC/OAuth/session identity and a trusted review surface showing immutable proposal hash/diff before approval.

### P1. Fine-grained experiment sub-runs

`after_each_run` is currently enforced at ExecutionRun granularity. If one phase executor internally batches many scientific runs/seeds, it must expose those sub-runs as first-class runs/events so each seed/run can checkpoint independently.

### P1. Root-cause diagnosis quality

The recovery path supports confirmed roots and affected-subgraph resume, but root candidates currently come from the executor or domain failure taxonomy. Add an independent diagnosis service and evidence-backed root proposal before human confirmation for ambiguous failures.

### P1. Real citation and claim verification

The runtime traces artifacts/evidence but does not verify that cited papers exist, quotes are accurate, claims match source content, or statistical interpretation is scientifically sound.

### P1. PostgreSQL + migrations

SQLite remains the reference persistence. Add repository abstraction, versioned migrations, transaction/isolation tests, backup/restore, and PostgreSQL support.

### P1. Queue/worker model

Add durable task queue, worker leases/heartbeats, distributed concurrency control, cancellation propagation, resource scheduling, and crash recovery across processes/nodes.

### P1. Observability

Add structured logs, metrics, tracing, SLOs, failure dashboards, run cost/token/compute accounting, and operational alerts.

### P2. Domain SDK

Provide typed helpers to author/validate new Domain Packages, WorkUnits, gates, recovery policies, and artifact schemas without hand-editing YAML.

### P2. UI/API/MCP surface

The FastAPI adapter remains read-oriented/minimal. Add authenticated mutation endpoints and/or MCP tools for project creation, proposal review, phase status, failure diagnosis, recovery approval, resume, and report navigation.

### P2. Fault/load/security tests

Add concurrent project stress tests, process kill/restart tests, DB corruption/restore drills, malicious executor evidence tests, authorization escalation tests, and supply-chain/package integrity checks.

## Recommended next milestone

**v0.3 Real Research Alpha** should run one real bounded research question end-to-end with:

1. web/paper retrieval,
2. protocol generation + human approval,
3. a small executable experiment,
4. machine-verifiable metrics,
5. adversarial review,
6. at least one intentionally injected runtime failure and resume,
7. final report whose claims are linked to exact evidence/revisions.

That milestone would move the system from orchestration reference implementation toward a usable internal research product.
