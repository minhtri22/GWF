# GWF — Browser Product Surface Audit & Locked Contract

## 1. Status

**State:** AUDITED / SURFACE CONTRACT LOCKED / IMPLEMENTATION NOT AUTHORIZED BY THIS DOCUMENT

This document defines the browser-facing product surface that GWF must expose across the **entire implemented product lineage**, not only the current seven-wave roadmap. The baseline includes pre-wave product foundations (v0.5 through v0.8.5), Documentation Governance DG-P0..P10, and prospectively frozen later DG/GAC/RA/AI capabilities.

It does not itself authorize runtime, API, schema, UI, adapter, catalog, reference-acquisition, MCP, ARC, Codex, Claude, Gemini, or routing implementation.

The contract is intentionally broader than the current static UAT site. It covers the complete governed product surface from the existing production foundation through Documentation Governance, Shared Library/GAC, Reference Acquisition, and Agent Interoperability.

## 2. Audit baseline

Product implementation baseline:

- DG-P10 final formal-close HEAD: `a09f79ae74a838d2c5998813560373c849669872`.
- DG-P10 final exact-head workflow: `35671227699` PASS.
- Current FastAPI implementation exposes **68 HTTP endpoints**.
- Current static `web/` navigation exposes only:
  - Dashboard;
  - Process Inspector;
  - Approvals;
  - Failure & recovery;
  - Distributed runtime;
  - Domain Registry.
- The current static web site identifies itself as static UAT and stores simulated lifecycle mutations in browser `localStorage`; it is therefore not authoritative product UAT.
- The product checkout has a FastAPI application factory but no canonical installed server launcher and no `uvicorn` runtime dependency in the product installation contract.
- A debt-branch live-browser harness exists only to inspect the actual backend and must not be mistaken for the product UI.

## 3. Documents reconciled

The browser surface was reconciled against the active architecture/roadmap documents, including:

- data and production foundation;
- identity/multitenancy;
- distributed runtime;
- Research Product Alpha;
- project lifecycle/process inspector;
- project governance/agent protocol;
- orchestrator integration;
- GitHub plugin/SHA-safe QA;
- domain/skill audit;
- Documentation Integrity & Governance and the complete DG seven-wave plan;
- Reference Acquisition;
- Governed Artifact Catalog / Shared Library specifications and integration boundaries;
- Agent Interoperability Foundation;
- current README, handoffs, and formal-close lineage.

The governing dependency source for future work remains `docs/IMPLEMENTATION_7_WAVES_PLAN.md`.

Detailed navigation, project workflow, Package Registry/usage, graph interaction, themes, and implementation flows are governed by `docs/UI_UX_PRODUCT_ARCHITECTURE_SPEC.md`.

## 4. Browser authority invariant

Browser UAT is valid only when:

```text
installed product
  -> canonical local/hosted GWF server
  -> browser UI
  -> authenticated HTTP operation
  -> authoritative runtime/database state
  -> audit/evidence
```

A browser-only simulation, fixture-only page, `localStorage` mutation, demo JSON, or generated mock does not count as acceptance evidence for a product capability.

Every browser feature must declare one of these states:

- `LIVE` — authoritative backend/API exists and the browser operates it.
- `BACKEND_NO_API` — runtime/service exists but product HTTP contract is missing.
- `API_NO_UI` — backend and HTTP contract exist but browser UX is missing.
- `PLANNED_BLOCKED` — capability is frozen in roadmap/specification but implementation gate is not open.
- `OPTIONAL_FUTURE` — explicitly conditional/parking-lot capability.
- `NOT_APPLICABLE` — intentionally no browser action is required.

Only `LIVE` surfaces count toward browser UAT acceptance.

## 4A. Pre-seven-wave product-lineage coverage contract

The Browser Product Surface is not a UI layer only for the seven-wave Documentation/GAC/Agent roadmap.

BPS-W0 must audit and surface every user/operator-relevant capability already implemented before the current seven-wave plan:

| Product lineage | Capability family | Browser obligation |
| --- | --- | --- |
| v0.5 Production Foundation | database/backend identity, CAS/object storage, provider failover, observability | system/diagnostic visibility; operational controls only where a governed user action exists |
| v0.6 Identity / Multi-tenancy | tenant, workspace, project scopes, memberships, authorization | full authoritative browser administration |
| v0.7 Distributed Runtime | jobs, workers, leases, recovery/capacity state | full authoritative runtime visibility |
| v0.8 Research Product Alpha | dashboard, approvals, failure/recovery, project read model | replace static fixture UI with live API-backed UI |
| v0.8.1 Lifecycle / Process Inspector | rename/archive/restore, lifecycle, process/phase/event inspection | full authoritative browser UI |
| v0.8.2 Project Governance / Agent Protocol | settings, protocol, plan, step, problem, recovery, verify, handoff, complete | full authoritative browser UI |
| v0.8.3 Orchestrator Integration | protocol-driven orchestration and live operational events | live browser inspection and execution state |
| v0.8.4 GitHub Plugin / SHA-safe QA | plugin connection, repository binding, change-set preflight/execute/verify | full integration configuration and governed action UI |
| v0.8.5 Domain / Skill maturity | research/software domain packages, skill packages/revisions, tool requirements, QA contract | full live registry/configuration UI |
| DG-P0..DG-P10 | Documentation Governance | bounded API exposure plus full document-governance browser UI |

Infrastructure-only mechanisms are **not automatically required to have mutation controls**. They are still required to have browser-visible status/identity where operationally meaningful. A capability may be marked `NOT_APPLICABLE` only when a written rationale shows that no human/operator browser action or inspection surface is needed.

The legacy static `web/` implementation is therefore a **design/reference asset only**. Its existing views must either:

1. be rewired to authoritative product APIs; or
2. be replaced by an equivalent live browser surface.

They must not remain fixture/localStorage simulations in a product-ready build.

---

## 5. Global browser shell checklist

### 5.1 Installation and server lifecycle

- [ ] canonical installed command starts the GWF server;
- [ ] server dependency is part of installation, not injected by a UAT-only harness;
- [ ] browser URL is printed by installation/start command;
- [ ] health/readiness shown in UI;
- [ ] exact Git/runtime version/backend shown;
- [ ] local database/storage path shown without exposing secrets;
- [ ] stop/restart behavior documented;
- [ ] failed startup produces actionable error state;
- [ ] browser UAT report binds exact product HEAD/version.

**Current:** API application exists; canonical product launcher is missing.  
**Status:** `API_NO_UI / PRODUCT_LAUNCHER_GAP`.

### 5.2 Authentication/session

- [ ] login UI;
- [ ] current actor/session view;
- [ ] OIDC provider path when configured;
- [ ] expiry/re-authentication handling;
- [ ] logout/session revoke flow;
- [ ] no token printed into browser logs or persisted in static artifacts.

**Current:** API exists; product UI absent.  
**Status:** `API_NO_UI`.

### 5.3 Navigation and capability status

The browser shell follows the project-centered architecture frozen in `docs/UI_UX_PRODUCT_ARCHITECTURE_SPEC.md`.

Global areas:

1. Home
2. Projects
3. Operations — Runs / Approvals / Audit / Runtime
4. Research — Packages (Domains / Skills / Usage) and future Reference Acquisition
5. Shared Library — future GAC-backed cross-project capability
6. Agents / Codex — future Agent Interoperability
7. System — GitHub / Access / Diagnostics / Settings

Project-scoped deep areas:

1. Overview
2. Execution
3. Library — Documents / Artifacts / Evidence / future References
4. Governance
5. Configuration — Packages / GitHub / Agent Protocol / Members & Access / Settings

Relations & Lineage is contextual to a selected project document/object; it is not a global/Home navigation item.

Future-gated sections may appear only as clearly disabled/read-only capability status pages. They must not simulate successful actions.

## 6. Identity, tenancy, workspace, membership

### Browser checklist

- [ ] tenant list/create;
- [ ] workspace list/create;
- [ ] project list/create;
- [ ] tenant/workspace/project membership list;
- [ ] add/remove member;
- [ ] role display;
- [ ] inaccessible cross-tenant resources hidden;
- [ ] project scope breadcrumb;
- [ ] authorization failure presented without leaking hidden-resource existence.

**Current backend/API:** implemented.  
**Current static UI:** project selection only; no complete tenancy/member administration.  
**Status:** `API_NO_UI`.

## 7. Project lifecycle and operator dashboard

### Browser checklist

