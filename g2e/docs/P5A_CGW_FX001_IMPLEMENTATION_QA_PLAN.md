# P5A-CGW P5-FX-001 Functional Implementation Qualification

## Status

BOUNDED IMPLEMENTATION CANDIDATE / ZERO-MODEL QA ONLY / DISPATCH FORBIDDEN UNTIL V2

## Predecessor

This workstream is bound to:

- execution envelope v1 blob: `22cefe57c214cf58c759fd76ad25fff9dba834cb`;
- execution config blob: `aea462b84e4583096129820d2a17417803d0f6a2`;
- execution config canonical SHA-256:
  `b7097e8a63607e33f520ab370e48106fc7234f782204e3c366be409b5b594ab8`;
- reserved attempt:
  `p5a-cgw-v4-p5-fx-001-attempt-001`.

No normative runtime, route, model, task, result, authority, consumption or evidence rule may change in this implementation lane.

## Components

The bounded implementation contains four execution-support components:

1. predispatch admission;
2. functional runner;
3. independent verifier;
4. Windows one-click wrapper.

The qualification workflow imports/tests these components only. It MUST NOT invoke their live execution entrypoints against Codex/CGW.

## Predispatch admission

Before attempt consumption it must prove:

- exact CGW 4.0.7 config fingerprint;
- exact CGW/Codex binary fingerprints;
- healthy and idle loopback bridge;
- Full mode / Codex Native2;
- isolated Codex config selects exactly `chatgpt-web/high`;
- exact `127.0.0.1:17841/v1` route;
- bounded permission profile;
- exact P5-FX-001 workspace prestate;
- no existing attempt marker;
- browser-diagnostic baseline and launcher-log byte offset captured.

A predispatch mismatch remains BLOCK / attempt not consumed.

## Consumption

The runner must contain exactly one scientific `turn/start` path.

The ordering is frozen:

`predispatch PASS -> Codex control-plane/thread preparation -> marker fsync -> consumed=true -> sole turn/start write`

The 90-second timeout and retry budget zero remain unchanged.

## Route evidence

The implementation uses evidence surfaces already present in exact CGW v4.0.7; it does not patch the bridge.

Exact source mechanisms:

- turn broker blob `6017bbaafd87c58078a72dbac42e843d5bcf3209`;
- MCP server blob `51d9c787f93c391fba70f68ce759c673d789275d`;
- browser worker blob `4e82981a28158e65705f31213bfbd123a6be5e2e`;
- launcher browser host blob `305fd64d7c99b2d0b47442bc03b40f07349e8da9`;
- launcher helper client blob `db85083d54ba372c77df8819a0382edd5760afdd`;
- runtime supervisor source at the same frozen v4.0.7 source commit.

The route projection must correlate one fresh trace across:

- broker registration;
- privacy-safe capability-token fingerprint;
- one fresh browser diagnostic surface;
- `send-accepted`;
- `response-visible`;
- `turn-completed`;
- MCP tool name;
- broker completed-call prefix;
- full outer Codex item id from the Codex protocol.

The v4 broker exposes only a 12-hex SHA-256 token fingerprint and a 17-character completed-call prefix. The implementation MUST NOT describe either as stronger evidence than the source exposes. A full invocation ID is admitted only when an outer Codex item ID matches the broker prefix.

## Verifier

The verifier is verdict-neutral.

It materializes the original six P5-FX-001 metrics and adjudication inputs but never assigns PASS/FAIL/INVALID itself.

Evidence integrity requires the live MCP route correlation. Missing/ambiguous route, browser binding, tool correlation, unexpected server approval/request, or forbidden web search makes the evidence non-admissible.

## One-click wrapper

The Windows wrapper must:

- require a future v2 dispatch lock;
- verify exact component blobs and execution-config blob;
- preserve exact Python and Codex executable paths across UAC elevation;
- create an isolated NTFS VHDX;
- create isolated Codex home/config;
- call only loopback `/healthz` before dispatch;
- run admission before runner;
- cleanly dismount the VHDX in `finally`.

The QA workflow parses and inspects the wrapper but never executes its live path.

## Zero-model qualification gates

- I0 predecessor v1/config identities exact;
- I1 admission synthetic PASS/BLOCK behavior;
- I2 one marker / one turn-start / retry=0 / timeout=90;
- I3 fresh trace + browser-surface correlation;
- I4 token fingerprint + MCP call + full Codex item correlation;
- I5 secret minimization and no raw capability token;
- I6 verifier metrics and verdict neutrality;
- I7 missing MCP / authority failure fail-closed;
- I8 Windows PowerShell parser + UAC path preservation + VHDX cleanup surface;
- I9 preregistration and exact-v4 regressions.

## Promotion rule

Only if the complete Linux and Windows zero-model macro-gate passes may v1 be promoted to:

`DISPATCH_AUTHORIZED_EXECUTION_LOCK_V2`

V2 may add only:

- exact admission/runner/verifier/one-click blobs;
- exact QA workflow/test/plan blobs;
- authoritative zero-model QA run/artifact identities.

Any normative contract change requires a new lineage instead of promotion.

Promotion authorizes at most one future local dispatch. Promotion itself executes no model turn and consumes no attempt.
