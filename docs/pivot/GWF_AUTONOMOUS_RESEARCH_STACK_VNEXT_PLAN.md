# GWF vNext — Autonomous Research Stack Pivot Plan

**Status:** PIVOT-P0 PASS / PIVOT-P1 PASS+LOCKED / PIVOT-P2 PASS+LOCKED / PIVOT-P3 contract freeze PASS / PIVOT-P3 implementation preflight authorized  
**Pivot branch:** `pivot/gwf-autonomous-research-stack-v1`  
**Pivot base:** `feature/bps-i00-product-shell@de3247c18c1a8546db9611ecd0fdf24f827662ae`  
**Date:** 2026-10-07

## 1. Purpose

GWF vNext is a pivot from a workflow-product-first implementation toward an autonomous research governance stack.

The target stack is:

- **G2E** — proof reasoning: Goal -> Claim -> ProofObligation -> Evidence -> Adjudication -> Next admissible proof.
- **GWF** — governance runtime and durable system of record: authority, policy, budgets, protected resources, lineage, approvals, persistence, transitions.
- **Execution environments** — independent executor families selected prospectively under GWF/G2E policy.
- **RemoteMCP** — internal execution bridge for ChatGPT Web agents working on real devices/projects/tasks/worktrees/jobs.
- **Browser UI** — Mission Control / observation + authority surface; never required for headless execution.

The current GWF product line remains preserved independently. This branch is not a replacement migration and must not mutate the current product line by implication.

## 2. Non-negotiable architectural invariants

1. **Headless-first:** the complete governed research loop must run without the browser UI.
2. **UI is not the workflow engine:** the UI observes, pauses, stops, changes authority/budget/governance profile, and approves claim-elevating actions.
3. **Transport is not authority:** two systems using MCP are not the same execution environment.
4. **G2E semantics stay independent:** GWF may persist/enforce G2E objects but must not redefine Goal/Claim/Proof/Evidence/Adjudication semantics.
5. **Research and software remain separate domain packages.**
6. **Operational failure is not scientific failure:** infrastructure/code/runtime repair records must not pollute scientific lineage.
7. **Scientific lineage is append-only:** PASS/FAIL/UNRESOLVED and spent/closed scientific outcomes are immutable.
8. **No-rescue:** a failed/consumed confirmatory lineage cannot be reinterpreted into PASS by post-outcome mutation.
9. **Fresh/protected evidence is never consumed implicitly.**
10. **Agent output is proposal until admitted under the governing contract.**
11. **PM, worker, QA reviewer, execution environment, and physical placement are separate identities.**
12. **Different model != automatic independence; same model != automatic non-independence. Independence is policy-defined.**

## 3. Two execution environments must remain distinct

### 3.1 Environment A — G2E / Codex route

```text
G2E ProofObligation
      |
      v
GWF authorization / persistence
      |
      v
Codex harness
      |
      v
CGW
      |
      v
ChatGPT Web inference
      |
      v
Tunnel
      |
      v
G2E-specific MCP/tool surface
```

Canonical meaning:

- Codex = outer execution harness/agent.
- CGW = transport + inference mediation only.
- ChatGPT Web = inference + admitted tool requests.
- tunnel/MCP = delegated tool surface for that route.
- RemoteMCP is **not** inserted into this route merely because it also uses MCP.

### 3.2 Environment B — ChatGPT Web agent / RemoteMCP

```text
ChatGPT App PM
      |
      | governed work proposal
      v
G2E / GWF
      |
      | authorized WorkAssignment
      v
ChatGPT Web worker
      |
      v
RemoteMCP
      |
      +-- device
      +-- project
      +-- task
      +-- worktree
      +-- lease
      +-- durable job
      +-- checkpoint / resume
      |
      v
real local execution
```

Canonical meaning:

- ChatGPT Web agent = primary worker agent.
- RemoteMCP = internal execution bridge/substrate for that agent.
- RemoteMCP does not own Goal, Claim, ProofObligation, scientific verdict, governance mode, or claim resolution.

## 4. Agent-role model

### 4.1 Portfolio PM

Default target:

- app: ChatGPT App
- model: GPT-6 Astra
- role: portfolio/project manager

Responsibilities:

- inspect governed project state;
- reason across projects and dependencies;
- ask G2E what remains unproven;
- ask GWF what is authorized;
- propose work decomposition;
- choose among qualified executor classes;
- track blockers/budgets/resources;
- escalate only actions requiring human authority.

