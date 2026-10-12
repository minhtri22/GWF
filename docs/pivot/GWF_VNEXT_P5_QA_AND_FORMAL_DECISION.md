# GWF vNext P5 — ChatGPT Web / RemoteMCP Execution Environment QA and Formal Decision

**Gate:** `GWF_VNEXT_P5_CHATGPT_WEB_REMOTEMCP_EXECUTION_ENVIRONMENT_PREREGISTRATION_AND_CONTRACT_FREEZE`  
**Date:** 2026-10-12  
**Branch:** `pivot/gwf-autonomous-research-stack-v1`  
**Contract base HEAD:** `739b8f62a6672f13eb48bca980a6aee234570335`  
**Manifest blob:** `2e4587cb501d3f98e29bb79be35e48f8f8bd1a36`  
**Preregistration blob:** `10d8126d56d9ccd9cd68acc310e00619d62a27b2`  
**Verdict:** **PASS / CONTRACT FROZEN / FORMALLY CLOSED**

## 1. Upstream-lock QA

P5 is based on the exact P4 execution-lock branch state.

Preserved execution-lock blobs:

- P1: `ecfc8435f0f381d0a2edfac8575cbbc09a87abe3`;
- P2: `25660c52526923d557224ac9fbc9abeae23adcc4`;
- P3: `60aa70e8f03a2c4f11e5693bf58cf82b5806b24e`;
- P4: `da96b599137835592d0ceb390ffe0162d6bcee33`.

The P5 contract does not redefine any P1-P4 object or verdict.

Result: **PASS**.

## 2. Environment-separation QA

The contract retains two non-equivalent execution environments.

P5 covers only:

`CHATGPT_WEB_REMOTEMCP`

It does not import the Codex/CGW P6 route.

RemoteMCP remains an internal execution bridge for environment B and does not become the owner of G2E proof semantics or GWF governance.

Result: **PASS**.

## 3. Canonical Web identity QA

Frozen logical Web plugin identity:

`remote-mcp-v2-web-clean`

Frozen transport:

`APP_BACKED`

Legacy `remote-mcp-v2-web` is explicitly forbidden as canonical P5 fallback.

The contract also freezes backend namespace/display label as a non-normative implementation detail. Therefore backend naming cannot silently become semantic execution identity or authority.

Result: **PASS**.

## 4. Worker identity QA

The contract does not create a competing G2E `AgentBinding` or GWF `ExecutorBinding`.

It freezes a foreign `ChatGPTWebWorkerContextRef` whose identity projection must be equal-or-narrower than upstream frozen agent identity.

Material worker/model/provider/harness substitution remains governed by P3 equivalence/replacement semantics.

Result: **PASS**.

## 5. Placement identity QA

`RemoteMCPExecutionPlacement` maps one authorized Env-B dispatch to exact:

- WorkAssignment;
- ExecutorBinding;
- ExecutionEnvironmentRef;
- worker context;
- device ID/fingerprint/route generation;
- managed project/binding generation;
- task;
- source/base/worktree state.

RemoteMCP IDs remain foreign runtime IDs.

Task cannot override inherited project-device placement.

Result: **PASS**.

## 6. WorkAssignment-to-runtime cardinality QA

Frozen cardinalities preserve:

- one Env-B WorkAssignment dispatch -> one resolved ExecutorBinding;
- one ExecutorBinding -> one qualified Env-B ExecutionEnvironmentRef;
- one WorkAssignment dispatch -> at most one active placement revision;
- one placement -> one device + one managed project + one task;
- one task -> zero or more bounded operational jobs;
- v1 -> at most one authoritative mutating job active per task/worktree.

Multiple operational jobs do not imply multiple scientific attempts.

Result: **PASS**.

## 7. Lease and secret QA

Lease token is ephemeral and forbidden from durable records.

Pairing and connector/account secrets are forbidden in:

- commands/jobs;
- argv;
- task payloads;
- repository;
- logs;
- checkpoints;
- evidence/result envelopes;
- scientific lineage.

Only opaque connection references may persist where upstream contracts allow them.

Result: **PASS**.

## 8. Authority non-escalation QA

P5 effective action authority is frozen as the intersection of:

- WorkAssignment;
- ExecutorBinding;
- active GovernanceProfile;
- qualified environment capability manifest;
- placement policy;
- resolved HumanActionRequest constraints.

The contract explicitly denies authority creation from:

- plugin technical capability;
- connector account permission;
- prompt text;
- device ONLINE state;
- arbitrary-command capability;
- pairing ticket;
- UI state.

Result: **PASS**.

## 9. Infrastructure-action QA

Ordinary worker authority cannot silently pair/re-pair/revoke, restart nodes, register/bind projects, widen roots, or create replacement identities.

Root mismatch has the frozen fail-closed disposition:

`BLOCKED_ON_MANAGED_PROJECT_EXPOSURE_OR_EXPLICIT_DEDICATED_NODE_GATE`

