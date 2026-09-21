# GWF — DG-P3 Git/Blob Revision Evidence Resolver Handoff

## 1. Scope

This handoff records bounded DG-P3 implementation qualification. It does not open DG-W1, Wave 2, GAC, Reference Acquisition or G2E Library.

## 2. Frozen input identity

- pre-implementation qualification head: `20bb90aa791f20a57de861e2458368e7b0ce9a82`
- frozen DG-P3 specification commit: `f8d18e55d17344f10c0eb45c9d8beb3df6eea279`
- frozen DG-P3 specification blob: `e005776db28d57ce1276b07475b9a7f7a5b6be97`
- pre-implementation QA blob: `8592090a6eebe85a23b38715bb88f69b27790df2`

## 3. Implementation identity

- initial implementation commit: `c3adc7e5021043743847468ece24ce371caab533`
- qualified implementation head: `9b4426f4c0d3dd6f39b2e2b2750473fd309b779b`

Qualified implementation blobs:

- `src/gwr/github_plugin.py`: capability separation + read-only exact resolver
- `src/gwr/github_rest_adapter.py`: provider repository-identity read
- `tests/test_dg_p3_git_blob_resolver.py`: F1–F13 + write-regression fixture
- `tools/run_dg_p3_gate.py`: real GitHub exact-identity smoke
- `.github/workflows/dg-p3-git-blob-resolver.yml`: bounded qualification workflow

No migration or database schema file changed.

## 4. Delivered behavior

DG-P3 now resolves:

```text
GitHub provider repository ID
        +
exact commit SHA
        +
exact Git blob SHA
        +
independent UTF-8 content SHA-256
```

Repository full name and path are retained as observed locators, not immutable identity.

Supported minimum ref modes:

- `BRANCH`: branch is resolved once to an exact commit before file lookup;
- `COMMIT`: full exact commit SHA is used directly.

Tags, PR refs and generic binary blob retrieval remain out of scope.

## 5. Least-privilege boundary

The qualified boundary is:

```text
repository binding / exact resolution
  requires REPO_READ

write preparation / execution
  requires CONTENT_WRITE

workflow-file mutation
  additionally requires WORKFLOW_WRITE
```

A read-only connection can resolve evidence and cannot prepare a write.

Existing v0.8.4 SHA-safe write regression remains intact.

## 6. Persistence and ownership

DG-P3 introduces:

- no new repository registry;
- no new Artifact/Revision store;
- no new ObjectRef store;
- no new Evidence table;
- no DocumentRecord/DocumentRevision persistence;
- no migration.

The resolver returns normalized evidence. Consumers may later persist it through existing governed primitives when separately authorized.

## 7. Security boundary

- GitHub credential is resolved at request time only;
- no credential/token is persisted;
- normalized evidence excludes raw file content;
- normalized evidence excludes provider response bodies;
- no mutation operation is invoked by resolution;
- stale expected repository/commit/blob identity fails closed;
- no silent SHA refresh/fallback/retry-to-PASS is permitted.

## 8. Qualification evidence

Initial run:

- workflow `35576942299`
- head `c3adc7e5021043743847468ece24ce371caab533`
- result: FAIL before real-provider execution; preserved as negative evidence.

Qualified run:

- workflow `35577009823`
- head `9b4426f4c0d3dd6f39b2e2b2750473fd309b779b`
- result: **PASS**
- artifact ID: `10627989044`
- artifact digest: `sha256:ca9f74f9e6b7db30b2f11b81e80604b3dc2aff1c95d0d46f590beb3cabbd82c9`

Observed real-provider evidence:

- provider: GitHub
- repository: `minhtri22/GWF`
- provider repository ID: `1374857546`
- exact commit: `9b4426f4c0d3dd6f39b2e2b2750473fd309b779b`
- subject path: `docs/DG_P3_GIT_BLOB_RESOLVER_SPEC.md`
- independent content SHA-256: `1f9683b6a71dadb16fb2a2ddac84ea1b37dbeb3766e317af5da05ceb0b5298d4`

Qualification checks:

- DG-P3 unit/fixture tests: **14/14 PASS**
- real GitHub exact identity: **PASS**
- repository ID binding: **PASS**
- exact commit binding: **PASS**
- exact blob binding: **PASS**
- independent content SHA-256: **PASS**
- raw content not normalized: **PASS**
- read-only write denied: **PASS**
- deterministic exact resolution: **PASS**
- credential material absent: **PASS**
- bounded regression: **54/54 PASS**
- compile: **PASS**

## 9. Findings

F-51 through F-56 are recorded as resolved in `docs/Finding_checklist.md`.

The finding ledger remains the place for implementation issues and remediations. `LINEAGE.md` intentionally records completed milestone outcomes only.

## 10. Explicit non-scope

DG-P3 did not implement:

- document registry/graph;
- document lifecycle/validity runtime;
- authority resolution changes;
- automatic ObjectRef creation;
- GAC;
- Reference Acquisition;
- G2E Shared Library;
- tag/PR resolver expansion;
- binary Git object persistence;
- auto-repair/source mutation.

## 11. Formal-close criterion

DG-P3 is implementation-qualified at `9b4426f4...`.

Formal close requires:

1. commit this handoff/finding/roadmap/lineage package;
2. run DG-P3 workflow on that exact handoff HEAD;
3. require every gate to PASS;
4. preserve the resulting exact-head run and artifact identity.

Until that exact-head PASS exists, DG-P3 is not formally closed and DG-W1 remains open.
