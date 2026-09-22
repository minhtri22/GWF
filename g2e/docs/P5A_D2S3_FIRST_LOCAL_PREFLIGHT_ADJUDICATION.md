# G2E P5A D2-S3 — First Local Platform Preflight Adjudication

## Status

**Observed verdict:** PRETURN_INVALID_OR_BLOCKED  
**Failure class:** WRAPPER CONFIG-SERIALIZATION IMPLEMENTATION DEFECT  
**App Server started:** NO EVIDENCE / NOT REACHED  
**turn/start:** FALSE  
**Scientific attempt consumed:** FALSE  
**Result created:** FALSE  
**VHDX cleanup:** PASS

## 1. Bound local report

- file: `P5A_D2S3_PLATFORM_NO_TURN_REPORT.json`
- SHA256:
  `850188c448e182d2808819c20a837c86b0e489a114156552f15f906e27ed0dd6`
- source HEAD:
  `bb0d96a8d93e35ad48d25fc8425b48c5c0e6ae13`
- qualified candidate:
  `c1878bb34a8325f42483fba239f2b8cb73c81594`
- one-click blob:
  `e7cf24562425f3bbdfd8b5c2275eaa266ccb970b`
- preflight blob:
  `ecd0af7cd487e14ea1691f4195af1d147efd0fe4`

The report binds the expected staged instrument and fixture hashes.

## 2. Failure localization

Observed:

- isolated VHDX creation succeeded;
- input/task copies succeeded and matched frozen hashes;
- `config_sha256=null`;
- no preflight evidence file exists;
- diagnostic is a Windows PowerShell overload conversion error:
  `String.Replace` attempted to bind the first argument `CRLF` to `System.Char`.

The failing implementation expression is:

`$config.Replace([Environment]::NewLine, [char]10) + [char]10`

On Windows PowerShell 5.1 the second argument forces the `Replace(char,char)` overload, after which the
two-character CRLF string cannot be converted to one `System.Char`.

This occurs before the Python preflight driver is invoked.

## 3. Firewalls preserved

The returned report records:

- `turn_start_request_sent=false`;
- `scientific_attempt_consumed=false`;
- `result_exists=false`.

Therefore this failure does not consume the D2-S3 scientific attempt.

## 4. Resource cleanup

The same report records:

- VHDX attached before cleanup: true;
- cleanup action: `DISMOUNTED`;
- attached after cleanup: false;
- cleanup error: null.

The new VHDX hygiene contract worked as designed.

## 5. Governance consequence

A bounded implementation repair is admissible because the failure occurred before App Server/preflight
execution and before any scientific dispatch.

No RPC, permission, fixture, instrument, model, task, threshold, retry, or scientific semantics may change.

The invalid local preflight root must be preserved as evidence. A repair execution must use a fresh
repository-local preflight root.

## 6. Next gate

`D2S3_PRETURN_CONFIG_SERIALIZATION_REPAIR_001`

Only after the repair passes Windows PowerShell 5.1 qualification may one fresh no-turn local preflight
be authorized.