The PM is not the final scientific authority.

### 4.2 Worker

Typical target:

- ChatGPT Web + GPT-5.6 Sol through RemoteMCP; or
- Codex through its qualified G2E/CGW route.

Responsibilities:

- implementation;
- experiment execution;
- measurement;
- diagnostics/triage;
- evidence collection;
- bounded repair;
- handoff.

### 4.3 Independent QA reviewer

Target examples:

- GPT-6 Astra in a separate QA context;
- GPT-6/5.6 Sol in a separate QA context;
- another qualified harness when policy requires it.

Independence dimensions are prospective policy, e.g.:

- separate context;
- separate attempt;
- no inherited worker chat history;
- read-only evidence;
- cannot modify source result;
- source-blind recomputation when required;
- different model/harness/provider only when the frozen IndependencePolicy requires it.

### 4.4 Adjudicator

Prefer deterministic code/rules whenever the frozen decision rule can be expressed deterministically.

LLM review may produce candidate recomputations/analysis but must not silently replace frozen adjudication semantics.

## 5. GovernanceProfile

GWF core should add a generic policy primitive:

`GovernanceProfile`

The profile is domain-owned, not hard-coded to research.

### Research package profiles

- `research.triage`
- `research.exploratory`
- `research.measurement`
- `research.confirmatory`

### Software package profiles

Software defines its own profiles independently.

GWF core understands only generic concepts such as:

- authority;
- protected resource;
- mutation class;
- claim level;
- budget;
- approval boundary;
- policy overlay;
- transition;
- lineage;
- evidence ref;
- execution request.

Research-specific concepts remain in the research package.

## 6. Research governance profile semantics

### TRIAGE

High operational freedom, no scientific claim elevation.

Allowed examples:
- diagnose;
- inspect;
- restart;
- reroute;
- recover;
- resume checkpoint;
- repair environment.

Forbidden:
- scientific PASS/FAIL creation from infrastructure state;
- protected TEST consumption;
- hypothesis mutation masquerading as science;
- infrastructure failures in scientific lineage.

### EXPLORATORY

High search freedom, low claim authority.

Allowed examples:
- create/drop hypotheses;
- change mechanisms/architecture/metrics;
- branch;
- spawn bounded workers;
- pilot;
- instrumentation;
- ablation;
- retry/replan.

Still forbidden:
- protected fresh TEST consumption;
- calling exploratory outcomes confirmatory proof;
- retroactive preregistration;
- lineage deletion.

### MEASUREMENT

Locks increase:

- measurement protocol freeze;
- metric freeze;
- instrumentation freeze;
- baseline/cohort controls;
- repeatability obligations.

Operational repairs remain autonomous when they do not alter measurement semantics.

### CONFIRMATORY

Full proof governance:

- preregistration;
- exact source/config/data identities;
- study lock;
- protected fresh evidence;
- execution lock;
- one-shot/no-rescue where required;
- frozen thresholds;
- independent QA;
- raw evidence freeze;
- deterministic adjudication where possible;
- append-only PASS/FAIL/UNRESOLVED lineage.

## 7. Governance transitions

Agents/G2E may propose transitions, but they do not freely mutate governance state.

Introduce a generic:

`GovernanceTransitionProposal`

Disposition:

- `AUTO_ALLOWED`
- `HUMAN_APPROVAL_REQUIRED`
- `FORBIDDEN`
- `SUCCESSOR_REQUIRED`

Mandatory asymmetry:

```text
CONFIRMATORY FAIL
      |
      +--> immutable FAIL lineage
      |
      +--> new successor
              |
              v
          EXPLORATORY
              |
              v
        new hypothesis/protocol
              |
              v
          new fresh evidence
```

No transition may reinterpret the original consumed evidence.

## 8. Identity reconciliation

Before implementation, reconcile overlapping concepts across G2E, GWF, and RemoteMCP.

Do not use one overloaded `AgentBinding` for everything.

Target conceptual split:

- **G2E AgentBinding** — semantic executor identity requirements for one proof attempt.
- **GWF ExecutorBinding** — governed runtime mapping/authority/budget for the selected executor.
- **ExecutionEnvironment** — Codex/CGW route, ChatGPT-Web/RemoteMCP route, or future family.
- **RemoteMCP Placement** — device/project/task/worktree/lease/job physical placement.
- **AgentRole** — PM, worker, QA reviewer, etc.
- **AgentIdentity** — app/model/harness identity.
- **ExecutionEvidence** — normalized evidence returned to GWF/G2E.

