# GWF — DG-P4 Document Facade / Identity Mapping Specification

## 1. Status

**Item:** DG-P4 — Document facade / identity mapping  
**Wave:** 2 — Minimal Documentation Kernel  
**Specification state:** FROZEN FOR DOCUMENT QA  
**Implementation state:** NOT_STARTED  
**Authorized transition:** the user explicitly authorized the next roadmap step after DG-W1 success. DG-W1 final exact-head run `35580754186` passed on `2a0bb00367859166230d11d12ea482c253138dc7`.

This document qualifies reuse and freezes the minimum DG-P4 contract. It does not authorize DG-P5/P6, Wave 3, GAC, migration of existing documents, document relations, authority claims, or implementation before this specification receives exact document QA.

## 2. Exact dependency evidence

DG-P4 starts from exact DG-W1 formal-close state:

- DG-W1 closure head: `2a0bb00367859166230d11d12ea482c253138dc7`
- final closure workflow: `35580754186` PASS
- final closure artifact: `10629914348`
- artifact digest: `sha256:9ba2216e664da231f9dac902d417a388a3e150c9bec8d03192e9c494cccc3c3b`

Exact inspected governing/runtime blobs:

| Artifact | Git blob |
| --- | --- |
| `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` | `e50d0f17433c6f0ec57f987278a0d24a7bbd4610` |
| `docs/IMPLEMENTATION_7_WAVES_PLAN.md` | `2c7a3c62cdea3594be361c3b7027cbdb5c32a8e1` |
| `docs/DG_W1_HANDOFF.md` | `a3e7bfdd5b011994c78957ecc12d5900f4c76e79` |
| `src/gwr/knowledge.py` | `4f848c2be53451df01b9b91d2705ae3c59aa7bf7` |
| `src/gwr/domain.py` | `b257a675fbd8ba2da34a3009489e09ad9accc0af` |
| `src/gwr/domain_registry.py` | `a94e8b3e888b977edada5755a14ba4432e2f4b1a` |
| `src/gwr/governance.py` | `0eb8f3eeb7a6ee01512bc778241fa2ee0b42f6a6` |
| `src/gwr/runtime.py` | `86e3305fc7981babbe9ea1640b2800f47210b8bc` |
| `src/gwr/db.py` | `b9825998757423822ab7ffb22bd37dd202f3e30d` |
| `src/gwr/github_plugin.py` | `1e95f24ac29696a96fcd865d90c2e15a670c98f6` |
| `spec/01-knowledge-kernel.md` | `7ae27750f3d2672c72953808ba5da36eafd836d1` |

## 3. Reuse question

DG-P4 asks:

> Can stable governed-document identity and immutable document revisions be represented by the existing `PRIM-ARTIFACT` / `PRIM-REVISION` system without creating parallel document/revision storage?

### 3.1 Storage answer

**YES.**

Existing Artifact already provides:

- stable `artifact_id`;
- project scope;
- project-unique logical key;
- current revision pointer;
- lifecycle storage field;
- optimistic version.

Existing Revision already provides:

- immutable `revision_id`;
- immutable structured payload;
- canonical payload hash;
- creator/time;
- supersession lineage;
- validity state initialized `UNVERIFIED`.

No new DocumentRecord/DocumentRevision table is justified for DG-P4.

### 3.2 Admission gap

Existing `KnowledgeKernel.create_artifact()` accepts only an `artifact_type` present in the active project domain package. Documentation Governance is cross-domain; requiring every domain package to duplicate a document artifact declaration would couple a GWF core concern to domain vocabulary and create drift.

Therefore storage reuse is sufficient, but artifact-type admission needs one bounded core extension.

## 4. Canonical identity mapping

DG-P4 freezes this mapping:

```text
DocumentRecord.document_id
    = Artifact.artifact_id

DocumentRevision.revision_id
    = Revision.revision_id

DocumentRecord.current_revision_id
    = Artifact.current_revision_id

stable document lookup key
    = Artifact.logical_key
    = "gwr:document:" + explicit document_key
```

Rules:

1. `document_id` is never a path.
2. `document_key` is explicit and stable; it must not be derived from the current path.
3. repository full name and file path are locators only.
4. a path rename keeps the same `document_id` and creates a new revision when the governed stored state changes.
5. the same path at a later commit does not imply the same revision.
6. identical blobs do not automatically imply identical logical documents.

