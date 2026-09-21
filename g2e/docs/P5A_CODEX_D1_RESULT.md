# G2E P5A — Codex D1 Actual-Harness Result

## Verdict

**PASS — D1 STRUCTURAL ACTUAL-HARNESS QUALIFIED**

The original one-shot Codex discovery is admitted after the separately qualified P5A.1R invalidity repair and repaired one-shot adjudication.

This result qualifies only the observed D1 structural surface. It does not qualify functional task execution, does not authorize D2, and does not authorize a Codex runtime adapter.

## Immutable evidence chain

- original discovery SHA-256: `ba098a56be39e996488e5a543af8c373199f8b4cc66f922be6d7bc6386c6e860`
- original parent adjudication verdict: `INVALID`
- original parent reason: `INVENTORY_PATHS_NOT_SORTED`
- qualified invalidity-repair candidate: `4e447ef19a843aa3dd1337c57a9c70b4c1a00de1`
- repaired adjudicator git blob: `b2ba81801d2bfe7a662acb477fa449e16d13fa55`
- repaired adjudicator local-source SHA-256 recorded by the result: `6d31911576ec39cf927294996e4335279fafb10217b307a56afeb50a70955860`
- repaired adjudication file SHA-256: `04035432c5f290dfd7bbcc91feba8865dc86bfae11686a4e44da2f56cb4ac578`
- repaired adjudication verdict: `PASS`
- repaired reason codes: empty

The repaired adjudication references the same original discovery SHA-256. No Codex discovery recollection was used.

## Qualified harness identity

The actual harness evidence records:

- reported CLI version string: `codex-cli 0.0.0`
- executable SHA-256: `a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8`
- initialize handshake: PASS
- schema inventory digest: `4da66f2fac241c53ec857bf1a5f0f9586a445e39c4b0c4e7b4bdb0b103aa8376`
- recomputed schema inventory digest: exact match
- discovery errors: none
- functional task executed: false
- secrets persisted: false.

The reported version string is retained exactly as evidence and is not rewritten from filesystem naming or external release information. Exact harness identity therefore relies on the executable SHA-256 plus discovery/schema fingerprints.

## D1 required structural surface

All frozen required protocol tokens are observed:

```text
initialize      true
thread/start    true
thread/resume   true
turn/start      true
item/started    true
item/completed  true
```

The initialize handshake is successful.

## D1 optional observed structural surface

The original discovery additionally observes these optional schema/protocol tokens as present:

```text
command/exec      true
mcpServer         true
requestApproval   true
sessionId         true
skill             true
thread/fork       true
turn/steer        true
```

These observations qualify only that a structural surface is present in the exact generated schema/protocol bundle. They do not establish that any corresponding functional operation succeeds.

## Capabilities still unqualified

D1 does not qualify:

- repository read;
- repository write;
- shell execution;
- test execution;
- network access;
- side-effect approval execution;
- active-task cancellation/interruption semantics;
- completed-task artifact/evidence extraction;
- model/task correctness.

These remain unavailable for scientific proof admission until D2 or a separately preregistered functional probe.

## Authorization state

```text
Codex D1 structural profile surface  QUALIFIED
Codex AgentCapabilityManifest        NOT YET MATERIALIZED
D2 P5-FX-001                         NOT AUTHORIZED
Codex runtime adapter                NOT AUTHORIZED
ChatGPT P5B                          UNTOUCHED
```

## Next admissible step

Materialize one exact canonical Codex `AgentCapabilityManifest` from D1-qualified structural evidence only, then independently qualify that manifest against P1.4 schema and the immutable D1 evidence chain.

No D2 execution may begin until the exact manifest is qualified.