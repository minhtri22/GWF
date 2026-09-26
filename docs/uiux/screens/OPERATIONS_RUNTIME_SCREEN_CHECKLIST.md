# Operations Runtime Screen — BPS-M03 Checklist

## Identity

```text
SCREEN_ID        = OPERATIONS_RUNTIME
OWNER            = BPS-M03
ROUTE            = /app/operations/runtime
PROTOCOL         = BPS-QA-FIRST-DEFERRED-UAT-v1
STATUS           = QA_FINDINGS_CLOSED / CI_PENDING / FINAL_UAT_PENDING
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

- [x] ORT-01 Add authenticated read-only `GET /browser/operations/runtime`.
- [x] ORT-02 Include jobs only from actor-visible projects.
- [x] ORT-03 Include worker records only when referenced by visible current jobs or visible job-attempt history.
- [x] ORT-04 Return exact job/project/workunit IDs and project tenant/workspace scope.
- [x] ORT-05 Return persisted job status, priority, available/created/updated timestamps.
- [x] ORT-06 Return required resources/capabilities and WorkUnit conflict reservation keys.
- [x] ORT-07 Return current lease worker/token-presence/expiry without exposing reusable secret material.
- [x] ORT-08 Never return raw lease token value to browser.
- [x] ORT-09 Return attempt count/max attempts and full visible attempt history.
- [x] ORT-10 Attempt history includes worker, attempt number, run ID, status, start/heartbeat/lease-expiry/finish/error.
- [x] ORT-11 Return persisted run status for linked attempt run where present.
- [x] ORT-12 Return visible scheduler event/requeue/recovery history for each visible job.
- [x] ORT-13 Return referenced worker actor/status/capabilities/resources/heartbeat TTL/last heartbeat/registered time.
- [x] ORT-14 Return generated_at/build/query status and truthful zero/error distinction.

### B. UI

- [x] ORT-15 Promote Runtime Operations subroute to LIVE; Runs/Approvals/Audit remain LIVE.
- [x] ORT-16 Job table shows exact IDs, project, status, required resources/capabilities, attempts and lease summary.
- [x] ORT-17 Selecting a job opens read-only detail with attempts + scheduler events.
- [x] ORT-18 Worker section shows only referenced workers and exact worker/actor IDs.
- [x] ORT-19 Worker capacity/capabilities and heartbeat status are visible without a mutation control.
- [x] ORT-20 Conflict reservation keys are visible for job/workunit inspection.
- [x] ORT-21 Project/run linkage is inspectable but no Project/Run deep action is faked before their owning screens are LIVE.
- [x] ORT-22 Page filters cover job/project/workunit/status/worker.
- [x] ORT-23 Loading/empty/error/partial states are distinct.
- [x] ORT-24 No worker register/status/heartbeat/lease/effect-commit controls appear.
- [x] ORT-25 Back/Forward/reload/theme/sidebar/session behavior does not regress.

### C. QA

- [x] ORT-26 Tests prove hidden-project jobs/attempts/workers absent.
- [x] ORT-27 Tests prove historical worker from an abandoned attempt remains visible when referenced by a visible job.
- [x] ORT-28 Tests prove raw `lease_token` is absent while token presence may be indicated.
- [x] ORT-29 Tests cover READY/LEASED/RUNNING/SUCCEEDED/FAILED-style persisted states without inventing new state.
- [x] ORT-30 Tests cover scheduler recovery/requeue event preservation.
- [x] ORT-31 Tests cover zero/unavailable projection.
- [x] ORT-32 UI/source regression proves forbidden worker/runtime mutation controls/endpoints are absent.
- [x] ORT-33 No schema/authority/runtime-protocol semantic change.
- [x] ORT-34 Findings fixed/rechecked to implementation `FAIL=0 OPEN=0 COUNT=0`.

## QA findings and adjudication

| Finding | Observation | Correction | State |
| --- | --- | --- | --- |
| ORT-F01 | attempt projection included arbitrary persisted `job_attempts.metadata` although the browser contract did not require it | removed attempt metadata from the browser projection; exact required attempt/run/error fields remain | PASS |
| ORT-F02 | targeted QA covered truthful zero state but not a projection outage | added controlled unavailable-path regression proving failure is not represented as empty jobs/workers | PASS |
| ORT-F03 | authoritative `available_at` was returned but omitted from the job presentation | Runtime table now shows persisted availability time alongside status/priority/update | PASS |
| ORT-F04 | initial status-fixture enqueue order allowed FIFO scheduler selection to lease the READY sentinel instead of the intended RUNNING fixture | reordered fixture creation so persisted READY/LEASED/RUNNING/SUCCEEDED/FAILED states are deterministic | PASS |

Deterministic assistant QA on implementation HEAD `91f2b8d8984e384626e6538dae57b34d815ef58c`:

- full `web/app.js` syntax parse: PASS;
- duplicate HTML IDs: 0;
- missing static `$("#id")` targets: 0;
- all Runtime view/filter/detail IDs resolve;
- browser projection constructs no raw `lease_token` field;
- attempt metadata and worker metadata are not emitted;
- tests assert actual lease token strings are absent from serialized browser response;
- hidden-project job/worker exclusion is locked;
- abandoned historical attempt/worker visibility is locked;
- persisted READY / LEASED / RUNNING / SUCCEEDED / FAILED states are covered without normalization;
- scheduler recovery/requeue history is preserved;
- zero and unavailable outcomes are distinct;
- frontend contains no `register_worker`, `heartbeat_worker`, `set_worker_status`, `lease_next`, `heartbeat_job`, `commit_effect`, `complete_job`, or `fail_job` call;
- no schema, authority or distributed-runtime protocol mutation was introduced.

Exact-head GitHub Actions may remain capacity-queued. Queue state is external execution evidence, not an implementation finding and is never represented as PASS. Any later CI failure reopens the affected unit before integrated QA/final UAT.

```text
TOTAL_IMPLEMENTATION_ITEMS = 34
IMPLEMENTATION_PASS        = 34
IMPLEMENTATION_FAIL        = 0
IMPLEMENTATION_OPEN        = 0
IMPLEMENTATION_COUNT       = 0

QA_FINDINGS_FAIL           = 0
QA_FINDINGS_OPEN           = 0
QA_FINDINGS_COUNT          = 0

CI_EXECUTION               = PENDING_EXTERNAL_CAPACITY
FINAL_UAT                  = DEFERRED
UNIT_STATE                 = QA_FINDINGS_CLOSED / CI_PENDING / FINAL_UAT_PENDING
```
