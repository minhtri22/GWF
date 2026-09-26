# Project Workspace / Overview — BPS-M04 Checklist

## Identity

```text
SCREEN_ID        = PROJECT_OVERVIEW
OWNER            = BPS-M04
ROUTE            = /app/projects/:projectId/overview
PROTOCOL         = BPS-QA-FIRST-DEFERRED-UAT-v1
STATUS           = QA_FINDINGS_CLOSED / CI_PENDING / FINAL_UAT_PENDING
BASE_HEAD        = 83b88e92657b86fa4db554c5b3c664f3db5f303b
FINAL_UAT        = DEFERRED
```

## Governing sources

- `AGENTS.md`
- `docs/BPS_QA_FIRST_DEFERRED_UAT.md`
- `docs/BPS_MODULE_EXECUTION_MODEL.md` — BPS-M04 Project Workspace / Overview.
- `docs/UI_UX_PRODUCT_ARCHITECTURE_SPEC.md` §7, §8, §34A.2.
- `docs/BROWSER_PRODUCT_SURFACE_SPEC.md` §7.
- `src/gwr/product.py` existing authoritative project/process/read models.
- `src/gwr/project_governance.py` lifecycle semantics.
- `src/gwr/tenancy.py` project visibility authority.
- `src/gwr/agent_protocol.py` persisted handoff records.
- `src/gwr/distributed.py` persisted distributed jobs.
- GitHub/plugin persisted project binding state.

## Scope

This unit establishes the project-scoped workspace foundation and the read-only Overview screen.

Project-local navigation is:

```text
Overview       LIVE in BPS-M04
Execution      LOCKED until BPS-M05
Library        LOCKED until BPS-M08/M09
Governance     LOCKED until owning project-governance screens
Configuration  LOCKED until BPS-M06/M07 and project settings/access screens
```

Locked local routes are real/reload-safe orientation routes only. They must not fabricate module data/actions.

## Frozen checklist

### A. Authorized project Overview projection

- [x] PO-01 Add cookie-authenticated `GET /browser/projects/{project_id}/overview`.
- [x] PO-02 Unauthorized or unknown project returns non-disclosing not-found behavior.
- [x] PO-03 Projection is scoped to one exact authoritative project ID.
- [x] PO-04 Return `generated_at`, exact build SHA and complete/partial query status.
- [x] PO-05 Return project name/ID, lifecycle and tenant/workspace exact IDs/names.
- [x] PO-06 Return pinned Domain package/revision/semantic version/payload hash/status/bound actor/time when present.
- [x] PO-07 Project lifecycle and execution activity are separate and use §34A.2 exact semantics.
- [x] PO-08 Return latest orchestration identity/status/generation/outcome/pivot count.
- [x] PO-09 Return latest/current phase execution identity/domain phase label/status.
- [x] PO-10 Return active RUNNING run identity/workunit/start/executor when present.
- [x] PO-11 Current actor/executor follows §34A.2: latest authoritative current phase/protocol event, otherwise active run executor, otherwise `SYSTEM`/em dash.
- [x] PO-12 Return pending approval count and exact pending proposal identities/actions.
- [x] PO-13 Return unresolved failure count and exact failure/recovery summary.
- [x] PO-14 Return latest persisted phase handoff identity/hash/actor/time when present.
- [x] PO-15 Return recent authoritative project audit activity.
- [x] PO-16 Return GitHub binding summary from persisted project bindings without exposing credentials/secrets.
- [x] PO-17 Return validity frontier summary from the existing knowledge kernel.
- [x] PO-18 Return distributed-job summary including persisted status counts and active-job count.
- [x] PO-19 Document/governance health is not fabricated before BPS-M09; explicit unavailable maturity is allowed.
- [x] PO-20 Truthful zero/empty state is distinguishable from unavailable/partial/error.

### B. Project workspace routing/header/navigation

- [x] PO-21 Project rows can open the exact project Overview once Overview is LIVE.
- [x] PO-22 `/app/projects/{projectId}/overview` deep-links and reloads through the canonical browser shell.
- [x] PO-23 Project header always shows name, exact project ID, lifecycle, tenant/workspace, pinned Domain identity, execution activity and exact breadcrumb.
- [x] PO-24 Project local navigation is second-level navigation, not duplicate global sidebar.
- [x] PO-25 Overview is LIVE and selected.
- [x] PO-26 Execution/Library/Governance/Configuration project-local routes remain truthful locked routes until their owning units close.
- [x] PO-27 Browser Back/Forward preserves project route context.
- [x] PO-28 Back-to-Projects returns to the authoritative Projects index.
- [x] PO-29 Unknown project-local section does not silently render Overview as another route.
- [x] PO-30 Global Projects navigation remains active for project-scoped routes.

### C. Overview presentation

