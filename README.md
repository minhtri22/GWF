# Governed Workflow Runtime (GWF)

> **Mandatory BPS agent startup:** before any UI/UX / Browser Product Surface implementation or handoff, read the root `AGENTS.md` first. It is the canonical one-slice-at-a-time QA/local-UAT protocol; repository state and exact governing blobs override chat summaries.

GWF is a domain-neutral governance and execution runtime for long-running AI/agent work.

Its purpose is to make agent work **resumable, auditable, authority-aware and reproducible** even when the agent, model, machine or session changes. GWF treats plans, revisions, evidence, approvals, failures, QA, checkpoints and handoffs as governed runtime state rather than relying on chat history.

GWF is not an n8n-style integration platform and is not a replacement for Git, GitHub, documentation tools or domain-specific scientific methods. External systems remain tools/plugins; GWF owns the control plane around them.

## What GWF governs

A governed execution can make explicit:

- who or what is allowed to act;
- the exact artifact/revision/SHA being used;
- what scope is frozen before work starts;
- what evidence was produced and by which run;
- what failed and whether retry/recovery is allowed;
- when human approval is required;
- which QA result applies to which exact revision;
- what remains valid/stale/blocked;
- where execution can safely resume;
- what must be preserved in the final handoff.

The core design principle is:

> Preserve exact state and evidence; do not silently repair history to make a workflow look clean.

## Project documentation governance

Projects using the current Documentation Governance contract organize governed documentation under their own repository:

```text
docs/
  gov/
    <document>.vN.md
    archive/
  <phase-id>/
    <document>.vN.md
    archive/
```

The active document is versioned. On revision, the previous source is destined for the sibling `archive/`, and the new version links to it. Stable GWF Artifact/Revision identity remains canonical even when paths change.

Document mutation consumes the workflow mode already frozen for the running PhaseExecution:

- `AUTO` — the agent may mutate documents owned by its authorized phase/workflow scope;
- `HUMAN_APPROVE` — document mutation requires human approval.

This does **not** broaden AUTO recovery semantics.

A frozen governance document is stronger than either mode:

```text
GOV / FROZEN
    -> BLOCK_REQUIRES_EXPLICIT_USER_AUTHORIZATION
```

DG-P10 classifies the change, decides mutation authority and computes the deterministic archive/version lineage plan. Concrete multi-file source mutation remains a governed DG-P11 DocumentChangeSet.

## Agent execution protocol

Agent work is observable through:

```text
LOAD -> PREFLIGHT -> PLAN -> EXECUTE -> VERIFY -> HANDOFF -> COMPLETE
```

Important invariants include:

- no preflight PASS -> no plan;
- no plan -> no execution;
- persist a problem before retry/replan;
- no QA PASS -> no handoff;
- no handoff -> no complete;
- project/database state, not chat context, is authoritative.

## Domain packages

GWF ships domain packages that map domain-specific artifacts, phases, gates, failure modes and approval policies onto the same runtime primitives.

Current first-party examples include:

- `domains/research.workflow.yaml` — governed research execution;
- `domains/software.workflow.yaml` — repository-first software delivery;
- `domains/example.workflow.yaml` — scaffold/reference domain.

The runtime is designed so other domains can reuse the same governance substrate without copying the kernel.

## GitHub safety

GWF's GitHub boundary uses exact repository/commit/blob identities and optimistic expected-SHA writes.

For a governed write, GWF freezes the expected branch/file state, verifies it before mutation, writes with an expected head, then re-fetches and verifies the resulting commit, branch and content.

`COMMITTED` alone is not QA-complete; exact verification is required.

## Windows install + canonical product server

After clone or pull:

```powershell
.\install.ps1
```

The default installer is intentionally bounded to make the product runnable:

- resolves Python >=3.11;
- creates/updates `.venv`;
- installs normal runtime dependencies, including the canonical ASGI server;
- validates production Domain/Pilot contracts;
- compiles runtime sources;
- validates canonical server configuration wiring with a temporary smoke-only secret;
- writes exact HEAD/environment/timing evidence to `.gwr\install\install-report.json`.

Full repository/DG/PostgreSQL qualification is explicit:

```powershell
.\install.ps1 -Qualification
.\install.ps1 -Qualification -SkipPostgres
```

Legacy qualification switches such as `-SkipPostgres`, `-SkipTests`, `-SkipUat` and `-RequirePostgres` continue to enter qualification mode for compatibility with existing qualification automation.

### Start the canonical local product

Configure a deployment auth secret of at least 32 bytes. A fresh local database may optionally receive one bootstrap human identity.

```powershell
$env:GWR_AUTH_SECRET = "<at-least-32-byte-local-secret>"
$env:GWR_BOOTSTRAP_USERNAME = "operator"
$env:GWR_BOOTSTRAP_PASSWORD = "<at-least-12-character-password>"

.\scripts\gwf_server.ps1 start
```

Open:

```text
http://127.0.0.1:8765/app
```

Lifecycle commands:

```powershell
.\scripts\gwf_server.ps1 status
.\scripts\gwf_server.ps1 restart
.\scripts\gwf_server.ps1 stop
```

The browser shell uses an HttpOnly same-origin GWF session cookie. It does not persist reusable bearer tokens in JavaScript-accessible browser storage.

The historical `tools/browser_uat_server.py` and related UAT launchers are not the canonical product server.


## Repository map

```text
src/gwr/       runtime kernels/services
domains/       governed domain packages
tests/         regression + governance fixtures
tools/         gates, QA and historical/operational utilities
scripts/       canonical product lifecycle and slice-local UAT entry points
docs/          architecture/governance/research records for GWF itself
pilots/        bounded pilot profiles
evidence/      generated qualification evidence
web/           authoritative browser shell/product assets
```

## Current development model

GWF evolves through bounded governance transitions. A documentation/specification PASS does not automatically authorize implementation, an implementation PASS does not automatically formal-close a phase, and a later phase is not inferred merely because an earlier one passed.

Negative runs and findings are preserved rather than erased by rerun.
