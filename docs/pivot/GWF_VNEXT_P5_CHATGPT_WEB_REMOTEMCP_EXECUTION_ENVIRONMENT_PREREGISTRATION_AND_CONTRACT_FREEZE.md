# GWF vNext P5 — ChatGPT Web / RemoteMCP Execution Environment Preregistration and Contract Freeze

**Gate:** `GWF_VNEXT_P5_CHATGPT_WEB_REMOTEMCP_EXECUTION_ENVIRONMENT_PREREGISTRATION_AND_CONTRACT_FREEZE`  
**Date:** 2026-10-12  
**Branch:** `pivot/gwf-autonomous-research-stack-v1`  
**Contract base HEAD:** `739b8f62a6672f13eb48bca980a6aee234570335`  
**Status:** FROZEN CANDIDATE

## 1. Purpose

P5 freezes the provider/runtime-specific contract for execution environment B:

```text
GWF-authorized WorkAssignment
  -> resolved GWF ExecutorBinding
  -> qualified CHATGPT_WEB_REMOTEMCP ExecutionEnvironmentRef
  -> ChatGPT Web worker context
  -> RemoteMCP placement
       device
       project
       task
       worktree/source state
       lease epoch
       durable jobs
       checkpoints
  -> normalized ExecutionResultEnvelope
  -> candidate evidence path only
```

P5 does not implement the adapter yet. It does not run a real project, consume protected evidence, or open P6.

The contract exists to prevent runtime power from silently becoming governance or scientific authority.

## 2. Frozen upstream authority boundaries

P5 inherits without reinterpretation:

- P1: GWF owns `WorkAssignment`, `ExecutorBinding`, `ExecutionEnvironmentRef`, `AuthorityEnvelope`, `BudgetEnvelope`, `HumanActionRequest`.
- P2: domain `GovernanceProfile` may narrow runtime behavior and protected-resource access.
- P3: G2E owns semantic/scientific identity, evidence admission and adjudication; one exact G2E `ExecutionAttempt` may dispatch through at most one active GWF `WorkAssignment`.
- P4: PM is proposal/decomposition/escalation only and cannot direct-dispatch RemoteMCP.

P5 owns only environment-B physical/runtime materialization and operational provenance.

## 3. Canonical environment identity

The frozen environment type is:

`CHATGPT_WEB_REMOTEMCP`

Canonical worker app class:

`CHATGPT_WEB`

Canonical Web plugin identity:

`remote-mcp-v2-web-clean`

Canonical transport class:

`APP_BACKED`

The older `remote-mcp-v2-web` identity is legacy and forbidden as the canonical P5 route.

The backend tool namespace or display label is explicitly non-normative. It may differ while the logical P5 environment identity remains the same. Neither a namespace nor a connector label is authority.

A model/provider identity remains bound prospectively by G2E `AgentBinding` and GWF `ExecutorBinding`. P5 does not infer authority or independence from model strength/name.

## 4. Identity chain and non-collapse rule

The following identities remain distinct:

```text
G2E ExecutionAttempt
  -> GWF WorkAssignment
  -> GWF ExecutorBinding
  -> GWF ExecutionEnvironmentRef
  -> ChatGPTWebWorkerContextRef
  -> RemoteMCPExecutionPlacement
       -> device_id
       -> project_id
       -> task_id
       -> worktree/source state
       -> lease epoch
       -> durable job IDs
       -> checkpoint IDs
  -> ExecutionResultEnvelope
```

RemoteMCP device/project/task/job IDs are foreign runtime identities. They never replace:

- G2E `object_id/revision_id/content_hash`;
- GWF `work_assignment_id`;
- GWF `executor_binding_id`;
- GWF frozen hashes.

## 5. ChatGPTWebWorkerContextRef

P5 freezes a foreign worker-context reference rather than a new canonical agent authority object.

It must bind:

- an opaque worker context reference;
- the non-widening projection of the frozen G2E/GWF agent identity;
- the session binding class;
- the P5 execution environment identity.

Rules:

1. Chat/session/plugin attachment is operational state only.
2. Worker context does not create authority.
3. Backend namespace/display name does not define the worker identity.
4. Material worker/model/provider/harness substitution follows the P3 equivalence/replacement rule and cannot occur in place.

## 6. RemoteMCPExecutionPlacement

One active P5 placement revision binds an authorized Env-B dispatch to:

