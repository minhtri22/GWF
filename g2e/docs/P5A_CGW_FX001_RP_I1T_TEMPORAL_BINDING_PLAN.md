# P5A-CGW FX001 RP-I1T — TC-003 Temporal Instance Binding

Status: ZERO-SCIENCE TEMPORAL ATTRIBUTION ONLY

## Purpose

Bind the currently proven development-profile listener mismatch to the exact historical TC-003 execution window without running any model.

Hard Git bounds:

- TC-003 live-lock qualification commit: 2026-09-25T02:59:15Z
- TC-003 post-live adjudication commit: 2026-09-25T03:40:47Z

Therefore the scientific execution necessarily occurred inside that interval.

## PASS requirements

1. Current health PID == sole listener PID.
2. Listener process creation time <= 2026-09-25T02:59:15Z.
3. Listener process is still alive now and command contains `serve`.
4. Listener executable resolves under development profile home `~/.codex-chatgpt-web-dev`.
5. Parent launcher process creation time <= 2026-09-25T02:59:15Z.
6. Parent launcher executable is the portable development launcher path already observed.
7. Development profile source-derived launcher userData/root exists.
8. Development launcher logs contain `runtime.daemon_started` bound to the same listener PID at or before the TC-003 window.
9. No source-compatible evidence indicates the listener PID exited before TC-003 completion.

If all hold, H-R1 may be promoted from current-state mechanism evidence to historical TC-003 root-cause evidence.

## Safety

GET /healthz only. No /v1/responses request, no model, no browser submission, no MCP, no scientific attempt.
