# G2E P5A D2-S3 — Preturn Config Serialization Repair 001

## Status

SPEC-LOCKED / ZERO-SCIENCE / IMPLEMENTATION-REPAIR-ONLY

Baseline:

- branch: `feature/g2e-framework`
- exact baseline HEAD: `21fae70d98e0da3f0e3ad85d79864b01cb3dfcb5`
- bound invalid local report SHA256:
  `850188c448e182d2808819c20a837c86b0e489a114156552f15f906e27ed0dd6`

## 1. Permitted repair

Replace only the newline normalization expression that is incompatible with Windows PowerShell 5.1.

Required deterministic normalization:

1. replace CRLF with LF using the string/string overload;
2. replace any residual CR with LF using the string/string overload;
3. append exactly one LF;
4. write UTF-8 without BOM.

A helper function may be introduced for this exact transformation.

## 2. Fresh repair root

The invalid first preflight root is evidence and MUST NOT be deleted, overwritten, or reused.

The repair run must use:

`g2e/.local/P5A-D2S3-PREFLIGHT-R1/`

with a fresh VHDX:

`P5A-D2S3-PREFLIGHT-R1-TASK.vhdx`

and a distinct NTFS label:

`G2ED2S3R1`.

This is a preturn implementation retry only. It does not create a new scientific attempt.

## 3. Frozen semantics

MUST remain unchanged:

- study ID;
- scientific attempt ID;
- permission profile ID;
- fixture hashes;
- staged Codex/helper hashes;
- staging report hash;
- RPC allowlist;
- no-turn firewall;
- App isolation overrides;
- VHDX cleanup `finally` contract;
- PASS criteria.

The Python preflight driver blob MUST remain unchanged.

## 4. Qualification

PASS requires:

- PowerShell parser PASS under pwsh;
- PowerShell parser PASS under Windows PowerShell 5.1;
- real Windows PowerShell 5.1 config-serialization self-test PASS;
- generated self-test bytes use LF only, no CR, and exactly one trailing LF;
- protected VHDX body still contains no `exit`;
- Python preflight blob unchanged;
- exact RPC/no-turn static QA unchanged;
- P1/P1.4/P1.5/P2/P3/P4 regressions PASS.

PASS verdict:

`CONFIG_SERIALIZATION_REPAIR_PASS_ONE_LOCAL_R1_PREFLIGHT_REQUIRED`

It authorizes exactly one fresh local R1 no-turn preflight and does not authorize scientific execution.
