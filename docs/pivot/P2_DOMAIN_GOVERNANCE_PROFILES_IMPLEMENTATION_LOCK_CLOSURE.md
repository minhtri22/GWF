# GWF vNext P2 — Domain Governance Profiles Implementation Static Preflight and Execution Lock Closure

**Gate:** `GWF_VNEXT_P2_DOMAIN_GOVERNANCE_PROFILES_IMPLEMENTATION_STATIC_PREFLIGHT_AND_EXECUTION_LOCK`  
**Date:** 2026-10-07  
**Branch:** `pivot/gwf-autonomous-research-stack-v1`  
**Verdict:** **PASS / EXECUTION LOCKED / FORMALLY CLOSED**

## 1. Frozen contract baseline

- P2 contract head: `1f64ff9df32ddbfe1460025ac8ec2716cb884669`
- P2 definitions blob: `fe83c0c638baee9912aa6b15f82bee1c19c2267a`
- P2 preregistration blob: `4009b9fe8cb9bb0d48b6dea15b7df528010c7bde`
- P1 execution-lock implementation blobs remained unchanged and were checked by P2 static preflight.

## 2. Qualified implementation

Qualified implementation HEAD:

`2fadb7f7c9ffeb8ba95800b65e06603db852f4ef`

Exact implementation blobs:

- `domains/research.governance_profiles.v1.json` — `7ca53b894c8be051e7375e036d43c6c7b6499326`
- `domains/software.governance_profiles.v1.json` — `9b8a18eed9d45343a32a733efd9b400f022285f8`
- `src/gwr/domain_governance_vnext.py` — `d83ec96de7c572401f44d23f8a7e9dd3a05b4f60`
- `tests/test_gwf_vnext_p2_domain_governance_profiles.py` — `0f0f31d6c0d59067f31997333c00dea8de9f8578`
- `scripts/pivot/gwf_vnext_p2_static_preflight.py` — `bcafb2e0589290b012268623b595c85f183435ff`
- `.github/workflows/gwf-vnext-p2-domain-governance-profiles.yml` — `c9a1df7b9b4a6ecf808d00497a6f9abf3f81cffe`

## 3. Implemented scope

P2 materializes and enforces exactly eight frozen profiles.

### Research

- `research.triage`
- `research.exploratory`
- `research.measurement`
- `research.confirmatory`

### Software

- `software.triage`
- `software.development`
- `software.qualification`
- `software.release`

Implementation adds:

- exact-hash domain profile package validation;
- exact profile registration into the P1 governance kernel;
- initial profile binding;
- forward-only transition lookup;
- transition readiness-condition enforcement;
- durable HumanActionRequest creation for human-required transitions;
- exact human-approval binding before activation;
- stale-transition protection;
- TRIAGE non-downgrade enforcement;
- protected-resource firewalls;
- claim ceilings and formal-verdict/release-acceptance firewalls;
- research successor requirement for material scientific changes;
- software successor requirement for material scope/product changes;
- qualification candidate-SHA invalidation semantics;
- release external-effect retry safety checks.

P1 locked runtime/kernel files were not modified.

## 4. Qualification evidence

### Initial run

Run:

`37603082434`

Head:

`ee50c33d380209e8df2c980fddea4be40da2c740`

Result:

`FAIL`

The P2 static preflight, P2 targeted tests, and P1 regression tests had already PASSed. The failure was a CI harness path error:

`tests/test_software_domain.py` did not exist.

The failure was retained and not rewritten.

No contract/profile/runtime semantic change was made to repair it.

### Bounded harness repair

Workflow path was corrected to real domain-regression surfaces.

Qualified run:

`37603208717`

Head:

`2fadb7f7c9ffeb8ba95800b65e06603db852f4ef`

Conclusion:

`SUCCESS`

Checks:

- P2 static architecture/hash/P1-lock preflight — PASS;
- all 30 preregistered negative tests — PASS;
- positive domain/zero-protected-resource fixtures — PASS;
- P1 locked governance regressions — PASS;
- domain package regressions — PASS;
- Python compile preflight — PASS.

## 5. Execution lock

Execution lock artifact:

`docs/pivot/GWF_VNEXT_P2_EXECUTION_LOCK.json`

Lock blob:

`25660c52526923d557224ac9fbc9abeae23adcc4`

Lock commit:

`6893f81a7da9728c909fe05eb44ff572f3ab4bbf`

The commit containing the lock was itself revalidated:

- run: `37603357263`
- head: `6893f81a7da9728c909fe05eb44ff572f3ab4bbf`
- conclusion: **SUCCESS**

Therefore no unverified post-qualification mutation is being used as the P2 lock.

## 6. Preserved invariants

The implementation and lock preserve:

- P1 authority/budget monotonicity;
- P1 WorkAssignment/ExecutorBinding identity boundaries;
- research/software domain separation;
- forward-only acyclic in-place profile transitions;
- TRIAGE as bootstrap/pre-domain-work rather than post-lock downgrade;
- operational recovery inside active advanced profiles;
- no-rescue and successor semantics;
- human approval for research confirmatory activation;
- human approval for software release promotion;
- protected confirmatory evidence firewall;
- profile completion != scientific verdict;
- profile completion != release acceptance;
- transport/model/provider/UI neutrality.

## 7. Explicit non-claims

This P2 closure does not claim:

- RemoteMCP adapter integration;
- Codex adapter integration;
- G2E runtime integration/import;
- Mission Control UI implementation;
- any real research project execution;
- any real software project execution;
- any protected confirmatory evidence consumption;
- any scientific PASS/FAIL;
- any software release acceptance.

## 8. RemoteMCP infrastructure note

The approved managed RemoteMCP project remains:

- project: `prj_f65cb1dc522d61a293467983`
- device: `machine-1 / dev_dd73ebfa742f468f2d212bade88c175b`
- path: `D:\WORK\RESEARCH\4.GWF-VNEXT`

At P2 closure it remains `NON_GIT`.

No replacement project/device, re-pair, restart, or duplicate clone job was used during P2.

This infrastructure condition is operational only and does not rewrite P2 qualification evidence.

## 9. Formal disposition

```text
GWF_VNEXT_P2_DOMAIN_GOVERNANCE_PROFILES_IMPLEMENTATION_STATIC_PREFLIGHT_AND_EXECUTION_LOCK
= PASS
= EXECUTION LOCKED
= FORMALLY CLOSED
```

Any change to a P2 bound implementation blob invalidates this lock and requires requalification.

## 10. Next bounded frontier

The next authorized phase is specification/reconciliation only:

`GWF_VNEXT_P3_G2E_SEMANTIC_RUNTIME_RECONCILIATION_PREREGISTRATION_AND_CONTRACT_FREEZE`

P3 may:

- pin the canonical qualified G2E baseline;
- classify G2E files as canonical core / reusable adapter / qualification test / historical evidence / transport experiment;
- freeze the G2E AgentBinding ↔ GWF ExecutorBinding mapping;
- freeze Goal/Claim/ProofObligation/ExecutionAttempt/Evidence/Adjudication ownership and persistence mappings;
- freeze cardinality/revision/identity rules between G2E and GWF;
- define protected-resource and evidence-admission bridge contracts.

P3 must not yet:

- import/merge G2E runtime code;
- integrate RemoteMCP;
- integrate Codex;
- refactor Mission Control UI;
- run a real research project;
- consume protected evidence.
