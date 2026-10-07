# GWF vNext P0 — Architecture and Identity Reconciliation

**Gate:** `GWF_VNEXT_P0_ARCHITECTURE_AND_IDENTITY_RECONCILIATION`  
**Status:** FROZEN CANDIDATE  
**Pivot branch:** `pivot/gwf-autonomous-research-stack-v1`  
**Pivot base:** `feature/bps-i00-product-shell@de3247c18c1a8546db9611ecd0fdf24f827662ae`  
**G2E reference line inspected:** `research/p5a-cgw-fx001-transport-corrected@d2ba5a123e2fbefd0138d3f1a7a0dd81373e5b87`  
**RemoteMCP canonical Web identity:** `remote-mcp-v2-web-clean`  
**Date:** 2026-10-07

## 1. Decision

GWF vNext is not a workflow SaaS and not a UI-first orchestrator.

It is the governance and durable-state layer in an autonomous research/software stack where:

- **G2E** owns proof semantics;
- **GWF** owns governance, durable authority state and runtime mappings;
- **domain packages** own domain-specific governance profiles and semantics;
- **agent environments** execute authorized work;
- **RemoteMCP** is an internal execution bridge for ChatGPT Web agents only;
- **the browser UI** is Mission Control for observation and human authority, not a required execution path.

The stack MUST be fully operable headlessly.

## 2. Canonical stack boundary

```text
                         HUMAN / PRINCIPAL
                    goal + authority + limits
                              |
                              v
                   ChatGPT App PM (Astra)
                              |
                    proposal / prioritization
                              |
                  +-----------+-----------+
                  |                       |
                  v                       v
                G2E                      GWF
          proof semantics          governance runtime
          what remains             what is allowed
          unproven?                and persisted?
                  |                       |
                  +-----------+-----------+
                              |
                       WorkAssignment
                              |
                 +------------+------------+
                 |                         |
                 v                         v
      EXECUTION ENVIRONMENT A    EXECUTION ENVIRONMENT B
      Codex / CGW route          ChatGPT Web / RemoteMCP
                 |                         |
                 v                         v
          candidate evidence          candidate evidence
                 |                         |
                 +------------+------------+
                              |
                              v
                       GWF persistence
                              |
                              v
                    G2E admission / QA /
                    adjudication / next
```

No arrow in this diagram implies that one layer owns the semantics of another.

## 3. Ownership matrix

| Concern | Canonical owner | May persist/map | Must not own |
| --- | --- | --- | --- |
| Goal semantics | G2E | GWF | RemoteMCP, UI |
| Claim semantics | G2E | GWF | RemoteMCP, UI |
| ProofObligation | G2E | GWF | RemoteMCP |
| EvidenceAdmission | G2E | GWF | executor |
| Adjudication semantics | G2E | GWF stores result | executor, RemoteMCP |
| Goal/Claim verdict | G2E | GWF stores result | PM, worker, UI |
| Governance policy | GWF core + domain package | GWF | executor |
| GovernanceProfile definition | domain package | GWF resolves effective policy | G2E core, RemoteMCP |
| Human authority | GWF | UI renders/acts through governed command | transport |
| Budget / authority ceiling | GWF | WorkAssignment | worker |
| Agent-app semantic binding for a proof attempt | G2E | GWF maps | RemoteMCP |
| Runtime executor binding | GWF | adapter/runtime | G2E canonical identity |
| Physical execution placement | execution environment adapter; RemoteMCP for Env B | GWF foreign refs | G2E semantic identity |
| Device/project/task/worktree/job | RemoteMCP for Env B | GWF foreign refs | G2E |
| Codex thread/turn | Codex adapter for Env A | GWF/G2E foreign refs | RemoteMCP |
| CGW route/browser/tool trace | Env A adapter | evidence refs | GWF authority |
| PM planning recommendation | PM agent | GWF proposal record | final authority |
| QA analysis/recomputation | QA agent/process | G2E evidence | final authority unless frozen rule says so |
| Deterministic verdict application | G2E adjudicator | GWF persistence | PM/worker |
| Browser presentation | GWF UI | none beyond governed commands | semantic/runtime authority |

## 4. Identity namespaces

The following identities are distinct and MUST NOT be overloaded.

### 4.1 G2E semantic identities

G2E owns canonical proof-program identities such as:

- `goal_id`;
- `claim_id`;
- `proof_obligation_id`;
- `attempt_id`;
- `evidence_id`;
- G2E `AgentBinding` identity;
- G2E canonical content hashes.

A G2E `AgentBinding` answers:

> What agent-app/harness/provider/model/transport identity and capabilities are prospectively bound to this proof attempt under the frozen equivalence/independence policy?

It does not identify a RemoteMCP task or physical machine.

### 4.2 GWF governance/runtime identities

GWF vNext will use separate names:

