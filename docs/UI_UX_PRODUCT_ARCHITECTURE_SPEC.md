# GWF — UI/UX Product Architecture & Implementation Contract

## 1. Status

**State:** UI/UX ARCHITECTURE LOCK / IMPLEMENTATION CONTRACT / CODE NOT AUTHORIZED BY THIS DOCUMENT

This document defines the complete browser information architecture, navigation, interaction model, module placement, backend binding rules, visual system, implementation sequence, and browser-UAT acceptance contract for GWF.

It is the detailed UI/UX companion to:

- `docs/BROWSER_PRODUCT_SURFACE_SPEC.md` — capability maturity and browser-authority contract;
- `docs/IMPLEMENTATION_7_WAVES_PLAN.md` — backend/governance dependency plan;
- the completed v0.5→v0.8.5 product lineage;
- Documentation Governance DG-P0→DG-P10;
- future GAC / Shared Library, Reference Acquisition, and Agent Interoperability work.

The design direction is **Governed Knowledge Studio**: research-first, SaaS-operable, project-centric, dense enough for expert work, but organized by workflow instead of by implementation subsystem.

This document does not authorize code changes by itself.

### 1.1 Approved visual baseline v1.1

The user-approved visual baseline is repository-persisted under:

- `docs/uiux/approved/GWF_UI_BASELINE_v1_1_APPROVED.jpg`;
- `docs/uiux/approved/UI_VISUAL_BASELINE_MANIFEST.md`.

The visual baseline governs **composition, hierarchy, visual language and interaction placement**. This specification governs semantics, authority and exact behavior. If a compressed visual reference cannot depict a later approved detail, the explicit textual amendment in this specification and the baseline manifest takes precedence.

The approved product direction is a **project-centered Governed Knowledge Studio**, not a restyled legacy v0.8.5 dashboard.

For BPS-I00 specifically, the baseline establishes the correct shell/design system only. Visual examples of Documents/Relations/Preview define the target design language for later slices; they do not authorize BPS-I10/BPS-I11 functionality early.

---

## 2. Product UX principles

### 2.1 Research-first, not generic SaaS

GWF is not an integration marketplace, generic project tracker, or n8n-style connector surface.

The UI must optimize for:

- reproducible research/work execution;
- governed project state;
- exact revision and identity visibility;
- human approvals;
- traceable runs and agent/execution activity;
- documents, artifacts and evidence;
- package/domain/skill configuration;
- audit and recovery;
- controlled external boundaries.

### 2.2 Project context before deep knowledge context

Deep objects such as documents, relations, evidence, run traces and governance state are normally interpreted inside a project.

Therefore:

```text
Home
  -> Project
      -> Overview / Execution / Library / Governance / Configuration
```

The UI must not promote document relation graphs or project-internal details onto the global Home dashboard.

### 2.3 UI is a projection, never a second system of record

Browser state may cache presentation preferences, but authoritative product state comes from GWF APIs/runtime/database.

Allowed browser-local state:

- dark/light/system theme preference;
- sidebar expanded/collapsed preference;
- table column/display preference;
- transient unsaved form state;
- dismissed non-authoritative UI hints.

Forbidden browser-local authority:

- project lifecycle;
- approvals;
- run status;
- document validity;
- relation state;
- package binding;
- GitHub change-set state;
- governance decision;
- catalog state.

### 2.4 Capability maturity must be visible

Every feature is one of:

- `LIVE`
- `BACKEND_NO_API`
- `API_NO_UI`
- `PLANNED_BLOCKED`
- `OPTIONAL_FUTURE`
- `NOT_APPLICABLE`

A planned feature may be visible for roadmap orientation but must be disabled and labeled. It must never simulate successful backend behavior.

### 2.5 Exact identity over friendly ambiguity

Friendly names are useful, but critical governed objects must expose copyable exact identity:

- project ID;
- run/execution ID;
- document logical ID;
- revision ID/hash;
- package/revision ID;
- Git commit/blob SHA;
- proposal payload hash;
- catalog/query identity when GAC exists;
- external agent session identity when AI-P0+ exists.

---

## 3. Design direction

### 3.1 Visual character

The product must feel:

- serious;
- calm;
- scientific;
- technical;
- trustworthy;
- modern SaaS;
- suitable for long-duration expert work.

Avoid:

- decorative consumer-app styling;
- excessive gradients;
- gamification;
- fake activity;
- marketing copy inside operational screens;
- large illustration blocks that displace research state.

### 3.2 Dark and light modes

Both modes are first-class and must have equivalent information hierarchy.

Use semantic tokens rather than direct component colors:

```text
--bg-app
--bg-sidebar
--surface-1
--surface-2
--surface-elevated
--border-subtle
--text-primary
--text-secondary
--text-muted
--accent-primary
--status-success
--status-warning
--status-danger
--status-info
--status-planned
--focus-ring
```

Rules:

- status meaning cannot depend on color alone;
- all status pills contain text/icon;
- graphs and charts must remain distinguishable in both themes;
- theme preference may be browser-local because it is not authoritative product state;
- default supports `System | Light | Dark`;
- theme parity applies to the **entire shell**, including sidebar, top bar, content surfaces, overlays/drawers, inspectors and graph chrome;
- Light mode must not leave a permanently dark-only navigation shell when the approved baseline defines a full-shell light treatment; Dark mode preserves the same information hierarchy.

### 3.3 Density

Default density: professional/compact, not spreadsheet-dense.

Provide consistent spacing and no arbitrary one-off layouts.

Baseline desktop geometry:

- expanded sidebar: ~260 px;
- collapsed sidebar rail: ~68 px;
- top bar: ~60 px;
- context/project subnavigation: ~48 px;
- main content: fluid;
- collapsing the desktop sidebar must reclaim the released layout width; a hidden/68 px sidebar must not leave an empty ~260 px grid track;
- inspector panel: ~320–380 px when open.

### 3.4 Sidebar behavior

Expanded sidebar shows a **semantic icon + label + group**.

Collapsed sidebar shows semantic icons only, with tooltip on hover/focus. Single-letter placeholders derived from labels (for example `Home -> H`) are not accepted as the production icon system.

Collapse state is presentation preference only.

Future/blocked sections retain a small maturity marker in expanded mode and tooltip in collapsed mode.

---

## 4. Global information architecture

### 4.1 Global sidebar

```text
HOME
  Home

PROJECTS
  Projects

OPERATIONS
  Runs
  Approvals
  Audit
  Runtime

RESEARCH
  Packages
    Domains
    Skills
    Usage
  Reference Acquisition          [PLANNED]

SHARED
  Shared Library                 [PLANNED]

AI
  Agents / Codex                 [PLANNED]

SYSTEM
  GitHub
  Access
  Diagnostics
  Settings
```

There is no generic “Integrations marketplace”.

At the current implementation frontier:

- GitHub is the only implemented plugin/integration family;
- OIDC is an authentication boundary, not an app marketplace item;
- markdownlint/Vale/Lychee are validation tooling, not user-facing SaaS connectors;
- Codex/MCP/Claude/Gemini/ARC are future Agent Interoperability capabilities;
- external research providers belong to future Reference Acquisition.

### 4.2 Global top bar

Must include:

- tenant/workspace context;
- command/navigation palette; resource filtering/search follows the bounded search contract in §34A.2;
- current environment/runtime indicator;
- notifications/attention count;
- theme toggle;
- current actor/avatar;
- actor menu;
- exact version/build accessible from product info.

Global search must not invent cross-project discovery semantics before GAC/search capability exists. Before GAC, search scope is restricted to resources for which authoritative indexed/list APIs exist.

---

## 5. Home — system command dashboard

Home answers one question:

> What is GWF doing right now, and what needs my attention?

Home must not contain the document relations graph.

### 5.1 Primary KPI row

Required cards:

- Total Projects;
- Active Projects;
- Running Runs / Executions;
- Pending Approvals;
- Failed / Attention Required;
- System Health.

“Active Project” must be derived from authoritative runtime state, for example a non-terminal orchestration/phase, active distributed job, running run, or equivalent current execution activity.

Do not infer activity from last-modified timestamps alone.

### 5.2 Active Projects table

Columns:

- Project;
- Domain;
- Current stage/phase;
- Active run/execution;
- Activity state;
- Current actor/executor using the deterministic identity rule in §34A.2;
- Last authoritative event;
- Attention status.

Current GWF agent-protocol execution may be shown as execution activity. External Codex/Claude/etc. must not be shown as active agent sessions until AI-P0+ exists.

### 5.3 Live Runs / Executions

Columns:

- Run/execution ID;
- Project;
- Workunit/phase;
- Status;
- Started;
- Duration;
- Actor/executor;
- latest event;
- action/inspect.

### 5.4 Attention Required

Aggregate:

- pending approvals;
- failed runs;
- recovery proposals awaiting human decision;
- blocked/stale governance state where existing APIs expose it;
- GitHub change-set conflicts;
- system/runtime degradation.

### 5.5 Recent Activity

Chronological authoritative event feed.

No fabricated “AI summary” is allowed unless a real summarized-result service exists. A normal deterministic activity summary is allowed.

### 5.6 Home API requirement

Prefer a read-only `HomeSummary` projection/API instead of N+1 browser fan-out over every project.

It may aggregate existing authoritative tables/services but must not create new governance semantics.

---

## 6. Projects index

### 6.1 Projects list

Required fields:

- Name;
- Project ID;
- Tenant/workspace;
- Lifecycle;
- Domain package/revision;
- current execution state;
- active runs/jobs;
- pending approvals;
- last authoritative event;
- created date.

Filters:

- Active / Archived;
- tenant/workspace;
- domain;
- activity;
- attention required.

### 6.2 Project creation

Project creation flow:

```text
select tenant/workspace
  -> project name
  -> optional published domain revision
  -> review exact scope
  -> create
  -> Project Overview
```

No package or domain revision may silently float after creation. `DomainRegistryService.pin_project` accepts only a PUBLISHED Domain revision and the project binding is immutable; no upgrade action appears until an explicit governed upgrade flow exists.

---

## 7. Project workspace

Selecting a project changes the product into a project-scoped workspace.

### 7.1 Project header

Always show:

- project name;
- project ID;
- lifecycle state;
- tenant/workspace;
- pinned domain package/revision;
- current activity;
- exact context breadcrumb.

### 7.2 Project-local navigation

```text
Overview
Execution
Library
Governance
Configuration
```

This is a second-level navigation, not a duplicate global sidebar.

---

## 8. Project Overview

The Project Overview answers:

> What is happening in this project?

### Required sections

- lifecycle/status;
- current orchestration/phase;
- active run/execution;
- current actor/executor using the deterministic identity rule in §34A.2;
- pending approvals;
- failures/recovery;
- latest handoff;
- recent activity;
- package/domain configuration summary;
- GitHub binding summary;
- document/governance health summary when available;
- validity frontier summary;
- distributed job summary.

No relations graph on the overview page.

---

## 9. Project Execution

### 9.1 Runs & Process

Show:

- orchestration history;
- current orchestration;
- phase timeline;
- current phase;
- runs;
- workunit;
- start/end/duration;
- input/output identities;
- generated evidence;
- failures;
- current event stream.

### 9.2 Agent protocol

Represent the actual GWF phase protocol:

```text
LOAD
 -> PREFLIGHT
 -> PLAN
 -> EXECUTE
 -> VERIFY
 -> HANDOFF
 -> COMPLETE
```

UI must show:

- current stage;
- preflight result;
- loaded skill revision/hash;
- frozen plan revision;
- checklist;
- step execution;
- QA/verification;
- handoff;
- completion.

Do not expose hidden model chain-of-thought.

### 9.3 Recovery

Show:

- problem;
- failure classification;
- recovery mode;
- retry budget;
- retry count;
- proposal;
- human decision if required;
- applied result;
- preserved prior failed evidence.

### 9.4 Live activity

Use `/product/phases/{phase_execution_id}/events/stream`; reconnect with `Last-Event-ID`. If SSE transport fails, show `Live stream unavailable` and use the authoritative GET event list.

Browser refresh must reconstruct state from the backend.

---

## 10. Project Library

**Project Library** is not the future Shared Library/GAC.

Project Library is the project-scoped working view of governed knowledge and evidence already belonging to one project.

```text
Project
  -> Library
      -> Documents
      -> Artifacts
      -> Evidence
      -> Relations & Lineage
      -> References             [only when RA exists]
```

The Library landing page provides counts/status and recent items, but deep relation visualization belongs to a selected object/document.

---

## 11. Documents

### 11.1 Documents list

Columns/filters:

- logical document ID;
- title;
- role/class;
- active revision;
- lifecycle;
- validity;
- authority state;
- QA/findings summary;
- last update;
- source identity;
- owner;
- enrolled vs legacy state.

### 11.2 Document detail

Tabs:

```text
Overview
Content
Revisions
QA & Findings
Authority
Relations
Audit
```

Future tabs may appear when backend exists:

- Impact;
- Change Sets;
- Generated provenance.

### 11.3 Overview

Must display:

- logical identity;
- title;
- role;
- governance state;
- owner;
- active revision;
- exact source;
- lifecycle;
- validity;
- QA status;
- authority summary;
- relation count;
- latest classification if available.

### 11.4 Revisions

Show exact revision history:

- revision ID;
- revision number/version;
- payload/source hash;
- created/activated time;
- source path/blob/commit for GitHub-backed revisions; otherwise show the exact source-kind identity returned by the backend;
- QA status for that exact revision;
- supersession/archive relationship when implemented.

A PASS on an old revision must not visually imply current revision PASS.

