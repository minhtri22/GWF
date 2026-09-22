# G2E P5A D2-S4 — Pre-Execution QA

## Scope

QA the queue-safe D2-S4 successor before local scientific execution.

## Checks

- D2-S3 remains formally closed and cannot be retried.
- D2-S4 has a new study ID and new attempt ID.
- Post-closure bundle hash is bound.
- Queue failure mechanism is explicitly identified.
- Only queue polling semantics changed.
- Exact official Codex/helper hashes remain unchanged.
- P5-FX-001 input/TASK hashes remain unchanged.
- Permission profile policy is intentionally reused unchanged.
- Fresh runtime control-plane checks precede marker creation.
- Exactly one scientific `turn/start` code path exists.
- Marker precedes transport write.
- Turn timeout remains 90 seconds.
- Retry budget remains zero.
- Independent verifier does not assign the scientific verdict.
- D2-S4 root is fresh `P5A-D2S4-SCIENCE-001`.
- VHDX cleanup remains protected by `finally`.
- Synthetic delayed-notification test survives >2 seconds and multiple empty polls.
- True stdout EOF remains fail-closed.
- Unexpected server request remains fail-closed.
- Linux static/inherited/P1-P4 qualification PASS.
- Windows PowerShell 5.1/infrastructure/structural/P1.5 qualification PASS.
- No model turn occurred during qualification.
- Execution-critical blobs match the exact qualified candidate.

## Findings

`count = 0`

No open finding blocks the single authorized D2-S4 local scientific execution.
