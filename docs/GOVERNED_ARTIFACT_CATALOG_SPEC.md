# GWF — Governed Artifact Catalog Specification

## 1. Status

**Document status:** packing-only specification / implementation deferred.

**Working branch:** `docs/governed-artifact-catalog-pack`.

**Specification baseline:** GWF `docs/reference-agent-interop-specs` at `f9a638310e095f760b3755583d230d2e65f50f45`.

This package defines the GWF-side capability required to publish, discover and retrieve governed artifacts across projects/workspaces without embedding research-specific interpretation into GWF.

No database migration, API, service, indexer, search engine, UI, DomainSDK change, Documentation Governance implementation, or G2E runtime change is authorized by this specification.

## 2. Problem

GWF already has project-scoped governed primitives:

- `Artifact` and immutable `Revision` in `KnowledgeKernel`;
- typed `TraceLink` provenance and impact propagation;
- evidence, gates, decisions and append-only audit events;
- content-addressed `ObjectRef`;
- tenant/workspace/project governance.

What is missing is a governed cross-project catalog/discovery layer that can answer:

- which exact governed artifacts are available for reuse or inspection;
- which immutable revision/object a result refers to;
- who may publish/query/read it;
- which project/workspace/tenant produced it;
- what provenance/classification metadata may be searched;
- whether a catalog item is published, withdrawn, or tombstoned;
- how semantic consumers such as G2E can publish/query their own payload types without GWF learning their scientific semantics.

## 3. Core boundary

The catalog is **not a second KnowledgeKernel**.

~~~text
Existing GWF state
Artifact → Revision → ObjectRef / TraceLink / Evidence
                │
                │ exact immutable identity
                ▼
        Governed Artifact Catalog
      publication / index / query
                │
                ▼
       consumers / adapters
  G2E, software, research, docs, UI
~~~

Canonical payload remains owned by existing GWF primitives. The catalog stores/indexes a reference to exact governed identity plus publication/search metadata.

### 3.1 GWF owns

- durable catalog membership;
- tenant/workspace/project scope;
- publication/withdrawal authority;
- immutable subject binding;
- catalog metadata/versioning;
- query/index behavior;
- access checks;
- audit/provenance of publication actions;
- optional search-backend adapter contracts.

### 3.2 GWF does not own

- whether studies corroborate/contradict;
- applicability of prior evidence to a new claim;
- scientific synthesis/meta-analysis;
- G2E ClaimSignature, ReuseDecision or SynthesisVerdict;
- automatic evidence admission into a G2E proof;
- domain interpretation of search results.

## 4. Relationship to existing GWF systems

### 4.1 KnowledgeKernel

The catalog MUST reuse, not replace, `artifacts`, `revisions`, `trace_links`, validity, audit and governance.

A catalog entry for a GWF artifact MUST bind an exact `revision_id + content_hash`.

A floating current revision may be exposed only as a convenience resolver. Formal catalog subject identity remains pinned.

### 4.2 Object store

Large/binary content remains in content-addressed object storage. Catalog records immutable `ObjectRef` identity when required and MUST NOT duplicate blobs.

### 4.3 Documentation Integrity & Governance

Documentation Governance remains authoritative for DocumentRecord/DocumentRevision semantics, document relations, validity/staleness, QA/findings, append-only and authority rules.

Catalog MAY index a document revision only after the Documentation Governance layer declares it eligible. Publication does not make an unverified/stale document valid and cannot bypass document QA.

Catalog MUST NOT introduce a competing document registry, link checker, Markdown validator, stale-propagation engine or documentation authority model.

### 4.4 Reference Acquisition

Reference Acquisition owns external retrieval/session/canonical-source provenance. It MAY produce a candidate subject for catalog publication when the exact inspected snapshot/reference satisfies PublicationPolicy.

Retrieval alone does not publish an item. Publication does not convert a reference into empirical proof.

### 4.5 Agent interoperability

Agents may propose publication/query actions through GWF authority. Agent/provider/harness identity does not grant publication authority by itself.

## 5. Conceptual objects

### 5.1 CatalogEntry

Required conceptual fields:

- `catalog_entry_id`;
- `subject_kind`;
- `subject_ref`;
- `subject_content_hash`;
- `subject_schema_or_type`;
- `producer_project_id`;
- `tenant_id`;
- `workspace_id`;
- `publication_scope`;
- `catalog_state`;
- `classification_tags`;
- `search_metadata`;
- `provenance_refs`;
- `publication_policy_ref`;
- `published_by`;
- `published_at`;
- `withdrawn_at`;
- `withdrawal_reason`.

CatalogEntry is an index/publication record, not a payload copy.

### 5.2 Subject kinds

Initial subject kinds:

- `GWF_REVISION`;
- `GWF_OBJECT_REF`;
- `EXTERNAL_IMMUTABLE_REF`.

Additional kinds require an adapter with immutable identity and access semantics.

### 5.3 Catalog state

Catalog membership is independent from source lifecycle/validity:

`CANDIDATE | PUBLISHED | WITHDRAWN | TOMBSTONED`

A catalog transition MUST NOT rewrite source artifact lifecycle or validity.

### 5.4 PublicationPolicy

Policy defines:

- allowed subject kinds/types;
- minimum source validity when applicable;
- required exact hashes;
- allowed publication scopes;
- authority/approval requirements;
- sensitive-data restrictions;
- metadata requirements;
- withdrawal behavior;
- external-reference eligibility.

Domain-specific payload validity remains owned by the producer/domain.

### 5.5 CatalogQuery / CatalogQueryResult

Query SHOULD support:

- tenant/workspace/project scope;
- subject type/schema;
- tags/classification;
- producer;
- time/revision filters;
- content/provenance hashes;
- optional full-text/semantic query delegated to a qualified adapter;
- pagination and stable ordering.

Result MUST return exact subject identity and catalog-entry identity.

A result is a **candidate discovery record**, not evidence admission.

## 6. Publication and query flow

~~~text
governed artifact/revision
        ↓
publication proposal
        ↓
authority + eligibility
        ↓
freeze exact identity
        ↓
metadata validation
        ↓
PUBLISHED CatalogEntry
        ↓
index
        ↓
authorized query
        ↓
candidate results
        ↓
consumer-specific interpretation
~~~

## 7. Scope and tenancy

Initial visibility scopes:

- `PROJECT`;
- `WORKSPACE`;
- `TENANT`.

Cross-tenant/global publication is deferred.

Query MUST enforce caller access before metadata or subject locator disclosure. Metadata itself may be sensitive.

## 8. Identity and immutability

For `GWF_REVISION`: bind `revision_id + content_hash`.

For `GWF_OBJECT_REF`: bind `ref_id + sha256 + size`.

For `EXTERNAL_IMMUTABLE_REF`: require canonical locator, exact snapshot/version, digest when available, and retrieval provenance.

A PUBLISHED entry never silently floats when source gets a new revision. New revision requires a new entry or explicit supersession publication.

## 9. Provenance and relations

Catalog is primarily an index over existing provenance from TraceLinks, producer run/evidence, supersession, object refs and external acquisition records.

Generic catalog relations may include:

- `CATALOGS`;
- `PUBLISHED_FROM`;
- `SUPERSEDES_ENTRY`;
- `WITHDRAWS_ENTRY`;
- `MIRRORS_EXACT`.

Research-specific relations such as `CORROBORATES`, `CONTRADICTS`, `BOUNDS` or `REPLICATES` belong inside G2E/domain payloads, not GWF catalog core.

## 10. Search backend boundary

GWF defines stable catalog/query semantics independent of search product.

Optional adapters may use relational metadata, SQLite/PostgreSQL FTS, vector/embedding search or external search.

Search backend MAY rank candidates but MUST NOT:

- mutate catalog truth;
- grant access;
- determine domain applicability;
- omit exact identity;
- become source of publication state.

Semantic/vector search must report backend/version, index revision/snapshot, query execution ID and score interpretation when defined.

## 11. Security and privacy

Publication fails closed when authority, subject identity, scope, classification/redaction or eligibility is invalid.

Catalog metadata MUST NOT persist reusable credentials, provider tokens or raw sensitive snippets merely for search convenience.

Withdrawal does not delete audit/provenance history.

## 12. Source validity and catalog visibility

Catalog membership and artifact validity are separate.

If a published source later becomes `STALE/DIRTY/FAILED/SUPERSEDED`:

- entry remains historically attributable;
- PublicationPolicy controls default visibility;
- current known source validity is surfaced;
- entry never silently repoints.

## 13. Failure classes

Future implementation should distinguish at least:

- `SUBJECT_NOT_FOUND`;
- `SUBJECT_HASH_MISMATCH`;
- `SUBJECT_NOT_ELIGIBLE`;
- `PUBLICATION_SCOPE_DENIED`;
- `METADATA_SCHEMA_INVALID`;
- `CATALOG_ENTRY_STALE_SOURCE`;
- `INDEX_BACKEND_UNAVAILABLE`;
- `INDEX_REVISION_MISMATCH`;
- `QUERY_SCOPE_DENIED`;
- `SUBJECT_RESOLUTION_FAILED`;
- `WITHDRAWAL_NOT_AUTHORIZED`.

Search/index failure is not equivalent to “no matching artifacts exist”.

## 14. Later implementation phases

This package does not authorize implementation.

### GAC-P0 — Contract qualification

CatalogEntry, PublicationPolicy, CatalogQuery/Result, identity/access fixtures; zero search backend.

### GAC-P1 — Metadata catalog over existing KnowledgeKernel

Publish/withdraw exact GWF revisions; tenant/workspace/project authorization; deterministic metadata query; audit; no FTS/vector.

### GAC-P2 — Object/external immutable refs

ObjectRef subjects, Reference Acquisition bridge, subject resolution.

### GAC-P3 — Optional search adapters

FTS/vector/external search with query/index provenance.

### GAC-P4 — Cross-project pilot

Multiple projects in one workspace/tenant; publish/query/withdraw/supersede; Documentation Governance integration fixture; G2E consumer fixture after G2E semantics freeze.

## 15. Explicit non-goals

- research evidence applicability;
- synthesis/convergence;
- ClaimSignature;
- G2E EvidenceCapsule semantics;
- study-quality scoring;
- meta-analysis;
- automatic cross-study conclusions;
- documentation registry/validator;
- universal knowledge graph;
- crawler;
- embedding model;
- UI;
- runtime/code implementation in this pack.

## 16. References and dependencies

### Architectural dependencies

- [GWF README](../README.md)
- [Documentation Integrity & Governance](DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md)
- [Reference Acquisition Specification](V0.8.6_REFERENCE_ACQUISITION_SPEC.md)
- [Agent Interoperability Foundation](V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)

### Existing implementation primitives inspected

- `src/gwr/knowledge.py`
- `src/gwr/object_store.py`
- `src/gwr/governance.py`
- `src/gwr/db.py`
- `src/gwr/runtime.py`

### Documentation Governance frontier

The active Documentation Governance P0 implementation explicitly leaves document registry, dependency graph runtime, lifecycle/validity persistence and stale propagation for later phases. GAC must integrate with those stabilized APIs later rather than preempt them.