- [ ] live project dashboard;
- [ ] project rename;
- [ ] archive with drain/reason;
- [ ] restore;
- [ ] lifecycle history;
- [ ] domain pin;
- [ ] current attention queue;
- [ ] live metrics;
- [ ] audit count;
- [ ] artifact validity frontier;
- [ ] no localStorage state used as authority.

**Current backend/API:** implemented.  
**Current web:** visual design exists but authoritative mutations are simulated.  
**Status:** `API_NO_LIVE_UI`.

## 8. Artifact, revision, object, evidence, checkpoint surface

### Browser checklist

- [ ] artifact explorer;
- [ ] stable artifact identity;
- [ ] revision list/detail;
- [ ] exact hashes/source identity;
- [ ] validity state and provenance;
- [ ] evidence detail;
- [ ] producing run/workunit linkage;
- [ ] object/blob metadata where applicable;
- [ ] checkpoint detail and resume reconciliation;
- [ ] validity frontier drill-down;
- [ ] immutable IDs copyable from UI.

**Current backend:** foundational primitives exist.  
**Current API:** partial (`frontier`, checkpoint resume, dashboard/runs); no complete artifact/revision/evidence explorer API.  
**Status:** mixed `BACKEND_NO_API` / `API_NO_UI`.

## 9. Domains, pilots and skills

### Browser checklist

- [ ] current domain inspection;
- [ ] domain package list/create;
- [ ] YAML revision editor/upload;
- [ ] validate;
- [ ] publish;
- [ ] immutable revision identity;
- [ ] project domain binding;
- [ ] pilot profile inspection and validation;
- [ ] skill package list/create;
- [ ] skill revision list/create;
- [ ] tool requirements;
- [ ] QA contract display;
- [ ] phase skill binding.

**Current backend/API:** domain and skill APIs exist; pilot validation is primarily tooling/config based.  
**Current static UI:** Domain Registry simulation exists; no live Skills/Pilot UI.  
**Status:** `API_NO_UI` plus pilot surface gap.

## 10. Research/software orchestration and process inspector

### Browser checklist

- [ ] orchestration list/detail;
- [ ] phase timeline;
- [ ] current phase;
- [ ] generation/attempt lineage;
- [ ] phase inputs/outputs;
- [ ] live event stream;
- [ ] runs;
- [ ] final report;
- [ ] software-domain and research-domain presentation without conflating semantics;
- [ ] exact handoff chain.

**Current backend/API:** implemented for current orchestration/process paths.  
**Current static UI:** process inspector exists but is fixture/simulation driven.  
**Status:** `API_NO_LIVE_UI`.

## 11. Agent execution protocol, recovery and handoff

### Browser checklist

- [ ] project default recovery mode/retry budget;
- [ ] phase protocol creation;
- [ ] LOAD/PREFLIGHT/PLAN/EXECUTE/VERIFY/HANDOFF/COMPLETE state;
- [ ] preflight checklist;
- [ ] frozen plan;
- [ ] step progress;
- [ ] problem record;
- [ ] recovery proposal;
- [ ] AUTO vs HUMAN_APPROVE behavior;
- [ ] human recovery decision;
- [ ] apply recovery;
- [ ] verification result;
- [ ] handoff record;
- [ ] completion;
- [ ] operational event log;
- [ ] no hidden chain-of-thought display.

**Current backend/API:** implemented.  
**Current static UI:** design/simulation exists.  
**Status:** `API_NO_LIVE_UI`.

## 12. Proposal, approval and audit

### Browser checklist

- [ ] pending approval queue;
- [ ] proposal frozen payload;
- [ ] exact payload hash;
- [ ] approve exact hash;
- [ ] reject with reason;
- [ ] approval history;
- [ ] project audit timeline;
- [ ] actor attribution;
- [ ] no simulated approval counted as acceptance.

**Current backend/API:** implemented.  
**Current static UI:** simulated.  
**Status:** `API_NO_LIVE_UI`.

## 13. Distributed runtime

### Browser checklist

- [ ] distributed job list/detail;
- [ ] status/attempt/lease;
- [ ] worker identity;
- [ ] capacity/capability;
- [ ] lease expiry/recovery visibility;
- [ ] failure/requeue history;
- [ ] producing project/run linkage.

