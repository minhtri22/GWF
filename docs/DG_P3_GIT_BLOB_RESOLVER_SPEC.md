# GWF — DG-P3 Git/Blob Revision Evidence Resolver Specification

## 1. Status and authorization boundary

**Item:** DG-P3 — Git/blob revision evidence resolver  
**Wave:** 1 — Documentation Validator Foundation  
**Specification state:** FROZEN FOR DOCUMENT QA  
**Implementation state:** AUTHORIZED_NOT_STARTED  
**Specification base:** DG-P2 formal-close head `462b55b1b493c28791d237708eda7eae91b742c6`

The human authorization gate for DG-P3 has passed. This document qualifies dependencies and freezes the bounded resolver contract. It does **not** authorize implementation to begin before this specification passes exact document QA and the cumulative finding checklist returns `OPEN = 0`.

This document does not open DG-W1, Wave 2, GAC, Reference Acquisition, G2E Library, document registry/graph, document validity runtime, or any new authority semantics.

## 2. Governing exact revisions inspected

All conclusions in this specification are based on the exact DG-P2 formal-close repository state.

| Artifact | Exact Git blob |
| --- | --- |
| `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` | `e50d0f17433c6f0ec57f987278a0d24a7bbd4610` |
| `docs/IMPLEMENTATION_7_WAVES_PLAN.md` | `a69e46107049b3309e82c560eef7b9373ae373ea` |
| `docs/GITHUB_SHA_QA_STANDARD.md` | `b3e2528c551bd137a0ca6ee063db508f45dab1cf` |
| `docs/v0.8.4-github-plugin-sha-qa.md` | `948c8453b6b429f32df18cd01b940385401da685` |
| `src/gwr/github_plugin.py` | `19d3f8ce0baf38675bd0ca7938d781ff1521bca3` |
| `src/gwr/github_rest_adapter.py` | `dbf370b4e9c7d052a96e3ad41de176205263525e` |
| `src/gwr/plugins.py` | `4b1caf00f83250018c07af43541906b245996d7d` |
| `src/gwr/knowledge.py` | `4f848c2be53451df01b9b91d2705ae3c59aa7bf7` |
| `src/gwr/object_store.py` | `d9d8f2ca42ce747b43463f4ca037aae234037d6e` |
| `src/gwr/execution.py` | `87dfa05789acc71c7681c3ca1e6e3bd9895025d3` |
| `src/gwr/db.py` | `b9825998757423822ab7ffb22bd37dd202f3e30d` |
| `src/gwr/migrations.py` | exact revision at base head |
| `migrations/0001_v05_production_foundation.sql` | `c500c9bf57b1be022a45a6499a4a354a94caa6e4` |
| `tests/test_v084_github_plugin_sha_qa.py` | `047f835b4f94ba68b47e679ee2cae8f37ca9ce04` |

The Documentation Governance specification requires immutable document-revision identity to be bindable to repository, commit and blob/content evidence. Its Git integration boundary states that Git contributes exact commit/blob evidence while GWF retains document semantics.

## 3. Existing v0.8.4 GitHub SHA QA behavior

The v0.8.4 path already establishes the following reusable invariants:

1. Git SHA inputs are full 40-hex SHA-1 or 64-hex SHA-256 values; short SHA input is rejected.
2. repository writes are bound to a `GitHubRepositoryBinding`;
3. branch HEAD is checked against a frozen expected SHA;
4. UPDATE/DELETE is checked against an exact expected blob SHA;
5. branch HEAD is rechecked immediately before write;
6. provider-side commit uses the frozen expected parent;
7. post-commit commit parent, branch HEAD and file content are independently re-fetched and verified;
8. stale SHA is not silently refreshed or retried;
9. plugin credentials are runtime-only and are not persisted in GWF;
10. `COMMITTED != VERIFIED`.

DG-P3 reuses these identity and fail-closed rules. It must not implement a second SHA parser, a second connection store, a second repository binding store, or an alternate credential path.

## 4. Existing primitive inventory

### 4.1 Artifact / Revision

`KnowledgeKernel` already owns logical `Artifact` identity and immutable `Revision` records. Revision payload/content identity is immutable and supersession updates current state without rewriting prior payloads.

**DG-P3 use:** consumer integration only. A successful Git resolution may later be attached to a governed document revision by Documentation Governance, but DG-P3 does not create, migrate, or infer Artifact/Revision state.

### 4.2 ObjectRef

`ObjectRefService` already owns content-addressed GWF objects with:

- stable `ref_id`;
- SHA-256;
- byte size;
- content type;
- content-addressed object key.

**DG-P3 use:** none required for resolver qualification. A Git blob SHA is provider identity, not automatically a GWF `ObjectRef`. Creating an ObjectRef is an explicit later consumer action if a payload snapshot must be stored locally.

### 4.3 Generic Evidence

`ExecutionService.add_evidence` already provides generic attributable evidence persistence with subject refs, payload hash and trust class.

