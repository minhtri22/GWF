# GWF vNext P0 — Architecture and Identity Reconciliation QA

**Gate:** `GWF_VNEXT_P0_ARCHITECTURE_AND_IDENTITY_RECONCILIATION`  
**Candidate:** `f43bd6ea61447230253e8a613cbed09f4c6a5b02`  
**Date:** 2026-10-07  
**Verdict:** **PASS**  
**OPEN findings:** **0**

## 1. Scope reviewed

Reviewed against:

- pivot plan `docs/pivot/GWF_AUTONOMOUS_RESEARCH_STACK_VNEXT_PLAN.md`;
- GWF Agent Interoperability design `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md`;
- current `domains/research.workflow.yaml`;
- current `domains/software.workflow.yaml`;
- G2E `README.md`, Core Semantics, PRD-07, PRD-08 and PRD-09 on the inspected G2E research line;
- actual G2E P1.4/P5A identity model previously qualified on that line;
- canonical RemoteMCP Web execution identity and managed-execution policy.

No runtime/code/UI implementation was authorized or modified by P0.

## 2. Findings

### P0-F01 — G2E/GWF `AgentBinding` name collision

**Observed**

G2E already uses `AgentBinding` as a canonical semantic object bound to one proof attempt. GWF v0.8.7 separately planned a future `AgentBinding` for runtime executor assignment.

**Risk**

Two canonical objects with the same name but different authority would create ambiguous source of truth.

**Resolution**

- G2E retains `AgentBinding`.
- GWF vNext runtime object is named `ExecutorBinding`.
- RemoteMCP task/placement identity is not a binding replacement.

**Status:** CLOSED.

### P0-F02 — ExecutionAttempt / AgentExecutionEnvelope conflation

**Observed**

G2E `ExecutionAttempt` is a semantic proof-execution identity. GWF planned `AgentExecutionEnvelope` is execution evidence/runtime metadata.

**Resolution**

- G2E `ExecutionAttempt` remains canonical for proof-attempt semantics.
- GWF may retain an execution-envelope concept only as runtime evidence/mapping.
- executor success does not imply G2E PASS.

**Status:** CLOSED.

### P0-F03 — RemoteMCP misclassification as generic agent

**Observed**

RemoteMCP exposes device/project/task/worktree/lease/job semantics. Those are placement/runtime semantics, not Goal/Claim/Proof semantics.

**Resolution**

RemoteMCP is frozen as Env-B internal execution substrate for ChatGPT Web workers.

**Status:** CLOSED.

### P0-F04 — Two MCP environments could be accidentally merged

**Observed**

Env A and Env B both involve MCP-shaped transport but differ in executor, authority and lifecycle.

**Resolution**

A canonical non-equivalence invariant now states that shared protocol does not imply shared executor, authority, identity, lifecycle or evidence semantics.

**Status:** CLOSED.

### P0-F05 — PM authority ambiguity

**Observed**

A ChatGPT App PM can reason across projects and propose next work, but treating PM output as authority would bypass G2E/GWF.

**Resolution**

PM is proposal/prioritization authority only. G2E owns proof semantics; GWF owns execution/governance authorization.

**Status:** CLOSED.

### P0-F06 — QA independence inferred from model difference

**Observed**

Astra/Sol role separation could be misread as automatic independent QA.

**Resolution**

Independence is prospectively defined by `IndependencePolicy`; model/provider/harness separation is required only when frozen by that policy.

**Status:** CLOSED.

### P0-F07 — Research governance leakage into GWF core

**Observed**

The existing research package contains study-lock and confirmatory semantics that must not become universal runtime defaults.

**Resolution**

`GovernanceProfile` is generic in GWF core; actual research profiles are domain-owned. Software remains separate.

**Status:** CLOSED.

### P0-F08 — Operational failure contaminating scientific lineage

**Observed**

Remote execution can fail for process/network/device/disk/parser/routing reasons.

**Resolution**

P0 freezes top-level failure taxonomy and prohibits automatic scientific PASS/FAIL from operational failures.

**Status:** CLOSED.

### P0-F09 — UI-centered execution assumption

**Observed**

Current BPS sequencing can encourage a manual workflow-product mental model.

**Resolution**

vNext freezes the headless invariant and reclassifies browser UI as Mission Control. Manual Create Execution is not the primary abstraction.

**Status:** CLOSED.

### P0-F10 — Whole-branch G2E merge risk

**Observed**

The current G2E research line contains canonical core work mixed with P5A/CGW transport-study history.

**Resolution**

PIVOT-P3 must classify and selectively import canonical core/reusable adapters/qualification tests only. Historical research/transport lineage remains on its existing line.

**Status:** CLOSED.

## 3. Exit criteria

| Criterion | Result |
| --- | --- |
| Ownership collision G2E/GWF/RemoteMCP closed | PASS |
| G2E AgentBinding vs GWF ExecutorBinding distinct | PASS |
| RemoteMCP IDs classified as foreign runtime placement | PASS |
| PM/worker/QA role vs identity split | PASS |
| QA independence policy-driven | PASS |
| Env A vs Env B non-equivalence explicit | PASS |
| Research/software package boundary intact | PASS |
| GovernanceProfile domain-owned/core-evaluated | PASS |
| Headless invariant testable | PASS |
| UI non-authoritative | PASS |
| Old-plan disposition explicit | PASS |
| No implementation opened in P0 | PASS |

## 4. P0 formal disposition

```text
GWF_VNEXT_P0_ARCHITECTURE_AND_IDENTITY_RECONCILIATION
= PASS
= FORMALLY CLOSED
```

P0 establishes architecture/identity authority only.

It does **not** claim that any new runtime primitive has been implemented.

## 5. Next authorized frontier

The next bounded phase is:

```text
GWF_VNEXT_P1_GOVERNANCE_KERNEL_PREREGISTRATION_AND_CONTRACT_FREEZE
```

P1 may specify/freeze generic provider-neutral contracts for:

- GovernanceProfile;
- GovernanceTransitionProposal;
- WorkAssignment;
- HumanActionRequest;
- ExecutorBinding;
- ExecutionEnvironment reference;
- budget/authority overlays.

P1 MUST NOT yet implement:

- RemoteMCP-specific adapter behavior;
- Codex-specific adapter behavior;
- G2E code import;
- research profile implementation;
- Mission Control UI.
