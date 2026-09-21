# PRD-07 — Execution Protocol

## Purpose

Define the provider-neutral contract between one frozen/authorized ProofObligation and execution backends.

## ExecutionAttempt

Each attempt MUST bind:

- unique `attempt_id`;
- ProofObligation ID/hash;
- implementation/source revision;
- config/artifact/data identities;
- agent/provider/model/app/harness/transport identities as applicable;
- resource/environment identity;
- protected-resource authorization;
- expected output/evidence classes;
- RetryPolicy;
- authority scope;
- IndependencePolicy requirements.

## Executor lifecycle

Normative states are:

`CREATED → PREFLIGHT → LOCKED → RUNNING → COMPLETED | EXECUTOR_FAILED | CANCELLED | TIMED_OUT | PREEMPTED`.

These states are executor-only. None means G2E PASS/FAIL/INVALID/UNRESOLVED.

A COMPLETED attempt may still adjudicate FAIL, INVALID or UNRESOLVED. An EXECUTOR_FAILED attempt normally produces evidence leading to INVALID, but the Adjudicator owns that verdict.

## Protected access

If protected resources are needed:

1. authorization is checked;
2. resource is durably RESERVED before access;
3. OUTCOME_EXPOSED is recorded according to Core Semantics;
4. uncertain crash recovery fails closed to EXPOSED.

## Retry

Infrastructure retry is allowed only under frozen RetryPolicy and must preserve semantic ProofObligation identity. Material agent/provider/resource reassignment creates a new attempt identity and must satisfy equivalence/IndependencePolicy.

## ExecutionResult

Normalized result contains:

- executor state;
- start/end;
- action/command summary;
- artifact/log/candidate-evidence references;
- resource identity;
- agent/provider/model/app/harness/transport identities;
- technical error class/reason;
- redaction metadata.

Executor must not assign scientific/substantive FAIL.

## Acceptance criteria

1. GWF/standalone consume the same canonical ProofObligation/envelope semantics.
2. Execution state cannot directly update Claim resolution.
3. Every execution-produced EvidenceRecord links to an attempt.
4. Protected-resource transitions are durable/fail-closed.
5. Material reassignment is visible.
6. Retry budget and semantic equivalence are enforceable.
7. Provider credentials never persist.

## Dependencies

- **HARD:** [PRD-03 Proof Planner](PRD_03_PROOF_PLANNER.md)
- **INTEGRATION:** [PRD-05 Adjudicator](PRD_05_ADJUDICATOR.md) consumes execution/evidence
- **CROSS_CUTTING:** [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)
- **NORMATIVE:** [Core Semantics](CORE_SEMANTICS.md)

## References

- [GWF Agent Interoperability Foundation](../../docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)
- [GWF software domain](../../domains/software.workflow.yaml)