- exact WorkAssignment ID/revision/frozen hash;
- exact ExecutorBinding ID/resolved payload hash;
- exact ExecutionEnvironmentRef;
- exact worker context ref;
- `device_id`;
- device key fingerprint;
- route generation;
- RemoteMCP managed `project_id`;
- project binding generation;
- `task_id`;
- source/repository ref;
- base commit or source digest;
- branch ref;
- worktree ref for Git-backed mutable execution, or an explicitly qualified non-Git execution class.

Frozen rules:

- task inherits project-to-device placement;
- task may not override device or project identity;
- an approved existing project/device identity is reused rather than silently replaced;
- root mismatch fails closed;
- root mismatch does not authorize root widening, re-pairing, replacement device creation, or replacement project registration;
- one WorkAssignment dispatch has at most one active placement revision;
- placement may narrow but never widen WorkAssignment authority.

## 7. Lease semantics

RemoteMCP lease capability material is split into:

Durable observation:
- `task_id`;
- lease epoch;
- acquisition/expiry timestamps.

Ephemeral only:
- lease token.

Lease tokens may not be stored in:

- repository;
- task payload;
- job argv;
- logs;
- checkpoints;
- GWF durable evidence records;
- scientific lineage.

A new lease epoch during recovery does not by itself create a new scientific attempt, but lease reacquisition cannot authorize changed source state, changed placement, changed worker identity, expanded authority, or reset protected-resource state.

## 8. Durable job model

A P5 placement may execute zero or more bounded durable jobs.

Each job record binds:

- proxy job ID;
- node job ID when materialized;
- task/project/device;
- submitted argv hash;
- cwd/worktree;
- job state/timestamps;
- terminal event and exit/result provenance when terminal.

V1 freezes serial mutation within one task/worktree: at most one authoritative mutating job may be active.

Multiple operational jobs under one WorkAssignment are allowed for bounded implementation/measurement workflow steps. They must not silently become multiple scientific attempts.

A proxy record with no `node_job_id` proves only that a control-plane intent exists; it does not prove node execution.

## 9. Bounded authority projection

Effective P5 runtime authority is:

```text
intersection(
  WorkAssignment authority,
  ExecutorBinding authority,
  active GovernanceProfile,
  qualified execution-environment capability manifest,
  RemoteMCP placement policy,
  resolved HumanActionRequest constraints
)
```

The following do not create authority:

- technical plugin/tool capability;
- connector/account permission;
- worker prompt text;
- device ONLINE state;
- ability to invoke an arbitrary command;
- pairing ticket;
- browser/UI state.

Ordinary worker execution does not implicitly authorize:

- pair/re-pair/revoke;
- device restart;
- project register/bind;
- root widening;
- replacement device identity;
- replacement project identity.

Destructive/external actions, protected-resource access, authority expansion and budget expansion remain governed upstream.

## 10. Managed-execution preflight

Before any placement mutation or scientific relaunch, P5 implementation must start read-only where applicable:

1. inspect canonical session/plugin attachment;
2. `device_list`;
3. `device_status` on the intended existing device;
4. reuse existing project/task/device identity when already approved;
5. classify failure domain before mutation;
6. verify project exposure/root;
7. verify authoritative node capacity when execution is about to begin.

Frozen fail-closed classifications:

- canonical Web session/plugin unavailable -> `PLUGIN_SESSION_BINDING_FAILURE`;
- managed root mismatch -> `BLOCKED_ON_MANAGED_PROJECT_EXPOSURE_OR_EXPLICIT_DEDICATED_NODE_GATE`.

Neither condition authorizes node repair.

Task-scoped routed tools are required for execution provenance. Gateway-local compatibility commands cannot prove routed task execution.

## 11. Pairing and secret firewall

Pairing capability material is not authorization.

Pairing/re-pairing is excluded from ordinary P5 worker execution.

Forbidden secret transports include:

- run command;
- routed job;
- job argv;
- shell argument;
- task payload;
- repository;
- log;
- checkpoint;
- lineage.

Only dedicated managed/local secret-consumption paths may handle pairing secrets.

Connector/account secrets are also excluded from persisted P5 result/evidence payloads.

## 12. Recovery contract

### 12.1 Observability loss

Loss of status/result/log observability does not authorize resubmission or relaunch.

Required order:

```text
inspect existing task
 -> inspect routed-job registry
 -> inspect exact proxy/node job identity
 -> recover terminal evidence when possible
 -> classify unresolved provenance when not possible
 -> only then take a separately authorized recovery action
```

