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


## 2026-09-21 — DG-P7 pre-implementation qualification completed

- Result: DG-P7 authority-claim dependency/semantic qualification PASS.
- Canonical specification commit: `f226eb8e01b2284381ba0e7cf5527518512c7ce7`.
- Canonical specification blob: `63d2252314e753b7485f1a0249dc011468be275b`.
- Dependency: DG-W2 final formal-close HEAD `f14abb9d8d8a591558ac6d4624a498eb32164726`, final exact-head workflow `35603521224` PASS.
- Outcome: actor authorization remains in PRIM-AUTHORITY; document ownership reuses Artifact/Revision identity and P5/P6 evidence semantics, while exactly one bounded `document_authority_claims` current-state table is justified for zero-to-many logical-document authority claims.


## 2026-09-21 — DG-P7 implementation qualification completed

- Result: DG-P7 implementation qualification PASS.
- Qualified implementation HEAD: `3f993ac639c8cb3147d0dc8d888c8b5266e54914`.
- Workflow: `35610704812` PASS.
- SQLite evidence artifact: `10644396006`, digest `sha256:dd838a1512d649cc1fce18d52b594699ca2e4395a2ca6cac624ba08aefd3d460`.
- PostgreSQL evidence artifact: `10644450806`, digest `sha256:cdcb6079b3e759286161d653a6e0924988826f8aa715be0400c0ba335cd8f972`.
- Outcome: explicit document authority claims now use one bounded current-state table with Proposal/Approval/Audit governance, exact composition contracts, cross-backend collision serialization and P5/P6 duplicate-authority integration.


## 2026-09-21 — DG-P7 formally closed

- Result: DG-P7 PASS / formally closed.
- Handoff HEAD: `30170e2f0b94f0cde6994c5b9b3ee7c920379688`.
- Exact-head workflow: `35611325233` PASS.
- SQLite evidence artifact: `10643909615`, digest `sha256:0480597ac095ba5f67c70cca7204173bdc3b988373e90b520bdfa98faf613825`.
- PostgreSQL evidence artifact: `10643409931`, digest `sha256:d90b98a201b3b28849135e84775af8f9a3f99a37057c46503713c7669c5a84af`.
- Outcome: document source-of-truth authority is now explicit, proposal/approval-governed, composition-aware, collision-detectable and cross-backend qualified without conflating actor authorization or introducing a parallel authority subsystem.


## 2026-09-21 — DG-P8 pre-implementation qualification completed

- Result: DG-P8 typed-document-relation semantic/dependency qualification PASS.
- Specification commit: `211308141106481104590b3d55cdc8c19d6b6d8e`.
- Specification blob: `d6996951522caa061b29f94d1b1f4f579251adaa`.
- Dependency: DG-P7 final formal-close HEAD `cf143d959b338e8d77811f5b2b79789ccbbb20aa`, final exact-head workflow `35611830804` PASS.
- Outcome: canonical typed document relations require one logical-document current-state table, while existing `trace_links` remains a distinct revision-level operational/provenance substrate whose projection use is deferred until binding and relation-specific semantics are qualified.


## 2026-09-21 — DG-P8 implementation qualification completed

- Result: DG-P8 implementation qualification PASS.
- Qualified implementation HEAD: `e784d7f56c0cfdf25ca453da48d570cd202ad0cc`.
- Workflow: `35621561857` PASS.
- SQLite evidence artifact: `10649881388`, digest `sha256:18b47ce4c730bd66a70de43eb881785281fc141c12a4f72564d4682be618d474`.
- PostgreSQL evidence artifact: `10649322400`, digest `sha256:62214aecf3fb2347626417ac467f82f32968a576b477ef8a07c387d6d7eaf05b`.
- Outcome: canonical typed document relations now have explicit logical-document current state, governed lifecycle and provenance, while TraceLink remains unchanged as a distinct operational/provenance primitive and DG-P9 binding semantics remain unopened.


## 2026-09-21 — DG-P8 formally closed

