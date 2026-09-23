# P5A-CGW FX001 — Fail-Visible Pre-UAC Diagnostic Repair

## Trigger

A second local V2R1 invocation returned exit code 1 with:

- attempt marker absent;
- no final report;
- only the parent message indicating administrator elevation was required.

Therefore the invocation remained pre-marker and the reserved attempt stayed unconsumed.

The wrapper still placed most local/environment preflight checks inside the elevated child. A child-side failure could therefore disappear with the elevated window and leave only exit code 1 in the caller terminal.

## Repair

This successor repair changes only pre-marker infrastructure behavior.

Before any UAC request, the wrapper now verifies in the current terminal:

- exact V2R2 lock and bound component blobs;
- tracked worktree/index cleanliness;
- critical-untracked-source guard;
- exact Python/Codex/CGW paths and binary fingerprints;
- exact CGW config/loopback route identity;
- launcher log presence;
- exact P5-FX-001 source fixture hashes;
- Codex auth-file presence;
- absence of the functional LocalRoot.

The resolved CGW binary, bridge home, launcher data, Python path and Codex path are then passed explicitly to the elevated child.

A new `-PreflightOnly` mode stops after those checks and guarantees:

- no UAC;
- no VHDX;
- no functional LocalRoot;
- no durable marker;
- no Codex thread/turn;
- no browser submission;
- no MCP invocation.

## Scientific contract

Unchanged:

- attempt id;
- CGW 4.0.7;
- Codex binary;
- route/model/mode/connector;
- task/result;
- authority;
- marker-before-sole-turn/start boundary;
- retry=0;
- timeout=90s;
- evidence requirements.

The repeated exit-code-1 invocations are not retries because neither crossed the durable marker boundary.

## Qualification

Linux and Windows zero-model QA must prove:

- V2R2 guard is present;
- preflight-only branch occurs before UAC and LocalRoot creation;
- all non-admin local dependency checks occur before UAC;
- exact paths are preserved across elevation;
- existing runner/verifier scientific contract regressions remain PASS.

Only after PASS may the same still-unconsumed attempt be bound to V2R2.
