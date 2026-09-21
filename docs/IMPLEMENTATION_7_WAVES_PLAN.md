# GWF — 7-Wave Implementation Plan and Handoff Checklist

## 1. Status

**Document status:** implementation plan / phased authorization map.

**Planning baseline:** documentation branch `docs/reference-agent-interop-specs` at `a05425cb948332c01ca4f2dde280a4f4ee2cd02c`.

This plan converts the approved specification set into an ordered implementation roadmap optimized for **lower complexity first without violating hard dependencies**.

This document does not by itself authorize every wave. The current user authorization covers:

1. writing and QA of this plan; and
2. if this plan passes QA, immediate implementation of **DG-P0 — External Validator Foundation** only.

All later items remain planned, not authorized.

## 2. Governing documents

The following documents define the semantics used by this plan:

- `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` — document identity, QA, findings, relations, validity, BUILD/INTEGRATE/OPTIONAL ADAPTER matrix.
- `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md` — reference query plan, retrieval log, registry, evidence map, temporal integrity.
- `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` — harness vs Agent Pool, bindings, execution envelope, transport/governance boundary.
- `docs/FUTURE_NODE_AGENT_ORCHESTRATION_PARKING_LOT.md` — explicitly deferred node-level orchestration.
- `docs/Finding_checklist.md` — cumulative resolved specification findings.
- `docs/DOCUMENT_QA_DOCUMENTATION_GOVERNANCE.md` — QA evidence for Documentation Governance.
- `docs/DOCUMENT_QA_REFERENCE_AGENT_INTEROP.md` — QA evidence for Reference Acquisition + Agent Interoperability.

## 3. Complexity scale

Each implementation item has one integer **priority complexity**. When an earlier analysis used a range, this plan uses the conservative upper bound so priority ordering is deterministic.

| Level | Meaning |
| --- | --- |
| **1 — Very Low** | Thin adapter/check, no authoritative state mutation |
| **2 — Low** | Small service/interface, reuses current primitives |
| **3 — Medium** | Persistence/state machine/cross-module behavior |
| **4 — High** | Authority, dependency propagation, research semantics, or external runtime |
| **5 — Very High** | Multi-agent orchestration, delegation, routing, scheduling |

Priority rule:

> Among work items whose **HARD** dependencies are satisfied, select the lowest-complexity item first. **ORDERING** dependencies preserve roadmap sequence but are not architectural prerequisites. **OPTIONAL** dependencies may improve the item but do not block it.

## 4. Dependency types

Planning control identities:

- **PLAN-QA** — `docs/DOCUMENT_QA_7_WAVES_PLAN.md` with PASS verdict bound to the exact plan blob/revision.
- **DIG-SPEC** — `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` exact reviewed revision.
- **DG-Wn / RA-W6 / AI-W7** — the named wave exit gate with its committed handoff/evidence package.

- **HARD** — item must not start until the dependency has passed its acceptance gate.
- **ORDERING** — roadmap sequencing decision; technically separable, but intentionally scheduled later.
- **OPTIONAL** — useful enhancement, not required for correctness.
- **EXTERNAL** — external tool/service capability that must be revalidated before implementation.

Every completed item must record exact dependency revisions/evidence used. A dependency named only by logical ID is insufficient for handoff; its evidence package must resolve to exact commit/blob/run identities.

---

# Wave 1 — Documentation Validator Foundation

**Goal:** obtain immediate deterministic documentation QA value with minimal state mutation.

### DG-P0 — External Validator Foundation + markdownlint

- **Complexity:** 2
- **Authorization:** **AUTHORIZED after this plan QA PASS**
- **HARD dependencies:**
  - PLAN-QA — this 7-wave plan must PASS.
  - DIG-SPEC — `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` exact reviewed revision.
