# G2E P3 — Standalone Runtime Semantic QA

## Status

**CANDIDATE QA: FAIL / remediation required**

Candidate:

`bfd5764a65cf109f14c66c82f7a9ce21bbe7e7ff`

Candidate workflows:

- P1: `35578640062` — PASS
- P2: `35578640039` — PASS
- P3: `35578640038` — PASS
- P3 fixtures: `16/16 PASS`

Green CI is insufficient until the semantic findings below are resolved.

## P3-QA-F01 — HIGH — OPEN — No canonical ProofResult; package Claim resolution can be caller-asserted

P2 has a deterministic in-memory ProofClosure, but no canonical terminal ProofResult schema/artifact. The current P3 package builder accepts a caller-provided Claim resolution map.

That permits a package caller to assert Claim PASS even if persisted Adjudication is FAIL, violating PRD-12 requirement that Claim resolution links frozen Proof/evidence decisions.

**Required:**

- canonical terminal ProofResult bound to exact Proof, Adjudication history and RetryPolicy;
- P2 materialization from deterministic closure;
- P3 package derives ClaimResolution from exact ProofResults + frozen ClaimResolutionPolicy;
- caller can no longer inject final Claim resolution.

- [ ] RESOLVED

## P3-QA-F02 — HIGH — OPEN — Standalone Library identity/capability contract is incomplete

PRD-17 requires query result publication IDs + exact subject hashes and capability-qualified backend selection.

Current schema/query execution carries subject refs but not publication IDs, and standalone adapter operations can be invoked without proving the requested LibraryCapabilityManifest capabilities are QUALIFIED.

**Required:**

- LibrarySnapshot binds publication IDs aligned with subject refs;
- LibraryQueryExecution binds result publication IDs aligned with subject refs;
- publish/query/snapshot/provenance/integrity operations fail closed unless exact standalone LibraryCapabilityManifest marks required capabilities QUALIFIED;
- QueryContract.required_capability_ids enforced.

- [ ] RESOLVED

## P3-QA-F03 — HIGH — OPEN — Capsule publication does not independently verify source package

Current publish path checks capsule/contract seal strings agree, but does not itself verify the referenced source package manifest/seal. A fabricated 64-byte seal value could be published.

**Required:**

- PackageSeal binds source package type;
- generic result-package verifier verifies canonical manifest/seal and package-type required structure;
- standalone publication calls verifier on exact source package before publication;
- capsule source package type and seal hash must match the verified PackageSeal.

- [ ] RESOLVED

## Existing-debt verification

The P1.1 DecisionRule gap remains closed in the candidate:

- ProofObligation persists exact DecisionRule ref;
- adjudicator persists exact DecisionRule hash;
- P3 restart fixture preserves both;
- PROOF_GRAPH export includes frozen DecisionRule content.

This invariant must remain green after remediation.

## Verdict

`OPEN = 3`

**P3 NOT CLOSED.**