- Result: DG-P8 PASS / formally closed.
- Handoff HEAD: `11eba1b424896b421fc4a32c8a1970dfcf6c34dc`.
- Exact-head workflow: `35622268576` PASS.
- SQLite evidence artifact: `10650102588`, digest `sha256:61a5fd125cf10e767753c79372c826b8dcdaaa8e831f0e2e56da4a9f1ca00147`.
- PostgreSQL evidence artifact: `10650297246`, digest `sha256:7329e88ac80eeb5d781000b8ac356be069248a704464b043b80f87f1be4ada83`.
- Outcome: canonical typed document relations are now governed logical-document state with explicit lifecycle and provenance, while TraceLink remains unchanged and DG-P9 target-binding semantics remain unopened.


## 2026-09-21 — DG-P9 pre-implementation qualification completed

- Result: DG-P9 relation-target-binding semantic/dependency qualification PASS.
- Specification commit: `1a9f8737e36392c8a8db49b93c9371ceee16085f`.
- Specification blob: `73e1d7c8c01ea954af2a65e1df1942b4f95738f3`.
- Dependency: DG-P8 final formal-close HEAD `4a93e564adf52ae0dfdffabefaef32d431bbef6d`, final exact-head workflow `35622798852` PASS.
- Outcome: relation target binding is part of canonical DocumentRelation state; VALIDATES/GENERATED_FROM/DERIVED_FROM/SUPERSEDES are pinned, MUST_ALIGN_WITH follows logical-current, and resolution is side-effect-free with no TraceLink projection.



## 2026-09-21 — DG-P9 implementation qualification completed

- Result: DG-P9 implementation qualification PASS.
- Qualified implementation HEAD: `9ffd64a1e9b98ea307ed8f9682b88e26570dc208`.
- Workflow: `35628998000` PASS.
- SQLite evidence artifact: `10653386409`, digest `sha256:651c9a59f77d83176cbc452d39a9beebf17c27e2390ef83a96aee85ed29ea160`.
- PostgreSQL evidence artifact: `10653461137`, digest `sha256:aff7462c949ce6645bd0edc4ea130cbce884ac424a72234fc79ad8b9dc7b8ae4`.
- Outcome: canonical DocumentRelation target binding now distinguishes logical-current from exact pinned Revision identity, preserves one-time legacy binding and exact historical pins, and remains side-effect-free with no TraceLink projection or relation-aware impact execution.



## 2026-09-21 — DG-P9 formally closed

- Result: DG-P9 PASS / formally closed.
- Handoff HEAD: `5f6ecece5bbb15c36b00a35c7a4dbb6b340e0e4e`.
- Exact-head workflow: `35629583197` PASS.
- SQLite evidence artifact: `10653762329`, digest `sha256:b5151006d5a04a2b925e8a678f36b93e944f760d233a1ab05ebd5ebd60d5a593`.
- PostgreSQL evidence artifact: `10653647093`, digest `sha256:61d498e21dcf0ba3297aec5aa878e0e79a8a1ec9aa9ebe7f54fd54728197d996`.
- Outcome: relation target binding is formally closed with explicit current-vs-pinned semantics, immutable exact historical binding, qualified native DOCUMENT resolution, external fail-closed behavior and zero TraceLink/impact/validity side effects.



## 2026-09-21 — DG-P10 pre-implementation qualification completed

- Result: DG-P10 governed change-classification semantic/dependency qualification PASS.
- Specification commit: `f5d8544758cfdaeb1867c1fa9f72dab346c387c7`.
- Specification blob: `56a99967ebe815c56341b1668c3acb1a1517d589`.
- Governance frontier: DG-P9 final formal-close HEAD `7a081bd8f1f2218859963e304230a8904f56a6eb`, final exact-head workflow `35629863163` PASS.
- Outcome: one-document change classification is frozen as a pre-commit, exact-base/exact-candidate governance adjudication using immutable Evidence, monotonic QA escalation, conservative ambiguity handling and no structural/supersession execution side effects; DG-P11 retains multi-document change-set scope.



## 2026-09-22 — DG-P10 document-mutation policy Amendment 1 qualified

