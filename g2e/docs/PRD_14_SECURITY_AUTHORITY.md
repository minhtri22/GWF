# PRD-14 — Security & Authority

## Purpose

Define cross-cutting authority, independence, protected-resource, credential and adapter-trust rules.

## Roles and authority actions

Runtime may map roles differently, but MUST identify authority for each normative action:

- goal owner: approve/freeze GoalContract, authorized STOP;
- planner/proposer: propose Claims/Proofs/Next Steps;
- executor: execute authorized attempt;
- evidence authority: admit/reject EvidenceRecord;
- machine adjudicator: deterministic attempt verdict;
- reviewer: evaluate process/evidence as required;
- approver: approve GovernanceDisposition/normative amendments;
- runtime/system: enforce persistence/locks/credentials.

One identity may hold multiple roles only when the Proof/AuthorityPolicy permits it.

## Separation of duty and independence

A ProofObligation MAY require an IndependencePolicy across:

- implementation author vs reviewer;
- planner vs adjudicator;
- provider/app identity;
- protected outcome exposure;
- environment/resource lineage.

Different provider/app alone is never sufficient evidence of independence.

If required separation cannot be satisfied, proof execution/use fails closed.

## Agent authority

Agents may propose/analyze/execute within authority. They may not self-elevate, mutate frozen semantics, access unauthorized protected resources, replace terminal verdicts, or expand write scope beyond authorization.

Delegated authority ≤ parent authority.

## Machine verdict vs governance disposition

Adjudication verdict is immutable.

Authorized governance may attach:

- `ACCEPT_FOR_USE`;
- `REJECT_FOR_USE`;
- `REQUEST_NEW_PROOF`;
- `STOP`.

GovernanceDisposition never rewrites PASS/FAIL/INVALID/UNRESOLVED.

## Protected resources

Use the canonical resource model in [Core Semantics §8](CORE_SEMANTICS.md).

Access requires:

- exact resource identity;
- authorized ProofObligation;
- durable reservation before access;
- exposure record before/atomically with external availability;
- reuse policy.

Uncertain crash recovery is EXPOSED fail-closed.

## Secret boundary

Credentials/secrets MUST NOT persist in Goal/Claim/Proof graphs, AgentBindings, envelopes, logs/evidence, result packages or static docs.

Use external credential resolver/runtime secret store.

Security findings persist only non-reversible fingerprint/classification plus redacted context.

## Adapter trust contract

Every external adapter declares:

- capabilities;
- mutation surface;
- credential requirements;
- version/interface identity;
- security assumptions;
- failure semantics.

External tools do not own G2E verdicts.

## Acceptance criteria

1. Every normative action has an authority check.
2. Required separation-of-duty/independence fails closed when unavailable.
3. Agent cannot approve forbidden self-mutation/elevation.
4. Machine verdict remains immutable under governance disposition.
5. Protected-resource exposure is monotonic/fail-closed.
6. Secret fixtures never persist.
7. Adapter mutation scope explicit.
8. GWF stricter policy governs in GWF mode.

## Dependencies

- **CROSS_CUTTING:** applies to all PRDs
- **NORMATIVE:** [Core Semantics](CORE_SEMANTICS.md)

## References

- [GWF Agent Interoperability Foundation](../../docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)
- [GWF Documentation Integrity & Governance](../../docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md)
- [GWF Findings](../../docs/Finding_checklist.md)