No runtime-specific ID replaces the canonical G2E/GWF identity it maps to.

## 9. WorkAssignment

PMs should not dispatch arbitrary prose directly to workers.

Introduce a governed `WorkAssignment` concept containing at least:

- project;
- source goal/claim/proof obligation;
- objective;
- role;
- execution environment;
- required capabilities;
- authority scope;
- budget;
- protected-resource constraints;
- expected outputs/evidence;
- completion/handoff contract;
- independence requirements if QA.

GWF authorizes the WorkAssignment before execution.

RemoteMCP materializes only the placement/runtime part for ChatGPT Web workers.

## 10. HumanActionRequest

Any human-required action must exist as durable governed state, not only as a browser modal.

Examples:

- confirmatory transition;
- protected evidence consumption;
- destructive external action;
- claim elevation;
- authority/budget expansion.

The browser UI may render and resolve these requests, but UI absence must not erase them.

## 11. Mission Control UI

The browser becomes an observation and authority surface.

Primary project view should emphasize:

- Goal;
- Governance profile;
- current scientific/software state;
- current proof/work obligation;
- PM/worker/QA agents;
- running/queued/blocked executions;
- protected evidence state;
- latest admitted evidence;
- claims and their level;
- next automatic action;
- human action required;
- budgets/resources.

Primary operator actions:

- OBSERVE;
- PAUSE;
- STOP;
- CHANGE AUTHORITY;
- CHANGE BUDGET;
- REQUEST/APPROVE GOVERNANCE TRANSITION;
- APPROVE CLAIM-ELEVATING ACTION.

Manual Create Execution / Add Task / Assign Agent must not become the fundamental product abstraction.

## 12. Pivot treatment of the existing 7-wave/BPS plan

The existing plan remains valid historical/current-product governance on the current product branch.

For vNext, the following sequencing is superseded:

```text
finish browser modules
 -> BPS-W0
 -> resume backend roadmap
 -> GAC
 -> Codex
 -> UI integration
```

vNext uses architecture-first sequencing:

```text
PIVOT-P0 architecture + identity reconciliation
 -> PIVOT-P1 governance kernel
 -> PIVOT-P2 domain profiles
 -> PIVOT-P3 G2E adapter/reconciliation
 -> PIVOT-P4 PM / WorkAssignment protocol
 -> PIVOT-P5 ChatGPT-Web + RemoteMCP execution environment
 -> PIVOT-P6 Codex/CGW execution environment
 -> PIVOT-P7 independent QA/adjudication flow
 -> PIVOT-P8 headless end-to-end pilot
 -> PIVOT-P9 Mission Control UI
 -> PIVOT-P10 real-project pilot
```

Existing qualified code may be reused, but no historical UI/backend roadmap item is automatically imported as a vNext requirement.

## 13. Phase gates

### PIVOT-P0 — Architecture freeze

Deliverables:

- stack boundary document;
- identity map;
- authority map;
- execution-environment map;
- package ownership map;
- old-plan -> vNext disposition matrix;
- explicit non-goals.

Exit:

- no unresolved ownership collision among G2E/GWF/RemoteMCP;
- headless invariant testable;
- two MCP-based environments explicitly non-equivalent;
- current product line untouched.

### PIVOT-P1 — Governance kernel

Implement provider-neutral primitives only:

- GovernanceProfile;
- GovernanceTransitionProposal;
- WorkAssignment;
- HumanActionRequest;
- ExecutorBinding/ExecutionEnvironment references;
- budget/authority overlays.

No Codex, ChatGPT, RemoteMCP-specific code in core.

### PIVOT-P2 — Domain packages

Research and software remain separate packages.

Research implements TRIAGE/EXPLORATORY/MEASUREMENT/CONFIRMATORY overlays.

### PIVOT-P3 — G2E reconciliation

Integrate against a pinned G2E canonical baseline.

Rules:

- no wholesale merge of the P5A research branch;
- import/reuse only canonical schemas/engines/adapters with exact provenance;
- preserve G2E semantic authority;
- GWF is default persistence/governance runtime.

### PIVOT-P4 — PM protocol

Qualify the ChatGPT App PM role against read/propose/assign/escalate contracts.

PM may propose; GWF/G2E remain authoritative.

### PIVOT-P5 — ChatGPT Web / RemoteMCP environment

Qualify:

- worker identity;
- RemoteMCP device/project/task/worktree/job mapping;
- durable/resumable execution;
- bounded authority;
- evidence return;
- no hidden privilege escalation.