## 5. Reserved core artifact type

DG-P4 implementation must introduce exactly one reserved core artifact type:

```text
governed_document
```

Semantics at P4:

- maps to existing `PRIM-ARTIFACT` / `PRIM-REVISION`;
- storage is the existing `artifacts` and `revisions` tables;
- it is cross-domain and does not require modifying every domain package;
- it is identity-only at this phase;
- it does **not** grant normative authority;
- it does **not** activate Documentation Governance lifecycle semantics;
- it does **not** activate document validity semantics beyond existing revision `UNVERIFIED`;
- it does **not** create relation/graph semantics.

The type must enter KnowledgeKernel through the same artifact-config resolution used by `create_artifact` and `create_revision`. Direct database insertion from the facade is forbidden.

A domain package must not silently override the reserved `governed_document` type. Collision must fail closed.

All existing domain-defined artifact types must retain current behavior.

## 6. Governance boundary

DG-P4 does not create a new authority path.

Every facade mutation must continue to pass through:

```text
ProjectGovernance mutable check
        ↓
GovernanceKernel.authorize(CREATE_REVISION)
        ↓
KnowledgeKernel Artifact/Revision mutation
        ↓
existing audit append
```

No direct `INSERT INTO artifacts/revisions` from DocumentFacade is permitted.

Current research-domain authority policies already authorize `CREATE_REVISION` by role without an artifact-type selector. DG-P4 must not weaken those policies or add a hidden bypass.

Document authority claims remain DG-P7 scope. Registration in DG-P4 establishes identity/provenance only.

## 7. Source identity binding

A document revision backed by GitHub must bind exact source identity from DG-P3.

Minimum source identity:

- provider = GitHub;
- provider repository ID;
- repository full name observed at resolution;
- exact commit SHA;
- path locator at that commit;
- exact Git blob SHA;
- independent source content SHA-256.

The facade must consume resolver-produced exact evidence, not a mutable URL/path alone.

### 7.1 Hash distinction

Two hashes must remain distinct:

1. `Revision.content_hash` — hash of the canonical GWF revision payload;
2. `source_content_sha256` — digest of the underlying document bytes.

They must never be treated as interchangeable.

The Git blob SHA is also a separate provider identity.

## 8. Minimum revision payload

A DG-P4 document revision payload should normalize at least:

```text
schema = "DG-P4-DOCUMENT-REVISION-v1"
document_key
title
storage_locator:
  provider
  repository_id
  repository_full_name_at_resolution
  path
source_identity:
  commit_sha
  blob_sha
  content_sha256
  content_size_bytes
source_resolved_at
```

Optional descriptive document class may be recorded only as metadata. It does not grant authority or lifecycle/validity semantics at P4.

Raw document content is not duplicated into the structured payload merely to establish identity.

## 9. Facade operations

Minimum conceptual operations:

### `register_document`

Inputs include:

- project;
- explicit stable `document_key`;
- title;
- GitHub binding/ref/path and exact expectations;
- actor.

Sequence:

```text
resolve source through DG-P3
        ↓
validate exact source identity
        ↓
create Artifact(type=governed_document,
                logical_key="gwr:document:"+document_key)
        ↓
create first Revision with normalized identity payload
        ↓
return document_id + revision_id
```

Registration is explicit. Repository scanning must not auto-register files.

### `revise_document`

Inputs include:

- existing `document_id`;
- expected artifact version;
- new exact source reference;
- actor.

Sequence:

```text
load exact governed_document Artifact
        ↓
resolve new source through DG-P3
        ↓
build normalized revision payload
        ↓
KnowledgeKernel.create_revision(expected version)
        ↓
return new revision_id
```

A rename or content change therefore creates a new revision while preserving document ID.

### Read facade

Minimum read output:

- `document_id`;
- stable `document_key`;
- title/current locator from current revision;
- current revision ID;
- exact current source identity.

P4 must not expose document authority, relation graph, QA state, or document lifecycle as if those later contracts already exist.

## 10. No-silent-migration rule

Approval of DG-P4 does not register any existing Markdown automatically.

Existing repository files remain ordinary repository content until a separately invoked registration/migration action creates governed identity.

