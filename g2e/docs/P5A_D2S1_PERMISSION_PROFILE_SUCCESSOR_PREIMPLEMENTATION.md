# G2E P5A D2-S1 — Permission-Profile Successor Pre-Implementation

**Status:** FROZEN CANDIDATE FOR ZERO-FRESH QA  
**Baseline:** `d6610cb2d996a85bd194b9796490fb206fd95ec5`  
**Predecessor:** P5A D2 attempt 001 = `INVALID`, consumed 1/1  
**Study:** P5A D2-S1 — successor functional qualification using exact Codex 0.153.4 named-permissions protocol  
**Model turn:** PROHIBITED  
**Codex runtime adapter:** NOT AUTHORIZED  
**ChatGPT P5B:** OUT OF SCOPE

## 1. Origin and non-rescue boundary

P5A D2 attempt 001 was consumed when `turn/start` was sent. The exact Codex App Server rejected that request before a turn ID was created because the request used the removed `workspaceWrite.readOnlyAccess` field. No result was produced and no functional capability was established.

D2-S1 is a **new study**, not a retry or replacement attempt under the spent D2 proof:

- predecessor attempt ID remains spent;
- predecessor retry budget remains zero;
- predecessor result remains `INVALID`;
- D2-S1 receives a new study identity, new proof/config identities and a new attempt identity;
- only the frozen P5-FX-001 fixture/task may be reused;
- predecessor outcome is not evidence of functional capability and is not used to tune expected task output.

The purpose of D2-S1 is to test the same bounded functional question under the exact permissions protocol actually supported by the frozen Codex 0.153.4 harness.

## 2. Exact harness and protocol authority

Exact executable identity remains:

```text
sha256:a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8
```

Exact upstream release source used only to interpret this executable's protocol:

```text
openai/codex
tag: rust-v0.153.4
commit: 3d2ee51ca2d5db578f328aa75e20aa22c0197c9a
```

Exact locally generated schemas already frozen from the executable:

```text
v2/ThreadStartParams.json
sha256:792e2f32e37cece971bd616664ea2053741acbed4e9c92e9d1766427718f2ecd

v2/TurnStartParams.json
sha256:a3835e8c1e942e4b358e1a670939b89918b16c4d13105a579899892b7ade6dea
```

Release-source facts that govern D2-S1:

1. `InitializeCapabilities.experimental_api` opts a client into experimental request fields.
2. `ThreadStartParams.permissions: Option<String>` selects a named permission-profile ID for the thread and cannot be combined with legacy `sandbox`.
3. `TurnStartParams.permissions: Option<String>` selects a named permission-profile ID for a turn and cannot be combined with `sandboxPolicy`.
4. `permissionProfile/list` is the protocol method that enumerates named profile IDs and whether each is allowed.
5. top-level `permissionProfile` is rejected for `thread/start` and `turn/start`; the supported field is `permissions`.
6. legacy `workspaceWrite.readOnlyAccess=restricted` is rejected and MUST NOT appear in D2-S1.
7. custom permission profiles are defined in Codex config under `[permissions.<id>]`; filesystem entries accept read/write/deny access and network can be explicitly disabled.

The generated non-experimental JSON schema not containing `permissions` is not evidence that the field is absent: in release source it is explicitly marked experimental and therefore requires experimental API negotiation.

## 3. Reused fixture — scientific content unchanged

D2-S1 reuses **only** the frozen P5-FX-001 scientific fixture and task:

```text
fixture_id = P5-FX-001
generator_version = p5-fx-001-v1
seed = g2e-p5-agent-profile-v1
count = 32

input_sha256 =
a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6

TASK.md_sha256 =
4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e
```

The task bytes, expected-output semantics, verifier arithmetic and PASS/FAIL metric definitions MUST NOT change.

Pre-workspace remains exactly:

```text
input.json
TASK.md
```

Only permitted task output remains:

```text
result.json
```

## 4. New successor identities

The successor must materialize fresh canonical identities. Proposed stable IDs:

```text
study_id:
p5a-d2s1-permission-profile-successor

proof_object_id:
p5a-d2s1-p5-fx-001-proof

permission_profile_id:
g2e_p5a_d2s1

agent_binding_object_id:
p5a-d2s1-final-agent-binding

predispatch_object_id:
p5a-d2s1-predispatch-attempt-envelope

attempt_id:
p5a-d2s1-p5-fx-001-attempt-001
```

None may alias the predecessor D2 attempt/proof/binding.

