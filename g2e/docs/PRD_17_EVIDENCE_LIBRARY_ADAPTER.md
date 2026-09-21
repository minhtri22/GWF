# PRD-17 — Evidence Library Adapter

## Purpose

Define G2E's provider-neutral interface for publishing and discovering EvidenceCapsules/SynthesisResults while keeping physical catalog/storage ownership outside G2E core.

Default backend: GWF Governed Artifact Catalog (GAC).

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

Default preference is GWF GAC only when the GAC backend is implemented and qualified. If it is unavailable/unqualified, G2E may explicitly select a qualified standalone backend. There is no silent fallback.

If no qualified backend satisfies the Proof/Synthesis requirements, fail closed with `LIBRARY_UNAVAILABLE`.

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

- sealed/verified source Goal Result Package or SynthesisResult;
- capsule hash tied to source seal;
- terminal source Claim resolution;
- complete configured provenance;
- security/redaction checks;
- publication metadata namespace/schema.

Negative results are not excluded because they are FAIL/UNRESOLVED.

Backend PublicationPolicy may impose stricter requirements.

## 8. Retrieval is not admission

```text
query result
   ≠ EvidenceAdmission
   ≠ ReuseDecision
   ≠ Claim PASS
```

Retrieved capsule begins as a candidate prior-evidence object. PRD-15 governs applicability/reuse; PRD-04 governs admission.

## 9. Library snapshot semantics

A synthesis or reproducible reuse decision may require a frozen library snapshot.

Adapter must expose a stable snapshot/manifest identity sufficient to replay:

- catalog state in scope;
- query filters;
- exact returned publication/subject IDs;
- derived search-index identity if used.

## 10. Security

Adapter must not leak metadata for inaccessible subjects.

Effective access is backend catalog visibility AND subject/source permission.

No provider tokens, credentials or hidden source snippets are persisted in G2E query records.

## 11. Failure classes

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

## Dependencies

- **HARD:** [PRD-15 Evidence Reuse & Applicability](PRD_15_EVIDENCE_REUSE_APPLICABILITY.md)
- **INTEGRATION:** [PRD-08 GWF Adapter](PRD_08_GWF_ADAPTER.md), [PRD-11 Standalone Runtime](PRD_11_STANDALONE_RUNTIME.md)
- **CROSS_CUTTING:** [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)

## References

- [GWF GAC Specification](https://github.com/minhtri22/GWF/blob/docs/governed-artifact-catalog-pack/docs/GOVERNED_ARTIFACT_CATALOG_SPEC.md)
- [GWF GAC Integration Boundaries](https://github.com/minhtri22/GWF/blob/docs/governed-artifact-catalog-pack/docs/GOVERNED_ARTIFACT_CATALOG_INTEGRATION_BOUNDARIES.md)
- [GWF GAC QA](https://github.com/minhtri22/GWF/blob/docs/governed-artifact-catalog-pack/docs/GOVERNED_ARTIFACT_CATALOG_QA.md)
