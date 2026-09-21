# G2E P5A D2 — Qualification Authority Admission Pre-Implementation

**Status:** FROZEN CANDIDATE FOR ZERO-FRESH QA  
**Phase:** P5A D2 qualification-authority prerequisite  
**Baseline:** `11c04f7c7be88ebfd40ea6755a8bfc633262048d`  
**D2 model turn:** PROHIBITED  
**Codex runtime adapter:** NOT AUTHORIZED  
**Core/runtime implementation:** NOT AUTHORIZED BY THIS SPEC PHASE

## 1. Origin

P5A D2 / P5-FX-001 pre-implementation qualified at:

`15eeae4776a969cb0d64b9d55f33146e303161ec`

with authoritative workflow:

`35603125876` / job `106343728888` — PASS.

The formal verdict is:

`SPEC_PASS_EXECUTION_BLOCKED`

and the sole execution blocker is **D2-F01**.

Exact frozen D2 identities:

- ProofObligation:
  `p5a-d2-p5-fx-001-proof@p5-fx-001-v1#8e275db790fe4c83061385f9988f4165f54d514611a44a4a555c5d01f6d3dbcd`;
- preflight identity AgentBinding:
  `p5a-d2-preflight-binding@p5-fx-001-v1#a5a9287d464d3d3450e9cf82d7866d45e9e2fc2921b0c28d938fd7257a3940f8`;
- D2 input SHA-256:
  `a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6`;
- TASK.md SHA-256:
  `4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e`;
- preregistration pack SHA-256:
  `eaeff7a8141697b2ecb824709277ba51db5e60643a722f2d06b3d5d3f6d4d4b4`.

No D2 model turn has occurred.

## 2. Problem statement

The exact qualified D1 Codex AgentCapabilityManifest intentionally says:

```text
repository_read  available = false
repository_write available = false
...
max_authority_scope = ()
```

The D2 proof exists precisely to test functional capability that is not yet qualified.

However, P1.4 currently requires:

1. every `AgentBinding.required_capability_id` to be present and AVAILABLE; and
2. `AgentBinding.authority_scope ⊆ AgentCapabilityManifest.max_authority_scope`.

P5-FX-001 requires the bounded actions:

```text
READ_FROZEN_FIXTURE
WRITE_DESIGNATED_OUTPUT
```

Therefore current semantics cannot authorize the experimental attempt without pretending the functional capability is already qualified.

## 3. Required semantic distinction

The framework MUST distinguish:

```text
CAPABILITY EVIDENCE
"What has already been demonstrated?"
```

from:

```text
QUALIFICATION AUTHORITY
"What narrowly bounded action may be attempted in order to test an unqualified capability?"
```

Formally:

```text
authority_to_attempt(C)
    ⇏
capability_available(C)
```

and:

```text
qualification_PASS(C)
    may later justify
capability_available(C)=true
```

A qualification grant is permission to create evidence. It is not evidence itself.

## 4. Existing semantics preserved

The following P1.4 semantics remain unchanged for normal/operational bindings:

- `AgentCapabilityManifest` remains descriptive capability identity;
- `AgentCapability.available=true` still requires qualification evidence;
- `required_capability_ids` still means capabilities already qualified as AVAILABLE;
- ordinary `AgentBinding.authority_scope` still cannot exceed the manifest operational authority ceiling;
- a normal binding cannot use an unavailable capability;
- executor success never upgrades capability availability or scientific verdict;
- the agent cannot self-elevate;
- delegated authority cannot exceed its governing parent authority;
- P2 remains the attempt scientific verdict authority.

No existing normal binding is retroactively reinterpreted.

## 5. New canonical primitive — QualificationAuthorityGrant

A future bounded schema prerequisite MUST introduce a canonical object:

`QualificationAuthorityGrant`

Schema kind:

`qualification_authority_grant`

Frozen fields:

- `mode: "QUALIFICATION_ONLY"`;
- exact `proof_ref`;
- exact `capability_manifest_ref`;
- `attempt_id`;
- `target_capability_ids`;
- exact `authority_policy_ref`;
- `granted_role`;
- `granted_authority_scope`;
- `allowed_read_paths`;
- `allowed_write_paths`;
- `network_allowed: false`;
- `interactive_approval_allowed: false`;
- `single_attempt: true`;
- `may_imply_capability_available: false`;
- `may_be_reused_for_operational_binding: false`;
- `qualification_lineage_ref`.

The object contains no outcome or verdict.

## 6. QualificationAuthorityGrant invariants

A valid qualification grant MUST satisfy all of:

