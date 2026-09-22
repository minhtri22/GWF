# G2E P5A-CGW — Trust, Dataflow, Identity, Authority, Observability and Fail-Closed Contract

## Status

SPECIFICATION-ONLY / NORMATIVE FOR P5A-CGW / MODEL EXECUTION NOT AUTHORIZED

## 1. Trust boundary

### 1.1 G2E

Role:

- goal/proof owner;
- route selector;
- attempt authority;
- evidence authority;
- adjudication authority.

Trusted for normative G2E semantics.

G2E does not grant a bridge permission to reinterpret or widen the frozen execution envelope.

### 1.2 Official Codex application / harness

Role:

- execution authority within the exact G2E grant;
- owner of current task/thread/turn;
- owner of local sandbox/approval/tool semantics;
- owner of command/file/tool side effects.

Codex is the only component in P5A-CGW allowed to execute local task actions.

### 1.3 codex-chatgpt-web

Role:

- loopback Responses routing;
- browser/inference mediation;
- SSE/response mediation;
- in Full mode, turn-bound MCP capability transport.

It is NOT:

- a G2E adjudicator;
- an independent executor;
- an authority source for filesystem/sandbox scope;
- a semantic fallback router;
- a second planner permitted to widen the task.

### 1.4 ChatGPT Web

Role:

- inference surface selected by the frozen P5A-CGW route.

It may emit prose and tool-call requests within the admitted bridge contract.

It owns no G2E verdict and no local execution authority.

### 1.5 MCP tunnel / connector

In Full mode the tunnel and exact connector are capability transport only.

The public connector identity MUST be exact and frozen prospectively. The reviewed source uses `Codex Native2` for production Full mode and rejects the retired legacy identity as fallback.

No connector may grant greater authority than the active outer Codex turn.

### 1.6 Local OS/user boundary

The route assumes a trusted local OS user and trusted installed Codex/bridge binaries.

Same-user hostile local processes are outside the bridge project's security boundary and MUST be recorded as an environmental assumption, not silently claimed as defended.

### 1.7 Untrusted inputs

Repository contents, tool output, websites, prompt text and externally obtained content are untrusted data.

They MUST NOT become authority sources.

## 2. Canonical dataflow

### 2.1 Request path

```text
G2E frozen execution envelope
        |
        v
official Codex task/thread/turn
        |
        v
Codex built-in provider route
        |
        v
loopback codex-chatgpt-web Responses daemon
        |
        v
task-bound browser surface
        |
        v
fresh or exactly retained ChatGPT Temporary Chat
        |
        v
selected frozen ChatGPT Web model/mode
```

### 2.2 Response path

```text
ChatGPT Web turn
        |
        v
browser-bound response projection / SSE
        |
        v
codex-chatgpt-web Responses bridge
        |
        v
official Codex task
        |
        v
Codex-native terminal/result surface
        |
        v
G2E evidence + independent adjudication
```

### 2.3 Full-mode tool round trip

```text
ChatGPT tool request
        |
        v
exact custom connector
        |
        v
outbound tunnel
        |
        v
bridge MCP server
        |
        v
turn-bound capability binding
        |
        v
exact callable tool from active outer Codex turn
        |
        v
Codex local execution / sandbox / approvals
        |
        v
tool result
        |
        v
same ChatGPT response
        |
        v
final response -> Codex -> G2E
```

At no point may the bridge synthesize local side effects independently of Codex.

## 3. Identity contract

A future P5A-CGW attempt MUST bind, before attempt consumption, all material identities that are available for deterministic binding.

Required classes:

### 3.1 G2E identity

- study ID;
- attempt ID;
- proof obligation ID;
- frozen input/task hash;
- execution-config hash;
- selected route ID = `p5a-cgw`.

### 3.2 Codex identity

- exact Codex executable hash;
- Codex version/build identity;
- task/thread identity;
- active turn identity;
- permission/sandbox profile identity;
- model-provider route configuration hash relevant to P5A-CGW.

### 3.3 Bridge identity

