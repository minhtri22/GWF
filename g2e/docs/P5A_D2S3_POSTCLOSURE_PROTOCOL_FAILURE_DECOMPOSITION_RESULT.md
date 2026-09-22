# G2E P5A D2-S3 — Post-Closure Protocol Failure Decomposition Result

## Status

**Mechanism class:** CLIENT_QUEUE_OR_READER_FAILURE  
**Exact mechanism:** UNCAUGHT_QUEUE_EMPTY_IN_RPC_CLIENT_NEXT_MESSAGE  
**D2-S3 scientific verdict:** unchanged — TERMINAL INVALID / ATTEMPT CONSUMED / NO RETRY  
**D2-S4 successor justified:** YES

## 1. Bound post-closure bundle

- bundle SHA256:
  `1775c3430692ec4e8037eb1776368d2544f5268d4dd71df77c63f3fca5c6eb66`
- manifest SHA256:
  `e05c68c85bc5b3d7a5ec1b0c930cddf64a0031478065ab5b9ad3a527c313ea56`
- Science-002 top-level report SHA256:
  `09e71058bd9e9b4b4fd2e5c4f5f0c412c228932fa183d08dc7d6df4d0fc5e712`
- runner evidence SHA256:
  `ae60858bfd53268fbb43fb5f1166aaa3acd4fe322f23279b139412bb260b8017`
- verification SHA256:
  `528b1fd3460c1efdd180dfab703dc264a5102d44fabf887411dc3f1bbc51c418`
- sanitized protocol SHA256:
  `f181f34459b5c233b91d45e8c411ad808bb6a1fb2892841cb41bd9c7e5b86ed2`
- turn-start marker SHA256:
  `69a15abfbf2ffd3933d5f5e946382d174c02b075c6cb73cb3e133a7d6b6ded00`
- stderr-hash file: not materialized; this is valid because the frozen RpcClient writes that file only after the first stderr record.

Collection was read-only: Codex not started, no RPC sent, no VHDX mounted, no scientific retry.

## 2. Observed timing

The final sanitized protocol record is:

`turn/started`

at Unix timestamp:

`1790087075.1843534`.

Runner evidence records:

`finished_at_unix = 1790087076.2615757`.

Elapsed time from final `turn/started` record to runner finish:

`1.0772223 s`.

The frozen scientific turn timeout is 90 seconds.

Therefore Science-002 did not reach the frozen turn timeout boundary.

## 3. Exact client control flow

Frozen `RpcClient.next_message(timeout)` computes a deadline and then calls:

`self.q.get(timeout=remaining)`

without catching `queue.Empty`.

Python `queue.Queue.get(timeout=...)` raises `queue.Empty` when the queue receives no item before the
requested timeout.

Frozen `wait_for_turn()` calls:

`client.next_message(min(remaining, 1.0))`

inside:

`except TimeoutError: continue`

but does not catch `queue.Empty`.

Consequently, the first one-second interval with no new queue item after `turn/started` raises
`queue.Empty`, bypasses the intended retry loop, reaches the outer runner exception handler, and is
serialized as:

`driver_exception = "Empty:"`

because the exception type is `Empty` and its message is empty.

This matches the bundle exactly.

## 4. App Server exit-code interpretation

Runner evidence contains:

`app_server_exit_code = 1`.

This is not evidence that App Server independently terminated before the client failure.

The frozen runner `finally` block checks `proc.poll()`; if the server is still running, it explicitly
calls `proc.terminate()`, waits, and only then records `proc.poll()`.

Therefore the recorded exit code is downstream of runner cleanup and cannot establish an antecedent
server crash.

## 5. Mechanism classification

Selected:

`CLIENT_QUEUE_OR_READER_FAILURE`

Sub-mechanism:

`UNCAUGHT_QUEUE_EMPTY_IN_RPC_CLIENT_NEXT_MESSAGE`

Evidence chain:

1. `turn/start` accepted;
2. `turn/started` observed;
3. no protocol record after `turn/started`;
4. only ~1.077 s elapsed;
5. frozen wait loop polls `next_message(..., <=1 s)`;
6. `next_message` leaks `queue.Empty`;
7. wait loop catches only `TimeoutError`;
8. runner records exactly `Empty:`.

## 6. Alternative mechanisms ruled out or unsupported

### UNEXPECTED_SERVER_REQUEST_PATH — ruled out

Runner evidence:

- `unexpected_server_request=false`;
- no unexpected-server-request record is present.

### TURN_NOTIFICATION_MATCHING_OR_CONSUMPTION_FAILURE — unsupported

No `turn/completed` record exists in sanitized protocol before the client abort. There is therefore no
evidence of a completion notification that was received but mismatched or consumed incorrectly.

### SERVER_NONTERMINAL_TURN_FAILURE — not established

The client aborted after ~1.077 s. The frozen 90 s terminal observation window was never exercised.
No conclusion about 90 s server nontermination can be drawn.

### APP_SERVER_TERMINATION_OR_TRANSPORT_FAILURE — not established

No stdout EOF record or stderr evidence was captured before the exception. The runner cleanup itself
terminates the process and then records the exit code.

## 7. Scientific consequence

D2-S3 remains permanently closed as INVALID because its consumed attempt cannot be retried.

However, the invalidity is attributable to a deterministic client-side observation defect rather than
to the task/model result.

A new successor is scientifically justified because:

- the defect is mechanistically identified;
- its repair can be specified prospectively;
- the repair does not depend on task outcome;
- the D2-S3 attempt identity will not be reused;
- all task, fixture, permission, official-harness and adjudication semantics can remain frozen.

## 8. Required prospective repair before any new attempt

A successor client MUST ensure that an empty one-second polling interval does not terminate the turn
observation loop.

Permitted equivalent forms include:

- catch `queue.Empty` in `RpcClient.next_message()` and rethrow `TimeoutError`; or
- catch `queue.Empty` alongside `TimeoutError` in `wait_for_turn()`.

Qualification MUST prove with synthetic delayed-message tests that:

1. repeated empty one-second intervals do not abort the wait loop;
2. a terminal notification arriving after more than one polling interval is still consumed;
3. the total deadline remains authoritative;
4. true stdout EOF still fails closed;
5. unexpected server requests still fail closed;
6. no model turn occurs during qualification.

No D2-S3 rerun is authorized.
