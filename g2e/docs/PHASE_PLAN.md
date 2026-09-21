# G2E Initial Phase Plan

This plan is intentionally implementation-neutral. Phase progression requires the prior phase exit gate.

## P0 — Foundation Specification

Scope:
- architecture;
- README/lineage;
- PRD set;
- reference/dependency map.

Exit:
- documents internally consistent;
- all components have PRD;
- standalone/GWF boundary explicit;
- agent-app priority explicit.

## P1 — Core Schemas

Implement:
- GoalContract;
- Claim;
- ClaimGraph;
- ProofObligation;
- EvidenceRecord/relations;
- Adjudication;
- SelectionDecision.

Exit:
- schema validation;
- canonical serialization/hashing;
- fixture graph;
- no execution backend.

## P2 — Deterministic Core Engine

Implement:
- graph validation;
- evidence admission;
- adjudicator;
- next-step admissibility engine;
- intentional PASS/FAIL/INVALID/UNRESOLVED fixtures;
- anti-rescue tests.

Exit:
- no agent required;
- deterministic fixtures PASS.

## P3 — Standalone Runtime

Implement:
- durable local state;
- atomic persistence;
- attempt ledger;
- protected-resource ledger;
- local executor facade.

Exit:
- restart/recovery;
- terminality preserved;
- exportable result package.

## P4 — GWF Adapter

Implement:
- G2E↔GWF mapping;
- authority/recovery/handoff integration;
- generic dynamic proof execution facade.

Exit:
- parity fixture against standalone;
- no semantic reinterpretation.

## P5 — Codex / ChatGPT Agent Adapter

Implement first-priority agent-app binding using the GWF interoperability contracts and existing harness capabilities.

Exit:
- one frozen proof executed end-to-end;
- binding/attempt/evidence identities attributable;
- no hidden authority escalation.

## P6 — GitHub Evidence Adapter

Implement SHA-safe code/workflow/evidence loop.

Exit:
- implementation SHA → workflow evidence → adjudication → evidence-only closure fixture.

## P7 — Adaptive Goal-to-Evidence Pilot

Use a new bounded technical goal not hard-coded into tests.

Exit:
- goal compiled to claims;
- multiple dynamic proof obligations;
- at least one non-PASS outcome handled correctly;
- final Goal Result Package.

## P8 — Additional Agent Providers

Order:
1. Claude;
2. Gemini;
3. ARC transport paths for other model-backed agents.

No provider may require a G2E core schema change.

## References

- [PRD Index](PRD_INDEX.md)
- [GWF Agent Interoperability Foundation](../../docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)
- [GWF 7-Wave plan](../../docs/IMPLEMENTATION_7_WAVES_PLAN.md)