### PIVOT-P6 — Codex/CGW environment

Reuse the qualified G2E Codex route separately.

Do not substitute RemoteMCP for the route-specific tunnel/MCP.

### PIVOT-P7 — QA/adjudication

Qualify independent QA contexts using Astra/Sol under frozen IndependencePolicy and deterministic adjudication where possible.

### PIVOT-P8 — Headless end-to-end pilot

No browser UI dependency.

Demonstrate:

```text
Goal
 -> ProofObligation
 -> GWF authorization
 -> PM/assignment
 -> worker execution
 -> evidence
 -> QA
 -> adjudication
 -> next obligation
```

with restart/recovery and immutable lineage.

### PIVOT-P9 — Mission Control

Only after headless PASS, refactor browser product around observation/authority.

### PIVOT-P10 — Real-project pilot

Start with one bounded non-protected successor task in an existing project. Do not begin with fresh confirmatory TEST consumption.

## 14. Branch and workspace policy

Current product line remains:

- repository: `minhtri22/GWF`
- branch: `feature/bps-i00-product-shell`
- current HEAD at pivot: `de3247c18c1a8546db9611ecd0fdf24f827662ae`

vNext line:

- repository: `minhtri22/GWF`
- branch: `pivot/gwf-autonomous-research-stack-v1`
- base: exact current-product HEAD above.

Recommended independent local clone:

`D:\WORK\RESEARCH\4.GWF-VNEXT`

Do not implement vNext inside the current `D:\WORK\RESEARCH\4.GWF` checkout or its BPS UAT worktree.

## 15. G2E integration policy

The current G2E research branch is deliberately not merged wholesale because it has diverged substantially from the BPS product line and contains transport-study lineage.

Before PIVOT-P3:

1. identify the canonical qualified G2E core surface;
2. pin exact source SHAs/blobs;
3. classify files as:
   - canonical core;
   - reusable adapter;
   - qualification test;
   - historical research evidence;
   - transport-specific experiment;
4. import only the first three categories when required;
5. preserve historical research evidence in its existing lineage;
6. do not rewrite P5A scientific/transport history into the vNext product line.

## 16. Current frontier after P3 contract freeze

PIVOT-P0 is formally closed PASS.

PIVOT-P1 governance kernel contract + implementation are formally closed PASS and execution-locked.

PIVOT-P2 domain-governance-profile contract + implementation are formally closed PASS and execution-locked.

PIVOT-P3 G2E semantic/runtime reconciliation preregistration is formally closed PASS and contract-frozen.

Authoritative P3 records:

- `docs/pivot/GWF_VNEXT_P3_G2E_RECONCILIATION_MANIFEST_V1.json`;
- `docs/pivot/GWF_VNEXT_P3_G2E_SEMANTIC_RUNTIME_RECONCILIATION_PREREGISTRATION_AND_CONTRACT_FREEZE.md`;
- `docs/pivot/GWF_VNEXT_P3_QA_AND_FORMAL_DECISION.md`.

P3 pins:

- provider-neutral qualified G2E baseline `6e9c518671c3f9ba140daa798458b37bee83647c`;
- exact G2E semantic/core blobs;
- exact classification of 585 G2E-related files;
- 31 canonical-core files;
- 2 reusable legacy-adapter files;
- 16 qualification-test files;
- 35 historical-evidence files;
- 501 transport-experiment files;
- 0 unclassified files;
- G2E semantic ownership vs GWF governance/runtime ownership;
- G2E AgentBinding ↔ GWF ExecutorBinding reconciliation without semantic collision;
- Goal/Claim/Proof/Attempt cardinality;
- G2E/GWF revision and hash-domain separation;
- protected-resource bridge;
- evidence-admission bridge;
- independent QA/reviewer mapping;
- 40 preregistered implementation negative tests.

The next authorized bounded phase is:

`GWF_VNEXT_P3_G2E_SEMANTIC_RUNTIME_RECONCILIATION_IMPLEMENTATION_STATIC_PREFLIGHT_AND_EXECUTION_LOCK`

That phase may implement only the frozen provider-neutral G2E↔GWF semantic/runtime bridge and its qualification fixtures.

Do **not** yet:

- integrate Codex adapter behavior;
- integrate RemoteMCP adapter behavior;
- import transport-experiment/P5A material as semantic core;
- refactor Mission Control UI;
- run a real research/software project;
- consume protected evidence.

