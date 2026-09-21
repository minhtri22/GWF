# G2E ↔ GWF Shared Library Integration Mapping

## 1. Purpose

Freeze the integration contract between G2E Evidence Library semantics and the reconciled GWF Shared Library / Governed Artifact Catalog (GAC) documentation.

This document does not implement either system.

## 2. Exact GWF authority baseline

Current integration authority:

- GWF reconciliation commit: be7d606c64a97d9525d1f72d744fe5b7a336ff0c
- GWF reconciliation QA: PASS / OPEN=0
- revised 7-wave plan blob: 229decfb067ead7ef38d51012b06abf69cc12fc0
- GAC specification blob: 831a4f9260ff6a1f74d531d9d24a91cdb6feff7e
- GAC integration-boundary blob: 2fef77627127bf58c6376202f96de681d5b3050a
- Reference Acquisition specification blob: 110dae0b492b56492c52eec2dfc64a8d2070d966
- reconciliation QA blob: 624bc36f9012af92711f80b2ee1d6157b358f570

The earlier GAC packing head 194c66c... remains historical design lineage, not current cross-system integration authority.

## 3. Ownership

~~~text
Canonical payload
Artifact / Revision / ObjectRef
             │
             ▼
GWF Governed Artifact Catalog
publication / access / discovery
             │
      ┌──────┴───────────────┐
      ▼                      ▼
Reference Acquisition      G2E Evidence Library
research-side curation     semantic consumer/view
prior art / novelty        applicability / reuse /
                           synthesis / convergence
~~~

### GWF/GAC owns

- catalog membership/publication/withdrawal;
- tenant/workspace/project scope and access intersection;
- exact CatalogEntry identity;
- CatalogQueryExecution and catalog snapshot semantics;
- deterministic metadata query;
- cross-project governed discovery;
- optional search-adapter boundary.

### G2E owns

- EvidenceCapsule and ClaimSignature;
- ApplicabilityPolicy / ApplicabilityAssessment;
- ReuseDisposition;
- Reuse ProofObligation;
- independence/provenance clustering;
- SynthesisContract/SynthesisUniverse;
- ConvergenceClassification;
- EvidenceAdmission/Claim/Goal semantics.

### Reference Acquisition owns

- external retrieval/session/source provenance;
- research-side reference registry and curation;
- prior-art/novelty interpretation;
- the governed GWF_CATALOG research discovery channel when enabled.

No layer may silently acquire another layer's authority.

## 4. Terminology mapping

Canonical G2E names remain authoritative for G2E schemas.

| GWF reconciliation prose | Canonical G2E meaning |
| --- | --- |
| Shared Library | Consumer-facing capability backed by GAC; not a second store |
| G2E Evidence Library | G2E semantic consumer/view over governed library results |
| ReuseDecision | Generic prose reference to G2E ReuseDisposition; no separate G2E schema |
| SynthesisVerdict | Non-normative shorthand only; G2E uses ConvergenceClassification plus normal Adjudication/Claim/Goal verdicts |
| Catalog result | Candidate discovery record only; never automatic EvidenceAdmission |

## 5. Discovery routing

### Route A — Direct G2E evidence reuse/synthesis

Use when the user/Goal needs:

- prior EvidenceCapsules;
- ApplicabilityAssessment;
- QUALIFIED_REUSE / REPLICATION_REQUIRED;
- synthesis/convergence inputs.

~~~text
G2E PRD-17 query
      ↓
GAC CatalogQueryExecution
      ↓
exact catalog snapshot + CatalogEntry IDs
      ↓
exact EvidenceCapsule subjects
      ↓
PRD-15 applicability/reuse
      ↓
PRD-04 EvidenceAdmission
~~~

### Route B — Research prior-art / novelty curation

Use when the research workflow needs:

- literature/prior art;
- novelty collision analysis;
- method/source curation;
- source coverage.

~~~text
G2E PRD-13 / GWF Reference Acquisition
      ↓
reference_query_plan with GWF_CATALOG channel
      ↓
GAC CatalogQueryExecution
      ↓
reference retrieval log + registry
      ↓
prior-art / novelty interpretation
~~~

RA retention is not G2E reuse admission.

### Same subject through both routes

One exact subject revision/hash is one canonical subject identity.

Each query/retrieval remains a distinct observation identity.

~~~text
same subject
  ├── direct PRD-17 observation
  └── RA GWF_CATALOG observation
          ↓
one candidate subject
multiple provenance observations
never double-counted
~~~

## 6. Capability/readiness mapping

G2E MUST resolve exact evidence for every requested capability.

