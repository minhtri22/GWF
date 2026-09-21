# G2E P5A D2 — Qualification Authority Admission Pre-Implementation Result

## Verdict

**SPEC_PASS_IMPLEMENTATION_REQUIRED**

The qualification-authority admission semantics are sufficiently frozen to resolve D2-F01 prospectively, but a bounded schema/governance prerequisite is required before D2 can execute.

**D2 execution remains NOT AUTHORIZED.**  
**No Codex model turn is authorized.**  
**Codex runtime adapter remains NOT AUTHORIZED.**

## Qualified candidate

- exact SHA: `e771faccb8b4370e6720d34f9905c2504846f96f`
- baseline: `11c04f7c7be88ebfd40ea6755a8bfc633262048d`
- specification blob: `dfaed0e1fcabf23d1cd3d2b4b5978dc9190eef68`
- qualification test blob: `7d3f0df49527b52a7941a3e4188aa0666e127d89`
- workflow blob: `58bc9d797b627e77ccda7d3cc2783fe02e6f5728`

## Exact workflow evidence

- workflow: `G2E P5A D2 Qualification Authority Preimplementation`
- run: `35603911135`
- job: `106346284252`
- conclusion: **PASS**
- artifact: `10641056299`
- artifact digest:
  `sha256:c3fadfc2a42f75f9d252ec13b48877bc064276b2f52ef08e9167c2f489b9e740`

The machine-readable report records:

```text
adjudication = SPEC_PASS_IMPLEMENTATION_REQUIRED
blocking_finding = D2-F01
next_prerequisite = P1.5_QUALIFICATION_ATTEMPT_AUTHORITY
model_turn_authorized = false
d2_execution_authorized = false
runtime_adapter_authorized = false
fresh_d2_outcome_consumed = false
```

## Scientific decision

The framework now freezes the distinction:

```text
authority to ATTEMPT an unqualified capability
        ≠
evidence that the capability is AVAILABLE
```

A qualification attempt may receive an exact, bounded governance permit to create evidence about an unavailable capability.

That permit is not itself evidence and cannot mutate the capability manifest.

## Frozen future primitive

The bounded implementation prerequisite must introduce canonical:

`QualificationAuthorityGrant`

with schema kind:

`qualification_authority_grant`.

The grant is:

- `QUALIFICATION_ONLY`;
- exact-ProofObligation bound;
- exact-attempt bound;
- exact-capability-manifest bound;
- exact-target-capability bound;
- exact-AuthorityPolicy bound;
- finite authority-scope bound;
- finite read/write-path bound;
- single-attempt;
- non-transferable;
- non-operational;
- incapable of implying capability availability.

For P5-FX-001 the frozen target is exactly:

```text
target capabilities:
  repository_read
  repository_write

authority:
  READ_FROZEN_FIXTURE
  WRITE_DESIGNATED_OUTPUT

read paths:
  input.json
  TASK.md

write path:
  result.json

network:
  false

interactive approval:
  false
```

## Preserved P1.4 semantics

Normal AgentBinding behavior remains unchanged.

Normal bindings still require:

- every `required_capability_id` AVAILABLE with evidence;
- ordinary authority scope within the manifest operational authority ceiling.

Qualification bindings must be explicit and separate.

The future AgentBinding extension is frozen as:

```text
qualification_authority_ref: ExactRef | None = None
qualification_target_capability_ids: tuple[str, ...] = ()
```

For a qualification binding:

- `required_capability_ids` contains only already-qualified structural prerequisites;
- `qualification_target_capability_ids` contains unavailable capabilities intentionally under test;
- the exact qualification grant supplies only bounded attempt authority.

## Authority semantics

For normal binding:

```text
binding.authority_scope
    ⊆
manifest.max_authority_scope
```

For qualification binding:

```text
binding.authority_scope
    ⊆
manifest.max_authority_scope
      ∪
qualification_grant.granted_authority_scope
```

but every authority element outside the manifest ceiling must be authorized by the exact parent AuthorityPolicy and bound to the same proof, attempt, manifest and qualification target.

This does not change the manifest authority ceiling.

## PRD-14 preservation

The zero-fresh qualification explicitly preserves:

```text
delegated authority ≤ parent authority
```

The parent normative authority for the experimental attempt is the exact canonical AuthorityPolicy, not the descriptive capability manifest.

The P5-FX-001 future policy may authorize only the role:

`qualification_executor`

for:

- `READ_FROZEN_FIXTURE`;
- `WRITE_DESIGNATED_OUTPUT`.

No generic repository, shell, network, credential or approval-bypass authority is admitted.

## Capability-state transition remains post-evidence

Even a future D2 PASS cannot mutate the existing D1 manifest in place.

The frozen sequence is:

```text
D2 admitted evidence
        ↓
D2 Adjudication PASS
        ↓
separate manifest revision proposal
        ↓
qualification_refs bind exact D2 evidence
        ↓
new AgentCapabilityManifest revision
```

D2 FAIL or INVALID leaves target capabilities unavailable.

## Zero-fresh integrity

The authoritative workflow proved:

- specification-only diff;
- no `src/g2e`, `src/gwr` or `scripts/g2e` mutation;
- no tracked D2 result/adjudication/outcome artifact;
- current P1.4 schema still has no hidden qualification-authority fields;
- D2-F01 remains reproducible from the exact qualified Codex manifest;
- P1 regression PASS;
- P1.4 regression PASS;
- P2 regression PASS;
- P3 regression PASS;
- P4 regression PASS;
- qualification-authority semantic QA PASS.

## Implementation boundary

This phase did not add:

- QualificationAuthorityGrant runtime/schema implementation;
- AgentBinding schema changes;
- a D2 execution binding;
- a Codex runtime adapter;
- a model turn;
- D2 outcome evidence;
- ChatGPT P5B work.

## Next admissible frontier

The next step is:

**P1.5 — Qualification Attempt Authority**

This is a bounded provider-neutral schema/governance implementation.

It must implement:

1. canonical `QualificationAuthorityGrant`;
2. optional qualification fields on AgentBinding;
3. explicit qualification-binding validator;
4. preservation of normal P1.4 validation;
5. exact P5-FX-001 grant fixtures;
6. P1/P1.4/P2/P3/P4 regressions;
7. no model turn and no Codex runtime adapter.

Only after P1.5 PASS may the exact P5-FX-001 QualificationAuthorityGrant and final D2 AgentBinding be materialized and subjected to a final zero-fresh admission check.

Only after that final admission PASS may one D2 model turn be authorized.
