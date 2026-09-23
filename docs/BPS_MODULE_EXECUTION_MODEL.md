# GWF Browser Product Surface — Module Isolation and Final Wiring Model

## 1. Status

```text
MODEL_ID                  = BPS-MODULE-ISOLATION-v1
APPROVAL                  = USER_APPROVED
APPROVAL_DATE             = 2026-09-23
CURRENT_FOUNDATION        = BPS-I00
MODULE_SEQUENCE           = BPS-M01..BPS-M10
FINAL_WIRING_ROUND        = BPS-W0
ONE_MODULE_OPEN_AT_A_TIME = YES
```

After BPS-I00, the browser program executes one isolated product module at a time. Each module receives its own QA/UAT/freeze boundary. Cross-module wiring is deferred to BPS-W0.

## 2. Route availability is not module functionality

BPS-I00 owns a real navigable SPA/global route skeleton. A route may exist and be navigable while its owning module is still locked.

Presentation maturity states:

```text
SKELETON_LOCKED
PLANNED_BLOCKED
LIVE_FOUNDATION
LIVE_MODULE
```

- `SKELETON_LOCKED`: navigable route; truthful locked surface; no module data/actions.
- `PLANNED_BLOCKED`: navigable orientation route; dependency not yet authorized.
- `LIVE_FOUNDATION`: BPS-I00 real foundation route/data.
- `LIVE_MODULE`: module reached MODULE_FINAL_PASS.

Locked navigation is not disabled navigation. URL, selected nav, reload, Back/Forward and deep-link entry must work while module functionality remains absent.

## 3. BPS-I00 route-skeleton contract

Minimum top-level routes:

```text
/app/home
/app/projects
/app/operations
/app/research/packages
/app/system/diagnostics
/app/system/settings

/app/shared-library                  [PLANNED_BLOCKED]
/app/research/reference-acquisition [PLANNED_BLOCKED]
/app/agents                          [PLANNED_BLOCKED]
```

Required:

- clickable top-level navigation;
- History API navigation;
- Back/Forward restoration;
- direct reload/deep link under recognized `/app/*`;
- route-specific title, maturity and owning module;
- no fake counts, projects, runs, documents, actions or mutations;
- `/app/system/diagnostics` is LIVE_FOUNDATION with authoritative runtime/build/backend/health/session identity.

## 4. Module sequence

### BPS-M01 — Home
Home KPIs, Executing Projects, Live Runs, Attention, Recent Activity, Core Health.

### BPS-M02 — Projects + Access
Projects index/create/lifecycle plus tenant/workspace/member/session access.

### BPS-M03 — Operations
Global Runs, Approvals, Audit and Distributed Runtime read surface.

### BPS-M04 — Project Workspace / Overview
Project context/header, Overview and project-local navigation foundation.

### BPS-M05 — Execution + Recovery
Orchestration, phases, WorkUnits, Runs, Gates, Decisions, Failures, PIVOT, Recovery, Checkpoint, SSE and Agent Protocol.

### BPS-M06 — Research / Packages
Domain/Skill Registry, revisions, usage and Project↔Packages.

### BPS-M07 — System / GitHub
Repository binding, plugin capabilities, ChangeSet state and GitHub surfaces.

### BPS-M08 — Project Library
Artifacts, Revisions, Evidence, checkpoints and Artifact Trace/Impact reads.

### BPS-M09 — Documents
Already-qualified DG-P0→P10 HTTP exposure plus Documents list/detail/revisions/QA/findings/lifecycle/validity/authority, Quick Preview and Full-screen Reader.

Internal stages may be M09-A API and M09-B browser, but there is one QA1→QA6 + local UAT + MODULE_FINAL_PASS. No intermediate stage unlocks M10.

### BPS-M10 — Document Relations
Relations/Lineage graph, exact binding, node/edge inspector, root navigation and accessible relation table. Document Impact stays blocked until later backend authorization.

## 5. Per-module state machine

```text
LOCKED
 -> explicit authorization
SPEC_FROZEN
 -> IMPLEMENTED
 -> QA1→QA6 PASS
 -> PRE_LOCAL_PASS
 -> LOCAL_UAT PASS
 -> MODULE_FINAL_PASS
 -> FROZEN_FOR_INTEGRATION
```

Only one module implementation is OPEN at a time. A frozen module is not modified by later modules unless impacted-module IDs and regression scope are recorded before mutation.

## 6. BPS-W0 — integration-only round

Starts only after BPS-I00 and BPS-M01..BPS-M10 have their required final pass/freeze state.

W0 does not finish missing module features. It verifies:

- route handoff/deep links/breadcrumbs;
- context propagation and return context;
- Back/Forward;
- exact IDs and authorization across module boundaries;
- cross-module state consistency;
- end-to-end operator journeys.

Minimum journeys:

```text
Home -> Project
Project -> Execution
Execution -> Evidence
Project -> Documents
Document -> Relations
Package -> Project
Operations -> Run -> Project
Approval -> governed resource
```

## 7. UAT isolation rule

Each module UAT tests that module plus foundation invariants. M09 Documents does not require Relations. M10 focuses on graph/binding/inspector using frozen M09. BPS-W0 is the only mandatory full cross-module UAT round.

## 8. Naming migration

Historical BPS-Ixx evidence is not rewritten. Future execution mapping:

```text
I01 -> M01
I02 -> M02
I03 -> M03
I04 -> M04
I05 -> M05
I06 -> M06
I07 -> M07
I08 -> M08
I09 + I10 -> M09
I11 -> M10
```

BPS-I00 keeps its name because it is the shared shell/routing foundation.

## 9. Amendment — screen-level Fast Lane

The user-approved execution unit for ordinary browser development is now the **screen**, not the whole module.

`docs/BPS_SCREEN_FAST_LANE.md` governs execution:

```text
READ DOCS
 -> CHECKLIST
 -> IMPLEMENT
 -> SELF-QA
 -> COUNT=0
 -> USER P/F UAT
 -> SCREEN_PASS
 -> NEXT SCREEN
```

BPS-M01…M10 remain architectural ownership groupings. `MODULE_FINAL_PASS` is no longer required between ordinary screens.

A module/screen returns to strict governance only when it crosses backend/schema/authority/security/scientific-evidence/API-contract/destructive-mutation boundaries.

BPS-W0 remains useful as a later cross-screen integration check, but it must not slow ordinary sequential screen delivery.
