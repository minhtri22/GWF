# P5A-CGW FX001 — V2R6 pre-consumption infrastructure amendment

## Trigger

The first V2R5 live attempt reached the Windows sandbox control plane but failed before the durable attempt marker because the local Codex installation was mixed-build:

- local `codex.exe` emitted `interactive-provision`;
- selected helper was the official `rust-v0.153.4` helper and rejected that mode;
- marker was absent and `turn/start` was never sent.

The scientific attempt therefore remains unconsumed.

## Local coherent package

A project-local official `rust-v0.153.4` package was independently qualified and then locally reproduced with:

- archive SHA-256: `a6ef3442cb12766a88b39311d79244289e4f9763e2c53ff4fbebc2cb653cc5f3`;
- `codex.exe` SHA-256: `444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b`;
- sandbox helper SHA-256: `0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4`;
- version: `codex-cli 0.153.4`;
- zero model/browser/MCP/sandbox execution during qualification.

## Amendment scope

V2R6 changes only pre-consumption infrastructure identity and evidence location:

1. replace the rejected mixed-build Codex binary with the qualified project-local official 0.153.4 binary;
2. bind the matching official sandbox helper;
3. preserve `P5A-CGW-FX001-V4-001` as immutable prior failure evidence;
4. use fresh execution root `P5A-CGW-FX001-V4-002`;
5. move handoff/diagnostic files to the V4-002 namespace;
6. use `P5A_CGW_FX001_EXECUTION_CONFIG_V2.json`.

Unchanged:

- study id and attempt id;
- CGW 4.0.7 route and bridge config;
- model and effort;
- P5-FX-001 task/input/result contract;
- Codex sole local execution authority;
- workspace authority;
- durable marker boundary;
- retry budget = 0;
- single turn/start;
- 90 second timeout;
- mandatory live MCP/browser route evidence;
- PASS / FAIL / INVALID criteria.

## Fail-closed preflight additions

Before UAC, the wrapper must prove:

- predecessor V4-001 marker is absent;
- local qualification report exists and is PASS;
- report archive/Codex/helper hashes match frozen values;
- report firewall records no model/browser/MCP/sandbox/attempt consumption;
- project-local Codex path equals the path recorded in the report;
- actual Codex and helper file hashes match;
- V4-002 does not already exist.

## Execution config V2

The original execution config remains immutable predecessor evidence.

V2 canonicalization is recursive key-sort JSON with no whitespace. Frozen canonical SHA-256:

`4af6909cecd412e8daf9c641222e129f1e35b7f94b00179339991a6f3ddb72ea`

Git blob:

`5551262c62389eaecf928e8d60fbde22e39d3b1e`

## Qualification

No live dispatch is authorized by this implementation candidate.

Linux and Windows zero-model QA must pass for admission, runner, verifier, wrapper, V2 config binding, old-root preservation, project-local package binding, PowerShell parsing, and all preregistration regressions.

Only after PASS may V2R6 be formalized as a dispatch lock for the same still-unconsumed attempt.
