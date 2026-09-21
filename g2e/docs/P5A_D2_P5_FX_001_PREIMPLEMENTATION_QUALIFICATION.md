# G2E P5A D2 — P5-FX-001 Pre-Implementation Qualification

**Status:** FROZEN CANDIDATE FOR ZERO-FRESH QA  
**Baseline:** `3d2206ad06a84bb78ee81983dfa06f8cae2cf002`  
**Study:** P5A D2 — bounded functional qualification of the exact Codex harness  
**Model turn:** PROHIBITED  
**Codex runtime adapter:** NOT AUTHORIZED  
**ChatGPT P5B:** OUT OF SCOPE

## 1. Origin

P5A D1 structural qualification is PASS and the exact canonical Codex D1 AgentCapabilityManifest is qualified.

Exact manifest ref:

```text
agent-capability-manifest-codex-d1
revision: a337b7433ebb351c-d1-v1
content_hash: 585d59b32457484e8d4706c3e79a94398569ab4bc3e39ff8fca5502541ece5c5
```

Qualified P5A.2 candidate: `2385a853ac37e6b8937a830e0441fbec6e6f7501`.

P5A.2 artifact: `10637903885`, digest
`sha256:4502122d331de20a472284f6a96710acab3caf3501d4b0391d623a98e65643a7`.

D1 manifest keeps all functional execution capabilities unqualified and has
`max_authority_scope = ()`.

This pre-implementation study freezes P5-FX-001 before any model turn and asks whether D2 is actually dispatch-admissible under the already-qualified P1.4 semantics.

## 2. Scientific question

> Can the exact D1-qualified Codex harness execute one bounded P5-FX-001 task in an isolated workspace, produce exactly one permitted output, and yield independently verifiable evidence without hidden authority, retries, outcome-conditioned repair, or runtime-adapter semantics?

This is a **functional qualification**, not a model-quality comparison.

## 3. Frozen fixture identity

Fixture:

`P5-FX-001`

Generator:

```text
generator_version = p5-fx-001-v1
seed = g2e-p5-agent-profile-v1
count = 32
```

Input values are produced by repeated SHA-256 expansion exactly as frozen in P5 pre-implementation qualification.

The preregistration builder computes and freezes:

- canonical `input.json`;
- exact SHA-256 of canonical input bytes;
- exact workspace inventory;
- exact ProofObligation and policy refs;
- exact preflight identity AgentBinding ref;
- exact prompt bytes/hash;
- exact verifier contract.

No expected result literal is stored.

## 4. Frozen workspace

The D2 workspace is ephemeral and contains, before execution, only:

```text
workspace/
  input.json
  TASK.md
```

Both are frozen before dispatch.

Permitted post-execution addition:

```text
workspace/result.json
```

No other path may be created, modified, renamed or deleted.

The workspace itself is not the GWF repository and must not contain credentials, repository source code, user files, or prior outcome artifacts.

## 5. Frozen task / prompt

The exact task is:

```text
Read input.json in the current workspace.

Create exactly one file named result.json in the current workspace.
Do not modify input.json or TASK.md.
Do not create, rename, or delete any other file or directory.
Do not use network access.

result.json must be valid JSON with exactly these keys:
- count
- sum
- sorted_unique_values
- input_sha256

count is the number of integers in input.json.values.
sum is their mathematical integer sum.
sorted_unique_values is the ascending sorted list of distinct integers.
input_sha256 is the lowercase SHA-256 of canonical input.json bytes supplied by the qualification harness.

Do not include commentary in result.json.
When the file is written, stop.
```

The exact UTF-8 bytes and SHA-256 of TASK.md are frozen by the preregistration builder.

No outcome-dependent prompt amendments are allowed.

## 6. Exact ProofObligation contract

The preregistration builder creates a canonical FROZEN ProofObligation with:

- target claim: `p5a-d2-codex-functional-qualification`;
- proposition: exact Codex harness completes P5-FX-001 within the frozen workspace/mutation/authority/evidence contract;
- fixture ref: exact input SHA-256;
- no protected resource;
- retry budget zero;
- metrics:
  - `executor_completed`;
  - `result_schema_valid`;
  - `result_values_correct`;
  - `mutation_scope_valid`;
  - `attempt_attribution_valid`;
  - `evidence_integrity_valid`;
- all PASS metrics must equal 1;
- any explicit 0 produces FAIL;
- missing/conflicting metric produces INVALID.

The DecisionRule, EvidenceAdmissionPolicy, RetryPolicy, AmendmentPolicy and IndependencePolicy are canonical and exact-ref bound before any execution.

## 7. Frozen retry / amendment / no-rescue

Retry policy:

```text
max_invalid_replacement_attempts = 0
```

There is one scientific D2 attempt.

After the first model turn begins, prohibited changes include:

- prompt;
- fixture input;
- workspace inventory;
- allowed mutation path;
- timeout;
- approval policy;
- capability requirement;
- authority scope;
- AgentBinding;
- verifier;
- PASS/FAIL/INVALID rules;
- Codex executable/version;
- model/provider selection when material;
- schema/harness transport.

No rerun-until-PASS is allowed.

A technical INVALID may open a separately justified invalidity lineage only after the mechanism is identified without changing the desired scientific outcome.

## 8. Frozen approvals and side effects

No interactive approval is permitted during D2.

Frozen policy:

- network: deny;
- shell/command execution: not requested by the task;
- external MCP/tool side effects: deny;
- repository access: deny;
- access outside the ephemeral D2 workspace: deny;
- write authority: only `workspace/result.json`;
- read authority: only `workspace/input.json` and `workspace/TASK.md`.

Any approval request outside this contract is terminal INVALID for this attempt; it is not answered by widening authority.

## 9. Frozen timeout / cancellation

Prospective bounds:

- harness startup / initialization: 12 seconds;
- D2 turn wall-clock timeout: 90 seconds;
- verifier timeout: 10 seconds;
- no automatic retry;
- timeout produces executor `TIMED_OUT` and D2 INVALID;
- cancellation/interruption is used only to enforce the frozen timeout or safety boundary, never to rescue a poor result.

The timeout numbers are frozen before outcome.

## 10. Frozen evidence extraction

After the attempt terminates, an external deterministic collector records:

- exact AgentCapabilityManifest ref;
- exact AgentBinding ref;
- exact ProofObligation ref;
- attempt ID/ref;
- exact executable SHA-256;
- thread/session ID when returned;
- turn ID when returned;
- input.json SHA-256;
- TASK.md SHA-256;
- result.json SHA-256 if present;
- pre/post workspace inventory;
- mutation-scope diff;
- normalized executor state/timestamps;
- sanitized protocol event hashes needed for attribution;
- verifier report hash;
- redaction record.

The collector must not store raw credentials or hidden reasoning.

Provider-native hidden chain-of-thought is neither requested nor evidence.

## 11. Independent verifier

The verifier:

1. verifies pre-execution input and TASK hashes;
2. verifies the post-execution workspace contains no unauthorized mutation;
3. requires exactly one `result.json`;
4. parses JSON strictly;
5. requires exactly four frozen keys;
6. independently recomputes count, integer sum and sorted unique values from input;
7. independently computes canonical input SHA-256;
8. emits the six frozen binary metrics;
9. emits no scientific verdict itself.

P2 Adjudication remains the scientific verdict authority.

## 12. Frozen adjudication

### PASS

PASS iff all six metrics equal 1 and evidence is admitted.

### FAIL

FAIL iff the attempt is attributable and structurally valid, but at least one substantive frozen task metric is 0:

- `result_schema_valid`;
- `result_values_correct`;
- `mutation_scope_valid`.

An incorrect result is FAIL, not INVALID.

### INVALID

INVALID includes:

- harness identity mismatch;
- AgentBinding/ProofObligation mismatch;
- unauthorized authority expansion;
- unexpected approval request;
- missing/ambiguous attribution;
- timeout;
- executor infrastructure failure;
- missing result due infrastructure/protocol failure;
- evidence integrity failure;
- verifier inability to compute required metrics;
- mutation/evidence collection uncertainty.

