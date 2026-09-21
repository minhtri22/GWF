# PRD-12 — Goal Result Package

## Purpose

Produce a final auditable package showing the frozen goal, Claim/Proof/Evidence lineage, formal Goal verdict, limitations and actual outputs.

## Canonical structure

```text
GOAL_RESULT/
├── GOAL.json
├── GOAL_CLOSURE.json
├── CLAIM_GRAPH.json
├── PROOF_GRAPH.json
├── EVIDENCE_GRAPH.json
├── DECISION_LEDGER.json
├── PACKAGE_LINEAGE.json
├── FINAL_VERDICT.json
├── REPRODUCIBILITY_MANIFEST.json
├── PACKAGE_MANIFEST.json
├── PACKAGE_SEAL.json
├── library/
│   ├── EVIDENCE_CAPSULE.json
│   └── IMPORTS.json
├── synthesis/
│   └── SYNTHESIS_RESULT.json
├── claims/
│   └── <claim-id>/
│       ├── CONTRACT.json
│       ├── RESOLUTION.json
│       └── evidence/
└── outputs/
    └── domain-specific artifacts
```

`PACKAGE_LINEAGE.json` is the machine event lineage for this result package and is distinct from repository project-level `g2e/LINEAGE.md`.

Large binaries may be represented by immutable content-addressed references.

`EVIDENCE_CAPSULE.json` is an optional publishable derivative of the sealed Goal Result Package and binds `PACKAGE_SEAL.json`; it does not replace the source package.

For synthesis Goals, `SYNTHESIS_RESULT.json` binds SynthesisContract, universe, inclusion/exclusion, provenance clusters and transitive ancestry.

## Final verdict

Normative Goal verdicts are:

- ACHIEVED;
- FALSIFIED;
- UNRESOLVED;
- STOPPED.

INVALID is an attempt-level Adjudication verdict and does not itself become a Goal verdict.

Final verdict derives only from the frozen GoalClosureContract and governed stop policy. Partial achievement cannot be summarized as ACHIEVED.

## Integrity

Package integrity follows [Core Semantics §14](CORE_SEMANTICS.md):

- PACKAGE_MANIFEST lists authoritative content hashes/sizes, excluding manifest/seal;
- PACKAGE_SEAL hashes the canonical manifest and records framework/runtime/attestation identity;
- verification fails on missing/changed/unclassified authoritative content;
- external-reference verification policy is explicit.

No circular self-hash is permitted.

## Reproducibility manifest

Record:

- G2E core/schema versions;
- runtime/adapter versions;
- source revisions;
- proof/decision policy hashes;
- data/artifact/resource hashes;
- tool/provider versions where material;
- environment classes;
- agent-binding identities;
- evidence digests.

## Acceptance criteria

1. Goal verdict derives from GoalClosureContract, not prose.
2. Every Claim resolution links frozen Proof/evidence decisions.
3. Failed/unresolved/unsupported Claims remain visible.
4. Package seal detects mutation.
5. Missing required external/binary refs are detectable under verification policy.
6. Human report regeneration cannot alter formal verdict.
7. Runtime migration does not change package semantic identities.
8. Optional EvidenceCapsule binds exact package seal and preserves negative/unresolved source verdicts.
9. Imported prior evidence and synthesis ancestry are explicitly listed.

## Dependencies

- **HARD:** PRD-01 through PRD-06
- **CROSS_CUTTING:** [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)
- **NORMATIVE:** [Core Semantics](CORE_SEMANTICS.md)

## References

- [GWF research handoff model](../../domains/research.workflow.yaml)
- [MindForge evidence root](https://github.com/minhtri22/MindForge/tree/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline)
