# G2E P3 Preflight — Schema Dependency Findings

## Status

**BLOCKING SCHEMA FINDINGS — resolve before Standalone Runtime implementation.**

## Baseline

- P1.1 qualified schema: `0002790f0ea3da1c6e03b69124e3bfd38741b3b5`
- P2 qualified core: `c2fc03a7470b835904252246421e1b8d9a1ec5ef`
- current branch: `a4d4601db84ac6496e70569320b629cf23f0dd73`

## Debt verification from prior turn

The prior P1 DecisionRule gap is **closed**:

- every ProofObligation now requires exact `decision_rule_ref`;
- P2 adjudicator requires the supplied DecisionRule exact-ref to match the frozen ProofObligation;
- Adjudication stores the exact DecisionRule content hash;
- post-outcome rule/proof mutation is rejected by P2 no-rescue enforcement.

No P3 workaround is permitted for this boundary.

## P3-F01 — HIGH — OPEN — RuntimeCapabilityManifest missing from canonical schema surface

PRD-11 requires a RuntimeCapabilityManifest and fail-closed handling of unsupported governance capabilities. P1 has LibraryCapabilityManifest but no runtime capability object.

**Required:** add canonical RuntimeCapability / RuntimeCapabilityManifest schemas before P3 runtime selection/execution.

- [ ] RESOLVED

## P3-F02 — HIGH — OPEN — Provider-neutral ExecutionResult missing from canonical schema surface

PRD-07 defines a normalized ExecutionResult distinct from ExecutionAttempt state. P1 only materialized ExecutionAttemptEnvelope. A standalone executor facade would otherwise create an ad-hoc runtime-only result contract that P4 could later reinterpret.

**Required:** add canonical ExecutionResult schema bound to exact attempt identity, terminal executor state, artifacts/candidate-evidence refs, technical failure and redaction metadata.

- [ ] RESOLVED

## P3-F03 — HIGH — OPEN — Result-package manifest/seal integrity objects are not schema-bound

Core Semantics §14 and PRD-12 require PACKAGE_MANIFEST and PACKAGE_SEAL with non-circular hashing and independent verification. P1 contains PackageMember and ClaimResultPackage summary hashes, but no canonical manifest/seal contract.

**Required:** add canonical PackageManifest and PackageSeal schemas that:
- exclude manifest/seal from member entries;
- require sorted unique member paths;
- bind exact manifest identity and exact manifest-file SHA-256;
- bind framework/runtime identity;
- preserve explicit external-reference verification policy.

- [ ] RESOLVED

## Verdict

`OPEN = 3`

**P3 runtime code remains blocked until these schema dependencies requalify P1.**
