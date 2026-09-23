# Home Screen Checklist — BPS Fast Lane

## Identity

```text
SCREEN_ID        = HOME
OWNER            = BPS-M01
ROUTE            = /app/home
PROTOCOL         = BPS-SCREEN-FAST-LANE-v1
STATUS           = CHECKLIST_FROZEN / IMPLEMENTATION_NOT_STARTED
BASE_HEAD        = 28f82c10de8737ee33e59027f804ea54ce41bf95
```

## Governing sources reread before implementation

- `AGENTS.md` — Fast Lane override active.
- `docs/BPS_SCREEN_FAST_LANE.md` — blob `24ea27e8760b66c949f0c9ab00fe2a1882004bf8`.
- `docs/UI_UX_PRODUCT_ARCHITECTURE_SPEC.md` — blob `ab1c449769fce29d61882d7359ef3e9914b21b71`.
- `docs/BROWSER_PRODUCT_SURFACE_SPEC.md` — current BPS browser contract.
- `docs/UI_UX_QA.md` — blob `3f2a05f1e94a5a1abc82be28fe0bf4849e77c37b`.
- `docs/uiux/approved/UI_VISUAL_BASELINE_MANIFEST.md` — blob `f8feb8356ea5c45b3ea6d2c838c47a5007c56e7d`.
- approved baseline image blob `ce1db70baf3452b3b295d28b14669e3c7dac9f24`.
- current runtime implementation inspected in `src/gwr/product.py`, `src/gwr/api.py`, `src/gwr/tenancy.py`, `src/gwr/project_governance.py`, `src/gwr/execution.py`, `src/gwr/distributed.py`.

## Scope statement

Home answers:

> What is GWF doing right now, and what needs my attention?

This screen is operational/read-only. It must not introduce new mutation semantics, authority rules, project lifecycle semantics, document graphs, future Agent/Codex state, or browser-local authority.

## Frozen implementation checklist

### A. Authoritative Home projection

- [ ] HOME-01 Add one authorized read-only `HomeSummary` projection/API; no frontend direct DB access.
- [ ] HOME-02 HomeSummary owns no authoritative state and performs no mutation.
- [ ] HOME-03 HomeSummary returns `generated_at` and exact build identity.
- [ ] HOME-04 HomeSummary only includes projects visible to the authenticated actor.
- [ ] HOME-05 Avoid browser N+1 fan-out over every project; aggregation occurs server-side.
- [ ] HOME-05A Display Home scope truthfully. Until a tenant/workspace selector exists, identify it as the actor's all-authorized scope rather than inventing a selected tenant/workspace.

### B. Exact KPI semantics

- [ ] HOME-06 Total Projects = authorized projects in current scope.
- [ ] HOME-07 Lifecycle Active = lifecycle exactly `ACTIVE`; never equate lifecycle ACTIVE with execution.
- [ ] HOME-08 Executing Now uses exact activity rule: RUNNING run/orchestration or LEASED/RUNNING distributed job.
- [ ] HOME-09 Running Runs counts only `runtime_status=RUNNING`.
- [ ] HOME-10 Pending Approvals counts visible `PENDING_APPROVAL` proposals.
- [ ] HOME-11 Attention Required counts unresolved authoritative records by stable ID, not project count.
- [ ] HOME-12 Core Health is categorical `HEALTHY|DEGRADED|UNHEALTHY|UNKNOWN`; no invented uptime percentage.

### C. Executing Projects

- [ ] HOME-13 Show project ID + name.
- [ ] HOME-14 Show lifecycle separately from execution activity `EXECUTING|PAUSED|QUEUED|IDLE`.
- [ ] HOME-15 Show exact Domain revision where one is pinned.
- [ ] HOME-16 Show orchestration ID, phase-execution ID and persisted/domain phase label where available.
- [ ] HOME-17 Current actor/executor follows deterministic identity rule; do not label current GWF actor as external “Agent”.
- [ ] HOME-18 Show running run ID, latest authoritative event timestamp and attention count.
- [ ] HOME-19 Do not expose fake project-detail action before the destination screen exists.

### D. Live Runs / Attention / Recent Activity

- [ ] HOME-20 Live Runs shows run ID, project, workunit/phase, status, started, duration, actor/executor and latest event where authoritative data exists.
- [ ] HOME-21 Attention sources are limited to qualified authoritative sources: pending approval, unresolved failure, WAITING_HUMAN recovery, GitHub stale/verification conflict, system/runtime degradation; DG blocked findings only after their browser API is LIVE.
- [ ] HOME-22 Recent Activity is chronological authoritative activity; no fabricated AI summary.
- [ ] HOME-23 External Codex/Claude/etc. must not appear as active sessions before Agent Interoperability is qualified.

### E. UI state and visual contract

- [ ] HOME-24 Home contains no document/knowledge/relation graph.
- [ ] HOME-25 Successful zero-result states are distinct from unavailable/error/unauthorized/partial states.
- [ ] HOME-26 Visual composition follows approved Governed Knowledge Studio baseline: compact KPI row + operational tables/panels, professional research workspace, full shell parity.
- [ ] HOME-27 Light/Dark/System, sidebar reflow and semantic icon behavior from BPS-I00 must not regress.
- [ ] HOME-28 Home remains usable at the mobile-minimum level required by the UX spec.
- [ ] HOME-28A Global attention indicator/count uses the same authoritative HomeSummary attention total; no fake notification feed/action is introduced.

### F. Safety / Fast Lane boundary

- [ ] HOME-29 No new destructive or authoritative mutation endpoint is introduced.
- [ ] HOME-30 No backend/schema/authority/security/scientific-evidence semantics are changed.
- [ ] HOME-31 If implementation requires such a change, stop Fast Lane before mutation and return to strict governance.

## QA rule

Before user UAT:

```text
TOTAL = 33
PASS  = 33
FAIL  = 0
OPEN  = 0
COUNT = 0
```

The assistant must return this checklist with concrete QA evidence before asking the user to UAT Home.

## User UAT rule

User acceptance is a bounded set of observable Home statements answered only with:

```text
P = PASS
F = FAIL
```

Any F keeps Home open. All P marks `HOME = SCREEN_PASS`, then the next screen may begin.
