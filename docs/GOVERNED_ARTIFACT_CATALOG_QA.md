# GWF Governed Artifact Catalog — Documentation QA

## Status

**Semantic QA: FAIL / remediation required.**

Candidate specification commit:

`4cc187320820ea4ff144130b0b63f6d23e3a9e3b`

## Scope

Review only the new packing-only GAC documents. This QA does not validate an implementation.

## Findings

### GAC-F01 — HIGH — OPEN — Publication uniqueness/idempotency is undefined

Repeated publication of the same exact subject under the same scope/policy could create multiple active entries with ambiguous identity.

Required: define publication identity/idempotency key and collision behavior.

- [ ] RESOLVED

### GAC-F02 — HIGH — OPEN — Publication policy identity/snapshot is insufficient

`publication_policy_ref` alone does not prove which exact policy version/hash admitted an item or what source validity was observed.

Required: bind exact policy revision/hash and publication-time eligibility snapshot.

- [ ] RESOLVED

### GAC-F03 — MEDIUM — OPEN — Search index drift/rebuild semantics are undefined

Optional FTS/vector/external indexes are derived state, but the spec does not define rebuild source, index revision identity or stale-index handling.

Required: catalog database remains authoritative; search indexes are rebuildable projections with explicit index revision/status.

- [ ] RESOLVED

### GAC-F04 — HIGH — OPEN — Query execution status can be confused with “zero matches”

Failure classes mention index unavailability, but CatalogQueryResult does not separate execution validity/completeness from content results.

Required: separate query execution status from result-set status; unavailable/partial index cannot be represented as a valid empty result.

- [ ] RESOLVED

### GAC-F05 — MEDIUM — OPEN — Catalog-state transitions are not formalized

`CANDIDATE | PUBLISHED | WITHDRAWN | TOMBSTONED` exists without allowed transitions/republication semantics.

Required: define allowed transitions, immutable history, authority and whether withdrawn exact subject can be republished as a new entry/revision.

- [ ] RESOLVED

### GAC-F06 — MEDIUM — OPEN — Search metadata namespace/ownership is undefined

Generic `search_metadata` can create collisions between G2E, software, research and document consumers.

Required: core metadata fields plus namespaced extension metadata with schema/version owner.

- [ ] RESOLVED

### GAC-F07 — HIGH — OPEN — Catalog visibility could accidentally broaden source access

Catalog scope and source artifact permission are described but intersection semantics are not explicit.

Required: effective read permission = catalog visibility AND source/object/external-ref access; catalog publication never grants broader source access.

- [ ] RESOLVED

### GAC-F08 — MEDIUM — OPEN — External immutable reference eligibility is too weak

“Digest when available” can allow a mutable external locator to be presented as immutable.

Required: external publication must bind either verified content digest or provider-issued immutable snapshot/version identity accepted by PublicationPolicy; otherwise reject.

- [ ] RESOLVED

## Existing boundary checks

- [x] GAC is catalog/index/publication, not canonical artifact storage.
- [x] Existing Artifact/Revision/TraceLink/ObjectRef primitives are reused.
- [x] Search results are discovery candidates, not proof/evidence admission.
- [x] No research-specific synthesis/applicability semantics are assigned to GWF.
- [x] Documentation Governance remains owner of document registry/QA/validity.
- [x] Reference Acquisition remains owner of external retrieval provenance.
- [x] This candidate changes only four new `docs/GOVERNED_ARTIFACT_CATALOG_*.md` files.
- [x] No code/runtime/schema migration/workflow changes exist.

## Verdict

`OPEN = 8`

**FAIL until all findings are resolved.**