1. `mode == QUALIFICATION_ONLY`;
2. exact ProofObligation is FROZEN/AUTHORIZED before dispatch;
3. exact capability manifest is the manifest under qualification;
4. `attempt_id` is one prospective unique attempt;
5. every target capability exists in the exact manifest;
6. every target capability is currently `available=false`;
7. target capabilities are not copied into `required_capability_ids`;
8. grant authority is explicitly allowed by the exact AuthorityPolicy for `granted_role`;
9. granted scope is finite and unique;
10. read/write path scopes are finite and explicit;
11. network remains false unless a separately preregistered proof explicitly requires it;
12. interactive approval remains false for P5-FX-001;
13. grant is single-attempt and non-transferable;
14. grant cannot be used by another ProofObligation, attempt, manifest or harness binding;
15. grant cannot change `AgentCapabilityManifest.available`, `qualification_refs`, or `max_authority_scope`;
16. grant cannot be reused for production/operational execution;
17. no grant field may encode PASS/FAIL/INVALID or expected task outcome.

## 7. AuthorityPolicy relationship

PRD-14 requires every normative action to have an authority check and requires delegated authority ≤ parent authority.

For qualification execution, the parent normative authority is an exact canonical `AuthorityPolicy`, not the capability manifest.

For P5-FX-001 the future exact AuthorityPolicy must contain only:

```text
READ_FROZEN_FIXTURE       allowed role: qualification_executor
WRITE_DESIGNATED_OUTPUT   allowed role: qualification_executor
```

No generic:

- repository write;
- arbitrary shell;
- network;
- credential;
- protected-resource;
- approval bypass

authority is implied.

The QualificationAuthorityGrant delegates only a subset of actions already explicitly permitted to `qualification_executor` by that exact policy.

## 8. AgentBinding extension

A future bounded P1-compatible schema patch MUST extend AgentBinding with:

- `qualification_authority_ref: ExactRef | None = None`;
- `qualification_target_capability_ids: tuple[str, ...] = ()`.

Normal binding:

```text
qualification_authority_ref = None
qualification_target_capability_ids = ()
```

and retains current P1.4 validation unchanged.

Qualification binding:

```text
required_capability_ids
    = already-qualified structural prerequisites only

qualification_target_capability_ids
    = capabilities intentionally under test

qualification_authority_ref
    = exact QualificationAuthorityGrant
```

For P5-FX-001:

```text
required_capability_ids:
  app_server_launch
  jsonrpc_initialize
  thread_lifecycle_surface
  turn_stream_surface
  external_session_attribution_surface

qualification_target_capability_ids:
  repository_read
  repository_write
```

This explicitly prevents pretending the target capabilities are already qualified.

## 9. Authority scope semantics

For a normal binding:

```text
binding.authority_scope
    ⊆
manifest.max_authority_scope
```

unchanged.

For a qualification binding:

```text
binding.authority_scope
    ⊆
manifest.max_authority_scope
      ∪
qualification_grant.granted_authority_scope
```

but every authority element outside the manifest ceiling MUST be:

- present in the exact qualification grant;
- permitted by the exact AuthorityPolicy for the grant role;
- bound to the same ProofObligation;
- bound to the same attempt ID;
- bound to the same exact capability manifest;
- used only for the named qualification target capabilities.

This union is an **attempt authority calculation**, not a new manifest authority ceiling.

The manifest remains unchanged.

## 10. Capability validation semantics

For `required_capability_ids`:

current P1.4 behavior remains:

```text
capability exists
AND available == true
AND qualification_refs non-empty
```

For `qualification_target_capability_ids`:

required qualification behavior is:

```text
capability exists
AND available == false
AND capability is named by exact QualificationAuthorityGrant
```

A target capability already `available=true` is not an error scientifically, but it MUST NOT be silently routed through qualification-target semantics; the binding must use normal required-capability semantics or be refrozen under an explicit reason.

A missing capability ID fails closed.

## 11. New explicit validator

The future bounded implementation MUST NOT silently weaken
`validate_agent_binding_identity()`.

Instead it must provide an explicit qualification path, either:

`validate_qualification_agent_binding_identity(...)`

or an equivalent explicit mode whose normal-path behavior remains byte-for-byte semantically equivalent.

The qualification validator must verify at least:

1. all existing manifest/equivalence/binding/attempt identity rules;
2. exact grant ref;
3. exact ProofObligation ref;
4. exact attempt ID;
5. exact capability manifest ref;
6. target capability set equality;
7. targets currently unavailable;
8. normal prerequisites currently available;
9. AuthorityPolicy permits every granted action for the frozen role;
10. binding authority is within manifest ceiling plus exact grant;
11. read/write paths are within the frozen workspace contract;
12. no network/interactive approval for P5-FX-001;
13. grant is QUALIFICATION_ONLY and single-attempt;
14. grant cannot imply capability availability;
15. result identity propagation, when present, does not assign scientific verdict.

## 12. P5-FX-001 exact qualification grant

