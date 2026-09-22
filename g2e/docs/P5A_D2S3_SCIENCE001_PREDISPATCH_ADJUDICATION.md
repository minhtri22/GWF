# G2E P5A D2-S3 — Science-001 Pre-Dispatch Adjudication

## Status

**Observed top-level status:** SCIENTIFIC_COLLECTION_BLOCKED  
**Scientific attempt consumed:** FALSE  
**turn/start sent:** FALSE  
**Scientific outcome observed:** NO  
**VHDX cleanup:** PASS

## Bound local report

- file: `P5A_D2S3_SCIENTIFIC_EXECUTION_REPORT.json`
- SHA256: `5da2db218c2b14856a5f07262cc840a63288fb81c490160ea83d0175d4cbca87`
- source HEAD: `d8cdb36b28c891e3fc262b24207791d24cd7679a`
- execution config:
  `df5308888eac7fa0b876f2cd68a51d0f2dd80a1b7c6d556cb04c854067b86e81`

Observed firewalls:

- `scientific_attempt_consumed=false`;
- `turn_start_request_sent=false`;
- `turn_start_accepted=false`;
- `turn_id=null`;
- `result_exists=false`;
- no runner evidence;
- no verifier evidence.

Cleanup closed the exact VHDX and records `attached_after_cleanup=false`.

Therefore this invocation is a pre-dispatch implementation INVALID and does not consume the frozen
D2-S3 scientific attempt.

## Root cause

Qualified runner blob:

`0048d25b7bd236b3bfe339d7b076ff8077d052e5`

contains:

`PREFLIGHT_MODULE_SHA = "ecd0af7cd487e14ea1691f4195af1d147efd0fe4"`

That value is the frozen Git blob identity of
`scripts/g2e/p5a_d2s3_platform_no_turn_preflight.py`.

The runner incorrectly evaluates:

`sha256_file(path) != PREFLIGHT_MODULE_SHA`

which compares a 64-hex SHA-256 file digest to a 40-hex Git blob identity. The predicate is
deterministically false even when the exact frozen preflight blob is present.

This failure occurs before scientific control-plane dispatch and before marker creation.

## Secondary diagnostic transport defect

The PowerShell one-click uses `$ErrorActionPreference = "Stop"` while capturing native Python stderr
with `2>&1`. On Windows PowerShell 5.1, a Python traceback emitted on stderr can surface as a terminating
`NativeCommandError` before the wrapper records the native exit code and complete output. This explains
why the top-level diagnostic contains only the first traceback line.

## Admissible repair

A bounded successor may:

1. verify the preflight script by exact Git blob identity using
   `git rev-parse HEAD:scripts/g2e/p5a_d2s3_platform_no_turn_preflight.py`;
2. preserve the frozen expected blob
   `ecd0af7cd487e14ea1691f4195af1d147efd0fe4`;
3. capture native runner/verifier stdout+stderr without PowerShell terminating on stderr;
4. preserve Science-001 evidence and use a fresh `SCIENCE-002` local root.

No scientific task, fixture, permission profile, admission graph, execution config, timeout, marker
boundary, retry budget, or outcome rule may change.

Because no marker was created, Science-002 is a replacement pre-dispatch invocation of the same
authorized attempt, not a scientific retry.
