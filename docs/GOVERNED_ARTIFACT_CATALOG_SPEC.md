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

### 3.1 Shared Library terminology

For integration purposes, **Shared Library** is a consumer-facing capability built on the Governed Artifact Catalog; it is not a second canonical store.

- GWF GAC owns governed publication, scope, discovery, and exact artifact identity.
- G2E may expose an **Evidence Library** semantic view over GAC results and may publish G2E artifacts through GWF.
- Reference Acquisition may query GAC as an internal governed discovery channel during research.
- Canonical payloads remain in existing GWF Artifact/Revision/ObjectRef or accepted external immutable-reference systems.

Therefore `Library`, `Catalog`, and `G2E Evidence Library` are related but not interchangeable authority concepts.

### 3.2 GWF owns

- durable catalog membership;
- tenant/workspace/project scope;
- publication/withdrawal authority;
- immutable subject binding;
- catalog metadata/versioning;
- query/index behavior;
- access checks;
- audit/provenance of publication actions;
- optional search-backend adapter contracts.

### 3.3 GWF does not own

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

The direction also works from GAC to research: Reference Acquisition MAY query GAC as an **internal governed discovery channel**. Such query results remain candidate references. The research workflow must preserve the CatalogQueryExecution identity, authoritative catalog snapshot, exact CatalogEntry identities observed, and the exact subject identities selected for further interpretation.

Retrieval alone does not publish an item. Catalog discovery does not convert a candidate into empirical proof or automatically admit it into a study.

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
- `publication_policy_revision`;
- `publication_policy_hash`;
- `publication_identity_key`;
- `eligibility_snapshot`;
- `extension_metadata` keyed by namespace + schema/version;
- `published_by`;
- `published_at`;
- `withdrawn_at`;
- `withdrawal_reason`.

CatalogEntry is an index/publication record, not a payload copy.

Publication identity MUST be idempotent for the tuple:

`subject_kind + exact subject identity/hash + publication_scope + publication_policy_hash`.

Publishing the same tuple again returns/reuses the same active logical publication identity rather than creating ambiguous duplicate active entries. A materially different scope/policy/subject revision is a different publication identity.

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

Allowed v0.x transitions:

- `CANDIDATE → PUBLISHED | WITHDRAWN`;
- `PUBLISHED → WITHDRAWN | TOMBSTONED`;
- `WITHDRAWN → PUBLISHED` only by a new authorized publication action that records a new publication event/revision while preserving withdrawal history;
- `TOMBSTONED` is terminal for that CatalogEntry identity.

Withdrawal/tombstone require explicit authority and audit. History is never deleted.

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

Every publication MUST bind the exact PublicationPolicy revision/hash and record an eligibility snapshot sufficient to reconstruct why publication was allowed, including source validity/classification observed at publication time where applicable.

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

Query execution and query content are separate.

`CatalogQueryExecution` MUST report at least:

- execution status: `SUCCEEDED | BACKEND_UNAVAILABLE | PARTIAL | FAILED`;
- authoritative catalog snapshot/revision;
- derived index backend/version/revision when used;
- query ID and timing;
- completeness declaration/reason.

`CatalogQueryResultSet` contains zero or more candidate records only when execution semantics allow interpretation. A backend/index failure MUST NOT be encoded as a valid empty result set.

Each candidate MUST return exact subject identity and catalog-entry identity.

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

Effective read authorization is the intersection of:

1. catalog-entry visibility/scope; and
2. the underlying source/object/external-reference read permission.

Catalog publication MUST NOT broaden source access. Query MUST enforce effective access before metadata, relevance information, provenance details or subject locator disclosure. Metadata itself may be sensitive.

## 8. Identity and immutability

For `GWF_REVISION`: bind `revision_id + content_hash`.

For `GWF_OBJECT_REF`: bind `ref_id + sha256 + size`.

For `EXTERNAL_IMMUTABLE_REF`: require canonical locator, retrieval provenance, and either:

- a verified content digest; or
- a provider-issued immutable snapshot/version identity explicitly accepted by the bound PublicationPolicy.

If neither exists, publication MUST fail; a mutable URL/string is not an immutable subject identity.

A PUBLISHED entry never silently floats when source gets a new revision. New revision requires a new entry or explicit supersession publication.

## 9. Provenance and relations

Catalog is primarily an index over existing provenance from TraceLinks, producer run/evidence, supersession, object refs and external acquisition records.

