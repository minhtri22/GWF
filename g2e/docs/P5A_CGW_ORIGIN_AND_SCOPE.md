# G2E P5A-CGW — Origin and Scope

## Status

SPECIFICATION-ONLY / BOUNDED / NO MODEL EXECUTION / NO FUNCTIONAL CLAIM

Workstream identity:

`p5a-cgw-codex-chatgpt-web-bridge-qualification`

This workstream defines an alternative G2E executor route in which the official Codex application remains the execution authority while `codex-chatgpt-web` mediates inference transport between Codex and ChatGPT Web.

No scientific attempt is authorized by this document.

## 1. Origin

The canonical P5A route remains the official Codex route:

```text
G2E
  -> P5A official Codex adapter
  -> official Codex app-server / harness
  -> official Codex backend
```

P5A-CGW is a separate route:

```text
G2E
  -> official Codex task / harness
  -> codex-chatgpt-web loopback Responses bridge
  -> ChatGPT Web inference surface
  -> optional turn-bound MCP capability round-trip
  -> official Codex task / harness
  -> G2E evidence / adjudication
```

P5A-CGW is NOT:

- a repair of D2-S5;
- a retry of any consumed P5A official attempt;
- a replacement for the official Codex route;
- a silent fallback when Codex quota or another official-route prerequisite is unavailable;
- evidence that the official P5A route has passed functional qualification.

The official route remains canonical and independent. Its next admissible infrastructure work is the separately governed quota-admission workstream. This P5A-CGW branch does not modify or authorize that work.

## 2. Why a separate lineage is required

P5A-CGW changes material execution-path identities:

- transport path;
- model/inference surface;
- browser state;
- bridge build;
- connector/tunnel path in Full mode;
- route-specific failure modes;
- route-specific observability.

Under PRD-09, provider/model/app/harness/transport identities must remain separate and capability parity must not be inferred across applications or transports.

Therefore P5A-CGW requires its own:

- capability manifest;
- admission evidence;
- route identity;
- attempt identity;
- observability evidence;
- qualification result;
- scientific lineage.

Evidence from P5A-CGW MUST NOT promote P5A official capabilities, and official P5A evidence MUST NOT silently promote P5A-CGW.

## 3. Exact specification bases

GWF specification base:

- repository: `minhtri22/GWF`
- branch base: `feature/g2e-framework`
- exact base commit: `065960bbe764337da7bca60b9dd0c451e62fa2e4`

Reviewed bridge source basis:

- repository: `miuuyy/codex-chatgpt-web`
- branch: `main`
- reviewed commit: `eaf4f09ae92d4dc4429fa597b0861663138f08f8`
- package metadata at that source revision: `5.0.8`

The source basis is a specification reference, not runtime admission. Future qualification MUST fingerprint the actual installed bridge build/binary and MUST fail closed if it cannot be bound to an approved source/release identity.

Canonical P5A official Codex protocol reference remains separately frozen by the official route. P5A-CGW MUST independently fingerprint the Codex executable/harness actually used by its route before any future attempt.

## 4. Upstream architecture assumptions being converted into G2E requirements

The reviewed bridge documentation states that:

- Codex remains responsible for its sandbox, approvals, UI, command sessions and tool results;
- the bridge transports decisions and does not add a second planner, semantic router or fallback model;
- Full mode can request only callable tools advertised by the active outer Codex turn;
- unsupported routes, models, connector identities or browser states fail explicitly rather than silently switching transport/model;
- the Responses surface is loopback-bound;
- the Full-mode MCP tunnel is outbound;
- browser automation is unofficial and UI drift is a material failure mode.

For G2E these are not accepted merely as project claims. They become prospective invariants that P5A-CGW must independently qualify before model-bearing science.

## 5. Governing authority statement

The authority hierarchy is frozen as:

```text
G2E governance / attempt authorization
          |
          v
official Codex execution authority
          |
          +-- bounded local task/harness/tools/approvals
          |
          v
codex-chatgpt-web
transport + inference mediation only
          |
          v
ChatGPT Web
inference surface only
```

The bridge MUST NOT become a hidden second executor.

ChatGPT Web MAY propose actions only through the capabilities exposed by the exact active Codex turn. The bridge MAY transport those requests. Codex remains the component that owns local tool execution, sandbox and approval semantics.

G2E remains the authority for:

- attempt authorization;
- frozen goal/proof envelope;
- evidence admission;
- adjudication;
- capability promotion;
- successor governance.

## 6. Scope of this workstream

In scope now:

- trust-boundary specification;
- route/dataflow specification;
- identity contract;
- authority contract;
- observability contract;
- fail-closed contract;
- zero-model/synthetic qualification plan;
- specification lock.

Out of scope now:

- installing or modifying codex-chatgpt-web;
- changing Codex routing;
- authenticated ChatGPT browser interaction;
- MCP tunnel connection;
- model inference;
- scientific task execution;
- P5-FX-001 execution;
- functional PASS/FAIL;
- comparative A/B testing;
- P5A official quota-admission implementation.

## 7. Exit condition

This specification phase closes only when the documents and lock are internally coherent.

The next phase, if authorized, is bounded implementation of P5A-CGW admission/observability plus zero-model/synthetic qualification.

Only a PASS of that future macro-gate may authorize preregistration and exact locking of the first P5A-CGW model-bearing functional attempt.
