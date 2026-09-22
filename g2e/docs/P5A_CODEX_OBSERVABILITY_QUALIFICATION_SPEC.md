# G2E P5A-CODEX-OQ1 — Observability Qualification

## Status

PREREGISTERED / ZERO-MODEL / OUTCOME-INDEPENDENT / BOUNDED IMPLEMENTATION

## 1. Question

Can the Codex adapter preserve enough terminal-error evidence to classify a failed turn while preventing
credential leakage and without widening execution authority?

## 2. Exact upstream protocol identity

Frozen Codex source:

- repository: `openai/codex`
- commit: `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`
- release: `rust-v0.153.4`

Exact protocol artifacts:

- `v2/thread_data.rs` Git blob:
  `649a94be493dadac887a9eb67cecae1365ff3c1e`
- `v2/notification.rs` Git blob:
  `ca0e7753f3cb3c007e544b3507881b6cffeecacd`
- `schema/json/v2/ErrorNotification.json` Git blob:
  `69187dd539dfa5f676397444b3e36a426884b81d`
- `schema/json/v2/TurnCompletedNotification.json` Git blob:
  `7db8c18c82325feee77876ed7172dae8125a4cd5`

The exact protocol specifies:

- `ErrorNotification.error: TurnError`;
- `ErrorNotification.willRetry: bool`;
- `ErrorNotification.threadId`;
- `ErrorNotification.turnId`;
- failed `Turn.error: TurnError | null`;
- `TurnError.message`;
- `TurnError.codexErrorInfo`;
- `TurnError.additionalDetails`;
- optional `TurnError.misalignment`.

## 3. Required observability projection

For protocol method `error`, preserve:

- method;
- threadId;
- turnId;
- willRetry;
- privacy-safe projection of `TurnError.message`;
- complete structural `codexErrorInfo` classification;
- privacy-safe projection of `additionalDetails`;
- privacy-safe mechanism projection of `misalignment`, when present;
- raw message length and SHA-256 for integrity.

For `turn/completed`, preserve:

- method;
- threadId;
- turn.id;
- turn.status;
- the same privacy-safe TurnError projection when `turn.error` is present;
- raw message length and SHA-256.

Other protocol messages may remain method/hash/timing-only unless a separately qualified requirement
needs more fields.

## 4. Privacy contract

The evidence projection MUST NOT persist:

- Authorization/Bearer credentials;
- API keys or token-like `sk-...` values;
- values under keys matching token/password/secret/credential/api-key patterns;
- user-home path identity when recognizable;
- unrelated prompt/content payloads.

For redacted text fields, preserve:

- redacted text;
- original raw-field SHA-256;
- raw-field length;
- `redaction_applied` boolean.

`codexErrorInfo` must preserve its classification/variant and non-secret scalar metadata such as
`httpStatusCode`.

## 5. Synthetic failed-turn qualification

ZERO-MODEL tests MUST cover at least:

1. `error` notification with:
   - message;
   - string `codexErrorInfo`;
   - additionalDetails;
   - willRetry=false;
2. structured `codexErrorInfo` with `httpStatusCode`;
3. secret-bearing message/additionalDetails redaction;
4. secret-bearing object keys redaction;
5. user-home path redaction;
6. `turn/completed(status=failed)` with `turn.error`;
7. completed turn with `error=null`;
8. unrelated protocol methods remain payload-minimal;
9. projection is deterministic for identical input;
10. raw hashes/lengths remain stable even when text is redacted.

## 6. Exact protocol compatibility

CI MUST retrieve the four exact upstream protocol artifacts from the frozen commit, verify their Git blob
IDs, and independently verify:

- `ErrorNotification` requires `error/threadId/turnId/willRetry`;
- `TurnError.message` exists and is required;
- `codexErrorInfo`, `additionalDetails`, `misalignment` exist;
- `TurnCompletedNotification.turn` resolves to a Turn containing `status` and `error`;
- Turn status admits `failed`.

Compatibility failure blocks qualification.

## 7. Zero-model firewalls

Qualification MUST NOT:

- start Codex/App Server;
- send RPC;
- dispatch `thread/start` or `turn/start`;
- mount a scientific VHDX;
- access D2-S4 auth/config credentials;
- execute P5-FX-001;
- expose a new model outcome.

## 8. Regression surface

PASS requires:

- observability synthetic tests PASS;
- exact upstream protocol compatibility PASS;
- secret-redaction negative tests PASS;
- deterministic projection PASS;
- Python compile PASS;
- P1/P1.4/P1.5/P2/P3/P4 regressions PASS;
- Windows Python qualification PASS;
- no model turn.

## 9. PASS consequence

PASS means:

`CODEX_TERMINAL_ERROR_OBSERVABILITY_QUALIFIED`.

It authorizes only the **design/preregistration** of a successor functional qualification attempt with a
new attempt identity and this exact observability component bound prospectively.

It does not authorize execution of that successor.

## 10. FAIL consequence

Any privacy leak, protocol mismatch, non-deterministic projection, or hidden model execution yields
qualification failure and blocks successor design.
