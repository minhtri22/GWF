# System Access Screen — BPS-M02 Checklist

## Identity

```text
SCREEN_ID        = SYSTEM_ACCESS
OWNER            = BPS-M02
ROUTE            = /app/system/access
PROTOCOL         = BPS-QA-FIRST-DEFERRED-UAT-v1 + STRICT_GOVERNANCE for mutations
STATUS           = CHECKLIST_FROZEN / IMPLEMENTATION_PENDING
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

- [ ] AC-01 Add authenticated `GET /browser/access-summary`.
- [ ] AC-02 Return current actor/session identity without exposing reusable tokens.
- [ ] AC-03 Return only tenants/workspaces/projects visible to the actor.
- [ ] AC-04 Show the actor's role/status at each visible scope.
- [ ] AC-05 Full membership lists are returned only where the actor has `MANAGE_MEMBERS`; otherwise no hidden member directory is leaked.
- [ ] AC-06 Return exact tenant/workspace/project IDs and human-readable names.
- [ ] AC-07 Distinguish complete/empty/error state; no browser-local authority.

### B. Existing authority semantics

- [ ] AC-08 Tenant roles use only `OWNER|ADMIN|MEMBER|VIEWER`.
- [ ] AC-09 Workspace roles use only `OWNER|ADMIN|MEMBER|VIEWER`.
- [ ] AC-10 Project roles use only `OWNER|RESEARCH_LEAD|RESEARCHER|REVIEWER|APPROVER|VIEWER`.
- [ ] AC-11 Tenant creation remains HUMAN-only through `TenantService.create_tenant`.
- [ ] AC-12 Workspace creation requires `MANAGE_WORKSPACE`.
- [ ] AC-13 Member add requires existing `MANAGE_MEMBERS` checks at the target scope.
- [ ] AC-14 Unauthorized/missing scope mutation does not disclose hidden resource existence.

### C. Browser mutation bridge — strict

- [ ] AC-15 Browser mutations use the HttpOnly session principal; no bearer token is exposed to JavaScript.
- [ ] AC-16 Add bounded browser tenant-create endpoint reusing `TenantService.create_tenant`.
- [ ] AC-17 Add bounded browser workspace-create endpoint reusing `TenantService.create_workspace`.
- [ ] AC-18 Add bounded browser member-add endpoints reusing tenancy service methods.
- [ ] AC-19 Project member revoke reuses the existing tenancy mutation.
- [ ] AC-20 If tenant/workspace revoke is added, it must mirror existing membership authority, persist a security event, and be regression-tested.
- [ ] AC-21 Mutations return authoritative post-mutation projection/state, not optimistic browser-only state.

### D. UI

- [ ] AC-22 Add `/app/system/access` as a BPS-M02 LIVE route only when the implemented surface is real.
- [ ] AC-23 Show current session/actor identity.
- [ ] AC-24 Show tenant/workspace/project access hierarchy and role.
- [ ] AC-25 Show member lists only for manageable scopes.
- [ ] AC-26 Provide create tenant/workspace controls only against live browser mutations.
- [ ] AC-27 Provide add/revoke member controls only where actor authority permits.
- [ ] AC-28 Member add uses exact Actor ID input; no unqualified global actor directory is invented.
- [ ] AC-29 Loading/empty/error/unauthorized states are distinct.
- [ ] AC-30 Light/Dark/System, sidebar, routing, Back/Forward and session behavior do not regress.

### E. QA / findings

- [ ] AC-31 Positive tests cover tenant/workspace creation and membership add/revoke.
- [ ] AC-32 Negative tests cover invalid role, unauthorized scope, hidden-resource non-disclosure and inactive/unknown actor.
- [ ] AC-33 Access projection tests prove hidden tenant/workspace/project/member data is absent.
- [ ] AC-34 Existing bearer APIs remain valid.
- [ ] AC-35 No schema migration, no new role value, no weakened permission rule.
- [ ] AC-36 Findings are recorded/fixed/rechecked until `FAIL=0 OPEN=0 COUNT=0`.

## Initial count

```text
TOTAL = 36
PASS  = 0
FAIL  = 0
OPEN  = 36
COUNT = 36
```
