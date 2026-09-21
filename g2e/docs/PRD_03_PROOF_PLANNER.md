# PRD-03 — Proof Obligation Planner

## Purpose

Turn a READY Claim into one or more explicit ProofObligation candidates without consuming protected outcomes prematurely.

Validity and minimality are separate: a proof is first checked for admissibility; ranking/minimality is handled by SelectionPolicy.

## ProofObligation

A ProofObligation MUST freeze:

- `proof_id`, revision/hash and target Claim ID;
- exact proposition under test;
- prerequisites/assumptions;
- intervention if any;
- controls/baselines;
- fixture/population/cohort identity;
- evidence requirements and EvidenceAdmissionPolicy;
- metrics/decision rules using canonical decimal-string thresholds where needed;
- PASS/FAIL/INVALID/UNRESOLVED semantics;
- protected-resource/freshness policy;
- implementation/tool identity requirements;
- execution identity requirements;
- RetryPolicy;
- AmendmentPolicy;
- IndependencePolicy if required;
- estimated `protected_resource_cost`;
- estimated `resource_cost_class`;
- estimated `implementation_complexity`;
- bounded stop conditions.

Proof lifecycle and attempt closure rules are normative in [Core Semantics §2.5 and §3](CORE_SEMANTICS.md).

## Planning rules

1. All HARD Claim prerequisites must be PASS before authorization.
2. Prefer fixture-scale qualification when it can falsify the mechanism.
3. Protected/fresh resources are not debugging resources.
4. Engineering qualification and scientific improvement are separate ProofObligations.
5. Use intentional negative fixtures where needed to qualify adjudication/no-rescue behavior.
6. Reuse mature external implementations and qualify them before rebuilding.
7. A planner may propose multiple candidates; it does not choose an inadmissible candidate.

## Minimality

“Smallest” is not a proof-validity claim. The planner records normalized resource/complexity/freshness estimates; [PRD-06](PRD_06_NEXT_STEP_SELECTOR.md) ranks admissible candidates under a frozen SelectionPolicy.

## Frozen boundary

At `PROOF_FROZEN`, semantic proof identity becomes immutable. Changes listed in [Core Semantics §3.1/§9](CORE_SEMANTICS.md) create a new proof revision/lineage and are never infrastructure retries.

## Acceptance criteria

1. Exactly one primary target Claim per ProofObligation.
2. HARD prerequisites PASS before authorization.
3. Evidence/adjudication/resource/retry policies freeze before protected outcome access.
4. Proof and ExecutionAttempt identities are separate.
5. Planner emits normalized ranking estimates rather than untestable “minimality” prose only.
6. Baseline/cohort/resource identities are exact and non-stale.
7. Independence requirements are prospective when used.

## Dependencies

- **HARD:** [PRD-01 Goal Contract](PRD_01_GOAL_CONTRACT.md), [PRD-02 Claim Graph](PRD_02_CLAIM_GRAPH.md)
- **CONDITIONAL:** [PRD-13 Reference Acquisition](PRD_13_REFERENCE_ACQUISITION.md) when external evidence informs design
- **CROSS_CUTTING:** [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)
- **NORMATIVE:** [Core Semantics](CORE_SEMANTICS.md)

## References

- [GWF research study-lock model](../../domains/research.workflow.yaml)
- [MindForge M2 exact-resume reference](https://github.com/minhtri22/MindForge/blob/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline/m2/IMPLEMENTATION_RESULT.md)
