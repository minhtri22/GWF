# GWF Governed Artifact Catalog — Integration Boundaries

## 1. Purpose

Freeze ownership boundaries before implementation so the future GAC agent does not duplicate GWF core, Documentation Governance, Reference Acquisition, or G2E.

## 2. Ownership matrix

| Concern | Existing GWF core | Documentation Governance | Reference Acquisition | GAC | G2E/consumer |
| --- | --- | --- | --- | --- | --- |
| Artifact logical identity/revisions | OWNS | consumes/specializes docs | references | indexes exact identity | consumes |
| Blob/object identity | OWNS | consumes | may resolve external | indexes exact identity | consumes |
| Artifact validity/impact | OWNS generic | OWNS document semantics | no | surfaces only | interprets own payload |
| Document QA/findings | no | OWNS | no | no | no |
| External retrieval provenance | no | references | OWNS | indexes eligible snapshot | consumes |
| Catalog membership/publication | no | eligibility input | eligibility input | OWNS | requests/consumes |
| Cross-project discovery | limited | no | retrieval only | OWNS | consumes |
| Search backend/index | no | no | provider retrieval | OWNS adapter boundary | no |
| Claim applicability/reuse | no | no | no | no | G2E OWNS |
| Synthesis/convergence | no | no | no | no | G2E OWNS |
| Authority/audit | OWNS primitives | specializes | specializes | uses | declares semantic needs |

## 3. No-duplication rules

### B-01 — No parallel artifact store

GAC refers to exact GWF revisions/object refs. It does not create a second canonical payload store.

### B-02 — No parallel document registry

DocumentRecord/DocumentRevision/DocumentFinding/DocumentQARecord remain Documentation Governance concepts. GAC receives only an eligible exact document revision reference.

### B-03 — No parallel external crawler

Reference Acquisition owns retrieval/session/canonical-source provenance. GAC indexes only eligible immutable retrieval outputs.

### B-04 — No research semantics

GAC stores generic/domain metadata and exact payload type/schema. It does not interpret corroboration, contradiction, applicability or convergence.

### B-05 — Search is advisory discovery

Ranking/search score returns candidates. It never establishes evidence validity, artifact validity or domain truth.

### B-06 — No silent current-pointer binding

Formal catalog membership binds exact subject identity. Convenience aliases may resolve current state but must return the exact resolved identity.

## 4. Documentation Governance integration

Expected future handshake:

~~~text
DocumentRevision
   ↓
Document QA / validity
   ↓
publication eligibility
   ↓
GAC publish exact revision
~~~

If a document later becomes stale/superseded:

~~~text
document state change
   ↓
GAC observes validity
   ↓
PublicationPolicy applies visibility
   ↓
never silently repoint
~~~

GAC implementation must wait for stable document identity/validity APIs rather than duplicating temporary assumptions.

## 5. Reference Acquisition integration

Expected handshake:

~~~text
retrieval session
  ↓
canonical source + inspected snapshot
  ↓
immutable-reference eligibility
  ↓
GAC candidate/publish
~~~

A mutable URL string alone is insufficient immutable identity when the source can change.

## 6. G2E integration boundary

Future G2E may publish an `EvidenceCapsule` or `SynthesisResult` as a normal governed GWF artifact revision and then request catalog publication.

GAC sees:

- payload type/schema;
- exact revision/hash;
- producer/project;
- publication/search metadata.

GAC does **not** evaluate:

- ClaimSignature compatibility;
- applicability;
- independence clusters;
- ReuseDecision;
- SynthesisContract;
- convergence verdict.

Those belong to G2E.

## 7. Agent implementation boundary

Current package is documentation only.

Future implementation should begin only after:

1. Documentation Governance active work has completed or established stable integration APIs.
2. this pack is reconciled with the then-current GWF baseline.
3. actual registry/validity/API conflicts are recorded before code.
4. code work is explicitly authorized.

No file in `src/`, `tests/`, `.github/`, migrations, DomainSDK, or shared implementation plans is part of this pack.

## 8. References

- [GAC Specification](GOVERNED_ARTIFACT_CATALOG_SPEC.md)
- [Documentation Integrity & Governance](DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md)
- [Reference Acquisition Specification](V0.8.6_REFERENCE_ACQUISITION_SPEC.md)
- [Agent Interoperability Foundation](V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)