| G2E requested capability | Minimum GWF evidence/gate |
| --- | --- |
| Exact revision publication/query contract | GAC-P0 + GAC-P1 PASS; their DG-W4 prerequisite lineage resolvable |
| ObjectRef subject publication | GAC-P2A PASS |
| Minimum cross-project Shared Library | DG-GAC-W5 PASS |
| G2E-specific GAC consumer path | GAC-P4B PASS + G2E PRD-17 adapter qualification |
| Optional FTS/vector/external search | GAC-P3 PASS; never required for core metadata Library |
| Research-curated GAC discovery | RA-P1C PASS |
| Full research workflow Shared Library bridge | RA-GAC-W6 PASS |
| External immutable-reference publication | GAC-P2B PASS |

GAC-P0/P1 may not be treated as open before DG-W4 PASS.

A logical phase name without exact evidence identity is insufficient for LibraryCapabilityManifest.

## 7. LibraryCapabilityManifest rules

For a GWF-backed adapter, manifest MUST include:

- requested capability IDs;
- exact GWF commit/revision;
- exact gate/handoff evidence refs;
- GAC schema/adapter/runtime version;
- supported subject kinds;
- supported query modes;
- cross-project support;
- Reference Acquisition bridge support when requested;
- optional search support when requested;
- availability and qualification status;
- security/access model.

Capability is qualified only for the operations demonstrated by its evidence.

No silent fallback.

## 8. Failure semantics

These must remain distinguishable:

~~~text
query SUCCEEDED + zero candidates
≠
query PARTIAL
≠
backend unavailable
≠
access denied
≠
snapshot mismatch
~~~

A partial/unavailable GAC query cannot become "Library contains no relevant result".

Similarly, an unavailable RA-GAC bridge cannot be replaced silently by a direct PRD-17 query when the frozen research query plan required Reference Acquisition curation.

## 9. Metadata mapping

G2E-owned catalog metadata uses namespaced g2e.* extensions with explicit schema/version owner.

Examples:

- g2e.subject_type;
- g2e.capsule_schema_version;
- g2e.claim_signature_family;
- g2e.source_package_type;
- g2e.convergence_result_type.

GAC may index these fields but MUST NOT reinterpret their scientific meaning.

## 10. Implementation ordering

G2E core is not blocked by GWF GAC runtime implementation.

~~~text
G2E P0/P0.1/P0.2/P0.3 docs
          ↓
G2E P1 schemas
          ↓
G2E P2 deterministic core
          ↓
G2E P3 standalone runtime + local Library
~~~

GWF-backed Library integration is conditional:

~~~text
requested GWF capability evidence PASS
          +
G2E PRD-17 implementation ready
          ↓
G2E P4L GWF Shared Library Integration
~~~

Therefore GWF's current next planned item (DG-P1) and G2E's P1 schema work do not conflict; they are independent workstreams until P4L integration.

## 11. References

- [G2E PRD-13 Reference Acquisition](PRD_13_REFERENCE_ACQUISITION.md)
- [G2E PRD-15 Evidence Reuse & Applicability](PRD_15_EVIDENCE_REUSE_APPLICABILITY.md)
- [G2E PRD-16 Synthesis & Convergence](PRD_16_SYNTHESIS_CONVERGENCE.md)
- [G2E PRD-17 Evidence Library Adapter](PRD_17_EVIDENCE_LIBRARY_ADAPTER.md)
- [GWF reconciled GAC specification](https://github.com/minhtri22/GWF/blob/be7d606c64a97d9525d1f72d744fe5b7a336ff0c/docs/GOVERNED_ARTIFACT_CATALOG_SPEC.md)
- [GWF reconciled integration boundaries](https://github.com/minhtri22/GWF/blob/be7d606c64a97d9525d1f72d744fe5b7a336ff0c/docs/GOVERNED_ARTIFACT_CATALOG_INTEGRATION_BOUNDARIES.md)
- [GWF reconciled Reference Acquisition](https://github.com/minhtri22/GWF/blob/be7d606c64a97d9525d1f72d744fe5b7a336ff0c/docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md)
- [GWF revised 7-wave plan](https://github.com/minhtri22/GWF/blob/be7d606c64a97d9525d1f72d744fe5b7a336ff0c/docs/IMPLEMENTATION_7_WAVES_PLAN.md)
- [GWF reconciliation QA](https://github.com/minhtri22/GWF/blob/be7d606c64a97d9525d1f72d744fe5b7a336ff0c/docs/DOCUMENT_QA_GAC_7_WAVES_RECONCILIATION.md)
