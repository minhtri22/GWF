# Home Screen Checklist — BPS Fast Lane

## Identity

```text
SCREEN_ID        = HOME
OWNER            = BPS-M01
ROUTE            = /app/home
PROTOCOL         = BPS-SCREEN-FAST-LANE-v1
STATUS           = USER_UAT_OPEN
BASE_HEAD        = 28f82c10de8737ee33e59027f804ea54ce41bf95
CHECKLIST_HEAD   = f37b20c14f001e83f2b0cb3ef176102c59a02cd0
CANDIDATE_HEAD   = b3bb883085d65fbcfbd655da7d895599b9d65210
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

- [x] HOME-01 Add one authorized read-only `HomeSummary` projection/API; no frontend direct DB access.
- [x] HOME-02 HomeSummary owns no authoritative state and performs no mutation.
- [x] HOME-03 HomeSummary returns `generated_at` and exact build identity.
- [x] HOME-04 HomeSummary only includes projects visible to the authenticated actor.
- [x] HOME-05 Avoid browser N+1 fan-out over every project; aggregation occurs server-side.
- [x] HOME-05A Display Home scope truthfully. Until a tenant/workspace selector exists, identify it as the actor's all-authorized scope rather than inventing a selected tenant/workspace.

### B. Exact KPI semantics

- [x] HOME-06 Total Projects = authorized projects in current scope.
- [x] HOME-07 Lifecycle Active = lifecycle exactly `ACTIVE`; never equate lifecycle ACTIVE with execution.
- [x] HOME-08 Executing Now uses exact activity rule: RUNNING run/orchestration or LEASED/RUNNING distributed job.
- [x] HOME-09 Running Runs counts only `runtime_status=RUNNING`.
- [x] HOME-10 Pending Approvals counts visible `PENDING_APPROVAL` proposals.
- [x] HOME-11 Attention Required counts unresolved authoritative records by stable ID, not project count.
- [x] HOME-12 Core Health is categorical `HEALTHY|DEGRADED|UNHEALTHY|UNKNOWN`; no invented uptime percentage.

### C. Executing Projects

- [x] HOME-13 Show project ID + name.
- [x] HOME-14 Show lifecycle separately from execution activity `EXECUTING|PAUSED|QUEUED|IDLE`.
- [x] HOME-15 Show exact Domain revision where one is pinned.
- [x] HOME-16 Show orchestration ID, phase-execution ID and persisted/domain phase label where available.
- [x] HOME-17 Current actor/executor follows deterministic identity rule; do not label current GWF actor as external “Agent”.
- [x] HOME-18 Show running run ID, latest authoritative event timestamp and attention count.
- [x] HOME-19 Do not expose fake project-detail action before the destination screen exists.

### D. Live Runs / Attention / Recent Activity

- [x] HOME-20 Live Runs shows run ID, project, workunit/phase, status, started, duration, actor/executor and latest event where authoritative data exists.
- [x] HOME-21 Attention sources are limited to qualified authoritative sources: pending approval, unresolved failure, WAITING_HUMAN recovery, GitHub stale/verification conflict, system/runtime degradation; DG blocked findings only after their browser API is LIVE.
- [x] HOME-22 Recent Activity is chronological authoritative activity; no fabricated AI summary.
- [x] HOME-23 External Codex/Claude/etc. must not appear as active sessions before Agent Interoperability is qualified.

### E. UI state and visual contract

- [x] HOME-24 Home contains no document/knowledge/relation graph.
- [x] HOME-25 Successful zero-result states are distinct from unavailable/error/unauthorized/partial states.
- [x] HOME-26 Visual composition follows approved Governed Knowledge Studio baseline: compact KPI row + operational tables/panels, professional research workspace, full shell parity.
- [x] HOME-27 Light/Dark/System, sidebar reflow and semantic icon behavior from BPS-I00 must not regress.
- [x] HOME-28 Home remains usable at the mobile-minimum level required by the UX spec.
- [x] HOME-28A Global attention indicator/count uses the same authoritative HomeSummary attention total; no fake notification feed/action is introduced.

### F. Safety / Fast Lane boundary

- [x] HOME-29 No new destructive or authoritative mutation endpoint is introduced.
- [x] HOME-30 No backend/schema/authority/security/scientific-evidence semantics are changed.
- [x] HOME-31 If implementation requires such a change, stop Fast Lane before mutation and return to strict governance.

## Self-QA adjudication

```text
TOTAL = 33
PASS  = 33
FAIL  = 0
OPEN  = 0
COUNT = 0
```

Evidence:

- exact implementation candidate: `b3bb883085d65fbcfbd655da7d895599b9d65210`;
- source/checklist matrix: 33/33 PASS after correcting two over-broad QA predicates; no product code was changed merely to satisfy those predicates;
- `HOME-19`: Home renderer has no project-detail link/navigation/action;
- `HOME-23`: HomeSummary and Home renderer contain no Codex/Claude active-session source/rendering; the separate Agents/Codex route remains correctly PLANNED_BLOCKED;
- DG-P10 exact-head run `35880739631`: D10 gate PASS, targeted regressions PASS, full regression PASS, compile PASS, PostgreSQL PASS;
- new Home tests verify authenticated read-only HomeSummary, exact KPI semantics, authoritative visibility scope, executing-project identity, attention stable records, recent audit activity and LIVE_MODULE capability;
- no Home mutation endpoint was introduced.

Fast Lane does not wait for duplicate Windows installer qualification; final Windows browser behavior is the next user UAT step.

## User UAT rule

User acceptance is a bounded set of observable Home statements answered only with:

```text
P = PASS
F = FAIL
```

Any F keeps Home open. All P marks `HOME = SCREEN_PASS`, then the next screen may begin.

## User UAT — 2026-09-24

Observed on the current Home product surface. Screenshot footer reports build:

```text
910612aeb1c7508cabec5e42a5d36ff87277d861
```

Adjudication:

```text
H-UAT-01 = P
H-UAT-02 = P
H-UAT-03 = P
H-UAT-04 = UNTESTED_NONEMPTY_STATE
H-UAT-05 = UNTESTED_NONEMPTY_STATE
H-UAT-06 = UNTESTED_NONEMPTY_STATE
H-UAT-07 = UNTESTED_NONEMPTY_STATE
H-UAT-08 = OPEN_INTERMITTENT_SESSION_LOSS_ON_REFRESH
H-UAT-09 = UNTESTED_ERROR_STATE
H-UAT-10 = P
H-UAT-11 = P
```

The currently visible zero-result states were:

- Executing Projects: `No projects are executing in the current authorized scope.`
- Live Runs / Executions: `No RUNNING execution runs.`
- Attention Required: `No authoritative attention items.`
- Recent Activity: `No authoritative activity in this scope yet.`

These observations are not promoted to PASS for the non-empty authoritative-data behaviors because the operator explicitly reported that no dogfood data was available to judge them.

Refresh was reported as intermittent: sometimes preserving login/session and sometimes returning the operator to login. This remains OPEN until localized; a prior UAT phase did not show the loss.

Error/unavailable rendering remains untested by the operator because no controlled error was observed.

```text
USER_UAT_PASS       = 5
USER_UAT_FAIL       = 0
USER_UAT_OPEN       = 1
USER_UAT_UNTESTED   = 5
HOME                = OPEN
NEXT_SCREEN_ALLOWED = false
```


## Remaining UAT fixture — isolated / non-product

A bounded local fixture was added only to make the still-untested Home states observable without mutating the canonical working database or adding fake frontend data.

Implementation lineage:

```text
2c669ac1fc59a7efe12d6481c3c3889708884de4  BPS Home: add isolated UAT data fixture
3cb25b62d9cdbacd8bf76ab227980988ae40e9aa  BPS Home: add Windows UAT fixture launcher
8cbe2037be6bee79db4355fb4060db334e278ac8  BPS Home: test isolated UAT fixture
```

Files:

- `scripts/bps_home_uat_fixture.py`
- `scripts/bps_home_uat_fixture.ps1`
- `tests/test_bps_home_uat_fixture.py`

Safety properties:

- fixture runtime uses a fresh ephemeral temporary directory;
- canonical `.gwr/server/gwr.db` is not used;
- no production API/auth/schema semantics are changed;
- `data` mode seeds backend records that are read through the real authenticated `HomeSummary` projection;
- `error` mode injects a fixture-process-only HTTP 503 for `/browser/home-summary`, leaving auth/bootstrap/shell live so the operator can distinguish unavailable from zero;
- process exits with Ctrl+C and the temporary fixture database is removed.

Operator commands from an isolated BPS worktree:

```powershell
git pull --ff-only origin feature/bps-i00-product-shell

# H-UAT-04/05/06/07 + fresh-session H-UAT-08R
.\scripts\bps_home_uat_fixture.ps1 -Mode data

# after finishing data-mode UAT, Ctrl+C, then:
# H-UAT-09
.\scripts\bps_home_uat_fixture.ps1 -Mode error
```

Fixture credentials:

```text
username = home-uat
password = home-uat-password
URL      = http://127.0.0.1:8877/app/home
```

Only H-UAT-04/05/06/07/08R/09 need to be rerun. Already accepted H-UAT-01/02/03/10/11 are not reopened.
