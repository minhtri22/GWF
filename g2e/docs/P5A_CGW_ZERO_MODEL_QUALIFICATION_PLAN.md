# G2E P5A-CGW — Zero-Model / Synthetic Qualification Plan

## Status

PLAN-ONLY / IMPLEMENTATION NOT AUTHORIZED BY THIS FILE / MODEL EXECUTION FORBIDDEN

## 1. Purpose

Before any P5A-CGW scientific attempt, qualify that the alternative route can preserve identity, authority, provenance, failure semantics and evidence without using an authenticated model turn.

PASS of this future macro-gate will mean only:

`P5A_CGW_ROUTE_INFRASTRUCTURE_QUALIFIED_FOR_ATTEMPT_DESIGN`

It will NOT mean:

- ChatGPT Web functional success;
- Codex functional success;
- P5-FX-001 success;
- P5A official success;
- authorization to run a model-bearing attempt without a later exact execution lock.

## 2. Frozen reference inputs for implementation

The implementation phase must start from an explicit lock containing:

- exact GWF source HEAD;
- reviewed `miuuyy/codex-chatgpt-web` source commit;
- exact bridge release/build chosen for local qualification;
- exact bridge binary/package SHA-256;
- exact Codex binary SHA-256;
- exact relevant configuration fingerprints;
- exact test fixtures;
- exact connector schema identity if Full mode is the target.

If the installed bridge cannot be mapped to the approved source/release identity, qualification fails closed.

## 3. Firewalls

Zero-model qualification MUST NOT:

- dispatch a scientific Codex `turn/start`;
- open P5-FX-001;
- send an authenticated ChatGPT model message;
- consume a ChatGPT Web message allowance;
- execute a real MCP tool through ChatGPT;
- create a scientific attempt-consumption marker;
- mutate P5A official route state;
- claim functional executor success.

Static source retrieval and deterministic synthetic fixtures are allowed.

Any browser/runtime check included in qualification must prove that it cannot submit a model message.

## 4. Macro-gate

### Q0 — Source and build provenance

Prove:

- exact reviewed upstream source identity;
- exact installed bridge build identity;
- exact Codex build identity;
- no unbound executable enters the route.

PASS requires deterministic fingerprints.

### Q1 — Route ownership and no-fallback static qualification

Verify against exact bridge source/configuration behavior that:

- routed models use the bridge-owned namespace;
- official/native passthrough is distinguishable;
- unsupported routed model fails explicitly;
- transport capability negotiation cannot silently change the selected model;
- bridge mode is explicit;
- legacy connector identity is not accepted as an implicit substitute.

This is evidence about exact source/build behavior, not a trust-by-documentation shortcut.

### Q2 — Synthetic request/response correlation

With no model:

- inject a synthetic Codex-like Responses request into the route adapter or an isolated harness around the same handler;
- assign deterministic outer thread/turn/request identities;
- simulate browser submission acceptance;
- simulate terminal response/SSE;
- prove one-to-one correlation through the complete evidence projection.

Negative cases:

- missing request ID;
- duplicate request ID;
- mismatched outer turn;
- stale browser lease;
- duplicate terminal response;
- response from another task.

All must fail closed.

### Q3 — Browser-binding observability

Using fixtures/mocks only, prove the evidence layer can distinguish:

- correct task-bound browser surface;
- wrong surface;
- stale retained surface;
- missing logical turn identity;
- duplicate logical turn identity;
- UI/DOM drift fixture.

If the production bridge does not expose enough identity for independent verification, bounded observability instrumentation must be designed and qualified before science.

### Q4 — Authority preservation

Synthetic outer Codex authority must define:

- cwd/root set;
- sandbox/approval semantics;
- tool registry;
- allowed write surface.

Then prove the bridge cannot:

- add a tool;
- rename an unlisted tool into an allowed tool;
- widen arguments beyond the admitted schema/contract;
- manufacture filesystem/terminal execution;
- use prompt text as authority;
- elevate approval/sandbox policy.

### Q5 — Full-mode MCP capability binding

Required only if first P5A-CGW scientific route is Full mode.

With a synthetic MCP server/tool registry:

