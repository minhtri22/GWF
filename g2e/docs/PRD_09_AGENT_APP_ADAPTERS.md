# PRD-09 — Agent App Adapters

## Purpose

Provide normalized execution bindings for agent applications while leveraging each application's existing harness, tools, context handling and coding/research capabilities.

## Priority

### P0 — Codex / ChatGPT

Primary implementation target.

Goals:

- exploit existing coding/research harness rather than rebuilding shell/browser/Git tooling;
- allow G2E/GWF to assign a frozen proof objective;
- receive attributable execution/evidence/handoff;
- preserve attempt identity and authority boundary.

### P1 — Claude

Implement the same normalized adapter contract after P0 semantics stabilize.

### P2 — Gemini

Implement the same normalized adapter contract after P0/P1.

### P3 — Other model-backed agents through ARC

ARC is a **transport**, not a model/resource class. Model/provider/resource identities remain explicit.

## AgentBinding

A normalized binding SHOULD contain:

- `agent_app`;
- `provider_ref`;
- `agent/model identity` where available;
- `harness_ref`;
- `transport_ref`;
- `capabilities`;
- `execution_constraints`;
- `authority_scope`;
- `binding_mode: dynamic | frozen`;
- equivalence policy;
- resolved attempt identity.

## Adapter behavior

The adapter must support:

- capability discovery;
- binding resolution before attempt;
- prompt/task envelope submission;
- streaming or batched progress normalization;
- artifact/evidence extraction;
- interruption/cancellation;
- final handoff;
- redaction of secrets/provider tokens.

The adapter may preserve provider-native reasoning/status fields for diagnostics, but G2E must not treat hidden chain-of-thought as required evidence. Formal evidence is explicit artifact/result data.

## Independence

Using a different provider does not automatically create independent QA. Independence must be a prospective constraint over lineage, data exposure, implementation role and binding identity.

## No hard provider dependency

G2E core cannot require an OpenAI-, Anthropic-, Google-, or ARC-specific schema. Provider-specific behavior lives behind the adapter.

## Acceptance criteria

1. Codex/ChatGPT adapter can execute one frozen proof through an existing harness and return a normalized envelope.
2. Provider/transport/harness identities remain distinct.
3. Dynamic reassignment creates a new attempt identity.
4. Frozen binding detects material substitution.
5. Secret material never persists.
6. Claude/Gemini can be added without changing core proof schemas.
7. ARC-backed execution preserves provider/model identity separately from ARC transport identity.

## Dependencies

- [PRD-07 Execution Protocol](PRD_07_EXECUTION_PROTOCOL.md)
- [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)
- GWF default integration: [PRD-08 GWF Adapter](PRD_08_GWF_ADAPTER.md)

## References

- [GWF Agent Interoperability Foundation](../../docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)
- [GWF interoperability findings/checklist](../../docs/Finding_checklist.md)
- [GWF Agent Protocol overview](../../README.md)
