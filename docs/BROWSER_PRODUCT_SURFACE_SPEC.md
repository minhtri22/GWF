# GWF — Browser Product Surface Audit & Locked Contract

## 1. Status

**State:** AUDITED / SURFACE CONTRACT LOCKED / IMPLEMENTATION NOT AUTHORIZED BY THIS DOCUMENT

This document defines the browser-facing product surface that GWF must eventually expose for the capabilities already implemented or prospectively frozen in the current seven-wave roadmap.

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

The browser shell must contain top-level areas for:

1. Home / Dashboard
2. Organization / Access
3. Projects
4. Process / Runs
5. Artifacts / Evidence
6. Domains / Skills
7. Approvals / Audit
8. Distributed Runtime
9. Integrations
10. Documents
11. Shared Library
12. Reference Acquisition
13. Agent Interoperability
14. System / Diagnostics

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

### Surface tranche A — live existing APIs

May be implemented without inventing new domain semantics:

1. auth/session;
2. tenant/workspace/project/member administration;
3. dashboard/project lifecycle;
4. domain/skill registry;
5. process/orchestration/event views;
6. agent protocol/recovery/handoff;
7. approvals/audit;
8. distributed runtime;
9. GitHub/plugin configuration;
10. system diagnostics.

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
