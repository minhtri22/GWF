# G2E P5A D2-S3 — Scientific Pre-Dispatch Repair 001

## Status

SPEC-LOCKED / ZERO-SCIENCE / PRE-DISPATCH-REPAIR-ONLY

Baseline after adjudication:

`640e7bd217b1f1fd33d2033561b0d922b6340dd5`

Bound invalid Science-001 report SHA256:

`5da2db218c2b14856a5f07262cc840a63288fb81c490160ea83d0175d4cbca87`

## Permitted mutations

Only:

- `scripts/g2e/p5a_d2s3_scientific_runner.py`;
- `scripts/g2e/p5a_d2s3_scientific_oneclick.ps1`;
- repair qualification test/workflow;
- repair specification/lock.

## Required runner repair

The frozen preflight module identity is a Git blob ID, not a file SHA-256.

The runner MUST verify:

`git rev-parse HEAD:scripts/g2e/p5a_d2s3_platform_no_turn_preflight.py`

equals:

`ecd0af7cd487e14ea1691f4195af1d147efd0fe4`.

It MUST NOT compare that 40-hex value to `sha256_file()`.

## Required wrapper repair

Native runner and verifier execution MUST preserve full stdout/stderr and native exit code under
Windows PowerShell 5.1 without allowing stderr alone to terminate the wrapper before evidence/reporting.

The repair MUST NOT suppress a non-zero native exit status.

## Fresh replacement root

Science-001 remains immutable evidence.

The sole replacement pre-dispatch invocation MUST use:

`g2e/.local/P5A-D2S3-SCIENCE-002/`

with VHDX:

`P5A-D2S3-SCIENCE-002-TASK.vhdx`

and NTFS label:

`G2ED2S3S02`.

The scientific identity remains:

`p5a-d2s3-p5-fx-001-attempt-001`.

## Frozen scientific semantics

MUST remain unchanged:

- execution config hash:
  `df5308888eac7fa0b876f2cd68a51d0f2dd80a1b7c6d556cb04c854067b86e81`;
- R2 report/evidence hashes;
- official Codex/helper hashes;
- input/TASK hashes;
- permission profile `g2e_p5a_d2s3`;
- exact single marker-before-send attempt boundary;
- exactly one scientific `turn/start` code path;
- no automatic retry;
- turn timeout 90 seconds;
- independent verifier;
- finally/detach verification.

## Qualification

PASS requires:

- static proof that preflight blob is checked as a Git blob;
- negative test preventing SHA256-vs-Git-blob regression;
- exactly one `turn/start`;
- marker precedes send;
- Science-002 fresh root and Science-001 never removed/reused;
- PowerShell 5.1 parser PASS;
- infrastructure self-test PASS;
- native stderr/exit-code capture self-test PASS;
- original D2-S3 scientific macro tests PASS;
- inherited no-turn tests PASS;
- P1/P1.4/P1.5/P2/P3/P4 regressions PASS;
- no model turn in CI.

PASS verdict:

`D2S3_SCIENTIFIC_PREDISPATCH_REPAIR_PASS_ONE_SCIENCE002_INVOCATION_AUTHORIZED`

No retry is authorized after the attempt-consumption marker exists.