- **EXTERNAL dependency:** markdownlint/markdownlint-cli2 capability must be revalidated and pinned before adapter execution.
- **Governing documents:**
  - `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§18–21, 32, 35.
  - this plan §Wave 1.
- **Scope:**
  - define `ValidatorAdapter` contract;
  - define normalized `ValidatorExecution`;
  - define normalized non-persistent finding result compatible with future `DocumentFinding`;
  - implement first markdownlint adapter;
  - capture validator identity/version, exact subject hash, execution status, findings and locations;
  - pin a minimal markdownlint configuration and record its content hash;
  - distinguish validator unavailable/error from document failure;
  - prohibit auto-fix and document mutation.
- **Explicit non-scope:**
  - no document registry;
  - no graph/dependency propagation;
  - no `DocumentQARecord` database persistence;
  - no research workflow changes;
  - no GitHub Ruleset/CODEOWNERS mutation;
  - no Vale/Lychee yet.
- **Acceptance checklist:**
  - [ ] adapter interface is provider-neutral;
  - [ ] exact input/content hash recorded;
  - [ ] validator version/config identity recorded;
  - [ ] valid fixture returns successful execution with zero structural findings;
  - [ ] invalid fixture returns deterministic structural findings with location;
  - [ ] a real pinned markdownlint-cli2 executable/version passes a smoke fixture; mocks/shims alone cannot qualify P0;
  - [ ] pinned markdownlint config identity/hash recorded;
  - [ ] missing/unavailable validator fixture is not represented as document FAIL;
  - [ ] adapter cannot mutate source content;
  - [ ] repeated identical fixture invocation normalizes equivalently;
  - [ ] no secret material persisted in execution result;
  - [ ] unit tests PASS;
  - [ ] P0 QA gate PASS;
  - [ ] exact commit/evidence recorded.

### DG-P1 — Vale terminology/prose adapter

- **Complexity:** 2
- **HARD dependencies:** DG-P0.
- **EXTERNAL dependency:** Vale capability/version/config revalidation.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§18–21.
- **Acceptance checklist:**
  - [ ] adapter uses DG-P0 normalized contract;
  - [ ] project vocabulary/config hash attributable;
  - [ ] terminology drift fixture detected;
  - [ ] tool unavailable distinguished from content failure;
  - [ ] no auto-fix mutation;
  - [ ] QA PASS.

### DG-P2 — Lychee link adapter

- **Complexity:** 2
- **HARD dependencies:** DG-P0.
- **EXTERNAL dependency:** Lychee capability/version/config revalidation.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§18–21.
- **Acceptance checklist:**
  - [ ] adapter uses normalized contract;
  - [ ] internal/external link results distinguishable;
  - [ ] network/tool failure distinguished from broken-link finding;
  - [ ] deterministic local fixture PASS/FAIL evidence;
  - [ ] QA PASS.

### DG-P3 — Git/blob revision evidence resolver

- **Complexity:** 2
- **HARD dependencies:** DG-P0 contract only; may execute before P1/P2.
- **Governing documents:**
  - `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§8, 20, 30.
  - existing GitHub SHA QA behavior in GWF v0.8.4.
- **Acceptance checklist:**
  - [ ] exact repository/commit/blob identity can be captured;
  - [ ] path is not treated as identity;
  - [ ] stale expected SHA fails closed;
  - [ ] no credential material persisted;
  - [ ] QA PASS.

### Wave 1 exit gate — DG-W1

This is a **future wave gate**, not authorization to continue automatically after DG-P0. The current authorization frontier still stops after DG-P0.

- [ ] DG-P0 PASS
- [ ] DG-P1 PASS
- [ ] DG-P2 PASS
- [ ] DG-P3 PASS
- [ ] external validator outputs normalized through one contract
- [ ] no authoritative document-state runtime added yet
- [ ] handoff package records exact tool versions/config fingerprints

---

# Wave 2 — Minimal Documentation Kernel

**Goal:** represent governed documents and exact QA identity by reusing current GWF knowledge primitives instead of creating a parallel knowledge system.

### DG-P4 — Document facade / identity mapping

- **Complexity:** 3
- **HARD dependencies:** DG-P3.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§6–8, 33.
- **Design constraint:** first evaluate specialization/facade over existing `artifacts/revisions`; creating parallel document/revision tables requires explicit evidence that reuse is insufficient.
- **Acceptance checklist:**
  - [ ] stable `document_id` independent of path;
  - [ ] exact revision identity;
  - [ ] no silent migration of existing Markdown;
  - [ ] current GWF artifact semantics preserved;
  - [ ] QA PASS.

