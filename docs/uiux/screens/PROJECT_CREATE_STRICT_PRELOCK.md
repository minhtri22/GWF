# Project Create Flow — Strict Governance Prelock

## Identity

```text
SCREEN_ID          = PROJECT_CREATE_FLOW
OWNER              = BPS-M02
ENTRY_SURFACE      = Projects index
DESTINATION        = /app/projects/:projectId/overview
PROTOCOL           = STRICT_GOVERNANCE (BPS-SCREEN-FAST-LANE-v1 exit)
STATUS             = IMPLEMENTED / STRICT_CONTRACT_SATISFIED / MASTER_REAUDIT_PASS
BASE_HEAD          = b0d628e3b3d160f4007ba77e215c17f6fae8fac5
PREDECESSOR        = PROJECTS_INDEX = SCREEN_PASS
```

## Why Fast Lane stops here

`docs/BPS_SCREEN_FAST_LANE.md` requires leaving Fast Lane before a screen introduces a new destructive or authoritative mutation or changes an already-qualified API contract.

The browser currently has no cookie-authenticated project-create mutation endpoint. The existing qualified product mutation is:

```text
POST /workspaces/{workspace_id}/projects
Authorization: Bearer ...
```

The browser shell deliberately does not expose/reuse the bearer token in JavaScript. Therefore a live Create Project browser flow cannot be implemented truthfully by wiring the current frontend directly to that endpoint. A browser-authoritative mutation contract is required and must preserve the existing authority rules.

This paragraph records the historical prelock state. Product implementation was subsequently authorized and delivered under the exact frozen semantics below; see the closure addendum at the end of this document.

## Governing sources

- `AGENTS.md` — backend-before-UI, exact authority and strict-mode stop rules.
- `docs/BPS_SCREEN_FAST_LANE.md` — strict trigger for new authoritative mutation/API-contract work.
- `docs/BPS_MODULE_EXECUTION_MODEL.md` — BPS-M02 owns Projects index/create/lifecycle plus tenant/workspace/member/session access.
- `docs/UI_UX_PRODUCT_ARCHITECTURE_SPEC.md` §6.2 — canonical Project creation flow.
- `docs/UI_UX_PRODUCT_ARCHITECTURE_SPEC.md` §7–8 — Project Workspace / Project Overview destination.
- `docs/BROWSER_PRODUCT_SURFACE_SPEC.md` §6–7 — authoritative tenant/workspace/project administration and lifecycle browser obligations.
- `src/gwr/api.py` — existing bearer-auth project-create endpoint and body contract.
- `src/gwr/runtime.py` — `create_scoped_project` orchestration.
- `src/gwr/tenancy.py` — `MANAGE_PROJECT` authority and project-scope binding.
- `src/gwr/domain_registry.py` — PUBLISHED-only, same-tenant, immutable Domain revision pinning.

## Frozen product semantics from the existing specification

Canonical flow:

```text
select tenant/workspace
  -> project name
  -> optional published domain revision
  -> review exact scope
  -> create
  -> Project Overview
```

Required invariants:

1. the selected workspace must be ACTIVE and visible/manageable by the actor;
2. project creation authority remains `MANAGE_PROJECT`;
3. unauthorized workspace identity must not be leaked;
4. optional Domain revision must be PUBLISHED;
5. optional Domain revision must belong to the same tenant as the target workspace/project;
6. Domain binding is immutable after creation under the current backend contract;
7. no “upgrade to latest” or floating Domain behavior may be introduced;
8. created project ownership/scope/member state comes from the existing tenancy service, not browser-local state;
9. success must reconstruct from authoritative backend state;
10. failed creation must not be represented as success.

## Prelock findings that must be resolved before implementation

### PC-PRE-01 — Browser mutation contract is missing

The browser currently authenticates with the HttpOnly `gwr_browser_session` cookie and has read-only browser endpoints for Home and Projects. The existing create endpoint requires a bearer Authorization header.

Therefore implementation requires a **new bounded browser mutation API** or another explicitly qualified bridge. This is a strict-mode API/authority surface and cannot be added under ordinary screen Fast Lane.

### PC-PRE-02 — Selection projections are incomplete

The create form needs authoritative choices for:

- actor-manageable ACTIVE tenant/workspace scope;
- PUBLISHED Domain revisions eligible for the selected tenant.

Current browser APIs do not expose a bounded create-options projection. The browser must not infer these choices from unrelated visible-project rows or from local state.

