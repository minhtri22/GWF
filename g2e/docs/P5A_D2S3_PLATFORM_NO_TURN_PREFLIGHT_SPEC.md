# G2E P5A D2-S3 — Platform No-Turn Preflight Specification

## Status

SPEC-LOCKED / PRETURN-ONLY / ZERO-SCIENCE

Prerequisites:

- D2-S2 formal-closed at preturn instrument boundary;
- D2-S3 S3-I0 official release coherence PASS;
- D2-S3 local instrument staging PASS;
- local staging evidence SHA256:
  `21dedde191d144ad561af7e78903fce73990d8ffbb6d8bb701a34eb95e336c76`;
- historical VHDX cleanup evidence SHA256:
  `d5a70d7a6d2b057405fa858b0951cbb3c24712026d538bb516ba81e783d20adf`.

## 1. Identity

- study:
  `p5a-d2s3-release-coherent-instrument-successor`
- attempt:
  `p5a-d2s3-p5-fx-001-attempt-001`
- permission profile:
  `g2e_p5a_d2s3`

Scientific attempt state remains:

- authorized: false;
- consumed: false.

## 2. Frozen fixture

- `input.json` SHA256:
  `a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6`
- `TASK.md` SHA256:
  `4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e`

The preflight may copy these two files into a fresh isolated VHDX. It must not alter their bytes.

## 3. Exact staged instrument

Codex executable:

`g2e/.local/P5A-D2S3-INSTRUMENT/package/bin/codex.exe`

SHA256:

`444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b`

Setup helper:

`g2e/.local/P5A-D2S3-INSTRUMENT/package/codex-resources/codex-windows-sandbox-setup.exe`

SHA256:

`0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4`

Global Codex installation is not an admissible instrument for D2-S3.

## 4. Fresh local preflight root

`g2e/.local/P5A-D2S3-PREFLIGHT/`

The root must not exist before the authorized local run.

It may contain only preturn support state:

- isolated VHDX;
- local CODEX_HOME;
- preflight evidence;
- report;
- generated config.

It is not the D2-S3 scientific execution root.

## 5. Isolated volume contract

Create one 128 MiB expandable NTFS VHDX and assign the first free drive letter from R through Z.

Before App Server startup, the mounted root must contain exactly:

- `input.json`
- `TASK.md`

The permission profile must encode:

- `:root = "read"`;
- exact `result.json` path = `"write"`;
- network disabled.

No `result.json` may exist at the end of preflight.

## 6. Allowed RPC sequence

The no-turn preflight may execute only the following platform/control operations after App Server
initialization:

1. `initialize`
2. `initialized`
3. `windowsSandbox/readiness`
4. if and only if readiness is `updateRequired`:
   `windowsSandbox/setupStart` with:
   - `mode = "elevated"`
   - `cwd = isolated volume root`
5. wait for `windowsSandbox/setupCompleted`
6. `windowsSandbox/readiness`
7. `mcpServerStatus/list`
8. `app/installed`
9. `account/read`
10. `permissionProfile/list`
11. `thread/start`

`thread/start` is preturn control-plane state only and does not consume the scientific attempt.

## 7. Absolute dispatch firewall

The implementation MUST NOT send:

- `turn/start`;
- any model inference request;
- any task instruction payload;
- any automatic retry after a platform failure.

The evidence and top-level report must always record:

- `turn_start_request_sent=false`;
- `scientific_attempt_consumed=false`;
- `result_exists=false`.

## 8. App isolation

App Server must be started from the exact staged Codex executable with the same isolation overrides
already qualified in D2-S2:

- `mcp_servers={}`
- `features.apps=false`
- `features.plugins=false`
- `features.remote_plugin=false`
- `features.workspace_dependencies=false`

The preflight must fail closed if:

- configured MCP count is nonzero;
- installed/callable/enabled apps are nonzero;
- auth is not ready;
- permission profile is absent or disallowed;
- unexpected instruction sources are present;
- unexpected server requests occur.

## 9. VHDX cleanup

The one-click wrapper MUST obey the active ephemeral VHDX cleanup contract.

On every exit path after the VHDX may have been attached:

1. enter a `finally` path;
2. inspect the exact VHDX by image path;
3. dismount it if attached;
4. verify `Attached == false`;
5. record:
   - attached_before_cleanup;
   - cleanup_action;
   - attached_after_cleanup;
   - cleanup_error;
6. convert an otherwise-PASS preflight into BLOCKED if detach verification fails.

No `exit` is allowed inside the protected work body before cleanup.

The VHDX file and all evidence/report files remain preserved.

## 10. PASS criteria

PASS requires all of the following:

- exact staged Codex/helper hashes;
- exact frozen fixture hashes;
- source worktree clean;
- App Server initialized;
- Windows sandbox readiness becomes `ready`;
- if setup was required, setup completes successfully in elevated mode;
- MCP/apps disabled and empty;
- auth ready;
- D2-S3 permission profile present and allowed;
- thread created;
- instruction sources empty;
- no unexpected server requests;
- no `turn/start`;
- no `result.json`;
- fixture bytes unchanged;
- exact VHDX detached after preflight.

PASS verdict:

`PRETURN_PASS_SCIENTIFIC_AUTHORIZATION_REVIEW_REQUIRED`

A PASS does not itself authorize scientific execution.

## 11. Qualification boundary

Before one local preflight may run, CI must prove:

- Python preflight compiles;
- PowerShell wrapper parses on Windows PowerShell 5.1;
- exact hashes/IDs/paths are bound;
- static RPC allowlist and `turn/start` absence;
- cleanup `finally` contract;
- no global Codex instrument fallback;
- P1/P1.4/P1.5/P2/P3/P4 regressions PASS.

Qualification does not execute a model turn and does not consume the D2-S3 attempt.