Bulk discovery/migration remains DG-P20.

## 11. Existing lifecycle and validity fields

Artifact/Revision already carry lifecycle/validity storage fields, but DG-P4 does not claim those are the final Documentation Governance state machines.

At P4:

- new revisions retain existing KnowledgeKernel behavior, including `UNVERIFIED`;
- P4 does not add `BLOCKED`, review-required, document lifecycle transitions or validity propagation;
- P6 owns documentation lifecycle + validity mapping.

This prevents P4 from preempting P6.

## 12. Frozen fixture matrix

### D4-F1 — stable document identity

Explicit registration creates one Artifact; returned `document_id == artifact_id`.

### D4-F2 — exact revision identity

Each registration/revision returns the exact underlying `Revision.revision_id`.

### D4-F3 — path rename preserves document identity

Same document, new locator, same `document_id`, new `revision_id`.

### D4-F4 — content change preserves document identity

Same locator with new exact source blob creates a new revision under the same document.

### D4-F5 — path is not identity

Two different explicit document keys may point to the same path in different governed contexts without identity being derived from the path.

### D4-F6 — stable logical key is not path-derived

Stored logical key uses `gwr:document:<document_key>`; rename does not change it.

### D4-F7 — stale expected version fails closed

Concurrent revision with stale artifact version raises existing `StaleVersion`; no silent refresh.

### D4-F8 — exact source required

Mutable path/ref without exact resolver identity cannot create a successful governed revision.

### D4-F9 — hash namespaces remain distinct

Revision payload hash, Git blob SHA and source content SHA-256 are all retained separately.

### D4-F10 — no silent migration

Starting runtime with repository Markdown does not create any `governed_document` artifact.

### D4-F11 — existing domain artifact behavior preserved

A normal domain artifact can still be created/revised exactly as before.

### D4-F12 — unknown non-core artifact still rejected

Core admission must not turn arbitrary unknown artifact types into accepted types.

### D4-F13 — reserved core type collision fails

A domain attempt to redefine `governed_document` is rejected rather than silently overriding core meaning.

### D4-F14 — authority/audit path preserved

Facade create/revise invokes existing authorization and audit; no direct persistence shortcut.

### D4-F15 — no later-wave semantics

Registration does not create document relations, authority claims, QA/finding records, GAC entries, or document validity/lifecycle transitions.

## 13. Persistence verdict

**NEW DOCUMENT TABLES: NOT JUSTIFIED.**  
**SCHEMA MIGRATION FOR DG-P4: NOT JUSTIFIED.**

Existing tables are sufficient:

- `artifacts`;
- `revisions`;
- existing audit/proposal primitives as applicable.

The only qualified implementation delta is facade/service logic plus bounded core artifact-type admission.

If implementation later demonstrates a concrete invariant that cannot be represented safely in existing primitives, that requires a new finding and explicit scope amendment before any migration.

## 14. Security and privacy

DG-P4 must:

- reuse DG-P3 read-only exact source resolution;
- not persist provider credentials;
- not copy raw source content into facade metadata by default;
- preserve project/tenant access checks;
- preserve existing mutation authority;
- never broaden source access;
- never infer authority from file ownership, path, README status or document class.

## 15. Explicit non-scope

DG-P4 must not implement:

- DocumentQARecord / DocumentFinding persistence;
- document lifecycle/validity mapping;
- authority claims or duplicate-authority detection;
- document relations or graph traversal;
- change classification;
- DocumentChangeSet;
- append-only enforcement;
- supersession policy beyond existing Revision lineage;
- bulk migration/discovery;
- GAC;
- Reference Acquisition;
- G2E Shared Library;
- code/schema/API bindings;
- automatic source mutation.

## 16. Qualification verdict

```text
Artifact/Revision storage reuse        = SUFFICIENT
parallel document/revision tables      = REJECTED
cross-domain artifact admission        = BOUNDED CORE EXTENSION REQUIRED
document_id mapping                    = artifact_id
document revision mapping              = revision_id
path as identity                       = FORBIDDEN
exact DG-P3 source binding             = REQUIRED
silent migration                       = FORBIDDEN
P5/P6/P7+ semantics                    = DEFERRED
schema migration                       = NONE
```

**DG-P4 reuse/specification qualification is ready for exact document QA.**
