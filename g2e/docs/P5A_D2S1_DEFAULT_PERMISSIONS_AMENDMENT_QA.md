# G2E P5A D2-S1 — Default-Permissions Amendment QA

**Verdict:** `AMENDMENT_PASS_IMPLEMENTATION_REQUIRED`  
**Finding count:** `0`  
**Amendment candidate:** `38c4d4c7f833abf059cec2a96d8fac8543baaa91`  
**Parent spec blob:** `7764ede707b632a18346a650adeb4d1fb23f7f54`  
**Fresh D2-S1 model turn:** NONE  
**Scientific attempt consumed:** FALSE

## 1. Exact-source check

Checked against exact frozen Codex source:

```text
openai/codex
rust-v0.153.4
commit 3d2ee51ca2d5db578f328aa75e20aa22c0197c9a
```

The release source explicitly rejects a non-legacy configured `[permissions]` catalog when no profile selection is resolved and emits:

```text
config defines `[permissions]` profiles but does not set `default_permissions`
```

It also resolves the selected profile from configured `default_permissions` when no stronger override is present.

Therefore adding:

```toml
default_permissions = "g2e_p5a_d2s1"
```

is a protocol/configuration prerequisite of the already-selected custom profile, not an outcome-based scientific rescue.

## 2. Scope audit

The amendment changes only configuration selection metadata.

Unchanged:

- P5-FX-001 input bytes/hash;
- TASK.md bytes/hash;
- expected task output semantics;
- verifier;
- target capabilities;
- exact Codex executable;
- model/provider;
- startup/turn/verifier timeouts;
- network disabled;
- approval policy never;
- MCP/apps isolation;
- read authority;
- write authority;
- runtime-support read rule;
- one-attempt identity;
- zero replacement-attempt budget.

## 3. Attempt-consumption audit

The blocking local invocation reported:

```text
thread_id_present = false
turn_start_request_sent = false
scientific_attempt_consumed = false
result_exists = false
```

Thus D2-S1 attempt 001 remains unused and the bounded amendment occurs before scientific dispatch.

## 4. Conflict / ambiguity audit

Checked for:

- broadening the profile by making it default;
- loss of explicit thread-level profile selection;
- fallback to a built-in workspace profile;
- new inheritance;
- new repository visibility;
- new network access;
- new retry authority;
- scientific identity mutation;
- prompt/fixture/result adaptation;
- preflight evidence reuse.

The amendment requires the configured default and explicit thread selector to be the same exact profile ID, while preserving the exact custom profile authority.

Remaining findings:

```text
0
```

## 5. Authorization

This QA authorizes only:

1. update the deterministic profile materializer with exact `default_permissions`;
2. rebind materializer tests and exact hashes;
3. rerun P1/P1.4/P1.5/P2/P3/P4 + materializer qualification;
4. rebind the no-turn local preflight to the newly frozen hashes;
5. rerun a fresh local preturn qualification.

It does not authorize `turn/start` or any model turn.