Plugin/session attachment failure has:

`PLUGIN_SESSION_BINDING_FAILURE`

Neither disposition authorizes node repair.

Result: **PASS**.

## 10. Managed routing QA

The contract requires task-scoped routed execution evidence.

Gateway-local compatibility command success cannot prove task/device routing.

Task/project/device/job provenance must reconcile before terminal result is accepted.

Result: **PASS**.

## 11. Durable-job provenance QA

The job contract separates proxy job and materialized node job identities.

A proxy with no node-job ID proves only control-plane intent.

The terminal path requires task/project/device, argv hash, terminal event, exit code/state and normalized result provenance.

This prevents a queued proxy residue from being mistaken for completed execution.

Result: **PASS**.

## 12. Scientific continuity QA

Loss of job observability does not authorize relaunch.

The contract freezes:

`inspect/reconcile existing identity before any replacement action`.

Scientific rerun remains separately governed by G2E/GWF and cannot be inferred from infrastructure uncertainty.

Result: **PASS**.

## 13. Checkpoint/recovery QA

Checkpoint identity binds exact:

- G2E attempt;
- WorkAssignment;
- ExecutorBinding;
- placement;
- source state;
- job refs;
- protected-resource state;
- semantic-state digest.

Recovery cannot silently move to a different task/worktree/source state or roll protected-resource exposure backward.

Result: **PASS**.

## 14. Restart/rebind QA

Restart remains infrastructure governance.

When separately authorized, recovery requires same-device identity checks and source/checkpoint revalidation.

Material device/fingerprint/worker/source substitution requires governed rebinding and follows P3 new-attempt rules where material.

Result: **PASS**.

## 15. Protected-resource QA

P5 inherits P3 monotonic state:

`FRESH -> RESERVED -> EXPOSED`

Backward transition is forbidden.

Uncertain protected access is:

`EXPOSED_FAIL_CLOSED`

P5 does not create a new protected-resource authority path.

Result: **PASS**.

## 16. Evidence-return QA

The frozen flow is:

```text
RemoteMCP output
 -> P5 provenance/digest normalization
 -> ExecutionResultEnvelope
 -> candidate evidence bridge
 -> G2E EvidenceAdmissionPolicy
 -> admitted/rejected/invalidated
 -> adjudication
```

Runtime success is neither evidence admission nor scientific PASS.

Raw logs are not automatically evidence.

Result: **PASS**.

## 17. Result-envelope completeness QA

The contract requires exact cross-layer provenance including:

- G2E attempt;
- WorkAssignment;
- ExecutorBinding;
- environment;
- worker context;
- placement;
- device/project/task;
- source/worktree;
- proxy/node job;
- argv hash;
- terminal event/status;
- log/artifact digests;
- checkpoint/environment attestation;
- protected-resource state.

Missing or mismatched provenance is rejected.

Result: **PASS**.

## 18. Negative-test preregistration QA

The manifest freezes exactly **56** symbolic negative tests before implementation.

Coverage includes:

- canonical plugin/session identity;
- worker/device/project/task/worktree identity;
- lease and secret handling;
- durable-job provenance;
- authority non-escalation;
- infrastructure privilege boundaries;
- observability/recovery continuity;
- checkpoint identity;
- protected-resource monotonicity;
- evidence-return/admission firewall;
- upstream P3/P4 authority boundaries;
- P5 qualification scope.

Result: **PASS**.

## 19. Scope QA

This gate authorizes documentation/contract artifacts only.

No P5 adapter/runtime code is authorized or created by this contract-freeze decision.

No real RemoteMCP P5 qualification job, real research/software project, protected evidence, P6 adapter, Mission Control refactor, or scientific execution is authorized.

Operational infrastructure state is not appended to scientific `LINEAGE.md`.

Result: **PASS**.

## 20. Formal disposition

All P5 preregistration/contract-freeze criteria pass.

```text
GWF_VNEXT_P5_CHATGPT_WEB_REMOTEMCP_EXECUTION_ENVIRONMENT_PREREGISTRATION_AND_CONTRACT_FREEZE
= PASS
= CONTRACT FROZEN
= FORMALLY CLOSED
```

This is an architecture/runtime-contract PASS only.

It does **not** claim that the P5 RemoteMCP adapter has been implemented or qualified.

## 21. Next authorized frontier

The only authorized successor is:

`GWF_VNEXT_P5_CHATGPT_WEB_REMOTEMCP_EXECUTION_ENVIRONMENT_IMPLEMENTATION_STATIC_PREFLIGHT_AND_EXECUTION_LOCK`

That successor may implement the adapter and run zero-science/synthetic qualification fixtures against the frozen 56-test matrix.

It still may not:

- execute a real research/software project as P5 qualification;
- consume protected scientific evidence;
- open P6 Codex/CGW;
- open P8 headless real pilot;
- refactor Mission Control;
- open P10 real-project pilot.
