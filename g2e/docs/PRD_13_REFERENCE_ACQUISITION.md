# PRD-13 — Reference Acquisition

## Purpose

Acquire prior art/specifications/repository capability evidence without contaminating protected outcomes or treating contextual references as empirical proof by default.

## Default strategy

In GWF mode, reuse the GWF Reference Acquisition capability. G2E adds Claim/Proof relation semantics and EvidenceAdmissionPolicy.

Reference Acquisition and Evidence Library are distinct:

- Reference Acquisition discovers external/current prior art, specifications and capability sources.
- PRD-17 retrieves previously governed G2E/GWF result artifacts such as EvidenceCapsules.
- Either may inform planning, but neither bypasses Applicability/EvidenceAdmission.

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

## Dependencies

- **HARD:** [PRD-01 Goal Contract](PRD_01_GOAL_CONTRACT.md), [PRD-02 Claim Graph](PRD_02_CLAIM_GRAPH.md)
- **CROSS_CUTTING:** [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)
- **NORMATIVE:** [Core Semantics](CORE_SEMANTICS.md)

## References

- [GWF Reference Acquisition Specification](../../docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md)
- [Reference Baseline](REFERENCE_BASELINE.md)