- bind one opaque turn capability;
- persist only its digest;
- prove exact active outer-turn binding;
- prove exact connector identity;
- prove exact-name tool dispatch;
- prove a token from another turn fails;
- prove an unknown tool fails;
- prove legacy connector identity fails;
- prove recursive/unbounded raw gateway behavior cannot bypass the admitted contract;
- prove tool-result evidence returns to the same synthetic turn.

No real ChatGPT connector call is permitted.

### Q6 — Observability and privacy

Synthetic evidence must prove deterministic preservation of:

- route identity;
- Codex outer thread/turn;
- bridge request correlation;
- bridge build/config fingerprints;
- browser binding;
- model/mode/effort;
- terminal/error classification;
- tool round trip when applicable;
- result/evidence hashes.

Negative privacy fixtures must cover:

- Authorization/Bearer values;
- API keys;
- cookies;
- browser storage values;
- tunnel credentials;
- MCP turn tokens;
- user-home paths when policy requires redaction.

Persisted evidence must contain no recoverable secret.

### Q7 — Failure injection matrix

Inject at least:

1. bridge daemon unavailable;
2. bridge health/version mismatch;
3. routed model unavailable;
4. browser not authenticated/ready;
5. browser task lease mismatch;
6. submission not acknowledged;
7. response identity ambiguous;
8. SSE interrupted before terminal evidence;
9. explicit browser/UI drift;
10. connector mismatch;
11. tunnel unavailable;
12. active tool registry mismatch;
13. tool capability turn mismatch;
14. approval denial;
15. missing evidence field;
16. secret-redaction failure;
17. attempted native/official fallback;
18. attempted browser-only/Full-mode substitution.

Each expected outcome must be preregistered as either:

- PRE-ATTEMPT BLOCK, or
- future-attempt INVALID,

depending on the later frozen consumption boundary.

Qualification itself has no scientific attempt consumption.

### Q8 — G2E regression

The bounded implementation must pass all relevant existing G2E regressions, including at minimum:

- core schema/semantics;
- P1/P1.4/P1.5 authority/binding where applicable;
- P2/P3/P4 evidence/adjudication invariants;
- Windows-specific parser/runtime tests for any PowerShell entrypoint;
- secret-redaction regressions;
- deterministic evidence serialization.

No existing P5A official executable/hash may be silently replaced.

## 5. Mode selection rule

The first functional P5A-CGW attempt MUST freeze exactly one route mode.

If Full mode is selected, Q5 is mandatory.

If browser-only is selected, no Full-mode MCP capability may be present and the functional task must not require local tool capability beyond what that mode legitimately provides.

Mode choice must be made prospectively from the target proof obligation, not after observing outcome.

## 6. PASS gate

PASS requires every applicable Q0-Q8 gate to pass with:

- zero authenticated model turns;
- zero scientific attempt markers;
- complete machine-readable evidence;
- exact source/build fingerprints;
- no secret leakage;
- no unresolved authority or identity ambiguity.

The resulting qualification must emit:

- qualification result document;
- evidence JSON;
- exact component blob hashes;
- exact source/build identities;
- route capability manifest;
- explicit list of known-unproven live behaviors.

## 7. Known limitation after zero-model PASS

Synthetic qualification cannot prove the live ChatGPT Web model will successfully complete a G2E task.

Therefore PASS only authorizes the next governance step:

```text
ZERO-MODEL QUALIFICATION PASS
        |
        v
preregister one functional P5A-CGW study
        |
        v
freeze exact task + route + identities + consumption boundary
        |
        v
implementation/execution lock
        |
        v
exactly one authorized model-bearing attempt
```

## 8. First functional attempt constraints

The first attempt must:

- use a new P5A-CGW study and attempt identity;
- never reuse a consumed P5A official attempt identity;
- freeze bridge/Codex/model/mode identities;
- use route-specific evidence;
- have retry budget defined prospectively;
- preserve fail-closed semantics;
- adjudicate infrastructure/transport failures separately from substantive task FAIL;
- never back-credit its outcome to P5A official.

No first attempt identity is assigned during this specification-only phase.
