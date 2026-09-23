# P5A-CGW P5-FX-001 Execution Envelope Lock

## Status

**EXECUTION_ENVELOPE_LOCKED / DISPATCH WITHHELD / ZERO MODEL**

Preregistration qualification passed on exact candidate `5efb9a48556be0f1e61d47d94b63f6ee2391fb4e`.

- run: `35807190228`
- Linux: `107010545413` PASS
- Windows: `107010545129` PASS
- artifact: `10728505435`
- artifact digest: `sha256:a4e97b27420135c8475079870b41eb2947f6b997aa2c6bb12e7c70eef325df4d`
- preregistration file SHA-256: `8b25e5fce8e2c69bd6ff79b1a9ead9854d5d6311bb50878cd26c32e559a78324`
- preregistration canonical contract SHA-256: `061a4d897c87b1176f3fe8ac11fa5efc6839d18626328ce3395698012d704ec6`

The frozen execution config is `g2e/config/P5A_CGW_FX001_EXECUTION_CONFIG.json`.

- Git blob: `aea462b84e4583096129820d2a17417803d0f6a2`
- file SHA-256: `a15f8a44d50625fae00e6472e997ccc56ddacd4a938a3c02a2d16802d1bb2e7a`
- canonical SHA-256: `b7097e8a63607e33f520ab370e48106fc7234f782204e3c366be409b5b594ab8`

## Frozen attempt

Study:

`p5a-cgw-v4-p5-fx-001-functional-qualification`

Attempt:

`p5a-cgw-v4-p5-fx-001-attempt-001`

Route:

`Codex -> 127.0.0.1:17841/v1 -> codex-chatgpt-web 4.0.7 Full / Codex Native2 -> chatgpt-web/high -> gpt-5.6-sol`

Codex executable SHA-256:

`a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8`

CGW installed binary SHA-256:

`ac152ad499b1f41b2cafe94a3d05f5d4e4d3cd7ddbb417b9c60b118b08bc3cbb`

## Frozen task/result

P5-FX-001 is unchanged.

- input SHA-256: `a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6`
- TASK.md SHA-256: `4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e`
- expected canonical result SHA-256: `6dd3ebce33677409bec596309e061cc421bfa38b3160c5b577ffe5f7fbc9980d`
- exact result keys: `count, input_sha256, sorted_unique_values, sum`

## Authority and consumption

Codex remains the sole local execution authority. CGW and Codex Native2 are transport/capability mediation only.

The attempt is consumed only after a durable marker is fsync'd immediately before the sole Codex `turn/start` transport write.

Retry budget is zero. Timeout is 90 seconds. Model, mode, connector, route, task, permission or timeout changes after the marker are forbidden.

A local selected-model mismatch is a pre-marker BLOCK and does not consume the attempt. The runner must not rewrite local model/config state automatically.

## Evidence

A valid future execution must bind the exact G2E attempt, Codex outer thread/turn, bridge request, browser response binding, exact route/model/mode, and at least one live Full-mode MCP roundtrip whose executor is Codex.

Secret-bearing raw cookies, auth/tunnel credentials and raw capability tokens are forbidden from evidence.

## Dispatch boundary

This v1 lock freezes the execution envelope but does **not** authorize dispatch.

Before a model turn may be sent, a bounded functional runner/admission/verifier implementation must pass zero-model QA and bind its exact component blobs. A v2 promotion may only add those implementation identities and QA evidence.

Changing any frozen runtime, route, model, task, result, authority, consumption or evidence requirement requires a new lineage instead of v1 -> v2 promotion.
