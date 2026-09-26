# Operations Audit Screen — BPS-M03 Checklist

## Identity

```text
SCREEN_ID        = OPERATIONS_AUDIT
OWNER            = BPS-M03
ROUTE            = /app/operations/audit
PROTOCOL         = BPS-QA-FIRST-DEFERRED-UAT-v1
STATUS           = CHECKLIST_FROZEN / IMPLEMENTATION_PENDING
BASE_HEAD        = 4adacf55d999e62cfc0f0fad3c9237fb22266683
FINAL_UAT        = DEFERRED
```

## Governing sources

- `docs/UI_UX_PRODUCT_ARCHITECTURE_SPEC.md` §14.2, §17.3, §24, §28.
- `docs/BROWSER_PRODUCT_SURFACE_SPEC.md` §12.
- `src/gwr/db.py` authoritative `audit_events` schema.
- `src/gwr/governance.py` append-only audit semantics.
- `src/gwr/tenancy.py` project visibility authority.

## Source-supported boundary

Global Operations §17.3 requires cross-project audit only within actor-authorized scope. The persisted `audit_events` record has no generic `outcome` column. Therefore this screen must not invent one. It may expose/filter the persisted `reason_code`; project-local outcome semantics remain for a later screen only when backed by authoritative data.

## Frozen checklist

### A. Projection

- [ ] OAU-01 Add authenticated read-only `GET /browser/operations/audit`.
- [ ] OAU-02 Include events only from actor-visible projects.
- [ ] OAU-03 Return exact event ID, project ID/name and tenant/workspace context.
- [ ] OAU-04 Return actor, action, resource type/id, timestamp and persisted reason code.
- [ ] OAU-05 Return exact proposal/approval/run/decision/correlation IDs when present.
- [ ] OAU-06 Return before/after version and metadata hash when present.
- [ ] OAU-07 Preserve append-only ordering/provenance; no browser-authored audit state.
- [ ] OAU-08 Return generated_at/build/query status and truthful zero/error distinction.

### B. Filtering/presentation

- [ ] OAU-09 Page filter covers event/project/actor/action/resource IDs.
- [ ] OAU-10 Provide tenant/workspace/project filters.
- [ ] OAU-11 Provide actor filter.
- [ ] OAU-12 Provide action/event filter.
- [ ] OAU-13 Provide resource-type filter.
- [ ] OAU-14 Provide client-side from/to time filter over authoritative timestamps.
- [ ] OAU-15 Display persisted reason_code as reason, never relabel it generic outcome.
- [ ] OAU-16 Exact linked identities remain inspectable/copyable.
- [ ] OAU-17 No mutation/control that alters audit history is exposed.

### C. Navigation/UI

- [ ] OAU-18 Promote Audit Operations subroute to LIVE; Runs/Approvals stay LIVE.
- [ ] OAU-19 Runtime remains visibly locked until its own screen closes.
- [ ] OAU-20 Loading/empty/error/partial states are distinct.
- [ ] OAU-21 Back/Forward/reload/theme/sidebar/session behavior does not regress.
- [ ] OAU-22 Compact research-workspace hierarchy matches approved shell.

### D. QA

- [ ] OAU-23 Tests prove hidden-project audit events absent.
- [ ] OAU-24 Tests prove linked proposal/approval/run/decision/correlation identities preserved.
- [ ] OAU-25 Tests prove reason_code is preserved verbatim and no fabricated outcome exists.
- [ ] OAU-26 Tests cover zero/unavailable states.
- [ ] OAU-27 No schema/authority/mutation/evidence semantics change.
- [ ] OAU-28 Findings fixed/rechecked to implementation `FAIL=0 OPEN=0 COUNT=0`.

## Initial count

```text
TOTAL = 28
PASS  = 0
FAIL  = 0
OPEN  = 28
COUNT = 28
```