### 11.5 QA & Findings

Show validator execution and finding lifecycle without using `Finding_checklist.md` as runtime state.

Runtime document findings are separate product records.

Required:

- validator/tool;
- version;
- target revision;
- outcome;
- finding code;
- severity;
- lifecycle;
- resolution evidence;
- waiver where permitted;
- exact timestamps/actors.

### 11.6 Authority

Show:

- authority key;
- scope;
- active claim;
- composition;
- conflicting/duplicate authority;
- actor/provenance;
- active/retired history.

### 11.7 Quick Preview and full-screen Reader

Documents are knowledge/work products, not metadata-only registry rows.

Selecting a document from a list or selecting a document node in a relation graph opens a **Quick Preview** in the contextual inspector. The default inspector tabs are:

```text
Preview | Details | Relations | History
```

Quick Preview shows useful governed content, not only tags/IDs. At minimum it includes the document title/type, exact resolved revision identity, status/validity summary, and rendered/readable content sufficient for orientation.

Because research documents, protocols and papers may be long and information-dense, Quick Preview must provide an explicit **Expand / Full screen** action opening a near-full-screen Reader Mode.

Reader Mode requirements:

- readable long-form content with normal scrolling;
- exact logical document ID and exact revision visible;
- lifecycle/validity/status visible without dominating the reading surface;
- exact source/hash/provenance reachable from the reader;
- `Close` / `Back to graph` returns to the same prior list/graph context and selected root/node;
- Reader Mode is a projection of the authoritative revision, never browser-authored product truth.

DG-P9 resolution semantics apply to preview:

- `LOGICAL_CURRENT` previews the exact revision resolved as current at read time and identifies it as current;
- `PINNED_REVISION` previews the exact pinned revision even when it is no longer current and visibly labels the pinned/current distinction;
- a historical pinned preview must not silently float to the latest revision.

Source-code preview, isolated execution and explainable replay are future work recorded in `TD-UX-03`; they are not authorized by the document Reader requirements above.

---

## 12. Relations & Lineage graph

The graph is **document/object contextual**, never a Home dashboard widget.

Primary path:

```text
Projects
  -> Project
      -> Library
          -> Documents
              -> select Document
                  -> Relations
```

### 12.1 Root selection

The selected document is the graph root.

Default graph:

- 1 hop;
- active relations;
- incoming + outgoing;
- maximum visual density bounded;
- exact IDs available on hover/inspector.

### 12.2 Interaction

Single click node:

- select node;
- update right inspector;
- default the inspector to the selected document's **Preview** tab when the node resolves to a document;
- do not change graph root.

Explicit `Set as root` action:

- changes root;
- reloads graph around new root;
- updates breadcrumb/history.

Browser back restores prior root.

### 12.3 Relation inspector

For an edge show:

- relation type;
- source document/revision;
- target kind/identity;
- active/retired;
- creation provenance;
- binding mode;
- exact target revision/hash whenever `target_binding_mode=PINNED_REVISION`; never show a pinned hash for `LOGICAL_CURRENT`;
- current resolution;
- failure state.

### 12.4 Binding visualization

`LOGICAL_CURRENT` and `PINNED_REVISION` must be visually distinguishable.

Suggested convention:

- dashed edge: `LOGICAL_CURRENT`;
- solid edge + lock marker: `PINNED_REVISION`.

Binding legend is fixed: dashed edge = `LOGICAL_CURRENT`; solid edge plus lock marker = `PINNED_REVISION`. The edge inspector also prints the binding-mode text.

### 12.5 Modes

```text
Relations   LIVE after DG-P8/P9 API/UI
Lineage     partial/current revision lineage, expanding with DG-P15
Impact      PLANNED until DG-P12/P13
```

Impact controls remain disabled until backend implementation passes.

### 12.6 Filters

- relation type;
- direction;
- object kind;
- active/retired;
- logical/pinned;
- depth;
- current/historical.

No relation may be fabricated from Markdown hyperlinks or inferred text unless an explicitly governed future relation-inference feature is implemented.

---

## 13. Artifacts & Evidence

### 13.1 Artifacts

Display:

- artifact stable ID;
- revision(s);
- producer;
- project;
- object refs;
- hashes;
- validity;
- provenance;
- related run/workunit.

### 13.2 Evidence

Display:

- evidence ID/type;
- exact producing run;
- exact target/resource;
- payload identity;
- timestamps;
- actor/executor;
- audit/provenance;
- applicability only when owned by the relevant domain semantics.

### 13.3 Checkpoints

For every checkpoint record returned by a phase/run inspection or resume flow, show:

- checkpoint ID;
- run/workunit;
- state;
- resume/reconciliation result;
- validity.

---

## 14. Project Governance

Project Governance navigation:

```text
Approvals
Audit
Document Governance
Failures & Recovery
```

### 14.1 Approvals

Show:

- pending proposal;
- action;
- resource refs;
- frozen payload;
- exact payload hash;
- approval policy;
- proposer;
- created time;
- approve exact hash;
- reject with reason;
- decision history.

### 14.2 Audit

Project-scoped chronological audit with filters:

- actor;
- action/event;
- resource;
- time range;
- outcome.

### 14.3 Document Governance summary

Project-level aggregate of:

- document validity;
- open runtime findings;
- duplicate authority conflicts;
- relation/binding issues;
- pending governed document changes when later implemented.

---

## 15. Project Configuration

Project Configuration:

```text
Packages
GitHub
Agent Protocol
Members & Access
Settings
```

### 15.1 Packages

Show the exact configuration used by this project.

#### Domain

- package ID/name;
- domain ID;
- pinned domain revision;
- semantic version;
- payload hash;
- status;
- binding time/actor.

Project domain binding is immutable under the current backend contract. UI must not provide a silent “upgrade to latest” action.

#### Skills

Skill usage is not the same as project package installation.

Display two concepts:

- **Configured skill usage** — skill revisions reachable from the project's pinned domain/workunit bindings;
- **Observed skill usage** — exact skill revisions actually loaded by project phase executions.

Show:

- skill package;
- revision ID;
- version;
- content hash;
- workunit type;
- required tools;
- QA contract;
- Configured / Observed state.

No duplicate project-skill source-of-truth table should be created solely for UI if the information can be derived from authoritative bindings/executions.

### 15.2 GitHub

Only GitHub is LIVE as an external plugin family today.

Project configuration must support:

- PluginConnection;
- opaque external connection reference;
- capabilities;
- active/disabled status;
- repository binding;
- repository full name;
- default branch;
- allowed branches;
- write policy;
- exact identity state;
- SHA-safe change sets;
- preflight;
- stale conflict;
- execute;
- COMMITTED vs VERIFIED;
- post-write exact verification.

No raw reusable token field is allowed.

### 15.3 Agent Protocol settings

Show/edit permitted project defaults:

- recovery mode;
- retry budget;
- effective hierarchy explanation.

