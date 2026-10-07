# GWF vNext P1 — Governance Kernel Preregistration and Contract Freeze

**Gate:** `GWF_VNEXT_P1_GOVERNANCE_KERNEL_PREREGISTRATION_AND_CONTRACT_FREEZE`  
**Status:** PREREGISTERED / CONTRACT FROZEN CANDIDATE  
**Date:** 2026-10-07  
**Branch:** `pivot/gwf-autonomous-research-stack-v1`  
**P0 closure baseline:** `c0af7cb31756df2533e5d2d944eb30cf07a601c3`  
**Machine-readable contract:** `docs/pivot/GWF_VNEXT_P1_CONTRACT_MANIFEST_V1.yaml`  
**Frozen manifest blob:** `c05a94657863cc5ccb3b95273723fd0dda2ff519`

## 1. Purpose

P1 freezes the provider-neutral governance contracts required by GWF vNext before runtime implementation.

P1 does not implement these contracts.

The contracts must support both:

1. G2E-driven proof work;
2. non-G2E governed work such as software delivery, infrastructure triage, documentation, and future domain packages.

No contract in P1 may encode Codex, ChatGPT, RemoteMCP, Astra, Sol, research hypothesis semantics, or software release semantics directly into the GWF core.

## 2. P1 research/engineering question

Can the GWF governance kernel represent:

- active governance policy;
- controlled policy transitions;
- bounded work delegation;
- durable human intervention;
- executor/environment binding;
- authority ceilings;
- resource budgets;

without:

- duplicating G2E semantic authority;
- conflating runtime placement with semantic identity;
- hard-coding provider or transport behavior;
- forcing research semantics into software domains;
- requiring browser UI presence?

P1 PASS requires a frozen contract set for which the answer is YES with no unresolved ownership collision.

## 3. Frozen baselines

P1 is derived from, but does not mutate, these exact architectural sources:

### GWF vNext

- P0 architecture/identity reconciliation on the pivot branch;
- existing GWF execution kernel;
- existing GWF decision kernel;
- existing GWF governance kernel;
- existing GWF domain package contract.

### Existing GWF primitives retained

P1 does not replace:

- `PRIM-ACTOR`;
- `PRIM-AUTHORITY`;
- `PRIM-APPROVAL`;
- `PRIM-AUDIT`;
- `PRIM-WORKUNIT`;
- `PRIM-RUN`;
- `PRIM-EVIDENCE`;
- `PRIM-CHECKPOINT`;
- `PRIM-GATE`;
- `PRIM-DECISION`;
- `PRIM-FAILURE`;
- `PRIM-RECOVERY`.

P1 adds higher-order governance objects that compose with these primitives.

### G2E semantic baseline

P1 preserves the P0 decision that G2E owns:

- Goal;
- Claim;
- ProofObligation;
- canonical ExecutionAttempt semantics;
- EvidenceAdmission;
- Adjudication;
- G2E AgentBinding.

GWF vNext may persist/map those objects but may not reinterpret them.

## 4. Contract set frozen by P1

P1 freezes these provider-neutral contracts:

1. `GovernanceProfileRef`;
2. `GovernanceProfileDefinition` contract;
3. `GovernanceTransitionProposal`;
4. `AuthorityEnvelope`;
5. `AuthorityEnvelopeDelta`;
6. `BudgetEnvelope`;
7. `BudgetEnvelopeDelta`;
8. `ExecutionEnvironmentRef`;
9. `ExecutorBinding`;
10. `WorkAssignment`;
11. `HumanActionRequest`;
12. derived `EffectiveGovernancePolicy`.

The exact field-level candidate contract is frozen in the machine-readable manifest bound above.

## 5. GovernanceProfile semantics

### 5.1 Ownership

`GovernanceProfileDefinition` is domain-owned.

GWF core owns:

- validation of the generic shape;
- exact version/hash resolution;
- deterministic compilation;
- enforcement of generic policy sections.

GWF core does not own the domain meaning of profile IDs.

Therefore:

```text
research.exploratory
research.measurement
research.confirmatory
```

may be defined by the research package, while the software package may define a completely different profile vocabulary.

The core must not infer policy from names such as `confirmatory`, `release`, `strict`, or `exploratory`.

### 5.2 Exact reference

An active profile is always:

```text
domain_id
profile_id
profile_version
profile_hash
```

A floating reference such as:

```text
research.current
latest
default-current
```

