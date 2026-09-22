# G2E P5A D2-S3 — Preturn NTFS Root-Closure Repair 002

## Status

SPEC-LOCKED / ZERO-SCIENCE / IMPLEMENTATION-REPAIR-ONLY

Baseline:

- branch: `feature/g2e-framework`
- exact baseline HEAD: `a6735efc74302e67c9b71fb313c757138d793dac`
- bound invalid R1 report SHA256:
  `6b09fecc104ff334ee11c8e600c49110127996e3f6805a0bf93b77674cfb634f`

## 1. Permitted repair

Replace only the wrapper's strict isolated-volume root equality check with deterministic closed-set
classification.

Required classification:

### Task payload

Exactly two regular files:

- `input.json`
- `TASK.md`

### Optional filesystem-support metadata

At most:

- `System Volume Information`, and only as a directory.

### Blocking entries

Any other file, directory, reparse point, or root entry is unexpected and MUST block preflight.

The wrapper must record payload, metadata, and unexpected root-name sets in the top-level report.

## 2. Fresh R2 local root

The invalid R1 root remains immutable evidence.

R2 must use:

`g2e/.local/P5A-D2S3-PREFLIGHT-R2/`

Fresh VHDX:

`P5A-D2S3-PREFLIGHT-R2-TASK.vhdx`

NTFS label:

`G2ED2S3R2`

Report:

`P5A_D2S3_PLATFORM_NO_TURN_R2_REPORT.json`

## 3. Frozen semantics

MUST remain unchanged:

- study ID:
  `p5a-d2s3-release-coherent-instrument-successor`;
- scientific attempt ID:
  `p5a-d2s3-p5-fx-001-attempt-001`;
- permission profile:
  `g2e_p5a_d2s3`;
- fixture hashes;
- staged Codex/helper hashes;
- staging report hash;
- config serialization repair from R1;
- Python preflight driver blob:
  `ecd0af7cd487e14ea1691f4195af1d147efd0fe4`;
- RPC allowlist;
- no-turn firewall;
- App isolation overrides;
- VHDX `finally` detach/verify contract.

## 4. Qualification

The macro-gate must prove all of the following before local execution:

1. PowerShell parser PASS under pwsh;
2. PowerShell parser PASS under Windows PowerShell 5.1;
3. Windows config-serialization self-test PASS;
4. deterministic root-classification self-test PASS for:
   - exact payload only;
   - exact payload + `System Volume Information` directory;
   - rejection of unexpected file;
   - rejection of unexpected directory;
   - rejection of `System Volume Information` when not a directory;
5. Python preflight blob unchanged;
6. original D2-S3 exact RPC/no-turn qualification still PASS;
7. protected VHDX body contains no `exit`;
8. P1/P1.4/P1.5/P2/P3/P4 regressions PASS.

PASS verdict:

`NTFS_ROOT_CLOSURE_REPAIR_PASS_ONE_LOCAL_R2_PREFLIGHT_REQUIRED`

A PASS authorizes exactly one fresh local R2 no-turn preflight. It does not authorize scientific
execution.