### 15.4 Members & Access

Show:

- project members;
- role;
- status;
- inherited tenant/workspace authority where explainable;
- add/revoke according to permission.

---

## 16. Global Package Registry

Use the product term **Packages**, not “Installed Apps”. Domain revisions own `DRAFT|VALIDATED|PUBLISHED`; Skill revisions must show only lifecycle/state fields actually persisted by the Skill Registry and must not inherit a fake PUBLISHED state.

Global path:

```text
Research
  -> Packages
      -> Domains
      -> Skills
      -> Usage
```

### 16.1 Domain Packages

Domain package list:

- tenant;
- package ID;
- domain ID;
- name;
- package status;
- latest revision;
- latest revision status;
- number of revisions;
- project usage count.

Revision detail:

- revision ID/number;
- semantic version;
- hash;
- DRAFT / VALIDATED / PUBLISHED;
- validation report;
- published at;
- projects pinned to this exact revision.

### 16.2 Skill Packages

Skill package list/detail:

- skill package ID;
- skill ID;
- name;
- description;
- revisions;
- version;
- content hash;
- tool requirements;
- QA contract;
- domain/workunit bindings.

Do not invent a PUBLISHED state if the current skill registry does not own that lifecycle.

### 16.3 Package Usage — two-way projection

The UI must support both directions:

```text
Project -> Packages
Package -> Projects
```

#### Project → Packages

Show:

- pinned Domain revision;
- configured Skill revisions;
- observed Skill revisions used by executions.

#### Package → Projects

For Domain revision:

- all projects pinned to that exact revision.

For Skill revision:

- projects configured to resolve the revision through domain/workunit bindings;
- projects with observed executions that loaded the revision.

Label usage basis:

- `CONFIGURED`;
- `OBSERVED`.

### 16.4 Package Usage API rule

Package usage is a read projection.

Required implementation:

- derive from `project_domain_bindings`;
- `domain_skill_bindings`;
- `phase_execution_protocols` / loaded skill revision records;
- existing project/domain registry data.

Do not create a parallel mutable package-usage truth table merely for UI convenience.

### 16.5 “Behind latest” indicator

The UI may show:

```text
Pinned: r15
Latest published: r17
2 revisions behind
```

This is informational only.

It must never imply automatic upgrade authorization.

---

## 17. Global Operations

### 17.1 Runs

Cross-project run/execution view with scope filters.

### 17.2 Approvals

Cross-project pending approval inbox for resources the actor is authorized to review.

### 17.3 Audit

Cross-project audit only within the actor's authorized scope.

### 17.4 Runtime

Distributed runtime operational view:

- jobs;
- workers;
- leases;
- attempts;
- capacities/capabilities;
- recovery/requeue;
- project/run linkage.

---

## 18. Global Research

### 18.1 Domains & Skills

Implemented through Package Registry.

### 18.2 Reference Acquisition

`PLANNED_BLOCKED` until RA implementation.

When enabled, it must include:

- query plan;
- executed queries;
- source/provider observations;
- registry;
- exact inspected identities;
- dedup;
- evidence map;
- coverage;
- temporal mode;
- GAC discovery provenance.

No fake provider connectors before implementation.

---

## 19. Shared Library

**Shared Library** means the future cross-project GAC-backed capability.

It is not the Project Library.

Current state: `PLANNED_BLOCKED`.

When GAC product core passes, the browser must support:

- catalog entries;
- exact subject identity;
- publication state;
- eligibility;
- publish/withdraw/supersede;
- deterministic metadata query;
- query execution identity;
- catalog snapshot;
- access intersection;
- source validity observation;
- PARTIAL/backend failure distinct from zero results;
- ObjectRef subjects;
- external immutable refs when GAC-P2B exists.

Do not expose a second canonical payload store.

---

## 20. Agents / Codex

Current state: `PLANNED_BLOCKED`.

Until AI-P0/AI-P2 pass, menu may be visible with a Planned badge but no fake Connect or Run button.

When implemented:

- Codex harness identity;
- opaque connection ref;
- workspace/repository scope;
- tool capabilities;
- locality/network/privacy constraints;
- maximum authority;
- execution ID;
- Codex session/thread;
- AgentExecutionEnvelope;
- evidence/trace;
- executor success separate from GWF PASS.

Claude/Gemini/ARC appear only after their own backend items pass.

---

## 21. GitHub is not an integration marketplace

Global/System GitHub page provides:

- connection status;
- projects using GitHub;
- connection refs;
- capabilities;
- bound repositories;
- health/preflight status;
- recent governed change sets.

Project GitHub page provides project-specific configuration/actions.

No unrelated SaaS logos or placeholders are permitted.

---

## 22. Organization and Access

Global Access UI should expose only real identity/multitenancy concepts:

- actor/session;
- tenants;
- workspaces;
- memberships;
- project memberships;
- roles;
- revocation.

Where read/list APIs are currently missing, BPS implementation must add bounded read projections rather than infer state in the browser.

---

## 23. System Diagnostics

Must expose operationally meaningful v0.5+ foundation state:

- product version;
- exact Git SHA/build;
- backend type;
- database connectivity;
- object store/CAS status;
- observability status;
- server uptime/readiness;
- domain/runtime identity;
- GitHub adapter status;
- capability matrix;
- current feature maturity states.

Infrastructure-only components may be read-only.

---

## 24. Route architecture

Suggested browser routes:

```text
/app/home

/app/projects
/app/projects/:projectId/overview
/app/projects/:projectId/execution
/app/projects/:projectId/execution/runs/:runId
/app/projects/:projectId/library
/app/projects/:projectId/library/documents
/app/projects/:projectId/library/documents/:documentId
/app/projects/:projectId/library/documents/:documentId/relations
/app/projects/:projectId/library/artifacts
/app/projects/:projectId/library/evidence
/app/projects/:projectId/governance/approvals
/app/projects/:projectId/governance/audit
/app/projects/:projectId/governance/documents
/app/projects/:projectId/configuration/packages
/app/projects/:projectId/configuration/github
/app/projects/:projectId/configuration/agent-protocol
/app/projects/:projectId/configuration/access

/app/operations/runs
/app/operations/approvals
/app/operations/audit
/app/operations/runtime

/app/research/packages/domains
/app/research/packages/skills
/app/research/packages/usage
/app/research/reference-acquisition            [PLANNED]

/app/shared-library                            [PLANNED]
/app/agents                                    [PLANNED]

/app/system/github
/app/system/access
/app/system/diagnostics
/app/system/settings
```

Routes are browser organization, not permission boundaries. Backend authorization remains authoritative.

---

## 25. API/product-surface gaps to implement

The UI must not work around missing authoritative APIs with fake state.

### 25.1 Existing API-backed areas needing UI

