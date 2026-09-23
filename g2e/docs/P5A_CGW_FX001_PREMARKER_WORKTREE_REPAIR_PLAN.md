# P5A-CGW FX001 — Pre-Marker Worktree Gate Repair

## Trigger

The first authorized local invocation reached only the UAC handoff and exited before a final report existed.

The caller's repository contained only unrelated untracked output directories:

- `.local/`
- `dist/`
- `evidence/dg-p9/`

The frozen v2 one-click wrapper used a blanket `git status --porcelain` clean-tree requirement. The elevated child therefore had a deterministic pre-marker blocking path before `LocalRoot`, predispatch admission, runner startup, durable marker creation, and `turn/start`.

Regardless of whether UAC itself was cancelled or the elevated child reached the blanket dirty-tree check, the observed invocation could not cross the frozen attempt-consumption boundary. The reserved attempt remains unconsumed.

## Repair scope

This is a bounded infrastructure repair only.

Unchanged:

- study and attempt identity;
- CGW v4.0.7;
- Codex binary;
- route/model/mode/connector;
- P5-FX-001 input/task/result;
- Codex execution authority;
- marker-before-send boundary;
- retry budget 0;
- timeout 90 seconds;
- route/browser/MCP evidence requirements.

Changed:

The wrapper source-clean gate now requires:

1. no tracked worktree diff;
2. no staged/index diff;
3. no untracked file under execution-critical prefixes:
   - `scripts/g2e/`
   - `g2e/docs/`
   - `g2e/config/`
   - `src/`
   - `tests/g2e/`
   - `.github/workflows/`

Untracked runtime/output directories outside those prefixes do not block dispatch.

The existing local-root nonexistence gate remains unchanged and still prevents accidental repeat execution.

## Qualification rule

The repaired one-click blob and regression tests must pass the existing Linux/Windows zero-model implementation workflow.

Only then may the unconsumed reserved attempt be re-authorized under a successor lock that binds the repaired one-click blob. The old V2 lock remains immutable and must not be used with the new wrapper blob.

No model/browser/MCP execution is permitted during repair qualification.
