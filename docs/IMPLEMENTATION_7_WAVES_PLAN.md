# GWF — 7-Wave Implementation Plan and Handoff Checklist

## 1. Status

**Document status:** implementation plan / phased authorization map.

**Planning lineage:** original 7-wave plan committed on `docs/reference-agent-interop-specs`; this revision reconciles the plan with the Governed Artifact Catalog / G2E Shared Library documentation on `docs/governed-artifact-catalog-pack`.

This plan converts the approved specification set into an ordered implementation roadmap optimized for **lower complexity first without violating hard dependencies**.

DG-P0 has formal-closed on implementation head `ef322ff0618b83fbfaef40b096cb43f5193d8db0`; exact-head workflow `35560831581` passed.

DG-P1 has formal-closed on implementation head `385016bf6d0c3df512bae6fa8776cca32eac83ee`; exact implementation workflow `35563206375` passed.

DG-P2 implementation has qualified on head `eb71f30916cca08e7df418e1ffbc2e91eca91a13`; workflow `35564566332` passed after preserving failed qualification run `35564490278`.

DG-P3 received explicit human authorization after DG-P2 formal-close. Its pre-implementation specification is frozen at commit `f8d18e55d17344f10c0eb45c9d8beb3df6eea279`, exact blob `e005776db28d57ce1276b07475b9a7f7a5b6be97`, and the bound document QA passes. **DG-P3 implementation remains NOT_STARTED in this revision.**

## 2. Governing documents

The following documents define the semantics used by this plan:

- `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` — document identity, QA, findings, relations, validity, BUILD/INTEGRATE/OPTIONAL ADAPTER matrix.
- `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md` — reference query plan, retrieval log, registry, evidence map, temporal integrity.
- `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` — harness vs Agent Pool, bindings, execution envelope, transport/governance boundary.
- `docs/GOVERNED_ARTIFACT_CATALOG_SPEC.md` — GWF Shared Library catalog/publication/query substrate.
- `docs/GOVERNED_ARTIFACT_CATALOG_INTEGRATION_BOUNDARIES.md` — ownership boundaries among GWF core, Documentation Governance, Reference Acquisition, GAC and G2E.
- `docs/Finding_doc.md` — reconciliation findings and closure checklist for the GAC/G2E Library integration.
- `docs/FUTURE_NODE_AGENT_ORCHESTRATION_PARKING_LOT.md` — explicitly deferred node-level orchestration.
- `docs/Finding_checklist.md` — cumulative resolved specification findings.
- `docs/DOCUMENT_QA_DOCUMENTATION_GOVERNANCE.md` — QA evidence for Documentation Governance.
- `docs/DOCUMENT_QA_REFERENCE_AGENT_INTEROP.md` — QA evidence for Reference Acquisition + Agent Interoperability.
- `docs/DOCUMENT_QA_GAC_7_WAVES_RECONCILIATION.md` — current cross-document QA for the GAC/G2E Library reconciliation and revised 7-wave plan.

## 3. Complexity scale

Each implementation item has one integer **priority complexity**. When an earlier analysis used a range, this plan uses the conservative upper bound so priority ordering is deterministic.

| Level | Meaning |
| --- | --- |
| **1 — Very Low** | Thin adapter/check, no authoritative state mutation |
| **2 — Low** | Small service/interface, reuses current primitives |
| **3 — Medium** | Persistence/state machine/cross-module behavior |
| **4 — High** | Authority, dependency propagation, research semantics, or external runtime |
| **5 — Very High** | Multi-agent orchestration, delegation, routing, scheduling |

Priority rule:

> Among work items whose **HARD** dependencies are satisfied, select the lowest-complexity item first. **ORDERING** dependencies preserve roadmap sequence but are not architectural prerequisites. **OPTIONAL** dependencies may improve the item but do not block it.

## 4. Dependency types

Planning control identities:

- **PLAN-QA** — `docs/DOCUMENT_QA_GAC_7_WAVES_RECONCILIATION.md` with PASS verdict bound to the exact reconciled plan blob/revision. `docs/DOCUMENT_QA_7_WAVES_PLAN.md` remains historical QA for the pre-GAC plan.
- **DIG-SPEC** — `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` exact reviewed revision.
- **DG-Wn / DG-GAC-W5 / RA-GAC-W6 / AI-W7** — the named wave exit gate with its committed handoff/evidence package.

- **HARD** — item must not start until the dependency has passed its acceptance gate.
- **ORDERING** — roadmap sequencing decision; technically separable, but intentionally scheduled later.
- **OPTIONAL** — useful enhancement, not required for correctness.
- **EXTERNAL** — external tool/service capability that must be revalidated before implementation.

Every completed item must record exact dependency revisions/evidence used. A dependency named only by logical ID is insufficient for handoff; its evidence package must resolve to exact commit/blob/run identities.

---

# Wave 1 — Documentation Validator Foundation

**Goal:** obtain immediate deterministic documentation QA value with minimal state mutation.

### DG-P0 — External Validator Foundation + markdownlint

- **Complexity:** 2
- **Status:** **COMPLETED / PASS**
- **Completion evidence:** implementation/handoff head `ef322ff0618b83fbfaef40b096cb43f5193d8db0`; exact-head workflow `35560831581` PASS.
- **HARD dependencies:**
  - PLAN-QA — this 7-wave plan must PASS.
  - DIG-SPEC — `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` exact reviewed revision.
