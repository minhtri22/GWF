# GWF — DG-P2 Handoff: Lychee Link Adapter

## 1. Item identity

- **Wave:** 1 — Documentation Validator Foundation
- **Item:** DG-P2 — Lychee link adapter
- **Branch:** `v0.8.6-dg-p2-lychee-adapter`
- **DG-P1 formal-close base:** `fcf57ef875f6c68157a45b7e9fc04c9096a00683`
- **Initial DG-P2 implementation commit:** `1df9341a4b8c6e5daab792c6d3801c9b0ea19006`
- **Technical repair commit / final implementation head:** `eb71f30916cca08e7df418e1ffbc2e91eca91a13`

DG-P2 implementation is qualified at `eb71f309...`. This handoff does not authorize DG-P3, DG-W1 closure, Wave 2, or GAC implementation.

## 2. Governance / change classification

This close package is a bounded **NORMATIVE implementation-state update**: it records DG-P2 completion evidence and the next authorization frontier. It does not widen Documentation Governance semantics.

Impact analysis:

- no downstream document is silently rewritten;
- no document dependency binding changes;
- no authority model changes;
- no validity runtime changes;
- GAC remains blocked until `DG-W4 PASS`;
- DG-P3 remains separately authorized work.

## 3. Governing dependencies

- DG-P0 formal-close implementation head: `ef322ff0618b83fbfaef40b096cb43f5193d8db0`
- DG-P1 formal-close branch head used as P2 base: `fcf57ef875f6c68157a45b7e9fc04c9096a00683`
- Documentation Integrity & Governance spec: `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md`
- Revised 7-wave plan: `docs/IMPLEMENTATION_7_WAVES_PLAN.md`
- Cumulative findings: `docs/Finding_checklist.md`

Sequential governance was preserved even though DG-P2's architectural HARD dependency is DG-P0.

## 4. External dependency qualification

- Project: `lycheeverse/lychee`
- Version: `0.24.2`
- Release tag: `lychee-v0.24.2`
- Published: `2026-05-01T15:41:38Z`
- Exact upstream commit: `2bba271688c1abb1503097a064e6c3bc1d1b6a9b`
- Linux asset: `lychee-x86_64-unknown-linux-gnu.tar.gz`
- Release asset SHA-256: `1f4e0ef7f6554a6ed33dd7ac144fb2e1bbed98598e7af973042fc5cd43951c9a`
- Observed extracted binary SHA-256 in final gate: `87e6e75195df5753f08c53b5c0a13694b8328edd8df009914ae9e29b5000162d`

No floating `latest` qualifies DG-P2.

The exact upstream 0.24.2 JSON interface used by the adapter exposes separate `error_map` and `timeout_map` structures. Lychee returns exit code 2 for link-check failures, so normalized semantics cannot be inferred from exit code alone.

## 5. Configuration identity

`tools/document_validation/lychee/lychee.toml`

- Git blob: `eed9625cf6a6c12f3fd51c1276f270877288429c`
- SHA-256: `14ac358f3823a9798bc144a1f029460ceff88916e256285f254f7a5ff3ef1794`

Pinned behavior includes:

- JSON output;
- plain/non-interactive output;
- no progress UI;
- cache disabled;
- retries fixed to 0;
- request timeout fixed to 5 seconds;
- email checks disabled.

`tools/document_validation/lychee/toolchain.json`

- Git blob: `3d4071e0c1c268b541784510f724745bf3c18b12`

## 6. Implementation contents

### Adapter

`src/gwr/document_validation.py`

Git blob: `31bd854593bbfd962f61d293c732d879a56ead6f`

DG-P2 adds `LycheeAdapter` while reusing:

- `ValidatorAdapter`
- `ValidatorExecution`
- `ValidatorFinding`

The established execution/content split remains:

```text
execution_status:
  SUCCEEDED
  TOOL_ERROR
  UNAVAILABLE

content_status:
  PASS
  FINDINGS
  NOT_EVALUATED
```

Normalization rules:

- missing internal file → `LYCHEE.INTERNAL_BROKEN`;
- external HTTP error with explicit status code → `LYCHEE.EXTERNAL_BROKEN`;
- external transport error without HTTP code → `TOOL_ERROR / NOT_EVALUATED / NETWORK_FAILURE`;
- timeout-map entry → `TOOL_ERROR / NOT_EVALUATED / NETWORK_FAILURE`;
- malformed JSON or inconsistent exit/report → fail closed;
- raw checked URLs are not copied into normalized finding messages;
- source mutation is checked after execution;
- subprocess environment is allowlisted rather than forwarding broad secret-bearing environment variables.

### Unit tests

`tests/test_document_validation_p2.py`

Git blob: `53b46d45a542a6a93882cf1a2b7f14c70ccd8163`

Final P2 unit suite: **10/10 PASS**.

### Real gate

`tools/run_dg_p2_gate.py`

Git blob: `e108ace3e61a41a7f323aebf53590ee344d0bcfc`

The gate uses:

- deterministic local-file internal-link fixtures;
- a loopback HTTP server for deterministic external 200/404 checks;
- a closed loopback port for transport-failure differentiation;
- repeat normalization;
- source non-mutation checks.