- auth/login/me;
- projects;
- lifecycle;
- dashboard;
- domain registry;
- agent protocol;
- process/phases/events;
- approvals;
- audit;
- runtime/distributed;
- GitHub/plugin.

### 25.2 Read projections/API gaps

Bounded API work is required for:

- global Home summary;
- tenant/workspace/member listing where absent;
- complete skill package/revision listing;
- Package Usage reverse lookup;
- global runs/approvals/runtime projections when current APIs are project-scoped;
- artifact/revision/evidence explorer;
- document governance P0→P10;
- document relations graph;
- diagnostics/status aggregation.

### 25.3 Mutation rule

Any new browser mutation endpoint must invoke the same native service/authority/idempotency/audit path as non-browser execution.

No UI-only mutation semantics.

---

## 26. User flows

### 26.1 Daily operator flow

```text
Login
 -> Home
 -> identify Active Project / Attention Required
 -> Project Overview
 -> Execution / Approval / Library as needed
 -> governed action
 -> backend audit
 -> return Home
```

### 26.2 Run inspection

```text
Home or Operations/Runs
 -> Run
 -> Project context
 -> phase timeline
 -> inputs / outputs / evidence
 -> live events
 -> failures/recovery
 -> verification/handoff
```

### 26.3 Document relation flow

```text
Project
 -> Library
 -> Documents
 -> select document
 -> Relations
 -> 1-hop graph
 -> inspect node/edge
 -> Set as root if desired
```

### 26.4 Approval flow

```text
Home Attention
 or Operations/Approvals
 -> Proposal
 -> frozen payload/hash
 -> inspect resource/project context
 -> Approve exact hash or Reject with reason
 -> authoritative decision/audit
```

### 26.5 Package inspection flow

```text
Research / Packages
 -> Domain or Skill
 -> exact revision
 -> Usage
 -> projects configured/observed
 -> open Project Configuration
```

### 26.6 Project package flow

```text
Project
 -> Configuration
 -> Packages
 -> pinned Domain
 -> derived Skills
 -> exact revisions/hashes
 -> optional compare with latest
```

No silent upgrade.

### 26.7 GitHub flow

```text
Project
 -> Configuration
 -> GitHub
 -> Connection
 -> Repository Binding
 -> Prepare Change Set
 -> expected SHA
 -> Preflight
 -> Execute
 -> Verify
```

### 26.8 Future Shared Library flow

Only after GAC:

```text
Shared Library
 -> query
 -> exact catalog snapshot/result
 -> select governed entry
 -> source project/artifact/document
```

### 26.9 Future Codex flow

Only after AI-CODEX-G0:

```text
Agents / Codex
 -> governed harness configuration
 -> project/workspace scope
 -> execution
 -> Codex session/thread
 -> normalized AgentExecutionEnvelope
 -> GWF verification/gate
```

---

## 27. Component patterns

Required reusable UI primitives:

- StatusBadge;
- MaturityBadge;
- ExactIdentity;
- CopyIdentityButton;
- ProjectBreadcrumb;
- DataTable;
- FilterBar;
- Timeline;
- PhaseStepper;
- ApprovalCard;
- AuditEvent;
- RunStatus;
- EventStream;
- InspectorDrawer;
- RelationGraph;
- RevisionHistory;
- PackageRevisionBadge;
- UsageBasisBadge;
- CapabilityMatrix;
- EmptyState;
- ErrorState;
- LoadingSkeleton;
- ConfirmGovernedAction dialog.

Governed-action confirmations must show exact target identity and consequences, not generic “Are you sure?” dialogs.

---

## 28. Loading, empty, partial and failure states

Every data module must distinguish:

- loading;
- true empty result;
- unauthorized/not visible;
- backend failure;
- partial result;
- stale data;
- blocked capability;
- planned capability.

Examples:

- GAC backend failure must never look like “0 Library results”;
- failed run query must never look like “no runs”;
- GitHub adapter unavailable must not look like “repository empty”;
- document relation resolver failure must not look like “no relations”.

---

## 29. Accessibility and keyboard operation

Minimum:

- WCAG AA contrast target;
- visible focus;
- keyboard sidebar/navigation;
- keyboard table actions;
- graph nodes/edges reachable through alternative list/inspector representation;
- no color-only status;
- reduced-motion support;
- descriptive labels for icons;
- dark/light parity.

Graph accessibility requires a structured relation table equivalent to the visual graph.

---

## 30. Responsive behavior

Primary target: desktop research workstation.

### >= 1280 px

Full 3-column expert layouts allowed.

### 1024–1279 px

Inspector becomes drawer; tables reduce noncritical columns.

### < 1024 px

Sidebar collapses by default; graph becomes canvas + drawer; high-risk mutations remain usable but should not hide exact identity.

Mobile (<768 px) is outside UX-W0 acceptance for graph/document-authoring/configuration. It must still support login, Home, project/run status, approval inspection/decision and diagnostics. Desktop is required for dense governance and graph work.

---

## 31. Security/privacy UX

- no raw reusable credentials;
- connection refs may be shown if not secret;
- sensitive IDs scoped by authorization;
- tenant isolation must not leak hidden resource existence;
- irreversible/high-impact actions show exact scope;
- session expiry handled explicitly;
- browser logs must not contain secrets;
- static/public assets contain no operational credentials.

---

## 32. Implementation sequence

### UX-I0 — Foundation shell

- canonical server launcher;
- live app shell;
- auth/session;
- theme;
- collapsible sidebar;
- routing;
- capability maturity service;
- diagnostics/build identity.

### UX-I1 — Global operational product

- Home;
- Projects index;
- Operations Runs/Approvals/Audit/Runtime;
- Access;
- live replacement of legacy static dashboard/process/approval/recovery/runtime views.

### UX-I2 — Project workspace

- Project Overview;
- Execution;
- Governance;
- Configuration;
- GitHub;
- Agent Protocol;
- project package view.

### UX-I3 — Packages

- Domains;
- Skills;
- Usage;
- Project→Packages;
- Package→Projects;
- configured vs observed skill usage.

### UX-I4 — Project Library foundation

- Artifacts;
- Evidence;
- checkpoints;
- read projections.

### UX-I5 — Documents DG-P0→P10 API + UI

- document APIs;
- list/detail/revisions;
- Quick Preview;
- full-screen Reader Mode;
- QA/findings;
- lifecycle/validity;
- authority;
- relations/binding;
- classification/authority plan.

### UX-I6 — Relations graph

- selected-document root;
- 1-hop relation graph;
- inspector;
- exact binding;
- root navigation;
- accessible relation table.

### UX-W0 — Full current product browser readiness

Requires all user/operator-relevant v0.5→v0.8.5 and DG-P0→P10 capability to be LIVE in browser or explicitly `NOT_APPLICABLE` with written rationale.

Only after UX-W0/BPS-W0 and separate authorization does the roadmap resume DG-P11.

### Future

After backend gates:

- Shared Library/GAC UI;
- Reference Acquisition UI;
- Codex/Agent UI;
- Impact graph;
- document ChangeSet UI.

---

## 33. Browser UAT scenarios

Browser UAT must be human-operable against the real installed product.

Minimum current-product UAT:

1. install product;
2. start canonical server;
3. open browser;
4. login;
5. verify Home counts from backend;
6. open active project;
7. inspect project execution;
8. inspect live event stream;
9. inspect/act on an approval with exact hash;
10. inspect project packages;
11. open global Package Registry;
12. verify Package→Projects and Project→Packages;
13. inspect GitHub binding/change-set state;
14. inspect Project Library artifacts/evidence;
15. open Documents;
16. inspect exact revision/QA/validity/authority;
17. quick-preview a document and verify meaningful content plus exact resolved revision;
18. expand the document into full-screen Reader Mode and return to the same prior context;
19. open selected document Relations graph;
20. verify relation/binding identity;
21. verify LOGICAL_CURRENT vs PINNED_REVISION preview semantics;
22. switch graph root;
23. reload browser and confirm state comes from backend;
24. switch dark/light theme and verify full-shell parity;
25. collapse/expand sidebar and verify the main workspace reflows;
26. verify semantic navigation icons and collapsed tooltips/maturity;
27. verify unauthorized resources are not leaked;
28. verify diagnostics/version/HEAD.

A static or localStorage simulation is UAT INVALID.

---

## 34. Module completeness matrix

| Module | Global UI | Project UI | Current maturity | Required before UX-W0 |
| --- | --- | --- | --- | --- |
| Server/health/version | Diagnostics | summary | API/backend exists, launcher gap | LIVE |
| Auth/session | top-level | inherited | API exists | LIVE |
| Tenant/workspace/access | Access | Members & Access | backend/API partial UI gap | LIVE |
| Projects | Projects | Overview | API exists | LIVE |
| Dashboard | Home | Overview | API exists/static UI | LIVE |
| Runs/process | Operations | Execution | API exists/static UI | LIVE |
| Agent protocol | — | Execution | API exists/static UI | LIVE |
| Recovery | Operations attention | Execution/Governance | API exists/static UI | LIVE |
| Approvals | Operations | Governance | API exists/static UI | LIVE |
| Audit | Operations | Governance | API exists | LIVE |
| Distributed runtime | Runtime | Execution summary | API exists/static UI | LIVE |
| Domains | Packages | Configuration | registry/API exists | LIVE |
| Skills | Packages | Configuration | registry + partial API | LIVE |
| Package Usage | Packages/Usage | Configuration/Packages | derivable, API gap | LIVE |
| GitHub | System/GitHub | Configuration/GitHub | API exists | LIVE |
| Artifacts/Revisions | optional global search later | Library | backend partial API | LIVE |
| Evidence | — | Library | backend partial API | LIVE |
| Documents DG-P0→P10 | — | Library/Documents | backend services, API gap | LIVE |
| Relations graph | — | Document/Relations | backend relation service, API/UI gap | LIVE |
| Shared Library/GAC | Shared Library | link/view later | PLANNED_BLOCKED | not required for UX-W0 |
| Reference Acquisition | Research | Library/References later | PLANNED_BLOCKED | not required for UX-W0 |
| Codex/Agents | Agents/Codex | execution later | PLANNED_BLOCKED | not required for UX-W0 |
| Impact graph | — | Document/Impact | PLANNED_BLOCKED | not required for UX-W0 |

---


## 34A. QA closure — normative traceability and exact semantics

This section is normative and resolves any earlier generic wording in this document. If a preceding sentence is less specific than this section, this section controls implementation.

### 34A.1 Source precedence

UI semantics must be traced in this order:

1. current qualified runtime/service/storage behavior;
2. formally closed milestone specification/handoff for that capability;
3. `docs/IMPLEMENTATION_7_WAVES_PLAN.md` for dependency/authorization order;
4. `docs/BROWSER_PRODUCT_SURFACE_SPEC.md` for browser authority/maturity;
5. this document for navigation and presentation.

Core references:

| Capability | Governing docs | Primary source |
| --- | --- | --- |
| Gate/Decision/Failure/PIVOT/Recovery/Checkpoint | `HANDOFF_V0.2.md`, `IMPLEMENTATION_QA_V0.2.md` | `decision.py`, `execution.py`, `knowledge.py`, `research_orchestrator.py` |
| Retrieval + verifier provenance | `HANDOFF_V0.3.md`, `V0.4_HARDENING_REPORT.md`, `IMPLEMENTATION_QA_V0.4.md` | `retrieval.py`, `provider_chain.py`, `stat_verifier.py`, `tabular_verifier.py` |
| Development data foundation | `DATA_FOUNDATION_V0.4.1.md`, `HANDOFF_V0.5.md` | `datasets.py` + benchmark tooling |
| Production foundation | `V0.5_PRODUCTION_FOUNDATION.md` | DB/migrations/CAS/provider/observability modules |
| Identity/multitenancy | `V0.6_IDENTITY_MULTITENANCY.md`, `HANDOFF_V0.6.md` | `auth.py`, `tenancy.py` |
| Distributed runtime | `V0.7_DISTRIBUTED_RUNTIME.md`, `HANDOFF_V0.7.md` | `distributed.py` |
| Product dashboard | `V0.8_RESEARCH_PRODUCT_ALPHA.md`, `HANDOFF_V0.8.md` | `product.py`, `api.py` |
| Lifecycle/process/domain | `V0.8.1_PRODUCT_LIFECYCLE_PROCESS_INSPECTOR.md` | project/process/domain services |
| Agent protocol/skills | `V0.8.2_PROJECT_GOVERNANCE_AGENT_PROTOCOL.md` | `agent_protocol.py` |
| Orchestrator/SSE/handoff | `v0.8.3-orchestrator-integration.md` | orchestrator/protocol/API |
| GitHub | `v0.8.4-github-plugin-sha-qa.md`, `GITHUB_SHA_QA_STANDARD.md` | plugin/GitHub services |
| Domain/Skill maturity | `DOMAIN_SKILL_AUDIT_V0.8.5.md` | domain/skill services |
| Documentation Governance | `DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` + DG-P0…P10 specs | `document_*.py` |
| GAC / Shared Library | `GOVERNED_ARTIFACT_CATALOG_SPEC.md` | future gated |
| Reference Acquisition | `V0.8.6_REFERENCE_ACQUISITION_SPEC.md` | future gated |
| Agent Interoperability | `V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` | future gated |

### 34A.2 Deterministic product terminology

**Project lifecycle** is exactly `ACTIVE | ARCHIVING | ARCHIVED`, owned by `ProjectGovernanceService`.

**Project execution activity** is derived separately:

- `EXECUTING`: any project run is RUNNING, or latest orchestration is RUNNING, or a distributed job is LEASED/RUNNING;
- `PAUSED`: no EXECUTING condition and latest orchestration is PAUSED;
- `QUEUED`: no EXECUTING/PAUSED condition and a distributed job is READY;
- `IDLE`: none of the above.

The UI must never equate lifecycle `ACTIVE` with “agent active”.

**Current actor/executor** before AI-P0 is the latest authoritative actor_id from the current phase/protocol/event when present; otherwise `SYSTEM` or `—`. It is not labeled “Agent”. After AI-P0, external executor identity comes only from AgentExecutionEnvelope/binding identity.

**Attention item** is one unresolved authoritative record ID from: PENDING_APPROVAL proposal; unresolved FailureRecord; WAITING_HUMAN protocol recovery proposal; GitHub ChangeSet STALE/VERIFICATION_FAILED; and, only after DG browser APIs are LIVE, current DocumentFinding/effective BLOCKED document. Count records by stable ID, not project count.

**Core health** is categorical `HEALTHY | DEGRADED | UNHEALTHY | UNKNOWN`. UX-W0 must not invent uptime percentages. Required probes are server readiness, DB connectivity/migration state, CAS/object-store verification, and observability sink state. External GitHub/provider health is separate.

**Workflow phases** are never hard-coded as a generic Idea→Design→Execute flow. Labels/order come from the project's exact pinned Domain Package and persisted orchestration.

**Search** before a governed cross-project search exists is a command/navigation palette plus page-scoped authoritative filtering. Cross-project artifact/document search opens only through a qualified bounded search API or GAC.

**Zero results** are shown only after a successful complete query. Unauthorized, failed, partial, stale and blocked states each render distinctly.

### 34A.3 Home exact semantics

Home is operational only; no document/knowledge graph.

Required KPI definitions:

- Total Projects = authorized projects under selected scope;
- Lifecycle Active = projects whose lifecycle is exactly ACTIVE;
- Executing Now = projects whose execution activity is EXECUTING;
- Running Runs = runs whose runtime_status is RUNNING;
- Pending Approvals = visible proposals with status PENDING_APPROVAL;
- Attention Required = §34A.2 attention-item count;
- Core Health = categorical §34A.2 state.

The Executing Projects table must show project ID/name, lifecycle, execution activity, exact Domain revision, orchestration ID, phase-execution ID/domain phase label, current actor/executor, running run ID, latest event timestamp and attention count.

UX-I1 must add an authorized read-only `HomeSummary` projection returning these aggregates plus `generated_at` and exact build identity. It owns no authoritative state.

### 34A.4 Complete Project Execution coverage

Project Execution must expose the existing v0.2→v0.8.3 state, not only Agent Protocol.

For a selected phase/run show:

- orchestration ID/status/generation/outcome/pivot count;
- phase history and previous attempts;
- WorkUnit ID/type/status, input revisions, output contracts, preconditions, required gates/authorities, executor selector, execution/retry/recovery policy and conflict keys;
- Run ID/attempt/runtime status, produced revisions/evidence, exit metadata;
- Gate ID/type/policy version/scope/required inputs/evidence/result `PASS|FAIL|BLOCKED`/violation codes/evaluated refs;
- Decision type exactly `CONTINUE|RETRY|REVISE_CURRENT|REVISE_UPSTREAM|REPLAN|ESCALATE|ABORT|WAIT`;
- FailureRecord identity/class/stage/ref/revision/failed gate/evidence/severity/signature/root/resume/status;
- LoopGuard signature count/limit and retry-block state;
- PIVOT generation/history and affected/invalidation state;
- persisted ImpactSet/RecoveryPlan and resume target;
- full Checkpoint state: active/completed workunits, stage labels, valid/dirty/stale revisions, blocking failures, pending decisions/approvals, resume candidates and runtime metadata;
- Agent Protocol LOAD→PREFLIGHT→PLAN→EXECUTE→VERIFY→HANDOFF→COMPLETE, loaded Skill revision/hash, effective recovery hierarchy, prior-handoff identity/hash and events.

SSE uses `/product/phases/{phase_execution_id}/events/stream`, preserves event IDs and reconnects with `Last-Event-ID`.

### 34A.5 Three graph families are separate

1. **Failure/Recovery graph** — source: `ProjectDashboardService.failure_graph`; root/context: project/failure; edges Failure→Root and Failure→RecoveryPlan→Resume.
2. **Artifact Trace/Impact graph** — source: `KnowledgeKernel` trace links and persisted ImpactSet; root: exact artifact revision; edges use trace relation/strength/invalidation/propagation semantics.
3. **Document Relations/Lineage graph** — source: `DocumentRelationService`; root: selected governed document; P8/P9 current backend; Document Impact remains future DG-P12/P13.

A shared canvas primitive is allowed, but queries, edge semantics, legends and inspectors remain separate.

### 34A.6 Retrieval/provider and verifier evidence

Current v0.3–v0.5 paper/web retrieval is execution evidence, not future Reference Acquisition.

When persisted, render operation/query, ordered provider attempts, provider ID, success/failure/error, timing, source URL/identity/hash, cache/fallback provenance, degraded state, and failed-primary attempts preserved before later success.

Independent statistical/tabular verifier evidence renders verifier type/version, independent-process flag, input SHA-256, result SHA-256, worker/process identity when persisted, thresholds/spec and verdict/hash-mismatch failure.

These remain evidence/diagnostic views, not top-level SaaS integrations.

### 34A.7 Artifact, ObjectRef and existing impact coverage

Project Library must expose Artifact stable ID/type/logical key/lifecycle/version/current revision/revision history/producer/content hash/validity/provenance, ObjectRef content type/size/hash and CAS verification, Evidence identity/type/trust/subjects/payload/freshness/producer, and Checkpoint linkage.

Existing KnowledgeKernel Artifact Trace/Impact is current backend capability and is not the future DG Document Impact.

### 34A.8 Documentation Governance actions P3→P10

UX-I5 must add bounded service-backed HTTP contracts for:

- P3/P4 register/enroll and revise document using exact source identity/current expectations;
- P5 QA records and finding transitions: resolution-pending, reopen, verify-resolved, prepare/apply waiver, transition history;
- P6 legal lifecycle transition, inspect state and validity reconciliation;
- P7 PRIMARY/COMPOSED authority prepare/apply, collision inspection, retirement and authority-key scan;
- P8 relation declaration/apply/list/retire;
- P9 relation binding/apply/resolve;
- P10 classification with exact base revision, proposed active path/content, declared class, QA refs and phase context; show effective class/escalation/mutation-authority/archive-version plan. P10 never mutates source.

Current relation types are exactly `DEPENDS_ON|REFERENCES|MUST_ALIGN_WITH|SUPERSEDES|DERIVED_FROM|VALIDATES|IMPLEMENTS|GENERATED_FROM`.

