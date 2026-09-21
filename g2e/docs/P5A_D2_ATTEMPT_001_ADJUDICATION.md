# G2E P5A D2 — Attempt 001 Adjudication

**Attempt:** `p5a-d2-p5-fx-001-attempt-001`  
**Frozen execution config:** `740d5303d29b757e47571bc50b6367770296f7186a5528cef25adbb806669c3a`  
**Qualified harness SHA-256:** `a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8`  
**Runner SHA-256:** `f9ef2699f4ff77f43cad9316cb9cce5e496d832f72f9eb210ccfc5bcedca0171`  
**Verdict:** `INVALID`  
**Replacement attempt under current contract:** `NOT AUTHORIZED`

## 1. Evidence frozen

The one-shot execution produced the following immutable evidence identities:

- runner evidence SHA-256: `270d41e9d15265ad979250dcc0fb69faa1315e65b26586849ad815455d730617`;
- sanitized protocol SHA-256: `7cb3a00f9fb2bc2893d637e638cab2c54eef64a592120d5dd56f70b14220dc9f`;
- `TURN_START_SENT.marker` SHA-256: `80ee313731b33fa05d8cba7d38e4f4585424e25da4a20c9e7ecebf974fe2075d`;
- independent verification result SHA-256: `7e548a350c6fe910ad0fd3bceb4d3e6a456e6bda6c528f433bedbde299b659eb`.

The marker binds:

```text
attempt_id = p5a-d2-p5-fx-001-attempt-001
execution_config_hash = 740d5303d29b757e47571bc50b6367770296f7186a5528cef25adbb806669c3a
```

## 2. Attempt consumption

The frozen D2 rule defines the scientific attempt as begun when `turn/start` is sent.

Observed evidence establishes:

```text
turn_start_request_sent = true
turn_start_accepted = false
turn_id = null
TURN_START_SENT.marker = present
```

Therefore the single authorized D2 scientific attempt is **consumed**.

This conclusion does not depend on whether the server accepted the request or whether model inference began.

## 3. Pre-turn identity and isolation checks

Before `turn/start`, all bounded execution prerequisites that the runner was required to attest were clean:

- exact source HEAD `6938072806d61e6920a86abece79406630653f3c`;
- source worktree clean;
- exact input and TASK hashes;
- exact qualified admission pack hashes;
- exact Codex executable SHA-256;
- exact frozen execution config hash;
- configured MCP count = 0;
- installed app count = 0;
- callable/enabled app count = 0;
- authentication ready;
- instruction sources empty;
- exact thread attribution present;
- no command execution, MCP tool call, web search, approval request, or unexpected workspace mutation.

These observations support attribution and evidence integrity. They do **not** establish D2 functional capability.

## 4. Terminal mechanism

The sanitized protocol contains one `thread/started` notification followed by the response to request id `6` (`turn/start`):

```text
JSON-RPC error code = -32600
```

The runner evidence records the protocol rejection:

```text
Invalid request: workspaceWrite.readOnlyAccess is no longer supported;
use permissionProfile for restricted reads
```

Thus the request was rejected during App Server protocol validation before a task turn was accepted.

No `result.json` was created. `input.json` and `TASK.md` remained unchanged and no unexpected workspace entry appeared.

## 5. Independent verifier

`p5a_d2_attempt_001_verify.py` independently checks the exact attempt identity, frozen hashes, isolation state, marker, sanitized protocol, workspace state, and rejection mechanism.

All verifier checks PASS.

Observed frozen metrics are:

```text
executor_completed          = unobservable
result_schema_valid         = unobservable
result_values_correct       = unobservable
mutation_scope_valid        = 1
attempt_attribution_valid   = 1
evidence_integrity_valid    = 1
```

The first three metrics are not converted to zero because the task was not admitted for execution; treating them as substantive failures would incorrectly turn an infrastructure/protocol invalidity into a functional FAIL.

## 6. Adjudication

The frozen P5-FX-001 adjudication contract explicitly classifies these conditions as `INVALID`:

- executor infrastructure failure;
- missing result due infrastructure/protocol failure;
- inability to observe required task metrics because execution never became admissible.

The present evidence satisfies that INVALID path and does not satisfy the FAIL path, because no substantive frozen task metric was observed as zero after a structurally valid task execution.

Therefore:

```text
P5A D2 attempt 001 = INVALID
```

This INVALID result makes **no scientific claim** that Codex does or does not possess `repository_read` or `repository_write` capability for P5-FX-001.

## 7. No retry / no rescue

The frozen retry policy is:

```text
max_invalid_replacement_attempts = 0
```

Accordingly:

- do not rerun attempt `p5a-d2-p5-fx-001-attempt-001`;
- do not repair the runner and reuse the frozen attempt/config;
- do not change the prompt, fixture, timeout, authority, model/provider, or protocol and call it the same D2 attempt;
- do not update the Codex capability manifest from this INVALID result;
- `repository_read` and `repository_write` remain unavailable in the D1 manifest;
- Codex runtime adapter remains unauthorized;
- P5A functional qualification is not established.

A future functional qualification, if scientifically desired, requires a **new preregistered successor study** with a new attempt identity and a prospectively frozen protocol contract. It is not a replacement attempt for D2 attempt 001.

## 8. Lineage handling

No `LINEAGE.md` entry is added by this closure because the observed event is a protocol/infrastructure invalidity and yields no new scientific capability result. The detailed evidence and adjudication are preserved here instead.
