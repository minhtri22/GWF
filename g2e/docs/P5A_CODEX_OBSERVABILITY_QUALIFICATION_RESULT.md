# G2E P5A-CODEX-OQ1 — Observability Qualification Result

## Verdict

**PASS — CODEX_TERMINAL_ERROR_OBSERVABILITY_QUALIFIED**

The P5A Codex adapter now has a qualified, privacy-safe mechanism for preserving terminal failure
evidence without widening runtime authority or executing a model turn.

## Qualified candidate

- SHA: `bc06d9b75736407fc68018c6d5b81965c756e2bc`
- observability blob:
  `b6d3c6fcb671dd166893edd46388c8d69dca9105`
- test blob:
  `18aae7d6f23db5671c87619dfdc6a856b6dde870`
- workflow blob:
  `7f243f603bf1d8793a0f741e55b750871d9c7f1a`

Workflow:

- run `35789231154`
- Linux job `106953454697`: PASS
- Windows job `106953454444`: PASS
- artifact `10721262192`
- digest:
  `sha256:6ca1242dac89398430b164a4392a47e0b5d8419150f40734f566322c48beda26`

## Exact upstream compatibility

Frozen upstream:

`openai/codex@3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`

CI fetched and exact-Git-blob verified:

- `thread_data.rs`:
  `649a94be493dadac887a9eb67cecae1365ff3c1e`
- `notification.rs`:
  `ca0e7753f3c007e544b3507881b6cffeecacd`
- `ErrorNotification.json`:
  `69187dd539dfa5f676397444b3e36a426884b81d`
- `TurnCompletedNotification.json`:
  `7db8c18c82325feee77876ed7172dae8125a4cd5`

The qualified component preserves:

- `TurnError.message` as redacted text + raw hash/length;
- complete structural `codexErrorInfo` classification;
- `additionalDetails` as redacted text + raw hash/length;
- `willRetry`;
- bounded misalignment mechanism fields;
- turn/thread identity, terminal status, raw protocol hash/length.

## Privacy result

PASS fixtures verify redaction of:

- Bearer credentials;
- API-key/token-like values;
- secret-bearing object keys;
- recognizable user-home paths.

Unrelated protocol payloads remain method/hash/timing-only.

## Zero-model result

Qualification did not:

- start Codex/App Server;
- send RPC;
- execute `thread/start` or `turn/start`;
- run P5-FX-001;
- expose any new model outcome.

## Governance consequence

The prior D2-S4 verdict remains immutable:

`INVALID / CONSUMED / NO RETRY`.

P5A remains open.

This PASS authorizes only design/preregistration of a new functional successor with a new attempt
identity and this exact observability blob bound prospectively.

No successor model execution is authorized by this result.
