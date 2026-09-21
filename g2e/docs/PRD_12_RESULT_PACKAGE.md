# PRD-12 — Goal Result Package

## Purpose

Produce the final auditable artifact bundle showing what the user asked for, what G2E proved or failed to prove, the evidence lineage, and the actual output artifacts.

## Required structure

A canonical package SHOULD contain:

```text
GOAL_RESULT/
├── GOAL.json
├── CLAIM_GRAPH.json
├── PROOF_GRAPH.json
├── EVIDENCE_GRAPH.json
├── DECISION_LEDGER.json
├── LINEAGE.json
├── FINAL_VERDICT.json
├── REPRODUCIBILITY_MANIFEST.json
├── claims/
│   └── <claim-id>/
│       ├── CONTRACT.json
│       ├── ADJUDICATION.json
│       └── evidence/
└── outputs/
    └── domain-specific artifacts
```

Large binaries may be referenced by immutable content-addressed identity rather than copied.

## Final verdict

The package MUST state:

- goal revision/hash;
- achieved / falsified / unresolved / stopped state;
- which terminal goal claims are PASS;
- which claims are FAIL/INVALID/UNRESOLVED;
- limitations;
- unsupported claims explicitly not made;
- reproducibility scope;
- authoritative source/evidence identities.

A partially achieved goal must not be summarized as achieved.

## Reproducibility manifest

The manifest records enough identity to replay or audit:

- framework version;
- runtime adapter/version;
- source revisions;
- proof contracts;
- data/artifact hashes;
- tool/provider versions where material;
- execution environment classes;
- agent binding identities;
- evidence digests.

## Human-readable report

A generated report may summarize the package, but JSON/structured authoritative artifacts remain the source of truth.

## Acceptance criteria

1. Package closure is derived from Claim Graph terminal mapping, not narrative judgment.
2. Every claimed result links to evidence/adjudication.
3. Package can be verified offline except explicitly external immutable references.
4. Missing binary artifacts are detectable.
5. Unsupported/failed claims remain visible.
6. Re-generating the human report cannot change the formal verdict.

## Dependencies

- [PRD-01 Goal Contract](PRD_01_GOAL_CONTRACT.md)
- [PRD-02 Claim Graph](PRD_02_CLAIM_GRAPH.md)
- [PRD-03 Proof Planner](PRD_03_PROOF_PLANNER.md)
- [PRD-04 Evidence Graph](PRD_04_EVIDENCE_GRAPH.md)
- [PRD-05 Adjudicator](PRD_05_ADJUDICATOR.md)
- [PRD-06 Next-Step Selector](PRD_06_NEXT_STEP_SELECTOR.md)

## References

- [GWF handoff package model](../../domains/research.workflow.yaml)
- [MindForge M2 evidence package](https://github.com/minhtri22/MindForge/tree/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline/m2)
- [MindForge M4 evidence package](https://github.com/minhtri22/MindForge/tree/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline/m4)
