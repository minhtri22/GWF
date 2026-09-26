# Project Workspace / Overview — BPS-M04 Checklist

## Identity

```text
SCREEN_ID        = PROJECT_OVERVIEW
OWNER            = BPS-M04
ROUTE            = /app/projects/:projectId/overview
PROTOCOL         = BPS-QA-FIRST-DEFERRED-UAT-v1
STATUS           = CHECKLIST_FROZEN / IMPLEMENTATION_PENDING
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

- [ ] PO-01 Add cookie-authenticated `GET /browser/projects/{project_id}/overview`.
- [ ] PO-02 Unauthorized or unknown project returns non-disclosing not-found behavior.
- [ ] PO-03 Projection is scoped to one exact authoritative project ID.
- [ ] PO-04 Return `generated_at`, exact build SHA and complete/partial query status.
- [ ] PO-05 Return project name/ID, lifecycle and tenant/workspace exact IDs/names.
- [ ] PO-06 Return pinned Domain package/revision/semantic version/payload hash/status/bound actor/time when present.
- [ ] PO-07 Project lifecycle and execution activity are separate and use §34A.2 exact semantics.
- [ ] PO-08 Return latest orchestration identity/status/generation/outcome/pivot count.
- [ ] PO-09 Return latest/current phase execution identity/domain phase label/status.
- [ ] PO-10 Return active RUNNING run identity/workunit/start/executor when present.
- [ ] PO-11 Current actor/executor follows §34A.2: latest authoritative current phase/protocol event, otherwise active run executor, otherwise `SYSTEM`/em dash.
- [ ] PO-12 Return pending approval count and exact pending proposal identities/actions.
- [ ] PO-13 Return unresolved failure count and exact failure/recovery summary.
- [ ] PO-14 Return latest persisted phase handoff identity/hash/actor/time when present.
- [ ] PO-15 Return recent authoritative project audit activity.
- [ ] PO-16 Return GitHub binding summary from persisted project bindings without exposing credentials/secrets.
- [ ] PO-17 Return validity frontier summary from the existing knowledge kernel.
- [ ] PO-18 Return distributed-job summary including persisted status counts and active-job count.
- [ ] PO-19 Document/governance health is not fabricated before BPS-M09; explicit unavailable maturity is allowed.
- [ ] PO-20 Truthful zero/empty state is distinguishable from unavailable/partial/error.

### B. Project workspace routing/header/navigation

- [ ] PO-21 Project rows can open the exact project Overview once Overview is LIVE.
- [ ] PO-22 `/app/projects/{projectId}/overview` deep-links and reloads through the canonical browser shell.
- [ ] PO-23 Project header always shows name, exact project ID, lifecycle, tenant/workspace, pinned Domain identity, execution activity and exact breadcrumb.
- [ ] PO-24 Project local navigation is second-level navigation, not duplicate global sidebar.
- [ ] PO-25 Overview is LIVE and selected.
- [ ] PO-26 Execution/Library/Governance/Configuration project-local routes remain truthful locked routes until their owning units close.
- [ ] PO-27 Browser Back/Forward preserves project route context.
- [ ] PO-28 Back-to-Projects returns to the authoritative Projects index.
- [ ] PO-29 Unknown project-local section does not silently render Overview as another route.
- [ ] PO-30 Global Projects navigation remains active for project-scoped routes.

### C. Overview presentation

- [ ] PO-31 Overview answers “What is happening in this project?” without relation graph or unrelated global data.
- [ ] PO-32 Show lifecycle/activity/current actor/current orchestration-phase/active run as distinct fields.
- [ ] PO-33 Show approvals, failures/recovery, latest handoff and recent activity.
- [ ] PO-34 Show Domain/package, GitHub, validity frontier and distributed-runtime summaries.
- [ ] PO-35 Loading/empty/error/partial states are distinct and no browser-local project truth is persisted.
- [ ] PO-36 Light/Dark/System, sidebar, topbar/session/attention and global route switching do not regress.

### D. QA

- [ ] PO-37 Tests prove inaccessible project Overview is 404/non-disclosing.
- [ ] PO-38 Tests cover empty project and populated operational project.
- [ ] PO-39 Tests lock current-actor precedence: phase event over run executor.
- [ ] PO-40 Tests lock exact Domain binding, latest handoff, GitHub binding, frontier and distributed summary.
- [ ] PO-41 Tests lock dynamic route parsing/deep-link/project-row navigation and locked local subroutes.
- [ ] PO-42 No schema, authority, mutation or scientific/evidence semantics change.
- [ ] PO-43 Findings are recorded/fixed/rechecked until implementation `FAIL=0 OPEN=0 COUNT=0`.

## Initial count

```text
TOTAL = 43
PASS  = 0
FAIL  = 0
OPEN  = 43
COUNT = 43
```
