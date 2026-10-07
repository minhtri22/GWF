# GWF — DG-P1 Handoff: Vale Terminology / Prose Adapter

## 1. Item identity

- **Wave:** 1 — Documentation Validator Foundation
- **Item:** DG-P1 — Vale terminology/prose adapter
- **Branch:** `v0.8.6-dg-p1-vale-adapter`
- **DG-P0 base:** `ef322ff0618b83fbfaef40b096cb43f5193d8db0`
- **Reconciled documentation carry commit:** `77ce348d757c18b232716c535c535b133827ea00`
- **Initial DG-P1 implementation commit:** `ac99621a603269858dc52654aef28c342d27cd80`
- **Final DG-P1 implementation head:** `385016bf6d0c3df512bae6fa8776cca32eac83ee`

DG-P1 is complete at `385016bf...`. This handoff does not authorize DG-P2 or GAC implementation.

## 2. Governing dependency identities

- Documentation Integrity & Governance spec: `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md`
  - Git blob `e50d0f17433c6f0ec57f987278a0d24a7bbd4610`
- Reconciled 7-wave plan used for authorization:
  - Git blob `229decfb067ead7ef38d51012b06abf69cc12fc0`
- GAC/7-wave reconciliation QA:
  - `docs/DOCUMENT_QA_GAC_7_WAVES_RECONCILIATION.md`
  - Git blob `fe5e076c34f7665bb0d6cd354ae779b83e18a29a`
- DG-P0 hard-dependency handoff head:
  - `ef322ff0618b83fbfaef40b096cb43f5193d8db0`
  - exact-head workflow `35560831581` PASS

## 3. External dependency qualification

- Project: `vale-cli/vale`
- Release: `v3.22.0`
- Published upstream: 2026-09-17
- Revalidated for DG-P1: 2026-09-21
- Linux release asset: `vale_3.22.0_Linux_64-bit.tar.gz`
- Checksums asset: `vale_3.22.0_checksums.txt`
- CI verifies the release asset against the checksum file before execution.
- Observed binary SHA-256 in final gate:
  `93b640bab06de3161e2913db3b6cb3db9ffceb1278fd74d47377231ee4e50ee5`

No floating `latest` qualifies DG-P1.

## 4. Configuration / vocabulary identity

- `tools/document_validation/vale/.vale.ini`
  - Git blob `25512db6cdbe1d4b0a082e7581fcb37b6296370e`
  - SHA-256 `6d9113386f1efc797f0f4bafa7dd0d6ea5caaa7e1e3de303a91088e68c59b215`
- `tools/document_validation/vale/styles/GWF/Terminology.yml`
  - Git blob `ad4d9c4b92633ef2ff1f975a6d1cae1e04bc4df4`
  - SHA-256 `760ebe50287ef544a84f62abda62b51e61848dfc4af58dc19abf6440d9788f06`
- Aggregate configuration bundle SHA-256:
  `270b05bb9d8930556595d3d5a805f8dc72145345545250110d3bda2b65bc55d3`

Initial governed terminology rules intentionally remain bounded:

- `ARC fallback layer` → `ARC Agent Pool / Worker Fabric transport`
- `GAC Evidence Library` → `GWF Governed Artifact Catalog`
- `GWF library database` → `GWF Governed Artifact Catalog`

This is terminology linting only. It does not claim semantic contradiction detection.

## 5. Implementation contents

### Adapter

`src/gwr/document_validation.py`  
Git blob: `8963ceefeb9d6e53b47d5d874926d7d113be86dd`

DG-P1 adds `ValeAdapter` while reusing the DG-P0 normalized contracts:

- `ValidatorAdapter`
- `ValidatorExecution`
- `ValidatorFinding`

Execution/content state remains separate:

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

Vale-specific behavior:

- exact `vale --version` verification;
- deterministic config-bundle hashing;
- built-in Vale JSON output parsing;
- severity/rule/line/column normalization;
- warnings/suggestions may produce `FINDINGS` with process exit 0;
- exit 1 without parsed findings fails closed;
- raw `Match` is never persisted;
- source mutation is checked after execution.

### Tests

`tests/test_document_validation_p1.py`  
Git blob: `b044b69b6b7e257ff4c59e75ee8335e966c2eae1`

