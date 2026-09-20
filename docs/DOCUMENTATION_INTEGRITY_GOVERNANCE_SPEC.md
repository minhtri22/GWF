# GWF — Documentation Integrity & Governance Specification

## 1. Status

**Document status:** foundation specification / implementation not authorized.

**Baseline:** documentation branch `docs/reference-agent-interop-specs` at `8cf5173356f1655b19163cafc0692fce8a1f5a0b`, based on verified GWF v0.8.5 `main` `f7bbe2e91a148e11397406327ebf3d3389f7c6a7`.

This document defines a cross-domain Documentation Integrity & Governance foundation for research and software projects. It does **not** implement a document registry, dependency graph, validators, GitHub rules, publishing system, code↔docs drift integration, policy engine, or UI.

Passing document QA is necessary but not sufficient to authorize implementation.

## 2. Problem statement

In a long-running AI-assisted project, documentation is part of the operational and scientific state of the project. A syntactically valid edit can still damage the project by:

- changing a normative meaning without the required authority;
- making a dependent document stale;
- creating two active sources of truth for the same scope;
- breaking a reference or dependency;
- rewriting append-only lineage;
- changing a research protocol after study lock while presenting the change as documentation cleanup;
- describing code, schema, API, or behavior that no longer exists;
- silently cascading edits across multiple documents until contradictions are hidden;
- allowing an agent to edit a document without loading the authoritative revision and its dependency context;
- preserving an old QA report as if it still validated a changed document;
- introducing secrets or sensitive execution material into documentation or generated documentation artifacts.

The system therefore needs governance over **document identity, authority, relationships, changes, validity, QA, lineage, and interaction with code/research state**.

## 3. Objective

Treat important documentation as governed project artifacts rather than unstructured Markdown files.

The target control loop is:

```text
resolve document identity
        ↓
load authoritative revision
        ↓
load upstream dependencies + inbound dependents
        ↓
classify proposed change
        ↓
freeze edit scope
        ↓
edit
        ↓
structural / referential / semantic QA
        ↓
dependency impact analysis
        ↓
record findings
        ↓
resolve findings
        ↓
independent verification
        ↓
commit
        ↓
exact post-commit verification
        ↓
update document validity state
```

The core design rule is:

> **Propagate invalidity and review obligations; do not silently propagate edits.**

## 4. Scope

This foundation governs documentation used as project state, including:

- architecture and design specifications;
- research goals, hypotheses, protocols, study locks, analysis plans, reports, and lineage;
- software requirements, ADRs, implementation plans, release/QA reports, runbooks, and operational procedures;
- README and handoff documents when they summarize governed state;
- generated reports when downstream decisions depend on them;
- documentation that is explicitly bound to source code, schemas, APIs, workflows, datasets, or other artifacts.

Purely ephemeral chat text is outside scope unless promoted into a governed artifact.

## 5. Non-goals

Documentation Governance is **not** intended to become:

- a Markdown parser or Markdown style checker;
- a prose grammar/style engine;
- a hyperlink crawler;
- a documentation website generator;
- a full enterprise developer portal;
- a Git hosting/review replacement;
- a generic policy engine;
- an LLM writing assistant;
- a source-code documentation product;
- a silent auto-rewriter of stale documents.

Those capabilities should be integrated or adapted where appropriate instead of reimplemented inside GWF.

## 6. Core design principles

### 6.1 Document path is not document identity

A filename or repository path is a storage locator. Governed identity must survive path changes.

### 6.2 Lifecycle and validity are separate

A document may be `ACTIVE` but `STALE`; lifecycle state must not hide validity state.

### 6.3 Authority is explicit

A document that summarizes a rule is not automatically the authority for that rule.

### 6.4 Relationships have semantics

A Markdown hyperlink is not equivalent to `DEPENDS_ON`, `SUPERSEDES`, `VALIDATES`, or `MUST_ALIGN_WITH`.

### 6.5 Semantic changes require semantic governance

An agent may not downgrade a normative change into an editorial label merely because the diff is small.

### 6.6 No silent cascade repair

When an upstream document changes, downstream documents become review candidates or stale according to relation semantics. GWF does not silently rewrite them to make the graph appear consistent.

### 6.7 External tools report evidence; GWF owns validity