is invalid for authoritative execution.

### 5.3 Effective policy compilation

`EffectiveGovernancePolicy` is a derived record, not a mutable source of authority.

It is deterministically compiled from exact refs to:

```text
base GWF authority
+ exact GovernanceProfileRef
+ project overlays
+ AuthorityEnvelope
+ BudgetEnvelope
+ applicable resolved human-authority records
```

Same exact inputs must produce the same compiled hash.

Chat history, browser local state, model memory, or hidden planner state are forbidden inputs.

## 6. Governance transition contract

A profile change is never a direct field mutation.

It begins as `GovernanceTransitionProposal`.

### 6.1 Frozen transition payload

Before evaluation, the proposal freezes:

- source profile;
- target profile;
- project/subject;
- proposer;
- reason codes;
- evidence refs;
- requested authority delta;
- requested budget delta.

The frozen payload receives a canonical hash.

### 6.2 Disposition

The core resolves the exact domain-defined transition edge to one of:

- `AUTO_ALLOWED`;
- `HUMAN_APPROVAL_REQUIRED`;
- `FORBIDDEN`;
- `SUCCESSOR_REQUIRED`.

The core must not guess “stricter” or “looser” from profile names.

### 6.3 Human transition

`HUMAN_APPROVAL_REQUIRED` creates or references a durable `HumanActionRequest`.

Browser interaction is optional presentation; the request exists independently.

### 6.4 Successor transition

`SUCCESSOR_REQUIRED` means the old terminal lineage is preserved and a new governed successor identity is required.

It never means “reopen and edit the old result.”

## 7. AuthorityEnvelope contract

`AuthorityEnvelope` is a delegated ceiling, not a replacement authorization engine.

The existing `PRIM-AUTHORITY` remains authoritative.

### 7.1 Composition

For a child envelope:

```text
resource scope = intersection(parent, child)
ALLOW          = intersection(parent ALLOW, child ALLOW)
DENY           = union(parent DENY, child DENY)
conditions     = conjunction(parent, child)
expiry         = earliest applicable expiry
```

DENY wins.

### 7.2 Monotonicity

Without an explicit authorized change:

```text
child authority <= parent authority
```

No PM, worker, transport, execution adapter, plugin, task, or model may increase authority.

### 7.3 Expansion

Any proposed authority expansion must be explicit and hash-bound.

If policy requires human authority, expansion cannot occur until the corresponding `HumanActionRequest` resolves through the existing approval/decision authority path.

## 8. BudgetEnvelope contract

Budget is multidimensional and provider-neutral.

P1 does not hard-code dollars, tokens, GPU-hours, retries, experiments, or TEST accesses as universal dimensions.

A domain/project may define dimensions such as:

```text
wall_time
attempts
parallel_workers
compute
external_calls
protected_resource_consumptions
monetary_cost
```

Each dimension binds:

- name;
- unit;
- ceiling;
- enforcement: `HARD | ADVISORY`.

### 8.1 Composition

For a dimension constrained by both parent and child:

```text
effective ceiling = min(parent, child)
```

A child may add a new constraint.

A child may not increase an inherited ceiling without explicit authorized expansion.

### 8.2 Usage ledger

Consumed usage is runtime state and MUST NOT mutate the frozen budget definition.

Implementation must maintain usage separately.

## 9. ExecutionEnvironmentRef contract

`ExecutionEnvironmentRef` identifies a qualified adapter/environment, not an agent role and not authority.

Required identity dimensions:

- environment ID/type;
- adapter ID/version/hash;
- capability manifest ref.

Optional classifications may include:

- transport class;
- locality class;
- opaque secret connection ref.

Raw credentials are forbidden.

P1 deliberately does not enumerate provider-specific fields for Codex or RemoteMCP.

Those belong to later adapters.

## 10. ExecutorBinding contract

P1 permanently reserves the name `AgentBinding` for G2E semantics.

GWF runtime binding is `ExecutorBinding`.

### 10.1 Purpose

`ExecutorBinding` answers:

> Which resolved agent identity and qualified execution environment are allowed to materialize this exact WorkAssignment under its frozen authority/budget constraints?

### 10.2 Modes

- `DYNAMIC` — binding may be resolved per attempt before dispatch, within frozen constraints;
- `FROZEN` — material binding dimensions are prospectively locked.

Dynamic does not mean mutable mid-attempt.

