# PRD-05 — Adjudicator

## Purpose

Produce a deterministic, attributable decision for a proof obligation using only its frozen rules and admitted evidence.

## Required outcomes

G2E core MUST distinguish:

- **PASS** — valid evidence satisfies the frozen success rule.
- **FAIL** — valid substantive execution/evidence violates a required success rule.
- **INVALID** — the run cannot answer the claim because execution/evidence/protocol validity failed.
- **UNRESOLVED** — execution is valid but evidence does not support a decisive PASS/FAIL under the frozen rule.

Optional domain-specific verdicts may be mapped on top, but these four meanings are normative.

## One-shot semantics

An adjudication is terminal for a specific proof-obligation execution identity. It cannot be rerun with replacement evidence to obtain a preferred verdict.

If a technically invalid run is repaired, the replacement attempt must preserve the same semantic proof contract or receive a new obligation identity according to the frozen retry/amendment policy.

## No-rescue invariants

After outcome exposure, the adjudicator must reject silent changes to:

- threshold/operator;
- seed/cohort;
- target metric;
- baseline/control;
- refund/budget semantics;
- dataset inclusion/exclusion;
- artifact under test;
- claim semantics.

## Intentional negative qualification

Before production use, the adjudicator itself MUST pass fixtures demonstrating:

- known PASS → PASS;
- known scientific negative → FAIL;
- missing/invalid evidence → INVALID where appropriate;
- ambiguous valid evidence → UNRESOLVED;
- second adjudication attempt → rejected;
- post-lock threshold mutation → rejected.

## Acceptance criteria

1. Same frozen contract + same admitted evidence yields same decision.
2. Decision carries exact contract/evidence hashes.
3. FAIL is preserved as terminal history.
4. INVALID is never presented as scientific FAIL.
5. Adjudicator does not launch retries or mutate proof design.
6. Human override, if allowed, is a separate governance event and never rewrites the machine verdict.

## Dependencies

- [PRD-03 Proof Planner](PRD_03_PROOF_PLANNER.md)
- [PRD-04 Evidence Graph](PRD_04_EVIDENCE_GRAPH.md)
- [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)

## References

- [MindForge M3 — one-shot adjudication and anti-rescue](https://github.com/minhtri22/MindForge/blob/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline/m3/IMPLEMENTATION_RESULT.md)
- [GWF research study lock/no-rescue](../../domains/research.workflow.yaml)
- [GWF Agent Execution status distinction](../../docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)
