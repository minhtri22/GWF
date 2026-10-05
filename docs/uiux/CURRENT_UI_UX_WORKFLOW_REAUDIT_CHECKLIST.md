# Current Browser UI/UX Workflow Re-audit — Master Checklist

## Identity

```text
AUDIT_ID          = BPS_CURRENT_UI_UX_WORKFLOW_REAUDIT_V1
BRANCH            = feature/bps-i00-product-shell
SCOPE             = I00 + currently LIVE BPS-M01..M07-A
PROTOCOL          = BPS-QA-FIRST-DEFERRED-UAT-v1
STATUS            = OPEN / REAUDIT_IN_PROGRESS
FINAL_USER_UAT    = DEFERRED
```

## Governing source set

This re-audit rereads and reconciles the current process/UX contracts, including:

- `BPS_I00_IMPLEMENTATION_AUTHORIZATION.md`
- `BPS_I00_PRE_LOCAL_QA.md`
- `BPS_I00_UI_REIMPLEMENTATION_CONTRACT.md`
- `BPS_MODULE_EXECUTION_MODEL.md`
- `BPS_QA_FIRST_DEFERRED_UAT.md`
- `BPS_SCREEN_FAST_LANE.md`
- `BROWSER_PRODUCT_SURFACE_SPEC.md`
- `DOCUMENT_QA_INCREMENTAL_UI_EXECUTION_PLAN.md`
- `DOCUMENT_QA_UI_LOCAL_UAT_HANDOFF_PROTOCOL.md`
- `DOCUMENT_QA_UI_UX_PRODUCT_ARCHITECTURE.md`
- `UI_UX_PRODUCT_ARCHITECTURE_SPEC.md`
- `UI_UX_QA.md`
- `UI_UX_VISUAL_BASELINE_QA.md`
- `IMPLEMENTATION_7_WAVES_PLAN.md`
- all current `docs/uiux/screens/*` and `docs/uiux/workflows/*` checklists.

Source precedence follows UI/UX spec §34A.1.

## Explicit non-scope / deferred boundaries

The following are not opened by this re-audit:

- M07-B GitHub connection/binding/ChangeSet mutations, pending explicit user confirmation after the current surface;
- M08 Project Library;
- M09 Documents;
- M10 Document Relations;
- GAC / Reference Acquisition / Agent Interoperability future-gated browser surfaces;
- `RESEARCH_GOVERNANCE_MODES_V1`, which remains DEFERRED / NOT_OPENED.

A deferred item is not counted as PASS. It is outside the current authorized COUNT.

## A. Process and maturity integrity

- [ ] WQA-01 Current capability matrix matches actual LIVE/SKELETON/PLANNED behavior.
- [ ] WQA-02 No LIVE route depends on fixture/localStorage/demo state as product authority.
- [ ] WQA-03 Every LIVE browser mutation delegates to the native service/authority path.
- [ ] WQA-04 Existing per-screen checklist claims are rechecked against current code rather than trusted historically.
- [ ] WQA-05 Stale governance/checklist documents are reconciled when implementation has advanced beyond them.
- [ ] WQA-06 Future/locked modules remain truthful and do not simulate success.

## B. Global shell, auth and navigation

- [ ] WQA-07 Login uses canonical browser session auth and no bearer token is exposed to JavaScript.
- [ ] WQA-08 Logout revokes the authoritative session and returns to login.
- [ ] WQA-09 Session expiry/401 returns to login without stale authenticated UI.
- [ ] WQA-10 Refresh/deep-link/Back/Forward restore authoritative route state.
- [ ] WQA-11 Sidebar collapse reclaims workspace width and uses semantic icons/tooltips.
- [ ] WQA-12 Light/Dark/System remain presentation-only and preserve information hierarchy.
- [ ] WQA-13 Topbar shows truthful tenant/workspace scope context without inventing a selected scope.
- [ ] WQA-14 Topbar shows current runtime/environment identity.
- [ ] WQA-15 Command/navigation palette is operational and bounded to navigation/page filtering; it does not invent cross-project GAC search.
- [ ] WQA-16 Command palette/search copy does not promise Documents/Artifacts global search before GAC.
- [ ] WQA-17 Attention bell uses the same authoritative Home attention count and opens Attention Required.
- [ ] WQA-18 Actor menu exposes current authoritative session identity and is keyboard dismissible.
- [ ] WQA-19 Exact product version/build remains accessible.
- [ ] WQA-20 Keyboard focus/navigation has visible, usable controls for global actions.