### DG-P5 — QA run + finding persistence

- **Complexity:** 3
- **HARD dependencies:** DG-P0, DG-P4.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§8.5–8.6, 17–18.
- **Acceptance checklist:**
  - [ ] one `DocumentQARecord` represents one exact QA run;
  - [ ] zero-to-many `DocumentFinding` records;
  - [ ] finding status lifecycle enforced;
  - [ ] QA bound to exact revision/change set;
  - [ ] prior QA cannot validate a new revision;
  - [ ] QA PASS.

### DG-P6 — Lifecycle + validity mapping

- **Complexity:** 3
- **HARD dependencies:** DG-P4, DG-P5.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§11–12.
- **Special design question:** map documentation `BLOCKED` semantics onto existing GWF revision/gate states without prematurely adding a conflicting global validity state.
- **Acceptance checklist:**
  - [ ] lifecycle and validity separate;
  - [ ] new revision begins unverified;
  - [ ] prior VALID does not transfer automatically;
  - [ ] BLOCKED operational meaning explicitly mapped;
  - [ ] existing KnowledgeKernel semantics remain compatible;
  - [ ] QA PASS.

### Wave 2 exit gate — DG-W2

- [ ] DG-P4 PASS
- [ ] DG-P5 PASS
- [ ] DG-P6 PASS
- [ ] exact-revision QA invalidation demonstrated
- [ ] no duplicate knowledge subsystem created without justification
- [ ] handoff contains schema/migration decisions and compatibility evidence

---

# Wave 3 — Semantic Documentation Governance

**Goal:** add authority, relation, change-scope, and source-of-truth semantics.

### DG-P7 — Authority claims + duplicate-authority detection

- **Complexity:** 3
- **HARD dependencies:** DG-P4, DG-P6.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §9.
- **Acceptance checklist:**
  - [ ] multiple non-conflicting claims supported;
  - [ ] duplicate active authority detected;
  - [ ] informative summary does not acquire authority;
  - [ ] composition policy explicit where required;
  - [ ] QA PASS.

### DG-P8 — Typed document relations

- **Complexity:** 3
- **HARD dependencies:** DG-P4.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §10.
- **Acceptance checklist:**
  - [ ] relation direction explicit;
  - [ ] required relation types represented;
  - [ ] relation semantics not inferred from Markdown links;
  - [ ] integration with existing `trace_links` evaluated before new graph storage;
  - [ ] QA PASS.

### DG-P9 — Logical-current vs pinned-revision binding

- **Complexity:** 3
- **HARD dependencies:** DG-P8.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §10.
- **Acceptance checklist:**
  - [ ] `LOGICAL_CURRENT` and `PINNED_REVISION` distinct;
  - [ ] `VALIDATES` cannot float;
  - [ ] `GENERATED_FROM` exact identity preserved;
  - [ ] QA PASS.

### DG-P10 — Change classification

- **Complexity:** 3
- **HARD dependencies:** DG-P4, DG-P7.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§13–14.
- **Acceptance checklist:**
  - [ ] EDITORIAL / CLARIFICATION / NORMATIVE / STRUCTURAL / SUPERSESSION represented;
  - [ ] QA can escalate classification;
  - [ ] ambiguous clarification vs normative fails conservatively;
  - [ ] agent cannot downgrade escalated class;
  - [ ] QA PASS.

### DG-P11 — DocumentChangeSet

- **Complexity:** 3
- **HARD dependencies:** DG-P7, DG-P8, DG-P10.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§8.4, 15.
- **Acceptance checklist:**
  - [ ] base revisions frozen;
  - [ ] target docs and allowed paths frozen;
  - [ ] per-document + effective change class stored;
  - [ ] dependency/impact snapshot attributable;
  - [ ] scope violation fails closed;
  - [ ] proposal/approval primitives reused where possible;
  - [ ] QA PASS.

