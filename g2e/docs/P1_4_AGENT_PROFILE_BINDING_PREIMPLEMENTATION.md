# G2E P1.4 — Agent Profile / Binding Identity Pre-Implementation Qualification

**Status:** FROZEN CANDIDATE FOR ZERO-IMPLEMENTATION QA  
**Scope:** schema-only prerequisite for P5  
**Baseline:** `bfd7e29513ef22f569f931ab75f9d29fd5ec89f6`  
**Codex/ChatGPT runtime adapters:** PROHIBITED

## 1. Origin

P5 pre-implementation qualification at candidate `a799a6039498dfd4196b9874f230da48fdbb42c1` produced:

```text
SPEC_PASS_RUNTIME_BLOCKED
blocking prerequisite = P1.4_AGENT_PROFILE_BINDING_IDENTITY
findings = P5-F01, P5-F02
```

Exact evidence:

- P5 workflow `35587111264`, job `106292892218` — PASS;
- P5 evidence artifact `10632522432`;
- P5 evidence closure `6283bf4c033828b2915bf3029ed9b3e0ea9d0870`.

P1.4 is a bounded schema prerequisite. It is not a rescue of P5 runtime code and it does not qualify Codex or ChatGPT.

## 2. Scientific / semantic question

> Can G2E represent agent-app capability discovery and one prospectively resolved execution binding as canonical, attributable identity without conflating agent apps with runtime backends, weakening attempt identity, or introducing provider-specific semantics?

P1.4 passes only if the answer is demonstrated by canonical schema fixtures plus P1–P4 regressions.

## 3. Existing primitives to preserve

The following remain unchanged in meaning:

- `RuntimeCapabilityManifest` = execution backend capability (`STANDALONE | GWF`);
- `ExecutionAttemptEnvelope` = one attempt of one frozen ProofObligation;
- `ExecutionResult` = provider-neutral terminal executor result;
- `IndependencePolicy` = prospective independence requirements;
- `AuthorityPolicy` = normative authority constraints;
- P2 Adjudication remains sole scientific/substantive verdict authority;
- P3 standalone and P4 GWF execution remain valid for non-agent execution.

P1.4 MUST NOT reinterpret `RuntimeCapabilityManifest` as an agent-app profile.

## 4. New canonical schema surface

### 4.1 AgentProfileAvailability

Frozen values:

```text
AVAILABLE
UNAVAILABLE
UNQUALIFIED
```

`UNQUALIFIED` means capability/availability has not been demonstrated by exact discovery evidence. It must never be silently treated as AVAILABLE.

### 4.2 BindingMode

Frozen values:

```text
DYNAMIC
FROZEN
```

- `DYNAMIC`: policy may resolve a compatible executor for a future attempt.
- `FROZEN`: policy-declared material identity dimensions are fixed until governed amendment.

A resolved binding is immutable within its bound attempt in both modes.

### 4.3 AgentCapability

Strict descriptive record:

- `capability_id`;
- `available`;
- `qualification_refs`;
- `limitations`.

If `available=true`, at least one qualification ref is required.

Capabilities are descriptive, never quality scores.

### 4.4 AgentCapabilityManifest

Canonical schema kind:

`agent_capability_manifest`

Required identity:

- `agent_app`;
- `profile_version`;
- `harness_ref`;
- optional exact harness revision;
- optional `provider_ref`;
- optional `model_ref`;
- optional `transport_ref`;
- availability;
- descriptive capability records;
- execution constraints;
- maximum authority scope;
- opaque credential-reference classes;
- external-session attribution support;
- interruption/cancellation support;
- artifact/evidence extraction support;
- structured-output support;
- status/progress normalization support;
- discovery evidence refs;
- limitations.

Rules:

1. capability IDs unique;
2. `AVAILABLE` requires exact discovery evidence refs;
3. no app/provider-specific field names beyond generic identity strings;
4. secrets are not represented as values; only opaque credential-reference classes may be declared;
5. manifest identity belongs to the app/harness profile, not runtime backend identity.

### 4.5 AgentEquivalencePolicy

Canonical schema kind:

`agent_equivalence_policy`

Required fields:

- `material_dimensions`;
- `allowed_substitution_dimensions`;
- `substitution_requires_new_attempt=true`;
- `prospective=true`.

Rules:

- dimensions are unique;
- allowed substitution dimensions may not include an undeclared material dimension unless explicitly present in the policy;
- no outcome-conditioned field exists;
- policy is frozen before attempt dispatch.

### 4.6 AgentBinding

Canonical schema kind:

`agent_binding`

Required identity:

- `resolved_attempt_id`;
- `agent_app`;
- exact `capability_manifest_ref`;
- exact `equivalence_policy_ref`;
- `binding_mode`;
- app/provider/model/harness/transport identities;
- required capability IDs;
- execution constraints;
- granted authority scope;
- resolution timestamp/identity metadata.

Rules:

1. binding is resolved before dispatch;
2. `resolved_attempt_id` binds it to one attempt identity;
3. binding contains no outcome/verdict;
4. required capabilities are validated against the exact manifest;
5. granted authority must be a subset of manifest maximum authority;
6. identity copied from manifest may not conflict;
7. a material substitution requires a new attempt or governed amendment according to frozen equivalence policy.

## 5. Existing execution schema extension

### ExecutionAttemptEnvelope

Add:

`agent_binding_ref: ExactRef | None`

Compatibility rule:

- non-agent attempts may omit it and retain all P1–P4 semantics;
- if any of `agent_app/provider_ref/model_ref/harness_ref/transport_ref` is populated, `agent_binding_ref` is mandatory;
- if `agent_binding_ref` is populated, `agent_app` and `harness_ref` are mandatory.

### ExecutionResult

Add:

`agent_binding_ref: ExactRef | None`

Compatibility rule:

- non-agent results may omit it;
- if any agent identity field is populated, binding ref is mandatory;
- if binding ref is populated, `agent_app` and `harness_ref` are mandatory.

P3/P4 result construction must preserve the binding ref when present; this is propagation only, not a runtime adapter.

## 6. Deterministic relation validator

P1.4 may add one pure validation helper with no IO and no provider behavior:

`validate_agent_binding_identity(manifest, equivalence_policy, binding, attempt, result=None)`

It MUST verify:

1. `binding.capability_manifest_ref == manifest.exact_ref()`;
2. `binding.equivalence_policy_ref == equivalence_policy.exact_ref()`;
3. `binding.resolved_attempt_id == attempt.attempt_id`;
4. `attempt.agent_binding_ref == binding.exact_ref()`;
5. app/provider/model/harness/transport identity consistency across manifest → binding → attempt;
6. required binding capabilities exist and are AVAILABLE with qualification refs;
7. granted authority is a subset of manifest maximum authority;
8. result, when supplied, references the same binding and attempt and carries consistent copied identity;
9. no executor status is interpreted as Adjudication.

The helper returns normally on valid identity and raises `ValueError` on mismatch. It performs no discovery, dispatch, network access, secret resolution, retry, or adjudication.

## 7. Fail-closed fixtures

P1.4 qualification must include positive and negative fixtures for:

- canonical AgentCapabilityManifest hash/ref;
- AVAILABLE without discovery evidence → reject;
- available capability without qualification ref → reject;
- duplicate capability IDs → reject;
- canonical AgentEquivalencePolicy;
- duplicate/invalid policy dimensions → reject;
- canonical AgentBinding;
- agent attempt without binding ref → reject;
- binding ref without app/harness → reject;
- binding manifest-ref mismatch → reject;
- binding equivalence-ref mismatch → reject;
- resolved attempt ID mismatch → reject;
- app/provider/model/harness/transport mismatch → reject;
- required unavailable/missing capability → reject;
- authority escalation beyond manifest ceiling → reject;
- result binding/attempt/identity mismatch → reject;
- non-agent P1/P2/P3/P4 fixtures remain valid;
- executor COMPLETED remains non-scientific.

## 8. No provider-specific implementation

P1.4 MUST NOT add:

- Codex classes/drivers/commands;
- ChatGPT classes/drivers/commands;
- provider API calls;
- MCP server/client;
- ARC transport;
- GWF agent registry persistence;
- harness session creation;
- profile discovery implementation;
- secret/credential resolution;
- P4L/GAC/Reference Acquisition behavior.

Schema values may later contain `agent_app="codex"` or `agent_app="chatgpt"`, but no P1.4 code may branch on either value.

## 9. Pre-implementation gate

Zero-implementation qualification must prove:

```text
P1.4-Q0 exact P5 blocker/evidence bound
P1.4-Q1 reuse inventory frozen
P1.4-Q2 new schema surface minimal
P1.4-Q3 backward compatibility rule frozen
P1.4-Q4 relation validator contract frozen
P1.4-Q5 negative fixtures frozen
P1.4-Q6 provider-neutral scope frozen
P1.4-Q7 no runtime adapter code
P1.4-Q8 P1–P4 regressions PASS
```

Only after exact-SHA zero-implementation QA PASS may schema implementation begin.

## 10. Implementation authorization after spec PASS

If the pre-implementation gate passes, implementation is bounded to:

- `src/g2e/schemas.py`;
- P3/P4 provider-neutral binding-ref propagation only if required;
- P1.4 tests;
- existing P1–P4 regression-compatible adjustments;
- P1.4 workflow/evidence/result docs.

No Codex/ChatGPT runtime adapter is authorized.

## 11. Schema implementation exit gate

P1.4 may PASS only when an exact implementation SHA demonstrates:

1. all frozen P1.4 schema fixtures PASS;
2. P1 regression PASS;
3. P2 regression PASS;
4. P3 regression PASS;
5. P4 regression PASS;
6. no provider-specific runtime file exists;
7. no P4L/GAC/RA implementation opened;
8. exact implementation/evidence artifacts recorded;
9. evidence closure contains no post-qualification implementation mutation.

Only then may the frontier move to P5A actual-harness discovery/implementation.
