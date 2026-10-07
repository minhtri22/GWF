# GWF — DG-P4 Document Facade Handoff

## 1. Scope

This handoff records bounded DG-P4 implementation qualification for stable governed-document identity over existing GWF Artifact/Revision primitives.

It does not open DG-P5, DG-P6, Wave 3, GAC, Reference Acquisition, G2E Shared Library, document relations, authority claims or bulk migration.

## 2. Frozen input identity

- DG-W1 formal-close HEAD: `2a0bb00367859166230d11d12ea482c253138dc7`
- DG-P4 pre-implementation qualification HEAD: `a6d17ceb85006d539025225a2376ff1dc32911b8`
- frozen specification commit: `149b8f7d12010fc86bda16bb9f22fcda039a2402`
- frozen specification blob: `b0034171454d06dbdeec2145ab73d5fb0cee2982`
- pre-implementation QA blob: `4b591d329091655a89646d7567093b953d748f9e`

## 3. Implementation identity

- initial implementation: `438bed30ef7ed7f05790a063fdd28d36b7eec47f`
- capability-interface repair: `a992d0906eebc12bf880a16fcef8f0da46466b12`
- qualified implementation HEAD: `633e36eda823adb0cf8cdd9d6d1877c7c4e41300`

Qualified implementation files:

- `src/gwr/domain.py` — reserved core artifact type admission;
- `src/gwr/document_facade.py` — identity/provenance facade;
- `src/gwr/runtime.py` — runtime facade binding;
- `src/gwr/plugins.py` — capability-specific GitHub adapter interface validation;
- `tests/test_dg_p4_document_facade.py` — D4-F1..D4-F15 plus interface regression;
- `tools/run_dg_p4_gate.py` — real GitHub facade qualification;
- `.github/workflows/dg-p4-document-facade.yml` — qualification workflow.

Schema/migration changes: **NONE**.

## 4. Canonical mapping delivered

```text
document_id
    = artifacts.artifact_id

document_revision_id
    = revisions.revision_id

artifact_type
    = governed_document

stable logical_key
    = gwr:document:<explicit document_key>
```

Repository full name and path remain locators, not logical identity.

## 5. Source identity

Each facade revision binds exact DG-P3 source evidence:

- GitHub provider repository ID;
- exact commit SHA;
- exact Git blob SHA;
- independent source content SHA-256;
- observed repository full name;
- path locator.

The following remain distinct:

- GWF Revision payload `content_hash`;
- Git blob SHA;
- source content SHA-256.

## 6. Storage and ownership

DG-P4 reuses:

- `artifacts`;
- `revisions`;
- existing audit/governance behavior.

DG-P4 adds no:

- DocumentRecord table;
- DocumentRevision table;
- document graph store;
- QA/finding store;
- GAC store.

The facade itself performs no direct Artifact/Revision database insert.

## 7. Core artifact admission

`governed_document` is a reserved cross-domain core artifact type.

- domains do not need to duplicate its declaration;
- domain collision with the reserved type fails closed;
- unknown non-core types still fail;
- ordinary domain artifact behavior is preserved.

## 8. Governance and lifecycle boundary

Facade mutations retain:

- project mutable-state checks;
- `GovernanceKernel.authorize(CREATE_REVISION)`;
- KnowledgeKernel mutation;
- existing audit events;
- optimistic artifact version checks.

P4 creates identity/provenance only.

It does not establish:

- normative authority;
- Documentation Governance lifecycle transitions;
- final validity semantics;
- document relations;
- QA admission.

New revisions retain existing KnowledgeKernel `UNVERIFIED` behavior.

## 9. Adapter interface repair

Qualification exposed that a `REPO_READ`-only GitHub connection still required an adapter with `commit_files`.

The repaired interface now requires:

```text
read-only connection:
    get_branch_head
    get_file
    get_commit

CONTENT_WRITE / WORKFLOW_WRITE:
    above +
    commit_files
```

Action-level capability enforcement and SHA-safe write behavior remain unchanged.

## 10. Qualification evidence

Negative run preserved:

- workflow `35582000925`
- head `438bed30ef7ed7f05790a063fdd28d36b7eec47f`
- outcome: FAIL during fixture setup before real-provider smoke.

Qualified run:

- workflow `35582178488`
- head `633e36eda823adb0cf8cdd9d6d1877c7c4e41300`
- result: **PASS**
- artifact: `10630782224`
- artifact digest: `sha256:f050ee29f3bc7b68e3b0c44657436708f9de4b657b1cee6d6794bb719b36290f`

Qualification results:

- D4-F1..D4-F15: **PASS**
- capability-interface regression: **PASS**
- real GitHub document facade: **PASS**
- provider repository ID: `1374857546`
- exact spec Git blob: `b0034171454d06dbdeec2145ab73d5fb0cee2982`
- exact commit binding: **PASS**
- exact blob binding: **PASS**
- source SHA-256 binding: **PASS**
- new Revision = `UNVERIFIED`: **PASS**
- no relation/QA Evidence/Gate side effects: **PASS**
- full repository regression: **163/163 PASS**
- compile: **PASS**

## 11. Findings

F-57 through F-63 are resolved in `docs/Finding_checklist.md`.

Technical findings and negative runs remain in the finding/handoff record. `LINEAGE.md` records completed outcomes only.

## 12. Explicit non-scope

Not implemented by DG-P4:

- DocumentQARecord / DocumentFinding;
- lifecycle / validity mapping;
- authority claims;
- typed document relations;
- change classification;
- DocumentChangeSet;
- bulk migration;
- GAC;
- Reference Acquisition;
- G2E;
- automatic source mutation.

## 13. Formal-close criterion

DG-P4 is implementation-qualified at `633e36eda823adb0cf8cdd9d6d1877c7c4e41300`.

Formal close requires:

1. commit this handoff package;
2. run the DG-P4 workflow on that exact handoff HEAD;
3. require D4 fixtures, real-provider smoke, full regression and compile to PASS;
4. preserve exact run and artifact identities.

Until that PASS exists, DG-P4 is not formally closed and DG-P5 remains not started.


## 14. Formal-close evidence

The committed handoff HEAD `06e477b83f503c0a2eb0cdff16c33a8687545f1b` was requalified on its exact HEAD.

- exact-head workflow: `35582417034`
- conclusion: **PASS**
- evidence artifact: `10630384626`
- artifact digest: `sha256:060ecc5f9e1172b679adda4483915784174bddfa6f6ca61af5181b0ad45d2b3f`

D4-F1..D4-F15, real GitHub facade smoke, full repository regression and compile all passed again.

**DG-P4 status: FORMALLY CLOSED.**

DG-P5 is the next roadmap item. DG-W2 remains open. GAC remains locked until DG-W4 PASS.