- Result: Amendment 1 QA PASS; unresolved CRITICAL/HIGH findings = 0.
- Reconciled amended specification commit: `54ca635bcb322902a28f4a987af19c37e14b59ae`.
- DG-P10 specification blob: `2aeec0ff251567e784372ffb700d11c37fa9a037`.
- Documentation Integrity §14 blob: `c1b863784b3ca4bbada7020017818c2340fe5d3b`.
- Outcome: project documentation is organized as GOV/phase-owned versioned documents with immutable sibling archives; document mutation consumes the active PhaseExecution AUTO/HUMAN_APPROVE mode as configuration without broadening recovery semantics; AUTO is owner-scoped and GOV/FROZEN remains blocked pending explicit user authorization; P10 plans lineage while DG-P11 retains source mutation.



## 2026-09-22 — DG-P10 implementation qualification completed

- Result: DG-P10 implementation qualification PASS.
- Qualified implementation HEAD: `cc5ec5dc15cf28f7960ddf90a409de7578effe53`.
- Workflow: `35645249596` PASS.
- SQLite evidence artifact: `10659577518`, digest `sha256:9f8e75560ca38ac8622aac628fc9f1e1db3c658648ebbaedb2be0faa824b5782`.
- PostgreSQL evidence artifact: `10659608214`, digest `sha256:c6d2a39ffcbe7c9701c717e14f2911f5a03a3cf22f1873c85325b7c051bcdf03`.
- Windows one-click/UAT artifact: `10660730609`, digest `sha256:a7337a7c96120612ce47547532ac427eaf51ff11d5e9bb983a4f34295f0e0139`.
- Outcome: one-document change classification, workflow-scoped AUTO/HUMAN_APPROVE mutation authority, GOV/FROZEN protection and deterministic version/archive lineage planning are qualified without changing recovery semantics or executing DG-P11 source mutation.



## 2026-09-22 — DG-P10 formally closed

- Formal-close basis: implementation-qualified HEAD `cc5ec5dc15cf28f7960ddf90a409de7578effe53`, workflow `35645249596` PASS.
- Exact committed handoff HEAD: `83d7d5c3fcf6a4d4d182af93244bf6e3e1228382`, workflow `35647135853` PASS.
- Handoff SQLite artifact: `10661015045`, digest `sha256:7fec878f784105e86c9cfed2b4dd888b35cb43e19e83a6e3e91a9ddb5aaeb2ce`.
- Handoff PostgreSQL 17 artifact: `10660019330`, digest `sha256:3128253537083b65604c898b80bbf9b08717461280ce24158b69ed1ef523b7ae`.
- Handoff Windows UAT artifact: `10661103663`, digest `sha256:4f5eec01b8b269d2e92e0b9cd19a9dc18637ce4987b787e36d33c654769b2444`.
- Outcome: DG-P10 change classification, workflow-scoped document mutation authority, GOV/FROZEN protection and deterministic archive/version lineage planning are formally closed. Concrete source mutation remains DG-P11 and is not authorized by this closure.


## 2026-09-22 — Lineage recording policy clarified

- Governance rule: LINEAGE records only the final attributable result of a completed important phase, gate, or project step.
- Technical repair attempts, harness defects, troubleshooting iterations, transient failed runs, and implementation-level remediation are not lineage milestones and remain outside this file.
- Existing historical entries are preserved under the append-only policy; this clarification governs future entries.

## 2026-09-22 — DG-P10 final exact-head closure confirmed

- Result: DG-P10 FORMALLY_CLOSED / final exact-head confirmation PASS.
- Final formal-close HEAD: `a09f79ae74a838d2c5998813560373c849669872`.
- Final exact-head workflow: `35671227699` PASS.
- SQLite artifact: `10671026264`, digest `sha256:69f66e83d91b188e65d6bb82bea6029a01777f5fd06cc701c4b34edba954f9a3`.
- PostgreSQL 17 artifact: `10671440727`, digest `sha256:3462c7e968e7abd9084cec124f0f18b351e35fa701bceb7f50d26a7bf4683e4e`.
- Windows exact-head artifact: `10671293043`, digest `sha256:2130e5035a3a477a02e7caba1ecb66c0991f5514c6f871ab0671a79800b71dbf`.
- Outcome: DG-P10 one-document change classification, workflow-scoped document mutation authority, GOV/FROZEN protection, and deterministic archive/version lineage planning are closed on the immutable final HEAD. DG-P11 remains unopened by this result.
