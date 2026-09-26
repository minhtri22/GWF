# Operations Runtime Screen — BPS-M03 Checklist

## Identity

```text
SCREEN_ID        = OPERATIONS_RUNTIME
OWNER            = BPS-M03
ROUTE            = /app/operations/runtime
PROTOCOL         = BPS-QA-FIRST-DEFERRED-UAT-v1
STATUS           = CHECKLIST_FROZEN / IMPLEMENTATION_PENDING
BASE_HEAD        = 716a9ce775a50d421b70ac55d9f5dff12a051418
FINAL_UAT        = DEFERRED
```

## Governing sources

- `docs/UI_UX_PRODUCT_ARCHITECTURE_SPEC.md` §17.4 and §34A.10.
- `docs/BROWSER_PRODUCT_SURFACE_SPEC.md` §13.
- `src/gwr/distributed.py` durable scheduler/worker state and read models.
- `migrations/0003_v07_distributed_runtime.sql` exact runtime persistence.
- `src/gwr/tenancy.py` project visibility authority.

## Strict boundary

This screen is read-only for worker/runtime administration.

It MUST NOT expose:

- `register_worker`;
- `heartbeat_worker`;
- `set_worker_status`;
- lease grant/heartbeat;
- effect commit;
- worker-side completion.

Those operations are runtime protocol primitives without an authenticated browser-admin contract.

## Frozen checklist

### A. Authorized runtime projection

- [ ] ORT-01 Add authenticated read-only `GET /browser/operations/runtime`.
- [ ] ORT-02 Include jobs only from actor-visible projects.
- [ ] ORT-03 Include worker records only when referenced by visible current jobs or visible job-attempt history.
- [ ] ORT-04 Return exact job/project/workunit IDs and project tenant/workspace scope.
- [ ] ORT-05 Return persisted job status, priority, available/created/updated timestamps.
- [ ] ORT-06 Return required resources/capabilities and WorkUnit conflict reservation keys.
- [ ] ORT-07 Return current lease worker/token-presence/expiry without exposing reusable secret material.
- [ ] ORT-08 Never return raw lease token value to browser.
- [ ] ORT-09 Return attempt count/max attempts and full visible attempt history.
- [ ] ORT-10 Attempt history includes worker, attempt number, run ID, status, start/heartbeat/lease-expiry/finish/error.
- [ ] ORT-11 Return persisted run status for linked attempt run where present.
- [ ] ORT-12 Return visible scheduler event/requeue/recovery history for each visible job.
- [ ] ORT-13 Return referenced worker actor/status/capabilities/resources/heartbeat TTL/last heartbeat/registered time.
- [ ] ORT-14 Return generated_at/build/query status and truthful zero/error distinction.

### B. UI

- [ ] ORT-15 Promote Runtime Operations subroute to LIVE; Runs/Approvals/Audit remain LIVE.
- [ ] ORT-16 Job table shows exact IDs, project, status, required resources/capabilities, attempts and lease summary.
- [ ] ORT-17 Selecting a job opens read-only detail with attempts + scheduler events.
- [ ] ORT-18 Worker section shows only referenced workers and exact worker/actor IDs.
- [ ] ORT-19 Worker capacity/capabilities and heartbeat status are visible without a mutation control.
- [ ] ORT-20 Conflict reservation keys are visible for job/workunit inspection.
- [ ] ORT-21 Project/run linkage is inspectable but no Project/Run deep action is faked before their owning screens are LIVE.
- [ ] ORT-22 Page filters cover job/project/workunit/status/worker.
- [ ] ORT-23 Loading/empty/error/partial states are distinct.
- [ ] ORT-24 No worker register/status/heartbeat/lease/effect-commit controls appear.
- [ ] ORT-25 Back/Forward/reload/theme/sidebar/session behavior does not regress.

### C. QA

- [ ] ORT-26 Tests prove hidden-project jobs/attempts/workers absent.
- [ ] ORT-27 Tests prove historical worker from an abandoned attempt remains visible when referenced by a visible job.
- [ ] ORT-28 Tests prove raw `lease_token` is absent while token presence may be indicated.
- [ ] ORT-29 Tests cover READY/LEASED/RUNNING/SUCCEEDED/FAILED-style persisted states without inventing new state.
- [ ] ORT-30 Tests cover scheduler recovery/requeue event preservation.
- [ ] ORT-31 Tests cover zero/unavailable projection.
- [ ] ORT-32 UI/source regression proves forbidden worker/runtime mutation controls/endpoints are absent.
- [ ] ORT-33 No schema/authority/runtime-protocol semantic change.
- [ ] ORT-34 Findings fixed/rechecked to implementation `FAIL=0 OPEN=0 COUNT=0`.

## Initial count

```text
TOTAL = 34
PASS  = 0
FAIL  = 0
OPEN  = 34
COUNT = 34
```
