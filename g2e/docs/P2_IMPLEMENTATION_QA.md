# G2E P2 — Deterministic Core Implementation QA

## Status

**CANDIDATE QA: FAIL / remediation required**

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

### P2-F02 — HIGH — OPEN — Adjudicator can consume evidence without proving exact admission provenance

The current adjudicator checks `EvidenceRecord.lifecycle == ADMITTED` but a fixture/caller can construct an ADMITTED record without binding the exact `EvidenceAdmissionPolicy` frozen by the ProofObligation.

It also does not enforce exact producer-attempt binding at adjudication time when the frozen admission policy requires it.

**Required:**

- materialize admission as a new canonical EvidenceRecord revision carrying exact `admission_policy_ref` and reason;
- adjudicator must reject/fail-closed when admitted evidence does not bind the proof's exact admission policy;
- when the frozen policy requires attempt linkage, producer attempt must equal the adjudicated attempt;
- `admitted_evidence_refs` must contain only records actually verified as admitted.

- [ ] RESOLVED

### P2-F03 — HIGH — OPEN — IndependencePolicy is not fail-closed at adjudication

PRD-05 requires IndependencePolicy to be verified before verdict use when required. The candidate checks independence during proof selection/admissibility but adjudicator can be called directly without an independence-verification state.

**Required:** adjudicator must require explicit verified independence when the ProofObligation binds an IndependencePolicy; missing/false verification produces INVALID rather than a substantive PASS/FAIL.

- [ ] RESOLVED

### P2-F04 — MEDIUM — OPEN — Direct proof-admissibility API does not verify exact RetryPolicy identity

`select_next_proof` resolves the exact RetryPolicy ref, but direct `check_proof_admissibility` accepts any RetryPolicy object.

**Required:** exact retry policy ref mismatch must fail admissibility.

- [ ] RESOLVED

## Verdict

`OPEN = 3`

**P2 NOT CLOSED.**
