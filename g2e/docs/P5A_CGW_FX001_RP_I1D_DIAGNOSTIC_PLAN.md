# P5A-CGW FX001 RP-I1D — Diagnostic-Complete Instance Ownership Probe

Status: ZERO-SCIENCE DIAGNOSTIC ONLY

## Trigger

RP-I1 execution 002 was harness-valid but blocked because:

- `~/.codex-chatgpt-web/config.json` exists;
- launcher log exists;
- `~/.codex-chatgpt-web/runtime/launcher-supervisor.json` is absent;
- `~/.codex-chatgpt-web/runtime/launcher-browser.json` is absent.

Exact CGW 4.0.7 source confirms those are the production CORE_HOME ownership/descriptor paths.

## Purpose

Determine which live-state class exists **without changing the RP-I1 pass criteria**:

1. launcher/browser host not active;
2. a compatible listener exists but is externally/stale-owned;
3. listener/health exists with a PID that can be bound to a local process but not to launcher ownership state;
4. no listener exists;
5. unexpected profile/home evidence exists.

## Safety

The diagnostic:

- performs GET only to `/healthz`;
- performs no `POST /v1/responses`;
- performs no model execution;
- performs no browser submission;
- performs no MCP invocation;
- creates no scientific attempt;
- does not mutate TC-001/002/003 evidence;
- reads bounded process metadata and hashes command lines rather than emitting raw command lines.

## Governance

RP-I1D cannot PASS RP-I1 or RP-I2 by itself. Its output is diagnostic evidence only.
