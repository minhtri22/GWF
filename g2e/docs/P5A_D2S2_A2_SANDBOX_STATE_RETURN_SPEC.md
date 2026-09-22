# G2E P5A D2-S2 A2 — Sandbox State Read-Only Evidence Return

## Status

SPEC-LOCKED / ZERO-SCIENCE / READ-ONLY-LOCAL-EVIDENCE

Baseline:

- branch: `feature/g2e-framework`
- exact baseline HEAD: `ea1a8987508ed23d09b84fe2bd305eb68d68b850`
- bound setup evidence-return SHA256:
  `6f1f178aac74037ed8ab1661b5b98beef5871f0cde0456237a52afd84fb23ceb`

## 1. Purpose

Inspect the already-created A2 sandbox support state needed to distinguish:

- structured helper failure available but not surfaced;
- helper exited before writing a structured report;
- setup marker partial/incomplete state;
- setup log evidence pointing to provisioning/firewall/ACL/reporting failure.

This is not a rerun.

## 2. Fixed local scope

The collector may read only:

`g2e/.local/P5A-D2S2-A2/codex-home/preturn-a2/.sandbox/`

and may write only:

`g2e/.local/P5A-D2S2-A2/return/`

No other local path is in scope.

## 3. Allowed evidence

Return:

1. `.sandbox` directory existence;
2. immediate entry name/type/size/SHA256 for regular files;
3. `setup_error.json`:
   - existence;
   - raw file SHA256;
   - parsed `code`;
   - sanitized message;
   - raw message SHA256;
4. `setup_marker.json`:
   - existence;
   - SHA256;
   - parsed setup version if present;
5. every `sandbox.*.log`:
   - name;
   - SHA256;
   - size;
   - line count;
6. at most the last 80 setup-relevant log lines, sanitized before output.

## 4. Sanitization

The collector MUST replace:

- exact project root -> `<PROJECT_ROOT>`;
- exact user profile -> `<USERPROFILE>`;
- exact username path segment -> `<USER>`.

It must include only lines containing one or more setup-relevant tokens:

- `setup`
- `helper`
- `sandbox`
- `firewall`
- `acl`
- `user`
- `error`
- `fail`

No raw unfiltered log is returned.

## 5. Prohibitions

The collector MUST NOT:

- invoke Codex/App Server;
- invoke any setup/helper executable;
- execute RPC;
- execute diskpart;
- create/attach/detach/format/mount VHD/VHDX;
- modify/delete/rename files under A2 local root;
- change ACLs/firewall/users/groups;
- authorize `turn/start`;
- authorize or consume a scientific attempt.

## 6. Output

Create one file:

`g2e/.local/P5A-D2S2-A2/return/P5A_D2S2_A2_SANDBOX_STATE_RETURN_<UTC>.json`

The output must contain:

- `evidence_return_only=true`;
- `turn_start_request_sent=false`;
- `scientific_attempt_consumed=false`.

## 7. Qualification

PASS requires:

- PowerShell parser PASS;
- fixed-scope/static read-only tests PASS;
- sanitization tests PASS;
- no prohibited process/RPC/disk mutation tokens;
- P1/P1.4/P1.5/P2/P3/P4 regressions PASS.

A PASS authorizes exactly one local read-only sandbox-state collection.
