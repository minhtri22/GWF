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


## Post-remediation semantic audit

The implementation at `49e4c6e787bad65eb86ba84b3dd33c9ebc16d4ae` addresses the original F01–F03 mechanisms, but closure remains blocked by the findings below.

## P3-QA-F04 — HIGH — OPEN — Goal package trusts caller-supplied ProofResult without replaying its exact closure

The package builder checks that ProofResult points at a packaged Proof, but it does not prove that:
- every ProofResult adjudication ref is present in the supplied decision ledger;
- the exact RetryPolicy is present and matches both Proof and ProofResult;
- the ProofResult outcome/reason codes are exactly what P2 `materialize_proof_result` would derive.

A fabricated canonical ProofResult can therefore assert PASS/FAIL independently of the supplied adjudication history.

**Required:** replay materialization from exact packaged Proof + RetryPolicy + ordered Adjudications and require exact ProofResult identity before Claim resolution.

- [ ] RESOLVED

## P3-QA-F05 — HIGH — OPEN — Standalone Library accepts capability manifests without exact backend identity binding

`require_capability` checks only capability status. A manifest for another backend/adapter/runtime could be supplied and authorize standalone operations.

**Required:** bind `backend_type=STANDALONE`, exact standalone backend ID, adapter version, runtime version and no-silent-fallback before capability status is considered.

- [ ] RESOLVED

## P3-QA-F06 — MEDIUM — OPEN — Runtime capability check does not bind exact standalone runtime identity

`require_capabilities` checks availability flags but not runtime ID/version/mode. A foreign RuntimeCapabilityManifest could authorize standalone runtime operations.

**Required:** exact runtime ID/version/mode/persistence identity validation before capability checks.

- [ ] RESOLVED

## P3-QA-F07 — HIGH — OPEN — Capsule source Claim terminality/resolution is not verified from sealed source package

Publication verifies package integrity/type/seal, but does not prove that `source_goal_ref`, `source_claim_ref` and `source_claim_resolution` match the authoritative content inside the sealed GOAL_RESULT package. It also does not fail closed on `UNKNOWN` source Claim resolution.

**Required for the P3 standalone publication path:**
- support only source package types whose semantic verifier is implemented;
- for GOAL_RESULT, parse authoritative GOAL/CLAIM_GRAPH/claim resolution files from the verified package;
- exact source Goal/Claim refs and terminal resolution must match the capsule;
- unsupported source package types fail closed instead of being accepted by seal-string agreement alone.

- [ ] RESOLVED

## Current closure state

`OPEN = 7`

P3 remains **NOT CLOSED** until F01–F07 are all demonstrated resolved on one exact qualified SHA.


## P3-QA-F08 — HIGH — OPEN — Goal Result verifier checks integrity but not independently re-derived semantics

The current `verify_goal_result_package` verifies canonical manifest/seal, member hashes/sizes and required paths, but does not re-derive:

- ProofResult from exact Proof + RetryPolicy + Adjudication history;
- Claim resolutions from exact ClaimResolutionPolicy + ProofResults;
- final Goal verdict from GoalClosureContract;
- claim resolution files against those derived resolutions.

A semantically modified package could therefore be re-manifested/re-sealed and still pass integrity verification.

The heterogeneous `PROOF_GRAPH.json` dependency list also lacks explicit schema-kind tags, preventing an independent verifier from parsing all frozen dependencies without out-of-band type assumptions.

**Required:**

1. write proof/dependency graph entries as explicit `{schema_kind, payload}` records;
2. factor the same deterministic package-state derivation into export and verify paths;
3. record `authorized_stop` in FINAL_VERDICT so STOPPED can be reproduced;
4. `verify_goal_result_package` must parse authoritative objects, replay ProofResult closure, re-resolve Claims, re-evaluate Goal and compare files;
5. GOAL_RESULT capsule publication must use this semantic verifier, not integrity-only verification.

- [ ] RESOLVED

## Updated closure state

`OPEN = 8`

P3 remains **NOT CLOSED**.