### Wave 3 exit gate — DG-W3

- [ ] DG-P7…DG-P11 PASS
- [ ] duplicate authority fixture FAILS correctly
- [ ] exact-revision validation fixture works
- [ ] normative change cannot masquerade as editorial
- [ ] change scope is frozen before mutation

---

# Wave 4 — Dependency and Drift Core

**Goal:** implement the central “propagate invalidity, not silent edits” semantics.

### DG-P12 — Relation-aware impact traversal

- **Complexity:** 4
- **HARD dependencies:** DG-P8, DG-P9, DG-P11.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§10, 27–28.
- **Acceptance checklist:**
  - [ ] deterministic impact report;
  - [ ] relation-specific invalidation;
  - [ ] bounded/reconstructable traversal;
  - [ ] cycles handled according to relation policy;
  - [ ] existing `KnowledgeKernel.compute_impact` reused/extended where valid;
  - [ ] QA PASS.

### DG-P13 — STALE/review/BLOCK propagation

- **Complexity:** 4
- **HARD dependencies:** DG-P6, DG-P12.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§12, 16, 28.
- **Acceptance checklist:**
  - [ ] upstream material change marks obligations without editing content;
  - [ ] reason/path retained;
  - [ ] idempotent repeated evaluation;
  - [ ] return to VALID requires current-revision QA;
  - [ ] QA PASS.

### DG-P14 — No-silent-cascade enforcement

- **Complexity:** 4
- **HARD dependencies:** DG-P11, DG-P13.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§15–16.
- **Acceptance checklist:**
  - [ ] downstream edits require explicit change set;
  - [ ] auto-suggestion remains proposal only;
  - [ ] hidden recursive repair blocked;
  - [ ] original invalidation event preserved;
  - [ ] QA PASS.

### DG-P15 — Append-only + supersession

- **Complexity:** 4
- **HARD dependencies:** DG-P7, DG-P10, DG-P11.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§11, 14.
- **Acceptance checklist:**
  - [ ] APPEND_ONLY violation detected;
  - [ ] correction represented as appended amendment;
  - [ ] SUPERSEDES retires authority without erasing history;
  - [ ] unresolved inbound dependency blocks unsafe deletion;
  - [ ] QA PASS.

### DG-P16 — Generated-document provenance

- **Complexity:** 3
- **HARD dependencies:** DG-P9, DG-P13.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §25.
- **Acceptance checklist:**
  - [ ] generator/config/input/output identities captured;
  - [ ] changed input makes prior generation stale where policy requires;
  - [ ] generated doc does not become normative silently;
  - [ ] QA PASS.

### Wave 4 exit gate — DG-W4

- [ ] DG-P12…DG-P16 PASS
- [ ] A→B/C fixture demonstrates STALE/review propagation without B/C mutation
- [ ] append-only and supersession fixtures PASS
- [ ] no silent cascade path exists

---

# Wave 5 — Repository Enforcement and Implementation Alignment

**Goal:** connect GWF document validity to repository enforcement and implementation drift.

### DG-P17 — GitHub QA enforcement integration

- **Complexity:** 3
- **HARD dependencies:** DG-W4.
- **EXTERNAL dependency:** GitHub CODEOWNERS/Rulesets/current API revalidation.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§19–20, 30.
- **Acceptance checklist:**
  - [ ] GWF QA result consumable by repository checks;
  - [ ] merge enforcement does not become source of semantic truth;
  - [ ] exact SHA verification retained;
  - [ ] no secret in static/public surfaces;
  - [ ] QA PASS.

### DG-P18 — Code/schema/API/workflow/dataset bindings

- **Complexity:** 4
- **HARD dependencies:** DG-P8, DG-P9, DG-P13.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§22, 24.
- **Acceptance checklist:**
  - [ ] target kind + identity/hash stored;
  - [ ] target change creates review obligation;
  - [ ] change does not prove doc wrong automatically;
  - [ ] no auto-rewrite;
  - [ ] QA PASS.

### DG-P19 — Research study-lock integration

