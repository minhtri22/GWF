# G2E P2 — Deterministic Core Implementation QA

## Status

**DETERMINISTIC CORE QA: PASS**

Candidate implementation:

`3a231c2064b28b718124990ec332d660cafc56a8`

Candidate CI:

- P2 workflow `35573334923` — success
- P1 regression workflow `35573334853` — success
- P1 fixtures: 23/23 PASS
- P2 fixtures: 37/37 PASS
- forbidden runtime dependency check: PASS

Green CI is not sufficient for closure until the semantic findings below are resolved.

## Findings

### P2-F02 — HIGH — RESOLVED — Adjudicator can consume evidence without proving exact admission provenance

The current adjudicator checks `EvidenceRecord.lifecycle == ADMITTED` but a fixture/caller can construct an ADMITTED record without binding the exact `EvidenceAdmissionPolicy` frozen by the ProofObligation.

It also does not enforce exact producer-attempt binding at adjudication time when the frozen admission policy requires it.

**Required:**

- materialize admission as a new canonical EvidenceRecord revision carrying exact `admission_policy_ref` and reason;
- adjudicator must reject/fail-closed when admitted evidence does not bind the proof's exact admission policy;
- when the frozen policy requires attempt linkage, producer attempt must equal the adjudicated attempt;
- `admitted_evidence_refs` must contain only records actually verified as admitted.

- [x] RESOLVED

### P2-F03 — HIGH — RESOLVED — IndependencePolicy is not fail-closed at adjudication

PRD-05 requires IndependencePolicy to be verified before verdict use when required. The candidate checks independence during proof selection/admissibility but adjudicator can be called directly without an independence-verification state.

**Required:** adjudicator must require explicit verified independence when the ProofObligation binds an IndependencePolicy; missing/false verification produces INVALID rather than a substantive PASS/FAIL.

- [x] RESOLVED

### P2-F04 — MEDIUM — RESOLVED — Direct proof-admissibility API does not verify exact RetryPolicy identity

`select_next_proof` resolves the exact RetryPolicy ref, but direct `check_proof_admissibility` accepts any RetryPolicy object.

**Required:** exact retry policy ref mismatch must fail admissibility.

- [x] RESOLVED

## Verdict

OPEN = 0`

## Remediation evidence

Qualified implementation under final QA:

`c2fc03a7470b835904252246421e1b8d9a1ec5ef`

Authoritative workflows:

- P2 deterministic core: run `35573628326`, job `106250444186` — PASS
- P1 schema regression: run `35573628248`, job `106250444424` — PASS

Final fixture counts:

- P1 schema regression: `23/23 PASS`
- P2 deterministic core: `41/41 PASS`
- compileall: PASS
- forbidden runtime dependency assertion: PASS

Resolved enforcement:

- F02: canonical admission materialization binds exact EvidenceAdmissionPolicy; adjudicator verifies policy and producer-attempt linkage; only verified admitted refs enter Adjudication.
- F03: bound IndependencePolicy requires explicit verified independence; missing/false verification yields INVALID.
- F04: direct proof admissibility rejects RetryPolicy ref mismatch.

## Final P2 exit checklist

- [x] ClaimGraph / GoalClosure validation
- [x] Proof admissibility
- [x] Evidence admission + relation validation
- [x] protected-resource freshness state machine
- [x] deterministic attempt adjudicator
- [x] Proof closure / bounded INVALID retry
- [x] multiple-proof Claim resolver
- [x] alternate-path Goal evaluator
- [x] deterministic Next-Step admissible set
- [x] SelectionPolicy ranking + lexical tie-break
- [x] amendment/no-rescue enforcement
- [x] PASS / FAIL / INVALID / UNRESOLVED fixtures
- [x] applicability / reuse engine
- [x] prior PASS cannot directly flip current Claim
- [x] provenance overlap / independence clustering
- [x] dependent capsules are not counted as independent confirmation
- [x] synthesis universe dedup / inclusion
- [x] outcome-blind synthesis gate
- [x] coverage/publication-bias constraint
- [x] boundary-regime classification
- [x] synthesis transitive ancestry validation
- [x] synthesis post-outcome no-rescue
- [x] no agent
- [x] no DB/persistence
- [x] no standalone runtime
- [x] no GWF adapter
- [x] no GAC/P4L

## Verdict

**G2E P2 — DETERMINISTIC CORE ENGINE: PASS**

`OPEN = 0`

P3 — Standalone Runtime is the next phase allowed by the G2E phase plan. P4/P4L remain closed.
