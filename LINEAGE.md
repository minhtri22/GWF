# GWF — LINEAGE

## Policy

This file is **append-only**.

It records completed project milestones and validated work outcomes only. It is not a session log, troubleshooting log, finding ledger, or technical-debt tracker.

Rules:

1. existing lineage entries must not be edited, deleted, reordered, or rewritten;
2. corrections are appended as new correction entries;
3. open issues, failed attempts, implementation troubleshooting and finding-level remediation belong in the applicable finding/handoff documents, not here;
4. an entry is added only after the recorded work result has completed with attributable evidence;
5. exact commit/run/artifact identities should be included when available.

---

## 2026-09-21 — DG-P0 External Validator Foundation completed

- Result: DG-P0 PASS.
- Implementation/handoff head: `ef322ff0618b83fbfaef40b096cb43f5193d8db0`.
- Exact-head workflow: `35560831581` PASS.
- Outcome: normalized external-validator foundation and markdownlint integration qualified.

## 2026-09-21 — DG-P1 Vale adapter completed

- Result: DG-P1 PASS.
- Implementation head: `385016bf6d0c3df512bae6fa8776cca32eac83ee`.
- Workflow: `35563206375` PASS.
- Evidence artifact: `10622049755`.
- Outcome: Vale terminology/prose adapter qualified on the shared validator contract.

## 2026-09-21 — DG-P2 Lychee adapter completed

- Result: DG-P2 formally closed.
- Formal-close head: `462b55b1b493c28791d237708eda7eae91b742c6`.
- Exact-head workflow: `35564699490` PASS.
- Evidence artifact: `10623990886`.
- Outcome: Lychee referential-validation adapter qualified with content-vs-tool failure separation and non-mutating behavior.

## 2026-09-21 — DG-P3 pre-implementation qualification completed

- Result: pre-implementation dependency/reuse qualification PASS.
- Qualification head: `20bb90aa791f20a57de861e2458368e7b0ce9a82`.
- Frozen specification blob: `e005776db28d57ce1276b07475b9a7f7a5b6be97`.
- Outcome: bounded Git/blob resolver contract, reuse decision and F1–F13 fixture matrix frozen.

## 2026-09-21 — DG-P3 implementation qualification completed

- Result: implementation qualification PASS.
- Qualified implementation head: `9b4426f4c0d3dd6f39b2e2b2750473fd309b779b`.
- Workflow: `35577009823` PASS.
- Evidence artifact: `10627989044`.
- Evidence artifact digest: `sha256:ca9f74f9e6b7db30b2f11b81e80604b3dc2aff1c95d0d46f590beb3cabbd82c9`.
- Outcome: exact GitHub repository/commit/blob revision evidence resolver qualified; read-only repository resolution and write capability are separated; existing SHA-safe write behavior remains qualified.


## 2026-09-21 — DG-P3 formally closed

- Result: DG-P3 PASS / formally closed.
- Handoff head: `0331eedf20910b8d3b23018a6f7c86d114258baf`.
- Exact-head workflow: `35577202015` PASS.
- Exact-head evidence artifact: `10628478735`.
- Evidence artifact digest: `sha256:ff7465f287f6b368da995a1defafc67c40cc6d6c2057132a2c0e076f8f4145b8`.
- Outcome: Wave 1's Git/blob revision evidence resolver item is complete; DG-W1 remains a separate open governance gate.


## 2026-09-21 — DG-W1 Wave 1 formally closed

- Result: DG-W1 PASS / formally closed.
- Handoff head: `84383fe2978eff8ab795c7607df6f19360a5ca1f`.
- Exact-head workflow: `35580636537` PASS.
- Evidence artifact: `10629413613`.
- Evidence artifact digest: `sha256:54b8e518ef51553b6e5be1f428d346551a1c4f7b9b53fe0936c61e592a1cafe2`.
- Outcome: Documentation Validator Foundation is complete; DG-P4 is the next roadmap item.


## 2026-09-21 — DG-P4 pre-implementation qualification completed

- Result: DG-P4 reuse/specification qualification PASS.
- Specification commit: `149b8f7d12010fc86bda16bb9f22fcda039a2402`.
- Specification blob: `b0034171454d06dbdeec2145ab73d5fb0cee2982`.
- Dependency: DG-W1 final closure head `2a0bb00367859166230d11d12ea482c253138dc7`, exact-head workflow `35580754186` PASS.
- Outcome: existing Artifact/Revision storage selected for document identity; parallel document/revision storage rejected; bounded core artifact-type admission and identity-only document facade frozen for implementation.


## 2026-09-21 — DG-P4 implementation qualification completed

- Result: DG-P4 implementation qualification PASS.
- Qualified implementation HEAD: `633e36eda823adb0cf8cdd9d6d1877c7c4e41300`.
- Workflow: `35582178488` PASS.
- Evidence artifact: `10630782224`.
- Evidence artifact digest: `sha256:f050ee29f3bc7b68e3b0c44657436708f9de4b657b1cee6d6794bb719b36290f`.
- Outcome: stable governed-document identity is implemented over existing Artifact/Revision storage with exact Git source provenance and no schema migration.


## 2026-09-21 — DG-P4 formally closed

- Result: DG-P4 PASS / formally closed.
- Handoff HEAD: `06e477b83f503c0a2eb0cdff16c33a8687545f1b`.
- Exact-head workflow: `35582417034` PASS.
- Evidence artifact: `10630384626`.
- Evidence artifact digest: `sha256:060ecc5f9e1172b679adda4483915784174bddfa6f6ca61af5181b0ad45d2b3f`.
- Outcome: governed-document logical identity and exact revision provenance are now qualified over the existing Artifact/Revision kernel with no schema migration.