**DG-P3 use:** no new evidence table is required. The resolver core returns a normalized immutable evidence value. A caller that has a governed reason to persist it may use the existing evidence primitive; persistence is not required for resolution itself.

### 4.4 GitHub PluginConnection / RepositoryBinding

The current plugin layer already stores:

- opaque external connection reference;
- declared capabilities;
- non-secret metadata;
- GitHub repository binding with `repository_full_name`.

Credentials are resolved only at request time.

### 4.5 GitHub REST adapter

The current adapter already provides:

- `get_branch_head(repository, branch)`;
- `get_file(repository, path, ref)`;
- `get_commit(repository, commit_sha)`;
- Git Data write operations with expected-head concurrency.

The read primitives are sufficient to resolve exact commit/blob evidence except for one bounded gap: there is no normalized provider repository-identity read that captures GitHub's stable repository ID.

## 5. Reuse verdict

### 5.1 No new persistence primitive required

**Verdict: REUSE_EXISTING_PRIMITIVES.**

DG-P3 does **not** require:

- a new repository registry;
- a new artifact table;
- a new revision table;
- a new object store;
- a new evidence table;
- a new document table;
- a schema migration.

### 5.2 Bounded adapter/service additions are required

DG-P3 implementation may add only the minimum read-side capability necessary to resolve exact identity:

1. a provider repository identity read, returning at least provider repository ID and observed full name;
2. a read-only resolver service/facade that composes repository identity + exact commit + exact file/blob resolution;
3. operation-level capability enforcement so resolution requires `REPO_READ` but not `CONTENT_WRITE`.

This is an interface extension over existing primitives, not a new persistence subsystem.

## 6. Least-privilege qualification finding

Current `GitHubPluginService.bind_repository` requires both `REPO_READ` and `CONTENT_WRITE`. That was valid for the v0.8.4 write path but is over-broad for a read-only evidence resolver.

DG-P3 freezes the following security correction for implementation:

- repository binding creation must be usable with `REPO_READ` alone;
- every write preparation path must explicitly require `CONTENT_WRITE`;
- workflow-file writes retain the additional `WORKFLOW_WRITE` requirement;
- this relocation of the capability check must not weaken existing write tests.

No new capability name or authority semantic is introduced.

## 7. Repository identity contract

A successful DG-P3 result must not treat `owner/name` or a file path as immutable identity by themselves.

Minimum repository identity:

- `provider = "github"`;
- GWF `binding_id`;
- provider-issued stable `repository_id`;
- `repository_full_name_at_resolution`.

For the current GWF repository, GitHub currently resolves:

- repository ID: `1374857546`;
- full name: `minhtri22/GWF`.

The numeric provider repository ID is the stable provider identity. `repository_full_name_at_resolution` remains an attributable locator and is retained for audit/readability.

## 8. DG-P3 resolver request contract

Conceptual request:

```text
GitBlobResolveRequest
  project_id
  binding_id
  actor_id
  ref_kind = BRANCH | COMMIT
  ref_value
  path
  expected_repository_id?   # optional verification expectation
  expected_commit_sha?      # optional verification expectation
  expected_blob_sha?        # optional verification expectation
```

Constraints:

- `path` is normalized as a safe relative repository locator;
- commit expectations use the existing full-SHA parser;
- short SHAs are invalid;
- symbolic branch resolution must produce an exact commit before file lookup;
- the file is then fetched by **exact resolved commit SHA**, never by a floating branch name;
- tags and pull-request refs are outside DG-P3 minimum scope;
- bounded DG-P3 targets UTF-8 documentation/source text supported by the existing `get_file` adapter path; generic binary Git blob retrieval is deferred.

## 9. DG-P3 resolver result contract

Conceptual successful result:

```text
GitBlobRevisionEvidence
  provider
  binding_id
  repository_id
  repository_full_name_at_resolution
  requested_ref_kind
  requested_ref_value
  resolved_commit_sha
  commit_tree_sha
  path_locator
  blob_sha
  content_sha256
  content_size_bytes
  resolved_at
```

Rules:

- repository ID + commit SHA + blob SHA are the immutable provider identity core;
- `path_locator` is evidence about where the blob was observed at that commit, not identity;
- `content_sha256` is an independent GWF digest of returned UTF-8 content;
- raw file content is not part of the normalized evidence object;
- credentials, Authorization headers, provider tokens and opaque runtime secrets are never included;
- provider response bodies are not persisted merely for convenience.

## 10. Resolution algorithm

```text
authorize project use
        ↓
load GitHub repository binding
        ↓
require active connection + REPO_READ
        ↓
resolve provider repository identity
        ↓
if expected_repository_id supplied:
  exact compare or fail closed
        ↓
resolve ref to exact commit SHA
        ↓
if expected_commit_sha supplied:
  exact compare or STALE
        ↓
fetch commit metadata by exact commit SHA
        ↓
fetch path by exact commit SHA
        ↓
capture Git blob SHA + independent content SHA-256
        ↓
if expected_blob_sha supplied:
  exact compare or STALE
        ↓
return normalized GitBlobRevisionEvidence
```

