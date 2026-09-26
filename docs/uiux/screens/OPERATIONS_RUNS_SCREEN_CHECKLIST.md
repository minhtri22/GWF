# Operations Runs Screen — BPS-M03 Checklist

## Identity

```text
SCREEN_ID        = OPERATIONS_RUNS
OWNER            = BPS-M03
ROUTE            = /app/operations/runs
PROTOCOL         = BPS-QA-FIRST-DEFERRED-UAT-v1
STATUS           = CHECKLIST_FROZEN / IMPLEMENTATION_PENDING
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

- [ ] OR-01 Add authenticated read-only `GET /browser/operations/runs`.
- [ ] OR-02 Include runs only from projects visible to the authenticated actor.
- [ ] OR-03 Aggregate server-side; browser does not fan out project APIs or query DB.
- [ ] OR-04 Return `generated_at`, exact build SHA and complete/partial query status.
- [ ] OR-05 Successful zero results remain distinct from unavailable/error.

### B. Exact run identity/state

- [ ] OR-06 Show exact run ID.
- [ ] OR-07 Show exact project ID/name and tenant/workspace scope.
- [ ] OR-08 Show exact WorkUnit ID/type/status.
- [ ] OR-09 Show linked orchestration/phase execution identity and phase label when authoritative.
- [ ] OR-10 Show runtime status without inventing a normalized status not persisted by Runs.
- [ ] OR-11 Show actor/executor identity.
- [ ] OR-12 Show started/finished timestamps and duration only from authoritative timestamps.
- [ ] OR-13 Show exact input revision IDs, produced revision IDs and evidence IDs as counts/inspectable identities where appropriate.
- [ ] OR-14 Show latest authoritative audit/event timestamp/action associated with the run when available.

### C. Filters/presentation

- [ ] OR-15 Provide page filter by run/project/workunit identity or project name.
- [ ] OR-16 Provide tenant/workspace/project filters.
- [ ] OR-17 Provide runtime-status filter.
- [ ] OR-18 Filtering is transient presentation state only.
- [ ] OR-19 Compact table remains readable with exact IDs inspectable/copyable.
- [ ] OR-20 No fake Run detail link/action before BPS-M05 route becomes LIVE.

### D. Operations navigation/shared shell

- [ ] OR-21 `/app/operations/runs` deep-links/reloads correctly.
- [ ] OR-22 `/app/operations` resolves truthfully to the first LIVE Operations surface rather than a fake dashboard.
- [ ] OR-23 Operations local navigation exposes Runs and keeps Approvals/Audit/Runtime visibly locked until their own screens are QA-closed.
- [ ] OR-24 Light/Dark/System/sidebar/Back/Forward/session behavior does not regress.

### E. QA

- [ ] OR-25 Tests prove inaccessible project runs are absent.
- [ ] OR-26 Tests cover running/completed/failed-or-other persisted run statuses represented without fabrication.
- [ ] OR-27 Tests cover zero and error/unavailable contract.
- [ ] OR-28 BPS-I00/Home/Projects/Access routing regressions remain intact.
- [ ] OR-29 No schema, authority, mutation or scientific/evidence semantics change.
- [ ] OR-30 Findings are fixed/rechecked until implementation `FAIL=0 OPEN=0 COUNT=0`.

## Initial count

```text
TOTAL = 30
PASS  = 0
FAIL  = 0
OPEN  = 30
COUNT = 30
```