- **EXTERNAL dependency:** markdownlint/markdownlint-cli2 capability must be revalidated and pinned before adapter execution.
- **Governing documents:**
  - `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§18–21, 32, 35.
  - this plan §Wave 1.
- **Scope:**
  - define `ValidatorAdapter` contract;
  - define normalized `ValidatorExecution`;
  - define normalized non-persistent finding result compatible with future `DocumentFinding`;
  - implement first markdownlint adapter;
  - capture validator identity/version, exact subject hash, execution status, findings and locations;
  - pin a minimal markdownlint configuration and record its content hash;
  - distinguish validator unavailable/error from document failure;
  - prohibit auto-fix and document mutation.
- **Explicit non-scope:**
  - no document registry;
  - no graph/dependency propagation;
  - no `DocumentQARecord` database persistence;
  - no research workflow changes;
  - no GitHub Ruleset/CODEOWNERS mutation;
  - no Vale/Lychee yet.
- **Acceptance checklist:**
  - [x] adapter interface is provider-neutral;
  - [x] exact input/content hash recorded;
  - [x] validator version/config identity recorded;
  - [x] valid fixture returns successful execution with zero structural findings;
  - [x] invalid fixture returns deterministic structural findings with location;
  - [x] a real pinned markdownlint-cli2 executable/version passes a smoke fixture; mocks/shims alone cannot qualify P0;
  - [x] pinned markdownlint config identity/hash recorded;
  - [x] missing/unavailable validator fixture is not represented as document FAIL;
  - [x] adapter cannot mutate source content;
  - [x] repeated identical fixture invocation normalizes equivalently;
  - [x] no secret material persisted in execution result;
  - [x] unit tests PASS;
  - [x] P0 QA gate PASS;
  - [x] exact commit/evidence recorded.

### DG-P1 — Vale terminology/prose adapter

- **Complexity:** 2
- **Status:** **COMPLETED / PASS**
- **Completion evidence:** implementation head `385016bf6d0c3df512bae6fa8776cca32eac83ee`; workflow `35563206375` PASS; evidence artifact `10622049755`.
- **HARD dependencies:** DG-P0.
- **EXTERNAL dependency:** Vale capability/version/config revalidation.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§18–21.
- **Acceptance checklist:**
  - [x] adapter uses DG-P0 normalized contract;
  - [x] project vocabulary/config hash attributable;
  - [x] terminology drift fixture detected;
  - [x] tool unavailable distinguished from content failure;
  - [x] no auto-fix mutation;
  - [x] QA PASS.

### DG-P2 — Lychee link adapter

- **Complexity:** 2
- **Status:** **COMPLETED / PASS**
- **Completion evidence:** implementation head `eb71f30916cca08e7df418e1ffbc2e91eca91a13`; workflow `35564566332` PASS; evidence artifact `10623705600`.
- **Negative evidence preserved:** initial qualification run `35564490278` FAIL before tests because the release archive executable path was assumed incorrectly; repaired without changing Lychee version, config semantics or acceptance gates.
- **HARD dependencies:** DG-P0.
- **EXTERNAL dependency:** Lychee capability/version/config revalidation.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§18–21.
- **Acceptance checklist:**
  - [x] adapter uses normalized contract;
  - [x] internal/external link results distinguishable;
  - [x] network/tool failure distinguished from broken-link finding;
  - [x] deterministic local fixture PASS/FAIL evidence;
  - [x] exact Lychee 0.24.2 release/config identity attributable;
  - [x] source non-mutation verified;
  - [x] no auto-fix/link repair mutation;
  - [x] QA PASS.

### DG-P3 — Git/blob revision evidence resolver

- **Complexity:** 2
- **Status:** **COMPLETED / PASS / FORMALLY CLOSED**
- **Frozen specification:** `docs/DG_P3_GIT_BLOB_RESOLVER_SPEC.md`, commit `f8d18e55d17344f10c0eb45c9d8beb3df6eea279`, blob `e005776db28d57ce1276b07475b9a7f7a5b6be97`.
- **Document QA:** `docs/DOCUMENT_QA_DG_P3_PREIMPLEMENTATION.md` — PASS.
- **Reuse verdict:** existing Artifact/Revision, ObjectRef, generic Evidence, PluginConnection/RepositoryBinding and v0.8.4 GitHub read/SHA primitives are sufficient; no schema migration/new canonical store.
- **Implementation evidence:** head `9b4426f4c0d3dd6f39b2e2b2750473fd309b779b`; workflow `35577009823` PASS; artifact `10627989044` digest `sha256:ca9f74f9e6b7db30b2f11b81e80604b3dc2aff1c95d0d46f590beb3cabbd82c9`.
- **Bounded implementation delivered:** provider repository-ID read + read-only resolver façade + least-privilege REPO_READ/CONTENT_WRITE separation + F1–F13 fixtures.
- **HARD dependencies:** DG-P0 contract only; sequential P1/P2 governance is already closed.
- **Governing documents:**
  - `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§8, 20, 30.
  - `docs/GITHUB_SHA_QA_STANDARD.md`.
  - existing GitHub SHA QA behavior in GWF v0.8.4.
- **Pre-implementation qualification checklist:**
  - [x] exact governing revisions loaded;
  - [x] v0.8.4 GitHub SHA QA inspected;
  - [x] Artifact/Revision/ObjectRef/Evidence primitives inventoried;
  - [x] reuse vs new primitive requirement adjudicated;
  - [x] resolver contract frozen;
  - [x] stale-SHA/repository/blob fixtures frozen;
  - [x] security/credential boundary frozen;
  - [x] document QA PASS;
  - [x] Finding checklist OPEN = 0.
- **Implementation acceptance:**
  - [x] exact repository/commit/blob identity captured in runtime;
  - [x] path is not treated as identity in runtime;
  - [x] stale expected identity fails closed in runtime;
  - [x] no credential material persisted;
  - [x] bounded regression 54/54 PASS;
  - [x] implementation QA PASS;
  - [x] handoff commit exact-head workflow PASS — run `35577202015` on `0331eedf20910b8d3b23018a6f7c86d114258baf`, artifact `10628478735`.

### Wave 1 exit gate — DG-W1

- **Status:** **COMPLETED / PASS / FORMALLY CLOSED**
- **QA head:** `bea3cf23dd9b14cde999e9effe13e1cc9e6af1e5`
- **QA workflow:** `35580447186` PASS
- **QA artifact:** `10630420383`
- **QA document:** `docs/DOCUMENT_QA_DG_W1_WAVE1.md`

- [x] DG-P0 PASS
- [x] DG-P1 PASS
- [x] DG-P2 PASS
- [x] DG-P3 PASS
- [x] markdownlint, Vale and Lychee outputs normalize through the shared validator contract
- [x] no authoritative document-state runtime added yet
- [x] Wave-1 handoff package records exact tool versions/config fingerprints
- [x] exact committed DG-W1 handoff HEAD requalification PASS — run `35580636537` on `84383fe2978eff8ab795c7607df6f19360a5ca1f`, artifact `10629413613`.

---

# Wave 2 — Minimal Documentation Kernel

**Goal:** represent governed documents and exact QA identity by reusing current GWF knowledge primitives instead of creating a parallel knowledge system.

### DG-P4 — Document facade / identity mapping

- **Complexity:** 3
- **Status:** **COMPLETED / PASS / FORMALLY CLOSED**
- **HARD dependencies:** DG-P3; DG-W1 is formally closed.
- **Frozen specification:** `docs/DG_P4_DOCUMENT_FACADE_SPEC.md`, commit `149b8f7d12010fc86bda16bb9f22fcda039a2402`, blob `b0034171454d06dbdeec2145ab73d5fb0cee2982`.
- **Document QA:** `docs/DOCUMENT_QA_DG_P4_PREIMPLEMENTATION.md` — PASS.
- **Reuse verdict:** existing `artifacts/revisions` are sufficient; no parallel tables or schema migration. A bounded reserved core artifact type `governed_document` is required because current artifact admission is domain-only.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§6–8, 33.
- **Design constraint:** specialization/facade over existing `artifacts/revisions`; direct DB writes and parallel document/revision tables are forbidden.
- **Pre-implementation checklist:**
  - [x] stable `document_id` mapped to `artifact_id`;
  - [x] exact revision identity mapped to `revision_id`;
  - [x] stable document key is independent of path;
  - [x] exact source identity reuses DG-P3;
  - [x] cross-domain artifact admission gap bounded;
  - [x] no silent migration of existing Markdown;
  - [x] current GWF artifact semantics preservation contract frozen;
  - [x] D4-F1..D4-F15 fixtures frozen;
  - [x] pre-implementation QA PASS.
