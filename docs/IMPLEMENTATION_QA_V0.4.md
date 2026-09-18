# GWR v0.4 Implementation QA

## Final checks

- `tools/qa_v04.py`: PASS, 0 errors.
- generic kernel implementation QA: PASS.
- research Domain Package QA: PASS.
- 17 phases / 19 artifact types / 17 gates / 52 failure types.
- full pytest suite: 29/29 PASS.
- compileall: PASS.
- parent-process coverage run (28 tests, excluding the already separately executed full real-research e2e test): 75%.
- `api.py`: 82%.
- `auth.py`: 86%.
- `stat_verifier.py`: 86%.
- The excluded real-research e2e path is exercised both by the plain 29-test suite and the packaged `evidence/v0.4/real_run` acceptance execution.

`stat_verifier_worker.py` runs in a subprocess and therefore is not attributed by the parent pytest coverage process; its behavior is exercised through `SubprocessStatisticalVerifier` acceptance tests and the real run.

## Hardening-specific tests

### Retrieval
- 429 is retryable.
- `Retry-After` is honored.
- successful Crossref JSON is normalized.
- durable cache serves a repeated query without another provider request.
- live retrieval degradation in the real run is explicit and provenance-labelled.

### Verifier isolation
- worker PID differs from the caller PID.
- verifier input hash is checked.
- verifier result hash is checked.
- raw rows are authoritative.
- experiment-process aggregate metrics can be corrupted without changing the independent recomputation path.

### Human authentication
- wrong password is rejected.
- HUMAN actor is required for registered credentials.
- signed session is required for authenticated approval.
- proposal exact-hash enforcement remains active.
- session revocation is enforced.
- audit contains `AUTHENTICATED_APPROVAL`.
- real run uses authenticated approval for all proposal rows, including `CONFIRM_ROOT`.

## Real-run invariant checks

- `COMPLETED` / scientific `PASS`.
- generation >= 1, proving recovery/resume occurred.
- open failures = 0.
- RecoveryPlan count >= 1.
- approved `CONFIRM_ROOT` proposal exists.
- approval rows == authenticated approval audit events.
- auth sessions == approval rows in the evidence run.
- all one-time approval sessions revoked.
- independent verifier evidence present.