## C. Home workflows

- [ ] WQA-21 Home KPI/Executing/Live Runs/Attention/Recent Activity remain source-correct under §34A.2/§34A.3.
- [ ] WQA-22 Home distinguishes loading/complete-empty/partial/error states.
- [ ] WQA-23 Home active project rows can open the now-LIVE exact Project Overview.
- [ ] WQA-24 Home live run rows can enter the now-LIVE project Execution context without fabricating a run result.
- [ ] WQA-25 Home attention entries route to an available governed inspection/action surface when one is currently LIVE.
- [ ] WQA-26 Home refresh preserves a fresh authenticated session and reconstructs from backend.

## D. Projects + lifecycle + Access

- [ ] WQA-27 Projects filters/search are operational transient page state.
- [ ] WQA-28 Project rows open exact Project Overview; refresh/deep-link preserves project identity.
- [ ] WQA-29 Create Project implements tenant/workspace -> name -> optional exact PUBLISHED Domain revision -> review -> create -> Project Overview.
- [ ] WQA-30 Create options include only actor-manageable ACTIVE workspaces and same-tenant PUBLISHED Domain revisions.
- [ ] WQA-31 Create failure is atomic; no partial project/scope/member/domain state survives.
- [ ] WQA-32 Project Create governance document reflects the implemented/qualified state rather than stale PRELOCK text.
- [ ] WQA-33 Rename is available only with native project-management authority and preserves name history/audit.
- [ ] WQA-34 Archive shows exact consequences, active-execution/drain behavior and authoritative result.
- [ ] WQA-35 Restore is available only for eligible archived/archiving project state and uses native governance semantics.
- [ ] WQA-36 Lifecycle actions refresh Projects/Home/Project Overview from backend; no optimistic browser truth.
- [ ] WQA-37 Current immutable Domain binding is visible; no silent upgrade/rebind action exists.
- [ ] WQA-38 Access tenant/workspace creation uses native authority and authoritative post-mutation refresh.
- [ ] WQA-39 Access member add/revoke uses exact Actor ID and permission-scoped controls.
- [ ] WQA-40 Hidden tenant/workspace/project/member existence remains non-disclosing.
- [ ] WQA-41 Project lifecycle/create mutations use governed confirmation with exact target/scope/consequence.

## E. Operations workflows

- [ ] WQA-42 Runs projection/filtering remains authorized, exact and error/empty distinct.
- [ ] WQA-43 Runs can open the now-LIVE owning Project Execution/Overview context.
- [ ] WQA-44 Approval inspection shows frozen payload/hash/policy and exact project/resource identity.
- [ ] WQA-45 Approve exact hash / Reject with reason use native authority, governed confirmation and backend refresh.
- [ ] WQA-46 Approval action never implies the governed resource was automatically applied.
- [ ] WQA-47 Audit preserves exact append-only actor/action/resource/reason/linked identities with no mutation.
- [ ] WQA-48 Runtime exposes authorized jobs/attempts/referenced workers without raw lease token or worker mutation.
- [ ] WQA-49 Operations route/subroute reload, Back/Forward and zero/partial/error states remain correct.

## F. Project Overview / Execution / Recovery

