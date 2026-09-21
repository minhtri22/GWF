# G2E P1.4 — Agent Profile / Binding Identity Result

## Verdict

**PASS**

P1.4 schema-only prerequisite is qualified.

This result does **not** implement or qualify Codex or ChatGPT runtime adapters.

## Pre-implementation qualification

- baseline before P1.4: `bfd7e29513ef22f569f931ab75f9d29fd5ec89f6`
- frozen pre-implementation specification commit: `2f20bca03bf68b2f5acb1566105d1c47a4b72fb0`
- zero-implementation candidate: `995ca7a87e2acc3bdb7980046509b0061de48a4e`
- pre-implementation workflow: `35590024177`
- pre-implementation job: `106302073904`
- conclusion: **PASS**
- evidence artifact: `10633823851`
- artifact digest: `sha256:8058dc3040ec073e4d9210846c725e3362771ccecbea4a324712b738c09fa20b`
- pre-implementation spec blob: `4df89bf0b26ac545b09ee9add9f7be2b50340b8e`
- pre-implementation test blob: `eeb4d3015eda0562c6f57f798fec8414e7808ee1`
- pre-implementation workflow blob: `1716f54921af8e0e501ac29c89a2abb9c1cb6855`

The zero-implementation gate passed P1–P4 regressions before any schema mutation and explicitly authorized only the bounded P1.4 schema implementation.

## Qualified implementation

Exact qualified SHA:

`d3cb0bdb5644a9f1cff382450b5476e166759d72`

Qualified implementation blobs:

- `src/g2e/schemas.py`: `2ae69408704086e415e88bb977b2e3520ff981ee`
- `src/g2e/standalone.py`: `48c44050da96ecdac9061f74092b6af00cfc5694`
- `src/g2e/gwf_adapter.py`: `5ae80f28d03893848ec6e693b8c9f6197e87020a`
- `tests/g2e/test_p1_4_agent_binding.py`: `a87e094bed885198af0e95c89696bd02d28811a9`
- `tests/g2e/test_p4_gwf_adapter.py`: `13a94648df5154e769174d618604d03308f775c8`
- `.github/workflows/g2e-p1-4-agent-binding.yml`: `c428bd6a582312033cf80f4b4f54a466b67efd17`

The completed historical P5 pre-implementation workflow was removed from automatic `schemas.py` triggering before the schema patch so that its intentionally historical “P1.4 gap exists” fixture cannot create a false CI failure after the prerequisite is satisfied. Its original exact run/artifact remain immutable qualification evidence.

## New canonical schema surface

P1.4 adds provider-neutral canonical representations for:

- `AgentProfileAvailability`;
- `BindingMode`;
- `AgentCapability`;
- `AgentCapabilityManifest`;
- `AgentEquivalencePolicy`;
- `AgentBinding`.

New schema kinds:

```text
agent_capability_manifest
agent_equivalence_policy
agent_binding
```

No provider/app-specific schema was added.

## Execution identity extension

`ExecutionAttemptEnvelope` now supports:

`agent_binding_ref: ExactRef | None`

`ExecutionResult` carries the same binding reference.

Compatibility is fail-closed:

- non-agent attempts/results remain valid without a binding;
- any populated app/provider/model/harness/transport identity requires an exact binding ref;
- a binding ref requires at least app + harness identity;
- P3/P4 provider-neutral execution paths propagate the exact binding ref and copied identities.

This preserves old standalone/GWF non-agent behavior while preventing partially attributable agent execution.

## Canonical relation validation

P1.4 adds pure provider-neutral validation:

`validate_agent_binding_identity(...)`

It verifies:

- exact manifest ref;
- exact equivalence-policy ref;
- resolved attempt identity;
- exact attempt binding ref;
- manifest → binding → attempt identity equality;
- required capability availability + qualification refs;
- granted authority subset of manifest maximum;
- result → attempt/binding identity consistency when a result is supplied.

The validator performs no discovery, dispatch, network call, secret resolution, retry or adjudication.

## Fail-closed semantics qualified

The P1.4 fixtures cover:

- AVAILABLE profile without discovery evidence → rejected;
- available capability without qualification evidence → rejected;
- duplicate capability IDs → rejected;
- invalid equivalence policy → rejected;
- agent identity without binding ref → rejected;
- binding ref without app/harness → rejected;
- manifest identity drift → rejected;
- wrong manifest ref → rejected;
- wrong resolved attempt identity → rejected;
- unavailable/unqualified required capability → rejected;
- authority escalation → rejected;
- non-AVAILABLE manifest binding → rejected;
- standalone exact binding propagation → PASS;
- GWF exact binding propagation → PASS.

The implementation contains no `codex` or `chatgpt` branching.

## Exact qualification workflows

All independent workflows ran on the exact qualified SHA `d3cb0bdb5644a9f1cff382450b5476e166759d72`:

| Gate | Run | Job | Result |
| --- | ---: | ---: | --- |
| P1 Core Schemas | `35590544907` | `106303688907` | PASS |
| P2 Deterministic Core | `35590544803` | `106303689038` | PASS |
| P3 Standalone Runtime | `35590544876` | `106303688896` | PASS |
| P4 Base GWF Adapter | `35590544868` | `106303689021` | PASS |
| P1.4 Agent Binding | `35590544831` | `106303688970` | PASS |

P1.4 qualification artifact:

- artifact ID: `10634082369`
- name: `g2e-p1-4-agent-binding`
- digest: `sha256:7d28b488f937dc1f5d6afb3a6159688c76b9f1dd8c40f72de54f00455e551d22`

The P1.4 workflow also independently reran P1, P2, P3 and P4 and asserted provider-neutral implementation scope.

## Scope boundary

P1.4 did not add:

- Codex driver/profile runtime;
- ChatGPT driver/profile runtime;
- provider API calls;
- MCP server/client;
- ARC transport;
- agent registry persistence;
- harness session creation;
- actual profile discovery;
- credential resolution;
- GAC/P4L/Reference Acquisition behavior.

## P5 findings disposition

### P5-F01

**CLOSED.**

Agent-app capability identity is now represented by `AgentCapabilityManifest`; `RuntimeCapabilityManifest` remains backend-runtime-only.

### P5-F02

**CLOSED.**

Exact canonical `AgentBinding`, prospective equivalence policy, attempt binding reference and deterministic relation validation now exist.

## Next admissible frontier

P1.4 removes the schema blocker identified by P5 pre-implementation qualification.

The next admissible P5 activity is **P5A Codex actual-harness capability discovery / profile qualification preparation**.

That next phase must still discover and bind the actual Codex harness independently and must not infer ChatGPT capability. This P1.4 result does not itself authorize a runtime adapter implementation without that profile-specific qualification step.
