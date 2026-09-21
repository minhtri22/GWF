# PRD-02 — Claim Compiler & Claim Graph

## Purpose

Derive the propositions that must be supported before G2E may claim the Goal Contract is achieved, and represent their hard dependencies explicitly.

## Core idea

G2E must not hard-code project-specific stages such as M0→M8. It must derive claims from the goal.

Example:

```text
Goal: deploy a reproducible reasoning model locally
  ↓
C1 data identity is fixed
C2 training can recover exactly
C3 evaluation cannot be rescued post hoc
C4 reasoning representation is well-defined
C5 canonical model artifact is loadable
C6 conversion preserves required behavior
C7 target runtime preserves required semantics
```

## Claim model

Each claim MUST include:

- `claim_id`;
- proposition;
- claim class: functional / scientific / quality / safety / reproducibility / compatibility / governance;
- scope;
- assumptions;
- hard prerequisite claim IDs;
- supporting-evidence policy;
- falsification semantics;
- terminal relevance to the parent goal;
- status;
- derivation provenance;
- compiler version/agent proposal identity.

Recommended states:

`UNKNOWN | BLOCKED | READY | RUNNING | PASS | FAIL | INVALID | UNRESOLVED | SUPERSEDED`.

## Compiler behavior

The Claim Compiler MAY use an LLM/agent to propose decomposition, but the resulting graph must pass deterministic validation:

- no unknown dependencies;
- no forbidden cycles;
- all terminal goal requirements mapped to at least one claim;
- no claim with unfalsifiable PASS semantics when evidence is required;
- assumptions explicit;
- duplicate or semantically overlapping claims surfaced for review;
- claims that are merely implementation tasks must not masquerade as outcome claims.

## Minimality

The compiler SHOULD prefer the smallest sufficient claim set. New claims may be added when evidence exposes a previously unknown prerequisite, but the addition must have explicit lineage and may not retroactively convert an old FAIL into PASS.

## Acceptance criteria

1. Every required goal outcome has a claim path.
2. Hard dependency graph is acyclic or contains only explicitly allowed fixed-point structures.
3. Claims can be serialized and hashed canonically.
4. Agent-generated claims are attributable.
5. Graph mutation after locked downstream execution is classified and governed.
6. “PASS all leaves” alone is insufficient; final goal closure must evaluate the explicit terminal mapping.

## Dependencies

- [PRD-01 Goal Contract](PRD_01_GOAL_CONTRACT.md)
- Cross-cutting [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)

## References

- [G2E README — governing meta-rules](../README.md)
- [GWF research hypothesis/protocol structure](../../domains/research.workflow.yaml)
- [MindForge M3 governance result](https://github.com/minhtri22/MindForge/blob/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline/m3/IMPLEMENTATION_RESULT.md)
