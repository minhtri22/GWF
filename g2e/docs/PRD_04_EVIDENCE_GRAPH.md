# PRD-04 — Evidence Graph

## Purpose

Represent what has actually been observed, which exact execution produced it, and which claims it can or cannot support.

## Core distinction

Evidence is not narrative. A claim cannot become PASS because an agent says “looks good.” G2E requires attributable evidence.

## Evidence node

Each evidence record MUST include:

- `evidence_id`;
- evidence type/class;
- producer execution/attempt identity;
- source commit/artifact/config hashes as applicable;
- subject claim/proof-obligation IDs;
- timestamp;
- environment/resource identity;
- payload digest or immutable external reference;
- trust class;
- freshness/protection classification;
- redaction/security metadata;
- validity status;
- supersession relation if applicable.

## Evidence graph relations

Minimum relations:

- `PRODUCED_BY`
- `SUPPORTS`
- `FALSIFIES`
- `VALIDATES`
- `DERIVED_FROM`
- `REPRODUCES`
- `CONFLICTS_WITH`
- `SUPERSEDES`

An evidence record may be valid while not sufficient for a claim. Evidence validity and claim sufficiency are separate.

## Freshness

Protected evidence/resources must preserve exposure state. Once a confirmatory result is inspected, it cannot be treated as fresh in a later obligation.

## Negative evidence

FAIL/negative results remain first-class graph nodes. New evidence may create a new claim or proof lineage, but must not erase prior negative evidence.

## Acceptance criteria

1. Evidence identity is reconstructable from exact inputs/references.
2. Same evidence cannot be reclassified as fresh after exposure.
3. Evidence invalidation propagates to dependent claim sufficiency without deleting history.
4. Redacted evidence remains attributable without persisting secrets.
5. Standalone and GWF adapters expose the same logical graph semantics.
6. Conflicting evidence is represented, not silently resolved by last-write-wins.

## Dependencies

- [PRD-02 Claim Graph](PRD_02_CLAIM_GRAPH.md)
- [PRD-03 Proof Planner](PRD_03_PROOF_PLANNER.md)
- [PRD-07 Execution Protocol](PRD_07_EXECUTION_PROTOCOL.md) for producer identities.
- [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)

## References

- [GWF Documentation Integrity & Governance](../../docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md)
- [GWF research experiment/evidence artifacts](../../domains/research.workflow.yaml)
- [MindForge M3 evidence](https://github.com/minhtri22/MindForge/blob/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline/m3/M3_QUALIFICATION_EVIDENCE.json)
