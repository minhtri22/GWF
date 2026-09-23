# G2E P5A-CGW — Implementation / Synthetic Zero-Model Qualification

## Status

IMPLEMENTED / SYNTHETIC QUALIFICATION PENDING CI / LOCAL RUNTIME ADMISSION REQUIRED

This document is intentionally pre-adjudication. It does not claim PASS until the exact candidate workflow completes.

## Implemented components

- `scripts/g2e/p5a_cgw_bridge_qualification.py`
  - exact reviewed upstream source/blob contract;
  - CGW config projection with secret exclusion;
  - CGW `/healthz` admission;
  - Codex `openai_base_url` route ownership validation;
  - request/browser/terminal identity correlation;
  - Full-mode MCP authority binding;
  - recursive secret redaction;
  - frozen 18-case failure matrix;
  - synthetic and local zero-model reports.

- `scripts/g2e/p5a_cgw_local_zero_model_oneclick.ps1`
  - Windows local read-only bridge admission;
  - GET `/healthz` only;
  - no `/v1/models`;
  - no `/v1/responses`;
  - no Codex `thread/start` or `turn/start`;
  - no ChatGPT browser submission;
  - no MCP invocation;
  - exact local binary hashes captured without persisting secrets.

- `tests/g2e/test_p5a_cgw_zero_model_qualification.py`
  - synthetic Q1-Q7 plus zero-model firewall tests.

- `.github/workflows/g2e-p5a-cgw-zero-model-qualification.yml`
  - exact upstream static-source Q0a;
  - Linux and Windows qualification;
  - P1/P1.4/P1.5/P2/P3/P4 regressions;
  - no model execution.

## Q0 split

Q0 is deliberately split:

- Q0a — exact upstream source provenance: CI-verifiable.
- Q0b — exact installed local bridge/Codex runtime identity: requires the user's already-installed Windows runtime and therefore cannot be fabricated in GitHub Actions.

The synthetic macro-gate may therefore reach:

`SYNTHETIC_ZERO_MODEL_PASS_LOCAL_RUNTIME_ADMISSION_REQUIRED`

It may not reach final route qualification until Q0b/local route admission is supplied.

## G2E-to-CGW integration boundary

This phase deliberately connects G2E at the control/evidence plane rather than by injecting another browser controller:

```text
G2E route admission
  -> read exact CGW route/config identity
  -> verify Codex openai_base_url ownership
  -> verify CGW loopback health/version/mode/idle state
  -> bind exact binary/config hashes
  -> establish route identity + fail-closed evidence contract
```

CGW remains the browser/inference mediator. Codex remains the execution authority. The future model-bearing phase must add live cross-hop evidence for one frozen attempt; it must not create a second browser automation layer in G2E.

## Current authorization

- model turn: NOT AUTHORIZED
- scientific attempt: NOT AUTHORIZED
- A/B comparison: NOT AUTHORIZED
- local zero-model admission probe: eligible only after CI PASS is formally locked
