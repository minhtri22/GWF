# Operations Audit Screen — BPS-M03 Checklist

## Identity

```text
SCREEN_ID        = OPERATIONS_AUDIT
OWNER            = BPS-M03
ROUTE            = /app/operations/audit
PROTOCOL         = BPS-QA-FIRST-DEFERRED-UAT-v1
STATUS           = QA_FINDINGS_CLOSED / CI_PENDING / FINAL_UAT_PENDING
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

- [x] OAU-01 Add authenticated read-only `GET /browser/operations/audit`.
- [x] OAU-02 Include events only from actor-visible projects.
- [x] OAU-03 Return exact event ID, project ID/name and tenant/workspace context.
- [x] OAU-04 Return actor, action, resource type/id, timestamp and persisted reason code.
- [x] OAU-05 Return exact proposal/approval/run/decision/correlation IDs when present.
- [x] OAU-06 Return before/after version and metadata hash when present.
- [x] OAU-07 Preserve append-only ordering/provenance; no browser-authored audit state.
- [x] OAU-08 Return generated_at/build/query status and truthful zero/error distinction.

### B. Filtering/presentation

- [x] OAU-09 Page filter covers event/project/actor/action/resource IDs.
- [x] OAU-10 Provide tenant/workspace/project filters.
- [x] OAU-11 Provide actor filter.
- [x] OAU-12 Provide action/event filter.
- [x] OAU-13 Provide resource-type filter.
- [x] OAU-14 Provide client-side from/to time filter over authoritative timestamps.
- [x] OAU-15 Display persisted reason_code as reason, never relabel it generic outcome.
- [x] OAU-16 Exact linked identities remain inspectable/copyable.
- [x] OAU-17 No mutation/control that alters audit history is exposed.

### C. Navigation/UI

- [x] OAU-18 Promote Audit Operations subroute to LIVE; Runs/Approvals stay LIVE.
- [x] OAU-19 Runtime remains visibly locked until its own screen closes.
- [x] OAU-20 Loading/empty/error/partial states are distinct.
- [x] OAU-21 Back/Forward/reload/theme/sidebar/session behavior does not regress.
- [x] OAU-22 Compact research-workspace hierarchy matches approved shell.

### D. QA

- [x] OAU-23 Tests prove hidden-project audit events absent.
- [x] OAU-24 Tests prove linked proposal/approval/run/decision/correlation identities preserved.
- [x] OAU-25 Tests prove reason_code is preserved verbatim and no fabricated outcome exists.
- [x] OAU-26 Tests cover zero/unavailable states.
- [x] OAU-27 No schema/authority/mutation/evidence semantics change.
- [x] OAU-28 Findings fixed/rechecked to implementation `FAIL=0 OPEN=0 COUNT=0`.

## QA findings and adjudication

| Finding | Result |
| --- | --- |
| OAU-F01 A failed refresh could retain a stale scope badge and filter option metadata from a previous successful Audit projection | FIXED / RECHECKED |

Deterministic QA:

- JavaScript parse PASS;
- every static selector resolves to a unique HTML ID;
- Audit route hides Runs/Approvals and locked Operations view hides Audit;
- authorized projection excludes hidden-project events;
- exact linked proposal/approval/run/decision/correlation IDs are preserved;
- persisted `reason_code` is displayed verbatim and no generic `outcome` is invented;
- error rendering clears stale scope/filter metadata;
- no Audit mutation exists.

```text
TOTAL_IMPLEMENTATION_ITEMS = 28
IMPLEMENTATION_PASS        = 28
IMPLEMENTATION_FAIL        = 0
IMPLEMENTATION_OPEN        = 0
IMPLEMENTATION_COUNT       = 0
QA_FINDINGS_COUNT          = 0
CI_EXECUTION               = PENDING_EXTERNAL_CAPACITY
FINAL_UAT                  = DEFERRED
UNIT_STATE                 = QA_FINDINGS_CLOSED / CI_PENDING / FINAL_UAT_PENDING
```
