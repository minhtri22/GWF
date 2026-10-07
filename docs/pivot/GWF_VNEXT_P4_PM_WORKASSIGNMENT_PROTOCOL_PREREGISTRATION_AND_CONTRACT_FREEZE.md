# GWF vNext P4 — PM WorkAssignment Protocol Preregistration and Contract Freeze

Gate: `GWF_VNEXT_P4_PM_WORKASSIGNMENT_PROTOCOL_PREREGISTRATION_AND_CONTRACT_FREEZE`  
Date: 2026-10-07  
Base: `pivot/gwf-autonomous-research-stack-v1@6f580e240be9a4f7a61023e4e6872a473b316fef`

## Authority boundary

```text
PM != authority
G2E = semantic/scientific authority
GWF = governance authorization + durable runtime authority
```

P4 freezes a provider-neutral PM proposal protocol only. It does not implement runtime execution.

Preserved lock blobs: P1 `ecfc8435f0f381d0a2edfac8575cbbc09a87abe3`; P2 `25660c52526923d557224ac9fbc9abeae23adcc4`; P3 `60aa70e8f03a2c4f11e5693bf58cf82b5806b24e`.

## Frozen objects

- `PMVisibleGovernedState`: immutable GWF read-model; protected-resource metadata only, never protected payload.
- `PMPlanRevision`: `plan_id + revision_id + content_hash`; normative change creates a new revision.
- `PMRoleRequest`: provider-neutral `WORKER` or `QA_REVIEWER`; QA binds frozen independence requirements.
- `WorkAssignmentProposal`: `proposal_id + revision_id + content_hash`; lifecycle `DRAFT -> FROZEN -> SUBMITTED -> REJECTED|ESCALATED|AUTHORIZED_MATERIALIZED`; submitted revisions are immutable.
- `PMHandoffRecord`: durable handoff/recovery identity preserving exact proposal refs and governed-state revision.

P4 reuses the existing P1 `WorkAssignment`; redefining it is forbidden.

## Cardinality

- one exact proposal revision -> zero or one authorized WorkAssignment;
- each P4-derived authorized WorkAssignment -> exactly one source proposal revision;
- one G2E ExecutionAttempt -> at most one active GWF WorkAssignment dispatch, preserving P3;
- one proposal ID may have append-only revisions, at most one active/authorized revision.

## Materialization

Only GWF authorization may materialize a proposal. It must validate governed-state revision, G2E exact refs, active GovernanceProfile, AuthorityEnvelope, BudgetEnvelope, ProtectedResource policy, P3 dispatch cardinality, HumanActionRequest state, and QA IndependencePolicy.

## PM permissions and prohibitions

PM may read governed state, decompose work, propose assignments/roles/environment classes, request escalation, track progress, and create handoff records.

PM may not create/expand authority or budget; consume protected evidence; admit evidence; create scientific verdict or release acceptance; mutate frozen WorkAssignment/ProofObligation/GovernanceProfile; directly dispatch runtime before authorization; override G2E AgentBinding or GWF ExecutorBinding; infer independence from model/provider difference; downgrade profile to escape a blocker; reinterpret terminal lineage; change frozen threshold/metric/seed; use model strength or UI state as authority.

## Staleness and recovery

A proposal binds the governed-state revision used for planning. Material state change makes it stale; it must be rejected or revalidated as a new revision. Handoff/recovery cannot silently change proposal identity.

## Execution-environment scope

P4 permits class/capability requests only. RemoteMCP adapter, Codex adapter, provider/model-specific runtime binding, Mission Control refactor, real project execution, and protected evidence consumption remain forbidden.

## Negative tests and exit

Exactly 36 negative tests N01–N36 are frozen in the P4 manifest before implementation. They cannot be weakened after results are observed.

On contract PASS, the only next gate is `GWF_VNEXT_P4_PM_WORKASSIGNMENT_PROTOCOL_IMPLEMENTATION_STATIC_PREFLIGHT_AND_EXECUTION_LOCK`, limited to provider-neutral implementation, zero-science/static fixtures, lock-preservation regressions, and exact hash binding.