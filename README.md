# Governed Workflow Runtime (GWF) v0.8.5

GWF is a governance and execution-quality runtime for long-running AI/agent work.

It is deliberately **not** an n8n-style integration platform. External systems are tools/plugins; GWF focuses on authority, frozen plans, evidence, QA, recovery, provenance, handoff and reproducible outcomes that do not depend on one particular agent retaining context.

## One-click Windows install

After clone or pull:

```powershell
.\install.ps1
```

The installer:

- resolves Python >=3.11 (prefers Python 3.12 and can install it with winget);
- creates/updates `.venv`;
- installs development + PostgreSQL dependencies;
- validates the research and software domain packages;
- validates the CQG and GWF pilot profiles;
- runs Python compile checks;
- runs the full local test suite by default;
- uses `GWR_TEST_DATABASE_URL` when supplied, or an ephemeral PostgreSQL 17 Docker container when Docker is available;
- writes a non-secret report to `.gwr/install/install-report.json`.

Useful options:

```powershell
.\install.ps1 -FreshVenv
.\install.ps1 -SkipPostgres
.\install.ps1 -RequirePostgres
.\install.ps1 -SkipTests -SkipPostgres
```

## Production domain packages

### Research — `domains/research.workflow.yaml`

Research v0.5 adds a prospective `study_lock` so scientific validity is not left to agent memory.

The lock covers preregistration/source/artifact hashes, fresh-data policy, metrics/gates, forbidden adaptations, execution-amendment boundaries, resource limits, stop rules, repair budget and no-rescue policy.

Execution remains the 17-phase research cycle with explicit PASS/FAIL/PIVOT, replication/replay, reporting and handoff.

### Software delivery — `domains/software.workflow.yaml`

Software delivery governs:

repository audit → scope lock → implementation plan → implementation → local tests → integration/regression → independent QA → candidate verification → merge → exact-main verification → handoff.

A commit is not a release. The outcome is complete only after required gates pass again on the exact merged main SHA.

### Example — `domains/example.workflow.yaml`

Scaffold/reference only. It is not the production software domain.

## Agent execution protocol

Real phases are governed by:

`LOAD → PREFLIGHT → PLAN → EXECUTE → VERIFY → HANDOFF → COMPLETE`

Important invariants include:

- no preflight PASS → no plan;
- no plan → no execution;
- persist ProblemRecord before retry/replan;
- no QA PASS → no handoff;
- no handoff → no complete;
- project/database state, not chat context, is authoritative.

Recovery mode is configurable:

- `AUTO`: safe/transient retries may proceed within policy and budget;
- `HUMAN_APPROVE`: pause before retry for human approval.

Normative/high-impact boundaries can still require human authority regardless of default recovery mode.

## GitHub safety

GWF supports SHA-safe repository changes through the GitHub plugin boundary.

GitHub Pages is treated as a public/static surface and must never contain or accept API keys, tokens, passwords, private keys, or other provider credentials. Public assets are scanned before and after build. See `docs/PUBLIC_PAGES_SECURITY.md`.

A governed write freezes branch/file SHAs, verifies them before write, passes expected head SHA to the provider, then re-fetches the commit/branch/files after write.

Only `VERIFIED` is QA-complete; `COMMITTED` is not.

See `docs/GITHUB_SHA_QA_STANDARD.md`.

## Initial dogfood pilots

- CQG next new research study: `pilots/cqg.research.yaml`
- GWF bounded self-upgrade: `pilots/gwf.self-upgrade.yaml`

See `docs/PILOT_CQG_GWF_V0.8.5.md`.

## Validation

The v0.8.5 acceptance gate nests the complete v0.8.4 regression chain and adds domain-skill, installer and pilot qualification on SQLite, PostgreSQL and Windows.