Scientific rerun is never inferred from operational uncertainty.

### 12.2 Proxy record without node execution

A queued proxy with `node_job_id = null` is an unresolved control-plane intent.

It must not cause blind duplicate submission.

The adapter must reconcile/cancel/terminalize it under explicit operational rules before issuing a semantically duplicate command.

### 12.3 Checkpoint/resume

A checkpoint freezes:

- exact G2E attempt ref;
- exact WorkAssignment ref;
- exact ExecutorBinding ref;
- exact placement ref;
- source/worktree state;
- prior job refs;
- protected-resource state;
- semantic-state digest.

Resume is admissible only when these identities remain compatible.

### 12.4 Restart

Restart is infrastructure governance, not automatic worker behavior.

If separately authorized:

- active jobs require explicit confirmation;
- after restart, verify the same device ID;
- verify the same key fingerprint;
- capture/validate route generation;
- revalidate source/worktree/checkpoint state;
- revalidate protected-resource state.

A material device/fingerprint/worker/source substitution requires a new governed binding/placement and, when material under P3 equivalence rules, a new G2E attempt.

### 12.5 Protected-resource uncertainty

P5 inherits P3:

`FRESH -> RESERVED -> EXPOSED`

No backward transition.

Uncertain access recovery is `EXPOSED_FAIL_CLOSED`.

## 13. ExecutionResultEnvelope

RemoteMCP output is normalized into an operational result envelope before any G2E evidence path.

Required provenance includes:

- exact G2E ExecutionAttempt ref;
- exact WorkAssignment ref;
- exact ExecutorBinding ref;
- ExecutionEnvironmentRef;
- worker context ref;
- placement exact ref;
- device ID/fingerprint/route generation;
- project ID/binding generation;
- task ID;
- source/worktree state;
- proxy job ID;
- node job ID;
- submitted argv hash;
- terminal event;
- terminal state;
- exit code;
- stdout/stderr refs + digests;
- artifact refs + digests;
- checkpoint ref if any;
- environment attestation ref;
- protected-resource state.

Allowed operational status values:

- `OPERATIONAL_SUCCEEDED`;
- `OPERATIONAL_FAILED`;
- `BLOCKED`;
- `CANCELLED`;
- `UNRESOLVED_PROVENANCE`.

The envelope is not an admitted scientific EvidenceRecord.

## 14. Evidence-return firewall

Frozen semantics:

```text
RemoteMCP logs/artifacts/result
 -> P5 provenance + digest normalization
 -> operational ExecutionResultEnvelope
 -> candidate evidence bridge
 -> G2E EvidenceAdmissionPolicy
 -> ADMITTED / REJECTED / INVALIDATED
 -> adjudication
```

Therefore:

- `exit_code = 0` does not mean ADMITTED;
- `OPERATIONAL_SUCCEEDED` does not mean PASS;
- raw stdout/stderr is not admitted evidence;
- artifact existence without digest/provenance is insufficient;
- evidence from a wrong attempt/assignment/task is rejected;
- terminal result without independently retrievable provenance cannot satisfy the frozen completion/evidence-return contract.

## 15. Operational failure and lineage

RemoteMCP/plugin/session/node/project/task/job failures are operational facts.

They do not automatically create:

- scientific FAIL;
- scientific PASS;
- claim resolution;
- evidence admission.

Infrastructure repair records do not enter scientific `LINEAGE.md` by default.

## 16. Frozen cardinalities

- 1 authorized Env-B WorkAssignment -> exactly 1 resolved ExecutorBinding for dispatch.
- 1 ExecutorBinding -> exactly 1 qualified `CHATGPT_WEB_REMOTEMCP` ExecutionEnvironmentRef.
- 1 WorkAssignment dispatch -> 0..1 active P5 placement revision.
- 1 placement -> exactly 1 device + 1 managed project + 1 task.
- Git-backed mutable placement -> exactly 1 source/worktree binding.
- 1 task -> 0..N bounded operational durable jobs.
- v1 -> at most 1 authoritative mutating job active in one task/worktree.
- 1 materialized job -> exactly 1 proxy ID + exactly 1 node-job ID.
- 1 checkpoint -> exactly 1 placement revision.
- 1 terminal job -> 0..1 normalized result envelope.

## 17. Preregistered negative-test matrix

Exactly **56** negative tests are frozen before implementation:

1. canonical plugin missing cannot fall back to legacy Web route;
2. plugin/session failure cannot trigger node repair;
3. backend namespace/display label cannot become environment identity;
4. worker context mismatch with ExecutorBinding fails;
5. material worker identity substitution cannot reuse binding/attempt in place;
6. device ID substitution fails;
7. device fingerprint substitution fails;
8. unapproved route-generation change fails;
9. project ID substitution fails;
10. project binding-generation substitution fails;
11. project-root mismatch cannot widen root;
12. root mismatch cannot create replacement device/project;
13. task cannot override project device placement;
14. task cannot override project identity;
15. Git source/worktree/base mismatch fails;
16. gateway-local compatibility command cannot prove routed execution;
17. lease-token persistence fails;
18. pairing secret in task/job/repository fails;
19. connector secret in log/checkpoint/evidence fails;
20. stale lease epoch mutation fails;
21. routed job submit without current task lease fails;
22. job bound to wrong task/project/device fails;
23. proxy/node-job provenance mismatch fails;
24. submitted argv hash mismatch fails;
25. second active mutating job in same task fails;
26. duplicate scientific command after observability loss fails;
27. technical capability cannot expand authority;
28. connector/account permission cannot expand authority;
29. worker prompt cannot expand authority;
30. task capability beyond WorkAssignment fails;
31. destructive/external action without authority fails;
32. pair/re-pair/revoke cannot come from ordinary worker authority;
33. device restart cannot come from ordinary worker authority;
34. restart with active jobs without explicit confirmation fails;
35. project register/bind/root widening cannot be implicit;
36. adapter cannot widen budget/profile/protected policy;
37. observability loss cannot relaunch scientific job;
38. proxy with no node-job ID cannot cause blind duplicate submission;
39. unknown/nonterminal job cannot be replaced before reconciliation;
40. recovery to different task/worktree/source state fails;
41. checkpoint exact-ref mismatch fails;
42. recovery cannot roll protected resource EXPOSED backward;
43. device/fingerprint material change requires governed rebind;
44. operational failure cannot become scientific FAIL;
45. runtime success cannot become evidence ADMITTED;
46. runtime success cannot become scientific PASS;
47. result envelope missing exact provenance is rejected;
48. artifact/log digest mismatch is rejected;
49. raw log cannot become evidence without normalization/admission;
50. result from wrong WorkAssignment/attempt is rejected;
51. terminal result not independently retrievable is insufficient;
52. secret material in result envelope is rejected;
53. worker cannot rewrite terminal adjudication;
54. PM cannot direct-dispatch through RemoteMCP;
55. RemoteMCP cannot create a replacement G2E attempt;
56. P5 qualification cannot run a real project, consume protected evidence, or import the P6 route.

The machine-readable manifest contains the exact symbolic IDs for the same 56 tests.

## 18. Implementation lock for this gate

Allowed now:

- P5 environment manifest;
- this normative preregistration;
- contract consistency QA/formal decision;
- vNext plan frontier update.

Forbidden now:

- source/runtime mutation;
- RemoteMCP adapter implementation;
- ChatGPT Web worker runtime binding;
- P5 real device/job execution for qualification;
- real research/software project execution;
- protected evidence consumption;
- Codex/CGW P6 adapter work;
- Mission Control UI refactor;
- P6+ implementation.

## 19. Contract-freeze decision criteria

The P5 contract may freeze only if:

- all P1-P4 execution locks remain unchanged;
- environment B remains distinct from Codex/CGW environment A;
- no RemoteMCP runtime ID replaces G2E/GWF canonical identity;
- worker identity projection is non-widening;
- WorkAssignment -> placement -> job provenance is reconstructable;
- authority projection is intersection/narrowing only;
- secrets cannot persist through task/job/checkpoint/evidence paths;
- scientific continuity forbids blind relaunch;
- protected-resource monotonicity is preserved;
- evidence return remains candidate-only until G2E admission;
- all 56 negative tests are specified before implementation;
- diff scope is documentation/contract only.

## 20. Next gate after formal close

If this contract passes static review and formal close, the only authorized successor is:

`GWF_VNEXT_P5_CHATGPT_WEB_REMOTEMCP_EXECUTION_ENVIRONMENT_IMPLEMENTATION_STATIC_PREFLIGHT_AND_EXECUTION_LOCK`

That successor may implement and qualify the P5 adapter against synthetic/zero-science fixtures.

It still must not open a real project pilot, protected evidence, P6, P8, P9 or P10.
