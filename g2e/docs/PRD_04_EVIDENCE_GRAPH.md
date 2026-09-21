# PRD-04 — Evidence Graph

## Purpose

Represent candidate/admitted evidence, exact provenance, freshness, conflicts, and immutable relations without allowing narrative or last-write-wins evidence to resolve Claims.

## EvidenceRecord

Each EvidenceRecord MUST include:

- `evidence_id`, schema/hash;
- evidence/source class;
- lifecycle: `CANDIDATE | ADMITTED | REJECTED | INVALIDATED`;
- producer ExecutionAttempt identity when execution-produced;
- exact source/artifact/config/resource identities;
- subject Claim/Proof IDs;
- timestamp;
- environment/resource identity;
- payload digest or immutable external reference;
- freshness/protection state;
- redaction/security metadata;
- EvidenceAdmissionPolicy decision/provenance.

Only ADMITTED evidence may be consumed by adjudication.

## EvidenceAdmissionPolicy

Normative requirements are defined in [Core Semantics §10](CORE_SEMANTICS.md). The policy freezes accepted source classes, integrity, producer linkage, freshness, independence, redaction, derivation and missing-data rules.

“Trust class” alone is insufficient and is not a substitute for admission.

External reference/context material does not become empirical proof solely by being retained.

## Relations

Relation direction and immutable binding are normative in [Core Semantics §10](CORE_SEMANTICS.md):

- evidence → attempt: `PRODUCED_BY`;
- evidence → claim/proof: `SUPPORTS/FALSIFIES`;
- evidence → exact artifact/contract revision: `VALIDATES`;
- evidence → evidence: `DERIVED_FROM/REPRODUCES/CONFLICTS_WITH/SUPERSEDES`.

Authoritative relations never float to an unspecified “current” target.

## Freshness

Freshness uses the `FRESH | RESERVED | EXPOSED` model from [Core Semantics §8](CORE_SEMANTICS.md). Once EXPOSED, a resource/evidence source cannot become FRESH again.

## Conflicts

Conflicting evidence remains visible. ClaimResolutionPolicy, not insertion order, determines Claim resolution.

## Acceptance criteria

1. Every admitted evidence item has exact identity/integrity provenance.
2. Candidate/reference evidence cannot bypass EvidenceAdmissionPolicy.
3. Freshness is monotonic and crash recovery fails closed.
4. Relation direction/binding is deterministic.
5. Conflicts are retained without last-write-wins.
6. Invalidating evidence recomputes dependent sufficiency without deleting history.
7. Standalone/GWF expose equivalent logical evidence semantics.

## Dependencies

- **HARD:** [PRD-02 Claim Graph](PRD_02_CLAIM_GRAPH.md), [PRD-03 Proof Planner](PRD_03_PROOF_PLANNER.md)
- **CONDITIONAL/INTEGRATION:** [PRD-07 Execution Protocol](PRD_07_EXECUTION_PROTOCOL.md) for live producer binding
- **CROSS_CUTTING:** [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)
- **NORMATIVE:** [Core Semantics](CORE_SEMANTICS.md)

## References

- [GWF Documentation Integrity & Governance](../../docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md)
- [MindForge M3 evidence](https://github.com/minhtri22/MindForge/blob/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline/m3/M3_QUALIFICATION_EVIDENCE.json)