Final unit suite: **10/10 PASS**.

### Gate

`tools/run_dg_p1_gate.py`  
Git blob: `746c6ef240f6696dc8846dc8cf86d21bdc731c54`

Workflow:

`.github/workflows/dg-p1-vale-adapter.yml`  
Git blob: `c74a651eb182f786e183f0954d0ec41e43eb4344`

## 6. Final QA evidence

Final workflow:

- run: `35563206375`
- head: `385016bf6d0c3df512bae6fa8776cca32eac83ee`
- conclusion: **PASS**

Verified in final run:

- Vale release checksum: PASS
- Vale version `3.22.0`: PASS
- P1 unit tests: **10/10 PASS**
- real Vale clean fixture: PASS
- real terminology-drift fixture: PASS
- config/vocabulary hashes: PASS
- source-match redaction: PASS
- deterministic repeat: PASS
- source non-mutation: PASS
- bounded P0/v0.8.4/v0.8.5 regression: **34/34 PASS**
- compile: PASS

Evidence artifact:

- ID: `10622049755`
- name: `gwr-dg-p1-evidence`
- digest: `sha256:6ab11c80eccab0cefdb845ebf3c2c81c8ccd7c4adcd0f8b1637995314db2a535`

A prior implementation run `35562988832` also passed before the additional generic secret-like redaction regression was added. The final run above supersedes it for DG-P1 completion evidence.

## 7. Findings resolved during implementation

### F-45 — Vale exit/content semantics

Vale may emit suggestion/warning findings while exiting 0. DG-P1 therefore never equates exit 0 with prose PASS.

### F-46 — raw Match privacy boundary

Vale JSON contains source `Match`. DG-P1 omits it and redacts an echoed exact match from persisted messages.

### F-47 — configuration identity

Vale behavior depends on rule files as well as `.vale.ini`; DG-P1 binds both exact files and an aggregate config-bundle hash.

## 8. Schema / migration / authority impact

- database schema changes: **NONE**
- migrations: **NONE**
- DocumentRecord/DocumentFinding persistence: **NONE**
- document lifecycle/validity runtime: **NONE**
- relation/dependency graph: **NONE**
- Reference Acquisition runtime: **NONE**
- GAC runtime: **NONE**
- G2E runtime: **NONE**
- auto-fix/document mutation: **NONE**

The adapter reports evidence only; it does not grant document validity or authority.

## 9. Security / privacy

- no reusable provider secret is introduced;
- Vale release is pinned and checksum-verified;
- raw validator JSON is not persisted by the normalized result;
- raw `Match` source spans are excluded;
- messages redact exact matched source text;
- secret-like `SECRET_TOKEN=abc` regression PASS;
- source files are verified unchanged after validation.

## 10. Known limitations

- only the bounded GWF terminology rule set is qualified in P1;
- generic English grammar/style packages are not enabled;
- terminology linting does not detect cross-document semantic contradiction;
- real Vale execution is qualified on Linux CI;
- Windows execution is not yet a real Vale qualification target;
- no persistent QA/finding database exists yet;
- Lychee is not implemented;
- GAC remains documentation-only and gated behind DG-W4.

## 11. Rollback / recovery

DG-P1 introduces no database state.

Rollback may revert:

1. final security-test commit `385016bf6d0c3df512bae6fa8776cca32eac83ee`;
2. implementation commit `ac99621a603269858dc52654aef28c342d27cd80`; and
3. retain the reconciled documentation carry commit if desired.

DG-P0 remains independently qualified at `ef322ff0618b83fbfaef40b096cb43f5193d8db0`.

## 12. Explicit non-scope

DG-P1 did not implement:

- Lychee;
- Git/blob resolver DG-P3;
- document registry;
- document relations/impact/stale propagation;
- semantic contradiction analysis;
- GAC runtime/catalog/search;
- Reference Acquisition runtime;
- G2E Library runtime;
- MCP/harness/ARC.

## 13. Current frontier

```text
DG-P0 PASS
   ↓
DG-P1 PASS
   ↓
DG-P2 — Lychee link adapter
   NEXT PLANNED
   ↓
STOP
```

**DG-P2 is not automatically authorized. GAC remains blocked until DG-W4 PASS.**