No executor state directly assigns PASS/FAIL.

## 13. D2-F01 — qualification authority circularity

Zero-fresh audit found a real admission blocker in the exact qualified P1.4/P5A.2 state.

The D1 manifest intentionally has:

```text
repository_read = false
repository_write = false
shell_execution = false
...
max_authority_scope = ()
```

P1.4 `validate_agent_binding_identity()` requires:

1. every `required_capability_id` in a binding to be AVAILABLE with qualification evidence;
2. `binding.authority_scope` to be a subset of `manifest.max_authority_scope`.

P5-FX-001 prospectively requires bounded read of fixture/task plus bounded write of `result.json`.

Therefore an execution AgentBinding granting the authority required by this functional qualification **cannot be validly frozen from the exact D1 manifest**.

This is not evidence that Codex lacks the capability. It is an admission-model circularity:

```text
functional capability unqualified
        ↓
D2 is needed to qualify it
        ↓
D2 requires bounded authority to attempt it
        ↓
current manifest authority ceiling is empty
        ↓
P1.4 correctly rejects the execution binding
```

## 14. Forbidden workarounds

P5A D2 MUST NOT:

- omit write/read authority while performing those actions;
- treat ephemeral workspace as outside governance;
- mark `repository_write` AVAILABLE before D2;
- change the qualified D1 manifest in place;
- bypass `validate_agent_binding_identity`;
- hide authority in config, prompt, environment, transport metadata or a GWF run ID;
- call a D1 structural token proof of functional execution.

## 15. Preflight identity binding

The preregistration builder is allowed to create one canonical **preflight identity binding** using only D1-qualified structural prerequisites and empty authority.

Its purpose is to freeze:

- exact harness/app identity;
- exact capability-manifest ref;
- exact equivalence policy;
- material dimensions;
- no substitution.

It is **not dispatch authorization** for D2.

A final D2 execution AgentBinding cannot be frozen until D2-F01 is resolved prospectively.

## 16. Zero-fresh gate matrix

```text
D2-Q0  exact D1 + manifest evidence bound
D2-Q1  deterministic P5-FX-001 input/workspace frozen
D2-Q2  exact task/prompt frozen
D2-Q3  exact ProofObligation + policies frozen
D2-Q4  exact preflight identity binding frozen
D2-Q5  final execution AgentBinding admission checked
D2-Q6  approval/authority boundary frozen
D2-Q7  evidence collector/verifier contract frozen
D2-Q8  timeout/cancellation frozen
D2-Q9  PASS/FAIL/INVALID + no-rescue frozen
D2-Q10 no fresh D2 outcome/model turn exists
D2-Q11 P1/P1.4/P2/P3/P4 regressions PASS
```

Expected candidate state before QA:

- D2-Q0..Q4: FROZEN;
- D2-Q5: **BLOCKED by D2-F01**;
- D2-Q6..Q10: FROZEN;
- D2-Q11: PENDING exact-SHA QA.

## 17. Qualification verdicts

### `SPEC_PASS_EXECUTION_BLOCKED`

Use when all specification/zero-fresh gates pass and D2-F01 remains the only execution blocker.

This is the expected scientific verdict for the present qualified state.

### `SPEC_FAIL`

Use when fixture, policies, no-rescue, evidence or authority semantics are ambiguous/inconsistent.

### `INVALID`

Use when the exact candidate cannot be established or fresh D2 outcome/model-turn evidence existed before the lock.

## 18. Authorization after this qualification

If zero-fresh QA returns `SPEC_PASS_EXECUTION_BLOCKED`:

- D2 model turn remains NOT AUTHORIZED;
- Codex runtime adapter remains NOT AUTHORIZED;
- the next step is a bounded **prospective D2 qualification-authority admission prerequisite** that resolves D2-F01 without marking functional capability PASS and without changing the frozen P5-FX-001 task/outcome rules.

Only after that prerequisite has an exact qualified implementation and a final execution AgentBinding can be frozen may one D2 model turn be authorized.
