# G2E P5A D2-S1 — Zero-Fresh Specification QA

**Verdict:** `SPEC_PASS_IMPLEMENTATION_REQUIRED`  
**Finding count:** `0`  
**Spec candidate:** `3d955b64621e1346ecb2d3fdc6196f8acb6ae888`  
**Spec blob:** `7764ede707b632a18346a650adeb4d1fb23f7f54`  
**Predecessor closure baseline:** `d6610cb2d996a85bd194b9796490fb206fd95ec5`  
**Fresh D2-S1 model turn:** NONE  
**Runtime adapter authorization:** NONE

## 1. Independent protocol-source check

Exact upstream source identity checked:

```text
openai/codex
rust-v0.153.4
commit 3d2ee51ca2d5db578f328aa75e20aa22c0197c9a
```

Audited blobs:

```text
app-server-protocol/src/protocol/v1.rs
17013b528f92e67dcbef37731989a21dbd3d1108

app-server-protocol/src/protocol/common.rs
6c00f889f55cdf0be495a39c8693610af9a40010

app-server-protocol/src/protocol/v2/thread.rs
2a08c9fd1d4c6bf478a3c7881816c7766d3c4b59

app-server-protocol/src/protocol/v2/turn.rs
9629a784102d9d16a93b5a2646a35ca5948b74a6

app-server-protocol/src/protocol/v2/permissions.rs
38747f0ada6a4637ffdb485e462df0d10810cf80

app-server/src/message_processor.rs
8e78c929e14b65fa7189d8597ed7a077c805003e

config/src/permissions_toml.rs
98fd3534d62b304b0bee37810386c7f94e90e20b

core/src/config/permissions.rs
894d9c60ba64ae6a3af37e48dd664fe5a10665b9

core/config.schema.json
24d7988b04e801005ee926ea8381ae21f6ff1ab6
```

Confirmed independently:

- initialize capability `experimentalApi` exists and gates experimental fields;
- `thread/start.permissions` is an experimental named-profile selector;
- `turn/start.permissions` is an experimental named-profile selector;
- named `permissions` cannot be combined with legacy `sandbox`/`sandboxPolicy`;
- `permissionProfile/list` exists as a stable read of profile IDs/allowed state;
- top-level `permissionProfile` is explicitly rejected for thread/turn start;
- restricted legacy `workspaceWrite.readOnlyAccess` is explicitly rejected;
- custom profiles support filesystem entries plus network disable;
- non-special filesystem entries must be absolute paths;
- restricted-read runtime may add exact harness-support helper reads, so the spec's runtime-support-read closure is required rather than silently assuming literal two-path process visibility.

No source/spec conflict remains.

## 2. Gate review

| Gate | Review | Status |
|---|---|---|
| S1-Q0 | D2 attempt 001 frozen INVALID; spent identity is not reused | PASS |
| S1-Q1 | exact executable, release tag/commit and protocol schema identities bound | PASS |
| S1-Q2 | P5-FX-001 input/TASK hashes unchanged | PASS |
| S1-Q3 | successor proof/binding/attempt IDs are fresh and disjoint | PASS |
| S1-Q4 | named permission-profile semantics explicit; no legacy readOnlyAccess | PASS |
| S1-Q5 | experimental API negotiation explicitly required | PASS |
| S1-Q6 | deterministic config.toml and exact absolute task paths required before dispatch | PASS |
| S1-Q7 | implicit runtime-support reads are explicitly classified and bounded | PASS |
| S1-Q8 | no-turn permissionProfile/list + thread/start preflight required | PASS |
| S1-Q9 | one scientific attempt; replacement/retry budget zero | PASS |
| S1-Q10 | six metrics and PASS/FAIL/INVALID semantics preserved | PASS |
| S1-Q11 | no D2-S1 model turn/result/outcome exists before this lock | PASS |
| S1-Q12 | downstream implementation must retain P1/P1.4/P1.5/P2/P3/P4 regression gate | PASS |

## 3. Ambiguity / conflict audit

Checked specifically for:

- retry disguised as successor study;
- predecessor identity reuse;
- permissionProfile vs permissions naming conflict;
- sandbox + permissions simultaneous use;
- experimental-field use without capability negotiation;
- broad workspace write authority;
- network ambiguity;
- hidden user MCP/plugin inheritance;
- relative-path interpretation;
- platform/runtime helper-read ambiguity;
- result-dependent prompt/config adaptation;
- verifier conversion of unobservable metrics to FAIL;
- model turn authorization leaking out of pre-implementation phase.

Remaining findings:

```text
0
```

## 4. Authorization

This QA authorizes **implementation only**:

1. deterministic D2-S1 config/profile materializer;
2. exact profile/config identity tests;
3. no-turn profile-selection preflight;
4. final-admission materializer and exact-SHA regression QA.

It does not authorize `turn/start`.

A scientific D2-S1 model turn remains prohibited until a later final-admission artifact proves the exact successor configuration and explicitly opens one attempt.
