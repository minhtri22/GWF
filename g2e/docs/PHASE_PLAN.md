# G2E Initial Phase Plan

This plan is implementation-neutral. Phase progression requires the prior phase exit gate and a clean current [semantic QA](QA_doc.md).

## P0 — Foundation Specification

Scope:
- architecture;
- README/lineage;
- PRD set;
- normative Core Semantics;
- reference/dependency baseline;
- semantic QA.

Exit:
- documents internally consistent;
- all components have PRD;
- state/verdict namespaces separated;
- standalone/GWF boundary explicit;
- agent-app priority explicit;
- current semantic QA PASS with OPEN=0.

## P0.2 — Evidence Reuse & Convergence Specification

Scope:
- PRD-15 Evidence Reuse & Applicability;
- PRD-16 Synthesis & Convergence;
- PRD-17 Evidence Library Adapter;
- GWF Governed Artifact Catalog integration boundary;
- Core Semantics extensions;
- cross-document semantic QA.

Exit:
- prior evidence cannot bypass ProofObligation/EvidenceAdmission;
- library evidence freshness semantics frozen;
- provenance overlap/double-counting rules frozen;
- synthesis universe/inclusion/no-rescue rules frozen;
- GWF-vs-G2E library ownership boundary explicit;
- P0.2 QA PASS with OPEN=0.

## P1 — Core Schemas

Implement canonical schemas for:

- GoalContract and GoalRequirement;
- GoalClosureContract and satisfaction/falsification expressions;
- Claim and ClaimGraph;
- ClaimResolutionPolicy;
- ProofObligation and ProofRetryPolicy;
- ExecutionAttempt identity/envelope schema (no executor implementation);
- EvidenceRecord, EvidenceRelation, EvidenceAdmissionPolicy;
- ProtectedResource and freshness/reuse policy;
- Adjudication;
- SelectionPolicy and SelectionDecision;
- AmendmentPolicy;
- AuthorityPolicy, IndependencePolicy, GovernanceDisposition;
- canonical identity/hash/version fields;
- EvidenceCapsule and ClaimSignature;
- ApplicabilityPolicy/ApplicabilityAssessment/ReuseDisposition;
- reuse-proof metadata and provenance-cluster identifiers;
- SynthesisContract, SynthesisUniverse, SynthesisResult, ConvergenceClassification;
- Evidence Library Adapter query/publication/snapshot contracts.

Exit:
- schema validation;
- canonical JSON/identity conformance fixtures;
- HARD dependency DAG fixture;
- schema-version compatibility/fail-closed fixtures;
- no execution backend.

## P2 — Deterministic Core Engine

Implement:

- ClaimGraph/GoalClosure validation;
- Proof admissibility validation;
- Evidence admission and relation validation;
- protected-resource/freshness state machine;
- deterministic attempt adjudicator;
- Proof closure and Claim resolver;
- Goal evaluator;
- Next-Step admissible-set engine;
- deterministic SelectionPolicy ranking/tie-break;
- amendment/no-rescue enforcement;
- intentional PASS/FAIL/INVALID/UNRESOLVED fixtures;
- applicability/reuse-policy engine;
- Reuse ProofObligation qualification fixtures;
- provenance-overlap/independence clustering;
- synthesis universe/inclusion determinism;
- synthesis no-rescue and transitive-ancestry checks.

Exit:
- no agent required;
- no runtime adapter required;
- known negative fixtures cannot be rescued;
- prior PASS cannot directly flip a current Claim;
- dependent capsules cannot be counted as independent by default;
- multiple-proof Claim resolution tested;
- alternate-path Goal closure tested;
- deterministic fixtures PASS.

## P3 — Standalone Runtime

Implement:
- durable local system of record;
- atomic persistence;
- attempt ledger;
- protected-resource ledger;
- local executor facade;
- Result Package manifest/seal.

Exit:
- restart/recovery;
- terminality preserved;
- protected exposure fail-closed;
- exportable/verifiable result package.

## P4 — GWF Adapter

Implement:
- canonical G2E↔GWF mapping;
- authority/recovery/handoff integration;
- generic dynamic proof execution facade;
- runtime-specific IDs as mappings only.

Exit:
- parity fixture against standalone;
- canonical G2E IDs/hashes unchanged across export/import;
- no semantic reinterpretation.

## P5 — Codex and ChatGPT App Profiles

Implement in the same priority wave but as separate adapter profiles:

- Codex profile;
- ChatGPT profile;
- independent capability discovery/binding;
- no assumed harness parity.

Exit:
- each available profile executes one frozen proof end-to-end through its actual harness;
- binding/attempt/evidence identities attributable;
- unsupported capability fails closed;
- no hidden authority escalation.

## P6 — GitHub Evidence Adapter

Implement SHA-safe code/workflow/evidence loop.

Exit:
- implementation SHA → workflow evidence → admission → adjudication → evidence-only closure fixture;
- green workflow is not automatically PASS.

## P7 — Adaptive Goal-to-Evidence Pilot

Use a new bounded technical goal not hard-coded into tests.

Exit:
- goal requirements frozen;
- claim graph + goal closure compiled;
- multiple dynamic proof obligations;
- at least one non-PASS outcome handled correctly;
- Next-Step recomputation demonstrated;
- final sealed Goal Result Package.

## P8 — Additional Agent Providers

Order:
1. Claude;
2. Gemini;
3. ARC transport paths for other model-backed agents.

No provider may require a G2E core schema change.

## References

- [Core Semantics](CORE_SEMANTICS.md)
- [PRD Index](PRD_INDEX.md)
- [Reference Baseline](REFERENCE_BASELINE.md)
- [GWF Agent Interoperability Foundation](../../docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)
- [GWF 7-Wave plan](../../docs/IMPLEMENTATION_7_WAVES_PLAN.md)