A read-only create-options projection may be added as part of the strict slice, but it must return only choices the actor is authorized to use.

### PC-PRE-03 — Optional Domain pin needs atomicity adjudication

Current runtime sequence is:

```text
create_scoped_project
  -> create_project()       # commits
  -> tenancy.bind_project() # commits
  -> domains.pin_project()  # validates PUBLISHED / tenant / authority, then commits
```

No outer transaction is visible around that sequence.

Before the browser exposes optional Domain selection, strict QA must prove one of the following:

- failed Domain validation/pinning cannot leave a partially-created project/scope/member record; or
- the runtime/API is corrected transactionally without weakening existing authority semantics.

This is a backend mutation-safety question, not a UI-only defect, and must be resolved before product mutation is exposed.

### PC-PRE-04 — Success destination is not LIVE yet

The governing UI spec requires:

```text
create -> Project Overview
```

Project Overview belongs to BPS-M04 and is not yet LIVE.

The Create Project flow must not silently change the specified success destination or land the user on a fake/locked “successful” project workspace.

Before implementation, governance must choose one defensible path:

A. implement Project Workspace / Overview first, then return to Create Project; or  
B. explicitly amend the UI contract to permit a temporary authoritative post-create destination.

No implicit fallback to Projects index is authorized by this prelock.

## Strict-gate checklist

```text
PC-G01  exact existing mutation semantics mapped
PC-G02  browser-cookie authority boundary specified
PC-G03  manageable tenant/workspace option projection specified
PC-G04  eligible PUBLISHED Domain option projection specified
PC-G05  unauthorized-resource non-disclosure preserved
PC-G06  create atomicity / rollback behavior proven or repaired
PC-G07  duplicate/custom project-id behavior specified
PC-G08  successful authoritative response contract frozen
PC-G09  negative-path contract frozen
PC-G10  audit/security-event evidence expectations frozen
PC-G11  success destination dependency resolved
PC-G12  targeted SQLite/PostgreSQL regression scope frozen
PC-G13  browser UAT mutation verification plan frozen
```

## Current adjudication

```text
PROJECTS_INDEX                 = SCREEN_PASS
PROJECT_CREATE_FLOW            = IMPLEMENTED_UNDER_STRICT_CONTRACT
PRODUCT_MUTATION_IMPLEMENTED   = YES
FAST_LANE                      = NOT_APPLICABLE_TO_THIS_MUTATION
NEXT_LEGAL_ACTION              = CURRENT_UI_UX_MASTER_REAUDIT
```


## Closure addendum — implemented strict contract

The prelock findings were resolved without weakening the original service boundaries.

- PC-G01/P2: browser mutations use the HttpOnly browser-session principal and delegate to the existing tenancy/project-governance services.
- PC-G03/P4: `GET /browser/projects/create-options` returns only actor-manageable ACTIVE workspaces and same-tenant PUBLISHED Domain revisions.
- PC-G05: hidden/unauthorized workspace and project identities remain non-disclosing.
- PC-G06: `GovernedWorkflowRuntime.create_scoped_project` is transactionally qualified; forced late Domain-pin failure leaves no project/scope/member/domain/security-event residue.
- PC-G07: browser Project ID is server-generated; browser does not expose custom project-ID injection.
- PC-G08/P9: success returns exact authoritative project projection and destination; failure does not synthesize success.
- PC-G10: existing security/audit evidence remains service-owned.
- PC-G11: Project Overview is now LIVE and remains the success destination.
- PC-G12: targeted browser-create/lifecycle tests plus affected BPS regression are part of the current master re-audit.
- PC-G13: final browser UAT remains deferred under `BPS-QA-FIRST-DEFERRED-UAT-v1`.

Lifecycle workflow added under the same native authority boundary:

```text
RENAME   -> ProjectGovernanceService.rename()
ARCHIVE  -> ProjectGovernanceService.archive(drain, reason)
RESTORE  -> ProjectGovernanceService.restore()
```

Browser controls are capability-scoped by the same project `MANAGE_MEMBERS` authority used by the native lifecycle service. Governed confirmation exposes exact target/scope/consequence. Domain binding remains immutable; no upgrade/rebind action was introduced.

Current closure:

```text
STRICT_PRELOCK_FINDINGS = RESOLVED
IMPLEMENTATION          = PRESENT
TARGETED_QA             = PRESENT
MASTER_REAUDIT          = PASS
FINAL_USER_UAT          = DEFERRED
```
