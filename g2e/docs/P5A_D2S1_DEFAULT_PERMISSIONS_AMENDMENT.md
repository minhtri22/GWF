# G2E P5A D2-S1 — Bounded Default-Permissions Amendment

**Status:** FROZEN CANDIDATE FOR ZERO-FRESH QA  
**Parent specification:** `P5A_D2S1_PERMISSION_PROFILE_SUCCESSOR_PREIMPLEMENTATION.md`  
**Parent spec blob:** `7764ede707b632a18346a650adeb4d1fb23f7f54`  
**Observed local preflight:** BLOCKED BEFORE THREAD/ TURN  
**Model turn:** NOT SENT  
**Scientific attempt consumed:** FALSE  
**Scope:** Codex 0.153.4 configuration prerequisite only

## 1. Trigger

The first D2-S1 local preturn invocation reached App Server initialization but failed on the first post-initialize config reload with:

```text
failed to reload config:
config defines `[permissions]` profiles but does not set `default_permissions`
```

The preflight evidence reported:

```text
turn_start_request_sent = false
scientific_attempt_consumed = false
thread_id_present = false
result_exists = false
input_unchanged = true
task_unchanged = true
```

Therefore this is a preturn configuration blocker, not a scientific outcome and not a consumed D2-S1 attempt.

## 2. Exact-source confirmation

The exact frozen Codex release is:

```text
openai/codex
tag: rust-v0.153.4
commit: 3d2ee51ca2d5db578f328aa75e20aa22c0197c9a
```

Exact release source in `codex-rs/core/src/config/mod.rs` rejects an active `[permissions]` catalog when:

- profiles exist;
- syntax is not legacy;
- no selected profile exists;
- requirements do not force selection.

The emitted error is exactly:

```text
config defines `[permissions]` profiles but does not set `default_permissions`
```

The same source resolves the selected profile from an explicit override or configured `default_permissions`.

## 3. Amendment

The D2-S1 successor config MUST now contain the top-level assignment:

```toml
default_permissions = "g2e_p5a_d2s1"
```

before the custom profile definition.

The custom profile itself remains exactly:

```text
profile id:
g2e_p5a_d2s1

READ:
  exact successor workspace/input.json
  exact successor workspace/TASK.md

WRITE:
  exact successor workspace/result.json

NETWORK:
  disabled

inheritance:
  none
```

This amendment does not broaden filesystem, network, approval, MCP, app, model, prompt, fixture or retry authority.

## 4. Selection semantics

The successor uses the same profile identity for both:

```text
configured default_permissions
=
explicit thread/start permissions
=
g2e_p5a_d2s1
```

The explicit `thread/start.permissions` assertion remains mandatory.

The configured default exists only because the frozen Codex 0.153.4 config loader requires a selected profile whenever a non-legacy `[permissions]` catalog is defined.

The preturn qualification MUST prove all of:

```text
permissionProfile/list contains g2e_p5a_d2s1
allowed = true
thread/start permissions = g2e_p5a_d2s1 accepted
activePermissionProfile.id = g2e_p5a_d2s1, if emitted
```

## 5. Re-materialization rule

The previous materialized profile pack is superseded for future D2-S1 execution because adding `default_permissions` changes `config.toml` bytes.

Therefore the following MUST receive new frozen values before any subsequent local preflight:

- `config.toml` SHA-256;
- execution-config hash;
- materialized contract SHA-256;
- implementation candidate SHA;
- local preflight expected constants.

The scientific fixture/task hashes do not change.

## 6. No-rescue / outcome firewall

This amendment is admissible because no D2-S1 `turn/start` has occurred.

It is forbidden to change:

- fixture bytes;
- TASK.md;
- expected result semantics;
- verifier arithmetic;
- capability target;
- model/provider;
- timeout;
- retry budget;
- scientific attempt identity;
- task authority.

D2-S1 attempt identity remains:

```text
p5a-d2s1-p5-fx-001-attempt-001
```

and remains unused.

## 7. Required QA

Before local preflight may resume:

1. zero-fresh amendment QA must PASS with findings=0;
2. deterministic profile materializer must be updated;
3. tests must prove `default_permissions` equals the exact custom profile ID;
4. P1/P1.4/P1.5/P2/P3/P4 regressions must PASS;
5. canonical profile pack must be re-materialized and independently verified;
6. local no-turn preflight implementation constants must be rebound to the new config/execution hashes;
7. local preflight must use a fresh CODEX_HOME and fresh evidence directory.

No scientific model turn is authorized by this amendment.