- **Implementation evidence:** head `633e36eda823adb0cf8cdd9d6d1877c7c4e41300`; workflow `35582178488` PASS; artifact `10630782224` digest `sha256:f050ee29f3bc7b68e3b0c44657436708f9de4b657b1cee6d6794bb719b36290f`.
- **Implementation acceptance:**
  - [x] facade/core-type implementation PASS;
  - [x] D4-F1..D4-F15 PASS;
  - [x] real GitHub facade smoke PASS;
  - [x] existing domain artifact regression PASS;
  - [x] full regression 163/163 PASS;
  - [x] no schema migration;
  - [x] implementation QA PASS;
  - [x] handoff exact-head workflow PASS — run `35582417034` on `06e477b83f503c0a2eb0cdff16c33a8687545f1b`, artifact `10630384626`.

### DG-P5 — QA run + finding persistence

- **Complexity:** 3
- **Status:** **COMPLETED / PASS / FORMALLY CLOSED**
- **HARD dependencies:** DG-P0, DG-P4; both satisfied.
- **Frozen specification:** `docs/DG_P5_QA_FINDING_PERSISTENCE_SPEC.md`, commit `9e846621faf7b1a81c605ad624f4abbc6c354470`, blob `29ca1c85f665468aade7fc555b634a134af9a46a`.
- **Document QA:** `docs/DOCUMENT_QA_DG_P5_PREIMPLEMENTATION.md` — PASS.
- **Reuse verdict:** `DocumentQARecord` and persisted ValidatorExecution reuse PRIM-EVIDENCE. Existing primitives are insufficient for mutable DocumentFinding lifecycle, so exactly one `document_findings` current-state table is justified. Waivers reuse Proposal/Approval; transition history reuses Audit.
- **Schema decision:** no QA-record table, no validator-execution table, no waiver table; one finding table only.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§8.5–8.6, 17–18.
- **Pre-implementation checklist:**
  - [x] one `DocumentQARecord` maps to one exact PRIM-EVIDENCE record;
  - [x] zero-to-many finding relation frozen;
  - [x] finding lifecycle transitions frozen;
  - [x] exact revision freshness invariant frozen;
  - [x] prior QA cannot validate a new revision;
  - [x] waiver/approval reuse frozen;
  - [x] Evidence transactional extension bounded;
  - [x] D5-F1..D5-F20 frozen;
  - [x] document QA PASS.
- **Implementation evidence:** head `fda9f7b3c5486f629e47f13652a758de158f7d22`; workflow `35584865418` PASS; artifact `10631014201` digest `sha256:feb5203fafaac98640569a1d0816b6626fe7279214dfed2d41488f819f2c852e`.
- **Implementation acceptance:**
  - [x] migration adds only `document_findings`;
  - [x] Evidence writer transactional extension preserves existing callers;
  - [x] QA/finding service implementation PASS;
  - [x] D5-F1..D5-F20 PASS;
  - [x] existing Evidence/Gate/Failure regressions PASS;
  - [x] full repository regression PASS;
  - [x] no DG-P6/P11+ semantics;
  - [x] implementation QA PASS;
  - [x] handoff exact-head workflow PASS — run `35585124780` on `dc4e9d721bf9ee7f8bca16142f239c9fbc8364f9`, artifact `10631794399`.

### DG-P6 — Lifecycle + validity mapping

- **Complexity:** 3
- **Status:** **COMPLETED / PASS / FORMALLY CLOSED**
- **HARD dependencies:** DG-P4, DG-P5; both satisfied.
- **Frozen specification:** `docs/DG_P6_LIFECYCLE_VALIDITY_MAPPING_SPEC.md`, commit `29d3f987f4d23a752563c1e61c5df4e9dd964979`, blob `155a0c81c291568dbf7d2ba942a9386484f2dd14`.
- **Document QA:** `docs/DOCUMENT_QA_DG_P6_PREIMPLEMENTATION.md` — PASS.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§11–12.
- **Mapping verdict:** lifecycle reuses `Artifact.lifecycle_status`; persisted validity reuses `Revision.validity_state`; documentation `BLOCKED` is a derived effective state and is not added to global `KnowledgeKernel.VALIDITY`.
- **Schema decision:** zero tables, zero columns, zero migration.
- **Pre-implementation checklist:**
  - [x] lifecycle and validity separate;
  - [x] new revision begins UNVERIFIED;
  - [x] prior VALID does not transfer automatically;
  - [x] BLOCKED operational meaning mapped to derived effective state + kernel non-VALID compatibility;
  - [x] STALE/DIRTY/FAILED compatibility frozen;
  - [x] lifecycle transition subset frozen;
  - [x] archive/logical supersession dependency-gated;
  - [x] D6-F1..D6-F20 frozen;
  - [x] existing KnowledgeKernel semantics remain compatible;
  - [x] document QA PASS.
- **Implementation evidence:** HEAD `5f5121db3e505204452946d31de8dedb3ca5e73e`; workflow `35598284725` PASS; artifact `10638170391`; digest `sha256:891484a4f0d54b85c5101fc7d7944b10b2c10af19a4df88e771ed1718c3b31b5`.
- **Implementation acceptance:**
  - [x] no schema migration;
  - [x] global VALIDITY unchanged;
  - [x] lifecycle transition service uses Artifact.version + Audit;
  - [x] validity reconciliation is evidence-derived, not arbitrary setter;
  - [x] D6-F1..D6-F20 PASS;
  - [x] Knowledge/Execution/Decision/P4/P5 regressions PASS;
  - [x] full repository regression PASS;
  - [x] no DG-P7/P8 semantics;
  - [x] implementation QA PASS;
  - [x] handoff exact-head workflow PASS — run `35598699495` on `d25454481f0d972c83225e10d3d09b1bb997faf9`, artifact `10637792150`.

### Wave 2 exit gate — DG-W2

- **Status:** **COMPLETED / PASS / FORMALLY CLOSED**
- **Qualified QA HEAD:** `bdce1392db5e54597a12e5de02d4d916aa081b6f`
- **Workflow:** `35602717476` PASS
- **Evidence artifact:** `10638479929`
- **Digest:** `sha256:9fd5937a0c87dd51c9f6b10148bcea64fe1c0e65a9431b788a5933a7bd3f0f15`
- **QA:** `docs/DOCUMENT_QA_DG_W2_WAVE2.md`
- [x] DG-P4 PASS and same-head requalification PASS
- [x] DG-P5 PASS and same-head requalification PASS
- [x] DG-P6 PASS and same-head requalification PASS
- [x] exact-revision QA invalidation demonstrated
- [x] no duplicate knowledge subsystem created without justification
- [x] handoff contains schema/migration decisions and compatibility evidence
- [x] global KnowledgeKernel VALIDITY remains unchanged
- [x] no Wave-3 authority/relation state introduced
- [x] targeted regressions + full regression + compile PASS
- [x] committed handoff exact-head workflow PASS — run `35603196674` on `be02cdd7eaeadc0534631f15fbe183ddb4b6c7f3`, artifact `10640780655`