Core searchable metadata is governed by the catalog schema. Consumer/domain extensions MUST be namespaced (for example `g2e.*`, `software.*`) and bind an extension schema/version owner. Extension metadata may be indexed but does not acquire core semantic meaning.

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

The authoritative catalog record set is the rebuild source for every derived search index. Search indexes are projections, never system of record.

Every derived index MUST expose backend/version, index revision/snapshot, source catalog snapshot/revision and rebuild status. Stale/mismatched index state must be visible and may cause `PARTIAL` or fail-closed query execution according to query policy.

Semantic/vector search must additionally report query execution ID and score interpretation when defined.

## 11. Security and privacy

Publication fails closed when authority, subject identity, scope, classification/redaction or eligibility is invalid.

Catalog metadata MUST NOT persist reusable credentials, provider tokens or raw sensitive snippets merely for search convenience.

Withdrawal does not delete audit/provenance history.

## 12. Source state and catalog visibility

Catalog membership is separate from source lifecycle, validity, execution status, or domain-specific state.

GAC MUST NOT collapse different source-state namespaces into one catalog enum. Instead it surfaces an attributable source-state observation with at least:

- `source_state_namespace` (for example `GWF_REVISION_VALIDITY`, `DOCUMENT_VALIDITY`, `DOCUMENT_LIFECYCLE`, or a registered domain namespace);
- `source_state_value`;
- exact source revision/hash observed;
- observation time and provenance.

For Documentation Governance, lifecycle (for example `ACTIVE | SUPERSEDED`) remains distinct from validity (for example `VALID | STALE | BLOCKED`). For generic GWF revisions, existing revision-validity semantics remain owned by the KnowledgeKernel.

When a published source later changes state:

- entry remains historically attributable;
- PublicationPolicy controls default visibility;
- current known typed source state is surfaced;
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
- `WITHDRAWAL_NOT_AUTHORIZED`;
- `DUPLICATE_PUBLICATION_CONFLICT`;
- `SOURCE_ACCESS_DENIED`;
- `EXTERNAL_IDENTITY_NOT_IMMUTABLE`;
- `QUERY_PARTIAL_INDEX`.

Search/index failure is not equivalent to “no matching artifacts exist”.

## 14. Later implementation phases

This package does not authorize implementation.

### Implementation dependency gate

GAC-P0 and GAC-P1 MUST NOT begin until **DG-W4 PASS** (or a later explicitly documented equivalent compatibility gate) establishes stable document identity/validity/relation integration semantics. This gate prevents GAC from freezing temporary document assumptions into a competing registry.

### GAC-P0 — Contract qualification

CatalogEntry, PublicationPolicy, CatalogQuery/Result, identity/access fixtures; zero search backend.

### GAC-P1 — Metadata catalog over existing KnowledgeKernel

Publish/withdraw exact GWF revisions; tenant/workspace/project authorization; deterministic metadata query; audit; no FTS/vector.

### GAC-P2A — ObjectRef subjects

Add exact GWF ObjectRef publication/resolution after GAC-P1. This item has no Reference Acquisition dependency.

### GAC-P2B — External immutable-reference bridge

Add `EXTERNAL_IMMUTABLE_REF` publication/resolution only after the Reference Acquisition registry/identity contract is qualified. Preserve external retrieval provenance rather than duplicating it in GAC.

### GAC-P3 — Optional search adapters

FTS/vector/external search with query/index provenance. **GAC-P3 is not required for minimum Shared Library readiness**; deterministic metadata query from GAC-P1 is the minimum governed discovery path.

### GAC-P4A — Generic cross-project pilot

Multiple GWF projects in one workspace/tenant; publish/query/withdraw/supersede; Documentation Governance integration fixture. This pilot does not depend on G2E semantic freeze.

### GAC-P4B — G2E consumer fixture

After the G2E Evidence Library Adapter/semantic contract is frozen, verify that G2E can publish/query governed artifacts through GAC without transferring ClaimSignature, applicability, independence, reuse, or synthesis semantics into GWF. GAC-P4B is a consumer-integration fixture, not a prerequisite for GAC core readiness.

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

DG-P0 has formal-close evidence on implementation head `ef322ff0618b83fbfaef40b096cb43f5193d8db0` with exact-head workflow `35560831581` PASS. DG-P0 still intentionally leaves document registry, dependency graph runtime, lifecycle/validity persistence and stale propagation for later phases.

Accordingly, the exact GAC implementation gate is **DG-W4 PASS**, not merely DG-P0 completion. GAC must integrate with those stabilized APIs rather than preempt them.