## 5. Successor CODEX_HOME contract

D2-S1 uses a fresh successor-specific local root under the repository:

```text
D:\WORK\RESEARCH\4.GWF\g2e\.local\P5A-D2S1\
```

No D2-S1 mutable artifact may be created as a sibling of `D:\WORK\RESEARCH\4.GWF`.

Before app-server startup, successor `CODEX_HOME` contains exactly:

```text
auth.json
config.toml
```

`auth.json` is copied from the existing authenticated Codex home and is never committed, hashed into public evidence, printed, or inspected for token contents.

`config.toml` is generated deterministically and its exact bytes/SHA-256 are frozen before any model turn.

The config MUST NOT import user MCP servers, plugins, skills, memories, prior sessions or project history.

Invocation-level isolation remains:

```text
mcp_servers={}
features.apps=false
features.plugins=false
features.remote_plugin=false
features.workspace_dependencies=false
```

## 6. Exact named permission profile

The successor profile is named exactly:

```text
g2e_p5a_d2s1
```

It MUST be a custom profile with no parent inheritance.

Its task-data authority is:

```text
READ:
  exact successor workspace/input.json
  exact successor workspace/TASK.md

WRITE:
  exact successor workspace/result.json

NETWORK:
  disabled
```

No repository path is task-readable or task-writable.

No generic workspace write grant is permitted.

The materializer MUST use absolute Windows paths accepted by Codex 0.153.4 and MUST freeze the resulting `config.toml` bytes before dispatch.

### 6.1 Runtime-support read closure

Codex 0.153.4 may add narrowly scoped runtime helper reads required for its own sandbox/runtime implementation (for example the active arg0 wrapper/helper executable path).

These are **runtime-support reads**, not task-data authority.

D2-S1 permits them only if all of the following hold:

- they are added by the exact frozen harness, not by the task/prompt;
- they contain no GWF repository source, user documents, prior experiment outcomes or credentials;
- they are not writable by the task;
- their purpose is runtime/sandbox support only;
- the preturn attestation records their presence/class without exposing credential contents.

Any non-support read expansion outside the frozen fixture is a preturn blocker or an `INVALID` attempt if discovered only after turn start.

## 7. Frozen protocol sequence

### 7.1 Initialize

The client MUST initialize with experimental API negotiation enabled:

```json
{
  "capabilities": {
    "experimentalApi": true
  }
}
```

This is required solely because the exact 0.153.4 `permissions` request fields are experimental.

### 7.2 Preturn environment checks

Before `thread/start`:

1. `mcpServerStatus/list` returns zero configured MCP servers.
2. `app/installed` yields zero installed/callable apps in the isolated home.
3. `account/read` proves auth readiness.
4. `permissionProfile/list` with the exact successor cwd MUST contain:
   - `id = g2e_p5a_d2s1`;
   - `allowed = true`.
5. no result file exists.
6. fixture/task hashes match the frozen values.
7. exact executable hash, source baseline, admission identities and successor config hash match.

### 7.3 Thread start

`thread/start` MUST use:

```text
cwd = exact successor execution workspace
approvalPolicy = never
permissions = g2e_p5a_d2s1
sandbox = OMITTED
```

The response MUST provide a thread ID.

If `activePermissionProfile` is exposed by the negotiated response, its ID MUST equal `g2e_p5a_d2s1`.

Instruction sources MUST be empty.

Any mismatch blocks before the scientific turn.

### 7.4 Turn start

The scientific attempt begins immediately before sending `turn/start`, exactly as in the predecessor governance.

`turn/start` MUST contain:

- exact thread ID;
- exact frozen TASK.md text;
- exact cwd;
- `approvalPolicy = never`;
- no `sandboxPolicy`;
- no legacy `readOnlyAccess`;
- no `permissionProfile`.

The successor MAY omit `permissions` at turn level and inherit the already-attested thread profile. If it is included, it MUST equal `g2e_p5a_d2s1`; this choice must be frozen prospectively and covered by the successor execution-config hash.

No model/provider substitution is allowed.

## 8. Preturn profile-selection qualification

Before any D2-S1 model turn, a no-turn technical preflight MUST prove on a fresh successor `CODEX_HOME`:

```text
initialize(experimentalApi=true)        PASS
MCP count                              0
installed/callable apps                0
auth ready                             true
permissionProfile/list profile present true
permissionProfile/list allowed         true
thread/start permissions accepted      true
thread id present                      true
active profile identity, if emitted    exact
instructionSources                     []
turn/start sent                        false
result.json                            absent
```