Once resolved for a dispatched attempt, the resolved binding is immutable for that attempt.

### 10.3 Material identity

The binding explicitly lists material identity dimensions, such as:

- agent app;
- model;
- provider;
- harness;
- environment;
- tool set;
- capability manifest.

Material substitution is never silent.

### 10.4 Relation to G2E

`ExecutorBinding != G2E AgentBinding`.

PIVOT-P3 must map them without replacing either identity.

## 11. WorkAssignment contract

`WorkAssignment` is the central GWF vNext governed delegation object.

It is:

- not a G2E ProofObligation;
- not a G2E ExecutionAttempt;
- not a current GWF WorkUnit;
- not a RemoteMCP task;
- not a Codex turn.

### 11.1 Purpose

It converts an authorized objective into a bounded execution contract containing:

- origin refs;
- objective;
- role;
- required capabilities;
- environment constraints;
- authority envelope;
- budget envelope;
- protected-resource constraints;
- expected outputs;
- completion contract;
- independence requirements.

### 11.2 Proposal versus authority

A PM may create a `PROPOSED` assignment.

This grants no execution authority.

The assignment must be frozen and authorized by GWF before dispatch.

### 11.3 Normative immutability

After freeze, changes to normative fields create a new revision and require reauthorization.

Runtime progress fields are not normative mutations.

### 11.4 Existing execution kernel mapping

A WorkAssignment may materialize one or more existing GWF `PRIM-WORKUNIT` objects.

Existing `PRIM-RUN` remains the concrete runtime attempt/run record inside GWF.

P1 does not freeze a universal 1:1 cardinality between:

- G2E ExecutionAttempt;
- WorkAssignment;
- WorkUnit;
- ExecutionRun.

That mapping is adapter/domain-specific and is deferred to PIVOT-P3/PIVOT-P5/PIVOT-P6.

The only frozen rule is that every mapping must be explicit and reconstructable.

### 11.5 Completion semantics

`WorkAssignment.COMPLETED` means the assignment's operational completion contract was satisfied.

It MUST NOT imply:

- G2E PASS;
- scientific PASS;
- release acceptance;
- gate PASS;
- claim resolution.

## 12. Binding resolution timing

P1 freezes two valid patterns.

### Pattern A — frozen/material executor before authorization

When executor identity is itself material to authority, reproducibility, independence, or study validity:

```text
assignment freeze
 -> binding resolution
 -> binding freeze
 -> authorization
 -> dispatch
```

### Pattern B — dynamic executor after authorization

When policy permits an executor equivalence class:

```text
assignment freeze
 -> authorization of constraints/equivalence class
 -> binding resolution within those constraints
 -> dispatch
```

In both patterns, binding resolution occurs before dispatch.

A resolved binding may not mutate within the attempt.

## 13. HumanActionRequest contract

`HumanActionRequest` is durable governed state for something only an authorized human/principal may decide.

Examples include:

- governance transition;
- authority expansion;
- budget expansion;
- protected-resource consumption;
- destructive external action;
- claim/release elevation.

### 13.1 It does not replace Approval

Existing `PRIM-APPROVAL` remains the exact frozen-proposal approval primitive.

`HumanActionRequest` is the durable request/queue object.

Resolution references the authoritative approval/decision record.

### 13.2 Hash binding

A HumanActionRequest always binds the exact frozen payload hash.

Payload change invalidates the old request.

### 13.3 UI independence

Closing the browser does not cancel, approve, or erase a request.

## 14. Hash and revision contract

P1 reuses the existing GWF canonical hash semantics:

```text
canonical JSON:
  sort_keys = true
  separators = compact
  UTF-8
  ensure_ascii = false

digest:
  SHA-256
```

For each frozen object, the contract implementation must hash exactly its frozen normative payload.

Runtime status, timestamps generated after freeze, usage counters, logs, foreign job IDs, and observational projections must not silently change the frozen payload hash unless explicitly designated normative by that object's schema.

## 15. Mutation command invariants

Future implementation of every P1 mutating command must preserve existing GWF mutation discipline:

- idempotency key;
- expected version/revision where applicable;
- exact actor identity;
- server-side authority check;
- audit event;
- deterministic conflict on same idempotency key with different payload;
- no browser-only mutation authority.

P1 does not freeze HTTP routes or database tables.

Those are implementation concerns for the next phase.

## 16. Failure semantics

P1 retains P0's top-level separation:

### Operational

