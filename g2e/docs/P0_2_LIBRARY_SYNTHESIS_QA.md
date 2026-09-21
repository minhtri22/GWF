# G2E P0.2 — Evidence Reuse & Convergence Documentation QA

## Status

**Candidate QA — pending.**

## Scope extension

P0.1 PASS covered single-Goal proof semantics. P0.2 adds:

- reusable EvidenceCapsules;
- ClaimSignature / ApplicabilityAssessment;
- qualified reuse without bypassing ProofObligation;
- provenance overlap / anti-double-counting;
- SynthesisContract and convergence semantics;
- Evidence Library Adapter with GWF GAC default backend.

P1 Core Schemas is re-blocked until P0.2 QA PASS.

## Checklist

- [ ] Prior result cannot directly set current Claim PASS.
- [ ] QUALIFIED_REUSE flows through Reuse ProofObligation + EvidenceAdmission.
- [ ] FAIL/UNRESOLVED results can be published; no positive-result selection bias.
- [ ] Library evidence never becomes FRESH again.
- [ ] Applicability binds exact source/target/policy.
- [ ] Shared provenance prevents false independence/double counting.
- [ ] Synthesis universe/inclusion rules freeze prospectively.
- [ ] Excluded candidates and reasons remain observable.
- [ ] Search ranking cannot redefine synthesis universe post-lock.
- [ ] ConvergenceClassification is separate from Adjudication and GoalVerdict.
- [ ] Synthesis result keeps transitive source ancestry.
- [ ] Library adapter does not own applicability/synthesis semantics.
- [ ] GWF GAC is default backend; standalone remains supported.
- [ ] Query failure cannot masquerade as zero results.
- [ ] G2E docs reference the GWF GAC packing-only contract, not unimplemented APIs as if production-ready.
- [ ] P1/P2 phase plan includes new schemas/engines before implementation.

## Findings

Pending.

## Verdict

Pending.
