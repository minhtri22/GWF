# G2E P5A D2 — Final Admission Qualification Result

## Verdict

**FINAL_ADMISSION_PASS**

The complete prospective P5-FX-001 pre-dispatch identity and authority graph materialized deterministically and passed independent zero-fresh verification under P1.5.

No Codex model turn occurred in this phase.

## Qualified candidate

- exact SHA: `75e10b5a68616c2f48bf1b091a850daa8b0da60d`
- baseline: `926d6a46344e8ac4822907fdc6b597f8d6ba6feb`
- specification blob: `6b00c9ddec549e59d7d0234da0d27b782608d990`
- builder blob: `a8ae87414a3c69333d13600b6d3d7ebb506a138b`
- qualification test blob: `130568e3e619a868b3d87e348a2ff36a057b19f9`
- workflow blob: `99f5d61d440c33ed652b6d1d21d2d7940b6ce1e2`

## Exact workflow evidence

- workflow: `G2E P5A D2 Final Zero-Fresh Admission`
- run: `35608071469`
- job: `106359996540`
- conclusion: **PASS**
- artifact: `10642813459`
- artifact digest:
  `sha256:f2bdebc1f5f272c9465bf9961375bbbd2086b1ab23304a480fa87a95c6ff26f3`

All steps passed:

1. bounded zero-fresh diff;
2. compile;
3. P1 regression;
4. P1.4 regression;
5. P1.5 regression;
6. P2 regression;
7. P3 regression;
8. P4 regression;
9. final-admission qualification;
10. exact graph materialization;
11. independent re-verification of the materialized pack;
12. machine-readable report;
13. artifact upload.

## Exact final graph

### AuthorityPolicy

```text
object_id    p5a-d2-p5-fx-001-authority-policy
revision_id  p5-fx-001-v1
content_hash 8bf59660f19437120d2b26169b0bf7dc7670a5e075e0252ac951c8ad0aa20971
```

It authorizes exactly:

- `READ_FROZEN_FIXTURE` for `qualification_executor`;
- `WRITE_DESIGNATED_OUTPUT` for `qualification_executor`.

### QualificationAuthorityGrant

```text
object_id    p5a-d2-p5-fx-001-qualification-grant
revision_id  p5-fx-001-v1
content_hash 656cb4c2e06518ecf7d2da668b03d4f6084ebd2ed2bc03cd3289d3639efdafab
```

It binds exactly:

- target capabilities `repository_read`, `repository_write`;
- attempt `p5a-d2-p5-fx-001-attempt-001`;
- reads `input.json`, `TASK.md`;
- write `result.json`;
- network false;
- interactive approval false;
- one non-operational qualification attempt only.

### FINAL D2 AgentBinding

```text
object_id    p5a-d2-final-agent-binding
revision_id  p5-fx-001-v1
content_hash 472eb3a0573c093a8b7cb63b1dc320b4292f1c30b6d6dfd493f29014472999e1
```

It retains already-qualified structural prerequisites in
`required_capability_ids`, and keeps `repository_read/write` only in
`qualification_target_capability_ids`.

### Pre-dispatch ExecutionAttemptEnvelope

```text
object_id    p5a-d2-predispatch-attempt-envelope
revision_id  p5-fx-001-v1
content_hash 34369e7eacd0ad03a3ca4433c2ad0d643de9a1057ed7bcbc1729d10e33511ea3
attempt_id   p5a-d2-p5-fx-001-attempt-001
state        LOCKED
```

Its authority scope exactly equals the FINAL AgentBinding authority scope.

## Exact execution configuration

Frozen config hash:

`740d5303d29b757e47571bc50b6367770296f7186a5528cef25adbb806669c3a`

The config binds the exact:

- P5-FX-001 input SHA-256;
- TASK.md SHA-256;
- Codex executable SHA-256;
- ProofObligation;
- D1 manifest;
- AuthorityPolicy;
- QualificationAuthorityGrant;
- FINAL AgentBinding;
- workspace inventory;
- only permitted output addition;
- authority scope;
- read/write paths;
- network/approval policy;
- timeouts;
- zero retry budget.

Any execution drift is a different attempt and is not authorized by this admission.

## Materialized artifact file hashes

```text
P5A_D2_AUTHORITY_POLICY.json
984027e5911c37b5e0b7a9788d836558d0525dbb3b070ce33687788eb4b68e49

P5A_D2_QUALIFICATION_AUTHORITY_GRANT.json
420415c832531c0e59960acd81409857545ae4aeed35c21d3682fbb5bb938f82

P5A_D2_FINAL_AGENT_BINDING.json
03eb1bb5502fb4418f1d88695779bbb9535aa0f4ff0f84e73771c10a524a66bb

P5A_D2_PREDISPATCH_ATTEMPT.json
115ce76ac31139f42be264ae52b0928321ea718f8080d3da1f85e59547ec8e9a

P5A_D2_FINAL_ADMISSION.json
d505bbb2c68ddff8ddbc2246ed0d1d8891fa01d976adfa575c0f7270535463ba
```

## Independent verification

The qualification did not rely only on the materializer accepting its own output.

The emitted final-admission JSON was reparsed from disk and independently passed:

- exact ref reconstruction;
- exact inherited ProofObligation / manifest identities;
- P1.5 qualification validator;
- target capability unavailability checks;
- exact authority/action/role checks;
- exact read/write path checks;
- attempt/binding authority equality;
- harness/provider/model/transport identity checks;
- execution config hash recomputation;
- zero retry;
- network false;
- interactive approval false;
- no outcome/model-turn freshness checks.

Negative fixtures reject drift in proof, manifest, policy, grant, attempt, targets, authority, paths, fixture/task hashes, network/approval and harness identity.

## Capability state remains unchanged

Before D2:

```text
repository_read.available  = false
repository_write.available = false
```

The qualification grant and FINAL AgentBinding do not change these values.

## Authorization state

```text
P1.5                                 PASS
P5A D2 FINAL zero-fresh admission    PASS
FINAL D2 AgentBinding                FROZEN
pre-dispatch attempt                 LOCKED
fresh D2 outcome                     NONE
Codex model turn executed            NO
scientific D2 attempts authorized    EXACTLY ONE
retry authorization                  NONE
Codex runtime adapter                NOT AUTHORIZED
```

## Next admissible frontier

The governance prerequisite chain is now complete.

The next scientific step is **one and only one execution of the exact frozen P5-FX-001 D2 attempt** under the materialized final admission pack.

That execution must use:

- attempt ID `p5a-d2-p5-fx-001-attempt-001`;
- exact config hash `740d5303d29b757e47571bc50b6367770296f7186a5528cef25adbb806669c3a`;
- exact harness identity;
- exact prompt/input/workspace;
- exact bounded read/write authority;
- no network;
- no interactive approval;
- zero retry;
- frozen timeouts and adjudication rules.

No runtime adapter is authorized by this PASS.
