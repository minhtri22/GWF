# System Access Screen — BPS-M02 Checklist

## Identity

```text
SCREEN_ID        = SYSTEM_ACCESS
OWNER            = BPS-M02
ROUTE            = /app/system/access
PROTOCOL         = BPS-QA-FIRST-DEFERRED-UAT-v1 + STRICT_GOVERNANCE for mutations
STATUS           = QA_FINDINGS_CLOSED / CI_PENDING / FINAL_UAT_PENDING
BASE_HEAD        = fba88cb1603b751a182449e0afd28d6a355690dd
FINAL_UAT        = DEFERRED
```

## Governing sources

- `AGENTS.md`
- `docs/BPS_QA_FIRST_DEFERRED_UAT.md`
- `docs/BPS_SCREEN_FAST_LANE.md`
- `docs/BPS_MODULE_EXECUTION_MODEL.md` — BPS-M02 owns Projects + Access.
- `docs/UI_UX_PRODUCT_ARCHITECTURE_SPEC.md` §4.2, §15.4, §22, §24.
- `docs/BROWSER_PRODUCT_SURFACE_SPEC.md` §5.2, §6, §7.
- `src/gwr/tenancy.py` role/permission matrices and scope checks.
- `src/gwr/auth.py` session authority.
- `src/gwr/api.py` existing bearer tenancy/member mutations.

## Scope

This screen provides authoritative global Access administration for capabilities already implemented in the backend:

- current actor/session;
- accessible tenant/workspace/project memberships and roles;
- tenant creation;
- workspace creation;
- tenant/workspace/project member add;
- member revocation where a qualified service mutation exists or is added under this strict slice;
- exact authority/non-disclosure behavior.

Project-local Members & Access will later reuse these semantics in the Project Workspace configuration surface.

## Frozen checklist

### A. Read projection

- [x] AC-01 Add authenticated `GET /browser/access-summary`.
- [x] AC-02 Return current actor/session identity without exposing reusable tokens.
- [x] AC-03 Return only tenants/workspaces/projects visible to the actor.
- [x] AC-04 Show the actor's role/status at each visible scope.
- [x] AC-05 Full membership lists are returned only where the actor has `MANAGE_MEMBERS`; otherwise no hidden member directory is leaked.
- [x] AC-06 Return exact tenant/workspace/project IDs and human-readable names.
- [x] AC-07 Distinguish complete/empty/error state; no browser-local authority.

### B. Existing authority semantics

- [x] AC-08 Tenant roles use only `OWNER|ADMIN|MEMBER|VIEWER`.
- [x] AC-09 Workspace roles use only `OWNER|ADMIN|MEMBER|VIEWER`.
- [x] AC-10 Project roles use only `OWNER|RESEARCH_LEAD|RESEARCHER|REVIEWER|APPROVER|VIEWER`.
- [x] AC-11 Tenant creation remains HUMAN-only through `TenantService.create_tenant`.
- [x] AC-12 Workspace creation requires `MANAGE_WORKSPACE`.
- [x] AC-13 Member add requires existing `MANAGE_MEMBERS` checks at the target scope.
- [x] AC-14 Unauthorized/missing scope mutation does not disclose hidden resource existence.

### C. Browser mutation bridge — strict

- [x] AC-15 Browser mutations use the HttpOnly session principal; no bearer token is exposed to JavaScript.
- [x] AC-16 Add bounded browser tenant-create endpoint reusing `TenantService.create_tenant`.
- [x] AC-17 Add bounded browser workspace-create endpoint reusing `TenantService.create_workspace`.
- [x] AC-18 Add bounded browser member-add endpoints reusing tenancy service methods.
- [x] AC-19 Project member revoke reuses the existing tenancy mutation.
- [x] AC-20 If tenant/workspace revoke is added, it must mirror existing membership authority, persist a security event, and be regression-tested.
- [x] AC-21 Mutations return authoritative post-mutation projection/state, not optimistic browser-only state.

### D. UI

- [x] AC-22 Add `/app/system/access` as a BPS-M02 LIVE route only when the implemented surface is real.
- [x] AC-23 Show current session/actor identity.
- [x] AC-24 Show tenant/workspace/project access hierarchy and role.
- [x] AC-25 Show member lists only for manageable scopes.
- [x] AC-26 Provide create tenant/workspace controls only against live browser mutations.
- [x] AC-27 Provide add/revoke member controls only where actor authority permits.
- [x] AC-28 Member add uses exact Actor ID input; no unqualified global actor directory is invented.
- [x] AC-29 Loading/empty/error/unauthorized states are distinct.
- [x] AC-30 Light/Dark/System, sidebar, routing, Back/Forward and session behavior do not regress.

### E. QA / findings

- [x] AC-31 Positive tests cover tenant/workspace creation and membership add/revoke.
- [x] AC-32 Negative tests cover invalid role, unauthorized scope, hidden-resource non-disclosure and inactive/unknown actor.
- [x] AC-33 Access projection tests prove hidden tenant/workspace/project/member data is absent.
- [x] AC-34 Existing bearer APIs remain valid.
- [x] AC-35 No schema migration, no new role value, no weakened permission rule.
- [x] AC-36 Findings are recorded/fixed/rechecked until `FAIL=0 OPEN=0 COUNT=0`.

## QA findings and adjudication

Findings opened during assistant QA:

| Finding | Result |
| --- | --- |
| AC-F01 Targeted QA did not initially lock role catalogs, unknown actor, revoke security events and bearer regression | FIXED / RECHECKED |
| AC-F02 Compact viewport CSS hid the now-live actor/session menu | FIXED / RECHECKED |
| AC-F03 Member revoke executed without the required exact-target governed-action confirmation | FIXED / RECHECKED |
| AC-F04 Shared-shell regression test initially referenced CSS without loading the stylesheet fixture | FIXED / RECHECKED |

Deterministic assistant checks:

- full `web/app.js` parses successfully in a JavaScript engine;
- all 107 static `$("#id")` selectors resolve to real unique IDs in `web/index.html`;
- no duplicate HTML IDs were found;
- `/app/system/access` is covered by the canonical `/app/system/{path}` deep-link route;
- Access mutation UI uses only cookie-authenticated `/browser/access/*` contracts; no bearer token is exposed to JavaScript;
- member directories are emitted only for scopes where the current actor has `MANAGE_MEMBERS`;
- revoke confirmation names exact actor, exact scope and the consequence that direct membership becomes REVOKED while inherited access may remain;
- no schema migration, role addition or permission weakening was introduced.

Targeted automated tests are committed in `tests/test_bps_system_access.py`, and BPS-I00 routing/shared-shell regression assertions are extended in `tests/test_bps_i00_product_shell.py`.

At adjudication time, exact-head GitHub Actions are capacity-blocked in `queued` state. They are recorded as pending external execution, never as PASS. Any later failure reopens this screen before integrated QA/final UAT.

```text
TOTAL_IMPLEMENTATION_ITEMS      = 36
IMPLEMENTATION_PASS             = 36
IMPLEMENTATION_FAIL             = 0
IMPLEMENTATION_OPEN             = 0
IMPLEMENTATION_COUNT            = 0

QA_FINDINGS_FAIL                = 0
QA_FINDINGS_OPEN                = 0
QA_FINDINGS_COUNT               = 0

CI_EXECUTION                    = PENDING_EXTERNAL_CAPACITY
CI_EXAMPLE_DG_P10_RUN           = 36214785995
FINAL_UAT                       = DEFERRED
UNIT_STATE                      = QA_FINDINGS_CLOSED / CI_PENDING / FINAL_UAT_PENDING
```
