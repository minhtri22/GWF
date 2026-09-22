# G2E P5A D2-S2 — Isolated-Volume Root-Read Successor Preimplementation

**Status:** FROZEN CANDIDATE FOR ZERO-FRESH QA  
**Predecessor:** D2-S1 closed preturn on root-read authority incompatibility  
**Scientific model turn:** PROHIBITED  
**Scientific attempt identity:** NEW / UNUSED  
**Purpose:** test whether Windows elevated sandbox can enforce the same effective task-data authority when `:root = read` is confined to a dedicated isolated volume.

## 1. Study identity

```text
study_id
p5a-d2s2-isolated-volume-root-read-successor

attempt_id
p5a-d2s2-p5-fx-001-attempt-001

profile_id
g2e_p5a_d2s2
```

This is not a retry or replacement of D2-S1.

## 2. Frozen scientific fixture

The P5-FX-001 content remains byte-identical:

```text
input.json SHA256
a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6

TASK.md SHA256
4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e
```

No task, verifier, expected-result, model/provider or capability-target semantics may change.

## 3. Isolated-volume contract

The successor uses a dedicated dynamically created VHDX-backed NTFS volume under:

```text
D:\WORK\RESEARCH\4.GWF\g2e\.local\P5A-D2S2\volume\
```

The volume size is fixed at 128 MiB, dynamically allocated.

A deterministic drive-letter allocator checks this ordered candidate set and selects the first unused letter:

```text
R, S, T, U, V, W, X, Y, Z
```

The mounted volume root is the task workspace.

Before Codex App Server starts, the root MUST contain exactly:

```text
TASK.md
input.json
```

and those files MUST match the frozen hashes above.

The host Git repository, user profile, auth material and ordinary project files MUST remain outside this volume.

## 4. Permission profile

The Windows elevated backend requires effective root-read authority.

D2-S2 therefore uses:

```toml
default_permissions = "g2e_p5a_d2s2"

[windows]
sandbox = "elevated"

[permissions.g2e_p5a_d2s2.filesystem]
":root" = "read"
"<isolated-volume-root>\\result.json" = "write"

[permissions.g2e_p5a_d2s2.network]
enabled = false
```

The security interpretation is:

```text
:root read
=
read of isolated VHDX task volume only
!=
read of host D:\ or C:\
```

The successor is inadmissible if the runtime resolves `:root` outside the mounted isolated volume.

## 5. CODEX_HOME

A fresh isolated CODEX_HOME remains under:

```text
g2e/.local/P5A-D2S2/codex-home/preturn-001
```

It is outside the task VHDX.

Pre-start CODEX_HOME contains exactly:

```text
auth.json
config.toml
```

Runtime-generated sandbox control state is local-only and MUST NOT be committed or exposed to the model as task data.

## 6. No-turn preflight

Allowed RPC sequence:

```text
initialize(experimentalApi=true)
windowsSandbox/readiness
if updateRequired:
  windowsSandbox/setupStart(mode=elevated, cwd=<isolated-volume-root>)
  wait setupCompleted
windowsSandbox/readiness -> ready
mcpServerStatus/list -> 0
app/installed -> 0
account/read -> auth ready
permissionProfile/list -> g2e_p5a_d2s2 present+allowed
thread/start(cwd=<isolated-volume-root>, permissions=g2e_p5a_d2s2)
STOP
```

The preflight implementation MUST NOT contain `turn/start`.

## 7. Fail-closed one-click wrapper

The local execution MUST be performed through a repository-owned PowerShell wrapper:

```text
scripts/g2e/p5a_d2s2_isolated_volume_oneclick.ps1
```

The wrapper MUST:

1. require the project root to be the GWF checkout;
2. fetch and detach to its exact qualified Git SHA;
3. require a clean tracked worktree;
4. verify the Python preflight blob and frozen fixture hashes;
5. require an elevated PowerShell process before VHDX creation;
6. create the D2-S2 local root only under `g2e/.local/`;
7. create/mount the 128 MiB VHDX with deterministic drive-letter choice;
8. copy and hash-verify the frozen fixture;
9. create the permission profile and fresh CODEX_HOME;
10. run the no-turn Python preflight;
11. write both JSON and Markdown user-return reports;
12. exit non-zero on every gate failure;
13. never invoke a scientific turn.

## 8. Report contract

The one-click script must produce:

```text
g2e/.local/P5A-D2S2/report/
P5A_D2S2_ONECLICK_REPORT.json
P5A_D2S2_ONECLICK_REPORT.md
```

The report includes safe metadata only:

- exact source HEAD;
- script/preflight hashes;
- VHDX path;
- selected drive letter;
- volume root;
- fixture hashes;
- config hash;
- readiness/setup outcome;
- redacted setup error if any;
- profile/thread preflight outcome;
- `turn_start_request_sent=false`;
- `scientific_attempt_consumed=false`.

It MUST NOT contain auth contents, tokens, passwords or sandbox-user secrets.

## 9. Scientific firewall

The following remain prohibited until a later explicit final admission:

- model turn;
- `turn/start`;
- scientific result generation;
- retry of D2-S1;
- broad host-drive read;
- network access;
- repository read/write scientific claim;
- runtime adapter authorization.

## 10. Successor preturn verdicts

```text
PRETURN_PASS
  isolated volume + elevated setup + profile + thread all qualify

PRETURN_BLOCKED_PLATFORM
  VHDX/elevation/sandbox setup cannot qualify

PRETURN_BLOCKED_AUTHORITY
  effective root cannot be proven confined to isolated volume

PRETURN_INVALID
  hash/source/workspace/report integrity failure
```

No verdict above is a scientific PASS/FAIL.
