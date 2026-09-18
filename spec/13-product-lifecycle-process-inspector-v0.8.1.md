# GWR v0.8.1 — Product Lifecycle & Process Inspector

v0.8.1 closes three product gaps discovered before UAT: persistent domain lifecycle, project creation pinned to an immutable published domain revision, and process/phase inspection.

## Domain lifecycle

Tenant-scoped domain packages contain immutable revisions.

Revision states: DRAFT -> VALIDATED -> PUBLISHED.

Publishing requires the canonical DomainSDK validator to pass. A published revision cannot be edited in place; changes create a new revision.

## Project lifecycle

A scoped project may pin one PUBLISHED domain revision. The project binding is immutable. Future domain revisions do not silently upgrade existing projects.

The runtime host remains configured with one active executable domain package. v0.8.1 registry/pinning is a product lifecycle contract; executing a project whose pinned domain differs from the host's active domain requires a compatible domain-specific runtime host. The UI exposes the pin rather than pretending a silent multi-domain executor exists.

## Process inspector

ProcessInspectorService derives current status and full history from authoritative orchestration, phase, run, evidence, gate, failure, checkpoint and audit records.

Per-phase inspection returns inputs, outputs, evidence, gates, failure, checkpoint and a chronological event stream. Previous attempts and generations remain visible.

## Static UAT

GitHub Pages remains non-authoritative. Domain/project create operations are simulated in localStorage and explicitly labelled UAT. Phase Inspector uses pinned fixture history so users can test navigation, history comparison and logs without a fake backend.

## Exit gate

The complete v0.8 gate must remain PASS. Dedicated lifecycle/process tests run on SQLite and PostgreSQL 17, UI build is validated, and compileall must pass.