No step may silently replace an expected repository/commit/blob identity with current provider state.

## 11. Failure semantics

DG-P3 reuses existing GWF exceptions where sufficient.

Minimum fail-closed outcomes:

- invalid/short SHA → `ValidationError`;
- binding not found → `NotFound`;
- connection inactive / missing `REPO_READ` → authorization/validation failure;
- provider repository identity unavailable → `ValidationError` / provider read failure;
- expected repository ID mismatch → `StaleVersion`;
- expected commit mismatch → `StaleVersion`;
- expected blob mismatch → `StaleVersion`;
- path absent at exact commit → `NotFound`;
- non-file path → `ValidationError`;
- provider/network failure → provider/tool failure, never a fabricated successful evidence record;
- non-UTF-8 subject in bounded DG-P3 → `ValidationError`, not silent transcoding.

No automatic re-resolution, expected-SHA refresh, fallback ref, rescue ref, or retry-to-PASS is permitted.

## 12. Frozen fixture matrix

### F1 — exact repository / branch / blob success

A bound repository and branch resolve to provider repository ID, exact commit SHA and exact blob SHA. Result records independent content SHA-256.

### F2 — exact commit request success

A full commit SHA resolves the path without consulting a moving branch after commit identity is established.

### F3 — stale expected repository identity

Provider repository ID differs from the frozen expected ID. Resolver raises `StaleVersion`; no successful evidence is emitted.

### F4 — stale expected commit

Branch resolves to a commit different from `expected_commit_sha`. Resolver raises `StaleVersion`; it must not silently adopt the new branch HEAD.

### F5 — stale expected blob

Exact commit resolves the path to a blob different from `expected_blob_sha`. Resolver raises `StaleVersion`.

### F6 — path is not identity

The same path at two exact commits resolves to different blob SHAs. Evidence identity differs even though path is unchanged.

### F7 — blob survives locator change

The same blob content is observable at a different path/commit. Path changes do not create a claim that path itself is immutable identity.

### F8 — missing subject

Path absent at the exact commit returns `NotFound`; it is not encoded as an empty successful result.

### F9 — short SHA rejected

Short commit/blob SHA input is rejected using the existing full-SHA rule.

### F10 — read-only capability

A connection with `REPO_READ` can resolve evidence. It cannot prepare or execute a write without `CONTENT_WRITE`.

### F11 — credential boundary

Secret-like values exist only in the runtime credential resolver. Neither result, persisted binding metadata, audit metadata nor error details contain credential material.

### F12 — provider failure

Repository/commit/file provider read failure yields no successful evidence object and no fallback to a floating ref.

### F13 — deterministic normalization

Repeated resolution against the same exact repository ID + commit + path yields equivalent normalized identity/digests except allowed observational timestamp fields.

## 13. Security and privacy boundary

DG-P3 inherits the v0.8.4 credential boundary:

- persist only opaque connection references;
- resolve credentials at request time;
- never store tokens, refresh tokens, passwords, API keys, private keys, Authorization headers or secret-like provider values.

DG-P3 additionally requires:

- normalized evidence excludes raw file content;
- normalized evidence excludes provider response bodies;
- error details must not echo credentials or Authorization headers;
- audit metadata records identity/digest fields only;
- resolution requires only `REPO_READ`;
- no mutation endpoint is invoked by the resolver.

## 14. Implementation scope freeze

When implementation is permitted after document QA, the bounded scope is:

```text
existing PluginConnection / GitHubRepositoryBinding
        ↓
provider repository identity read
        ↓
GitBlobRevisionEvidence normalized value
        ↓
read-only resolver service
        ↓
F1..F13 fixtures
        ↓
bounded v0.8.4 SHA-QA regression
        ↓
compile / exact-head workflow
```

Permitted implementation files are expected to remain within existing GitHub plugin/adapter modules, tests and a DG-P3 gate/workflow if required by the established GWF pattern.

Any schema migration requires a new finding and explicit scope review because this qualification concludes that no schema change is required.

## 15. Explicit non-scope

DG-P3 must not implement:

- DocumentRecord / DocumentRevision persistence;
- document registry;
- document dependency graph;
- lifecycle/validity runtime;
- document authority resolution;
- Git history as semantic document authority;
- ObjectRef creation as an automatic side effect;
- GAC catalog/publication/search;
- G2E Shared Library;
- Reference Acquisition;
- PR/CODEOWNERS/Ruleset semantics;
- tag/PR-ref resolver expansion;
- binary Git blob storage;
- auto-repair;
- source mutation;
- new credential persistence;
- new authority semantics;
- DG-W1 formal-close before DG-P3 implementation itself passes.

## 16. Qualification verdict

**REUSE VERDICT: PASS — existing primitives are sufficient.**

Required implementation delta is a bounded read-only resolver façade plus provider repository-identity read and least-privilege capability separation. No new canonical store or persistence schema is justified.

This verdict is provisional until exact document QA binds this specification revision and the cumulative finding checklist returns `OPEN = 0`.