Linters, link checkers, GitHub rules, drift products, or policy engines may contribute findings or enforcement, but they do not become GWF's authoritative document-state engine.

### 6.8 Offline core

The core document registry, relation semantics, change classification, impact propagation, and QA state must remain usable without a hosted documentation service. Hosted systems may be optional adapters.

## 7. Governed document classes

A future `DocumentRecord` should classify documents at least as:

### `NORMATIVE`

Defines a rule, protocol, architecture contract, requirement, invariant, policy, or authoritative design decision.

### `OPERATIONAL`

Defines a procedure, runbook, setup, deployment, recovery, or execution process.

### `EVIDENCE`

Records observations, QA results, audit results, experiment reports, or verification evidence.

### `LINEAGE`

Preserves append-only or history-sensitive decisions, studies, branches, amendments, or evolution records.

### `INFORMATIVE`

Explains or summarizes governed state but is not itself the source of truth unless separately granted authority.

### `GENERATED`

Produced from another governed artifact or process and expected to be reproducible from declared inputs.

Document class does not by itself grant authority.

## 8. Core conceptual artifacts

### 8.1 `DocumentRecord`

Stable identity and governance metadata for a logical document.

Conceptual fields:

- `document_id`
- `document_class`
- `title`
- `storage_locator`
- `authority_claims`: zero or more `{scope, key, mode}` claims
- `change_policy`
- `owner_or_authority_ref`
- `lifecycle_state`
- `validity_state`
- `current_revision_id`
- `created_at`
- `archived_at`

### 8.2 `DocumentRevision`

Immutable identity of one document revision.

Conceptual fields:

- `revision_id`
- `document_id`
- `content_hash`
- `repository_ref`
- `commit_sha`
- `blob_sha_or_content_digest`
- `parent_revision_id`
- `change_class`
- `change_reason`
- `actor_ref`
- `created_at`
- `qa_record_ref`
- `supersession_ref`

A path change without a semantic change still produces a new revision if the governed stored artifact changes.

### 8.3 `DocumentRelation`

Typed edge between governed entities.

Conceptual fields:

- `relation_id`
- `source_document_id`
- `relation_type`
- `target_kind`: `DOCUMENT | SOURCE_CODE | SCHEMA | API | WORKFLOW | DATASET | STUDY_LOCK | OTHER_ARTIFACT`
- `target_ref`
- `target_binding_mode`: `LOGICAL_CURRENT | PINNED_REVISION`
- `target_revision_or_hash`
- `invalidation_policy`
- `created_revision_id`
- `retired_revision_id`

### 8.4 `DocumentChangeSet`

Frozen scope of a proposed documentation mutation.

Conceptual fields:

- `change_set_id`
- `base_revision_ids`
- `target_document_ids`
- `declared_change_class_by_document`
- `effective_change_class`
- `allowed_paths`
- `dependency_snapshot_ref`
- `impact_snapshot_ref`
- `actor_ref`
- `authority_ref`
- `status`

A documentation change set is analogous to a governed code change set: it freezes what may change and what state the edit was based on.

### 8.5 `DocumentQARecord`

One attributable QA run over an exact revision or change set.

Conceptual fields:

- `qa_record_id`
- `subject_revision_or_change_set`
- `qa_policy_ref`
- `validator_execution_refs`
- `finding_refs`
- `overall_status`
- `started_at`
- `finished_at`
- `verified_by`
- `verified_at`

### 8.6 `DocumentFinding`

One finding emitted or normalized by a QA run.

Conceptual fields:

- `finding_id`
- `qa_record_id`
- `finding_class`
- `severity`
- `location`
- `description`
- `evidence`
- `status`
- `required_fix`
- `resolution_revision_ref`
- `waiver_ref`

A QA record is not a finding. One QA record may contain zero or many findings, and a finding's resolution/waiver lifecycle remains attributable to the QA run that created it.

### 8.7 `DocumentImpactReport`

Records the effect of a changed document on its graph neighborhood.

Conceptual fields:

- `impact_report_id`
- `changed_document_id`
- `old_revision_id`
- `new_revision_id`
- `change_class`
- `inbound_relations_examined`
- `affected_documents`
- `stale_documents`
- `blocked_documents`
- `review_required_documents`
- `unaffected_documents_with_reason`

