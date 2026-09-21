# G2E P5A D2 — P5-FX-001 Pre-Implementation Qualification Result

## Verdict

**SPEC_PASS_EXECUTION_BLOCKED**

The P5A D2 / P5-FX-001 specification and zero-fresh qualification PASS.

**No model turn is authorized.**  
**D2 execution remains NOT AUTHORIZED.**  
**Codex runtime adapter remains NOT AUTHORIZED.**

The only execution blocker is the prospectively identified admission finding **D2-F01**.

## Qualified candidate

- exact SHA: `15eeae4776a969cb0d64b9d55f33146e303161ec`
- baseline: `3d2206ad06a84bb78ee81983dfa06f8cae2cf002`
- specification blob: `401762a3edb0c9fd81b25d9428bf7d49926d2ad5`
- preregistration builder blob: `e25cf943091571c4b7f8b6a3413aaeb2bc6e1e8a`
- qualification test blob: `c8c238446f87c0b7e3d1ea376ce439ba88db5112`
- workflow blob: `93c536d44bb32e20750774f4fc0ae67d378f3238`

## Exact workflow evidence

- workflow: `G2E P5A D2 P5-FX-001 Preimplementation`
- run: `35603125876`
- job: `106343728888`
- conclusion: **PASS**
- artifact: `10639439364`
- artifact digest: `sha256:ff7d2ef4592e734767bcb297b51c8b06d7b037d80968beeeb35956bc3d8559ef`

The artifact contains:

- `P5A_D2_P5_FX_001_PREREGISTRATION.json`
- `p5a_d2_preimplementation_report.json`

Preregistration file SHA-256:

`eaeff7a8141697b2ecb824709277ba51db5e60643a722f2d06b3d5d3f6d4d4b4`

## Frozen fixture identities

P5-FX-001 input SHA-256:

`a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6`

TASK.md SHA-256:

`4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e`

Exact ProofObligation ref:

```text
object_id    p5a-d2-p5-fx-001-proof
revision_id  p5-fx-001-v1
content_hash 8e275db790fe4c83061385f9988f4165f54d514611a44a4a555c5d01f6d3dbcd
```

Exact preflight identity AgentBinding ref:

```text
object_id    p5a-d2-preflight-binding
revision_id  p5-fx-001-v1
content_hash a5a9287d464d3d3450e9cf82d7866d45e9e2fc2921b0c28d938fd7257a3940f8
```

The preflight binding freezes exact Codex/harness/manifest/equivalence identity with no substitution and empty authority. It is intentionally **not** D2 dispatch authorization.

## Frozen D2 contract

The zero-fresh candidate freezes:

- deterministic 32-integer P5-FX-001 input;
- exact prompt/task bytes;
- isolated pre-workspace containing only `input.json` and `TASK.md`;
- exactly one permitted post-execution addition: `result.json`;
- no network;
- no repository access;
- no external side effects;
- no interactive approvals;
- exact ProofObligation and DecisionRule;
- exact EvidenceAdmissionPolicy;
- zero-retry ProofRetryPolicy;
- no-rescue AmendmentPolicy;
- exact AgentEquivalencePolicy;
- exact preflight identity AgentBinding;
- startup timeout 12 s;
- model-turn timeout 90 s;
- verifier timeout 10 s;
- evidence extraction/attribution contract;
- PASS/FAIL/INVALID rules;
- no hidden reasoning requirement;
- no rerun-until-PASS.

P1, P1.4, P2, P3 and P4 regressions all PASS inside the same authoritative workflow.

## D2-F01 — confirmed qualification-authority admission blocker

The exact qualified Codex D1 AgentCapabilityManifest intentionally has:

```text
repository_read  = unavailable
repository_write = unavailable
shell_execution  = unavailable
...
max_authority_scope = ()
```

The frozen D2 fixture requires prospective execution authority:

```text
READ_FROZEN_FIXTURE
WRITE_DESIGNATED_OUTPUT
```

P1.4 binding validation requires:

1. required prerequisite capabilities to be qualified/available; and
2. AgentBinding authority scope to be a subset of the manifest maximum authority scope.

Therefore:

```text
required D2 authority
        ⊄
qualified manifest max_authority_scope ()
```

and the final D2 execution AgentBinding cannot currently be frozen without violating already-qualified P1.4 semantics.

The machine-readable preregistration correctly records:

```text
execution_admission.authorized = false
execution_admission.reason = D2-F01
final_execution_agent_binding_frozen = false
model_turn_authorized = false
runtime_adapter_authorized = false
```

## Scientific interpretation

D2-F01 is **not evidence that Codex lacks repository/file-write capability**.

It is an admission-model issue discovered prospectively:

```text
functional capability is unqualified
        ↓
D2 is needed to test it
        ↓
D2 must receive bounded authority to attempt it
        ↓
the exact D1 profile has zero authority ceiling
        ↓
current P1.4 validation correctly blocks dispatch
```

Bypassing this with unrecorded workspace authority, omitting write authority from the binding, or marking repository_write available before D2 would invalidate the qualification.

## Scope integrity

This phase introduced no:

- model turn;
- Codex task execution;
- Codex runtime adapter;
- `src/g2e` mutation;
- `src/gwr` mutation;
- D2 outcome evidence;
- ChatGPT P5B work.

## Next admissible frontier

The next step is **not D2 execution**.

It is a bounded, prospective **D2 qualification-authority admission prerequisite** whose sole purpose is to resolve D2-F01 without asserting functional capability success.

That prerequisite must determine and qualify a clean representation of:

```text
authority to ATTEMPT an unqualified capability
        ≠
evidence that the capability is AVAILABLE
```

Only after that prerequisite PASS may the final exact D2 AgentBinding be frozen.

Then, and only then, can one bounded Codex model turn be authorized under the already-frozen P5-FX-001 task and verdict rules.