- `work_assignment_id`;
- `executor_binding_id`;
- `execution_environment_id`;
- `governance_profile_ref`;
- `human_action_request_id`;
- existing GWF project/orchestration/workunit/runtime IDs where retained.

A GWF `ExecutorBinding` answers:

> Which qualified executor/environment is authorized to materialize this work, under what authority, budget and runtime policy?

GWF MUST NOT introduce a second type named `AgentBinding`.

### 4.3 Execution-environment foreign identities

Environment A may contribute:

- Codex session/thread/turn IDs;
- CGW trace IDs;
- browser-turn IDs;
- tunnel/MCP invocation IDs.

Environment B may contribute:

- ChatGPT agent/context identity;
- RemoteMCP `device_id`;
- `project_id`;
- `task_id`;
- lease epoch;
- `job_id` / proxy job ID;
- worktree path/ref;
- checkpoint refs.

These are foreign/runtime identities. They map to a GWF execution record and ultimately a G2E attempt when applicable. They never replace the G2E/GWF canonical IDs.

## 5. Identity chain

A reconstructable research execution should look conceptually like:

```text
goal_id
  -> claim_id
  -> proof_obligation_id
  -> g2e_attempt_id
  -> work_assignment_id
  -> executor_binding_id
  -> execution_environment_id
       |
       +-- Env A:
       |     codex_thread_id
       |     codex_turn_id
       |     cgw_trace_id
       |     mcp_invocation_id
       |
       +-- Env B:
             chatgpt_worker_context
             remotemcp_device_id
             remotemcp_project_id
             remotemcp_task_id
             remotemcp_job_id
  -> candidate_evidence_refs
  -> evidence_admission
  -> adjudication
```

Every mapping is explicit and attributable.

## 6. PM, worker and QA identity

Do not use one generic `agent` field to collapse roles.

Minimum conceptual separation:

```text
AgentRole
AgentIdentity
ExecutionEnvironment
ExecutionContext
ExecutionPlacement
```

### PM target

```text
role                = portfolio_pm
app                 = chatgpt_app
model               = GPT-6 Astra
execution_context   = PM context
placement           = none / app-native
```

PM authority:

- read governed state;
- propose priorities;
- propose WorkAssignments;
- propose governance transitions;
- request/escalate human actions.

PM may not:

- rewrite frozen G2E semantics;
- consume protected evidence without authorization;
- rewrite terminal verdicts;
- bypass GWF authority;
- silently mutate scientific lineage.

### Worker target examples

Environment B:

```text
role                = research_executor | software_executor | ...
app                 = chatgpt_web
model               = GPT-5.6 Sol or another qualified model
execution_environment = CHATGPT_WEB_REMOTEMCP
placement           = RemoteMCP device/project/task/worktree/job
```

Environment A:

```text
role                = executor
app                 = codex
execution_environment = CODEX_CGW
placement           = Codex/CGW route-specific identities
```

### QA reviewer

A QA reviewer may use Astra or Sol, including the same model family as another role, when the frozen `IndependencePolicy` permits it.

Independence is defined prospectively over dimensions such as:

- separate context;
- separate attempt;
- prior-chat isolation;
- read-only evidence;
- source-blind recomputation;
- implementation-author separation;
- model separation;
- harness separation;
- provider separation;
- environment separation.

`different model` is not sufficient proof of independence.  
`same model` is not sufficient proof of non-independence.

## 7. Execution environment A — Codex / CGW

Canonical route:

```text
G2E authorized attempt
   -> GWF runtime mapping
   -> Codex outer harness
   -> CGW
   -> ChatGPT Web inference
   -> route-specific tunnel
   -> route-specific MCP/tool surface
   -> Codex result/evidence
```

Frozen boundary decisions:

1. Codex is the outer execution harness.
2. CGW is transport/inference mediation, not governance authority.
3. ChatGPT Web in this route is inference plus admitted tool requests.
4. The tunnel/MCP is specific to this environment.
5. RemoteMCP MUST NOT be inserted into this route merely because both systems use MCP.
6. Existing G2E P5A transport research remains historical evidence; it is not wholesale-imported into vNext.
7. Any future vNext Codex adapter imports only qualified reusable contracts/code with exact provenance.

## 8. Execution environment B — ChatGPT Web / RemoteMCP

Canonical route:

```text
GWF-authorized WorkAssignment
   -> ChatGPT Web worker context
   -> RemoteMCP
   -> exact device
   -> exact managed project
   -> task/worktree
   -> lease
   -> durable job/checkpoint/resume
   -> execution result/evidence
```

Frozen boundary decisions:

1. ChatGPT Web agent is the worker.
2. RemoteMCP is the internal execution bridge/substrate.
3. RemoteMCP does not own scientific semantics or verdicts.
4. RemoteMCP project/task/job state is operational runtime state.
5. RemoteMCP operational failure is not scientific FAIL.
6. GWF stores RemoteMCP identities as foreign runtime mappings.
7. A RemoteMCP task may carry only authority equal to or narrower than its parent WorkAssignment.
8. Pairing/device identity is infrastructure governance and must never become scientific evidence by implication.

## 9. MCP non-equivalence invariant

The two MCP uses are explicitly non-equivalent.

```text
Env A MCP:
  route-specific delegated tool surface inside the Codex/CGW execution path

Env B RemoteMCP:
  internal execution substrate used directly by ChatGPT Web workers
```

Therefore:

```text
same protocol family
!= same authority
!= same executor
!= same identity
!= same lifecycle
!= same evidence semantics
```

This invariant is mandatory in vNext.

## 10. GovernanceProfile ownership

`GovernanceProfile` is a GWF core primitive whose **profile definitions are domain-owned**.

GWF core owns only generic policy fields and evaluation.

Research package will define at least:

- `research.triage`;
- `research.exploratory`;
- `research.measurement`;
- `research.confirmatory`.

Software package defines separate software profiles.

GWF core MUST NOT hard-code research concepts such as hypothesis, preregistration or scientific TEST.

## 11. Research package reconciliation

The existing `domains/research.workflow.yaml` encodes strong confirmatory-style governance across much of the full cycle, including:

- `study_lock`;
- fresh-data policy;
- frozen metrics/gates;
- forbidden adaptations;
- repair budget;
- no-rescue policy;
- independent/adversarial review.

vNext does not delete these semantics.

Instead, PIVOT-P2 will refactor them into policy overlays so that:

- TRIAGE is operationally free but scientifically non-claiming;
- EXPLORATORY permits broad search/mutation but low claim authority;
- MEASUREMENT freezes measurement semantics;
- CONFIRMATORY retains the current strict proof discipline.

The old domain remains historical/current-product behavior until vNext migration is explicitly implemented.

## 12. Software package reconciliation

Software remains a separate domain package.

It may define its own profiles such as development/qualification/release, but these names and semantics are not frozen by P0.

Research-specific profiles MUST NOT leak into software core behavior.

## 13. WorkAssignment contract boundary

P0 freezes only the ownership and conceptual contract, not the schema implementation.

A future `WorkAssignment` will minimally bind:

- project;
- originating goal/claim/proof/work reference;
- objective;
- role;
- execution environment;
- required capabilities;
- authority scope;
- budget;
- protected-resource constraints;
- expected outputs/evidence;
- completion/handoff contract;
- QA/independence requirements when applicable.

PMs propose WorkAssignments. GWF authorizes them.

A WorkAssignment is not a G2E ProofObligation and is not a RemoteMCP task.

## 14. HumanActionRequest boundary

Human-required decisions MUST be durable governed objects, not browser-only prompts.

Examples:

- protected evidence consumption;
- confirmatory transition;
- claim elevation;
- destructive external action;
- authority expansion;
- budget expansion.

The UI renders and resolves these through normal GWF authority checks.

## 15. State namespace reconciliation

These states must remain orthogonal:

| Namespace | Example states | Owner |
| --- | --- | --- |
| G2E Goal | IN_PROGRESS / ACHIEVED / FALSIFIED / UNRESOLVED / STOPPED | G2E |
| G2E Claim resolution | UNKNOWN / PASS / FAIL / UNRESOLVED | G2E |
| G2E ExecutionAttempt | CREATED / PREFLIGHT / LOCKED / RUNNING / COMPLETED / EXECUTOR_FAILED / ... | G2E execution semantics |
| G2E Adjudication | PASS / FAIL / INVALID / UNRESOLVED | G2E |
| GWF WorkAssignment | future runtime states; not frozen in P0 | GWF |
| GWF Governance transition | AUTO_ALLOWED / HUMAN_APPROVAL_REQUIRED / FORBIDDEN / SUCCESSOR_REQUIRED | GWF |
| RemoteMCP task/job | READY / RUNNING / RECOVERABLE / terminal operational states | RemoteMCP |
| UI rendering | loading / empty / partial / error / unauthorized | UI only |

No automatic mapping such as `RemoteMCP job SUCCEEDED -> G2E PASS` is permitted.

## 16. Authority lattice

Authority may only narrow as it descends.

```text
Human / project authority
        >= GWF effective policy
        >= WorkAssignment authority
        >= ExecutorBinding authority
        >= execution-environment delegated authority
        >= child/delegated worker authority
```

For Env A, the existing G2E route invariant is preserved conceptually:

```text
delegated tool authority <= outer Codex turn authority <= G2E attempt authority
```

For Env B:

```text
RemoteMCP task/job authority <= WorkAssignment authority <= GWF effective authority
```

No transport can create authority.

## 17. Failure taxonomy

P0 freezes a minimum top-level distinction:

```text
OPERATIONAL / INFRASTRUCTURE
  process, network, device, disk, timeout, dependency, parser, routing

EXECUTION CONTRACT
  wrong executor, authority mismatch, protocol mismatch, artifact invalidity

SCIENTIFIC / DOMAIN SUBSTANTIVE
  valid evidence violates or satisfies frozen proof rule
```

Operational failures:

- do not create scientific PASS/FAIL;
- do not enter scientific lineage unless the domain protocol explicitly defines them as material evidence;
- may authorize bounded retry/recovery only under the governing policy.

## 18. Old-plan to vNext disposition matrix

| Existing capability/plan item | vNext disposition |
| --- | --- |
| GWF persistence / governed state | RETAIN |
| exact revision/hash provenance | RETAIN |
| authority/approval primitives | RETAIN + GENERALIZE |
| recovery/handoff/checkpoint | RETAIN |
| GitHub SHA-safe writes | RETAIN |
| Documentation Governance | RETAIN AS PACKAGE/CAPABILITY; not the vNext sequencing spine |
| Governed Artifact Catalog | RETAIN; integrate when required by G2E/library needs |
| Reference Acquisition | RETAIN as research-side capability |
| Agent Interoperability concepts | RECONCILE/RENAME; do not implement old `AgentBinding` name in GWF |
| old GWF `AgentBinding` planned type | SUPERSEDE NAME with `ExecutorBinding` |
| AgentExecutionEnvelope | RETAIN CONCEPT, reconcile with G2E attempt/result mapping |
| Browser Product Surface current implementation | PRESERVE CURRENT PRODUCT; reuse selectively in Mission Control |
| BPS sequential module roadmap | SUPERSEDED FOR vNext sequencing |
| manual Create Execution as primary UX | REJECT AS PRIMARY ABSTRACTION |
| G2E core semantics | RETAIN EXTERNALLY; PIVOT-P3 import/reconcile selectively |
| G2E P5A transport-study lineage | PRESERVE IN G2E RESEARCH LINE; DO NOT MERGE WHOLESALE |
| Codex adapter route | RETAIN AS SEPARATE EXECUTION ENVIRONMENT |
| RemoteMCP | ADD AS ENV-B EXECUTION SUBSTRATE, not G2E semantic layer |
| research.workflow.yaml strict study lock | RETAIN semantics, later profile-ize |
| software.workflow.yaml | RETAIN separate domain |

## 19. Package ownership map

```text
src/gwr/
  generic governance kernel
  persistence
  authority
  budgets
  runtime mappings
  transition evaluation
  WorkAssignment/HumanActionRequest/ExecutorBinding primitives

domains/research.*
  research GovernanceProfiles
  research-specific mutation/claim/evidence policy
  research lineage rules

domains/software.*
  software GovernanceProfiles
  software-specific delivery/release policy

g2e/
  canonical proof semantics and adapters when selectively imported
  remains logically separable from GWF core

execution adapters/
  Env A: Codex/CGW
  Env B: ChatGPT Web/RemoteMCP

web/
  Mission Control projection + governed human actions
  no independent authority
```

P0 does not authorize moving files yet.

## 20. Headless invariant

Before Mission Control implementation, PIVOT-P8 must prove a complete loop without browser interaction:

```text
Goal
 -> ProofObligation
 -> GWF authorization
 -> WorkAssignment
 -> executor selection
 -> execution
 -> candidate evidence
 -> independent QA when required
 -> admission/adjudication
 -> next obligation
```

Any capability that only exists as a browser click and cannot be represented as durable governed state is architecturally incomplete.

## 21. Explicit non-goals of P0

P0 does not authorize:

- implementation of GovernanceProfile;
- implementation of WorkAssignment;
- implementation of HumanActionRequest;
- RemoteMCP adapter code;
- Codex adapter changes;
- G2E code import/merge;
- research.workflow.yaml mutation;
- software.workflow.yaml mutation;
- browser refactor;
- real project execution;
- fresh/protected TEST consumption;
- pairing/re-pairing RemoteMCP devices;
- migration of current BPS users/state.

## 22. P0 exit criteria

P0 may PASS only if all are true:

1. G2E/GWF/RemoteMCP ownership has no unresolved collision.
2. G2E `AgentBinding` and GWF runtime binding have distinct names/semantics.
3. RemoteMCP placement identities are explicitly foreign runtime identities.
4. PM/worker/QA roles are distinct from model/app/harness identity.
5. Independence is policy-driven rather than inferred from model difference.
6. Env A and Env B remain non-equivalent despite MCP usage.
7. research/software package boundary remains intact.
8. GovernanceProfile ownership is domain-defined/core-evaluated.
9. headless invariant is testable.
10. UI is non-authoritative.
11. old-plan disposition is explicit.
12. implementation remains unopened until P1 authorization.
