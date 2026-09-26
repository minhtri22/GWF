# GWF — DG-P4 Pre-Implementation Document QA

## 1. QA identity

- subject: `docs/DG_P4_DOCUMENT_FACADE_SPEC.md`
- subject commit: `149b8f7d12010fc86bda16bb9f22fcda039a2402`
- subject blob: `b0034171454d06dbdeec2145ab73d5fb0cee2982`
- dependency base: DG-W1 formal-close `2a0bb00367859166230d11d12ea482c253138dc7`
- dependency exact-head workflow: `35580754186` PASS
- dependency artifact: `10629914348`

This QA binds only the exact subject blob above. Any change to the DG-P4 specification requires new QA.

## 2. Reuse qualification

| Question | Verdict |
| --- | --- |
| Can stable logical document identity map to existing Artifact? | PASS |
| Can immutable document revision identity map to existing Revision? | PASS |
| Is a parallel DocumentRecord/DocumentRevision table required? | NO |
| Is a schema migration required at P4? | NO |
| Can current KnowledgeKernel accept the cross-domain document type unchanged? | NO |
| Is the gap bounded without new storage? | YES |
| Can current authority/audit path be preserved? | YES |
| Can exact source identity reuse DG-P3? | YES |

The qualified architecture is therefore **existing storage + bounded core artifact-type admission + facade**, not a second registry.

## 3. Identity QA

PASS:

- `document_id = artifact_id`;
- document revision ID = underlying `revision_id`;
- `Artifact.logical_key = gwr:document:<explicit document_key>`;
- path is a locator, not identity;
- rename preserves document ID and creates a new revision;
- source commit/blob/digest remain revision-specific;
- same blob does not automatically merge logical documents.

## 4. Core artifact admission QA

Current `KnowledgeKernel.create_artifact()` and `create_revision()` resolve artifact configuration only through `DomainPackage.artifact()`.

For a cross-domain Documentation Governance facade, forcing every domain to declare the same document artifact type would duplicate core semantics and create domain drift.

The specification resolves this by freezing one reserved type:

`governed_document`

Implementation requirements:

- recognized by the KnowledgeKernel artifact-config path;
- stored in existing `artifacts/revisions`;
- domain packages cannot silently override it;
- all existing domain artifact behavior remains unchanged;
- arbitrary unknown types remain rejected;
- no direct DB persistence from DocumentFacade.

**Verdict: PASS as bounded implementation requirement.**

## 5. Governance QA

Existing research-domain authority policies authorize `CREATE_REVISION` without an artifact-type resource selector.

Therefore DG-P4 can preserve the existing authority path without introducing new authority semantics.

The facade must still invoke:

- project mutability checks;
- `GovernanceKernel.authorize(CREATE_REVISION)`;
- KnowledgeKernel create/revise methods;
- existing audit emission.

P4 registration itself does not establish normative document authority. DG-P7 owns authority claims.

## 6. Hash/provenance QA

The specification correctly distinguishes:

- GWF `Revision.content_hash` — canonical facade payload hash;
- Git blob SHA — provider Git identity;
- source content SHA-256 — document-byte digest.

Conflating these would make provenance ambiguous. The frozen contract keeps them separate and requires DG-P3 evidence.

## 7. Lifecycle/validity scope QA

PASS with explicit deferment:

- P4 does not invent final Documentation Governance lifecycle transitions;
- P4 does not add `BLOCKED` or review-required semantics;
- P4 does not mark a document VALID;
- underlying new Revision remains governed by existing KnowledgeKernel behavior, including `UNVERIFIED`;
- DG-P6 owns lifecycle/validity mapping.

## 8. Migration scope QA

PASS:

- no repository scan;
- no automatic registration;
- no retroactive authority assignment;
- no historical Markdown migration;
- DG-P20 remains the migration pilot.

## 9. Fixture adequacy

The D4-F1..D4-F15 matrix is sufficient to falsify the minimum identity/facade contract:

- stable identity;
- exact revision identity;
- rename/content revision behavior;
- non-path logical key;
- stale-version fail closed;
- exact source evidence;
- separate hash namespaces;
- no silent migration;
- existing domain semantics preserved;
- unknown type still rejected;
- reserved-type collision rejected;
- authority/audit preserved;
- no later-wave side effects.

## 10. Finding adjudication

- F-57 — stale roadmap current-frontier text: resolved by updating the plan to DG-P4.
- F-58 — cross-domain artifact admission gap: resolved by bounded reserved core type, no new store.
- F-59 — path/logical identity ambiguity: resolved by artifact ID + explicit stable namespaced document key.
- F-60 — payload hash vs source hash ambiguity: resolved by retaining separate namespaces.
- F-61 — P4 scope could preempt P6/P7+: resolved by explicit identity-only facade boundary.
- F-62 — silent migration risk: resolved by explicit registration only.

## 11. QA verdict

```text
DG-W1 dependency              = PASS
Artifact/Revision reuse       = PASS
parallel storage              = REJECTED
core type admission design    = PASS
exact source binding          = PASS
authority/audit preservation  = PASS
no migration                  = PASS
no later-wave semantics       = PASS
D4-F1..F15 fixture plan       = PASS
findings F-57..F-62           = RESOLVED
OPEN                          = 0
```

**DG-P4 PRE-IMPLEMENTATION QUALIFICATION: PASS**

DG-P4 implementation is not started by this document.
