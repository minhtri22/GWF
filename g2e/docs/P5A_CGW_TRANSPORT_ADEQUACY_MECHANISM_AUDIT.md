# P5A-CGW Transport Adequacy v1 — Mechanism Audit

## Status

**INFRASTRUCTURE STUDY ONLY — NO DISPATCH**

This program starts after formal closure of the consumed V2R6 attempt. It does not reopen, rearm,
replace, reinterpret, or retry `p5a-cgw-v4-p5-fx-001-attempt-001`.

## Question

Did the GWF execution harness preserve the lifecycle contract of the qualified
`codex-chatgpt-web` Full-mode route long enough for the outer Codex turn to complete, and did the
verifier keep transport/evidence failures separate from authority violations?

## Source-locked upstream facts

### codex-chatgpt-web v4.0.7

Exact source commit:

`b59d7dc51b84fb1f465ff1d00f5207f3b2b4a494`

The qualified architecture is a bidirectional loop:

```text
outer Codex Responses request
        |
        v
codex-chatgpt-web daemon
        |
        v
ChatGPT Web browser turn
        |
        | Codex Native2 over OpenAI Tunnel / MCP
        v
turn broker
        |
        | tool_call over Responses/SSE
        v
outer Codex executes local tool
        |
        | tool result in same canonical turn
        v
ChatGPT Web continues
        |
        v
final browser response -> Responses completion
```

Source contracts relevant to the V2R6 failure:

- browser turns have **no absolute deadline by default** (`turnTimeoutMs` is optional);
- the bridge emits parser-ignored `response.heartbeat` frames every 2 s during upstream silence;
- the shipped bridge stall budget is **300 s**;
- the source comment explicitly records that this budget was raised **from 90 s** so long reasoning
  and large tool writes are not cut mid-turn;
- one MCP invocation is bounded at **90 s**;
- the OpenAI tunnel owns an approximately **120 s** command-response deadline;
- tool calls and tool results stay in the same ChatGPT response while outer Codex executes them.

These are transport/liveness contracts. They do not authorize a GWF-level 90 s absolute turn
deadline.

### openai/codex 0.153.4

Exact release tag: `rust-v0.153.4`

Tag target commit:

`3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`

Codex consumes the Responses stream and the app-server exposes terminal turn completion as
`turn/completed`. Tool calls are ordinary Responses items and their outputs return into subsequent
same-turn model requests. The local route's heartbeat exists specifically to keep Codex's streamed
Responses transport alive while upstream work continues.

## V2R6 spent evidence and implementation mismatch

Frozen runner blob:

`678504c62cbd9afe1f6a0fd0b39c5147973bad8d`

It contains:

```text
TURN_TIMEOUT_S = 90.0
...
deadline = time.monotonic() + TURN_TIMEOUT_S
...
if remaining <= 0:
    return terminal=False, timeout=True
```

After that timeout, the runner terminates the app-server process in `finally`.

Therefore the outer harness imposed an absolute 90 s lifetime on a Full-mode turn whose qualified
upstream contract intentionally permits healthy turns to exceed 90 s. In particular, a **single**
valid MCP invocation may itself consume up to that same 90 s budget, before browser continuation,
final answer, and app-server `turn/completed` are observed.

This is a transport-contract mismatch. It is sufficient to explain why a valid in-progress Full-mode
turn can be killed by the harness before terminal evidence exists. It does **not**, by itself, prove
that the model, browser route, MCP tunnel, or outer Codex executor failed.

## Verifier signal conflation

Frozen verifier blob:

`c37052a00f3cef97b138c83c632e80ae88323142`

The V2R6 verifier computes authority violation using:

```text
web_search_seen
OR unexpected_server_requests
OR NOT route_check.valid
```

This mixes four logically different classes:

```text
route evidence incomplete
    -> evidence integrity failure

unexpected server request
    -> protocol/client-coverage failure

prohibited tool/network activity
    -> execution-scope violation

bridge/local execution outside outer Codex authority
    -> authority violation
```

Consequently, V2R6's reported `authority_violation=true` cannot be interpreted as positive evidence
that authority escaped outer Codex when `route_check.valid=false` is already sufficient to set it.

## Mechanism verdict

For infrastructure purposes only:

`INFRASTRUCTURE_CONTRACT_MISMATCH_CONFIRMED`

Confirmed defects:

1. GWF imposed a 90 s absolute outer-turn timeout that is not part of the qualified Full-mode
   contract and is shorter than the upstream healthy-turn liveness regime.
2. The verifier conflated route-evidence invalidity with authority violation.
3. Existing zero-model QA explicitly asserted `TURN_TIMEOUT_S = 90.0`, so the QA suite protected
   the wrong assumption rather than testing transport compatibility.

This does **not** alter the scientific adjudication of the spent attempt. V2R6 remains
`INVALID — SPENT`.

## Required future contract

Any future qualification is a **new preregistered attempt**, never a retry/rearm of V2R6.

Before such an attempt can be authorized:

- no scientific PASS/FAIL may be driven by a GWF absolute 90 s turn deadline;
- qualified upstream liveness owns transport continuation;
- any operator safety guard is administrative only and, if triggered, yields infrastructure INVALID;
- route invalidity must remain evidence-integrity failure, not become authority violation;
- unexpected app-server requests must remain protocol-coverage failure unless their semantics
  independently prove an authority breach;
- scope violations and authority violations must be separately represented;
- zero-model tests must cover these distinctions.

## Firewall

This study performs no model turn, browser submission, MCP invocation, marker creation, or scientific
attempt consumption.
