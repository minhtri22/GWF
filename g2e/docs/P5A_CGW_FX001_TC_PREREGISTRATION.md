# P5A-CGW P5-FX-001 Transport-Corrected Qualification — Preregistration

## Identity

- Study: `p5a-cgw-v4-p5-fx-001-transport-corrected-qualification`
- Attempt: `p5a-cgw-v4-p5-fx-001-tc-attempt-001`
- Route: `p5a-cgw`
- Model: `chatgpt-web/high` -> backend `gpt-5.6-sol`
- Connector: `Codex Native2`
- Outer execution authority: official Codex 0.153.4
- CGW source: v4.0.7 exact commit `b59d7dc51b84fb1f465ff1d00f5207f3b2b4a494`

This is a **new study and new attempt**. It is not a retry, rearm, replacement, or reinterpretation of
`p5a-cgw-v4-p5-fx-001-attempt-001`, which remains `INVALID — SPENT`.

## Scientific question

Can the alternative P5A-CGW route complete the frozen P5-FX-001 task while preserving:

1. outer Codex as the sole local executor;
2. exact bounded mutation;
3. a live Full-mode browser + MCP roundtrip;
4. complete attributable evidence;
5. correct task output;

when the harness no longer imposes the disproven 90-second absolute outer-turn deadline?

## Frozen task

Task, input, expected output, mutation scope, route, model, connector, and six metrics are unchanged
from the original P5-FX-001 qualification.

Frozen hashes:

- input: `a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6`
- task: `4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e`
- expected canonical result: `6dd3ebce33677409bec596309e061cc421bfa38b3160c5b577ffe5f7fbc9980d`
- count: `32`
- sum: `-6372402978`
- only allowed mutation: `result.json`
- network allowed by task: **no**

## Corrected transport contract

The qualified Full-mode upstream owns transport liveness.

- no scientific absolute outer-turn deadline;
- CGW browser turn has no absolute deadline by default;
- CGW bridge heartbeat: 2 s;
- CGW upstream-silence stall budget: 300 s;
- per-MCP invocation bound: 90 s;
- tunnel command-response bound: approximately 120 s;
- terminal scientific execution state is observed through exact app-server `turn/completed`.

An operator may still abort a pathological local process for safety/operations, but such an abort is
**infrastructure INVALID only** and can never assign scientific PASS or substantive FAIL.

## Signal separation

The verifier must not infer authority violation merely because route evidence is incomplete.

Frozen classes for this study:

```text
route invalidity
  -> evidence_integrity_failure

unexpected server request
  -> protocol_failure

prohibited tool / prohibited network activity
  -> scope_violation

positive evidence of execution outside outer Codex
  -> authority_violation
```

## Consumption

Exactly one live dispatch may eventually be authorized.

Consumption boundary remains:

`durable marker fsync immediately before the sole turn/start write`

- retry budget: 0
- same-attempt rearm: forbidden
- selective rerun: forbidden
- automatic retry: forbidden

No live dispatch is authorized by this preregistration.

## Required evidence

PASS requires all of:

- exact thread/turn attribution;
- browser send accepted;
- browser response visible;
- browser turn completed;
- live `Codex Native2` MCP tool invocation;
- correlation to outer Codex item execution;
- bridge did not perform local side effects;
- exact result;
- exact mutation scope;
- all six metrics = 1.

## Adjudication

### PASS

All six metrics equal 1 and mandatory route evidence is admitted.

### Substantive FAIL

Only a structurally valid, attributable, terminal-completed execution with at least one substantive
task metric equal to 0.

### INVALID

Infrastructure, protocol, evidence, scope, or authority failure; operator abort; nonterminal
execution; missing mandatory evidence; or missing metrics.

The verifier remains verdict-neutral.

## Current authorization

- implementation: authorized
- zero-model QA: authorized
- live dispatch: **withheld**

The next allowed action is bounded implementation of a new runner/verifier/one-click envelope plus
zero-model QA under this preregistration.