---

# Wave 3 — Semantic Documentation Governance

**Goal:** add authority, relation, change-scope, and source-of-truth semantics.

### DG-P7 — Authority claims + duplicate-authority detection

- **Complexity:** 3
- **Status:** **COMPLETED / PASS / FORMALLY CLOSED**
- **HARD dependencies:** DG-P4, DG-P6; roadmap Wave-3 admission dependency DG-W2 is formally closed.
- **Frozen specification:** `docs/DG_P7_AUTHORITY_CLAIMS_SPEC.md`, commit `f226eb8e01b2284381ba0e7cf5527518512c7ce7`, blob `63d2252314e753b7485f1a0249dc011468be275b`.
- **Document QA:** `docs/DOCUMENT_QA_DG_P7_PREIMPLEMENTATION.md` — PASS.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §9.
- **Reuse verdict:** Artifact/Revision own document identity + exact grant provenance; PRIM-AUTHORITY governs actor permission only; Evidence/P5 records collision QA; Proposal/Approval/Audit govern claim mutation and composition contract.
- **Persistence decision:** exactly one bounded new table `document_authority_claims`; no authority Artifact, composition table or duplicate-authority table.
- **Pre-implementation checklist:**
  - [x] multiple non-conflicting claims represented by semantic contract;
  - [x] duplicate active authority semantics frozen;
  - [x] informative summary cannot acquire implicit authority;
  - [x] composition policy is explicit and exact through approved frozen Proposal payload;
  - [x] `DUPLICATE_AUTHORITY` reuses P5 and remains non-waivable;
  - [x] P6 BLOCKED integration preserved;
  - [x] transactional collision invariant frozen;
  - [x] D7-F1..D7-F20 frozen;
  - [x] QA PASS.
- **Implementation evidence:** HEAD `3f993ac639c8cb3147d0dc8d888c8b5266e54914`; workflow `35610704812` PASS; SQLite artifact `10644396006`; PostgreSQL artifact `10644450806`.
- **Implementation acceptance:**
  - [x] bounded migration adds `document_authority_claims` only;
  - [x] actor authority policies remain semantically unchanged;
  - [x] grant/retire service uses Proposal/Approval/Audit + optimistic claim version;
  - [x] PRIMARY/COMPOSED collision adjudication implemented;
  - [x] authority collision QA emits existing P5 `DUPLICATE_AUTHORITY`;
  - [x] no-collision scan does not emit synthetic PASS QA;
  - [x] D7-F1..D7-F20 PASS on SQLite;
  - [x] D7-F1..D7-F20 PASS on PostgreSQL 17;
  - [x] P4/P5/P6 and governance regressions PASS;
  - [x] full repository regression PASS;
  - [x] no DG-P8+ semantics;
  - [x] implementation QA PASS;
  - [x] handoff exact-head workflow PASS — run `35611325233` on `30170e2f0b94f0cde6994c5b9b3ee7c920379688`; SQLite artifact `10643909615`; PostgreSQL artifact `10643409931`.

### DG-P8 — Typed document relations

- **Complexity:** 3
- **Status:** **COMPLETED / PASS / FORMALLY CLOSED**
- **HARD dependencies:** DG-P4; roadmap Wave-3 dependency DG-P7 is formally closed.
- **Frozen specification:** `docs/DG_P8_TYPED_DOCUMENT_RELATIONS_SPEC.md`, commit `211308141106481104590b3d55cdc8c19d6b6d8e`, blob `d6996951522caa061b29f94d1b1f4f579251adaa`.
- **Document QA:** `docs/DOCUMENT_QA_DG_P8_PREIMPLEMENTATION.md` — PASS.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §10.
- **Reuse verdict:** `document_relations` is canonical semantic state; existing `trace_links` remains revision-level operational/provenance state and may only be a later qualified projection substrate.
- **Persistence decision:** exactly one bounded new table `document_relations`; no node/type/event/projection table.
- **Pre-implementation checklist:**
  - [x] relation direction explicit;
  - [x] required relation types represented;
  - [x] relation semantics not inferred from Markdown links or TraceLinks;
  - [x] integration with existing `trace_links` evaluated before new graph storage;
  - [x] logical-document source lifetime separated from source Revision provenance;
  - [x] ACTIVE/RETIRED relation lifecycle frozen;
  - [x] P8/P9 binding boundary frozen;
  - [x] no TraceLink projection authorized in P8;
  - [x] SUPERSEDES has no P7/lifecycle side effect in P8;
  - [x] D8-F1..D8-F20 frozen;
  - [x] QA PASS.
- **Implementation evidence:** HEAD `e784d7f56c0cfdf25ca453da48d570cd202ad0cc`; workflow `35621561857` PASS; SQLite artifact `10649881388`; PostgreSQL artifact `10649322400`.
- **Implementation acceptance:**
  - [x] bounded migration adds `document_relations` only;
  - [x] relation service uses Proposal/Approval/Audit + optimistic versioning;
  - [x] required relation types/target kinds enforced;
  - [x] no Markdown/TraceLink inference;
  - [x] no target binding mode/revision/hash semantics;
  - [x] no TraceLink projection;
  - [x] D8-F1..D8-F20 PASS on SQLite and PostgreSQL 17;
  - [x] P4/P5/P6/P7 + Knowledge/Trace regressions PASS;
  - [x] full repository regression PASS;
  - [x] no DG-P9+ semantics;
  - [x] implementation QA PASS;
  - [x] handoff exact-head workflow PASS — run `35622268576` on `11eba1b424896b421fc4a32c8a1970dfcf6c34dc`; SQLite artifact `10650102588`; PostgreSQL artifact `10650297246`.

### DG-P9 — Logical-current vs pinned-revision binding