This preflight is not a scientific attempt.

A preflight failure may be diagnosed and repaired before authorization only if no `turn/start` was sent.

## 9. Successor execution configuration hash

The D2-S1 deterministic execution-config hash MUST cover at least:

- successor study/proof/binding/attempt IDs;
- exact reused input/TASK hashes;
- exact executable SHA-256;
- release source tag + commit;
- exact ThreadStart/TurnStart schema hashes;
- `experimentalApi=true`;
- permission profile ID;
- exact `config.toml` SHA-256;
- exact successor execution workspace path;
- exact task read/write path set;
- runtime-support-read policy version;
- network disabled;
- approval policy never;
- zero MCP/apps;
- thread/start request shape;
- turn/start request shape;
- startup/turn/verifier timeouts;
- retry budget zero.

Any material change creates a different prospective study configuration and requires a new zero-fresh admission before execution.

## 10. Retry, amendment and no-rescue

D2-S1 has exactly one scientific attempt:

```text
max_invalid_replacement_attempts = 0
```

After `turn/start` is sent, no change is permitted to:

- task/prompt;
- fixture;
- permission profile;
- config.toml;
- read/write authority;
- runtime-support-read policy;
- network/approval policy;
- timeout;
- executable;
- model/provider;
- transport;
- verifier;
- adjudication rule.

PASS, FAIL, INVALID, timeout or protocol rejection after the send are all terminal for D2-S1 attempt 001.

## 11. Evidence and verifier

The successor keeps the predecessor's independent verifier semantics.

Six frozen metrics remain:

```text
executor_completed
result_schema_valid
result_values_correct
mutation_scope_valid
attempt_attribution_valid
evidence_integrity_valid
```

PASS requires all six observable metrics to equal 1 and admitted evidence.

A wrong attributable result is FAIL.

Infrastructure/protocol failure, authority ambiguity, timeout, missing attribution, or unobservable required metrics is INVALID.

The verifier must never convert an unobservable task metric into zero merely to produce FAIL.

## 12. Outcome firewall

Before final D2-S1 admission:

- no D2-S1 model turn may occur;
- no D2-S1 result.json may exist;
- no D2-S1 scientific ExecutionResult/EvidenceRecord/Adjudication may exist;
- no target capability may be marked AVAILABLE;
- predecessor INVALID evidence may be used only to identify the protocol defect, not to select expected task outcome;
- no task arithmetic/output literal may be added to the prompt.

## 13. Zero-fresh gate matrix

```text
S1-Q0 predecessor INVALID formally frozen and attempt spent
S1-Q1 exact 0.153.4 release/source/protocol identities frozen
S1-Q2 reused P5-FX-001 fixture/task identities unchanged
S1-Q3 new successor IDs are disjoint from predecessor IDs
S1-Q4 named permission-profile semantics frozen
S1-Q5 experimental API negotiation frozen
S1-Q6 config.toml generation + exact path authority specified
S1-Q7 runtime-support read closure explicitly bounded
S1-Q8 preturn profile-selection qualification specified
S1-Q9 retry/amendment/no-rescue frozen
S1-Q10 evidence/verifier/adjudication semantics frozen
S1-Q11 no fresh D2-S1 outcome/model turn exists
S1-Q12 P1/P1.4/P1.5/P2/P3/P4 regression requirement preserved
```

## 14. Verdicts for this pre-implementation phase

### `SPEC_PASS_IMPLEMENTATION_REQUIRED`

Use iff the successor protocol and authority model are internally complete, all predecessor identities remain immutable, and no D2-S1 model turn/outcome exists.

### `SPEC_BLOCKED`

Use if exact named-profile enforcement cannot be demonstrated prospectively on the frozen harness.

### `INVALID`

Use if any D2-S1 model turn/outcome predates the successor lock or predecessor identities were mutated/reused as a retry.

## 15. Authorization after zero-fresh QA

A zero-fresh `SPEC_PASS_IMPLEMENTATION_REQUIRED` authorizes only:

1. deterministic D2-S1 config/profile materialization;
2. successor schema/config identity tests;
3. preturn `permissionProfile/list` + `thread/start` profile-selection qualification;
4. successor final-admission materialization.

It does **not** authorize a model turn.

Exactly one D2-S1 scientific attempt may be authorized only by a later final-admission PASS that freezes the exact successor execution configuration.