## 2026-09-21 — DG-P5 pre-implementation qualification completed

- Result: DG-P5 dependency/reuse/schema qualification PASS.
- Specification commit: `9e846621faf7b1a81c605ad624f4abbc6c354470`.
- Specification blob: `29ca1c85f665468aade7fc555b634a134af9a46a`.
- Dependency: DG-P4 final formal-close HEAD `a11d9ad205272c4c16c49eddb398dee4c8a0ff05`, exact-head workflow `35582578994` PASS.
- Outcome: QA records and validator executions selected for PRIM-EVIDENCE reuse; one dedicated DocumentFinding current-state table justified; waiver/history reuse existing approval and audit primitives.


## 2026-09-21 — DG-P5 implementation qualification completed

- Result: DG-P5 implementation qualification PASS.
- Qualified implementation HEAD: `fda9f7b3c5486f629e47f13652a758de158f7d22`.
- Workflow: `35584865418` PASS.
- Evidence artifact: `10631014201`.
- Evidence artifact digest: `sha256:feb5203fafaac98640569a1d0816b6626fe7279214dfed2d41488f819f2c852e`.
- Outcome: exact-revision document QA now reuses PRIM-EVIDENCE; governed finding lifecycle persists in one dedicated current-state table with atomic QA creation and Proposal/Approval-backed waiver.


## 2026-09-21 — DG-P5 formally closed

- Result: DG-P5 PASS / formally closed.
- Handoff HEAD: `dc4e9d721bf9ee7f8bca16142f239c9fbc8364f9`.
- Exact-head workflow: `35585124780` PASS.
- Evidence artifact: `10631794399`.
- Evidence artifact digest: `sha256:a468ca9ee878606653c2f7a46b6ff015f50f67832c8ea5f149a6d73b05ef1703`.
- Outcome: exact-revision QA and governed finding lifecycle are qualified with PRIM-EVIDENCE reuse, one bounded finding-state table, atomic persistence and approval-backed waiver.


## 2026-09-21 — DG-P6 pre-implementation qualification completed

- Result: DG-P6 lifecycle/validity dependency qualification PASS.
- Specification commit: `29d3f987f4d23a752563c1e61c5df4e9dd964979`.
- Specification blob: `155a0c81c291568dbf7d2ba942a9386484f2dd14`.
- Dependency: DG-P5 final formal-close HEAD `58a4cf5f0ca33ca8e15513eb07234dc575b097bc`, exact-head workflow `35585295768` PASS.
- Outcome: document lifecycle selected for Artifact lifecycle reuse; revision validity selected for existing KnowledgeKernel reuse; documentation BLOCKED defined as a derived effective state with no schema migration or global validity-enum extension.


## 2026-09-21 — DG-P6 implementation qualification completed

- Result: DG-P6 implementation qualification PASS.
- Qualified implementation HEAD: `5f5121db3e505204452946d31de8dedb3ca5e73e`.
- Workflow: `35598284725` PASS.
- Evidence artifact: `10638170391`.
- Evidence artifact digest: `sha256:891484a4f0d54b85c5101fc7d7944b10b2c10af19a4df88e771ed1718c3b31b5`.
- Outcome: governed-document lifecycle now reuses Artifact state with optimistic audit, while evidence-derived validity reconciliation preserves the existing kernel vocabulary and exposes documentation BLOCKED only as a derived effective state.


## 2026-09-21 — DG-P6 formally closed

- Result: DG-P6 PASS / formally closed.
- Handoff HEAD: `d25454481f0d972c83225e10d3d09b1bb997faf9`.
- Exact-head workflow: `35598699495` PASS.
- Evidence artifact: `10637792150`.
- Evidence artifact digest: `sha256:370e34264c5ac33dec4c1303a6a8abc5e4e5065a4935fa70e46ae0128b89bfe4`.
- Outcome: document lifecycle and effective validity are now qualified over existing Artifact/Revision/P5 primitives with zero schema migration and unchanged global KnowledgeKernel validity vocabulary.


## 2026-09-21 — DG-W2 Wave 2 requalification completed

- Result: DG-W2 combined Wave-2 requalification PASS.
- Qualified QA HEAD: `bdce1392db5e54597a12e5de02d4d916aa081b6f`.
- Workflow: `35602717476` PASS.
- Evidence artifact: `10638479929`.
- Evidence artifact digest: `sha256:9fd5937a0c87dd51c9f6b10148bcea64fe1c0e65a9431b788a5933a7bd3f0f15`.
- Outcome: DG-P4/P5/P6 pass together on one exact HEAD; exact-revision QA invalidation, single-subsystem ownership and Wave-2 schema compatibility are jointly demonstrated.


## 2026-09-21 — DG-W2 formally closed

- Result: DG-W2 PASS / formally closed.
- Handoff HEAD: `be02cdd7eaeadc0534631f15fbe183ddb4b6c7f3`.
- Exact-head workflow: `35603196674` PASS.
- Evidence artifact: `10640780655`.
- Evidence artifact digest: `sha256:1c52ad48c2d4b38995325b4b34e55520dd0ed24d772f6b20fe3d7e14176525db`.
- Outcome: Wave 2 Minimal Documentation Kernel jointly preserves exact document identity, revision-scoped QA freshness, bounded finding persistence and compatible lifecycle/validity semantics without a parallel knowledge subsystem.