The later implementation must materialize the exact P5-FX-001 grant prospectively with:

```text
mode:
  QUALIFICATION_ONLY

proof:
  p5a-d2-p5-fx-001-proof@p5-fx-001-v1
  #8e275db790fe4c83061385f9988f4165f54d514611a44a4a555c5d01f6d3dbcd

attempt_id:
  p5a-d2-p5-fx-001-attempt-001

target_capability_ids:
  repository_read
  repository_write

granted_role:
  qualification_executor

granted_authority_scope:
  READ_FROZEN_FIXTURE
  WRITE_DESIGNATED_OUTPUT

allowed_read_paths:
  input.json
  TASK.md

allowed_write_paths:
  result.json

network_allowed:
  false

interactive_approval_allowed:
  false

single_attempt:
  true

may_imply_capability_available:
  false

may_be_reused_for_operational_binding:
  false
```

No broader path or authority is admissible.

## 13. Capability-state transition after D2

Even if D2 later adjudicates PASS, this qualification grant itself does not mutate the manifest.

A future capability-state update requires a separate evidence-derived governed step:

```text
D2 admitted evidence
        ↓
D2 Adjudication PASS
        ↓
separate manifest revision proposal
        ↓
qualification_refs bind exact D2 evidence
        ↓
new AgentCapabilityManifest revision
```

D2 FAIL leaves target capabilities unavailable.

D2 INVALID leaves target capabilities unavailable and follows frozen retry/no-rescue policy.

No in-place manifest mutation is allowed.

## 14. Forbidden designs

The implementation MUST NOT:

- set `repository_read/write=true` to authorize their own test;
- widen the D1 manifest `max_authority_scope` before evidence;
- treat a QualificationAuthorityGrant as capability evidence;
- hide qualification authority in prompt/config/environment/GWF metadata;
- bypass AgentBinding identity validation;
- reuse a qualification grant for production;
- grant generic repository/shell/network authority for P5-FX-001;
- allow grant reuse across attempts;
- infer ChatGPT authority/capability from Codex;
- let executor success mutate manifest availability.

## 15. Required bounded implementation surface after spec PASS

If this preimplementation qualification passes, the next implementation is a schema/governance prerequisite only, provisionally:

**P1.5 — Qualification Attempt Authority**

Bounded implementation surface:

- `src/g2e/schemas.py`;
- canonical `QualificationAuthorityGrant`;
- two optional AgentBinding fields;
- explicit qualification binding validator;
- provider-neutral tests;
- P1/P1.4/P2/P3/P4 regressions;
- no Codex runtime adapter;
- no model turn.

P3/P4 propagation should change only if the new exact grant/binding identity requires provider-neutral propagation.

## 16. Zero-fresh gate

The preimplementation workflow must prove:

```text
QA-Q0  exact D2-F01 evidence bound
QA-Q1  capability-vs-authority distinction frozen
QA-Q2  QualificationAuthorityGrant schema contract frozen
QA-Q3  AuthorityPolicy parent/delegation semantics frozen
QA-Q4  AgentBinding extension frozen
QA-Q5  normal binding semantics preserved
QA-Q6  qualification validator contract frozen
QA-Q7  P5-FX-001 exact grant scope frozen
QA-Q8  manifest state transition remains post-evidence separate
QA-Q9  forbidden backdoors frozen
QA-Q10 no model turn / D2 outcome / runtime adapter
QA-Q11 P1/P1.4/P2/P3/P4 regressions PASS
```

## 17. Qualification verdicts

### `SPEC_PASS_IMPLEMENTATION_REQUIRED`

Use when all semantics are frozen and D2-F01 can be resolved only by the bounded P1.5 schema/governance prerequisite.

### `SPEC_FAIL`

Use when the proposed distinction weakens P1.4, violates PRD-14 delegated-authority constraints, permits capability self-qualification, or leaves authority/path scope ambiguous.

### `INVALID`

Use when fresh D2 outcome/model-turn evidence exists before this lock or the exact candidate cannot be established.

## 18. Authorization boundary

A PASS here does **not** authorize D2.

Expected sequence:

```text
P5A_D2_QUALIFICATION_AUTHORITY_ADMISSION_PREIMPLEMENTATION
        ↓
SPEC_PASS_IMPLEMENTATION_REQUIRED
        ↓
P1.5 Qualification Attempt Authority
bounded schema/governance implementation
        ↓
P1/P1.4/P2/P3/P4 + P1.5 PASS
        ↓
materialize exact P5-FX-001 QualificationAuthorityGrant
        ↓
freeze FINAL D2 AgentBinding
        ↓
zero-fresh final admission check
        ↓
ONLY THEN
one D2 model turn
```

Codex runtime adapter remains outside this prerequisite.