- **Complexity:** 3
- **Status:** **IMPLEMENTATION QUALIFIED / HANDOFF + EXACT-HEAD QA PENDING**
- **HARD dependencies:** DG-P8 — formally closed at final HEAD `4a93e564adf52ae0dfdffabefaef32d431bbef6d`.
- **Frozen specification:** `docs/DG_P9_RELATION_TARGET_BINDING_SPEC.md`, commit `1a9f8737e36392c8a8db49b93c9371ceee16085f`, blob `73e1d7c8c01ea954af2a65e1df1942b4f95738f3`.
- **Document QA:** `docs/DOCUMENT_QA_DG_P9_PREIMPLEMENTATION.md` — PASS.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §10.
- **Persistence verdict:** migration `0011_v086_dg_p9_relation_binding` extends `document_relations` only with `target_binding_mode` and `target_revision_or_hash`; no new P9 table.
- **Legality verdict:** MUST_ALIGN_WITH current-only; SUPERSEDES/DERIVED_FROM/VALIDATES/GENERATED_FROM pinned-only; DEPENDS_ON/REFERENCES/IMPLEMENTS dual-mode.
- **Pre-implementation checklist:**
  - [x] `LOGICAL_CURRENT` and `PINNED_REVISION` distinct;
  - [x] `VALIDATES` cannot float;
  - [x] `GENERATED_FROM` exact identity preserved;
  - [x] legacy P8 rows are not auto-backfilled;
  - [x] one-time governed binding + no-rebind frozen;
  - [x] DOCUMENT native current/pinned resolution frozen;
  - [x] external targets fail closed absent qualified resolver;
  - [x] no TraceLink projection;
  - [x] no impact/validity/Evidence side effect;
  - [x] D9-F1..D9-F20 frozen;
  - [x] QA PASS.
- **Implementation evidence:** HEAD `9ffd64a1e9b98ea307ed8f9682b88e26570dc208`; workflow `35628998000` PASS; SQLite artifact `10653386409`; PostgreSQL artifact `10653461137`.
- **Implementation acceptance:**
  - [x] bounded migration extends `document_relations` only;
  - [x] no new P9 table;
  - [x] legacy NULL binding preserved without default;
  - [x] BIND_DOCUMENT_RELATION uses Proposal/Approval/Audit + optimistic versioning;
  - [x] new relation creation requires legal explicit binding;
  - [x] relation legality matrix enforced;
  - [x] native DOCUMENT resolver returns exact snapshot;
  - [x] external unsupported resolver fails closed;
  - [x] resolver is side-effect free;
  - [x] no TraceLink projection;
  - [x] D9-F1..D9-F20 PASS on SQLite and PostgreSQL 17;
  - [x] P8/Knowledge/Trace regressions PASS;
  - [x] full repository regression PASS;
  - [x] compile PASS;
  - [x] no DG-P10+ semantics;
  - [x] implementation QA PASS;
  - [ ] handoff exact-head workflow PASS.

### DG-P10 — Change classification

- **Complexity:** 3
- **HARD dependencies:** DG-P4, DG-P7.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§13–14.
- **Acceptance checklist:**
  - [ ] EDITORIAL / CLARIFICATION / NORMATIVE / STRUCTURAL / SUPERSESSION represented;
  - [ ] QA can escalate classification;
  - [ ] ambiguous clarification vs normative fails conservatively;
  - [ ] agent cannot downgrade escalated class;
  - [ ] QA PASS.

### DG-P11 — DocumentChangeSet

- **Complexity:** 3
- **HARD dependencies:** DG-P7, DG-P8, DG-P10.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§8.4, 15.
- **Acceptance checklist:**
  - [ ] base revisions frozen;
  - [ ] target docs and allowed paths frozen;
  - [ ] per-document + effective change class stored;
  - [ ] dependency/impact snapshot attributable;
  - [ ] scope violation fails closed;
  - [ ] proposal/approval primitives reused where possible;
  - [ ] QA PASS.

### Wave 3 exit gate — DG-W3

- [ ] DG-P7…DG-P11 PASS
- [ ] duplicate authority fixture FAILS correctly
- [ ] exact-revision validation fixture works
- [ ] normative change cannot masquerade as editorial
- [ ] change scope is frozen before mutation

---

# Wave 4 — Dependency and Drift Core

**Goal:** implement the central “propagate invalidity, not silent edits” semantics.

### DG-P12 — Relation-aware impact traversal

- **Complexity:** 4
- **HARD dependencies:** DG-P8, DG-P9, DG-P11.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§10, 27–28.
- **Acceptance checklist:**
  - [ ] deterministic impact report;
  - [ ] relation-specific invalidation;
  - [ ] bounded/reconstructable traversal;
  - [ ] cycles handled according to relation policy;
  - [ ] existing `KnowledgeKernel.compute_impact` reused/extended where valid;
  - [ ] QA PASS.

### DG-P13 — STALE/review/BLOCK propagation

- **Complexity:** 4
- **HARD dependencies:** DG-P6, DG-P12.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§12, 16, 28.
- **Acceptance checklist:**
  - [ ] upstream material change marks obligations without editing content;
  - [ ] reason/path retained;
  - [ ] idempotent repeated evaluation;
  - [ ] return to VALID requires current-revision QA;
  - [ ] QA PASS.

### DG-P14 — No-silent-cascade enforcement

- **Complexity:** 4
- **HARD dependencies:** DG-P11, DG-P13.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§15–16.
- **Acceptance checklist:**
  - [ ] downstream edits require explicit change set;
  - [ ] auto-suggestion remains proposal only;
  - [ ] hidden recursive repair blocked;
  - [ ] original invalidation event preserved;
  - [ ] QA PASS.

### DG-P15 — Append-only + supersession

- **Complexity:** 4
- **HARD dependencies:** DG-P7, DG-P10, DG-P11.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§11, 14.
- **Acceptance checklist:**
  - [ ] APPEND_ONLY violation detected;
  - [ ] correction represented as appended amendment;
  - [ ] SUPERSEDES retires authority without erasing history;
  - [ ] unresolved inbound dependency blocks unsafe deletion;
  - [ ] QA PASS.

### DG-P16 — Generated-document provenance

- **Complexity:** 3
- **HARD dependencies:** DG-P9, DG-P13.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §25.
- **Acceptance checklist:**
  - [ ] generator/config/input/output identities captured;
  - [ ] changed input makes prior generation stale where policy requires;
  - [ ] generated doc does not become normative silently;
  - [ ] QA PASS.

### Wave 4 exit gate — DG-W4

- [ ] DG-P12…DG-P16 PASS
- [ ] A→B/C fixture demonstrates STALE/review propagation without B/C mutation
- [ ] append-only and supersession fixtures PASS
- [ ] no silent cascade path exists

---

# Wave 5 — Repository Enforcement, Catalog Foundation, and Implementation Alignment

**Goal:** finish the Documentation Governance integration surface and establish the minimum governed cross-project Shared Library substrate before research workflow integration.

### DG-P17 — GitHub QA enforcement integration

- **Complexity:** 3
- **HARD dependencies:** DG-W4.
- **EXTERNAL dependency:** GitHub CODEOWNERS/Rulesets/current API revalidation.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§19–20, 30.
- **Acceptance checklist:**
  - [ ] GWF QA result consumable by repository checks;
  - [ ] merge enforcement does not become source of semantic truth;
  - [ ] exact SHA verification retained;
  - [ ] no secret in static/public surfaces;
  - [ ] QA PASS.

