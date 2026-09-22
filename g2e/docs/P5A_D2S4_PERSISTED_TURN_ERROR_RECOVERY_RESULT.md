# G2E P5A D2-S4 — Persisted Turn-Error Recovery Result

## Status

**Recovery verdict:** UNRESOLVED_FROM_EXISTING_LOCAL_EVIDENCE  
**Scientific verdict:** unchanged — INVALID / ATTEMPT CONSUMED / NO RETRY  
**D2-S5 successor:** NOT AUTHORIZED  
**Further D2 model execution:** STOP

## 1. Bound recovery bundle

- bundle file:
  `P5A-D2S4-PERSISTED-ERROR-RECOVERY.zip`
- bundle SHA256:
  `60a94c50d9eaba65c49840ffeb5861d347aab2298b91d213bb6ea910de6f3a1b`
- recovery JSON:
  `P5A_D2S4_PERSISTED_TURN_ERROR_RECOVERY.json`
- recovery JSON SHA256:
  `72ad98eb08ac225ac6bbcb21fbbf44852264fe2474bd960db0d8402052572cd8`
- recovery schema:
  `G2E-P5A-D2S4-PERSISTED-TURN-ERROR-RECOVERY-v1`

Exact target identity:

- thread:
  `01a0c9af-d509-7203-9608-06304738b12e`
- turn:
  `01a0c9af-d523-72f3-84fa-a575e91076b6`

## 2. Recovery firewalls

The recovery report records:

- `collection_mode = READ_ONLY_EXISTING_LOCAL_EVIDENCE`;
- `codex_started = false`;
- `rpc_sent = false`;
- `vhdx_mounted = false`;
- `scientific_attempt_retried = false`;
- `forbidden_files_read = false`.

Therefore this recovery does not alter D2-S4 scientific state and does not create a new attempt.

## 3. Recovered evidence

### Text/session/log evidence

- `scanned_text_files = []`
- `text_match_count = 0`
- `text_matches = []`

No allowed text/session/log artifact containing the exact thread or turn ID was materialized in the
recoverable Science-001 local state.

### SQLite evidence

Six SQLite files were inspected read-only:

1. `science-001\\goals_1.sqlite`
2. `science-001\\logs_2.sqlite`
3. `science-001\\memories_1.sqlite`
4. `science-001\\queue_1.sqlite`
5. `science-001\\state_5.sqlite`
6. `science-001\\thread_history_1.sqlite`

Observed:

- `sqlite_match_count = 0`
- `sqlite_matches = []`

No row in the allowed SQLite scope contained the exact thread or turn ID.

## 4. Mechanism consequence

The previous sanitized protocol bundle established:

`turn/started → item/started → item/completed → account/rateLimits/updated → thread/status/changed → error → turn/completed(failed)`

but did not preserve the mechanism-bearing `TurnError` payload.

The persisted-error recovery also produced no matching text/session/log or SQLite record from which
the missing `TurnError` fields could be reconstructed.

Therefore the terminal failure cannot be scientifically classified as:

- model/provider execution failure;
- sandbox/permission execution failure;
- server-internal turn failure;
- tool/item execution failure;
- turn/request semantic failure;
- transport failure reported as terminal failed;
- another concrete mechanism.

The only admissible final mechanism adjudication is:

`UNRESOLVED_FROM_EXISTING_LOCAL_EVIDENCE`.

## 5. Why D2-S5 is not authorized

A D2-S5 model-bearing attempt would now require collecting new runtime data specifically because the
D2-S4 mechanism remained unresolved.

Without a concrete mechanism hypothesis, such an attempt would be exploratory rescue after two
consumed INVALID successors:

- D2-S3: client queue observation defect;
- D2-S4: server-declared terminal failed, mechanism not recoverable from preserved evidence.

The current evidence does not identify a single prospective mechanism change that can be preregistered
independently of outcome.

Therefore a D2-S5 scientific successor is not justified under the existing no-rescue governance.

## 6. Final D2 disposition

The D2 line is closed at:

`UNRESOLVED_FROM_EXISTING_LOCAL_EVIDENCE / STOP_MODEL_EXECUTION / NO_D2S5_AUTHORIZATION`.

Any future work in this area must begin as a new measurement/instrumentation program that improves
prospective error observability before any new model-bearing scientific attempt is proposed.

Such a program must not be framed as a D2-S4 retry or D2-S5 rescue.
