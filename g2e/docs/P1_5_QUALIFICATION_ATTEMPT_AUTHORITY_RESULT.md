# G2E P1.5 — Qualification Attempt Authority Result

## Verdict

**PASS**

P1.5 qualifies a provider-neutral governance primitive for narrowly bounded qualification attempts without changing the meaning of capability availability.

**D2 execution remains NOT AUTHORIZED.**  
**No Codex model turn is authorized.**  
**Codex runtime adapter remains NOT AUTHORIZED.**

## Qualified candidate

- exact SHA: `6e9c518671c3f9ba140daa798458b37bee83647c`
- baseline: `53c7ac3d138968a2b96ece9ac58b95aef04511dc`
- implementation contract blob: `01c96bf9c40a499dd569f5b9e7e32696edcafaa0`
- schema blob: `8631f9af598103f6c095fa3981255b9bf4609f64`
- qualification test blob: `6799d4f524cf4c59301f8fb55532060590e3cdfb`
- workflow blob: `aec9ed777c426a44c67e5683bbf6054b2f2579a2`

## Exact workflow evidence

- workflow: `G2E P1.5 Qualification Attempt Authority Gate`
- run: `35607098718`
- job: `106356752615`
- conclusion: **PASS**
- artifact: `10642236550`
- artifact digest:
  `sha256:cbc71ccc50363860ee817d434f206d6655f5adb0299a07b116eeb064e6f00a12`

The authoritative workflow passed:

1. bounded provider-neutral implementation diff;
2. compile;
3. P1 regression;
4. P1.4 regression;
5. P1.5 qualification;
6. P2 regression;
7. P3 regression;
8. P4 regression;
9. provider-neutral / explicit qualification-path assertions;
10. machine-readable qualification report.

## Canonical primitive

P1.5 adds canonical:

`QualificationAuthorityGrant`

with schema kind:

`qualification_authority_grant`.

The grant is structurally constrained to:

- mode `QUALIFICATION_ONLY`;
- exact ProofObligation ref;
- exact AgentCapabilityManifest ref;
- one prospective attempt ID;
- exact target capability IDs;
- exact AuthorityPolicy ref;
- one explicit role;
- finite explicit authority scope;
- finite relative read/write paths;
- network forbidden;
- interactive approval forbidden;
- single attempt;
- cannot imply capability availability;
- cannot be reused for operational binding;
- explicit qualification lineage ref.

Grant target IDs and authority scope must be non-empty and unique. Read/write paths must be unique, relative and traversal-free.

## AgentBinding extension

P1.5 adds only:

```text
qualification_authority_ref: ExactRef | None = None
qualification_target_capability_ids: tuple[str, ...] = ()
```

Fail-closed invariants reject:

- grant ref without targets;
- targets without grant ref;
- duplicate targets;
- overlap between normal `required_capability_ids` and qualification targets.

Bindings using default values preserve normal P1.4 semantics.

## Normal P1.4 semantics preserved

`validate_agent_binding_identity()` was not weakened.

Normal bindings still require:

- every required capability to exist;
- required capability `available=true`;
- non-empty qualification refs;
- binding authority contained within manifest `max_authority_scope`.

The P1.5 qualification tests explicitly demonstrate that the same binding carrying grant-derived authority is still rejected by the normal P1.4 validator when that authority exceeds the manifest ceiling.

An unavailable capability supplied as a normal required capability is still rejected.

## Explicit qualification validator

P1.5 adds:

`validate_qualification_agent_binding_identity(...)`

It verifies:

- manifest availability;
- proof lifecycle FROZEN or AUTHORIZED;
- exact grant → proof ref;
- exact grant → manifest ref;
- exact grant → AuthorityPolicy ref;
- grant attempt ID;
- binding grant ref;
- exact qualification target equality;
- manifest / equivalence / binding / attempt refs;
- attempt proof ref;
- attempt AgentBinding ref;
- attempt authority exactly equals binding authority;
- app/provider/model/harness/transport identity consistency;
- normal required capabilities are already qualified;
- qualification targets exist and remain unavailable;
- normal prerequisites and qualification targets do not overlap;
- every granted action exists in AuthorityPolicy;
- the exact grant role is permitted for every action;
- binding authority is contained in manifest authority ∪ grant authority;
- any authority outside the manifest ceiling comes from the exact grant;
- optional exact read/write workspace path contract;
- result identity consistency when a result is supplied.

The validator performs no IO, dispatch, discovery, model execution, adjudication or secret resolution.

## Negative qualification evidence

P1.5 fixtures fail closed on:

- missing grant/target pairing;
- target overlap with normal prerequisites;
- duplicate target IDs;
- duplicate authority entries;
- absolute/traversal paths;
- network or interactive-approval enablement;
- wrong proof ref;
- wrong manifest ref;
- wrong AuthorityPolicy ref;
- wrong attempt ID;
- missing target capability;
- target capability already AVAILABLE;
- AuthorityPolicy missing a granted action;
- grant role not allowed by policy;
- authority beyond manifest + exact grant;
- attempt/binding authority mismatch;
- read/write path mismatch.

The tests also verify that a valid qualification grant does **not** mutate
`repository_read` or `repository_write` to AVAILABLE.

## D2-F01 disposition

**D2-F01 is resolved at the schema/governance prerequisite level.**

P1.5 now permits a future final D2 AgentBinding to distinguish:

```text
required_capability_ids
  = already-qualified prerequisites

qualification_target_capability_ids
  = unavailable capabilities intentionally under test

qualification_authority_ref
  = exact bounded authority to attempt them
```

This does not itself create the P5-FX-001 grant or final D2 binding.

## Scope integrity

P1.5 introduced no:

- Codex-specific source;
- ChatGPT-specific source;
- D2 model turn;
- D2 outcome evidence;
- Codex runtime adapter;
- operational capability self-qualification.

The implementation is provider-neutral.

## Authorization state

```text
P1.5 Qualification Attempt Authority   PASS
D2-F01 schema/governance blocker       RESOLVED
P5-FX-001 exact grant                  NOT YET MATERIALIZED
FINAL D2 AgentBinding                  NOT YET FROZEN
final zero-fresh admission             NOT YET QUALIFIED
D2 execution                           NOT AUTHORIZED
Codex model turn                       NOT AUTHORIZED
Codex runtime adapter                  NOT AUTHORIZED
```

## Next admissible frontier

The next scientific step is to materialize prospectively:

1. the exact P5-FX-001 AuthorityPolicy;
2. the exact P5-FX-001 QualificationAuthorityGrant;
3. the exact final D2 AgentBinding;
4. the exact ExecutionAttemptEnvelope pre-dispatch identity;

then run a **final zero-fresh admission qualification** using the P1.5 validator.

That phase must still execute no model turn.

Only if the final admission qualification PASSes may exactly one D2 model turn become authorized.
