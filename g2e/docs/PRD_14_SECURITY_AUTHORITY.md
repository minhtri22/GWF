# PRD-14 — Security & Authority

## Purpose

Define the cross-cutting trust boundary for goals, agent actions, protected resources, credentials, evidence, approvals and external adapters.

## Authority model

G2E core defines required authority classes; runtime adapters implement them.

Minimum roles:

- goal owner;
- planner/proposer;
- executor;
- reviewer/adjudicator;
- runtime/system.

In single-user standalone mode, roles may map to one human identity, but self-review limitations must remain explicit.

## Agent authority

An agent may:

- propose claims;
- propose proof obligations;
- execute authorized tasks;
- analyze evidence;
- propose next steps.

An agent may not, without required authority:

- change frozen goal semantics;
- consume protected resources;
- mutate frozen decision rules;
- replace terminal adjudication;
- expand repository/write scope;
- elevate its own permissions.

Delegated child authority must be <= parent authority.

## Secret boundary

Provider/API credentials MUST NOT persist in:

- Goal Contracts;
- Claim/Proof graphs;
- AgentBindings;
- execution envelopes;
- logs/evidence;
- result packages;
- static UI/repository docs.

Use external credential resolvers or runtime secret stores.

Security findings persist only non-reversible fingerprints/classification plus redacted remediation context.

## Protected resources

Fresh seeds, confirmatory datasets, hidden tests, unpublished results and private corpora may be marked protected.

Access requires:

- eligible Proof Obligation;
- frozen access policy;
- attributable attempt identity;
- exposure event persisted immediately.

## Adapter trust

Every external adapter must declare:

- capabilities;
- mutation surface;
- credential requirements;
- version/interface identity;
- security assumptions;
- failure semantics.

External tools report results; they do not own G2E verdict semantics.

## Acceptance criteria

1. Unauthorized protected-resource access fails closed.
2. Agent cannot approve its own forbidden normative mutation.
3. Secret fixtures do not appear in persisted artifacts/logs.
4. Adapter mutation scope is explicit.
5. Delegation cannot escalate authority.
6. Standalone capability limitations are visible.
7. GWF mode defers to stricter GWF authority when policies overlap.

## Dependencies

Cross-cutting dependency for all PRDs.

## References

- [GWF Agent Interoperability Foundation](../../docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)
- [GWF Documentation Integrity & Governance](../../docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md)
- [GWF Finding checklist — authority/secrets/ARC findings](../../docs/Finding_checklist.md)
- [GWF Runtime/Governance architecture](../../README.md)