- **Complexity:** 5
- **HARD dependencies:** DG-P10, DG-P11, DG-P14.
- **ORDERING dependency:** DG-P18 preferred first for simpler cross-artifact binding evidence.
- **Governing documents:**
  - `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §23.
  - `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md` §8.
  - current research domain/study-lock contracts.
- **Acceptance checklist:**
  - [ ] scientific semantic edit cannot bypass study lock;
  - [ ] post-lock clarification that changes operational meaning escalates;
  - [ ] post-outcome edits preserve original preregistration;
  - [ ] stricter research authority wins;
  - [ ] QA PASS.

### DG-P20 — Existing-document migration pilot

- **Complexity:** 4
- **HARD dependencies:** DG-W4, DG-P7, DG-P17.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §33.
- **Acceptance checklist:**
  - [ ] candidate docs discovered without auto-authority assignment;
  - [ ] metadata inference labeled inferred;
  - [ ] collision audit before activation;
  - [ ] Git provenance preserved;
  - [ ] bounded pilot only;
  - [ ] QA PASS.

### Wave 5 exit gate — DG-W5

- [ ] DG-P17…DG-P20 PASS
- [ ] repository enforcement consumes GWF evidence
- [ ] code↔docs change creates review obligation
- [ ] research-lock bypass fixture fails
- [ ] bounded migration pilot produces no silent authority assignment

---

# Wave 6 — Reference Acquisition v0.8.6

**Goal:** add governed external research-reference acquisition using Documentation Governance primitives instead of creating a separate evidence universe.

### RA-P0 — Query plan + retrieval log

- **Complexity:** 3
- **HARD dependencies:** DG-W3; DG-P5 exact QA/finding semantics.
- **ORDERING dependency:** DG-W5, because Documentation Governance is intentionally completed first.
- **Governing document:** `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md` §§6.1–6.2, 8–10.
- **Checklist:**
  - [ ] plan revision;
  - [ ] acquisition mode;
  - [ ] exact executed queries;
  - [ ] append-only retrieval events;
  - [ ] amendment provenance;
  - [ ] QA PASS.

### RA-P1 — Reference Registry

- **Complexity:** 3
- **HARD dependencies:** RA-P0, DG-P4, DG-P9.
- **Governing document:** `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md` §6.3.
- **Checklist:**
  - [ ] canonical vs inspected identity separated;
  - [ ] dispositions preserved;
  - [ ] multi-query observations linked;
  - [ ] exact Git commit for retained repositories;
  - [ ] QA PASS.

### RA-P2 — GitHub/source-code acquisition adapter

- **Complexity:** 3
- **HARD dependencies:** RA-P1.
- **Governing documents:**
  - `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md` §§4.2, 7, 13.
  - existing GWF GitHub plugin/SHA QA contracts.
- **Checklist:**
  - [ ] read-only acquisition path;
  - [ ] exact commit/relevant paths;
  - [ ] paper-code relationship remains separate;
  - [ ] no arbitrary code execution;
  - [ ] QA PASS.

### RA-P3 — Paper/reference search adapters

- **Complexity:** 3
- **HARD dependencies:** RA-P0, RA-P1.
- **EXTERNAL dependencies:** provider/index interfaces revalidated before implementation.
- **Governing document:** `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md` §§4.1, 6, 9.
- **Checklist:**
  - [ ] provider identity attributable;
  - [ ] canonical/version identity where available;
  - [ ] unavailable provider represented explicitly;
  - [ ] no secret persistence;
  - [ ] QA PASS.

### RA-P4 — Identity dedup + evidence map

- **Complexity:** 4
- **HARD dependencies:** RA-P1, DG-P8, DG-P9.
- **Governing document:** `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md` §§6.4, 7.
- **Checklist:**
  - [ ] relation direction fixed;
  - [ ] explicit vs inferred assertion basis;
  - [ ] duplicate identity handling deterministic;
  - [ ] QA PASS.

### RA-P5 — Coverage/temporal/novelty handoff gates

- **Complexity:** 4
- **HARD dependencies:** RA-P0…RA-P4, DG-P19.
- **Governing document:** `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md` §§8, 10–14.
- **Checklist:**
  - [ ] REQUIRED vs OPTIONAL coverage;
  - [ ] PRE_LOCK / LOCKED_PRE_OUTCOME / POST_OUTCOME enforced;
  - [ ] required-source outage cannot silently PASS;
  - [ ] novelty collision behavior mode-specific;
  - [ ] governed handoff to prior art/novelty;
  - [ ] QA PASS.

### RA-P6 — Research workflow integration

- **Complexity:** 4
- **HARD dependencies:** RA-P5.
- **Governing documents:**
  - `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md`.
  - current `domains/research.workflow.yaml`.
  - current `research_orchestrator.py` contracts.
- **Checklist:**
  - [ ] explicit decision on phase insertion vs split;
  - [ ] fixed-phase assumptions migrated intentionally;
  - [ ] historical studies not silently backfilled;
  - [ ] regression suite PASS;
  - [ ] v0.8.6 gate PASS.

### Wave 6 exit gate — RA-W6

- [ ] RA-P0…RA-P6 PASS
- [ ] reference chain reconstructable end-to-end
- [ ] exact paper/repo identities retained
- [ ] temporal integrity demonstrated
- [ ] research-domain regression PASS

---

# Wave 7 — Agent Interoperability v0.8.7

**Goal:** connect GWF to external agent harnesses and Agent Pool transports without moving governance authority outside GWF.

### AI-P0 — AgentExecutionEnvelope + trace identity

- **Complexity:** 3
- **HARD dependencies:** existing GWF execution/audit primitives.
- **ORDERING dependency:** RA-W6; sequencing choice, not an architectural requirement.
- **Governing document:** `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` §§5, 14–18.
- **Checklist:**
  - [ ] executor status distinct from GWF gate PASS;
  - [ ] external trace/session IDs are foreign identities;
  - [ ] exact input/role/binding/evidence identity captured;
  - [ ] no secret persistence;
  - [ ] QA PASS.

### AI-P1 — MCP read-only surface

- **Complexity:** 3
- **HARD dependencies:** AI-P0.
- **Governing document:** `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` §§12–13.
- **Checklist:**
  - [ ] project/workunit/artifact/evidence read-only operations;
  - [ ] no unrestricted mutation;
  - [ ] authority checks preserved;
  - [ ] QA PASS.

### AI-P2 — Codex harness adapter

- **Complexity:** 4
- **HARD dependencies:** AI-P0.
- **ORDERING dependency:** AI-P1 preferred because ChatGPT/operator-facing path is planned first.
- **Governing document:** `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` §§2.1, 6, 19.
- **Checklist:**
  - [ ] native harness/session value preserved;
  - [ ] session/workspace/tools attributable;
  - [ ] result normalized to execution envelope;
  - [ ] harness cannot self-complete GWF node;
  - [ ] QA PASS.

### AI-P3 — Governed MCP mutation surface

- **Complexity:** 4
- **HARD dependencies:** AI-P1, AI-P0.
- **Governing document:** `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` §13.
- **Checklist:**
  - [ ] mutation maps to native GWF governed command;
  - [ ] same authority/idempotency/audit/verification;
  - [ ] no force-pass/force-merge/lineage deletion;
  - [ ] QA PASS.

### AI-P4 — Claude harness adapter

- **Complexity:** 4
- **HARD dependencies:** AI-P0.
- **ORDERING dependency:** AI-P2.
- **Governing document:** `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` §§6, 19.
- **Checklist:** same harness invariants as AI-P2; QA PASS.

### AI-P5 — Gemini harness adapter

- **Complexity:** 4
- **HARD dependencies:** AI-P0.
- **ORDERING dependency:** AI-P4.
- **Governing document:** `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` §§6, 19.
- **Checklist:** same harness invariants as AI-P2; QA PASS.

### AI-P6 — Agent Pool resource model

- **Complexity:** 4
- **HARD dependencies:** AI-P0.
- **Governing document:** `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` §§2.2, 5, 7.
- **Checklist:**
  - [ ] Agent Pool is resource class, not transport;
  - [ ] workers may be primary executors;
  - [ ] provider/transport/resource class separate;
  - [ ] capabilities vs execution constraints separate;
  - [ ] QA PASS.

### AI-P7 — ARC transport adapter

- **Complexity:** 4
- **HARD dependencies:** AI-P6, AI-P0.
- **EXTERNAL dependency:** ARC protocol/runtime capability revalidated at implementation time.
- **Governing document:** `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` §§7, 12, 15.
- **Checklist:**
  - [ ] ARC is transport, not model provider;
  - [ ] trace/task identity preserved;
  - [ ] substitution never silent;
  - [ ] result normalized to execution envelope;
  - [ ] QA PASS.

### Wave 7 exit gate — AI-W7

- [ ] AI-P0…AI-P7 PASS
- [ ] GWF remains authoritative across all execution paths
- [ ] harness and Agent Pool semantics remain distinct
- [ ] MCP mutation parity proven
- [ ] ARC transport proven without fallback-only semantics

---

# 5. Explicit parking lot after Wave 7

The following are **not active implementation items** in this 7-wave plan:

- node-level role→capability→agent binding;
- delegated senior/junior runtime;
- automatic routing;
- scheduler;
- cost optimizer;
- provider health ranking;
- visual node editor;
- model equivalence automation.

**Governing document:** `docs/FUTURE_NODE_AGENT_ORCHESTRATION_PARKING_LOT.md`.

Revisit only when one of its explicit triggers occurs.

# 6. Cross-wave dependency summary

```text
PLAN-QA
  ↓