## 9. Authority and source-of-truth model

### 9.1 Authority claims

A document may own zero, one, or multiple authority claims. Each claim contains an `authority_scope`, `authority_key`, and authority `mode` such as `PRIMARY` or an explicitly governed composition role.

Normative authority must be explicit and narrow enough to detect collisions.

Example conceptual scopes:

```text
research.protocol.execution-amendment
agent.interop.binding
documentation.lifecycle
software.release.exact-main-verification
```

### 9.2 Authority key

An `authority_key` identifies the governed proposition or contract within a scope when multiple authoritative documents legitimately compose one scope.

The default invariant is:

> One active authoritative owner for one authority key at one point in lineage.

Multiple active normative documents may share a broad `authority_scope` only when their `authority_key` values are non-conflicting or an explicit composition policy defines how they combine.

### 9.3 Duplicate authority

If two active normative documents claim the same authority key without an approved composition rule, QA raises `DUPLICATE_AUTHORITY` and the affected scope is blocked from clean PASS.

An informative README may summarize a normative document but does not acquire its authority.

## 10. Document relationship semantics

Minimum future relation types:

### `DEPENDS_ON`

The source document's correctness materially depends on the target. A material target change triggers impact review and may mark the source `STALE`.

### `REFERENCES`

Informational citation or navigation. Target disappearance produces referential findings; target semantic change does not automatically invalidate the source.

### `MUST_ALIGN_WITH`

The source and target must remain semantically compatible for the declared authority scope. Although the stored edge has a source and target for identity, its default invalidation semantics are **bidirectional review**: a material change on either side creates an alignment-review obligation for the pair. A relation may override this only with an explicit governed invalidation policy.

### `SUPERSEDES`

The source replaces the target as authority for the declared scope/key. Supersession changes lifecycle/authority state; history remains preserved.

### `DERIVED_FROM`

The source is generated, summarized, or derived from target state. Relevant target revision changes normally mark the derived document `STALE` until regenerated or reviewed.

### `VALIDATES`

The source is QA/audit evidence validating a specific target revision or change set. A new target revision makes the old validation historical evidence, not validation of the new revision.

### `IMPLEMENTS`

The source document describes how a normative target is implemented. A material target change requires implementation-alignment review.

### `GENERATED_FROM`

Stronger machine-reproducible derivation relation for generated documents; the target revision/hash must be recorded.

Relation direction must be explicit. Relation semantics, not link syntax, drive invalidation.

Relation target binding is also semantic:

- `LOGICAL_CURRENT` follows the currently active revision of the target logical document and is appropriate for relations such as many `DEPENDS_ON` or `MUST_ALIGN_WITH` edges;
- `PINNED_REVISION` binds an exact target revision/hash and is required for relations whose evidentiary meaning depends on exact identity, such as `VALIDATES` and `GENERATED_FROM`.

A relation type may constrain which binding modes are legal. A `VALIDATES` edge must never float to a later unvalidated revision.

## 11. Lifecycle state model

A future lifecycle should distinguish at least:

```text
DRAFT → IN_REVIEW → ACTIVE
                    ├──→ DEPRECATED → ARCHIVED
                    └──→ SUPERSEDED → ARCHIVED
```

A document does not need to pass through `DEPRECATED` before `SUPERSEDED`. Direct archival from an active authoritative state is blocked unless policy records why authority/dependencies are safely retired.

Rules:

- `ACTIVE` means the document participates in current governed project state.
- `SUPERSEDED` preserves historical identity but no longer owns the superseded authority key.
- `DEPRECATED` remains usable for a bounded transition but should not be chosen for new work.
- `ARCHIVED` is immutable historical material unless an explicit archival-correction policy exists.
- deletion of an authoritative document with unresolved inbound dependencies is blocked.

## 12. Validity state model

Validity is separate from lifecycle.

Minimum states:

- `UNVERIFIED`
- `VALID`
- `STALE`
- `BLOCKED`

Meanings:

- `UNVERIFIED`: no current QA establishes validity for the revision.
- `VALID`: required QA/gates passed for the exact revision and its required dependencies.
- `STALE`: a dependency, bound implementation, or authority context changed and review is required.
- `BLOCKED`: known unresolved finding or governance violation prevents use where clean validity is required.

