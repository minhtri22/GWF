# G2E P5A D2-S3 — R1 Local Preturn Adjudication

## Status

**Observed verdict:** PRETURN_INVALID_OR_BLOCKED  
**Failure class:** NTFS ROOT-CLOSURE WRAPPER DEFECT  
**Python preflight invoked:** NO  
**turn/start:** FALSE  
**Scientific attempt consumed:** FALSE  
**Result created:** FALSE  
**VHDX cleanup:** PASS

## 1. Bound R1 report

- file: `P5A_D2S3_PLATFORM_NO_TURN_R1_REPORT.json`
- SHA256:
  `6b09fecc104ff334ee11c8e600c49110127996e3f6805a0bf93b77674cfb634f`
- source HEAD:
  `da9d1f7df07b48db72a7aa1dd87561bdf1d30b8e`
- qualified candidate:
  `3039c2d517ac63d5dc4a54d511dacdbe4799def7`
- one-click blob:
  `0527494c02fe4f7f2f0a075c61632286ebf29268`
- Python preflight blob:
  `ecd0af7cd487e14ea1691f4195af1d147efd0fe4`

The staged Codex/helper hashes remain the exact D2-S3 release-coherent identities.

## 2. Failure localization

Observed diagnostic:

`ISOLATED_VOLUME_PRESTATE_DRIFT:input.json,System Volume Information,TASK.md`

The wrapper reached isolated-volume construction and copied the frozen task payload, but rejected the
automatic NTFS support directory `System Volume Information` before fixture hash recording and before
invoking the Python platform preflight.

This is the same already-understood NTFS filesystem-support phenomenon previously qualified in D2-S2 A1.
It is not new scientific evidence and is not a platform setup outcome.

## 3. Firewalls and cleanup

The report records:

- `turn_start_request_sent=false`;
- `scientific_attempt_consumed=false`;
- `result_exists=false`;
- preflight evidence absent.

Cleanup records:

- attached before cleanup: true;
- action: `DISMOUNTED`;
- attached after cleanup: false;
- cleanup error: null.

Therefore the R1 run is invalidated before platform preflight and does not consume the D2-S3 scientific
attempt.

## 4. Admissible repair

A bounded R2 wrapper repair may replace strict root-name equality with the already-qualified closed-set
classification:

Task payload, exactly:

- `input.json`
- `TASK.md`

Optional filesystem-support metadata:

- `System Volume Information`, only when it is a directory.

Every other root entry remains blocking.

No Python preflight, RPC, permission, fixture, staged-instrument, model, scientific, threshold, or retry
semantics may change.

R1 local evidence must remain preserved. R2 must use a fresh local root and fresh VHDX.

## 5. Next macro-gate

`D2S3_PRETURN_NTFS_ROOT_CLOSURE_REPAIR_002`

The macro-gate includes specification, implementation, Windows/static qualification, original no-turn
regression, P1-P4 regressions, and exact lock. Only a full PASS authorizes one local R2 preflight.