### GAC-P0 — Contract qualification

- **Complexity:** 3
- **HARD dependencies:** DG-W4.
- **Governing documents:**
  - `docs/GOVERNED_ARTIFACT_CATALOG_SPEC.md` §§3–8, 14.
  - `docs/GOVERNED_ARTIFACT_CATALOG_INTEGRATION_BOUNDARIES.md`.
- **Acceptance checklist:**
  - [ ] CatalogEntry / PublicationPolicy / CatalogQuery contracts qualified;
  - [ ] exact subject identity and access fixtures;
  - [ ] no second KnowledgeKernel/document registry;
  - [ ] zero FTS/vector/search-backend requirement;
  - [ ] query failure cannot masquerade as empty results;
  - [ ] QA PASS.

### GAC-P1 — Metadata catalog over existing KnowledgeKernel

- **Complexity:** 3
- **HARD dependencies:** GAC-P0, DG-W4.
- **Governing document:** `docs/GOVERNED_ARTIFACT_CATALOG_SPEC.md` §§4–10, 14.
- **Acceptance checklist:**
  - [ ] publish/withdraw exact GWF revisions;
  - [ ] tenant/workspace/project authorization;
  - [ ] deterministic metadata query;
  - [ ] publication identity/idempotency;
  - [ ] audit/provenance;
  - [ ] no FTS/vector requirement;
  - [ ] QA PASS.

### GAC-P2A — ObjectRef subjects

- **Complexity:** 3
- **HARD dependencies:** GAC-P1.
- **Governing document:** `docs/GOVERNED_ARTIFACT_CATALOG_SPEC.md` §§4.2, 8, 14.
- **Acceptance checklist:**
  - [ ] exact ObjectRef identity retained;
  - [ ] no blob duplication;
  - [ ] access intersection enforced;
  - [ ] no Reference Acquisition dependency introduced;
  - [ ] QA PASS.

### GAC-P4A — Generic cross-project pilot

- **Complexity:** 4
- **HARD dependencies:** GAC-P1, DG-W4.
- **Governing documents:**
  - `docs/GOVERNED_ARTIFACT_CATALOG_SPEC.md` §14.
  - `docs/GOVERNED_ARTIFACT_CATALOG_INTEGRATION_BOUNDARIES.md`.
- **Acceptance checklist:**
  - [ ] multiple projects in one workspace/tenant;
  - [ ] publish/query/withdraw/supersede exact entries;
  - [ ] document eligibility integration fixture;
  - [ ] catalog visibility cannot broaden source permission;
  - [ ] no G2E semantic dependency;
  - [ ] QA PASS.

### DG-P18 — Code/schema/API/workflow/dataset bindings

- **Complexity:** 4
- **HARD dependencies:** DG-P8, DG-P9, DG-P13.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §§22, 24.
- **Acceptance checklist:**
  - [ ] target kind + identity/hash stored;
  - [ ] target change creates review obligation;
  - [ ] change does not prove doc wrong automatically;
  - [ ] no auto-rewrite;
  - [ ] QA PASS.

### DG-P20 — Existing-document migration pilot