A new revision never inherits `VALID` merely because its parent revision was valid.

## 13. Change classification

Every governed edit must be classified before authoritative completion.

### `EDITORIAL`

Formatting, spelling, punctuation, or presentation change with no intended semantic effect.

### `CLARIFICATION`

Removes ambiguity or makes an existing contract explicit while claiming no intended normative change.

### `NORMATIVE`

Changes a rule, requirement, invariant, threshold, authority, protocol, architecture contract, or required behavior.

### `STRUCTURAL`

Changes document decomposition, identity, relation graph, authority ownership, or dependency topology.

### `SUPERSESSION`

Introduces a replacement authority and retires prior authority for a scope/key.

Classification policy:

- a multi-document change set classifies each document separately and records an `effective_change_class` equal to the strongest governance class triggered by any contained change;
- the proposing agent may declare a class;
- QA may **escalate** the class;
- an agent may not unilaterally downgrade an escalated class;
- uncertainty between `CLARIFICATION` and `NORMATIVE` resolves conservatively to `NORMATIVE` until reviewed;
- diff size is not evidence that a change is editorial.

## 14. Change policies

A document may declare a mutation policy such as:

- `MUTABLE_WITH_QA`
- `NORMATIVE_WITH_APPROVAL`
- `APPEND_ONLY`
- `GENERATED_ONLY`
- `IMMUTABLE_ARCHIVE`

### Append-only semantics

For `APPEND_ONLY` content, previously authoritative historical content must remain byte-equivalent or semantically immutable according to the declared append policy. Corrections to prior history must be represented as new appended correction/amendment records rather than silent rewrite.

Exact byte-prefix checking is one possible validator but is an implementation choice, not the semantic definition.

## 15. Agent documentation mutation protocol

An agent editing governed documentation must not start from an isolated file.

Minimum conceptual sequence:

```text
LOAD
  resolve document_id + current revision
  load authority metadata
  load outbound dependencies
  load inbound dependents
  load applicable research/software locks
  load open findings

PREFLIGHT
  verify exact base revision/hash
  determine edit authority
  classify proposed change
  compute initial impact scope

PLAN
  freeze DocumentChangeSet
  declare intended files/documents
  declare non-goals
  declare expected relation changes

EDIT
  modify only frozen scope

VERIFY
  structural QA
  prose/terminology QA
  reference/link QA
  semantic QA
  authority collision QA
  dependency impact QA
  domain-specific QA
  security QA

REMEDIATE
  create/resolve findings
  never silently cascade edits

HANDOFF
  independent verification where required

COMMIT
  exact post-commit revision verification

PROPAGATE
  update validity/review obligations of dependents
```

## 16. No silent cascade rule

If document A changes and B/C depend on A:

```text
A revision changes
       ↓
impact analysis
       ↓
B = review-required or STALE
C = review-required or STALE
       ↓
findings / remediation plan
       ↓
explicit B/C change sets if needed
```

GWF must not authorize an agent to recursively edit B/C merely to restore a clean graph without explicit governed scope.

Automation may **suggest** patches or create proposed change sets. It may not hide the invalidation event.

## 17. Document QA finding model

Minimum finding classes should include:

- `STRUCTURAL_ERROR`
- `BROKEN_REFERENCE`
- `UNRESOLVED_DEPENDENCY`
- `DEPENDENCY_CYCLE`
- `STALE_DEPENDENCY`
- `UNDEFINED_TERM`
- `TERMINOLOGY_DRIFT`
- `SEMANTIC_CONTRADICTION`
- `DUPLICATE_AUTHORITY`
- `INVALID_SUPERSESSION`
- `CHANGE_CLASS_MISMATCH`
- `IMPLEMENTATION_DRIFT`
- `SCHEMA_API_DRIFT`
- `APPEND_ONLY_VIOLATION`
- `RESEARCH_LOCK_VIOLATION`
- `MISSING_PROVENANCE`
- `SECURITY_LEAK`
- `GENERATED_ARTIFACT_DRIFT`

Minimum finding statuses:

- `OPEN`
- `RESOLVED_PENDING_VERIFY`
- `VERIFIED_RESOLVED`
- `WAIVED`

