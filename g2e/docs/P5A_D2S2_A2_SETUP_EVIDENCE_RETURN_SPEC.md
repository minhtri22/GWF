# G2E P5A D2-S2 A2 — Windows Sandbox Setup Evidence Return Diagnostic

## Status

SPEC-LOCKED / ZERO-SCIENCE / READ-ONLY-EVIDENCE-RETURN

Baseline:

- branch: `feature/g2e-framework`
- exact baseline HEAD: `a1af16f29f8de2ee644766eccc50f8267ad46a3b`
- bound A2 report SHA256:
  `2dd26dd7ce3a337307147c4be82da1f653ab76048abf3cba6bca7c0c8555c5d8`
- bound A2 preflight evidence SHA256:
  `984f828c4796b77d7bd125d5e5a8421c04f9b496d9117b6f1f5003d9b8a1e2c3`

## 1. Purpose

Return enough already-created A2 setup evidence to adjudicate the Windows sandbox helper failure without
rerunning A2 and without touching science.

## 2. Fixed inputs

The collector reads only:

- `g2e/.local/P5A-D2S2-A2/report/P5A_D2S2_A2_ONECLICK_REPORT.json`
- the preflight evidence path named by that report, which must remain under
  `g2e/.local/P5A-D2S2-A2/evidence/preturn-a2/`
- optional existing sanitized protocol/stderr-hash logs in the same evidence directory.

It must verify:

1. report SHA256 equals the bound report hash;
2. report source HEAD is `17bf616138433f96ee3447e8f846aad430df3771`;
3. report one-click/preflight blobs match the A2 qualification lock;
4. report firewalls are false;
5. evidence file SHA256 equals both the report-declared SHA and the bound evidence hash;
6. evidence file remains inside the fixed A2 evidence directory.

## 3. Returned setup fields

The return artifact may include only already-recorded/sanitized setup state:

- readiness before/after;
- setup requested/started/completed/success;
- setup mode;
- setup error code;
- redacted setup error;
- setup error SHA256;
- driver exception;
- App Server exit code;
- MCP/app/auth/profile/thread gate fields;
- result existence;
- input/task unchanged flags;
- workspace names;
- Codex-home post entries;
- hashes, sizes and line counts of the sanitized protocol and stderr-hash JSONL files.

No raw App Server stderr is returned.

## 4. Output

Create:

`g2e/.local/P5A-D2S2-A2/return/P5A_D2S2_A2_SETUP_EVIDENCE_RETURN_<UTC>.json`

The output must state:

- `scientific_attempt_consumed=false`;
- `turn_start_request_sent=false`;
- `evidence_return_only=true`.

## 5. Prohibitions

The collector MUST NOT:

- invoke Codex/App Server;
- send RPC;
- execute diskpart;
- create/attach/detach/format/mount VHD/VHDX;
- modify A2 report/evidence/protocol/stderr logs;
- delete or rename prior local artifacts;
- authorize model/scientific execution.

## 6. Qualification

PASS requires:

- PowerShell parser PASS;
- static read-only scope tests PASS;
- exact bound hashes embedded;
- no process-launch tokens for Codex/diskpart/App Server;
- P1/P1.4/P1.5/P2/P3/P4 regressions PASS.

A PASS authorizes exactly one local evidence-return execution.
