# P5A-CGW First Functional Attempt Preregistration

## Status

PREREGISTRATION CANDIDATE / ZERO-MODEL / NO DISPATCH

## Purpose

Freeze the first model-bearing P5A-CGW functional qualification before any attempt marker or Codex turn exists.

The scientific question is whether the exact G2E -> Codex -> codex-chatgpt-web v4.0.7 -> ChatGPT Web Full-mode route can complete P5-FX-001 while Codex remains the sole local execution authority.

## Exact route

- route: p5a-cgw
- CGW release: 4.0.7
- CGW source: b59d7dc51b84fb1f465ff1d00f5207f3b2b4a494
- installed CGW fingerprint: ac152ad499b1f41b2cafe94a3d05f5d4e4d3cd7ddbb417b9c60b118b08bc3cbb
- exact bridge config fingerprint already admitted at Q0b: f8ba628c60faf5c95409ee3a37ad359f74dd0eb41bb961312b67758f9ba53858
- Codex executable: a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8
- mode: full
- connector: Codex Native2
- loopback route: http://127.0.0.1:17841/v1
- model: chatgpt-web/high
- backend: gpt-5.6-sol
- Codex effort: high
- adapter effort: high

The exact model is frozen prospectively to chatgpt-web/high. v4.0.7 source defines this row directly and marks it non-Pro-only. The prior synthetic route qualification used the same row.

Execution must block before attempt consumption if the local Codex selected-model literal is not exactly chatgpt-web/high. No automatic config/model mutation is allowed.

## Frozen task

Reuse P5-FX-001 exactly:

- input SHA-256: a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6
- TASK.md SHA-256: 4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e
- expected result canonical SHA-256: 6dd3ebce33677409bec596309e061cc421bfa38b3160c5b577ffe5f7fbc9980d

Only result.json may be added. input.json and TASK.md remain immutable.

## Authority

G2E owns attempt/evidence/adjudication authority.

Codex is the sole local execution authority.

CGW is transport/inference mediation only. ChatGPT Web may reason and request admitted tools. Codex Native2/MCP transports a turn-bound capability back to the same outer Codex turn. Bridge-side local filesystem or terminal side effects are forbidden.

Task-level network/web search is denied. The frozen browser transport used for inference is route infrastructure and is the only network path admitted by this contract.

## Consumption and retry

The attempt is consumed only after a durable marker is fsync'd immediately before the sole Codex turn/start transport write.

Pre-marker admission failure does not consume the attempt.

After the marker:

- exactly one turn/start transport write;
- retry budget = 0;
- no automatic retry;
- timeout = 90 seconds;
- no timeout extension;
- no model/mode/connector/prompt/authority mutation;
- no official-route fallback.

## Evidence

Evidence must bind the G2E attempt, outer Codex thread/turn, exact binaries/configs, CGW request, browser response binding, exact model/mode/connector, at least one live Full-mode MCP roundtrip back to Codex, terminal state, workspace mutation and result.

Raw cookies, auth tokens, tunnel credentials, browser storage state and raw capability tokens are forbidden from evidence.

Route/evidence/authority failures adjudicate INVALID, not substantive task FAIL.

## Current authorization

This preregistration itself authorizes no model turn.

Only after static preregistration QA PASS may an execution-envelope lock be created. The lock may freeze one future attempt, but dispatch remains withheld until a bounded functional runner/admission implementation is zero-model qualified.