A waiver requires explicit authority, reason, scope, and expiration/review condition when appropriate. A waived finding remains observable.

`WAIVED` is **not** equivalent to `VERIFIED_RESOLVED`. Whether a waived finding permits a gate to PASS is defined by the applicable gate policy. Security leaks, research-lock violations, duplicate active authority, and other policy-declared non-waivable classes cannot be converted to clean PASS by waiver.

## 18. QA layers

Documentation QA should compose several layers rather than treat one linter as proof of correctness.

### L1 — Structural

Markdown/document syntax, headings, code fences, tables, front matter, basic file consistency.

### L2 — Prose and terminology

Project vocabulary, prohibited ambiguous terms, naming consistency, style constraints.

### L3 — Referential

Internal links, external links, anchors, document IDs, relation targets.

### L4 — Semantic and authority

Contradictions, undefined governed terms, duplicate authority, normative drift, source-of-truth conflicts.

### L5 — Dependency impact

Inbound/outbound relation consistency, stale propagation, cycles, supersession completeness.

### L6 — Implementation alignment

Code/schema/API/workflow/dataset bindings versus the document revision.

### L7 — Lineage and lifecycle

Append-only integrity, revision ancestry, supersession, archive constraints, QA-record freshness.

### L8 — Domain and security

Research lock integrity, software release requirements, secret/credential leakage, domain-specific invariants.

No single external validator is sufficient for L4–L8.

## 19. BUILD / INTEGRATE / OPTIONAL ADAPTER matrix

The classification below is an **architecture responsibility decision**, not implementation authorization.

Definitions:

- **BUILD** — GWF must own the semantic contract and authoritative state because delegating it would weaken governance.
- **INTEGRATE** — GWF should provide a supported adapter to a mature external capability when implementation is authorized. The external tool is replaceable and is **not** required for GWF core state to remain readable/reconstructable offline.
- **OPTIONAL ADAPTER** — useful integration for selected deployments; absence must not reduce core governance correctness.

An `INTEGRATE` decision does not authorize adding the dependency now and does not permit external product semantics to replace GWF semantics.

| Capability | Decision | Default candidate / model | GWF responsibility boundary |
| --- | --- | --- | --- |
| Document identity, class, revision, authority scope/key | **BUILD** | GWF-native | Core authoritative semantics |
| Typed document dependency graph | **BUILD** | GWF-native; Backstage relation model as design reference only | GWF owns relation semantics and invalidation |
| Lifecycle + validity state machines | **BUILD** | GWF-native | GWF owns state |
| Change classification | **BUILD** | GWF-native | GWF owns normative meaning |
| Stale/review/block propagation | **BUILD** | GWF-native | Never delegated to a docs platform |
| Source-of-truth collision detection | **BUILD** | GWF-native | Authority is a GWF concept |
| `DocumentQARecord` + `DocumentFinding` lifecycle | **BUILD** | GWF-native | External findings normalize here |
| Agent mutation protocol + no-silent-cascade rule | **BUILD** | GWF-native | Core agent governance |
| Research study-lock interaction | **BUILD** | Existing GWF research governance | Documentation governance may not bypass study lock |
| Append-only lineage semantics | **BUILD** | GWF-native + Git evidence | Git history alone is insufficient semantics |
| Code/schema/API binding metadata | **BUILD** | GWF-native bindings | Defines what must be checked, not how every check runs |
| Markdown structural lint | **INTEGRATE** | `markdownlint-cli2` / `markdownlint` | Normalize violations; do not rewrite parser/linter |
| Prose/terminology lint | **INTEGRATE** | Vale | GWF owns vocabulary policy; Vale executes applicable rules |
| Link/anchor checking | **INTEGRATE** | Lychee plus local referential checks | External URL checking is delegated; governed doc IDs remain GWF-native |
| Repository review/merge enforcement | **INTEGRATE** | GitHub CODEOWNERS + Rulesets where available | GitHub enforces merge boundary; GWF produces/checks QA evidence |
| Git revision/blob evidence | **INTEGRATE** | Git/GitHub | Used as immutable evidence, not full document governance |
| Versioned documentation publishing | **OPTIONAL ADAPTER** | Antora or equivalent | Publishing only; never authority engine |
| Developer portal / graph visualization | **OPTIONAL ADAPTER** | Backstage or equivalent | Export/view of graph; GWF remains source of truth |
| Code-coupled drift detector | **OPTIONAL ADAPTER** | Swimm or equivalent drift tool | Reports `IMPLEMENTATION_DRIFT`; does not decide GWF validity alone |
| General policy-as-code engine | **OPTIONAL ADAPTER** | OPA/Rego | May evaluate delegated policy later; GWF remains authority/orchestrator |
| Documentation website/CMS | **OPTIONAL ADAPTER** | Existing site/CMS tools | Presentation/authoring surface only |
| Search/index/vector retrieval over project docs | **OPTIONAL ADAPTER** | Existing search/index systems | Discovery aid; retrieved text is not authority without revision identity |

