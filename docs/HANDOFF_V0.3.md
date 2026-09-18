# Handoff — GWR v0.3 Real Research Alpha

## Completed
- Real research executor replaces the synthetic executor for the v0.3 run.
- Paper/web retrieval adapter implemented with live HTTP probe and deterministic provenance cache fallback.
- Exact experiment runner implemented.
- Statistical verifier implemented.
- 17-phase end-to-end run completed with PASS/FAIL/PIVOT decision machinery intact.
- Runtime retry and semantic recovery were both exercised by the real run.
- Checkpoint/resume lineage preserved; semantic recovery created generation 1.
- Final report and handoff artifacts were produced by the same runtime.

## Real run result
Outcome: `PASS` for the protocol-scoped Wilson-vs-Wald coverage hypothesis. See `evidence/v0.3/real_run/artifacts.json` for exact metrics and `runtime.db`/`audit.json` for authoritative execution provenance.

## Open engineering issues
1. Production retrieval connectors (Crossref/OpenAlex/Semantic Scholar), rate limits, retry/backoff, content licensing and DOI canonicalization.
2. Retrieval evidence should be content-addressed and preserve immutable raw responses, not only summarized records.
3. Human approval must move to an authenticated trusted UI/channel; the alpha runner uses a local human actor surrogate.
4. Statistical verifier should be isolatable as an independent process/container and sign its result.
5. Experiment runners need sandbox/resource quotas and artifact blob storage.
6. PostgreSQL, worker queue, distributed leases, migrations, backup/recovery and observability remain open from v0.2.
7. Citation verifier and claim-to-source entailment checking are not yet production-grade.
8. Run at least two unrelated real hypotheses before generalizing Research Domain readiness.

## Exact commands
```bash
python tools/run_real_research.py --out evidence/v0.3/real_run
pytest -q
python tools/qa_v03.py
```

## Resume semantics
No unresolved failure remains in the packaged run. The terminal checkpoint is recorded in `result.json`. To test recovery, rerun the command with the default recovery demo; phase 08 will detect the underspecified pilot plan and route back to phase 06.