**Current backend/API:** implemented read model.  
**Current static UI:** fixture based.  
**Status:** `API_NO_LIVE_UI`.

## 14. Plugin and GitHub integration configuration

### Browser checklist

#### Connection

- [ ] plugin connection list;
- [ ] create GitHub connection using opaque external connection reference;
- [ ] capability selection (`REPO_READ`, `CONTENT_WRITE`, `WORKFLOW_WRITE` as applicable);
- [ ] adapter-attached/connection status;
- [ ] disable connection;
- [ ] no raw token/credential field stored in GWF.

#### Repository binding

- [ ] repository full name;
- [ ] default branch;
- [ ] allowed branches;
- [ ] write policy;
- [ ] exact repository identity status.

#### Governed change set

- [ ] branch;
- [ ] expected head SHA;
- [ ] file changes;
- [ ] commit message;
- [ ] preflight state;
- [ ] stale SHA conflict display;
- [ ] exact file SHA mismatch display;
- [ ] execute;
- [ ] committed vs VERIFIED distinction;
- [ ] post-write exact verification.

**Current backend/API:** implemented.  
**Current UI:** absent.  
**Status:** `API_NO_UI`.

## 15. Documentation Governance — DG-P0 through DG-P10

### 15.1 Validator surface — DG-P0/P1/P2

- [ ] validator/tool availability and version;
- [ ] markdown structural findings;
- [ ] terminology/prose findings;
- [ ] referential/link findings;
- [ ] content finding vs tool/network failure separation;
- [ ] exact source hashes;
- [ ] raw external tool result never becomes authority by itself.

**Current:** backend/tooling exists; no browser product API/UX.  
**Status:** `BACKEND_NO_API`.

### 15.2 Exact Git/blob source identity — DG-P3

- [ ] repository/commit/path/blob identity;
- [ ] stale expected identity display;
- [ ] read-only vs write-capable binding distinction;
- [ ] credential redaction.

**Current:** backend service exists; no document browser surface.  
**Status:** `BACKEND_NO_API`.

### 15.3 Document explorer — DG-P4

- [ ] logical document list;
- [ ] document role/class;
- [ ] active revision;
- [ ] revision history;
- [ ] path independent logical identity;
- [ ] exact source provenance;
- [ ] enrolled vs legacy/non-enrolled state.

**Current:** service exists; no product HTTP/UI.  
**Status:** `BACKEND_NO_API`.

### 15.4 QA and findings — DG-P5

- [ ] QA record list/detail;
- [ ] exact target revision;
- [ ] validator executions;
- [ ] findings;
- [ ] severity/class;
- [ ] OPEN/RESOLUTION_PENDING/VERIFIED_RESOLVED lifecycle;
- [ ] waiver state/expiry where legal;
- [ ] prior revision PASS visibly non-transferable.

**Current:** service exists; no product HTTP/UI.  
**Status:** `BACKEND_NO_API`.

### 15.5 Lifecycle and validity — DG-P6

- [ ] document lifecycle;
- [ ] revision validity;
- [ ] effective BLOCKED state;
- [ ] STALE reason;
- [ ] validity evidence;
- [ ] legal transition actions;
- [ ] lifecycle vs validity visually separate.

**Current:** service exists; no product HTTP/UI.  
**Status:** `BACKEND_NO_API`.

### 15.6 Authority — DG-P7

- [ ] authority claims;
- [ ] authority key/scope;
- [ ] primary/composed ownership;
- [ ] duplicate authority conflict;
- [ ] claim provenance;
- [ ] active/retired history;
- [ ] approval flow where required.

**Current:** service exists; no product HTTP/UI.  
**Status:** `BACKEND_NO_API`.

### 15.7 Relations — DG-P8

- [ ] relation graph/table;
- [ ] relation type;
- [ ] source/target direction;
- [ ] creation provenance;
- [ ] active/retired state;
- [ ] no inference from Markdown links;
- [ ] relation semantics help text.

**Current:** service exists; no product HTTP/UI.  
**Status:** `BACKEND_NO_API`.

### 15.8 Relation binding — DG-P9

- [ ] `LOGICAL_CURRENT` vs `PINNED_REVISION`;
- [ ] exact pinned revision/hash;
- [ ] current resolution result;
- [ ] legacy binding state;
- [ ] non-rebind rule;
- [ ] external resolution fail-closed state.