### Matrix invariant

An agent must not implement an external-tool capability inside GWF merely because the adapter is absent.

For an `INTEGRATE` or `OPTIONAL ADAPTER` capability, the allowed choices are:

1. integrate the selected tool;
2. provide a minimal compatibility interface/stub when authorized;
3. mark the capability unavailable/deferred;
4. propose a documented architecture amendment if the tool is demonstrably unsuitable.

"Reimplement the whole external product inside GWF" is not the default path.

## 20. External tool boundary rationale

The current architecture decision uses existing tools where their problem is mature and separable:

- `markdownlint` provides Markdown/CommonMark static analysis and supports custom rules;
- Vale provides markup-aware, configurable prose/terminology linting and can run offline;
- Lychee provides Markdown/HTML/text link checking and CI/CLI use;
- GitHub CODEOWNERS and Rulesets provide repository-level review/merge enforcement;
- Antora provides component/version-oriented documentation publishing and can aggregate content sources;
- Backstage provides a useful directional entity-relation model and graph/catalog concepts, but its catalog is not adopted as GWF's authority store;
- Swimm represents the class of code-coupled documentation drift systems that may be integrated later;
- OPA/Rego represents the class of external general-purpose policy engines that may be adapted later if GWF policy volume justifies it.

These are integration boundaries, not claims that any external tool satisfies GWF's semantic governance requirements by itself.

This capability survey is an architecture-time snapshot, not a permanent vendor guarantee. Before any external adapter is implemented or upgraded, its current license, supported interfaces, execution model, security/privacy behavior, and required runtime/version must be revalidated and pinned in implementation evidence.

### 20.1 External capability evidence snapshot

Evidence checked on **2026-09-21** for the architecture decision:

- markdownlint / custom rules: https://github.com/DavidAnson/markdownlint
- markdownlint CLI integration: https://github.com/DavidAnson/markdownlint-cli2
- Vale prose/terminology linting: https://docs.vale.sh/
- Lychee link checking: https://github.com/lycheeverse/lychee
- GitHub CODEOWNERS: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
- GitHub Rulesets: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
- Antora component/version model: https://docs.antora.org/antora/latest/component-version/
- Backstage relation model: https://backstage.io/docs/features/software-catalog/well-known-relations/
- Backstage catalog-graph boundary: https://backstage.io/docs/features/software-catalog/creating-the-catalog-graph/
- Swimm code-coupled documentation/drift class: https://swimm.io/enterprise-documentation-platform
- Open Policy Agent: https://www.openpolicyagent.org/docs

These references justify the **capability-class** decision only. They do not freeze a vendor version, license, pricing model, or implementation dependency.

## 21. External validator contract

A validator adapter should return normalized evidence conceptually equivalent to:

```text
validator_id
validator_version
execution_environment
subject_document_id
subject_revision_id
finding_class
severity
location
message
external_rule_id
evidence
execution_status
```

Rules:

- validator version/configuration must be attributable;
- external tool PASS does not imply document `VALID`;
- external tool failure must remain evidence even if a later rerun passes;
- auto-fix output is a **proposed change**, not an authoritative mutation;
- hosted validator unavailability must be distinguishable from document failure.

## 22. Code ↔ documentation alignment

A normative or operational document may bind to implementation targets:

```text
document revision
    ├── SOURCE_CODE → path + commit/blob/function fingerprint
    ├── SCHEMA      → schema identity/hash
    ├── API         → contract/version/hash
    ├── WORKFLOW    → workflow identity/hash
    └── DATASET     → dataset/manifest hash
```

