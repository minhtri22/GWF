# PRD-05 — Adjudicator

## Purpose

Produce a deterministic one-shot verdict for one ExecutionAttempt using only the frozen ProofObligation and ADMITTED evidence.

## Verdict namespace

Only these Adjudication verdicts are normative:

- `PASS`;
- `FAIL`;
- `INVALID`;
- `UNRESOLVED`.

Meanings are defined in [Core Semantics §2.7](CORE_SEMANTICS.md). They are not Claim lifecycle states, Goal verdicts, or executor states.

## One-shot semantics

Each ExecutionAttempt may be adjudicated at most once. The verdict artifact binds:

- ProofObligation ID/hash;
- attempt ID and execution envelope hash;
- admitted evidence IDs/hashes;
- decision-rule hash;
- adjudicator implementation/version;
- verdict and reason codes.

A second verdict for the same attempt is rejected.

Proof retry/closure semantics follow [Core Semantics §3](CORE_SEMANTICS.md). INVALID may permit a replacement attempt only under frozen RetryPolicy; PASS/FAIL/UNRESOLVED never permit “same obligation until desired result”.

## No-rescue

After OUTCOME_EXPOSED the adjudicator rejects semantic mutation of thresholds, cohorts/seeds, metrics, baselines/controls, budgets/refunds, data inclusion, artifacts, evidence rules or Claim meaning.

## Governance disposition

Human review/approval may attach a `GovernanceDisposition` defined in [Core Semantics §12](CORE_SEMANTICS.md), but it never rewrites the machine verdict.

## Qualification fixtures

Before production use, the adjudicator MUST demonstrate:

- known positive → PASS;
- valid negative → FAIL;
- invalid execution/evidence → INVALID;
- valid but indecisive → UNRESOLVED;
- second adjudication → rejected;
- post-lock semantic mutation → rejected.

## Acceptance criteria

1. Same frozen inputs produce same verdict.
2. Verdict carries exact contract/attempt/evidence hashes.
3. FAIL remains immutable history.
4. INVALID never becomes substantive FAIL.
5. Adjudicator does not launch retries or mutate proof design.
6. GovernanceDisposition cannot overwrite verdict.
7. IndependencePolicy is verified before verdict use when required.

## Dependencies

- **HARD:** [PRD-03 Proof Planner](PRD_03_PROOF_PLANNER.md), [PRD-04 Evidence Graph](PRD_04_EVIDENCE_GRAPH.md)
- **CONDITIONAL/INTEGRATION:** [PRD-07 Execution Protocol](PRD_07_EXECUTION_PROTOCOL.md) supplies execution evidence
- **CROSS_CUTTING:** [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)
- **NORMATIVE:** [Core Semantics](CORE_SEMANTICS.md)

## References

- [MindForge M3 one-shot adjudication](https://github.com/minhtri22/MindForge/blob/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline/m3/IMPLEMENTATION_RESULT.md)
- [GWF Agent Interoperability Foundation](../../docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)
