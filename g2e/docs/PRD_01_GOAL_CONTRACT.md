# PRD-01 — Goal Contract

## Purpose

Convert an unstructured user goal into a versioned, reviewable, machine-readable contract without prematurely deciding the implementation path.

A Goal Contract answers: **what outcome does the user want, under what constraints, and what would make the goal terminal?**

## User problem

A solo researcher often begins with a sentence such as:

> “Build a small model that learns domain knowledge, exposes a reasoning rationale, runs locally, and is reproducible.”

If execution begins directly from prose, agents can silently change scope, success criteria, runtime targets, cost limits, or evidence expectations. G2E must establish a stable goal identity before claim decomposition.

## Required capabilities

The Goal Contract MUST contain:

- `goal_id` and revision identity;
- user-authored goal statement;
- desired outputs;
- explicit constraints and non-goals;
- target environments/runtimes when known;
- acceptable terminal outcomes;
- resource/privacy/locality constraints;
- required confidence/evidence class when specified;
- unresolved ambiguities;
- amendment policy;
- authority/approval metadata.

The contract MUST distinguish:

- **goal semantics** from implementation choices;
- **hard constraints** from preferences;
- **success outputs** from proof requirements;
- **unknown** from “not required.”

## Lifecycle

```text
DRAFT → REVIEWED → FROZEN
                  ↓
             AMENDED*
```

A semantic amendment after evidence exposure creates a new goal revision and may require a new lineage. The framework must never silently rewrite the original goal to match observed results.

## Input / output

Input:
- user natural-language goal;
- optional files/specifications;
- optional GWF project context.

Output:
- canonical `GoalContract`;
- unresolved-question list;
- goal hash;
- amendment class.

## Acceptance criteria

1. Same canonical content produces same goal hash.
2. Implementation-specific suggestions can change without changing goal semantics.
3. Semantic changes produce a new revision/hash.
4. Goal cannot become `FROZEN` while blocking ambiguities remain.
5. Agent proposal is not authoritative until accepted by the configured authority policy.
6. Standalone and GWF modes produce equivalent canonical Goal Contract content.

## Non-goals

- generating the claim graph;
- choosing tools or agents;
- executing research;
- deciding PASS/FAIL.

## Dependencies

- None inside G2E core.
- Cross-cutting authority semantics: [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md).

## References

- [G2E README](../README.md)
- [GWF research goal artifact](../../domains/research.workflow.yaml)
- [GWF Agent Interoperability Foundation](../../docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)
- [MindForge evidence root](https://github.com/minhtri22/MindForge/tree/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline)