A bound target change creates an impact event. It does not prove the document is wrong, but it invalidates any claim that the previous alignment check still validates the current implementation unless policy declares the change irrelevant.

Drift tools may help detect this condition; GWF owns the binding and resulting review obligation.

## 23. Research integration

Documentation Governance must not weaken research governance.

Examples:

- editing a protocol after study lock is not automatically an editorial documentation operation;
- changing a threshold, cohort, target, metric, stopping rule, or interpretation in prose is a scientific semantic change even if no code changes;
- a `CLARIFICATION` that changes operational interpretation of a frozen study must be escalated to the applicable research amendment path;
- post-outcome edits must preserve the distinction between original preregistration and later interpretation;
- `LINEAGE` and evidence documents must preserve negative results and failed branches.

Documentation Governance may add documentation controls but may **not relax or override** domain-specific research authority. Research study-lock/amendment rules remain authoritative for scientific semantics; any documentation action that would violate them is blocked or routed through the research amendment/new-lineage path.

## 24. Software integration

For software projects:

- architecture/API/schema changes may invalidate normative or operational docs;
- release handoff should be able to require no unresolved HIGH documentation findings and no `STALE` normative release-critical document;
- a code commit does not automatically mutate its documentation;
- a documentation auto-fix does not automatically authorize a code change;
- release evidence must bind the exact documentation revision used for release claims when that documentation is normative.

Exact release gating policy is deferred to implementation design.

## 25. Generated documentation

Generated documents must record:

- generator identity/version;
- source revision/hash inputs;
- generation command/config fingerprint;
- output content hash;
- generation timestamp.

If inputs change, prior generated output becomes historical evidence and may become `STALE`; regeneration must produce a new governed revision.

Generated content must not become an independent normative source unless explicitly promoted through governance.

## 26. Security boundary

Documentation tooling must not become a secret-exfiltration path.

At minimum:

- raw reusable credentials must not be embedded in governed documents, QA reports, generated docs, static sites, validator logs, or example configs;
- validator adapters receive only required access;
- hosted adapters must be blocked from documents whose privacy policy forbids external processing;
- secrets discovered during QA become `SECURITY_LEAK` findings; persisted evidence stores only a non-reversible fingerprint/classification and redacted context sufficient for remediation, never the raw secret;
- secret removal from a document does not erase repository/history exposure; incident/remediation policy is separate.

## 27. Dependency graph constraints

A future implementation must detect at least:

- unresolved target;
- relation to an invalid lifecycle target;
- forbidden self-dependency;
- cycles for relation types declared acyclic;
- supersession loops;
- duplicate active authority;
- validation attached to a different revision than claimed;
- generated/derived artifact whose input revision no longer matches;
- hidden dependency introduced only in prose when policy requires explicit relation metadata.

Not every relation type is acyclic; cycle policy belongs to relation semantics.

## 28. Impact propagation

Impact propagation computes obligations, not edits.

Conceptually:

```text
changed revision
      ↓
classify materiality
      ↓
traverse inbound relations by relation policy
      ↓
VALID → review-required / STALE / BLOCKED
      ↓
create impact report + findings
```

Propagation must be bounded and reconstructable:

- every state transition cites the triggering revision/relation;
- graph traversal version/config is attributable;
- repeated evaluation is idempotent for the same graph/revision state;
- a downstream document returns to `VALID` only after its required QA for its current exact revision and dependency state.

## 29. Independent QA

A clean checklist is necessary but does not prove validity by itself.

Where policy requires independence:

- the same execution identity that authored a normative change must not be the sole verifier;
- independence requirements must be declared prospectively;
- using a different model name alone does not establish independence;
- QA must bind to the exact revision/change set;
- a changed revision invalidates prior QA for the new revision.

## 30. Git and repository integration

Git provides immutable commit/blob evidence and change history, but GWF must not infer all documentation semantics from Git alone.

Git/GitHub integration may provide:

- exact commit/blob identities;
- branch/PR evidence;
- CODEOWNERS review;
- Ruleset-required checks;
- diff scope;
- post-commit verification.