### Workflow

`.github/workflows/dg-p2-lychee-adapter.yml`

Git blob: `f235a63e8eeb7c2b0e92ffea784d5d9314932d57`

## 7. Negative evidence preserved

### Initial run — FAIL

- run: `35564490278`
- head: `1df9341a4b8c6e5daab792c6d3801c9b0ea19006`
- exact release archive checksum: PASS
- failure: workflow expected `/tmp/lychee-bin/lychee`, but upstream tarball contains `lychee-x86_64-unknown-linux-gnu/lychee`
- tests/gate: not executed because qualification stopped first

This run is retained as F-48 evidence.

### Repair

- commit: `eb71f30916cca08e7df418e1ffbc2e91eca91a13`
- change: exact packaged executable path + executable guard only
- unchanged: Lychee version, config, adapter semantics, fixtures, scientific/governance acceptance gates

No silent retry occurred.

## 8. Final QA evidence

Final implementation workflow:

- run: `35564566332`
- head: `eb71f30916cca08e7df418e1ffbc2e91eca91a13`
- conclusion: **PASS**

Verified:

- exact release archive checksum: PASS
- Lychee version `0.24.2`: PASS
- P2 unit tests: **10/10 PASS**
- real internal valid link: PASS
- real internal broken link: detected
- real external loopback 200: PASS
- real external loopback 404: detected
- internal/external rule identity: distinguishable
- transport failure: `TOOL_ERROR/NOT_EVALUATED`
- raw URLs not persisted in normalized findings: PASS
- deterministic repeat: PASS
- source non-mutation: PASS
- bounded P0/P1/v0.8.4/v0.8.5 regression: **44/44 PASS**
- compile: PASS

Evidence artifact:

- ID: `10623705600`
- name: `gwr-dg-p2-evidence`
- digest: `sha256:e122694d4acc6db6fa5461dc88e39de864258091bbe7883b2011929e9baf0325`

## 9. Findings resolved during implementation

- **F-48:** release archive layout assumption caused first qualification run to fail; repaired with exact packaged path.
- **F-49:** Lychee exit code 2 cannot distinguish broken links from transport failures; JSON semantics now decide content vs tool uncertainty.
- **F-50:** raw URL output may contain sensitive source-derived material; normalized findings omit raw URLs.

All are recorded as `RESOLVED` in `docs/Finding_checklist.md`.

## 10. Schema / migration / authority impact

- database schema changes: **NONE**
- migrations: **NONE**
- DocumentRecord/DocumentFinding persistence: **NONE**
- document registry/graph: **NONE**
- lifecycle/validity runtime: **NONE**
- authority semantics: **NONE**
- Reference Acquisition runtime: **NONE**
- GAC runtime: **NONE**
- G2E Library runtime: **NONE**
- link auto-repair/source mutation: **NONE**

The adapter reports validation evidence only. Lychee does not decide authoritative GWF document validity.

## 11. Security / privacy

- no reusable provider token is introduced;
- exact upstream release asset is checksum-verified;
- subprocess environment is restricted to a small operational allowlist;
- raw Lychee JSON is not persisted in normalized execution state;
- raw URLs, including query strings, are not persisted in finding messages;
- source files are checked for mutation;
- no auto-fix or link rewrite is invoked.

## 12. Known limitations

- real Lychee qualification target is Linux CI;
- Windows execution is not separately qualified in DG-P2;
- transport uncertainty intentionally makes the subject `NOT_EVALUATED` rather than guessing document failure;
- link semantics are bounded to Lychee 0.24.2's qualified JSON interface;
- no persistent DocumentQARecord/DocumentFinding database exists yet;
- DG-P3 Git/blob evidence resolver is not implemented;
- Wave 1 remains open;
- GAC remains documentation-only and blocked until `DG-W4 PASS`.

## 13. Rollback / recovery

DG-P2 introduces no database state.

Rollback can revert:

1. repair commit `eb71f30916cca08e7df418e1ffbc2e91eca91a13`;
2. initial implementation commit `1df9341a4b8c6e5daab792c6d3801c9b0ea19006`.

DG-P1 remains independently formal-closed at base `fcf57ef875f6c68157a45b7e9fc04c9096a00683`.

## 14. Explicit non-scope

DG-P2 did not implement:

- DG-P3 Git/blob revision resolver;
- document registry;
- document dependency graph;
- validity/state propagation;
- semantic contradiction analysis;
- link auto-repair;
- GAC catalog/search/runtime;
- Reference Acquisition runtime;
- G2E Library runtime;
- agent interoperability runtime.

## 15. Formal-close criterion

After this handoff/checklist/plan commit is written, the DG-P2 workflow must run again on that **exact new HEAD**. Only an exact-head PASS completes formal-close.

## 16. Current frontier

```text
DG-P0 PASS
   ↓
DG-P1 PASS
   ↓
DG-P2 PASS
   ↓
DG-P3 — Git/blob revision evidence resolver
   NEXT PLANNED
   NOT AUTOMATICALLY AUTHORIZED
   ↓
STOP
```

**DG-P3 is not automatically authorized. DG-W1 remains open. GAC remains blocked until DG-W4 PASS.**
