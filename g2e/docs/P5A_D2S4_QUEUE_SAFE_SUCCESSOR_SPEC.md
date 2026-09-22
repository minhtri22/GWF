# G2E P5A D2-S4 — Queue-Safe Scientific Successor

## Status

PREREGISTERED / NEW SUCCESSOR / ZERO-SCIENCE UNTIL LOCK

Predecessor:

`P5A_D2S3_POSTCLOSURE_PROTOCOL_FAILURE_DECOMPOSITION_RESULT.md`

## 1. Identity

- study:
  `p5a-d2s4-queue-safe-scientific-successor`
- attempt:
  `p5a-d2s4-p5-fx-001-attempt-001`
- permission profile:
  `g2e_p5a_d2s3` (exact previously qualified infrastructure policy; reused intentionally to avoid a second mechanism change)

D2-S3 attempt identity MUST NOT be reused.

## 2. Scientific invariants inherited unchanged

- P5-FX-001 `input.json` SHA256:
  `a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6`
- `TASK.md` SHA256:
  `4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e`
- official Codex SHA256:
  `444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b`
- official setup-helper SHA256:
  `0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4`
- isolated NTFS VHDX;
- root read + exact `result.json` write;
- network disabled;
- MCP/apps disabled;
- no instruction sources;
- approval policy `never`;
- turn timeout = 90 seconds;
- retry budget = 0;
- one durable marker immediately before exactly one scientific `turn/start`;
- independent result verifier;
- finally/detach verification.

Expected P5-FX-001 result semantics remain unchanged.

## 3. Sole mechanism change

Repair only the client polling abstraction responsible for D2-S3 invalidity.

Required behavior:

`queue.Empty` caused by an ordinary bounded poll with no message MUST be normalized to the client's
existing timeout abstraction and MUST NOT escape as a fatal driver exception before the total turn
deadline.

Preferred implementation:

- in the shared `RpcClient.next_message()`, catch `queue.Empty` from `self.q.get(timeout=remaining)`;
- raise `TimeoutError()`.

This preserves existing `wait_for_id`, `wait_for_notification`, and `wait_for_turn` semantics.

No task/model/result/adjudication tuning is permitted.

## 3.1 Runtime authorization model

D2-S4 does not require a separate user-run no-turn preflight. The single local invocation MUST execute the same fresh control-plane checks before the attempt-consumption marker. Failure before the marker leaves the D2-S4 attempt unconsumed.

Historical D2-S3 R2 evidence may be used only as predecessor provenance, not as D2-S4 attempt authorization.

## 4. Structural rebind

Because the client implementation changes, D2-S4 must materialize new successor identities for:

- client/preflight blob;
- runner blob;
- one-click blob;
- successor structural manifest;
- P1.5 final binding;
- predispatch attempt envelope;
- execution-config hash.

The official Codex/helper binaries do not change.

## 5. Zero-science qualification

Before any local D2-S4 model-bearing run, CI MUST prove:

### Queue behavior

1. one empty bounded poll becomes `TimeoutError`, not `queue.Empty`;
2. at least three consecutive empty polls do not terminate a synthetic turn wait;
3. a synthetic `turn/completed` arriving after >2 seconds is consumed successfully;
4. total synthetic deadline expiration returns timeout;
5. stdout EOF remains fatal;
6. unexpected server request remains fail-closed.

### Scientific dispatch

7. exactly one `turn/start` code path;
8. durable marker precedes transport write;
9. retry remains false;
10. timeout remains 90 seconds.

### Governance

11. D2-S3 formal close remains immutable;
12. new D2-S4 study/attempt IDs are used;
13. P1/P1.4/P1.5/P2/P3/P4 regressions PASS;
14. Windows PowerShell 5.1 parser/self-tests PASS;
15. no Codex/model turn occurs in CI.

## 6. Local execution

Only after one exact lock may a single local D2-S4 invocation be authorized.

The local root must be fresh:

`g2e/.local/P5A-D2S4-SCIENCE-001/`

No automatic retry is allowed after the D2-S4 marker is created.
