# GWR v0.4 — Real Research Hardening Contract

## Scope
v0.4 closes three v0.3 alpha gaps without changing the 17-phase research lifecycle:

1. production-oriented paper/web retrieval boundary;
2. statistical verification in an independent process;
3. authenticated human approval/confirmation instead of actor-id trust.

The research outcome semantics remain `PASS | FAIL | PIVOT`. Runtime failures remain distinct from scientific `FAIL`.

## 1. Retrieval connector contract

### Provider boundary
`ProductionPaperRetriever` composes:
- `CrossrefConnector` for scholarly metadata;
- `WebDocumentConnector` for HTTPS document retrieval;
- `ResilientHttpClient` for transport policy;
- `DurableRetrievalCache` for durable response metadata caching.

### Required behavior
- HTTPS only by default.
- Private/loopback/link-local/reserved targets rejected by default to reduce SSRF risk.
- Explicit User-Agent identity.
- Crossref `mailto` support.
- retry on 408/425/429/5xx with bounded exponential backoff and `Retry-After` support.
- maximum response size enforcement.
- content SHA-256 and retrieval timestamp recorded.
- durable cache with TTL.
- degraded/offline provenance snapshot is never silent: `degraded=true` and `live_error` are recorded.

A cache/snapshot is evidence about retrieval provenance, not proof that a source was live-retrieved during the current run.

## 2. Independent statistical verification

The experiment process emits raw rows. `SubprocessStatisticalVerifier` sends only:
- raw experiment rows;
- precommitted thresholds;
- expected row count

to a separate Python process (`gwr.stat_verifier_worker`).

The verifier independently recomputes:
- Wilson/Wald MAE from raw coverages;
- per-n MAE;
- relative MAE reduction;
- paired sign-test counts and exact p-value;
- PASS/FAIL against the precommitted threshold.

The experiment-process aggregate metrics are deliberately ignored by the verifier.

Verifier evidence contains:
- `independent_process=true`;
- worker PID;
- verifier version;
- input SHA-256;
- result SHA-256.

`analysis_ready` now requires `independent_verifier_evidence` and the `independent_verifier_completed` predicate.

## 3. Authenticated human authority

### Credential boundary
`HumanAuthService` provides a local alpha authentication boundary:
- PBKDF2-HMAC-SHA256 password derivation with per-user random salt;
- signed HMAC bearer sessions;
- expiry;
- server-side session lookup;
- revocation;
- HUMAN actor enforcement.

### Approval contract
`GovernanceKernel.approve_proposal_authenticated(...)`:
1. verifies the bearer session;
2. resolves the authenticated human actor;
3. performs the existing exact proposal-hash approval checks;
4. writes an `AUTHENTICATED_APPROVAL` audit event bound to the session.

The v0.4 real run does not pass `human_approver_id` to `ResearchOrchestrator`.
Normative revisions pause at `WAITING_APPROVAL` until an externally authenticated human approves the frozen proposal.

### Root-cause confirmation
Semantic recovery also uses the same governance boundary. The runtime creates a system proposal with action `CONFIRM_ROOT`, pauses at `WAITING_HUMAN_CONFIRMATION`, and only executes invalidation/recovery after authenticated approval.

### Surfaces
- FastAPI: `/auth/login`, `/proposals/{id}`, `/proposals/{id}/approve`.
- CLI: `tools/approve_proposal.py` (interactive password + explicit `yes`).

The local password/session service is replaceable by OIDC/WebAuthn in a production deployment; GovernanceKernel consumes an authenticated actor rather than depending on the authentication mechanism itself.

## 4. Resume semantics

Authenticated approvals do not bypass checkpoints.

`PAUSE -> authenticated approval -> reconcile checkpoint -> resume`

For semantic failure:

`failure -> root proposal -> authenticated confirmation -> ImpactSet -> RecoveryPlan -> checkpoint -> resume earliest affected phase`

## 5. v0.4 acceptance requirements

A release passes only when all are true:
- 17 research phases validate.
- full real hypothesis run completes with a scientific outcome.
- at least one operational source failure is recorded and resolved when live retrieval is unavailable.
- at least one semantic recovery is checkpointed and resumed.
- no open failures remain at completion.
- every approval row in the v0.4 evidence run has an `AUTHENTICATED_APPROVAL` audit event.
- root confirmation is an approved `CONFIRM_ROOT` proposal.
- independent verifier process evidence is present and hash-consistent.
- retrieval degradation, if any, is explicit in provenance.
- automated tests, compile, domain QA, kernel QA and ZIP integrity pass.