Target kinds are `DOCUMENT|SOURCE_CODE|SCHEMA|API|WORKFLOW|DATASET|STUDY_LOCK|OTHER_ARTIFACT`. Non-document targets are typed terminal/opaque nodes; Set as root is enabled only for navigable governed-document targets.

Document graph default is root=selected document, depth=1, ACTIVE relations, incoming+outgoing, maximum 25 rendered neighbors plus deterministic overflow list/paging.

### 34A.9 Package semantics and reverse usage

Domain package/project usage comes from `project_domain_bindings` and exact immutable PUBLISHED Domain revision.

Skill usage has two bases:

- `CONFIGURED`: reachable from pinned Domain/workunit binding;
- `OBSERVED`: exact Skill revision loaded by a phase execution.

Package→Projects and Project→Packages are read projections only; no mutable duplicate usage table.

Current HTTP API lacks complete Skill list/get and Package Usage read endpoints; UX-I3 must add them.

### 34A.10 Distributed-runtime browser boundary

Runtime UI shows jobs/status, workers referenced by visible jobs, lease expiry, attempts, capacities/capabilities, required resources, conflict reservations, abandoned attempt/run history, recovery/requeue and project/run linkage.

UX-W0 is read-only for worker administration. Browser UI does not expose register_worker, heartbeat_worker, set_worker_status, lease grant/heartbeat or effect-commit mutation because those are worker/runtime protocol operations without an authenticated browser-admin contract.

### 34A.11 GitHub exact boundary

GitHub is the only current plugin family.

Plugin capabilities are exactly `REPO_READ|CONTENT_WRITE|WORKFLOW_WRITE|PULL_REQUEST_WRITE|MERGE_PULL_REQUEST`.

The UI displays assigned capabilities but exposes actions only for implemented service operations. Capability presence alone must not invent PR/merge buttons.

UX implementation must add reload-safe repository-binding list/detail and adapter-readiness reads because the current API is insufficient for authoritative refresh.

### 34A.12 Production diagnostics

Diagnostics must expose bounded read projections for:

- exact product/build SHA/runtime;
- DB backend/connectivity;
- migration IDs/checksums/status from `MigrationManager.status`;
- CAS/object-store read/write/hash-verification probe;
- observer type/sink/latest event/available metric keys;
- provider failover operational provenance when provider-event persistence is enabled;
- GitHub adapter state separately from core health;
- browser capability maturity matrix.

### 34A.13 Explicit HTTP/API obligations

Current missing browser contracts that must be added rather than faked:

1. session revoke/logout over `HumanAuthService.revoke`;
2. authorized tenant/workspace/member list projections;
3. HomeSummary;
4. cross-project Runs/Approvals/Audit/Runtime aggregation;
5. Skill package/revision list/detail;
6. Package Usage configured/observed reverse lookup;
7. GitHub repository-binding list/detail/adapter-readiness;
8. Artifact/Revision/ObjectRef/Evidence reads;
9. Gate/Decision/ImpactSet/RecoveryPlan reads;
10. production diagnostics;
11. DG-P0→P10 service-backed APIs;
12. Document Relations graph/list resolution.

Frontend must never query DB directly.

### 34A.14 Explicit source-module UI classification

| Module family | UI obligation |
| --- | --- |
| auth/tenancy | DIRECT_UI |
| knowledge | PROJECT_CONTEXT: Artifact/Revision/Trace/Impact/Validity |
| decision | PROJECT_CONTEXT: Gates/Decisions/Failure/LoopGuard/Recovery |
| execution | PROJECT_CONTEXT: WorkUnit/Run/Evidence/Checkpoint |
| orchestrators | PROJECT_CONTEXT: process/phase/handoff lineage |
| retrieval/provider_chain | PROJECT_CONTEXT + DIAGNOSTIC_READONLY provenance |
| statistical/tabular verifier workers | evidence renderer only; no menu |
| datasets + benchmark/demo executors | NOT_APPLICABLE direct production menu; resulting runtime evidence stays visible |
| DB/migrations/observability | DIAGNOSTIC_READONLY |
| object_store | DIAGNOSTIC_READONLY + artifact ObjectRef detail |
| domain/domain_sdk/domain_registry | DIRECT_UI Packages |
| agent_protocol | DIRECT_UI Skills + Project Execution/Configuration |
| distributed | DIRECT_UI read; worker mutation NOT_APPLICABLE browser action |
| product/process_inspector | DIRECT_UI Home/Project/Execution |
| project_governance | DIRECT_UI lifecycle |
| plugins/GitHub | DIRECT_UI GitHub only |
| document_* P0→P10 | DIRECT_UI project Documents/Governance |
| errors/utils/package internals | no standalone UI; map to typed error states |

Development DatasetRegistry is explicitly NOT_APPLICABLE as a production operator data module. It is development/reliability foundation; any dataset-derived project artifacts/evidence appear through normal governed Library/Execution surfaces.

### 34A.15 Historical capability closure

UX-W0 coverage includes:

- v0.2 Gate/Decision/Failure/PIVOT/Recovery/Checkpoint;
- v0.3 retrieval provenance;
- v0.4 authenticated approval and independent verifier evidence;
- v0.4.1 dataset foundation explicitly classified NOT_APPLICABLE direct UI;
- v0.5 DB/migrations/CAS/provider/observability diagnostics;
- v0.6 Access/multitenancy;
- v0.7 distributed runtime;
- v0.8→v0.8.5 product surfaces;
- DG-P0→DG-P10 Documents.

Nothing implemented is considered covered merely because a generic “summary” card exists.


## 35. Non-goals

This UI/UX program does not:

- invent new scientific semantics;
- make UI state authoritative;
- create a second Library database;
- create generic SaaS connectors;
- introduce unsupported external systems;
- auto-upgrade package revisions;
- infer document relations from prose;
- expose hidden chain-of-thought;
- weaken project/tenant authority;
- bypass GitHub SHA-safe rules;
- mark future GAC/Codex capability LIVE before backend qualification.

---

## 36. Lock decision

The target information architecture is locked as:

```text
GLOBAL
  Home
  Projects
  Operations
  Research / Packages
  Shared Library [future]
  Agents / Codex [future]
  System

PROJECT
  Overview
  Execution
  Library
    Documents
      Relations / Lineage / Impact(future)
    Artifacts
    Evidence
    References(future)
  Governance
  Configuration
    Packages
    GitHub
    Agent Protocol
    Members & Access
    Settings
```

Home is an operational dashboard.

Relations/Lineage graph is project/document contextual.

Document content is first-class: selected documents support contextual Quick Preview and an expandable full-screen Reader Mode bound to the exact resolved revision.

Package Registry exposes exact Domain/Skill package identity and two-way usage.

GitHub is the only current external plugin family shown as LIVE.

Shared Library, Reference Acquisition and Codex remain visibly planned until their backend gates pass.

Implementation is complete only when the real installed browser product follows this flow, uses authoritative APIs, and passes the browser UAT contract above.
