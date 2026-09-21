# G2E P5A D2-S1 — Windows Elevated Sandbox Amendment

**Status:** FROZEN CANDIDATE FOR ZERO-FRESH QA  
**Parent specification:** `P5A_D2S1_PERMISSION_PROFILE_SUCCESSOR_PREIMPLEMENTATION.md`  
**Prior amendment:** `P5A_D2S1_DEFAULT_PERMISSIONS_AMENDMENT.md`  
**Observed local preflight:** BLOCKED BEFORE THREAD CREATION  
**Model turn:** NOT SENT  
**Scientific attempt consumed:** FALSE  
**Scope:** exact Codex 0.153.4 Windows sandbox backend prerequisite only

## 1. Trigger

The amended D2-S1 profile was successfully loaded and listed:

```text
configured_mcp_count = 0
installed_app_count = 0
auth_ready = true
profile_present = true
profile_allowed = true
```

The first `thread/start` using the exact custom profile then failed before thread creation with:

```text
windows unelevated restricted-token sandbox cannot enforce split filesystem
read restrictions directly; refusing to run unsandboxed
```

The same evidence reported:

```text
thread_id_present = false
turn_start_request_sent = false
scientific_attempt_consumed = false
result_exists = false
input_unchanged = true
task_unchanged = true
```

Therefore this is a preturn platform-enforcement blocker, not a scientific outcome.

## 2. Exact-source confirmation

The frozen harness remains Codex `rust-v0.153.4`, commit:

```text
3d2ee51ca2d5db578f328aa75e20aa22c0197c9a
```

Exact release source establishes:

1. `windows.sandbox` accepts `elevated` or `unelevated`.
2. `unelevated` maps to the restricted-token backend.
3. the restricted-token backend explicitly rejects split filesystem read restrictions and refuses to run unsandboxed.
4. the elevated backend explicitly supports split restricted read policies.
5. elevated readiness is `UpdateRequired` until elevated setup is complete for the selected `CODEX_HOME`.
6. App Server exposes:
   - `windowsSandbox/readiness`;
   - `windowsSandbox/setupStart` with `mode="elevated"` and optional absolute `cwd`;
   - `windowsSandbox/setupCompleted` with `mode`, `success`, and optional `error`.
7. elevated setup state is stored under the selected `CODEX_HOME`, including a setup marker beneath `.sandbox`.

## 3. Amendment

D2-S1 MUST use the exact Windows elevated sandbox backend:

```toml
[windows]
sandbox = "elevated"
```

The custom permission profile remains unchanged:

```text
default_permissions = g2e_p5a_d2s1

READ:
  exact successor workspace/input.json
  exact successor workspace/TASK.md

WRITE:
  exact successor workspace/result.json

NETWORK:
  disabled
```

No broader filesystem authority is permitted as a fallback.

In particular, D2-S1 MUST NOT rescue the unelevated backend by granting filesystem-root read access, broad workspace read, repository read, or deny/read carveouts that weaken the frozen task authority.

## 4. Elevated setup is a preturn infrastructure gate

Before any successor scientific turn, a fresh successor `CODEX_HOME` must undergo elevated sandbox preparation.

Allowed no-turn sequence:

```text
initialize
  ↓
windowsSandbox/readiness
  ↓
if status == updateRequired:
    windowsSandbox/setupStart(mode=elevated, cwd=<exact execution workspace>)
    ↓
    wait for windowsSandbox/setupCompleted
    ↓
    require mode=elevated
    require success=true
  ↓
windowsSandbox/readiness
  ↓
require status=ready
  ↓
MCP/apps/auth/profile checks
  ↓
thread/start permissions=g2e_p5a_d2s1
  ↓
STOP
```

No `turn/start` is permitted anywhere in elevated setup/preflight code.

If Windows requests elevation/UAC during `setupStart`, user approval of that operating-system setup prompt is an infrastructure action only. It is not permission for the agent/model to broaden task authority.

## 5. CODEX_HOME mutation and evidence

Elevated setup is expected to create sandbox control/state below the isolated successor `CODEX_HOME`, including implementation-owned `.sandbox*` state.

Those files:

- are infrastructure state, not task input;
- must remain outside Git;
- must remain under `g2e/.local/P5A-D2S1/`;
- must never be exposed to the model as task-readable paths;
- may contain sandbox credentials/control data and must not be uploaded or committed.

The preturn evidence may record only safe metadata such as:

- readiness before/after;
- setup mode;
- setup success boolean;
- names of top-level sandbox-state directories;
- config.toml SHA-256;
- no credential contents.

## 6. Config identity

Adding `[windows] sandbox = "elevated"` changes canonical `config.toml` bytes and therefore requires new frozen:

- config.toml SHA-256;
- execution-config hash;
- contract-file SHA-256;
- materializer candidate;
- local-preflight expected constants.

The execution-config hash MUST additionally cover:

```text
windows_sandbox_mode = elevated
windows_sandbox_setup_required = true
windows_sandbox_setup_cwd = exact execution workspace
windows_sandbox_readiness_required = ready
```

The scientific fixture/task hashes and attempt identity remain unchanged.

## 7. No-rescue / no-outcome-tuning

This amendment changes only the platform enforcement backend required to implement the already-frozen split filesystem authority.

It does not change:

- fixture;
- TASK.md;
- expected result;
- verifier;
- capability target;
- model/provider;
- network authority;
- approval policy;
- MCP/apps isolation;
- task read/write authority;
- retry budget;
- scientific attempt identity.

D2-S1 attempt remains:

```text
p5a-d2s1-p5-fx-001-attempt-001
```

and remains unused.

## 8. Required qualification

Before local preflight resumes:

1. this amendment must pass zero-fresh QA;
2. profile materializer must emit `[windows] sandbox = "elevated"`;
3. tests must freeze elevated mode and forbid unelevated fallback;
4. P1/P1.4/P1.5/P2/P3/P4 regressions must pass;
5. a no-turn elevated-setup/preflight implementation must be statically qualified;
6. local execution must use a fresh isolated `CODEX_HOME`;
7. previous blocked preflight evidence must be archived, never overwritten.

No scientific model turn is authorized by this amendment.