GWF still owns document identity, authority, lifecycle, validity, semantic relations, impact propagation, and finding state.

## 31. Failure modes

A future implementation should represent at least:

- `document_identity_unresolved`
- `base_revision_stale`
- `change_scope_violation`
- `change_class_mismatch`
- `authority_collision`
- `relation_target_unresolved`
- `dependency_cycle_forbidden`
- `dependent_document_stale`
- `supersession_incomplete`
- `append_only_violation`
- `qa_revision_mismatch`
- `validator_unavailable`
- `validator_config_unresolved`
- `implementation_drift_detected`
- `research_lock_violation`
- `secret_detected`
- `generated_artifact_stale`
- `independence_requirement_unsatisfied`

## 32. Acceptance criteria for future implementation

Documentation Integrity & Governance is not complete until it can demonstrate at least:

1. stable document identity independent of storage path;
2. immutable revision identity bound to exact repository/content evidence;
3. explicit document class, authority scope/key, lifecycle, and validity;
4. duplicate active authority detection;
5. typed directional relations with relation-specific invalidation behavior;
6. separate lifecycle and validity state machines;
7. governed change classification with conservative escalation;
8. no silent cascade editing of affected dependents;
9. deterministic/reconstructable impact reports for the same graph state;
10. structured finding lifecycle with exact revision binding;
11. append-only policy enforcement for declared lineage documents;
12. stale QA detection when a validated revision changes;
13. research-lock changes route through research amendment governance;
14. code/schema/API binding changes create review obligations without silently rewriting docs;
15. external validator results normalize into GWF findings/evidence;
16. markdown structural lint is integrated rather than reimplemented;
17. prose/terminology lint is integrated rather than reimplemented;
18. link checking is integrated rather than reimplemented;
19. external tool outage is distinguishable from document failure;
20. Git/GitHub evidence is used without treating Git history as complete semantic governance;
21. hosted adapters cannot process documents that violate privacy/locality policy;
22. provider credentials/secrets do not persist in documentation evidence;
23. optional publishing/catalog/drift/policy products remain replaceable adapters;
24. exact post-commit document revision verification occurs before clean completion;
25. a new document revision cannot inherit a prior revision's `VALID` state without required QA.

## 33. Adoption and migration boundary

This specification does not retroactively claim that existing repository Markdown files already have `DocumentRecord`, dependency, authority, lifecycle, or validity state in the runtime.

Migration of existing documents is a separate governed operation. Until migration is explicitly implemented and executed, current repository content/Git history remain the storage/provenance record while existing GWF domain rules continue to govern applicable semantics. No `DocumentRecord` authority, lifecycle, validity, or relation state may be inferred merely from approval of this specification.

A future migration must:

- discover candidate governed documents without silently assigning authority;
- propose document IDs/classes/authority claims/relations;
- detect collisions before activation;
- preserve original Git provenance;
- distinguish inferred metadata from human/authority-approved metadata;
- avoid rewriting historical documents solely to fit the registry.

## 34. Deferred implementation decisions

Explicitly deferred:

- physical registry storage format;
- metadata location: sidecar vs front matter vs database;
- exact database schema;
- exact relation serialization;
- exact graph traversal implementation;
- exact severity model;
- exact independent-review identity policy;
- exact Markdown validator configuration;
- exact Vale rule vocabulary;
- exact Lychee network/offline policy;
- GitHub Ruleset/CODEOWNERS configuration;
- code↔docs binding fingerprint algorithm;
- Swimm or other drift adapter selection;
- Antora/Backstage adapter selection;
- OPA adoption threshold;
- generated-doc storage;
- documentation UI/editor;
- graph visualization;
- automatic patch suggestion;
- migration of existing historical documents into the registry.

These are implementation choices and do not authorize coding.

## 35. Implementation authorization boundary

This specification intentionally stops before implementation.

No agent may infer authorization to add:

- document-registry tables;
- graph storage;
- GWF document runtime services;
- markdownlint/Vale/Lychee dependencies;
- GitHub Rulesets or CODEOWNERS changes;
- Antora/Backstage/Swimm/OPA adapters;
- code↔docs drift workers;
- documentation UI;
- automatic document rewrites;

until a separate explicit implementation scope is approved after this specification and its documentation QA pass.
