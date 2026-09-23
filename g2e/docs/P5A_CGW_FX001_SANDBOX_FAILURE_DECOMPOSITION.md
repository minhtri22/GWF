# P5A-CGW FX001 — Sandbox Setup Failure Decomposition

## Trigger

V2R5 successfully passed parent preflight, UAC handoff, VHDX construction, and predispatch admission, then the frozen runner blocked before the durable attempt marker with:

`RuntimeError:PREDISPATCH_SANDBOX_SETUP_FAILED`.

The durable marker was absent and `turn/start` was never sent, so the reserved attempt remains unconsumed.

## Current frontier

The failure is localized to the Windows sandbox control plane:

`windowsSandbox/readiness -> updateRequired -> windowsSandbox/setupStart -> windowsSandbox/setupCompleted(success=false)`

No model, browser submit, or MCP roundtrip occurred.

The route-evidence errors emitted by the runner are derivative missing-evidence conditions caused by the pre-turn block and are not independently adjudicated route failures.

## Existing evidence first

Before any repair or rerun, inspect only artifacts already created by V2R5:

1. `g2e/.local/P5A-CGW-FX001-V4-001/codex-home/.sandbox/sandbox.2026-09-23.log`
2. the existing Codex protocol projection;
3. the isolated Codex config and permission profile;
4. existing local sandbox state/ACL metadata if needed, read-only.

The setup-completed notification includes an error field in the Codex app-server protocol, but the current safe protocol projection does not persist that field. Therefore the sandbox log is the first existing-evidence target.

## Prohibited until mechanism is identified

- no rerun;
- no deletion of LocalRoot;
- no new sandbox setup attempt;
- no switch to unelevated/MXC;
- no route/model/connector/task change;
- no attempt reauthorization;
- no tuning-to-pass.

## Decision

Only after the exact sandbox failure mechanism is recovered may a bounded infrastructure repair be designed and separately zero-model qualified. The scientific attempt identity remains unchanged and unconsumed.
