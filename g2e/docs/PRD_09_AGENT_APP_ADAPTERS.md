# PRD-09 — Agent App Adapters

## Purpose

Provide normalized bindings for agent applications while leveraging each application's existing harness/tools without assuming capability parity.

## Priority profiles

### P0a — Codex app profile

Separate `agent_app=codex` capability/binding profile.

### P0b — ChatGPT app profile

Separate `agent_app=chatgpt` capability/binding profile.

Codex and ChatGPT are the same priority wave, but MUST be discovered, qualified and versioned independently.

### P1 — Claude profile

Same normalized adapter contract; no core schema changes.

### P2 — Gemini profile

Same normalized adapter contract; no core schema changes.

### P3 — ARC transport paths

ARC is transport only. Provider/model/app/harness/resource identities remain separate.

## AgentBinding

A normalized binding MUST distinguish:

- `agent_app`;
- `provider_ref`;
- `model_ref` when material/available;
- `harness_ref`;
- `transport_ref`;
- capabilities;
- execution constraints;
- authority scope;
- `binding_mode: dynamic | frozen`;
- equivalence policy;
- resolved attempt identity.

Capability discovery is required before assignment. An adapter must not infer ChatGPT capability from Codex qualification or vice versa.

## Adapter behavior

Support:

- capability discovery;
- binding resolution before each attempt;
- frozen task/proof envelope submission;
- progress/status normalization;
- artifact/candidate-evidence extraction;
- interruption/cancellation;
- final handoff;
- credential redaction.

Provider-native reasoning fields may be diagnostic, but hidden chain-of-thought is not required G2E evidence.

## Independence

Independence is governed by the ProofObligation's IndependencePolicy. A different provider/app alone does not prove independent QA.

## Acceptance criteria

1. Codex and ChatGPT profiles have separate capability manifests and qualification evidence.
2. Provider/model/app/harness/transport identities remain separate.
3. Dynamic reassignment creates a new attempt ID.
4. Frozen binding detects material substitution.
5. Required independence dimensions are verified prospectively.
6. Secret material never persists.
7. Claude/Gemini/ARC additions do not change core proof schemas.
8. Unsupported app capability fails closed rather than degrading silently.

## Dependencies

- **HARD:** [PRD-07 Execution Protocol](PRD_07_EXECUTION_PROTOCOL.md)
- **INTEGRATION:** [PRD-08 GWF Adapter](PRD_08_GWF_ADAPTER.md) in default GWF mode
- **CROSS_CUTTING:** [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)
- **NORMATIVE:** [Core Semantics](CORE_SEMANTICS.md)

## References

- [GWF Agent Interoperability Foundation](../../docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)
- [GWF findings/checklist](../../docs/Finding_checklist.md)
