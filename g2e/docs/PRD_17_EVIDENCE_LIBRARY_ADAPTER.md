# PRD-17 — Evidence Library Adapter

## Purpose

Define G2E's provider-neutral interface for publishing and discovering EvidenceCapsules/SynthesisResults while keeping physical catalog/storage ownership outside G2E core.

Default infrastructure preference: the GWF **Shared Library** capability backed by Governed Artifact Catalog (GAC), when the requested G2E consumer capability is implemented and qualified.

“G2E Evidence Library” is the G2E semantic view over published/queryable governed results. It is not a second physical database/store.

Standalone backend: minimal local catalog/index preserving the same logical identities.

## 1. Boundary

```text
G2E semantic objects
EvidenceCapsule / SynthesisResult
          ↓
Evidence Library Adapter
          ↓
   ┌───────────────┬────────────────┐
   ▼               ▼
GWF GAC          Standalone
(default)        local catalog
```

The adapter does not decide applicability, admission, synthesis or Claim resolution.

## 2. LibraryCapabilityManifest

Before selecting a backend, runtime MUST resolve a `LibraryCapabilityManifest` containing:

- backend ID/type;
- adapter/runtime version;
- supported schema versions;
- publish/withdraw/query/snapshot/provenance capabilities;
- optional search capabilities;
- qualification status/evidence reference;
- availability status;
- security/access model.

Backend qualification is capability-specific and MUST bind exact GWF gate/evidence identities when GWF is selected.

Minimum GWF capability levels:

- `GAC_METADATA_CORE`: GAC-P0 + GAC-P1 PASS — exact governed revision publication/query contract.
- `GAC_OBJECTREF`: additionally GAC-P2A PASS when ObjectRef subjects are required.
- `GAC_SHARED_LIBRARY_CROSS_PROJECT`: DG-GAC-W5 PASS for the minimum governed cross-project Shared Library substrate.
- `GAC_G2E_CONSUMER`: GAC-P4B PASS plus the G2E adapter qualification for the exact PRD-17 contract. GAC-P4B may qualify the GWF consumer contract against the frozen PRD-17 fixture and does not require completed G2E P4L runtime beforehand.
- `GAC_OPTIONAL_SEARCH`: GAC-P3 PASS only when optional FTS/vector/external search is actually required.
- `RA_GAC_CURATED_DISCOVERY`: RA-P1C PASS when PRD-13 research-side GWF_CATALOG curation is required.
- `RA_GAC_RESEARCH_WORKFLOW`: RA-GAC-W6 PASS when the full research workflow bridge is required.

GAC-P0/P1 cannot open before DG-W4 PASS under the reconciled GWF roadmap.

Default preference is GWF only when the **requested** capability level is implemented/qualified. Otherwise G2E may explicitly select a qualified standalone backend where the Proof/Synthesis contract permits it. There is no silent fallback.

If no qualified backend satisfies the requested operation, fail closed with `LIBRARY_UNAVAILABLE` or `BACKEND_CAPABILITY_UNSUPPORTED`.

## 3. Required operations

Provider-neutral logical interface:

- `publish_capsule(capsule_ref, publication_metadata)`;
- `withdraw_publication(publication_ref, reason)`;
- `query_candidates(query_contract)`;
- `resolve_subject(publication_ref)`;
- `get_catalog_snapshot()`;
- `get_provenance_ancestors(subject_ref)`;
- `verify_subject_integrity(subject_ref)`.

Optional:

- semantic/full-text search if backend capability is qualified.

## 4. Query contract

Every query MUST record:

- query ID;
- backend/adapter identity/version;
- exact catalog/library snapshot;
- filter/query payload hash;
- access scope;
- execution status;
- result completeness;
- result publication IDs + exact subject hashes;
- ranking backend/version when applicable.

Library/backend failure cannot be represented as a valid empty result set.

## 5. GWF default mapping

When using GWF:

- EvidenceCapsule/SynthesisResult is stored as a normal governed GWF artifact/revision;
- G2E extension/search metadata uses the namespaced `g2e.*` schema family and records its schema/version owner;
- publication is a GAC CatalogEntry pointing to exact revision/hash;
- GWF owns tenant/workspace/project access, publication state, audit and search index;
- G2E receives exact subject/publication/query identities;
- G2E then performs ApplicabilityAssessment/ReuseDisposition.

The adapter MUST respect GAC rule that catalog visibility never broadens source access.

## 6. Standalone mapping

Standalone may use filesystem/SQLite for:

- exact capsule manifest;
- publication state;
- metadata index;
- provenance refs;
- deterministic query.

Canonical EvidenceCapsule/SynthesisResult IDs/hashes MUST remain identical when migrated to GWF. Backend publication IDs are mappings only.

## 7. Publication policy

G2E requests publication only for eligible immutable semantic outputs.

Default capsule publication requires:

- sealed/verified source ClaimResultPackage, Goal Result Package, or sealed SynthesisResult source package;
- exact source package type and seal identity;
- capsule hash tied to source seal;
- terminal source Claim resolution;
- complete configured provenance;
- security/redaction checks;
- publication metadata namespace/schema.

Negative results are not excluded because they are FAIL/UNRESOLVED.

Backend PublicationPolicy may impose stricter requirements.

## 8. Direct G2E discovery vs research curation

PRD-17 direct discovery is the route for EvidenceCapsule reuse/applicability/synthesis.

PRD-13 uses the GWF Reference Acquisition `GWF_CATALOG` channel for research prior-art/novelty curation. It preserves CatalogQueryExecution/snapshot/CatalogEntry provenance before research disposition.

Neither route owns the other. Both use the same GAC publication/query substrate when GWF-backed.

If the same exact subject is observed through both routes, canonical subject identity is shared while observation/query provenance remains separate.

## 9. Retrieval is not admission

```text
query result
   ≠ EvidenceAdmission
   ≠ ReuseDecision
   ≠ Claim PASS
```

Retrieved capsule begins as a candidate prior-evidence object. PRD-15 governs applicability/reuse; PRD-04 governs admission.

## 10. Library snapshot semantics

A synthesis or reproducible reuse decision may require a frozen library snapshot.

Adapter must expose a stable snapshot/manifest identity sufficient to replay:

- catalog state in scope;
- query filters;
- exact returned publication/subject IDs;
- derived search-index identity if used.

## 11. Security

Adapter must not leak metadata for inaccessible subjects.

Effective access is backend catalog visibility AND subject/source permission.

No provider tokens, credentials or hidden source snippets are persisted in G2E query records.

## 12. Failure classes

At minimum normalize:

- `LIBRARY_UNAVAILABLE`;
- `QUERY_FAILED`;
- `QUERY_PARTIAL`;
- `SUBJECT_NOT_FOUND`;
- `SUBJECT_INTEGRITY_FAILED`;
- `ACCESS_DENIED`;
- `SNAPSHOT_MISMATCH`;
- `PUBLICATION_REJECTED`;
- `BACKEND_CAPABILITY_UNSUPPORTED`.

These are adapter/execution conditions, not G2E scientific verdicts.

## Acceptance criteria

1. Core G2E schemas do not depend on GWF database/search implementation.
2. GWF is default backend without becoming semantic authority for reuse/synthesis.
3. Standalone and GWF preserve canonical capsule/result IDs/hashes.
4. Query failure cannot masquerade as zero results.
5. Query result is never direct evidence admission.
6. Negative-result capsules may be published.
7. Access rules fail closed before metadata leakage.
8. Synthesis can freeze/replay exact library snapshot/query identity.
9. Unimplemented/unqualified GWF GAC is never treated as available; backend selection is capability-gated and explicit.
10. GWF capability qualification binds exact reconciled gate evidence, not a generic “GAC available” boolean.
11. Direct PRD-17 discovery and PRD-13 research curation share subject identity but preserve separate observation provenance.
12. ClaimResultPackage is a valid sealed source for capsule publication.

## Dependencies

- **HARD:** [PRD-15 Evidence Reuse & Applicability](PRD_15_EVIDENCE_REUSE_APPLICABILITY.md)
- **INTEGRATION:** [PRD-08 GWF Adapter](PRD_08_GWF_ADAPTER.md), [PRD-11 Standalone Runtime](PRD_11_STANDALONE_RUNTIME.md)
- **CROSS_CUTTING:** [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)

## References

- [GWF Library Integration Mapping](GWF_LIBRARY_INTEGRATION_MAPPING.md)
- [Reconciled GWF GAC Specification](https://github.com/minhtri22/GWF/blob/be7d606c64a97d9525d1f72d744fe5b7a336ff0c/docs/GOVERNED_ARTIFACT_CATALOG_SPEC.md)
- [Reconciled GWF GAC Integration Boundaries](https://github.com/minhtri22/GWF/blob/be7d606c64a97d9525d1f72d744fe5b7a336ff0c/docs/GOVERNED_ARTIFACT_CATALOG_INTEGRATION_BOUNDARIES.md)
- [Reconciled GWF Reference Acquisition](https://github.com/minhtri22/GWF/blob/be7d606c64a97d9525d1f72d744fe5b7a336ff0c/docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md)
- [Reconciled 7-Wave Plan](https://github.com/minhtri22/GWF/blob/be7d606c64a97d9525d1f72d744fe5b7a336ff0c/docs/IMPLEMENTATION_7_WAVES_PLAN.md)
- [GWF Reconciliation QA](https://github.com/minhtri22/GWF/blob/be7d606c64a97d9525d1f72d744fe5b7a336ff0c/docs/DOCUMENT_QA_GAC_7_WAVES_RECONCILIATION.md)
