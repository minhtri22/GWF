# PRD-06 — Next-Step Selector

## Purpose

Select the next scientifically/technically admissible proof after every adjudication by recomputing the gap between the current evidence graph and final goal closure.

This component formalizes the recurring question:

> **What remains unproven, and what is the smallest valid next proof?**

## Inputs

- frozen Goal Contract;
- current Claim Graph;
- Proof Obligation registry;
- Evidence Graph;
- latest adjudications;
- resource/freshness state;
- user authority constraints;
- optional cost/time preferences.

## Selection algorithm

The selector MUST:

1. exclude claims already terminally satisfied unless replication/reconfirmation is explicitly required;
2. exclude BLOCKED claims whose hard prerequisites are not PASS;
3. identify READY claims with sufficient prerequisites;
4. obtain or validate one or more candidate Proof Obligations;
5. reject candidates that consume protected resources prematurely;
6. reject candidates that silently modify failed lineage;
7. rank only among **admissible** candidates;
8. record why the chosen proof is admissible and why alternatives were deferred.

The default ranking SHOULD prefer:

- prerequisite-enabling claims;
- high information gain;
- lower complexity/cost;
- smaller/faster falsifiable fixtures;
- lower freshness consumption;
- reuse of qualified external tooling.

User policy may override ranking among admissible candidates, but may not authorize an inadmissible proof without a governed amendment.

## PASS behavior

A PASS does not imply “continue to the next numbered phase.” It triggers a graph recomputation.

Example:

```text
checkpoint-resume PASS
  ↓
newly READY:
  evaluation-governance
  runtime-export
  security-contract

selector:
  evaluation-governance first
  because runtime-export depends on evaluation identity
```

## FAIL behavior

A FAIL must remain terminal for the tested obligation.

The selector MAY propose:

- close branch;
- open a new hypothesis/claim;
- design an upstream decomposition study;
- stop goal as falsified.

It MUST NOT propose “same study with easier threshold” as an equivalent retry.

## INVALID behavior

INVALID may authorize repair only if semantic proof identity remains unchanged and the frozen retry policy permits it. Otherwise create a new proof obligation.

## Acceptance criteria

1. Selector never chooses a claim with unsatisfied hard dependencies.
2. Selector recomputes after every adjudication/evidence invalidation.
3. Protected resources cannot be selected before eligibility.
4. FAIL cannot be hidden by selecting a modified equivalent obligation under the same identity.
5. Selection rationale is persisted and attributable.
6. Deterministic policy inputs produce a stable admissible set even if an agent proposes different wording.

## Dependencies

- [PRD-02 Claim Graph](PRD_02_CLAIM_GRAPH.md)
- [PRD-03 Proof Planner](PRD_03_PROOF_PLANNER.md)
- [PRD-04 Evidence Graph](PRD_04_EVIDENCE_GRAPH.md)
- [PRD-05 Adjudicator](PRD_05_ADJUDICATOR.md)
- [PRD-13 Reference Acquisition](PRD_13_REFERENCE_ACQUISITION.md) when novelty/prior art changes admissibility.

## References

- [G2E README — governing rules](../README.md)
- [GWF 7-Wave dependency/complexity selection rule](../../docs/IMPLEMENTATION_7_WAVES_PLAN.md)
- [MindForge M4 result and next-step logic](https://github.com/minhtri22/MindForge/blob/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline/m4/IMPLEMENTATION_RESULT.md)
