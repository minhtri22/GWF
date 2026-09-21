# PRD-03 — Proof Obligation Planner

## Purpose

Turn a READY claim into the smallest admissible, falsifiable proof obligation that can update confidence/state without consuming resources prematurely.

## Proof obligation

A `ProofObligation` MUST define:

- target claim ID;
- exact proposition under test;
- prerequisites and assumptions;
- intervention, if any;
- controls/baselines;
- fixture or population;
- evidence required;
- metrics and decision rules;
- PASS / FAIL / INVALID / UNRESOLVED semantics;
- fresh/protected resource policy;
- implementation/tool requirements;
- execution identity requirements;
- retry/amendment policy;
- estimated resource class;
- stop conditions.

## Planning rules

1. Prefer fixture-scale qualification before full-scale execution when the fixture can falsify the mechanism.
2. Do not consume fresh/confirmatory resources to debug harness or plumbing.
3. Reuse mature implementations when possible; qualify them rather than rebuild them.
4. A proof for an engineering mechanism and a proof for scientific improvement are different obligations.
5. Forced-negative or intentional-FAIL fixtures SHOULD be used where needed to prove the adjudicator cannot silently rescue failure.
6. The planner may propose multiple admissible proofs; the selector or human authority chooses among them.

## Example

For claim `training_is_recoverable`:

```yaml
intervention: forced_interrupt_after_step_1
control: uninterrupted_reference
evidence:
  - mutable_weights
  - optimizer_state
  - scheduler_state
  - rng_state
  - data_cursor
pass: resumed_final_state == uninterrupted_final_state
fail: valid_run_and_any_required_state_differs
invalid: execution_never_reached_comparison
```

## Frozen boundary

A proof obligation becomes immutable when execution is authorized. Outcome-dependent changes to thresholds, data, seeds, comparator, target, or semantics require a new obligation/lineage unless a prospective amendment rule explicitly permits them.

## Acceptance criteria

1. Every proof obligation references exactly one primary target claim.
2. All hard prerequisites are PASS before authorization.
3. Evidence sufficiency and adjudication rules are fixed before protected outcome access.
4. Technical validation can be separated from substantive execution.
5. Planner records why the selected proof is minimal/admissible.
6. No obligation can silently inherit stale baseline or resource identities.

## Dependencies

- [PRD-01 Goal Contract](PRD_01_GOAL_CONTRACT.md)
- [PRD-02 Claim Graph](PRD_02_CLAIM_GRAPH.md)
- [PRD-13 Reference Acquisition](PRD_13_REFERENCE_ACQUISITION.md) when external evidence informs proof design.

## References

- [GWF study_lock](../../domains/research.workflow.yaml)
- [GWF Reference Acquisition Specification](../../docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md)
- [MindForge M2 exact-resume evidence](https://github.com/minhtri22/MindForge/blob/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline/m2/IMPLEMENTATION_RESULT.md)
- [MindForge M3 governance evidence](https://github.com/minhtri22/MindForge/blob/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline/m3/IMPLEMENTATION_RESULT.md)
