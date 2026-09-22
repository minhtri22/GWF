# G2E P5A D2-S4 — Post-Closure Terminal-Failure Decomposition Result

## Status

**Bundle-level mechanism class:** UNRESOLVED_FROM_EXISTING_BUNDLE  
**Reason:** decisive `TurnError` payload was not preserved by the sanitized protocol recorder  
**Existing-local-evidence recovery justified:** YES  
**D2-S4 verdict:** unchanged — INVALID / ATTEMPT CONSUMED / NO RETRY

## 1. Bound bundle

- bundle SHA256:
  `ad7aef6c621554791213635c802578c5cc0f94f8e2e12381b5e629fd2836be39`
- manifest SHA256:
  `f6babf3e5dddb579be552247948f5a58cf1d3b39fe4d44e5790898d071c3d1f1`
- protocol SHA256:
  `69b8a585e684f9d0b72ab6c1144cda9fd72a0440f35dba6a15164c60f9471e10`
- Science-001 report SHA256:
  `e98ee53c550e13dd42715c63ca6cbf887aa69396f50c90abc6637a54a3dc9536`
- runner evidence SHA256:
  `6e1ef9d48bf640a8a285370549771f76048e0280eaf121450f3fa6679c069f5d`
- actual verification SHA256:
  `bf0e848c1eba9e8c0bf8a74da5fcf96dbe29898ec26d1ef91d21aca13a7be01b`

Collection mode was read-only: no Codex start, no RPC, no VHDX mount, no scientific retry.

## 2. Verification hash finding resolution

The collector manifest records:

- expected verification SHA256:
  `bf0e848c1eba9e8c0bf8a74da5fcf96dbe29898ec26d1ef91d21aca13a7be01`
- actual verification SHA256:
  `bf0e848c1eba9e8c0bf8a74da5fcf96dbe29898ec26d1ef91d21aca13a7be01b`

The expected value is only 63 hexadecimal characters. The actual value is 64 hexadecimal characters
and is exactly the verification hash recorded in the frozen top-level Science-001 report.

Therefore the mismatch is a governance transcription defect introduced after the scientific run, not
evidence mutation.

Finding:

`VERIFICATION_HASH_EXPECTED_VALUE_TRUNCATED_BY_ONE_HEX_CHAR`

Consequence:

- no scientific evidence-integrity downgrade;
- D2-S4 formal verdict unchanged;
- future governance artifacts must bind the full 64-hex value ending in `...be01b`.

## 3. Protocol sequence

The sanitized protocol establishes the following sequence after control-plane qualification:

1. `thread/started`
2. `warning`
3. `thread/status/changed`
4. `turn/started`
5. `item/started`
6. `item/completed`
7. `account/rateLimits/updated`
8. `thread/status/changed`
9. `error`
10. `turn/completed`

The runner independently records:

- `turn_terminal=true`;
- `terminal_status="failed"`;
- `turn_timeout=false`;
- `unexpected_server_request=false`;
- `driver_exception=null`;
- `result_exists=false`.

This rules out the D2-S3 client queue failure as the D2-S4 mechanism.

## 4. Exact upstream semantic boundary

At exact upstream source commit
`3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`:

- `ErrorNotification` contains a `TurnError`, a `will_retry` flag, `thread_id`, and `turn_id`;
- a failed `Turn` contains `error: Option<TurnError>`;
- `TurnError` contains:
  - `message`;
  - `codex_error_info`;
  - `additional_details`;
  - optional `misalignment`.

Those fields are the mechanism-bearing evidence needed to distinguish provider/model failure,
sandbox/permission failure, server-internal failure, turn semantic failure, policy/misalignment, or
another terminal-failure class.

## 5. Measurement limitation

The D2-S4 sanitized protocol recorder retained only:

- method;
- id where applicable;
- byte length;
- raw SHA256;
- timestamp.

It did not preserve the `error` notification payload or the failed turn's `turn.error`.

Therefore the existing bundle cannot scientifically discriminate among the registered terminal-failure
mechanism classes.

The correct bundle-level adjudication is:

`UNRESOLVED_FROM_EXISTING_BUNDLE`.

## 6. Why recovery is still admissible

The local Science-001 `CODEX_HOME` remains under:

`g2e/.local/P5A-D2S4-SCIENCE-001/codex-home`

after the run.

Exact upstream storage semantics persist thread/session material under `sessions` /
`archived_sessions` and may also materialize local SQLite/thread-state records and logs.

Those are already-produced local artifacts from the consumed D2-S4 attempt.

A read-only recovery may therefore inspect only records linked to the exact D2-S4 thread/turn IDs:

- thread:
  `01a0c9af-d509-7203-9608-06304738b12e`
- turn:
  `01a0c9af-d523-72f3-84fa-a575e91076b6`

without starting Codex, sending RPC, mounting VHDX, or rerunning the scientific attempt.

## 7. Next step

Open a bounded persisted-error recovery workstream.

The recovery MUST exclude credential/config material and MUST emit only records attributable to the
exact D2-S4 thread/turn IDs plus minimal provenance.

No D2-S5 successor is authorized until that recovery either:

1. identifies a concrete terminal-failure mechanism, or
2. returns `UNRESOLVED_FROM_EXISTING_LOCAL_EVIDENCE`.