DG-P0
  ├──→ DG-P1
  ├──→ DG-P2
  └──→ DG-P3
          ↓
        DG-P4
          ↓
        DG-P5
          ↓
        DG-P6
          ↓
     authority/relations/change-set
          ↓
      impact + STALE
          ↓
   no-silent-cascade
          ↓
 repo enforcement + code/research alignment
          ↓
 Reference Acquisition v0.8.6
          ↓ [ORDERING]
 Agent Interoperability v0.8.7
```

Hard dependency detail remains authoritative in each item above; this diagram is only a summary.

# 7. Handoff checklist for every item

Every item completion package must include:

- [ ] item ID and wave;
- [ ] exact implementation commit SHA;
- [ ] exact parent SHA;
- [ ] exact governing document blob/revision identities;
- [ ] HARD dependencies and their PASS evidence;
- [ ] external dependency version/config evidence where applicable;
- [ ] files changed;
- [ ] schema/migration changes, or explicit `NONE`;
- [ ] normative behavior changes, or explicit `NONE`;
- [ ] tests added/changed;
- [ ] exact test command or CI workflow;
- [ ] QA result;
- [ ] known limitations;
- [ ] open findings;
- [ ] security/privacy impact;
- [ ] rollback/recovery note;
- [ ] explicit non-scope;
- [ ] next allowed item(s).

No item may be marked complete with unresolved required handoff fields.

# 8. Global implementation invariants

- [ ] lower complexity is preferred only after HARD dependencies are satisfied;
- [ ] failed QA does not auto-trigger redesign;
- [ ] external tool outage is not converted into document failure;
- [ ] no external validator receives governance authority;
- [ ] no silent document cascade repair;
- [ ] no silent executor substitution;
- [ ] no raw reusable secrets persisted;
- [ ] exact revision/SHA evidence is preserved;
- [ ] research-lock semantics cannot be relaxed by documentation tooling;
- [ ] current failed/negative evidence is not erased by rerun;
- [ ] every wave exit gate must PASS before an ORDERING-dependent later wave is promoted to active work.

# 9. Current authorization frontier

At publication of this plan:

```text
7-WAVE PLAN QA
      ↓ PASS required
DG-P0 — External Validator Foundation + markdownlint
      ↓
STOP
```

Only DG-P0 is authorized after plan QA PASS. DG-P1 and later items require a new explicit implementation authorization or a later user instruction that clearly advances the roadmap.
