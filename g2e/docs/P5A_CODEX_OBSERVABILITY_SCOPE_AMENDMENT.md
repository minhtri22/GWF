# G2E P5A — D2 Stop-Scope Amendment

## Status

**P5A Codex adapter:** OPEN  
**D2-S4 attempt:** FORMALLY CLOSED / INVALID / CONSUMED / NO RETRY  
**D2-S5 model execution:** NOT YET AUTHORIZED  
**New admissible workstream:** P5A-CODEX-OQ1 — Observability Qualification

## Purpose

This amendment narrows the scope of `P5A_D2_TERMINAL_STOP_DECISION.md`.

That decision remains authoritative for:

- the consumed D2-S4 attempt;
- prohibition on D2-S4 retry/rescue;
- prohibition on launching a new model-bearing successor without a prospectively qualified mechanism change.

It does **not** close the P5A Codex adapter program or the G2E framework.

The D2-S4 post-closure result identified an instrumentation gap: the sanitizer preserved method/hash/timing
but did not preserve the mechanism-bearing `TurnError` fields required to adjudicate a terminal
`failed` turn.

A new zero-model workstream may therefore qualify observability independently of D2-S4 outcome.

## Scope correction

The following statement is superseded in scope:

`STOP_MODEL_EXECUTION / NO_D2S5_AUTHORIZATION`

It is interpreted prospectively as:

`NO_MODEL_BEARING_SUCCESSOR_UNTIL_OBSERVABILITY_QUALIFICATION_PASS`.

D2-S4 remains immutable and cannot be rerun.

## 5W1H confirmation

- **What:** qualify a privacy-safe Codex terminal-error evidence channel.
- **Why:** D2-S4 reached a genuine terminal `failed` state, but the sanitizer discarded the exact error
  payload needed for mechanism attribution.
- **Who/authority:** G2E P5A qualification governance; no agent output is authoritative until zero-model
  QA passes.
- **When:** before designing or authorizing any successor functional attempt.
- **Where:** reusable Codex adapter observability component, not the frozen D2-S4 runner.
- **How:** preserve a bounded `TurnError` projection, redact secrets/private path material, test synthetic
  failed turns, verify exact `rust-v0.153.4` protocol schemas, and run zero-model regressions.

## Successor boundary

A PASS of P5A-CODEX-OQ1 permits **design/preregistration** of a new functional successor attempt.

It does not itself authorize a model turn.
