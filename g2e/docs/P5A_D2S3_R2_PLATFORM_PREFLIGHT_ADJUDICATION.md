# G2E P5A D2-S3 — R2 Platform Preturn Adjudication

## Status

PLATFORM PRETURN PASS / WRAPPER REPORTING INVALIDITY ONLY

- Scientific attempt consumed: FALSE
- turn/start sent: FALSE
- result.json present: FALSE
- VHDX cleanup: PASS

## Bound local report

- file: P5A_D2S3_PLATFORM_NO_TURN_R2_REPORT.json
- SHA256: b24af8e5261ba8e5a90605e7a9b9d63c0025f37650f9a4e657cdaafd76b0545e
- source HEAD: 0f0b836b395079e91add69e049e567b8577d62bb
- qualified candidate: 6e12bb7f92f47819c9970794b961784c9a4ab748
- one-click blob: 046291e068cc3c42bd4dcf200201ad91e38a0eeb
- preflight blob: ecd0af7cd487e14ea1691f4195af1d147efd0fe4
- preflight evidence SHA256: 87f18cf15f06eb1bc3e0a9e28f76e3208b2c082c3cd458221242d65db7b8cc28

Observed report facts:

- exact input/task/config hashes are present;
- preturn_gate_pass=true;
- turn_start_request_sent=false;
- scientific_attempt_consumed=false;
- result_exists=false;
- payload is exactly input.json + TASK.md;
- System Volume Information is the only filesystem-support metadata;
- unexpected root set is empty;
- VHDX was DISMOUNTED and attached_after_cleanup=false.

## Reporting-only invalidity

The top-level status became PRETURN_INVALID_OR_BLOCKED only after the Python preflight evidence had
already been loaded and preturn_gate_pass had been copied as true.

Windows PowerShell Set-StrictMode then evaluated the optional property driver_exception directly.
A successful Python evidence object does not contain driver_exception; that field is created only on
the Python exception path. Direct access therefore raised a missing-property exception in the wrapper.

The exact Python driver sets preturn_gate_pass=true only after all of these have passed:

- Windows sandbox readiness is ready;
- conditional elevated setup succeeds when required;
- configured MCP count is zero;
- installed/callable apps are zero;
- authentication is ready;
- the D2-S3 permission profile exists and is allowed;
- thread/start returns a thread id;
- active profile, when returned, matches g2e_p5a_d2s3;
- instruction sources are empty;
- no unexpected server request was observed.

On any driver exception, the same Python code sets preturn_gate_pass=false.

Therefore R2 is admitted as a successful platform preturn observation with a wrapper reporting defect.
No preflight rerun is required merely to manufacture a cleaner top-level status.

## Scientific authorization consequence

Scientific execution may be prepared prospectively, but dispatch must remain fail-closed on the exact
R2 evidence file. The scientific one-click must verify its exact SHA256 and all frozen preturn fields
before it can create the attempt-consumption marker or send turn/start.

Because D2-S3 uses a new official Codex executable hash, the old D1 manifest/final admission cannot be
reused. A new zero-science structural qualification and final admission are required first.