- [ ] WQA-50 Project header/context always preserves exact project/scope/lifecycle/Domain/activity breadcrumb.
- [ ] WQA-51 Overview current actor/orchestration/phase/run/approval/failure/handoff/GitHub/frontier/runtime summaries remain authoritative.
- [ ] WQA-52 Execution orchestration/phase selection exposes the complete v0.2→v0.8.3 state without conflating semantics.
- [ ] WQA-53 Execution live SSE preserves event IDs/reconnect and falls back to persisted events without changing execution truth.
- [ ] WQA-54 Derived final report is clearly DERIVED_VIEW and domain-generic.
- [ ] WQA-55 Recovery decision controls appear only for WAITING_HUMAN + HUMAN + APPROVE.
- [ ] WQA-56 Recovery Approve/Reject requires exact confirmation, prevents duplicate submission and reconstructs backend state.
- [ ] WQA-57 Apply/retry/verify/handoff/complete protocol mechanics remain absent from browser unless separately authorized.
- [ ] WQA-58 Project-local locked Library/Governance/Configuration routes remain truthful and non-simulated.

## G. Packages workflows

- [ ] WQA-59 Domains/Skills/Usage tabs are reload-safe and distinguish zero/partial/error.
- [ ] WQA-60 Domain package revisions preserve exact lifecycle and latest vs latest-PUBLISHED distinction.
- [ ] WQA-61 Skill visibility remains AUTHORIZED_REACHABLE with CONFIGURED/OBSERVED basis and no fake tenant ownership/status.
- [ ] WQA-62 Package→Projects usage preserves exact authorized revision usage and CONFIGURED/OBSERVED bases.
- [ ] WQA-63 Project→Packages backend projection remains exact and non-disclosing; no silent Domain upgrade exists.
- [ ] WQA-64 Package UI exposes no create/publish/validate/install/upgrade mutation in the current read-first unit.

## H. System GitHub read surface

- [ ] WQA-65 GitHub global read is authorized by visible project and exposes no reusable credential/adapter object.
- [ ] WQA-66 Connection/binding/readiness states distinguish disabled/unattached/capability/identity/provider failures.
- [ ] WQA-67 ChangeSet PREPARED/PREFLIGHT_PASS/COMMITTED/VERIFIED/STALE/VERIFICATION_FAILED remain distinct.
- [ ] WQA-68 qa_complete is true only for VERIFIED.
- [ ] WQA-69 Readiness is explicit/on-demand and current M07-A exposes no mutation controls.

## I. Diagnostics

- [ ] WQA-70 Diagnostics shows exact product/build/runtime/backend and core readiness.
- [ ] WQA-71 Diagnostics distinguishes DB/migrations, CAS/object-store, observability and GitHub adapter state where currently qualified.
- [ ] WQA-72 Capability maturity matrix matches bootstrap capability state.
- [ ] WQA-73 Diagnostic failures are distinct from healthy/zero and expose no secrets.
- [ ] WQA-74 Diagnostics remains usable after session refresh and theme/sidebar changes.

## J. Cross-screen integration

- [ ] WQA-75 Home -> Project Overview works with exact identity.
- [ ] WQA-76 Home/Operations Run -> Project Execution works with exact owning project context.
- [ ] WQA-77 Attention -> Approval or Recovery inspection works where destination is LIVE.
- [ ] WQA-78 Project -> Execution -> back to Project/Projects preserves context.
- [ ] WQA-79 Package usage -> project identity is inspectable without inventing locked Project Configuration functionality.
- [ ] WQA-80 GitHub project selection -> binding/readiness/change-set context remains exact.
- [ ] WQA-81 Global nav switching clears stale prior-screen content and active navigation remains correct.
- [ ] WQA-82 Browser refresh reconstructs all product state from server/session plus presentation-only theme/sidebar preference.

## K. Regression and evidence

- [ ] WQA-83 HTML IDs/selectors/routes have no static wiring defects.
- [ ] WQA-84 JavaScript parses cleanly and no LIVE workflow references missing DOM targets.
- [ ] WQA-85 Targeted BPS tests cover all repaired workflows and negative/non-disclosure paths.
- [ ] WQA-86 Shared-component fixes recheck affected earlier screen contracts.
- [ ] WQA-87 Exact-head automated BPS QA is executed; queued/not-started is not counted as PASS.
- [ ] WQA-88 Findings ledger is closed with FAIL=0 / OPEN=0 / COUNT=0.

## Initial count

```text
TOTAL = 88
PASS  = 0
FAIL  = 0
OPEN  = 88
COUNT = 88
```