Examples:

- process crash;
- machine offline;
- transport timeout;
- disk exhaustion;
- dependency failure.

These may affect assignment/run state.

They do not automatically produce scientific/domain FAIL.

### Execution-contract violation

Examples:

- wrong executor;
- authority mismatch;
- wrong environment;
- binding substitution;
- stale frozen payload.

These fail execution admissibility and may require a new assignment/binding/revision.

### Domain substantive outcome

Only the owning domain/G2E semantics may decide substantive PASS/FAIL/UNRESOLVED.

## 17. Protected-resource boundary

P1 allows `WorkAssignment.protected_resource_constraints` and profile policy to carry governed constraints.

P1 does not redefine G2E protected-resource identity/freshness semantics.

If a G2E object is the semantic owner, GWF stores/enforces the exact referenced policy and records runtime access transitions through the adapter contract defined later.

No protected access may be inferred from UI action or executor intent.

## 18. Autonomy boundary

Autonomy is a policy result, not an intrinsic privilege of an LLM.

A domain profile may permit generic actions such as:

- propose child work;
- auto-retry;
- auto-replan;
- choose among pre-authorized equivalent executors;
- create bounded non-protected work.

The exact allowed actions are still checked through effective authority and budget.

No profile can grant authority unavailable at the parent GWF level.

## 19. Preregistered negative tests for implementation

The implementation phase MUST include negative tests proving at least:

1. child AuthorityEnvelope cannot add an action absent from parent;
2. child resource scope cannot widen parent scope;
3. DENY overrides ALLOW;
4. budget child cannot increase inherited ceiling silently;
5. WorkAssignment PROPOSED cannot dispatch;
6. changed frozen assignment payload invalidates prior authorization;
7. changed HumanActionRequest payload invalidates prior approval/request;
8. dynamic ExecutorBinding cannot mutate after dispatch;
9. frozen ExecutorBinding substitution is rejected;
10. WorkAssignment COMPLETED cannot directly set a G2E/scientific verdict;
11. RemoteMCP/Codex foreign IDs cannot replace canonical assignment identity;
12. UI state cannot authorize execution;
13. unresolved profile hash cannot execute;
14. unknown profile transition edge fails closed;
15. provider credentials cannot serialize into P1 contract records;
16. operational failure does not create domain PASS/FAIL by itself.

These negative tests are frozen before implementation.

## 20. P1 PASS / FAIL criteria

### PASS

P1 passes only if:

- all P0 ownership boundaries remain intact;
- machine-readable manifest and normative document agree;
- all P1 objects have a single owner;
- no provider-specific execution behavior appears in core contracts;
- authority composition is monotonic;
- budget composition is monotonic without authorized expansion;
- transition semantics fail closed;
- WorkAssignment remains distinct from WorkUnit/G2E attempt/RemoteMCP task;
- HumanActionRequest remains distinct from Approval;
- executor success remains distinct from domain verdict;
- research/software package separation remains intact;
- implementation negative tests are preregistered;
- no runtime implementation is introduced.

### FAIL

P1 fails if any of the following remains true:

- two systems claim semantic ownership of the same canonical identity;
- an executor/transport can grant itself authority;
- a profile can mutate domain verdict semantics retrospectively;
- provider-specific fields become mandatory GWF core semantics;
- browser state is required for authoritative progression;
- G2E AgentBinding is duplicated/redefined;
- a completed runtime object can imply scientific PASS;
- authority/budget expansion can occur without explicit governed change;
- P1 mutates runtime/domain implementation before contract freeze.

## 21. Implementation lock

Until P1 receives formal QA PASS, the following remain forbidden:

- DB/schema migrations;
- new runtime classes under `src/gwr`;
- modifications to research/software domain files;
- G2E code import;
- RemoteMCP adapter implementation;
- Codex adapter implementation;
- browser/Mission Control implementation;
- real-project pilot;
- protected evidence consumption.

## 22. Post-P1 frontier

If P1 formally closes PASS, the next bounded phase is:

`GWF_VNEXT_P1_GOVERNANCE_KERNEL_IMPLEMENTATION_STATIC_PREFLIGHT_AND_EXECUTION_LOCK`

That phase may implement only the frozen provider-neutral P1 contracts plus zero-domain/zero-provider fixtures and the preregistered negative tests.

It still must not integrate RemoteMCP, Codex, G2E runtime code, research profiles, or Mission Control UI.