- [x] PO-31 Overview answers “What is happening in this project?” without relation graph or unrelated global data.
- [x] PO-32 Show lifecycle/activity/current actor/current orchestration-phase/active run as distinct fields.
- [x] PO-33 Show approvals, failures/recovery, latest handoff and recent activity.
- [x] PO-34 Show Domain/package, GitHub, validity frontier and distributed-runtime summaries.
- [x] PO-35 Loading/empty/error/partial states are distinct and no browser-local project truth is persisted.
- [x] PO-36 Light/Dark/System, sidebar, topbar/session/attention and global route switching do not regress.

### D. QA

- [x] PO-37 Tests prove inaccessible project Overview is 404/non-disclosing.
- [x] PO-38 Tests cover empty project and populated operational project.
- [x] PO-39 Tests lock current-actor precedence: phase event over run executor.
- [x] PO-40 Tests lock exact Domain binding, latest handoff, GitHub binding, frontier and distributed summary.
- [x] PO-41 Tests lock dynamic route parsing/deep-link/project-row navigation and locked local subroutes.
- [x] PO-42 No schema, authority, mutation or scientific/evidence semantics change.
- [x] PO-43 Findings are recorded/fixed/rechecked until implementation `FAIL=0 OPEN=0 COUNT=0`.

## QA findings and adjudication

| Finding | Observation | Correction | State |
| --- | --- | --- | --- |
| PO-F01 | dynamic Project Workspace can receive a late Project A response after navigation to Project B | re-resolve the active route after fetch; discard/reroute before rendering a different project | PASS |
| PO-F02 | malformed project-local paths such as /app/projects/{id} could fall back to the global Projects index | project route parser now keeps malformed/deeper project URLs inside project-local handling and never silently substitutes Overview/index | PASS |
| PO-F03 | an in-flight Overview response could complete after logout/session replacement and repopulate browser cache | bind each Overview request to the requesting actor and discard response when session actor changes | PASS |
| PO-F04 | dangling Domain binding could be reported as ordinary unbound + COMPLETE | preserve the exact bound revision ID and mark projection PARTIAL when bound revision/package cannot resolve | PASS |
| PO-F05 | GitHub repository binding could disappear from summary when its connection row is missing | use left join, preserve the binding, and mark projection PARTIAL instead of fabricating zero bindings | PASS |
| PO-F06 | truthful PARTIAL and unavailable projection paths were implemented but not explicitly locked by targeted regression | added lifecycle-missing PARTIAL, forced outage 500, and dangling-identity PARTIAL tests | PASS |
| PO-F07 | Projects index regression still asserted that no /app/projects/... route could exist | updated the stale M02 assertion to require the now-authorized exact Overview navigation | PASS |

Deterministic assistant QA on implementation HEAD cf2fbab9fe34d4d976bafc6ff36779d6ef3c43e3:

- web/app.js syntax parse: PASS;
- duplicate HTML IDs: 0;
- missing static $(#id) targets: 0;
- Home, Projects index, Access, Operations, locked global routes and Diagnostics all hide projectWorkspaceView when leaving project context;
- dynamic project routes retain global Projects navigation ownership;
- project rows navigate to exact /app/projects/{projectId}/overview;
- Overview/Execution/Library/Governance/Configuration are explicit second-level project routes; only Overview is LIVE in M04;
- unknown/malformed project-local sections do not silently render Overview;
- unauthorized/unknown Overview is non-disclosing 404;
- projection itself rechecks project VIEW authority;
- current actor precedence is locked to phase event over active run executor;
- exact Domain binding, lifecycle/activity separation, pending approvals, unresolved failures/recovery, latest handoff, recent activity, GitHub binding, validity frontier and distributed summary are all source-backed;
- no external_connection_ref, raw lease_token, handoff structured payload/Markdown or browser-local authority is exposed by the Overview projection;
- dangling Domain/GitHub identities become PARTIAL rather than fake unbound/zero;
- Document governance health is explicitly UNAVAILABLE / BPS-M09_PENDING, never inferred;
- zero, PARTIAL, 404 and backend-unavailable states have separate contracts;
- project-switch and session-change asynchronous races are guarded;
- no rename/archive/restore/create mutation was added in M04;
- no schema, role, authority, scientific/evidence or runtime-protocol semantic change was introduced.

Exact-head GitHub Actions are externally capacity-queued and therefore not counted as PASS. Any later CI failure reopens the affected unit before integrated QA/final UAT.

```text
TOTAL_IMPLEMENTATION_ITEMS = 43
IMPLEMENTATION_PASS        = 43
IMPLEMENTATION_FAIL        = 0
IMPLEMENTATION_OPEN        = 0
IMPLEMENTATION_COUNT       = 0

QA_FINDINGS_FAIL           = 0
QA_FINDINGS_OPEN           = 0
QA_FINDINGS_COUNT          = 0

CI_EXECUTION               = PENDING_EXTERNAL_CAPACITY
FINAL_UAT                  = DEFERRED
UNIT_STATE                 = QA_FINDINGS_CLOSED / CI_PENDING / FINAL_UAT_PENDING
```
