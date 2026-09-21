# G2E P5A D2 — Final Admission Materialization and Zero-Fresh Qualification

**Status:** FROZEN CANDIDATE FOR ZERO-FRESH QA  
**Baseline:** `926d6a46344e8ac4822907fdc6b597f8d6ba6feb`  
**Prerequisite:** P1.5 Qualification Attempt Authority = PASS  
**D2 model turn during this phase:** PROHIBITED  
**Codex runtime adapter:** NOT AUTHORIZED

## 1. Purpose

Materialize the complete prospective P5-FX-001 pre-dispatch identity graph and prove it is admissible under P1.5 before any Codex model turn.

The graph is:

```text
exact D1 AgentCapabilityManifest
        +
exact frozen P5-FX-001 ProofObligation
        +
exact AuthorityPolicy
        ↓
exact QualificationAuthorityGrant
        ↓
FINAL D2 AgentBinding
        ↓
pre-dispatch ExecutionAttemptEnvelope
        ↓
validate_qualification_agent_binding_identity()
```

No object in this phase contains a D2 outcome.

## 2. Exact inherited identities

The final admission builder MUST reproduce without semantic change:

- D1 manifest:
  `agent-capability-manifest-codex-d1@a337b7433ebb351c-d1-v1#585d59b32457484e8d4706c3e79a94398569ab4bc3e39ff8fca5502541ece5c5`;
- frozen ProofObligation:
  `p5a-d2-p5-fx-001-proof@p5-fx-001-v1#8e275db790fe4c83061385f9988f4165f54d514611a44a4a555c5d01f6d3dbcd`;
- input SHA-256:
  `a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6`;
- TASK.md SHA-256:
  `4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e`;
- attempt ID:
  `p5a-d2-p5-fx-001-attempt-001`;
- exact harness SHA-256:
  `a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8`.

Any drift fails admission.

## 3. Exact AuthorityPolicy

Materialize canonical:

`p5a-d2-p5-fx-001-authority-policy@p5-fx-001-v1`

with exactly two actions:

```text
READ_FROZEN_FIXTURE
  allowed_roles = qualification_executor

WRITE_DESIGNATED_OUTPUT
  allowed_roles = qualification_executor
```

and:

`delegated_authority_may_exceed_parent = false`.

No generic repository, shell, network, credential, approval-bypass or external-tool authority is present.

## 4. Exact QualificationAuthorityGrant

Materialize canonical:

`p5a-d2-p5-fx-001-qualification-grant@p5-fx-001-v1`

with:

```text
mode = QUALIFICATION_ONLY
attempt_id = p5a-d2-p5-fx-001-attempt-001

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

network_allowed = false
interactive_approval_allowed = false
single_attempt = true
may_imply_capability_available = false
may_be_reused_for_operational_binding = false
```

It must bind the exact frozen proof, exact D1 manifest and exact AuthorityPolicy.

## 5. FINAL D2 AgentBinding

Materialize canonical:

`p5a-d2-final-agent-binding@p5-fx-001-v1`.

Normal qualified prerequisites remain:

```text
app_server_launch
jsonrpc_initialize
thread_lifecycle_surface
turn_stream_surface
external_session_attribution_surface
```

Qualification targets are exactly:

```text
repository_read
repository_write
```

Authority scope is exactly:

```text
READ_FROZEN_FIXTURE
WRITE_DESIGNATED_OUTPUT
```

It must bind the exact grant and exact prospective attempt ID.

The binding must preserve exact D1 app/harness/transport identity with no substitution.

## 6. Pre-dispatch ExecutionAttemptEnvelope

Materialize canonical:

`p5a-d2-predispatch-attempt-envelope@p5-fx-001-v1`

with:

- attempt ID exactly `p5a-d2-p5-fx-001-attempt-001`;
- exact ProofObligation ref;
- state `LOCKED`;
- external harness implementation identity tied to the exact Codex executable SHA-256;
- deterministic config hash over the frozen execution configuration;
- exact final AgentBinding ref;
- exact retry policy ref from preregistration;
- authority scope exactly equal to final binding authority;
- exact input/task data refs;
- no candidate evidence;
- no outcome artifact.

The envelope is an identity/authorization object only. It does not indicate execution success.

## 7. Frozen execution configuration

The deterministic config hash MUST cover at least:

- fixture ID;
- input SHA-256;
- TASK.md SHA-256;
- exact harness SHA-256;
- exact ProofObligation ref;
- exact manifest ref;
- exact AuthorityPolicy ref;
- exact QualificationAuthorityGrant ref;
- exact final AgentBinding ref;
- pre-workspace inventory;
- only permitted post addition;
- read/write path scopes;
- authority scope;
- network false;
- interactive approval false;
- startup/turn/verifier timeouts;
- retry budget zero.

Any later execution configuration drift creates a different attempt and is outside this admission.

## 8. Zero-fresh validation

The final gate MUST call:

`validate_qualification_agent_binding_identity(...)`

using:

- exact D1 manifest;
- exact AgentEquivalencePolicy;
- exact grant;
- exact AuthorityPolicy;
- exact ProofObligation;
- exact final AgentBinding;
- exact pre-dispatch attempt;
- expected reads `("input.json", "TASK.md")`;
- expected writes `("result.json",)`.

It must PASS before execution authority can open.

## 9. Negative final-admission fixtures

The candidate must fail closed if any of these are changed:

- proof ref;
- manifest ref;
- AuthorityPolicy ref;
- grant ref;
- attempt ID;
- target capability set;
- required structural prerequisite set;
- authority scope;
- attempt/binding authority equality;
- read/write paths;
- input/task hashes in frozen config;
- network/interactive approval;
- harness identity;
- execution config hash;
- model/provider/harness/transport substitution.

The D1 manifest must remain unchanged with `repository_read/write.available=false`.

## 10. Freshness and no-outcome gate

Before final admission PASS:

- no Codex D2 model turn may have occurred;
- no D2 result.json may be admitted;
- no D2 ExecutionResult/EvidenceRecord/Adjudication may exist;
- no capability-state update may exist;
- no runtime adapter may be added.

The final admission artifact itself is prospective governance evidence only.

## 11. Final admission verdicts

### `FINAL_ADMISSION_PASS`

Use iff:

- exact graph materializes deterministically;
- P1.5 validator PASSes;
- all negative fixtures fail closed;
- P1/P1.4/P1.5/P2/P3/P4 regressions PASS;
- no fresh D2 outcome/model turn exists.

### `FINAL_ADMISSION_BLOCKED`

Use if the graph is internally valid but an execution prerequisite outside the graph is missing.

### `INVALID`

Use if prospective identities cannot be established or any D2 outcome/model turn predates the final lock.

## 12. Authorization semantics after PASS

A final-admission PASS authorizes **at most one** scientific D2 attempt with the exact frozen attempt ID/configuration.

It does not authorize:

- retries;
- prompt/config changes;
- broader authority;
- another Codex version;
- manifest mutation;
- operational reuse;
- a Codex runtime adapter.

The target capabilities remain unavailable until separately admitted D2 evidence and adjudication justify a new manifest revision.

No model turn occurs in this qualification phase.
