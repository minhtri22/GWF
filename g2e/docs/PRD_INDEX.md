# G2E PRD Index

This index is the navigation root for G2E product requirements.

## Architectural references

- [G2E README](../README.md)
- [G2E Lineage](../LINEAGE.md)
- [GWF Agent Interoperability Foundation](../../docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)
- [GWF Reference Acquisition Specification](../../docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md)
- [GWF Documentation Integrity & Governance](../../docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md)
- [GWF 7-Wave Implementation Plan](../../docs/IMPLEMENTATION_7_WAVES_PLAN.md)
- [GWF Research Domain](../../domains/research.workflow.yaml)

## PRDs and hard dependency order

| ID | Component | Hard dependencies |
| --- | --- | --- |
| PRD-01 | [Goal Contract](PRD_01_GOAL_CONTRACT.md) | none |
| PRD-02 | [Claim Compiler & Claim Graph](PRD_02_CLAIM_GRAPH.md) | PRD-01 |
| PRD-03 | [Proof Obligation Planner](PRD_03_PROOF_PLANNER.md) | PRD-01, PRD-02 |
| PRD-04 | [Evidence Graph](PRD_04_EVIDENCE_GRAPH.md) | PRD-02, PRD-03 |
| PRD-05 | [Adjudicator](PRD_05_ADJUDICATOR.md) | PRD-03, PRD-04 |
| PRD-06 | [Next-Step Selector](PRD_06_NEXT_STEP_SELECTOR.md) | PRD-02, PRD-03, PRD-04, PRD-05 |
| PRD-07 | [Execution Protocol](PRD_07_EXECUTION_PROTOCOL.md) | PRD-03, PRD-05 |
| PRD-08 | [GWF Adapter](PRD_08_GWF_ADAPTER.md) | PRD-07 |
| PRD-09 | [Agent App Adapters](PRD_09_AGENT_APP_ADAPTERS.md) | PRD-07; GWF interop spec for default mode |
| PRD-10 | [GitHub Adapter](PRD_10_GITHUB_ADAPTER.md) | PRD-07 |
| PRD-11 | [Standalone Runtime](PRD_11_STANDALONE_RUNTIME.md) | PRD-04, PRD-05, PRD-07 |
| PRD-12 | [Goal Result Package](PRD_12_RESULT_PACKAGE.md) | PRD-01 through PRD-06 |
| PRD-13 | [Reference Acquisition](PRD_13_REFERENCE_ACQUISITION.md) | PRD-01, PRD-02 |
| PRD-14 | [Security & Authority](PRD_14_SECURITY_AUTHORITY.md) | cross-cutting |

## Reference implementation evidence

The MindForge M0–M4 lineage is used to derive requirements, not to prescribe fixed phases:

- [Evidence root](https://github.com/minhtri22/MindForge/tree/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline)
- [M2 trainer/checkpoint evidence](https://github.com/minhtri22/MindForge/blob/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline/m2/IMPLEMENTATION_RESULT.md)
- [M3 governance evidence](https://github.com/minhtri22/MindForge/blob/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline/m3/IMPLEMENTATION_RESULT.md)
- [M4 reasoning evidence](https://github.com/minhtri22/MindForge/blob/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline/m4/IMPLEMENTATION_RESULT.md)
