# PRD-15 — Evidence Reuse & Applicability

## Purpose

Allow G2E to reuse prior governed results without treating textual similarity, prior PASS, or library retrieval as proof that a result applies to a new Claim.

This component owns the semantic layer between library discovery and the current Goal's Evidence Graph.

## 1. Core principle

```text
library candidate
      ↓
EvidenceCapsule
      ↓
ApplicabilityAssessment
      ↓
ReuseDisposition
      ↓
current Proof design/admission
```

A prior result NEVER directly sets a current Claim to PASS.

When prior evidence is allowed to satisfy a current requirement, G2E creates a frozen **Reuse ProofObligation**. That ProofObligation is evaluated under the same EvidenceAdmission, Adjudication, ClaimResolution and no-rescue rules as any other proof.

## 2. EvidenceCapsule

An `EvidenceCapsule` is an immutable, portable semantic summary of one governed prior result suitable for library publication/discovery.

It MUST bind:

- `capsule_id`, schema/version/hash;
- exact sealed source package type and seal/hash (`ClaimResultPackage`, `GoalResultPackage`, or sealed synthesis source package);
- source Goal/Claim/Proof IDs and revisions;
- source Claim resolution;
- source Adjudication/result references;
- exact EvidenceRecord/provenance references;
- `ClaimSignature`;
- environment/resource/model/data/artifact regime;
- assumptions and limitations;
- temporal/version regime;
- provenance ancestor references;
- independence metadata/cluster hints;
- source exposure classification;
- producer/runtime identity;
- capsule-generation policy/version.

FAIL and UNRESOLVED results are first-class publishable capsules when provenance is complete. Library publication MUST NOT select only favorable PASS results.

A capsule is generated **after** its source package has been sealed. It is not included as authoritative content inside that source package and therefore cannot participate in the source package's manifest/seal hash cycle.

A capsule is a derived semantic summary; it does not erase or replace the sealed source package.

## 3. ClaimSignature

`ClaimSignature` provides structured comparison dimensions. At minimum:

- proposition/family;
- subject/population;
- intervention/exposure;
- comparator/control;
- outcome/metric;
- measurement procedure;
- environment/runtime;
- data/cohort regime;
- artifact/model/system identity where material;
- temporal/version regime;
- assumptions/preconditions;
- scope/boundaries.

The signature is not a universal ontology. Domain extensions MUST be namespaced/versioned.

Signature equality is not sufficient for reuse; applicability policy decides which dimensions are required and how exact/compatible/partial differences are treated.

## 4. ApplicabilityAssessment

Assessment binds:

- exact source capsule ID/hash;
- exact target Goal/Claim/Proof revision;
- `ApplicabilityPolicy` revision/hash;
- dimension-by-dimension comparison;
- relevant provenance overlap;
- source validity/integrity state;
- target assumptions;
- assessor/implementation identity;
- final `ReuseDisposition`;
- reason codes.

Assessment is a governed derived artifact, not agent prose.

## 5. ReuseDisposition

Normative v0.x dispositions:

- `QUALIFIED_REUSE` — prior capsule may be used in a Reuse ProofObligation capable of satisfying the target requirement if EvidenceAdmission also passes.
- `REPLICATION_REQUIRED` — prior result is relevant but insufficiently transportable; new empirical proof is required.
- `SYNTHESIS_INPUT` — eligible as an input candidate for a governed SynthesisContract.
- `METHOD_REFERENCE` — informs method/proof design only.
- `CONTEXT_ONLY` — informs understanding only.
- `INCOMPATIBLE` — not admissible for the proposed target use.

No disposition bypasses current EvidenceAdmissionPolicy.

## 6. Reuse ProofObligation

A Reuse ProofObligation MUST freeze:

- target Claim/proposition;
- exact capsule(s);
- allowed reuse disposition;
- ApplicabilityPolicy;
- EvidenceAdmissionPolicy;
- provenance-overlap constraints;
- target ClaimResolutionPolicy relation;
- adjudication criteria;
- no-new-empirical-execution declaration;
- stop/failure semantics.

The execution may be a deterministic applicability/admission evaluation rather than a new empirical experiment, but it still produces an exact ExecutionAttempt/evidence/adjudication record.

This preserves the existing G2E proof architecture.

## 7. Provenance overlap / anti-double-counting

G2E MUST be able to identify shared ancestry across capsules, including where available:

- same original EvidenceRecord;
- same dataset/cohort/seed family;
- same generated synthetic population;
- same implementation ancestor;
- same base artifact/model;
- same simulator;
- derived synthesis ancestry.

An `EvidenceIndependenceCluster` groups capsules that cannot be treated as independent confirmations under a stated IndependencePolicy.

Three capsules sharing one underlying evidence lineage are not three independent confirmations.

## 8. Freshness

Library evidence is already EXPOSED. Import/reuse NEVER resets it to FRESH.

```text
knowledge reuse ≠ confirmatory resource reuse
```

A new confirmatory proof may use prior capsules for context/design while still requiring a new protected cohort/seed/resource.

## 9. Library query boundary

Library search returns candidate capsule references only.

The sequence is:

```text
Library query
   ↓
candidate capsules
   ↓
ApplicabilityAssessment
   ↓
ReuseDisposition
   ↓
EvidenceAdmission / Proof planning
```

Semantic similarity/relevance score cannot determine ReuseDisposition by itself.

## 10. Capsule publication eligibility

A capsule is eligible for publication only when:

- source ClaimResultPackage, Goal Result Package, or sealed synthesis source package is sealed/verified;
- source Claim resolution is terminal;
- source provenance references are complete enough for configured policy;
- capsule hash binds source package seal;
- secrets/sensitive content pass publication policy;
- capsule does not misstate source verdict/limitations.

Capsule publication state is handled by [PRD-17 Library Adapter](PRD_17_EVIDENCE_LIBRARY_ADAPTER.md) and its backend.

## Acceptance criteria

1. Prior PASS cannot directly resolve a current Claim.
2. QUALIFIED_REUSE always flows through a frozen Reuse ProofObligation and EvidenceAdmission.
3. FAIL/UNRESOLVED capsules remain discoverable when eligible.
4. Reuse never restores freshness.
5. Applicability binds exact source/target/policy identities.
6. Provenance overlap is visible and can constrain independence.
7. Library relevance score cannot substitute for applicability.
8. Runtime/library backend cannot reinterpret ReuseDisposition.

## Dependencies

- **HARD:** [PRD-02 Claim Graph](PRD_02_CLAIM_GRAPH.md), [PRD-04 Evidence Graph](PRD_04_EVIDENCE_GRAPH.md)
- **CONDITIONAL:** [PRD-17 Evidence Library Adapter](PRD_17_EVIDENCE_LIBRARY_ADAPTER.md) for governed library discovery/publication
- **CROSS_CUTTING:** [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)
- **NORMATIVE:** [Core Semantics](CORE_SEMANTICS.md)

## References

- [G2E README](../README.md)
- [PRD-13 Reference Acquisition](PRD_13_REFERENCE_ACQUISITION.md)
- [GWF GAC spec pack](https://github.com/minhtri22/GWF/blob/docs/governed-artifact-catalog-pack/docs/GOVERNED_ARTIFACT_CATALOG_SPEC.md)
- [GWF GAC packing QA](https://github.com/minhtri22/GWF/blob/docs/governed-artifact-catalog-pack/docs/GOVERNED_ARTIFACT_CATALOG_QA.md)