- **Complexity:** 4
- **HARD dependencies:** DG-W4, DG-P7, DG-P17.
- **Governing document:** `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §33.
- **Acceptance checklist:**
  - [ ] candidate docs discovered without auto-authority assignment;
  - [ ] metadata inference labeled inferred;
  - [ ] collision audit before activation;
  - [ ] Git provenance preserved;
  - [ ] bounded pilot only;
  - [ ] QA PASS.

### DG-P19 — Research study-lock integration

- **Complexity:** 5
- **HARD dependencies:** DG-P10, DG-P11, DG-P14.
- **ORDERING dependency:** DG-P18 preferred first for simpler cross-artifact binding evidence.
- **Governing documents:**
  - `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` §23.
  - `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md` §8.
  - current research domain/study-lock contracts.
- **Acceptance checklist:**
  - [ ] scientific semantic edit cannot bypass study lock;
  - [ ] post-lock clarification that changes operational meaning escalates;
  - [ ] post-outcome edits preserve original preregistration;
  - [ ] stricter research authority wins;
  - [ ] QA PASS.

### Wave 5 exit gate — DG-GAC-W5

- [ ] DG-P17…DG-P20 PASS
- [ ] GAC-P0 PASS
- [ ] GAC-P1 PASS
- [ ] GAC-P2A PASS
- [ ] GAC-P4A PASS
- [ ] deterministic cross-project Shared Library metadata query works without optional search backend
- [ ] repository enforcement consumes GWF evidence
- [ ] code↔docs change creates review obligation
- [ ] research-lock bypass fixture fails
- [ ] bounded migration pilot produces no silent authority assignment

---

# Wave 6 — Reference Acquisition + Governed Shared Library Bridge

**Goal:** add governed research-reference acquisition and make the GWF Shared Library an internal reproducible discovery channel without turning catalog results into automatic evidence admission.

### RA-P0 — Query plan + retrieval log

- **Complexity:** 3
- **HARD dependencies:** DG-W3; DG-P5 exact QA/finding semantics.
- **ORDERING dependency:** DG-GAC-W5.
- **Governing document:** `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md` §§4.5, 6.1–6.2, 8–10.
- **Checklist:**
  - [ ] plan revision;
  - [ ] acquisition mode;
  - [ ] external source classes + internal source channels;
  - [ ] exact executed queries;
  - [ ] append-only retrieval events;
  - [ ] amendment provenance;
  - [ ] QA PASS.

### RA-P1 — Reference Registry

- **Complexity:** 3
- **HARD dependencies:** RA-P0, DG-P4, DG-P9.
- **Governing document:** `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md` §6.3.
- **Checklist:**
  - [ ] canonical vs inspected identity separated;
  - [ ] dispositions preserved;
  - [ ] multi-query observations linked;
  - [ ] GAC origin/catalog subject refs representable;
  - [ ] exact Git commit for retained repositories;
  - [ ] QA PASS.

### RA-P1C — Governed Catalog discovery bridge

- **Complexity:** 3
- **HARD dependencies:** RA-P0, RA-P1, GAC-P1.
- **Governing documents:**
  - `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md` §§4.5, 6, 9–10.
  - `docs/GOVERNED_ARTIFACT_CATALOG_SPEC.md` §§5.5, 7–10.
- **Acceptance checklist:**
  - [ ] CatalogQueryExecution identity captured;
  - [ ] authoritative catalog snapshot captured;
  - [ ] exact CatalogEntry candidates captured;
  - [ ] partial/backend failure is not encoded as zero matches;
  - [ ] selected candidates normalize into the research reference registry;
  - [ ] catalog result remains candidate discovery, not evidence admission;
  - [ ] QA PASS.

### GAC-P2B — External immutable-reference bridge

- **Complexity:** 3
- **HARD dependencies:** GAC-P1, RA-P1.
- **Governing documents:**
  - `docs/GOVERNED_ARTIFACT_CATALOG_SPEC.md` §§4.4, 8, 14.
  - `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md` §§6.2–6.3.
- **Acceptance checklist:**
  - [ ] external subject uses verified digest or accepted immutable provider identity;
  - [ ] Reference Acquisition provenance is referenced, not duplicated;
  - [ ] mutable URL alone fails eligibility;
  - [ ] QA PASS.

### RA-P2 — GitHub/source-code acquisition adapter

- **Complexity:** 3
- **HARD dependencies:** RA-P1.
- **Governing documents:**
  - `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md` §§4.2, 7, 13.
  - existing GWF GitHub plugin/SHA QA contracts.
- **Checklist:**
  - [ ] read-only acquisition path;
  - [ ] exact commit/relevant paths;
  - [ ] paper-code relationship remains separate;
  - [ ] no arbitrary code execution;
  - [ ] QA PASS.

### RA-P3 — Paper/reference search adapters

- **Complexity:** 3
- **HARD dependencies:** RA-P0, RA-P1.
- **EXTERNAL dependencies:** provider/index interfaces revalidated before implementation.
- **Governing document:** `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md` §§4.1, 6, 9.
- **Checklist:**
  - [ ] provider identity attributable;
  - [ ] canonical/version identity where available;
  - [ ] unavailable provider represented explicitly;
  - [ ] no secret persistence;
  - [ ] QA PASS.

### RA-P4 — Identity dedup + evidence map

- **Complexity:** 4
- **HARD dependencies:** RA-P1, DG-P8, DG-P9.
- **Governing document:** `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md` §§6.4, 7.
- **Checklist:**
  - [ ] relation direction fixed;
  - [ ] external and GAC-discovered identities deduplicate deterministically where they refer to the same exact source;
  - [ ] explicit vs inferred assertion basis;
  - [ ] duplicate identity handling deterministic;
  - [ ] QA PASS.

### RA-P5 — Coverage/temporal/novelty handoff gates

- **Complexity:** 4
- **HARD dependencies:** RA-P0…RA-P4, RA-P1C, DG-P19.
- **Governing document:** `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md` §§8, 10–14.
- **Checklist:**
  - [ ] REQUIRED vs OPTIONAL external classes/internal channels;
  - [ ] PRE_LOCK / LOCKED_PRE_OUTCOME / POST_OUTCOME enforced;
  - [ ] required source/channel outage cannot silently PASS;
  - [ ] novelty collision behavior mode-specific;
  - [ ] governed handoff to prior art/novelty;
  - [ ] QA PASS.

### RA-P6 — Research workflow integration

- **Complexity:** 4
- **HARD dependencies:** RA-P5.
- **Governing documents:**
  - `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md`.
  - current `domains/research.workflow.yaml`.
  - current `research_orchestrator.py` contracts.
- **Checklist:**
  - [ ] explicit decision on phase insertion vs split;
  - [ ] governed Shared Library query appears in the research flow without bypassing reference curation;
  - [ ] fixed-phase assumptions migrated intentionally;
  - [ ] historical studies not silently backfilled;
  - [ ] regression suite PASS;
  - [ ] v0.8.6 gate PASS.

### Conditional non-blocking GAC items

#### GAC-P3 — Optional search adapters

- **Complexity:** 4
- **HARD dependencies:** GAC-P1.
- **Status:** triggered only when deterministic metadata query is insufficient.
- **Not required for:** DG-GAC-W5, RA-GAC-W6, or minimum Shared Library readiness.

#### GAC-P4B — G2E consumer fixture

- **Complexity:** 3
- **HARD dependencies:** GAC-P1.
- **EXTERNAL/trigger dependency:** frozen G2E Evidence Library Adapter/semantic contract.
- **Status:** consumer-integration qualification; not a prerequisite for GAC core readiness or Reference Acquisition.

### Wave 6 exit gate — RA-GAC-W6

- [ ] RA-P0…RA-P6 PASS
- [ ] RA-P1C PASS
- [ ] GAC-P2B PASS
- [ ] reference chain reconstructable end-to-end
- [ ] Shared Library query provenance reconstructable end-to-end
- [ ] exact paper/repo/catalog subject identities retained
- [ ] temporal integrity demonstrated
- [ ] research-domain regression PASS
- [ ] GAC-P3/GAC-P4B absence does not block this gate

---

# Wave 7 — Agent Interoperability v0.8.7

**Goal:** connect GWF to external agent harnesses and Agent Pool transports without moving governance authority outside GWF.

### AI-P0 — AgentExecutionEnvelope + trace identity

- **Complexity:** 3
- **HARD dependencies:** existing GWF execution/audit primitives.
- **ORDERING dependency:** RA-GAC-W6; sequencing choice, not an architectural requirement.
- **Governing document:** `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` §§5, 14–18.
- **Checklist:**
  - [ ] executor status distinct from GWF gate PASS;
  - [ ] external trace/session IDs are foreign identities;
  - [ ] exact input/role/binding/evidence identity captured;
  - [ ] no secret persistence;
  - [ ] QA PASS.

### AI-P1 — MCP read-only surface

- **Complexity:** 3
- **HARD dependencies:** AI-P0.
- **Governing document:** `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` §§12–13.
- **Checklist:**
  - [ ] project/workunit/artifact/evidence read-only operations;
  - [ ] no unrestricted mutation;
  - [ ] authority checks preserved;
  - [ ] QA PASS.

### AI-P2 — Codex harness adapter

- **Complexity:** 4
- **HARD dependencies:** AI-P0.
- **ORDERING dependency:** AI-P1 preferred because ChatGPT/operator-facing path is planned first.
- **Governing document:** `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` §§2.1, 6, 19.
- **Checklist:**
  - [ ] native harness/session value preserved;
  - [ ] session/workspace/tools attributable;
  - [ ] result normalized to execution envelope;
  - [ ] harness cannot self-complete GWF node;
  - [ ] QA PASS.

### AI-P3 — Governed MCP mutation surface

- **Complexity:** 4
- **HARD dependencies:** AI-P1, AI-P0.
- **Governing document:** `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` §13.
- **Checklist:**
  - [ ] mutation maps to native GWF governed command;
  - [ ] same authority/idempotency/audit/verification;
  - [ ] no force-pass/force-merge/lineage deletion;
  - [ ] QA PASS.

### AI-P4 — Claude harness adapter

- **Complexity:** 4
- **HARD dependencies:** AI-P0.
- **ORDERING dependency:** AI-P2.
- **Governing document:** `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` §§6, 19.
- **Checklist:** same harness invariants as AI-P2; QA PASS.

### AI-P5 — Gemini harness adapter

- **Complexity:** 4
- **HARD dependencies:** AI-P0.
- **ORDERING dependency:** AI-P4.
- **Governing document:** `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` §§6, 19.
- **Checklist:** same harness invariants as AI-P2; QA PASS.

### AI-P6 — Agent Pool resource model

- **Complexity:** 4
- **HARD dependencies:** AI-P0.
- **Governing document:** `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` §§2.2, 5, 7.
- **Checklist:**
  - [ ] Agent Pool is resource class, not transport;
  - [ ] workers may be primary executors;
  - [ ] provider/transport/resource class separate;
  - [ ] capabilities vs execution constraints separate;
  - [ ] QA PASS.

### AI-P7 — ARC transport adapter

- **Complexity:** 4
- **HARD dependencies:** AI-P6, AI-P0.
- **EXTERNAL dependency:** ARC protocol/runtime capability revalidated at implementation time.
- **Governing document:** `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md` §§7, 12, 15.
- **Checklist:**
  - [ ] ARC is transport, not model provider;
  - [ ] trace/task identity preserved;
  - [ ] substitution never silent;
  - [ ] result normalized to execution envelope;
  - [ ] QA PASS.

### Wave 7 exit gate — AI-W7

- [ ] AI-P0…AI-P7 PASS
- [ ] GWF remains authoritative across all execution paths
- [ ] harness and Agent Pool semantics remain distinct
- [ ] MCP mutation parity proven
- [ ] ARC transport proven without fallback-only semantics

---

# 5. Explicit parking lot after Wave 7

The following are **not active implementation items** in this 7-wave plan:

- node-level role→capability→agent binding;
- delegated senior/junior runtime;
- automatic routing;
- scheduler;
- cost optimizer;
- provider health ranking;
- visual node editor;
- model equivalence automation;
- direct agent access to a search backend that bypasses GAC publication/query authority.

**Governing document:** `docs/FUTURE_NODE_AGENT_ORCHESTRATION_PARKING_LOT.md`.

Revisit only when one of its explicit triggers occurs.

# 6. Cross-wave dependency summary

```text
PLAN-QA
  ↓
