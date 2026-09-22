# P5A D2-S2 Diagnostic Return Wrapper — Native Stderr Runtime Repair

## Status

SPEC-LOCKED / ZERO-SCIENCE / WRAPPER-NATIVE-IO-REPAIR-ONLY

Baseline:

- branch: `feature/g2e-framework`
- exact baseline HEAD: `3904b1261b7eceae2ef81b5038430bec1b79ea2e`
- D2-S2 scientific attempt remains NOT AUTHORIZED and NOT CONSUMED.

## Observed runtime failure

Windows PowerShell 5.1 entered the repaired wrapper and called:

`git fetch --prune origin feature/g2e-framework`

Git emitted normal fetch progress to stderr beginning with:

`From https://github.com/minhtri22/GWF`

The wrapper used native invocation with `2>&1` while global `$ErrorActionPreference = "Stop"`.
Windows PowerShell surfaced the native stderr record as `NativeCommandError` before the wrapper could
inspect `$LASTEXITCODE`.

This is a wrapper native-I/O defect. It is not a Git failure and is not scientific evidence.

## Frozen repair

The repair SHALL:

1. keep the previously qualified `$GitArgs` argument-vector repair;
2. replace direct PowerShell native Git capture with `System.Diagnostics.Process`;
3. set `UseShellExecute = false`;
4. redirect stdout and stderr independently;
5. wait for process exit and adjudicate only by the native process `ExitCode`;
6. return stdout on success, regardless of non-empty stderr;
7. include both stdout and stderr only in the thrown diagnostic when `ExitCode != 0`;
8. preserve support for repository paths containing spaces via explicit native argument quoting;
9. add a zero-science runtime self-test using:
   `git fetch --dry-run --verbose origin feature/g2e-framework`
   so CI covers the exact class “native stderr present + exit 0”.

## Prohibitions

The repair MUST NOT:

- invoke Codex or Codex App Server;
- send RPC or `turn/start`;
- create/attach/format/mount VHD/VHDX;
- touch scientific fixture content;
- authorize or consume a scientific attempt;
- alter model/task/verifier/retry semantics;
- alter the frozen D2-S2 isolated-volume one-click, preflight, or elevation diagnostic blobs.

## Qualification

PASS requires:

- PowerShell parser PASS;
- real Git basic helper self-test PASS;
- real Git dry-run fetch stderr-path self-test PASS;
- wrapper regression QA PASS;
- elevation diagnostic, egg-info hygiene, and frozen D2-S2 qualification PASS;
- P1/P1.4/P1.5/P2/P3/P4 regressions PASS;
- zero-science proof PASS;
- frozen blob identities PASS.

Adjudication:

`RETURN_WRAPPER_NATIVE_STDERR_REPAIR_PASS_LOCAL_EXECUTION_REQUIRED`

A PASS authorizes only one fresh local execution of the repaired diagnostic return wrapper.
