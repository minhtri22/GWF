# G2E PRD Index

This index is the navigation root for G2E product requirements.

## Normative shared documents

- [G2E README](../README.md)
- [Core Semantics](CORE_SEMANTICS.md)
- [Reference Baseline](REFERENCE_BASELINE.md)
- [Current Semantic QA](QA_doc.md)
- [G2E Lineage](../LINEAGE.md)

Dependency classes are normative in [Core Semantics §6](CORE_SEMANTICS.md).

## Component dependency map

| ID | Component | HARD | CONDITIONAL / INTEGRATION | CROSS-CUTTING |
| --- | --- | --- | --- | --- |
| PRD-01 | [Goal Contract](PRD_01_GOAL_CONTRACT.md) | none | none | PRD-14 |
| PRD-02 | [Claim Compiler & Claim Graph](PRD_02_CLAIM_GRAPH.md) | PRD-01 | none | PRD-14 |
| PRD-03 | [Proof Obligation Planner](PRD_03_PROOF_PLANNER.md) | PRD-01, PRD-02 | PRD-13 when external references inform design | PRD-14 |
| PRD-04 | [Evidence Graph](PRD_04_EVIDENCE_GRAPH.md) | PRD-02, PRD-03 | PRD-07 for live producer binding | PRD-14 |
| PRD-05 | [Adjudicator](PRD_05_ADJUDICATOR.md) | PRD-03, PRD-04 | PRD-07 provides execution evidence | PRD-14 |
| PRD-06 | [Next-Step Selector](PRD_06_NEXT_STEP_SELECTOR.md) | PRD-02, PRD-03, PRD-04, PRD-05 | PRD-13 when prior art changes admissibility | PRD-14 |
| PRD-07 | [Execution Protocol](PRD_07_EXECUTION_PROTOCOL.md) | PRD-03 | PRD-05 consumes results | PRD-14 |
| PRD-08 | [GWF Adapter](PRD_08_GWF_ADAPTER.md) | PRD-07 | PRD-09 and PRD-10 are integration capabilities, not hard prerequisites | PRD-14 |
| PRD-09 | [Agent App Adapters](PRD_09_AGENT_APP_ADAPTERS.md) | PRD-07 | PRD-08 in default GWF mode | PRD-14 |
| PRD-10 | [GitHub Adapter](PRD_10_GITHUB_ADAPTER.md) | PRD-07 | PRD-08 in default GWF mode | PRD-14 |
| PRD-11 | [Standalone Runtime](PRD_11_STANDALONE_RUNTIME.md) | PRD-04, PRD-05, PRD-07 | import/export integration with PRD-08 | PRD-14 |
| PRD-12 | [Goal Result Package](PRD_12_RESULT_PACKAGE.md) | PRD-01 through PRD-06 | runtime artifact backends | PRD-14 |
| PRD-13 | [Reference Acquisition](PRD_13_REFERENCE_ACQUISITION.md) | PRD-01, PRD-02 | GWF reference subsystem in default mode | PRD-14 |
| PRD-14 | [Security & Authority](PRD_14_SECURITY_AUTHORITY.md) | none | runtime-specific authority adapters | applies across all |
| PRD-15 | [Evidence Reuse & Applicability](PRD_15_EVIDENCE_REUSE_APPLICABILITY.md) | PRD-02, PRD-04 | PRD-17 for governed library discovery/publication | PRD-14 |
| PRD-16 | [Synthesis & Convergence](PRD_16_SYNTHESIS_CONVERGENCE.md) | PRD-02, PRD-03, PRD-04, PRD-05, PRD-06, PRD-15 | PRD-17 for catalog-backed universe retrieval | PRD-14 |
| PRD-17 | [Evidence Library Adapter](PRD_17_EVIDENCE_LIBRARY_ADAPTER.md) | PRD-15 | PRD-08 default GWF backend; PRD-11 standalone backend | PRD-14 |

The HARD dependency graph must remain acyclic.

P0.2 adds PRD-15/16/17 before schema implementation. GWF Governed Artifact Catalog is an integration backend contract, not a HARD dependency of G2E core semantics.

## Implementation phases

See [PHASE_PLAN.md](PHASE_PLAN.md). P1 includes the original core schemas plus ClaimResultPackage, EvidenceCapsule, ClaimSignature, ApplicabilityAssessment, ReuseDisposition/Reuse Proof metadata, SynthesisContract/SynthesisResult, provenance-cluster, LibraryCapabilityManifest and Evidence Library Adapter contracts.

## Architectural references

- [GWF Agent Interoperability Foundation](../../docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)
- [GWF Reference Acquisition Specification](../../docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md)
- [GWF Documentation Integrity & Governance](../../docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md)
- [GWF 7-Wave Implementation Plan](../../docs/IMPLEMENTATION_7_WAVES_PLAN.md)
- [GWF Research Domain](../../domains/research.workflow.yaml)

Exact baseline commits are recorded in [REFERENCE_BASELINE.md](REFERENCE_BASELINE.md).


## GWF Shared Library integration mapping

Cross-system ownership, terminology, routing and exact readiness gates are frozen in [GWF_LIBRARY_INTEGRATION_MAPPING.md](GWF_LIBRARY_INTEGRATION_MAPPING.md).

G2E P1/P2 are not HARD-dependent on GWF GAC implementation. The GWF-backed Evidence Library path is a later conditional integration gated by the capabilities actually requested.
