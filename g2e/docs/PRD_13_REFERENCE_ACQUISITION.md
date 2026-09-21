# PRD-13 — Reference Acquisition

## Purpose

Acquire prior art/specifications/repository capability evidence without contaminating protected outcomes or treating contextual references as empirical proof by default.

## Default strategy

In GWF mode, reuse the GWF Reference Acquisition capability. G2E adds Claim/Proof relation semantics and EvidenceAdmissionPolicy.

Reference Acquisition and the G2E Evidence Library are distinct semantic consumers over potentially shared GWF infrastructure:

- Reference Acquisition owns research-side prior-art/novelty curation across external providers and the internal `GWF_CATALOG` channel.
- PRD-17 owns direct G2E discovery/publication of governed semantic results such as EvidenceCapsules/SynthesisResults.
- Both may query the same GAC substrate, but they produce different governed observation records and neither bypasses Applicability/EvidenceAdmission.

## GWF Shared Library channel

When GWF Reference Acquisition enables source channel `GWF_CATALOG`, G2E MUST preserve the GWF retrieval provenance:

- retrieval channel = `GWF_CATALOG`;
- exact `CatalogQueryExecution` reference;
- authoritative catalog snapshot/revision;
- exact CatalogEntry IDs observed;
- exact selected catalog subject revision/hash;
- query execution status/completeness;
- Reference Acquisition disposition/curation result.

A GAC backend failure or partial result is not a valid “zero relevant references” observation.

### Routing rule

Use PRD-13/Reference Acquisition when the purpose is research **prior-art, novelty, method/source curation, or literature/reference coverage**.

Use PRD-17 directly when the purpose is G2E **EvidenceCapsule reuse, applicability, proof reuse, or synthesis input discovery**.

The same exact GAC subject may be observed through both routes. Subject identity is deduplicated by exact immutable subject identity/hash; the two query/retrieval observations remain distinct provenance records.

A G2E EvidenceCapsule discovered through Reference Acquisition does not become an admitted G2E reuse candidate merely because RA retained it. PRD-15/17 still govern applicability/reuse.

## Temporal modes

Terms map exactly to [Core Semantics §7](CORE_SEMANTICS.md):

- `PRE_LOCK`: before PROOF_FROZEN;
- `LOCKED_PRE_OUTCOME`: PROOF_FROZEN through before OUTCOME_EXPOSED;
- `POST_OUTCOME`: from OUTCOME_EXPOSED onward.

A discovered reference that would normatively alter a locked proof follows amendment/new-lineage rules; it never silently rewrites the old proof.

## Reference record

Record:

- canonical source identity;
- exact inspected snapshot/revision;
- retrieval session/query identity;
- provider/timestamp;
- disposition;
- extracted capability/fact;
- relation to Goal/Claim/Proof;
- content digest where feasible;
- source/evidence class;
- exposure/temporal mode.

## Use classes

Examples:

- prior art/context;
- implementation capability evidence;
- specification authority;
- baseline source;
- candidate direct empirical evidence.

Classification alone does not admit evidence. Formal use in adjudication requires the frozen EvidenceAdmissionPolicy from PRD-04.

## Tool capability evidence

External tool/framework capability claims must be revalidated and pinned at implementation/upgrade time. Current docs are design references, not permanent vendor guarantees.

## Acceptance criteria

1. Exact executed retrieval/query sessions attributable.
2. Canonical source and inspected snapshot distinct.
3. PRE_LOCK/LOCKED_PRE_OUTCOME/POST_OUTCOME use canonical event boundaries.
4. Post-outcome discoveries cannot rewrite old proofs.
5. Reference class does not bypass EvidenceAdmissionPolicy.
6. GWF mode reuses GWF registry/log primitives.
7. Standalone exports equivalent records.
8. External reference retrieval and governed result-library retrieval remain distinguishable provenance classes.
9. GWF_CATALOG retrieval preserves CatalogQueryExecution/snapshot/CatalogEntry/subject identities.
10. Direct PRD-17 reuse discovery and PRD-13 research curation cannot be silently conflated.
11. Duplicate observations of one exact catalog subject do not create duplicate source identity.

## Dependencies

- **HARD:** [PRD-01 Goal Contract](PRD_01_GOAL_CONTRACT.md), [PRD-02 Claim Graph](PRD_02_CLAIM_GRAPH.md)
- **CROSS_CUTTING:** [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)
- **NORMATIVE:** [Core Semantics](CORE_SEMANTICS.md)

## References

- [Reconciled GWF Reference Acquisition Specification](https://github.com/minhtri22/GWF/blob/be7d606c64a97d9525d1f72d744fe5b7a336ff0c/docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md)
- [GWF Library Integration Mapping](GWF_LIBRARY_INTEGRATION_MAPPING.md)
- [Reference Baseline](REFERENCE_BASELINE.md)
