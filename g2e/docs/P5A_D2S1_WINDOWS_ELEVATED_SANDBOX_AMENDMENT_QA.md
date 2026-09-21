# G2E P5A D2-S1 — Windows Elevated Sandbox Amendment QA

**Verdict:** `AMENDMENT_PASS_IMPLEMENTATION_REQUIRED`  
**Finding count:** `0`  
**Amendment candidate:** `ab9de956f9ef822d3a5be341ac8a219bc60cf906`  
**Fresh D2-S1 model turn:** NONE  
**Scientific attempt consumed:** FALSE

## 1. Exact-source audit

Checked against exact Codex `rust-v0.153.4` at commit:

```text
3d2ee51ca2d5db578f328aa75e20aa22c0197c9a
```

Confirmed:

- `windows.sandbox` supports `elevated` and `unelevated`;
- `unelevated` maps to the restricted-token backend;
- restricted-token explicitly rejects split filesystem read restrictions rather than silently broadening access;
- elevated backend has dedicated support for split restricted reads;
- elevated readiness is not ready until setup state exists for the selected `CODEX_HOME`;
- App Server exposes `windowsSandbox/readiness`, `windowsSandbox/setupStart`, and `windowsSandbox/setupCompleted`;
- elevated setup state is stored under the selected `CODEX_HOME`.

## 2. Scientific-scope audit

The amendment is not an outcome rescue.

Unchanged:

- P5-FX-001 input hash;
- TASK.md hash;
- task semantics;
- target capability;
- model/provider;
- verifier;
- network disabled;
- approval policy never;
- MCP/apps isolation;
- exact task read paths;
- exact result write path;
- attempt identity;
- retry budget zero.

The only material change is selecting the Windows backend capable of enforcing the already-frozen split filesystem authority.

## 3. Security / authority audit

Rejected alternatives:

- filesystem-root read fallback;
- broad repository read;
- broad workspace read;
- weakening the profile to satisfy restricted-token limitations;
- unsandboxed fallback.

The amendment requires fail-closed elevated setup/readiness instead.

## 4. Attempt-consumption audit

Observed blocked preflight:

```text
profile_present = true
profile_allowed = true
thread_id_present = false
turn_start_request_sent = false
scientific_attempt_consumed = false
result_exists = false
```

Therefore amendment timing is valid and attempt 001 remains unused.

## 5. Local-state audit

Elevated setup may create `.sandbox*` state and sandbox-user secrets under isolated `CODEX_HOME`.

The amendment correctly classifies this as infrastructure state and prohibits:

- Git commit;
- upload;
- token/credential disclosure;
- model task-read access.

Only safe metadata may enter evidence.

## 6. Gate review

```text
WES-Q0 predecessor preflight blocked before thread/turn      PASS
WES-Q1 exact backend limitation source-confirmed             PASS
WES-Q2 elevated backend source-supported for split reads     PASS
WES-Q3 no authority broadening                               PASS
WES-Q4 no fixture/task/verifier change                       PASS
WES-Q5 no retry/attempt-identity change                      PASS
WES-Q6 elevated setup/readiness sequence specified           PASS
WES-Q7 CODEX_HOME secret-state handling bounded              PASS
WES-Q8 config/hash rebinding required                        PASS
WES-Q9 no scientific dispatch authorized                     PASS
```

## 7. Authorization

This QA authorizes only:

1. update deterministic D2-S1 materialization with `windows.sandbox="elevated"`;
2. bind elevated setup/readiness into the local no-turn preflight;
3. run static/regression qualification;
4. execute a fresh local no-turn elevated setup/profile-selection preflight.

It does not authorize `turn/start` or a model turn.
