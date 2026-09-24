# P5A-CGW FX001 TC-003 — Pre-UAC Runtime-Health Readiness Repair

## Origin

TC-002 stopped before admission and before the durable consumption marker.
The exact execution report was `EXECUTION_WRAPPER_ERROR` with diagnostic
`Unable to connect to the remote server`. Admission, runner, protocol,
route, verifier and marker artifacts were absent. VHDX cleanup succeeded.

The scientific attempt therefore remains `RESERVED_UNCONSUMED`.

TC-002 evidence is immutable and must not be reused.

## Repair

TC-003 uses fresh root:

`g2e/.local/P5A-CGW-FX001-TC-003`

and adds one bounded infrastructure guard:

> Before UAC elevation, VHDX creation, LocalRoot creation, admission, runner,
> marker or any scientific dispatch, GET the qualified loopback health
> endpoint and require the bridge to be healthy, exact-version/mode/port,
> accepting turns, and idle.

Required health projection:

- status = ok
- service = codex-chatgpt-web
- version = 4.0.7
- mode = full
- port = 17841
- accepting_turns = true
- active_http_turns = 0
- active_browser_turns = 0

If health is unavailable or mismatched, TC-003 fails before UAC/root creation.

## Unchanged

The TC-002 semantic admission implementation is reused unchanged.
Runner, verifier, execution config, task fixture, authority invariant,
consumption boundary, max scientific dispatches=1, retry budget=0 and
no-scientific-absolute-turn-deadline remain unchanged.

## Activation

No live dispatch is authorized by this plan.

First:
1. static/zero-model TC-003 QA;
2. local TC-003 `-PreflightOnly` while the qualified CGW service is active;
3. formal preflight adjudication;
4. only then a fresh TC-003 execution lock candidate may be considered.