**Current:** service exists; no product HTTP/UI.  
**Status:** `BACKEND_NO_API`.

### 15.9 Change classification and mutation authority — DG-P10

- [ ] declared class;
- [ ] effective class;
- [ ] escalation reason;
- [ ] exact base revision;
- [ ] proposed active path;
- [ ] proposed content SHA-256;
- [ ] workflow mode snapshot;
- [ ] owner match;
- [ ] document role/governance state;
- [ ] mutation authority decision;
- [ ] next version;
- [ ] archive path;
- [ ] previous-version link;
- [ ] explicit GOV/FROZEN block;
- [ ] clear notice that P10 does not mutate source.

**Current:** service exists; no product HTTP/UI.  
**Status:** `BACKEND_NO_API`.

## 16. Documentation Governance future surfaces — DG-P11 through DG-P20

These are part of the locked product information architecture but controls remain disabled until their implementation gates pass.

### DG-P11 — DocumentChangeSet

- [ ] multi-document change set;
- [ ] frozen base revisions;
- [ ] allowed paths/scope;
- [ ] per-document/effective class;
- [ ] approvals;
- [ ] archive/create/delete mutation plan;
- [ ] exact post-write verification.

**Status:** `PLANNED_BLOCKED` until DG-P11 is separately authorized/implemented.

### DG-P12–P16 — dependency/drift core

- [ ] impact traversal;
- [ ] relation-specific invalidation;
- [ ] STALE/review/BLOCK propagation;
- [ ] no-silent-cascade visibility;
- [ ] append-only/supersession;
- [ ] generated-document provenance.

**Status:** `PLANNED_BLOCKED`; opens after DG-W3 and individual authorizations.

### DG-P17–P20

- [ ] repository QA enforcement;
- [ ] code/schema/API/workflow/dataset bindings;
- [ ] research study-lock integration;
- [ ] existing-document migration pilot.

**Status:** `PLANNED_BLOCKED`; dependencies include DG-W4 and phase-specific gates.

## 17. Shared Library / Governed Artifact Catalog

The browser information architecture reserves **Shared Library** as the consumer-facing label. It must not create a second canonical store.

### Minimum Shared Library browser checklist

- [ ] catalog entry list;
- [ ] exact subject kind and identity;
- [ ] source project/workspace/tenant;
- [ ] publication state;
- [ ] publication eligibility;
- [ ] publish exact revision;
- [ ] withdraw/tombstone;
- [ ] supersession;
- [ ] deterministic metadata query;
- [ ] query execution identity;
- [ ] catalog snapshot identity;
- [ ] access intersection;
- [ ] source lifecycle/validity observation;
- [ ] query failure/partial distinct from zero matches;
- [ ] ObjectRef subject display after GAC-P2A;
- [ ] optional search backend/index status only after GAC-P3.

**Current implementation:** specification only.  
**Current blocker:** hard dependency `DG-W4 PASS` before GAC-P0/P1.  
**Minimum implementation path:**

```text
DG-W3
  -> DG-P12..P16
  -> DG-W4 PASS
  -> GAC-P0
  -> GAC-P1
  -> deterministic Shared Library metadata query
```

GAC-P2A adds ObjectRef subjects after GAC-P1. GAC-P3 is optional and is not required for minimum Shared Library readiness.

**Status:** `PLANNED_BLOCKED`.

## 18. Reference Acquisition browser surface

### Browser checklist

- [ ] prospective query plan;
- [ ] executed query log;
- [ ] provider/source observation;
- [ ] required vs optional source classes;
- [ ] canonical source identity;
- [ ] exact inspected snapshot/version;
- [ ] Git/source-code acquisition;
- [ ] paper/reference acquisition;
- [ ] reference registry;
- [ ] dedup/identity decision;
- [ ] evidence map;
- [ ] coverage status;
- [ ] temporal mode;
- [ ] novelty collision handling;
- [ ] GAC/Shared Library discovery execution after bridge opens;
- [ ] explicit provider/tool failure distinct from “no results”.

**Current implementation:** specification only.  
**Roadmap:** Wave 6, with GAC bridge dependencies where applicable.  
**Status:** `PLANNED_BLOCKED`.

## 19. Agent Interoperability / Codex / MCP / Agent Pool

