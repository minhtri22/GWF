# GWR v0.4 Handoff

## What is complete
The three v0.3 gaps requested for closure are implemented and exercised:

1. **Retrieval connector** — Crossref scholarly metadata + HTTPS document connector, bounded retry/backoff, 429 handling, durable TTL cache, response/source hashes, explicit degraded fallback and default SSRF-oriented host checks.
2. **Independent statistics** — raw experiment rows cross a subprocess boundary; the verifier recomputes metrics and returns hash-bound process evidence.
3. **Authenticated human authority** — password-derived credentials, signed/revocable sessions, authenticated exact-hash proposal approval, authenticated semantic root confirmation, FastAPI/CLI surfaces.

The existing 17-phase PASS/FAIL/PIVOT, checkpoint, invalidation and recovery logic remains intact.

## How to run

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\Activate.ps1
pip install -e ".[dev]"

PYTHONPATH=src python tools/run_real_research_v04.py --out evidence/v0.4/real_run
PYTHONPATH=src python tools/qa_v04.py
PYTHONPATH=src pytest -q
```

For a real external approval process, set a stable secret outside the source tree:

```text
GWR_AUTH_SECRET=<at least 32 random bytes>
```

and use `tools/approve_proposal.py` or the authenticated API. The automated evidence runner generates ephemeral QA credentials. Real deployments must provision stable identity secrets/credentials outside source control.

Crossref deployments should set a real contact email via `GWR_CROSSREF_MAILTO`.

## Evidence locations

`evidence/v0.4/real_run/`:
- `runtime.db` — authoritative state.
- `audit.json` — exported audit ledger.
- `status.json` — orchestration state.
- `artifacts.json` — current research artifacts.
- `auth_evidence.json` — authenticated session/approval evidence.
- `retrieval_evidence.json` — provider/cache/degradation provenance.
- `verifier_evidence.json` — process-isolation + hash evidence.
- `RUNTIME_REPORT.md` — derived human-readable report.

`evidence/v0.4/`:
- QA outputs.
- coverage XML/report.
- SHA-256 manifest.

## Remaining issues
These are no longer the three v0.3 shortcuts; they are next-stage product/deployment work:

- Add an enterprise identity adapter (OIDC/WebAuthn/passkeys) and TLS termination. The local password/HMAC service is a valid authenticated alpha boundary, not an enterprise identity platform.
- Add a second scholarly provider such as OpenAlex/DataCite and provider failover/consensus policies. Crossref + generic web retrieval is one production-oriented connector path, not universal literature coverage.
- Persist large raw source/experiment blobs in content-addressed object storage instead of SQLite/JSON artifacts.
- Add PostgreSQL migrations, queue/worker leases, distributed idempotency and multi-node recovery.
- Add observability: metrics, traces, provider latency/error SLOs and alerting.
- Optimize approval resume so expensive pre-approval executor output can be materialized as a frozen pending artifact rather than recomputed after approval.
- Add source-content extraction/citation verification for full PDFs; v0.4 primarily hardens retrieval/provenance, not semantic paper parsing.
- Run additional unrelated hypotheses to test generality of the Research Domain Package.

## Maturity
`v0.4` is a **hardened Real Research Alpha / single-node reference platform**. The requested three boundaries are now real mechanisms rather than synthetic shortcuts, but the overall system is not yet a public multi-tenant production product.
