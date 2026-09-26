# Operations Runs Screen — BPS-M03 Checklist

## Identity

```text
SCREEN_ID        = OPERATIONS_RUNS
OWNER            = BPS-M03
ROUTE            = /app/operations/runs
PROTOCOL         = BPS-QA-FIRST-DEFERRED-UAT-v1
STATUS           = QA_FINDINGS_CLOSED / CI_PENDING / FINAL_UAT_PENDING
BASE_HEAD        = 9fa896ed6745cadebb754fc017ef94265085f9c8
FINAL_UAT        = DEFERRED
```

## Governing sources

- `AGENTS.md`
- `docs/BPS_QA_FIRST_DEFERRED_UAT.md`
- `docs/UI_UX_PRODUCT_ARCHITECTURE_SPEC.md` §17.1, §24, §26.2, §28, §34A.2.
- `docs/BROWSER_PRODUCT_SURFACE_SPEC.md` §10, §22.
- `docs/BPS_MODULE_EXECUTION_MODEL.md` — BPS-M03 Operations.
- `src/gwr/product.py` existing project run read model.
- `src/gwr/process_inspector.py` run/phase linkage.
- `src/gwr/tenancy.py` project visibility authority.

## Scope

Global authorized cross-project **read-only Runs index**. Detailed run/phase inspection remains owned by Project Execution / BPS-M05 and must not be faked here.

## Frozen checklist

### A. Authorized projection

- [x] OR-01 Add authenticated read-only `GET /browser/operations/runs`.
- [x] OR-02 Include runs only from projects visible to the authenticated actor.
- [x] OR-03 Aggregate server-side; browser does not fan out project APIs or query DB.
- [x] OR-04 Return `generated_at`, exact build SHA and complete/partial query status.
- [x] OR-05 Successful zero results remain distinct from unavailable/error.

### B. Exact run identity/state

- [x] OR-06 Show exact run ID.
- [x] OR-07 Show exact project ID/name and tenant/workspace scope.
- [x] OR-08 Show exact WorkUnit ID/type/status.
- [x] OR-09 Show linked orchestration/phase execution identity and phase label when authoritative.
- [x] OR-10 Show runtime status without inventing a normalized status not persisted by Runs.
- [x] OR-11 Show actor/executor identity.
- [x] OR-12 Show started/finished timestamps and duration only from authoritative timestamps.
- [x] OR-13 Show exact input revision IDs, produced revision IDs and evidence IDs as counts/inspectable identities where appropriate.
- [x] OR-14 Show latest authoritative audit/event timestamp/action associated with the run when available.

### C. Filters/presentation

- [x] OR-15 Provide page filter by run/project/workunit identity or project name.
- [x] OR-16 Provide tenant/workspace/project filters.
- [x] OR-17 Provide runtime-status filter.
- [x] OR-18 Filtering is transient presentation state only.
- [x] OR-19 Compact table remains readable with exact IDs inspectable/copyable.
- [x] OR-20 No fake Run detail link/action before BPS-M05 route becomes LIVE.

### D. Operations navigation/shared shell

- [x] OR-21 `/app/operations/runs` deep-links/reloads correctly.
- [x] OR-22 `/app/operations` resolves truthfully to the first LIVE Operations surface rather than a fake dashboard.
- [x] OR-23 Operations local navigation exposes Runs and keeps Approvals/Audit/Runtime visibly locked until their own screens are QA-closed.
- [x] OR-24 Light/Dark/System/sidebar/Back/Forward/session behavior does not regress.

### E. QA

- [x] OR-25 Tests prove inaccessible project runs are absent.
- [x] OR-26 Tests cover running/completed/failed-or-other persisted run statuses represented without fabrication.
- [x] OR-27 Tests cover zero and error/unavailable contract.
- [x] OR-28 BPS-I00/Home/Projects/Access routing regressions remain intact.
- [x] OR-29 No schema, authority, mutation or scientific/evidence semantics change.
- [x] OR-30 Findings are fixed/rechecked until implementation `FAIL=0 OPEN=0 COUNT=0`.

## QA findings and adjudication

| Finding | Result |
| --- | --- |
| OR-F01 Operations view was not hidden by the older Home/Projects/Access/Diagnostics/locked renderers, allowing overlapping screens after navigation | FIXED / RECHECKED |
| OR-F02 Error/unavailable behavior had source handling but no negative API regression | FIXED / RECHECKED |

Deterministic QA:

- `web/app.js` parses successfully;
- every static `$("#id")` selector resolves to a unique HTML ID;
- all non-Operations route renderers explicitly hide `operationsRouteView`;
- `/app/operations` canonicalizes to `/app/operations/runs`;
- Runs preserves persisted runtime status and exact run/workunit/phase/project/scope identities;
- inaccessible-project runs are excluded by the server-side authorized projection;
- zero and API-unavailable states are distinct;
- no Run detail action is exposed before BPS-M05.

```text
TOTAL_IMPLEMENTATION_ITEMS = 30
IMPLEMENTATION_PASS        = 30
IMPLEMENTATION_FAIL        = 0
IMPLEMENTATION_OPEN        = 0
IMPLEMENTATION_COUNT       = 0
QA_FINDINGS_COUNT          = 0
CI_EXECUTION               = PENDING_EXTERNAL_CAPACITY
DG_P10_RUN                 = 36215445347
FINAL_UAT                  = DEFERRED
UNIT_STATE                 = QA_FINDINGS_CLOSED / CI_PENDING / FINAL_UAT_PENDING
```