### 19.1 Agent execution envelope

- [ ] execution ID;
- [ ] workunit/orchestration/node;
- [ ] executor resource class;
- [ ] provider identity;
- [ ] transport identity;
- [ ] binding identity/revision;
- [ ] frozen input identity;
- [ ] external session/thread/task IDs;
- [ ] tools/environment attribution;
- [ ] output/evidence;
- [ ] executor status explicitly distinct from GWF PASS.

**Roadmap:** AI-P0.  
**Status:** `PLANNED_BLOCKED`.

### 19.2 MCP surface

- [ ] connection/status;
- [ ] read-only governed operations;
- [ ] actor/authority context;
- [ ] request trace;
- [ ] mutation surface only after AI-P3;
- [ ] no force-pass/force-merge/lineage-delete action.

**Roadmap:** AI-P1 then AI-P3.  
**Status:** `PLANNED_BLOCKED`.

### 19.3 Codex harness configuration

- [ ] harness type = Codex;
- [ ] opaque external connection reference;
- [ ] harness/session identity;
- [ ] workspace/repository scope;
- [ ] allowed tool capability profile;
- [ ] execution/locality/network/privacy constraints;
- [ ] maximum authority;
- [ ] binding mode when applicable;
- [ ] native Codex session/thread trace;
- [ ] result normalization into AgentExecutionEnvelope;
- [ ] no raw reusable credential in browser/persistence;
- [ ] Codex success does not self-complete a GWF node.

**Roadmap:** AI-P2.  
**Hard dependency:** AI-P0.  
**Ordering preference:** AI-P1 before AI-P2, but AI-P1 is not a hard architectural dependency for AI-P2.  
**Wave sequencing:** Wave 7 is currently ordered after RA-GAC-W6; the plan explicitly states this is sequencing, not an architectural dependency for AI-P0.

**Status:** `PLANNED_BLOCKED` pending explicit implementation authorization and AI-P0.

### 19.4 Claude/Gemini

Same harness invariants as Codex, added only after their roadmap items open.

**Status:** `PLANNED_BLOCKED`.

### 19.5 Agent Pool / ARC

- [ ] resource class;
- [ ] agent identity;
- [ ] capabilities;
- [ ] execution constraints;
- [ ] worker status;
- [ ] ARC transport identity;
- [ ] task/trace identity;
- [ ] reassignment provenance;
- [ ] primary executor support;
- [ ] no fallback-only semantics.

**Roadmap:** AI-P6 then AI-P7.  
**Status:** `PLANNED_BLOCKED`.

## 20. System/diagnostic/admin surface

### Browser checklist

- [ ] runtime version;
- [ ] exact Git SHA;
- [ ] backend type/version;
- [ ] database connectivity;
- [ ] object-store status;
- [ ] observability sink status;
- [ ] domain/package status;
- [ ] plugin/integration status;
- [ ] server uptime/readiness;
- [ ] capability matrix with LIVE/API_NO_UI/BACKEND_NO_API/PLANNED_BLOCKED states;
- [ ] logs/evidence references without credential leakage.

## 21. Current browser gap summary

### Existing static web surface

Useful information architecture exists for:

- dashboard;
- process inspector;
- approvals;
- recovery;
- distributed runtime;
- domain registry.

But it is not authoritative browser UAT because it is fixture/localStorage based.

### Current live API but browser missing

Major implemented areas already eligible for browser product work:

- authentication;
- tenancy/workspaces/membership;
- project lifecycle/dashboard;
- domain registry;
- skill registry;
- orchestration/process/event stream;
- agent protocol/recovery/handoff;
- approvals/audit;
- distributed runtime;
- plugin/GitHub integration.

### Current backend service but API/browser missing

- Documentation Governance DG-P0 through DG-P10;
- complete artifact/revision/evidence explorer.

### Current specification/roadmap only

- DG-P11+;
- Shared Library/GAC;
- Reference Acquisition;
- MCP/Codex/Claude/Gemini;
- Agent Pool/ARC;
- parking-lot visual node editor/routing/scheduler.

## 22. Browser implementation sequencing contract

Browser implementation must follow backend maturity, not visual convenience.

### Surface tranche A — authoritative browserization of the existing product lineage

This tranche covers **all already-implemented pre-wave product capability from v0.5 through v0.8.5**, not only endpoints introduced near the seven-wave roadmap.

