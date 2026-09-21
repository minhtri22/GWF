# PRD-02 — Claim Compiler & Claim Graph

## Purpose

Derive falsifiable propositions from a frozen GoalContract, represent their HARD dependencies, and freeze the GoalClosureContract that maps Claim resolutions back to the user's goal requirements.

## Claim model

Each Claim MUST include:

- `claim_id`, schema/revision/hash;
- proposition;
- descriptive claim class;
- scope and assumptions;
- HARD prerequisite Claim IDs;
- ClaimResolutionPolicy;
- falsification semantics;
- mapped `goal_requirement_id` values;
- lifecycle state;
- resolution state;
- derivation provenance;
- compiler/agent proposal identity.

Claim class is metadata only in v0.x. It does not silently alter verdict semantics unless a future explicit domain policy is bound.

Lifecycle and resolution are separate namespaces in [Core Semantics §2.3–2.4](CORE_SEMANTICS.md).

## ClaimResolutionPolicy

Each terminal Claim MUST freeze either `ALL_REQUIRED` or `ANY_SUFFICIENT` semantics according to [Core Semantics §4](CORE_SEMANTICS.md). Multiple proofs/evidence may not resolve a Claim by last-write-wins.

## Graph requirements

The compiler MAY use an LLM/agent to propose decomposition, but the graph MUST pass deterministic validation:

- all IDs/references resolve;
- HARD dependency graph is a DAG in v0.x;
- every Goal requirement has explicit Claim coverage or an explicit unresolved coverage finding;
- implementation tasks do not masquerade as outcome Claims;
- ClaimResolutionPolicy is complete before the Claim can become READY;
- assumptions are explicit;
- duplicates/overlaps are surfaced for review.

Fixed-point/cyclic HARD dependencies are not supported in v0.x.

## GoalClosureContract

Before `CLAIM_GRAPH_FROZEN`, G2E MUST create and review a GoalClosureContract containing:

- exact GoalContract ID/revision/hash;
- exact ClaimGraph ID/revision/hash;
- requirement→Claim mappings;
- success expression;
- falsification expression;
- terminal Claim set;
- authorized stop policy.

Expression semantics are defined in [Core Semantics §5](CORE_SEMANTICS.md).

The ClaimGraph and GoalClosureContract freeze together.

## Completeness boundary

G2E cannot mathematically prove that agent-generated decomposition is globally complete. Therefore freeze requires:

- deterministic structural validation;
- a `coverage_statement`;
- unresolved-risk/unknown list;
- configured authority approval.

Newly discovered prerequisites after outcome exposure follow [Core Semantics §9](CORE_SEMANTICS.md); old results are not rewritten.

## Acceptance criteria

1. Every Goal requirement has mapped coverage or an explicit blocking/unresolved finding.
2. HARD dependency graph is acyclic.
3. Claim lifecycle and Claim resolution are separate.
4. Every terminal Claim has a frozen ClaimResolutionPolicy.
5. GoalClosureContract binds exact GoalContract/ClaimGraph revisions.
6. Agent-generated Claims are attributable and non-authoritative until approved.
7. Post-outcome graph changes create governed new revision/lineage.

## Dependencies

- **HARD:** [PRD-01 Goal Contract](PRD_01_GOAL_CONTRACT.md)
- **CROSS_CUTTING:** [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)
- **NORMATIVE:** [Core Semantics](CORE_SEMANTICS.md)

## References

- [G2E README](../README.md)
- [MindForge M3 governance reference](https://github.com/minhtri22/MindForge/blob/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline/m3/IMPLEMENTATION_RESULT.md)
