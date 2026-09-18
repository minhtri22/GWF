# Implementation QA — v0.8.4

The v0.8.4 gate nests the complete v0.8.3 gate.

Dedicated v0.8.4 checks cover:

- migration of plugin/SHA-QA tables on SQLite and PostgreSQL;
- AUTO and HUMAN_APPROVE remain separately configurable recovery modes;
- persisted plugin metadata rejects token/secret material;
- GitHub plugin capability enforcement;
- repository binding branch allowlist;
- feature-branch default write policy;
- HUMAN-only direct writes to the default branch;
- frozen change-set manifest;
- branch HEAD SHA preflight;
- per-file blob SHA preflight;
- second branch HEAD comparison immediately before write;
- adapter-side expected-head concurrency contract;
- commit parent SHA verification;
- resulting branch HEAD SHA verification;
- post-commit file SHA-256 verification;
- STALE on branch/file mismatch with zero provider write;
- content substitution rejection after manifest freeze;
- VERIFIED as the only QA-complete GitHub write state;
- API metadata advertises plugin registry and SHA-safe GitHub commit support;
- Python compileall.

The normative repository-write procedure is `docs/GITHUB_SHA_QA_STANDARD.md`.
