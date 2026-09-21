# PRD-01 — Goal Contract

## Purpose

Convert an unstructured user goal into a versioned, reviewable, machine-readable contract without prematurely deciding implementation or Claim IDs.

## Required contract

A GoalContract MUST contain:

- `goal_id`, revision, schema version and canonical hash;
- user-authored goal statement;
- stable `goal_requirement_id` records;
- desired outputs;
- hard constraints and explicit non-goals;
- preferences separated from hard constraints;
- target environments/runtimes when known;
- resource/privacy/locality constraints;
- acceptable governance stop conditions;
- ambiguity records;
- AmendmentPolicy reference;
- authority/approval metadata.

Each ambiguity record MUST contain:

- ambiguity ID;
- description;
- `blocking: true|false`;
- owner/resolution authority;
- resolution/disposition when closed.

GoalContract MUST NOT refer to Claim IDs. Claims are generated later from the frozen GoalContract.

## Lifecycle

Normative lifecycle is defined in [Core Semantics §2.1](CORE_SEMANTICS.md):

`DRAFT → REVIEWED → FROZEN → SUPERSEDED`.

A GoalContract cannot become FROZEN while any blocking ambiguity remains unresolved.

Normative amendments follow [Core Semantics §9](CORE_SEMANTICS.md). Post-outcome normative changes never rewrite the old lineage.

## Output

The component emits:

- canonical GoalContract;
- goal hash;
- unresolved ambiguity list;
- amendment classification.

Claim compilation later creates a GoalClosureContract bound to this exact GoalContract revision.

## Acceptance criteria

1. Same canonical semantic content produces the same hash under Core Semantics.
2. Implementation suggestions can change without changing frozen goal semantics.
3. Normative changes create a new revision and follow amendment/lineage rules.
4. Blocking ambiguities prevent FROZEN.
5. Agent proposals are non-authoritative until approved.
6. Standalone/GWF modes preserve canonical GoalContract IDs/hashes.
7. GoalContract contains stable requirements sufficient for later Claim coverage review without pre-creating Claim IDs.

## Non-goals

- Claim generation;
- GoalClosureContract generation;
- proof planning;
- execution;
- verdict calculation.

## Dependencies

- **CROSS_CUTTING:** [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)
- **NORMATIVE:** [Core Semantics](CORE_SEMANTICS.md)

## References

- [G2E README](../README.md)
- [Reference Baseline](REFERENCE_BASELINE.md)
- [GWF research domain](../../domains/research.workflow.yaml)
