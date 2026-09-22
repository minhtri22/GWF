# P5A D2-S2 Diagnostic Return Wrapper — Provenance Repair

## Status

SPEC-LOCKED / ZERO-SCIENCE / REPORT-PROVENANCE-ONLY

Baseline:

- branch: `feature/g2e-framework`
- exact baseline HEAD: `3f845c8e2f7521dd3d7f092b7dc4c94269d047f3`
- elevation bootstrap diagnostic qualification remains frozen;
- egg-info source-hygiene repair is qualified;
- D2-S2 scientific attempt remains NOT AUTHORIZED and NOT CONSUMED.

## Observed transport problem

The user returned the same stale bootstrap diagnostic report more than once after the source-hygiene
repair. The stale report carries source HEAD `54950e2c...`, the old timestamp, and the old generated
egg-info blocker.

This is a report provenance/return-path problem. It is not evidence that the hygiene repair failed.

## Frozen wrapper behavior

The wrapper MAY:

1. fetch `origin feature/g2e-framework`;
2. detach to exact `origin/feature/g2e-framework`;
3. record the exact resulting HEAD and wrapper start time;
4. archive any prior bootstrap report rather than deleting evidence;
5. invoke the already-qualified
   `scripts/g2e/p5a_d2s2_elevation_bootstrap_diagnostic.ps1`;
6. read the newly produced diagnostic JSON;
7. reject the result unless:
   - `report.source_head` equals the exact detached HEAD;
   - `report.started_utc` is not older than the wrapper invocation;
   - `scientific_attempt_consumed == false`;
   - `model_turn_executed == false`;
8. materialize a uniquely named return JSON containing exact HEAD and UTC timestamp in its filename.

The wrapper MUST NOT:

- invoke Codex or Codex App Server directly;
- send RPC;
- create/mount/format VHD/VHDX;
- touch the scientific fixture;
- contain or send `turn/start`;
- authorize or consume a scientific attempt;
- mutate D2-S2 one-click/preflight blobs.

## Return artifact

Directory:

`g2e/.local/P5A-D2S2-BOOTSTRAP/return/`

Filename pattern:

`P5A_D2S2_ELEVATION_BOOTSTRAP_REPORT_<HEAD12>_<UTC>.json`

A return artifact is valid only if its embedded `source_head` is exactly the HEAD encoded by the wrapper
execution.

## Adjudication

- `RETURN_WRAPPER_PASS_LOCAL_EXECUTION_REQUIRED`: static/CI qualification passes.
- otherwise: wrapper remains blocked.

A wrapper PASS authorizes only one fresh local bootstrap diagnostic invocation. It does not authorize the
D2-S2 isolated-volume preflight, scientific attempt, runtime adapter, or model turn.
