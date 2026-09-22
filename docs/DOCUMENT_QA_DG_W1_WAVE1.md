# GWF — Wave 1 Requalification QA

## 1. QA identity

- Wave: DG-W1 — Documentation Validator Foundation exit gate
- QA head: `bea3cf23dd9b14cde999e9effe13e1cc9e6af1e5`
- workflow: `35580447186`
- result: **PASS**
- artifact: `10630420383`
- artifact digest: `sha256:dca557bfe7cbc4a2fadc7399cf7e0551eadca7194da8d5a28cf9b66bc69647a1`

This QA requalified DG-P0 through DG-P3 together on one exact repository revision. It does not by itself open Wave 2 or GAC.

## 2. Component requalification

| Item | Real gate | Result |
| --- | --- | --- |
| DG-P0 markdownlint | pinned markdownlint-cli2 0.23.3 | PASS |
| DG-P1 Vale | pinned Vale 3.22.0 + upstream checksum | PASS |
| DG-P2 Lychee | pinned Lychee 0.24.2 + upstream checksum | PASS |
| DG-P3 Git/blob resolver | real GitHub repository/commit/blob identity | PASS |

Wave-1 unit and compatibility tests also PASS, and compile PASS.

## 3. Exact fingerprints

### DG-P0

- tool: `markdownlint-cli2`
- version: `0.23.3`
- toolchain Git blob: `5e41a2fc7dbcc691101f6b50ac3982ebd11574d2`
- config Git blob: `af424f28bd6c29f8dbef6ead45adcf72e471acc3`
- config SHA-256: `cf8eae4e746b5da0976b7ca10462e9a471f3f551eb92e6bc868f0ad39ad45764`

### DG-P1

- tool: `Vale`
- version: `3.22.0`
- toolchain Git blob: `8c7c2156c8315d63a5e8294f70b012dc78f5d1fd`
- `.vale.ini` Git blob: `25512db6cdbe1d4b0a082e7581fcb37b6296370e`
- `.vale.ini` SHA-256: `6d9113386f1efc797f0f4bafa7dd0d6ea5caaa7e1e3de303a91088e68c59b215`
- terminology Git blob: `ad4d9c4b92633ef2ff1f975a6d1cae1e04bc4df4`
- terminology SHA-256: `760ebe50287ef544a84f62abda62b51e61848dfc4af58dc19abf6440d9788f06`
- config bundle: `sha256:270b05bb9d8930556595d3d5a805f8dc72145345545250110d3bda2b65bc55d3`
- observed binary SHA-256: `93b640bab06de3161e2913db3b6cb3db9ffceb1278fd74d47377231ee4e50ee5`

### DG-P2

- tool: `Lychee`
- version: `0.24.2`
- upstream commit: `2bba271688c1abb1503097a064e6c3bc1d1b6a9b`
- release asset SHA-256: `sha256:1f4e0ef7f6554a6ed33dd7ac144fb2e1bbed98598e7af973042fc5cd43951c9a`
- toolchain Git blob: `3d4071e0c1c268b541784510f724745bf3c18b12`
- config Git blob: `eed9625cf6a6c12f3fd51c1276f270877288429c`
- config SHA-256: `14ac358f3823a9798bc144a1f029460ceff88916e256285f254f7a5ff3ef1794`
- observed binary SHA-256: `87e6e75195df5753f08c53b5c0a13694b8328edd8df009914ae9e29b5000162d`

### DG-P3

- provider: GitHub
- provider repository ID: `1374857546`
- QA exact commit: `bea3cf23dd9b14cde999e9effe13e1cc9e6af1e5`
- subject: `docs/DG_P3_GIT_BLOB_RESOLVER_SPEC.md`
- subject Git blob: `e005776db28d57ce1276b07475b9a7f7a5b6be97`
- independent content SHA-256: `1f9683b6a71dadb16fb2a2ddac84ea1b37dbeb3766e317af5da05ceb0b5298d4`

## 4. Cross-item boundary checks

All PASS:

- all four component real gates PASS on one exact HEAD;
- P0/P1/P2 share the existing `ValidatorFinding` / `ValidatorExecution` / `ValidatorAdapter` contract;
- P3 exact repository/commit/blob identity is bound to the same QA HEAD;
- no DocumentRecord/DocumentRevision/DocumentFinding/DocumentQARecord runtime exists yet;
- no GAC CatalogEntry runtime exists yet;
- no forbidden document/GAC persistence table exists;
- cumulative finding ledger remains `OPEN = 0`;
- no source mutation or automatic repair is introduced by Wave 1.

## 5. QA verdict

```text
DG-P0 = PASS
DG-P1 = PASS
DG-P2 = PASS
DG-P3 = PASS
cross-item compatibility = PASS
exact fingerprints = RECORDED
forbidden runtime hits = []
Finding OPEN = 0
```

**WAVE 1 REQUALIFICATION QA: PASS**

DG-W1 may proceed to committed handoff + exact-head qualification.
