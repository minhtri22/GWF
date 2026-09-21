# PRD-08 — GWF Adapter

## Purpose

Make GWF the default execution/governance/persistence backend for G2E without making GWF a hard dependency of G2E core semantics.

## Architecture boundary

```text
G2E Core Semantics
  Goal / Claim / Proof / Evidence / Adjudication
                ↓
            GWF Adapter
                ↓
GWF runtime / system of record
  artifacts/revisions
  authority/approval
  recovery/handoff
  GitHub/plugin infrastructure
  agent interoperability
```

G2E owns semantic meaning. GWF owns default durable persistence/governance execution. GWF MUST NOT reinterpret canonical G2E verdict/state semantics.

## Adapter mappings

The adapter MUST map:

- GoalContract/GoalClosureContract → governed GWF artifact revisions;
- ClaimGraph/ProofObligation → exact GWF artifact/trace refs;
- ExecutionAttempt → GWF execution/workunit state;
- G2E authority action → GWF actor/approval policy;
- EvidenceRecord → GWF artifact/evidence refs;
- Adjudication/GovernanceDisposition → immutable governed records;
- SelectionDecision/handoff → governed checkpoint/handoff state.

Canonical G2E IDs/hashes remain unchanged. GWF IDs are runtime mappings.

## Dynamic proof work

G2E dynamically creates ProofObligations. The adapter SHOULD use a generic governed G2E execution facade/workunit rather than generating arbitrary trusted domain YAML at runtime.

Dynamic work still passes normal GWF authority, preflight, execution, verification and handoff controls.

## System-of-record rule

In GWF mode:

- GWF is the durable system of record for canonical G2E objects;
- G2E schemas/semantics remain normative;
- runtime state may not silently mutate frozen canonical content;
- export back to standalone must preserve canonical IDs/hashes.

## Versioning

Record:

- G2E core/schema versions;
- GWF runtime version;
- adapter mapping version;
- GWF domain revision if used;
- active Agent Interoperability contract revision.

Unknown incompatible schema/runtime mappings fail closed.

## Acceptance criteria

1. Same G2E objects retain IDs/hashes in standalone and GWF.
2. GWF persistence reconstructs complete G2E execution/evidence mapping.
3. GWF completion/PASS-like runtime state is never Claim PASS by implication.
4. Recovery respects frozen G2E RetryPolicy/freshness.
5. GWF stricter authority remains effective.
6. GWF upgrades are independent when compatibility contract passes.
7. PRD-09/10 can be integrated later without being hard prerequisites for core GWF mapping.

## Dependencies

- **HARD:** [PRD-07 Execution Protocol](PRD_07_EXECUTION_PROTOCOL.md)
- **INTEGRATION:** [PRD-09 Agent App Adapters](PRD_09_AGENT_APP_ADAPTERS.md), [PRD-10 GitHub Adapter](PRD_10_GITHUB_ADAPTER.md)
- **CROSS_CUTTING:** [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)
- **NORMATIVE:** [Core Semantics](CORE_SEMANTICS.md)

## References

- [GWF README](../../README.md)
- [GWF DomainSDK](../../src/gwr/domain_sdk.py)
- [GWF Runtime](../../src/gwr/runtime.py)
- [GWF Agent Interoperability Foundation](../../docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)
