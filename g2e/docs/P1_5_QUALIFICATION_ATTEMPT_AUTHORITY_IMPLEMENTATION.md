# G2E P1.5 — Qualification Attempt Authority Implementation Contract

**Status:** FROZEN IMPLEMENTATION CONTRACT  
**Baseline:** `53c7ac3d138968a2b96ece9ac58b95aef04511dc`  
**Authority:** P5A D2 Qualification Authority Admission preimplementation = `SPEC_PASS_IMPLEMENTATION_REQUIRED`  
**D2 execution:** NOT AUTHORIZED  
**Model turn:** PROHIBITED  
**Codex runtime adapter:** NOT AUTHORIZED

## 1. Purpose

Implement the smallest provider-neutral schema/governance prerequisite that represents bounded authority to attempt an unqualified capability without claiming that capability is already available.

## 2. Authorized implementation surface

Only:

- `src/g2e/schemas.py`;
- `tests/g2e/test_p1_5_qualification_authority.py`;
- `.github/workflows/g2e-p1-5-qualification-authority.yml`;
- this implementation contract;
- result/evidence/LINEAGE after exact-SHA qualification.

No provider-specific file is authorized.

## 3. Canonical schema addition

Add `QualificationAuthorityGrant` with schema kind
`qualification_authority_grant`.

Required invariants are exactly those frozen by
`P5A_D2_QUALIFICATION_AUTHORITY_ADMISSION_PREIMPLEMENTATION.md`.

Additional fail-closed structural checks allowed by that contract:

- target capability IDs unique and non-empty;
- granted authority scope unique and non-empty;
- read/write path lists unique;
- all paths relative, non-empty, and traversal-free;
- qualification lineage ref non-empty.

No outcome/verdict field is added.

## 4. AgentBinding extension

Add only:

```text
qualification_authority_ref: ExactRef | None = None
qualification_target_capability_ids: tuple[str, ...] = ()
```

Fail closed when:

- target IDs exist without a grant ref;
- grant ref exists without target IDs;
- target IDs contain duplicates;
- target IDs overlap normal `required_capability_ids`.

Bindings with both new fields in their defaults preserve P1.4 behavior.

## 5. Normal validator preservation

`validate_agent_binding_identity()` remains unchanged in semantics and continues to reject:

- unavailable required capabilities;
- authority beyond manifest operational ceiling.

P1.5 does not route normal bindings through qualification semantics.

## 6. Explicit qualification validator

Add:

`validate_qualification_agent_binding_identity(...)`

Inputs:

- exact AgentCapabilityManifest;
- exact AgentEquivalencePolicy;
- exact QualificationAuthorityGrant;
- exact AuthorityPolicy;
- exact ProofObligation;
- exact AgentBinding;
- exact ExecutionAttemptEnvelope;
- optional ExecutionResult;
- optional expected read/write path tuples for frozen-workspace checking.

It must verify:

- manifest AVAILABLE;
- exact refs: manifest/equivalence/grant/policy/proof;
- proof lifecycle FROZEN or AUTHORIZED;
- attempt ID equality;
- attempt/binding ref equality;
- app/provider/model/harness/transport identity equality;
- normal required capabilities AVAILABLE with evidence;
- qualification targets exist, are unavailable, exactly equal the grant targets, and do not overlap normal prerequisites;
- every granted action exists in AuthorityPolicy and permits the grant role;
- binding authority is within manifest ceiling ∪ exact grant scope;
- attempt authority equals binding authority exactly;
- expected read/write paths equal grant paths when supplied;
- qualification-only/single-attempt/non-evidence/non-operational invariants;
- result identity consistency when supplied.

It performs no IO, no dispatch, no discovery, no model execution, no secret resolution, no adjudication.

## 7. P5-FX-001 qualification fixture

Tests must instantiate the exact semantic shape:

- unavailable targets: `repository_read`, `repository_write`;
- qualified structural prerequisites;
- role: `qualification_executor`;
- grant: `READ_FROZEN_FIXTURE`, `WRITE_DESIGNATED_OUTPUT`;
- reads: `input.json`, `TASK.md`;
- write: `result.json`;
- network false;
- interactive approval false.

The positive fixture proves a qualification binding can be valid without mutating capability availability.

## 8. Negative fixtures

Must reject at least:

- target capability already AVAILABLE;
- missing target capability;
- target duplicated or overlapping normal prerequisite;
- wrong grant ref;
- wrong proof ref;
- wrong manifest ref;
- wrong attempt ID;
- wrong AuthorityPolicy ref;
- action absent from AuthorityPolicy;
- role not permitted for action;
- binding authority beyond manifest+grant;
- attempt authority differs from binding authority;
- read/write path contract mismatch;
- absolute/traversal grant paths;
- attempt to set network/interactive approval true;
- normal validator still rejects the same unavailable target when supplied as `required_capability_ids`;
- grant cannot make manifest capability available.

## 9. Qualification gate

Exact candidate must PASS:

- compile;
- P1;
- P1.4;
- P1.5;
- P2;
- P3;
- P4;
- provider-neutral source assertion;
- no D2 outcome/model turn/runtime adapter;
- bounded implementation diff.

Only then may P1.5 formal-close.

P1.5 PASS does not itself authorize D2. The next step after PASS is to materialize the exact P5-FX-001 grant and final AgentBinding, then run a final zero-fresh admission qualification.