May be implemented without inventing new domain semantics:

1. product server lifecycle, runtime/backend/object-store/observability diagnostics;
2. auth/session;
3. tenant/workspace/project/member administration;
4. dashboard/project lifecycle;
5. domain/pilot/skill registry;
6. process/orchestration/event views;
7. agent protocol/recovery/handoff;
8. approvals/audit;
9. distributed runtime;
10. GitHub/plugin configuration;
11. artifact/revision/evidence/checkpoint inspection where existing primitives already support it;
12. capability/status matrix identifying any remaining BACKEND_NO_API/API_NO_UI/NOT_APPLICABLE item.

Existing static pages are not grandfathered as acceptable product surfaces; they must be connected to live APIs or replaced.

### Surface tranche B — expose already-implemented backend services

Requires bounded product API contracts before UI:

1. artifact/revision/evidence explorer;
2. Documentation Governance DG-P0..P10.

### Surface tranche C — future-gated capabilities

UI implementation follows each backend gate:

1. DG-P11..P20;
2. GAC/Shared Library;
3. Reference Acquisition;
4. Agent Interoperability/Codex/MCP/Agent Pool/ARC.

No future-gated action may be simulated as if authoritative.

## 23. Browser UAT acceptance contract

A capability may be marked browser-UAT PASS only when:

- [ ] backend implementation is qualified;
- [ ] HTTP contract is authoritative;
- [ ] browser uses that HTTP contract;
- [ ] exact actor/project/resource identity is visible;
- [ ] mutations produce authoritative state/audit;
- [ ] fail-closed and stale/conflict paths are visible;
- [ ] browser refresh reconstructs state from backend rather than local simulation;
- [ ] secrets are absent from browser/static artifacts;
- [ ] exact product HEAD/version is recorded;
- [ ] UAT evidence includes operator-observed result.

## 24. Lock decision

This document freezes the required browser information architecture and acceptance boundary across the current GWF roadmap.

It does **not** require all future-gated navigation to be implemented now. It requires that when a capability is implemented, its browser surface follows this contract and does not create parallel semantics, duplicate stores, hidden authority paths, or simulated acceptance.

Any change that removes a listed governed surface, merges authority-distinct concepts, or makes a blocked/future capability appear authoritative requires an explicit amendment to this contract.

## 24. Approved visual-baseline / document-preview amendment v1.1

The browser product surface is additionally governed by the user-approved visual baseline:

- `docs/uiux/approved/GWF_UI_BASELINE_v1_1_APPROVED.jpg`;
- `docs/uiux/approved/UI_VISUAL_BASELINE_MANIFEST.md`.

This does not change backend authority or BPS ordering.

### Document preview obligation

When Documents become LIVE in their authorized BPS slice, metadata-only inspection is insufficient.

Required browser behavior:

- document list and contextual selection;
- Quick Preview containing meaningful rendered/readable document content;
- exact logical ID and resolved revision identity;
- `Preview | Details | Relations | History` inspector organization;
- Expand / Full-screen Reader for long research documents/papers/protocols;
- return from Reader to the same prior project/document/graph context;
- DG-P9-correct preview resolution for `LOGICAL_CURRENT` and `PINNED_REVISION`;
- no browser-side fabrication of document content or revision identity.

When Relations become LIVE, node selection and document preview are coordinated while edge selection shows relation/binding detail.

### BPS-I00 boundary

The visual baseline is used immediately to correct the BPS-I00 shell/design system. Document/Relations/Reader functionality remains locked to its later authorized slices. A visual placeholder/reference must never be counted as LIVE capability.

Future source-code preview, isolated PowerShell/Python execution and explainable replay remain parked under `TD-UX-03` and require their own specification/security/authorization.

## 25A. Navigable locked routes and module isolation

Once BPS-I00 passes, the route tree is structurally navigable even when individual modules are not yet LIVE.

A locked/planned route may show only:

- route title;
- maturity state;
- owning BPS module;
- concise explanation of what is unavailable.

It must not show fabricated entities, counts, activity, mutations or backend state.

Future browser execution uses `BPS-M01…BPS-M10`; each module freezes independently after local UAT. `BPS-W0` is reserved for cross-module wiring and end-to-end journeys, not unfinished module work.