DG-P0  [COMPLETED]
  ├──→ DG-P1
  ├──→ DG-P2
  └──→ DG-P3
          ↓
        DG-P4
          ↓
        DG-P5
          ↓
        DG-P6
          ↓
     authority/relations/change-set
          ↓
      impact + STALE
          ↓
   no-silent-cascade
          ↓
        DG-W4
          ↓
   ┌──────┴──────────────┐
   │                     │
DG enforcement       GAC-P0 → GAC-P1 → GAC-P2A
   │                     │
   └──────────┬──────────┘
              ↓
          DG-GAC-W5
              ↓
  Reference Acquisition
      + GAC query bridge
      + GAC-P2B external refs
              ↓
          RA-GAC-W6
              ↓ [ORDERING]
 Agent Interoperability v0.8.7
```

GAC-P3 optional search adapters and GAC-P4B G2E consumer qualification are trigger-based and non-blocking for the minimum Shared Library / Reference Acquisition gates.

Hard dependency detail remains authoritative in each item above; this diagram is only a summary.

# 7. Handoff checklist for every item

Every item completion package must include:

- [ ] item ID and wave;
- [ ] exact implementation commit SHA;
- [ ] exact parent SHA;
- [ ] exact governing document blob/revision identities;
- [ ] exact catalog/publication/query policy identities when GAC is involved;
- [ ] HARD dependencies and their PASS evidence;
- [ ] external dependency version/config evidence where applicable;
- [ ] files changed;
- [ ] schema/migration changes, or explicit `NONE`;
- [ ] normative behavior changes, or explicit `NONE`;
- [ ] tests added/changed;
- [ ] exact test command or CI workflow;
- [ ] QA result;
- [ ] known limitations;
- [ ] open findings;
- [ ] security/privacy impact;
- [ ] rollback/recovery note;
- [ ] explicit non-scope;
- [ ] next allowed item(s).

No item may be marked complete with unresolved required handoff fields.

# 8. Global implementation invariants

- [ ] lower complexity is preferred only after HARD dependencies are satisfied;
- [ ] failed QA does not auto-trigger redesign;
- [ ] external tool outage is not converted into document failure;
- [ ] GAC backend/index failure is not converted into a valid empty Library result;
- [ ] catalog discovery never becomes automatic research evidence admission;
- [ ] cross-project governed discovery does not bypass GAC authority/access checks;
- [ ] no external validator receives governance authority;
- [ ] no silent document cascade repair;
- [ ] no silent executor substitution;
- [ ] no raw reusable secrets persisted;
- [ ] exact revision/SHA evidence is preserved;
- [ ] research-lock semantics cannot be relaxed by documentation tooling;
- [ ] current failed/negative evidence is not erased by rerun;
- [ ] every wave exit gate must PASS before an ORDERING-dependent later wave is promoted to active work.

# 9. Current authorization frontier

At this implementation state:

```text
DG-P5 — QA run + finding persistence
      PASS / FORMALLY CLOSED
      final closure HEAD 58a4cf5f0ca33ca8e15513eb07234dc575b097bc
      final exact-head run 35585295768 PASS
       ↓
DG-P6 — Lifecycle + validity mapping
      PASS / FORMALLY CLOSED
      handoff HEAD d25454481f0d972c83225e10d3d09b1bb997faf9
      exact-head run 35598699495 PASS
       ↓
DG-W2 — Wave 2 exit gate
      PASS / FORMALLY CLOSED
      handoff HEAD be02cdd7eaeadc0534631f15fbe183ddb4b6c7f3
      exact-head run 35603196674 PASS
       ↓
Wave 3 — Semantic Documentation Governance
      DEPENDENCY UNLOCKED
       ↓
DG-P7 — Authority claims + duplicate-authority detection
      PASS / FORMALLY CLOSED
      final closure HEAD cf143d959b338e8d77811f5b2b79789ccbbb20aa
      final exact-head run 35611830804 PASS
       ↓
DG-P8 — Typed document relations
      PASS / FORMALLY CLOSED
      final closure HEAD 4a93e564adf52ae0dfdffabefaef32d431bbef6d
      final exact-head run 35622798852 PASS
       ↓
DG-P9 — Logical-current vs pinned-revision binding
      IMPLEMENTATION QUALIFIED
      HEAD 9ffd64a1e9b98ea307ed8f9682b88e26570dc208
      workflow 35628998000 PASS
      HANDOFF EXACT-HEAD QA PENDING
       ↓
STOP

DG-P10+ = NOT_STARTED / NOT_AUTHORIZED
```

DG-P8 is formally closed at final exact closure evidence, and the explicitly authorized DG-P9 pre-implementation qualification has passed.

DG-P9 implementation remains NOT_STARTED and requires a separate explicit bounded implementation authorization. DG-P10+ remain unopened. DG-W3 remains OPEN / NOT_EXECUTED.

GAC implementation remains blocked until **DG-W4 PASS**, as specified in Wave 5.