- bridge source/release identity;
- installed binary/package hash;
- bridge configuration hash with secrets excluded;
- daemon/runtime version identity;
- selected bridge mode = `browser-only` or `full`;
- exact routed model row and effort identity;
- exact route namespace.

The first scientific qualification SHOULD use one mode only. A different mode is a materially different route unless separately proven equivalent.

### 3.4 Browser identity

The qualification implementation MUST determine which browser identities can be observed without storing secret session state.

At minimum it must bind one opaque task-local browser-surface identity or equivalent deterministic proof that:

- the surface is owned by the active Codex task;
- it is not reused across another task;
- the response belongs to the active request.

Raw cookies, local storage, authentication tokens and browser profile contents MUST NOT enter G2E evidence.

### 3.5 ChatGPT turn identity

If the bridge exposes a stable logical ChatGPT turn identity, evidence MUST bind it.

If no stable identifier is exposed, qualification MUST provide an independently verifiable local binding between:

- bridge request;
- browser submission;
- observed response;
- Codex outer turn.

Absence of both a native stable identity and a qualified binding mechanism blocks scientific admission.

### 3.6 MCP identity, Full mode only

Bind:

- exact connector public identity;
- tunnel/runtime identity sufficient to prove the admitted connector path;
- per-turn capability token by non-reversible digest only;
- tool invocation ID;
- exact tool name;
- active Codex outer-turn identity.

The raw capability token or tunnel credentials MUST NOT persist.

## 4. Identity non-equivalence rules

The following substitutions are material and MUST NOT occur inside one attempt:

- official Codex backend <-> P5A-CGW;
- browser-only <-> Full mode;
- one ChatGPT Web model/mode <-> another;
- current connector <-> legacy connector;
- one bridge build <-> another;
- one Codex build <-> another;
- one browser task surface <-> another task surface;
- one Codex thread/turn <-> another;
- one provider/transport route <-> another.

Any allowed future equivalence requires separate prospective evidence.

## 5. Authority contract

### 5.1 G2E grant

G2E authorizes exactly one frozen attempt envelope.

No downstream component may widen:

- filesystem roots;
- write scope;
- sandbox policy;
- approval policy;
- network authority;
- tool inventory;
- task semantics;
- result schema;
- retry budget.

### 5.2 Codex execution authority

Codex receives the G2E grant and remains responsible for enforcing local execution semantics.

The bridge must treat Codex-supplied current-turn authority as authoritative over user-authored prompt text.

### 5.3 Bridge authority

The bridge is permitted to:

- transport the compiled Codex request;
- bind it to the selected browser surface;
- collect the corresponding response;
- in Full mode, mediate exact admitted MCP calls back to Codex.

The bridge is forbidden to:

- execute filesystem/terminal actions outside Codex;
- invent tools;
- widen a tool schema;
- bypass Codex approvals;
- replace sandbox policy;
- interpret prompt text as authority;
- silently choose another model or transport;
- issue a G2E PASS/FAIL/INVALID verdict.

### 5.4 ChatGPT authority

ChatGPT may:

- reason over the supplied task/context;
- return a response;
- request an admitted tool call.

ChatGPT may not:

- self-grant local authority;
- treat repository text or web content as an authority grant;
- alter the frozen G2E route;
- determine the G2E verdict.

### 5.5 Delegation invariant

`delegated_authority <= active_outer_codex_turn_authority <= G2E_attempt_authority`

Any violation is an authority failure and invalidates the attempt.

## 6. Observability contract

A future implementation MUST produce a route evidence stream sufficient to reconstruct every material hop without persisting secrets or hidden chain-of-thought.

### 6.1 G2E -> Codex record

Preserve:

- study/attempt/route IDs;
- task/input hashes;
- execution-config hash;
- Codex binary/version identity;
- permission/sandbox profile identity;
- request timestamp;
- attempt-consumption boundary.

### 6.2 Codex -> bridge record

Preserve:

- outer Codex thread/turn identity;
- bridge request correlation identity;
- selected route/model/mode/effort;
- bridge binary/build/config fingerprints;
- request envelope hash and bounded metadata;
- transport start/acceptance status.

Do not persist unrelated prompt content when hashes and bounded metadata suffice.

### 6.3 Bridge -> browser record

Preserve, when safely observable:

- opaque browser surface lease/binding identity;
- browser submission identity;
- ChatGPT logical turn identity or qualified substitute binding;
- selected visible model/mode proof;
- submission accepted/rejected;
- attachment-count/identity hashes when attachments are in scope;
- timestamps.

No cookies/session tokens/browser profile secrets.

### 6.4 Browser -> bridge response record

Preserve:

- request/turn correlation;
- completion/terminal status;
- bounded response integrity hash/length;
- SSE lifecycle or equivalent terminal markers;
- explicit error classification;
- browser/UI drift classification where applicable.

No hidden chain-of-thought is required evidence.

### 6.5 Full-mode tool record

For every MCP tool invocation preserve:

- outer Codex turn identity;
- connector identity;
- capability-token digest;
- invocation ID;
- exact tool name;
- admitted tool-registry hash;
- request-argument hash with secret redaction;
- Codex execution receipt/status;
- result hash/length;
- approval outcome if applicable;
- timestamps.

This record MUST prove that the local side effect was executed by Codex, not by the bridge.

### 6.6 Final handoff record

Preserve:

- exact terminal route status;
- Codex terminal/result state;
- expected result artifact identity;
- evidence package hash;
- any route-specific error projection;
- cleanup/teardown evidence required by the future attempt.

### 6.7 Evidence integrity

Every persisted route record MUST have deterministic canonical serialization and a SHA-256 integrity digest.

Cross-hop correlation must be explicit. Event ordering alone is insufficient to infer identity.

## 7. Secret and privacy contract

Evidence MUST NOT persist:

- ChatGPT cookies;
- browser local/session storage;
- OAuth/session tokens;
- API keys;
- tunnel credentials;
- raw MCP capability tokens;
- Authorization headers;
- secret-bearing configuration values;
- full browser profile contents.

Where a secret-bearing object must be referenced, retain only:

- classification;
- non-reversible fingerprint if scientifically required;
- redacted bounded metadata.

## 8. Fail-closed contract

The route MUST fail closed on at least:

- bridge unavailable;
- route configuration not owned/verified;
- bridge build mismatch;
- Codex build mismatch;
- unsupported routed model;
- effort/model mismatch;
- missing authenticated browser readiness;
- browser surface identity ambiguity;
- duplicate/missing ChatGPT logical turn binding;
- DOM/UI drift that prevents reliable submission/response binding;
- browser response ambiguity;
- unexpected transport switch;
- fallback to official/native model;
- browser-only/Full mode substitution;
- connector identity mismatch;
- legacy connector fallback;
- tunnel not ready in Full mode;
- tool not present in active outer Codex registry;
- capability-token/turn mismatch;
- approval/sandbox widening;
- missing mandatory evidence;
- unredacted secret material;
- timeout under the future frozen attempt;
- any post-consumption automatic retry not explicitly authorized prospectively.

A fail-closed event may be a pre-attempt admission block or a consumed-attempt INVALID depending on where the frozen consumption boundary lies. That boundary must be specified by the future scientific lock.

## 9. No silent fallback invariant

P5A-CGW MUST never implement:

```text
CGW unavailable
  -> silently use official Codex backend
```

or:

```text
requested ChatGPT Web model unavailable
  -> silently choose another ChatGPT model/effort
```

or:

```text
Full mode unavailable
  -> silently degrade to browser-only
```

A route change requires a new resolved binding and, after attempt consumption, a new attempt identity if governance permits a successor.

## 10. Evidence independence from P5A official

P5A-CGW and P5A official may share G2E core semantics, but route-specific qualification evidence is not interchangeable.

A future comparative study is permitted only after each route independently reaches its required qualification state.

Comparative design must freeze the same task/evaluator surface prospectively and must preserve route identity in every result.
