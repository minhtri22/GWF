# G2E Framework — Lineage

**Policy:** append-only. Add short phase outcomes only after the phase has an authoritative PASS/FAIL/INVALID/UNRESOLVED result. Do not record transient implementation errors, debugging failures, or ordinary test iterations.

## Entries

### G2E-P0 — Foundation Specification

- **Status:** PASS
- **Specification commit:** `636f2959d4e927a0ccd008877fa36da2a4681524`
- **QA commit:** `4aad03c31611888037544cf1f1d5cb16b758f3f1`
- **Result:** G2E established as an independent Goal-to-Evidence core; GWF is the default execution/governance backend; standalone execution remains required.
- **Agent direction:** Codex/ChatGPT first; Claude/Gemini next; ARC is retained as transport for other model-backed agents.
- **Next:** P1 — Core Schemas.


### G2E-P0.1 — Semantic Specification Hardening

- **Status:** PASS
- **Findings audit:** `2fab50299800e9ac437f92aec796b3b104c46cc1`
- **Remediation:** `ed88ec721342456bbb90006b41e2308bdc043fcd`
- **QA:** `affbcbc8c8441d3d10cae0d47620b19e9e3d262f`
- **Result:** 22 semantic/logic findings resolved; state/verdict namespaces, Goal/Claim closure, retry, evidence admission, freshness, authority, dependency and runtime-parity contracts are now frozen for P1 handoff.
- **Next:** P1 — Core Schemas.


### G2E-P0.2 — Evidence Reuse & Convergence Specification

- **Status:** PASS
- **Candidate:** `ca001f806f9306bbd1ba6a57185879b3ec3ee71a`
- **Findings:** `b3730d095272b2c29f19e5baba7269272b667fec`
- **Remediation:** `eb7eed90ad6a5c5820ff981775aa77aa15c5f7f5`
- **QA:** `6407fb508a7cb57235795f00580ed0c6405f936d`
- **Result:** EvidenceCapsule, ClaimResultPackage, applicability/reuse, provenance-overlap, synthesis/convergence and provider-neutral Evidence Library Adapter semantics are frozen; GWF GAC is the default backend only when implemented/qualified.
- **Next:** P1 — Core Schemas.


### G2E-P0.3 — GWF Shared Library Reconciliation

- **Status:** PASS
- **Findings:** `610e05dd0fa6561df2b60e17e93f921392abc5f2`
- **Main reconciliation:** `550c257b57f31e046080ff7eefbc3c5771906a55`
- **Pinned-reference correction:** `ce490c4609105a17f644d4473a86c27f45ad7ecf`
- **Exact QA-blob correction:** `1c918693814bd0a346842a6a99ce54ebefbbfb84`
- **QA:** `edb11324a0490454f7c56e11e62a93ae0ccad98d`
- **Result:** G2E now matches GWF reconciliation `be7d606c...`: Shared Library ownership, direct-vs-Reference-Acquisition routing, exact GAC/RA readiness gates, same-subject dedup, terminology mapping and conditional P4L integration are frozen without introducing a second catalog/store.
- **Next:** P1 — Core Schemas; GWF-backed Library integration remains conditional P4L.


### G2E-P1 — Core Schemas

- **Status:** PASS
- **Qualified implementation:** `2fc077f8bc84f8dbdb42c180b3edc7af9418a6c1`
- **Authoritative workflow:** `35564563403` / job `106223715948` — PASS
- **Evidence closure:** `edfc8e805d3b061111f3012fdce0891177dcabd8`
- **Result:** 35 authoritative G2E schema models are canonically hashable/versioned and pass fail-closed structural qualification; 21/21 P1 tests and compile gate pass. No executor, standalone runtime, GWF adapter or GAC/P4L implementation was opened.
- **Next:** P2 — Deterministic Core Engine.


### G2E-P1.1 — Frozen Decision Rule Binding

- **Status:** PASS
- **Finding:** `P2-F01`
- **Qualified schema:** `0002790f0ea3da1c6e03b69124e3bfd38741b3b5`
- **Authoritative workflow:** `35572749902` / job `106247706920` — PASS
- **Evidence closure:** `16ae28f5279825b87379e56e7c36d3fa297423c7`
- **Result:** ProofObligation now binds an exact canonical DecisionRule, closing the no-rescue dependency required by deterministic adjudication.
- **Next:** P2 — Deterministic Core Engine.


### G2E-P2 — Deterministic Core Engine

- **Status:** PASS
- **Qualified implementation:** `c2fc03a7470b835904252246421e1b8d9a1ec5ef`
- **Authoritative workflow:** `35573628326` / job `106250444186` — PASS
- **P1 regression:** `35573628248` / job `106250444424` — PASS
- **Evidence closure:** `290164347db6c52043dfa9f863122d145c288293`
- **Result:** Deterministic Claim/Goal validation, proof admissibility, evidence admission, protected-resource freshness, one-shot adjudication, bounded retry, Claim/Goal resolution, Next-Step selection, no-rescue, applicability/reuse, independence clustering and synthesis/convergence mechanics qualified with P1 23/23 + P2 41/41 fixtures; no runtime/DB/agent/GWF/GAC dependency opened.
- **Next:** P3 — Standalone Runtime.


### G2E-P1.2 — Standalone Runtime Prerequisite Schemas

- **Status:** PASS
- **Qualified schema:** `fe02721b436e94fc7cd34a68f136d6088ca4b411`
- **Authoritative qualification:** P1 `35577307904` / job `106261951175` — PASS; P2 regression `35577307899` / job `106261951530` — PASS
- **Evidence closure:** `9165a3afd75b7386370e9eb7642ee0579a3d1a5b`
- **Result:** RuntimeCapabilityManifest, provider-neutral ExecutionResult and canonical PackageManifest/PackageSeal were added and requalified without weakening P1.1/P2 semantics.
- **Next:** P3 prerequisite package-integrity completion.


### G2E-P1.3 — Package External Reference Integrity

- **Status:** PASS
- **Qualified schema:** `931b7d23239f625136be12d26564e9f89f8785b9`
- **Authoritative qualification:** P1 `35577723392` / job `106263241695` — PASS; P2 regression `35577723441` / job `106263242213` — PASS
- **Evidence closure:** `e4ef2f8c62558b540f1babba7e9b5f2dc9bb0497`
- **Result:** PackageManifest now binds exact external-reference inventory and resolution policy required for independently verifiable sealed result packages.
- **Next:** P3 — Standalone Runtime.


### G2E-P3 — Standalone Runtime

- **Status:** PASS
- **Qualified implementation:** `b9345f3cbeba564a0bf666d388d3873d9ffd1191`
- **Authoritative qualification:** P1 `35581467359` / job `106275090078` — PASS; P2 `35581467348` / job `106275090278` — PASS; P3 `35581467424` / job `106275090584` — PASS
- **Evidence closure:** `b7a00ece1673663b2c8fde2331a20b7beb241490`
- **Result:** Standalone SQLite/filesystem runtime, fail-closed restart recovery, protected-resource ledger, local executor facade, independently re-verifiable sealed Goal Result packages and qualified local Evidence Library operations passed 29 P1 + 43 P2 + 25 P3 fixtures. Exact DecisionRule identity remains preserved through restart, adjudication, package export and semantic replay.
- **Next:** P4 — Base GWF Adapter; P4L remains conditional and closed.


### G2E-P3 — Post-Close Integrity Verification

- **Status:** PASS
- **Qualified implementation:** `b9345f3cbeba564a0bf666d388d3873d9ffd1191`
- **Verified workflows:** P1 `35581467359`, P2 `35581467348`, P3 `35581467424` — all PASS on the exact qualified SHA.
- **Result:** 8/8 qualified implementation/test/workflow blobs match P3 qualification evidence; the post-qualification path through evidence closure and lineage contains no `src/`, `tests/` or `.github/` mutation. The earlier DecisionRule debt remains closed through restart, adjudication, package export and independent semantic replay.
- **Next:** P4 — Base GWF Adapter; P4L remains conditional and closed.


### G2E-P4 — Base GWF Adapter

- **Status:** PASS
- **Qualified implementation:** `1f6d49957c0c0dffa7b83c11caebed4ab2b90e0b`
- **Authoritative qualification:** P1 `35584223713` / job `106283704496` — 29/29 PASS; P2 `35584223744` / job `106283704804` — 43/43 PASS (+ P1 29/29); P3 `35584223806` / job `106283705392` — 25/25 PASS (+ P1/P2); P4 `35584223810` / job `106283705280` — 17/17 PASS (+ P1/P2/P3 regressions).
- **Evidence closure:** `fbae7dcf6484556a1acf339f8187f8a2092faef0`
- **Result:** Base GWF mapping preserves canonical G2E exact refs/hashes while keeping GWF IDs, hashes and runtime success states as mappings only; standalone↔GWF parity is qualified through ExecutionAttempt, provider-neutral ExecutionResult, Evidence, P2 Adjudication, protected-resource fail-closed recovery, Claim/Goal resolution and Result Package semantic manifest. Fresh-runtime restart reconstruction and authority/retry/mapping negative fixtures PASS. P1–P3 qualified blobs remain unchanged.
- **Next:** exact P4L capability/dependency audit only; P4L Shared Library integration remains CONDITIONAL/CLOSED until `GWF_LIBRARY_INTEGRATION_MAPPING.md` gates are independently satisfied.


### G2E-P4 — Post-Close Integrity Verification

- **Status:** PASS
- **Qualified implementation:** `1f6d49957c0c0dffa7b83c11caebed4ab2b90e0b`
- **Evidence closure:** `fbae7dcf6484556a1acf339f8187f8a2092faef0`
- **Verified close-through:** `74570fe8074732258285e945322096ac13b0ba10`
- **Result:** Post-qualification compare contains only `g2e/docs/P4_IMPLEMENTATION_RESULT.md`, `g2e/docs/P4_QUALIFICATION_EVIDENCE.json` and append-only `g2e/LINEAGE.md`; post-qualification mutation in `src/`, `tests/` and `.github/` is 0. The qualified P4 implementation therefore remains exactly the implementation exercised by the authoritative exact-SHA workflows.
- **Next:** exact P4L capability/dependency audit only; P4L remains CONDITIONAL/CLOSED.


### G2E-P4L — Capability / Dependency Audit

- **Status:** CLOSED / NOT AUTHORIZED
- **Audit baseline:** `dec4c73ad15e9ee0a5883dee4a35bf6f7621bf89`
- **Audit result:** `5d56c54d505b0173bc6d5152250089ca0a4fac2d`
- **Audit evidence:** `ccdfb43742dfcc7b9de944daa1ed4f9c70d5d613`
- **Result:** Exact GWF capability audit found no qualifying PASS evidence for the mandatory base P4L opening set: DG-W4, GAC-P0, GAC-P1 and GAC-P4B. Latest exact Documentation Governance evidence formally closes DG-P5 and identifies DG-P6 as next while DG-W2 remains open; GAC remains locked until DG-W4 PASS. GAC-P2A/DG-GAC-W5/RA-P1C/RA-GAC-W6/GAC-P3 remain capability-triggered and unqualified; none is silently inferred available.
- **Implementation boundary:** P4L runtime implementation remains prohibited. The audit introduced no `src/`, `tests/` or `.github/` mutation.
- **Next external dependency frontier:** DG-P6 on the independent GWF Documentation Governance line. A future P4L audit must re-resolve exact gate evidence; prior documentation QA cannot substitute for runtime qualification.


### G2E-P5 — Pre-Implementation Qualification

- **Status:** SPEC_PASS_RUNTIME_BLOCKED
- **Qualified candidate:** `a799a6039498dfd4196b9874f230da48fdbb42c1`
- **Authoritative workflow:** `35587111264` / job `106292892218` — PASS
- **Evidence artifact:** `10632522432`
- **Artifact digest:** `sha256:f6d0bc2dafcf3e073e9119a419f41d2ef73e0f03ff7311bca94615cf344fedcd`
- **Evidence closure:** `6283bf4c033828b2915bf3029ed9b3e0ea9d0870`
- **Result:** P5 dependency, separate Codex/ChatGPT discovery, authority/security, prospective independence, fail-closed behavior and outcome-blind P5-FX-001 contracts are frozen. Zero-implementation QA and P1–P4 regressions PASS with no Codex/ChatGPT runtime adapter mutation. Findings P5-F01/P5-F02 confirm that backend RuntimeCapabilityManifest cannot substitute for app capability identity and that exact canonical AgentBinding identity is still missing.
- **Implementation boundary:** P5A/P5B runtime adapters remain NOT AUTHORIZED. Neither Codex nor ChatGPT is declared available until actual-harness discovery/qualification.
- **Next:** P1.4 — Agent Profile / Binding Identity, schema-only prerequisite; requalify P1–P4 before opening P5A.


### G2E-P1.4 — Agent Profile / Binding Identity

- **Status:** PASS
- **Pre-implementation qualification:** `995ca7a87e2acc3bdb7980046509b0061de48a4e`; workflow `35590024177` / job `106302073904` — PASS; artifact `10633823851`.
- **Qualified implementation:** `d3cb0bdb5644a9f1cff382450b5476e166759d72`
- **Exact qualification workflows:** P1 `35590544907` / job `106303688907` PASS; P2 `35590544803` / job `106303689038` PASS; P3 `35590544876` / job `106303688896` PASS; P4 `35590544868` / job `106303689021` PASS; P1.4 `35590544831` / job `106303688970` PASS.
- **P1.4 evidence artifact:** `10634082369`; digest `sha256:7d28b488f937dc1f5d6afb3a6159688c76b9f1dd8c40f72de54f00455e551d22`.
- **Evidence closure:** `233ab9442338e7ed0d4a53f70dc87ab803165711`
- **Result:** Canonical AgentCapabilityManifest, AgentEquivalencePolicy and AgentBinding identities are now qualified; ExecutionAttemptEnvelope/ExecutionResult carry exact binding refs; deterministic relation validation fails closed on capability, identity, attempt, authority and result mismatch; standalone and GWF propagate binding identity without acquiring scientific authority. P5-F01/P5-F02 are closed.
- **Implementation boundary:** provider-neutral schema/propagation only. No Codex/ChatGPT driver, provider API, MCP/ARC runtime, profile discovery runtime, P4L/GAC or Reference Acquisition implementation was opened.
- **Next:** P5A Codex actual-harness capability discovery/profile qualification preparation. ChatGPT remains a separate independently discoverable P5B profile.


### G2E-P5A — Codex Discovery Preparation

- **Status:** PREPARATION_PASS_ACTUAL_HARNESS_PENDING
- **Qualified candidate:** `d53ef2d246b099a1f0c654906b1ca35ab61ad9a3`
- **Authoritative workflow:** `35591574804` / job `106306922854` — PASS
- **Evidence artifact:** `10634153745`; digest `sha256:ba379edcd7e60ba50641bdc8cd6a4405dcdb326758482cf9164dce485c5518f7`
- **Evidence closure:** `8a1866f798ac44f7434404f64d4a5cead9e65a2c`
- **Result:** P5A now has a qualified read-only discovery instrument for exact Codex harness evidence. D0 official documentation/source is explicitly separated from D1 actual-harness structural evidence and D2 bounded functional qualification. The probe captures exact executable/version/schema fingerprints plus app-server initialize handshake without model turn, ProofObligation dispatch, repository mutation, credentials or side effects. P1/P1.4/P2/P3/P4 regressions PASS.
- **Implementation boundary:** Codex profile remains unavailable until D1 actual-harness evidence passes. No Codex runtime adapter, ChatGPT runtime, MCP/ARC execution path, or D2 functional task is authorized.
- **Next:** execute the qualified P5A discovery probe on the exact target Codex harness, freeze `P5A_CODEX_DISCOVERY.json`, and adjudicate D1 before constructing the Codex AgentCapabilityManifest.


### G2E-P5A.1 — Codex D1 Adjudication Lock

- **Status:** PASS / ZERO-FRESH
- **Qualified candidate:** `685739bf607ed456ace1bf723a352ab72a5237d3`
- **Authoritative workflow:** `35593990611` / job `106314510193` — PASS
- **Evidence artifact:** `10636246771`; digest `sha256:d844fcd43f3327c24f5ce7eede11df255895215cbeb84f64a485a216c9a9b184`
- **Evidence closure:** `8a2ae060aafec0b4382b76f88812b0ecc8f2b530`
- **Result:** PASS/FAIL/INVALID D1 adjudication semantics are frozen before any target Codex discovery evidence is consumed. The one-shot adjudicator verifies exact discovery schema, executable/version identity, schema-inventory digest, required protocol tokens, initialize handshake and sanitization, and contains no Codex/process/G2E execution path.
- **No-rescue boundary:** after first D1 evidence, required tokens/verdict rules may not be changed, D0 documentation may not substitute for D1, and rerun-until-PASS/version-switch rescue is prohibited.
- **Implementation boundary:** Codex profile is still not AVAILABLE; D2 and Codex runtime adapter remain NOT AUTHORIZED; ChatGPT P5B remains untouched.
- **Next:** one exact target-harness P5A discovery run, freeze `P5A_CODEX_DISCOVERY.json`, then apply the frozen adjudicator once.


### G2E-P5A.1R — Codex D1 Inventory Ordering Invalidity Repair

- **Status:** PASS / BOUNDED INVALIDITY REPAIR
- **Qualified candidate:** `4e447ef19a843aa3dd1337c57a9c70b4c1a00de1`
- **Authoritative workflow:** `35597985704` / job `106327133946` — PASS
- **Evidence artifact:** `10637389197`; digest `sha256:09a599886c44d3d3d2544d6ff61a93205f47c137d8807598caadda97ea6c2130`
- **Evidence closure:** `68cdd2e450da266064f41977b09c73314ce59d82`
- **Original immutable discovery:** SHA-256 `ba098a56be39e996488e5a543af8c373199f8b4cc66f922be6d7bc6386c6e860`; original verdict `INVALID` solely for `INVENTORY_PATHS_NOT_SORTED`.
- **Result:** invalidity mechanism attributed to cross-platform path-order semantics: Windows probe emits deterministic WindowsPath ordering while the parent adjudicator checked case-sensitive string ordering. Repair mirrors the qualified probe host semantics with PureWindowsPath/PurePosixPath while preserving inventory digest, token, handshake, secret, PASS/FAIL/INVALID and authorization rules.
- **No-rescue boundary:** no fresh Codex recollection, version switch, token relaxation, discovery-probe mutation, D2 or runtime-adapter opening is authorized.
- **Next:** pull the qualified repaired adjudicator and re-adjudicate the original discovery JSON exactly once; retain both original INVALID and repaired adjudication.


### G2E-P5A — Codex D1 Actual-Harness Qualification

- **Status:** PASS / STRUCTURAL SURFACE ONLY
- **Original discovery SHA-256:** `ba098a56be39e996488e5a543af8c373199f8b4cc66f922be6d7bc6386c6e860`
- **Original adjudication:** INVALID solely for `INVENTORY_PATHS_NOT_SORTED`
- **Qualified invalidity repair:** `4e447ef19a843aa3dd1337c57a9c70b4c1a00de1`; repaired adjudicator blob `b2ba81801d2bfe7a662acb477fa449e16d13fa55`
- **Repaired adjudication SHA-256:** `04035432c5f290dfd7bbcc91feba8865dc86bfae11686a4e44da2f56cb4ac578`
- **Repaired verdict:** PASS; reason codes empty; initialize handshake PASS; required protocol tokens all true; recomputed schema inventory digest exactly `4da66f2fac241c53ec857bf1a5f0f9586a445e39c4b0c4e7b4bdb0b103aa8376`.
- **Harness identity:** reported version `codex-cli 0.0.0`; executable SHA-256 `a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8`.
- **Result:** Codex is qualified only for the exact D1 structural App Server surface. Functional repository/shell/test/network/approval execution, active-task interruption and completed-task artifact extraction remain unqualified.
- **Authorization boundary:** exact Codex AgentCapabilityManifest materialization is authorized; D2 and Codex runtime adapter remain NOT AUTHORIZED; ChatGPT P5B remains untouched.
- **Next:** materialize and independently qualify one canonical Codex AgentCapabilityManifest from D1-only evidence.


### G2E-P5A.2 — Codex D1 AgentCapabilityManifest

- **Status:** PASS
- **Qualified candidate:** `2385a853ac37e6b8937a830e0441fbec6e6f7501`
- **Authoritative workflow:** `35599808982` / job `106332973410` — PASS
- **Artifact:** `10637903885`; digest `sha256:4502122d331de20a472284f6a96710acab3caf3501d4b0391d623a98e65643a7`
- **Canonical manifest exact ref:** `agent-capability-manifest-codex-d1@a337b7433ebb351c-d1-v1#585d59b32457484e8d4706c3e79a94398569ab4bc3e39ff8fca5502541ece5c5`
- **Manifest file SHA-256:** `0b5ad6c71ee5fa74a1ca917a943a38bd96687d7b5571901daa8a6acb8e927eac`
- **Result:** D1-qualified structural surfaces are materialized in one canonical AgentCapabilityManifest. Repository/shell/test/network/approval execution, interruption, artifact extraction and model-task correctness remain explicitly unavailable; max authority scope remains empty.
- **Exact-SHA regressions:** P1 `35599809068` PASS; P2 `35599809106` PASS; P3 `35599809084` PASS; P4 `35599809011` PASS.
- **Implementation boundary:** no `src/g2e` or `src/gwr` mutation; D2 execution and Codex runtime adapter remain NOT AUTHORIZED; ChatGPT P5B remains untouched.
- **Next:** P5A D2 / P5-FX-001 pre-registration and functional qualification specification only. No model turn before that lock passes.


### G2E-P5A-D2 — P5-FX-001 Pre-Implementation Qualification

- **Status:** SPEC_PASS_EXECUTION_BLOCKED
- **Qualified candidate:** `15eeae4776a969cb0d64b9d55f33146e303161ec`
- **Authoritative workflow:** `35603125876` / job `106343728888` — PASS
- **Evidence artifact:** `10639439364`; digest `sha256:ff7d2ef4592e734767bcb297b51c8b06d7b037d80968beeeb35956bc3d8559ef`
- **Preregistration artifact SHA-256:** `eaeff7a8141697b2ecb824709277ba51db5e60643a722f2d06b3d5d3f6d4d4b4`
- **Exact ProofObligation:** `p5a-d2-p5-fx-001-proof@p5-fx-001-v1#8e275db790fe4c83061385f9988f4165f54d514611a44a4a555c5d01f6d3dbcd`
- **Exact preflight identity binding:** `p5a-d2-preflight-binding@p5-fx-001-v1#a5a9287d464d3d3450e9cf82d7866d45e9e2fc2921b0c28d938fd7257a3940f8`
- **Result:** P5-FX-001 input/task/workspace, zero retry, mutation boundary, approvals, evidence extraction, timeout/cancellation, PASS/FAIL/INVALID and no-rescue rules are frozen before any model turn. P1/P1.4/P2/P3/P4 regressions PASS.
- **Blocking finding D2-F01:** the exact D1 Codex manifest has `max_authority_scope=()` while D2 requires bounded `READ_FROZEN_FIXTURE` + `WRITE_DESIGNATED_OUTPUT`; therefore a final execution AgentBinding cannot be frozen without violating P1.4 authority validation.
- **Implementation boundary:** no D2 outcome/model turn, Codex runtime adapter, core/runtime mutation or ChatGPT P5B work. D2 execution remains NOT AUTHORIZED.
- **Next:** bounded prospective D2 qualification-authority admission prerequisite; distinguish authority to attempt an unqualified capability from evidence that the capability is already available.


### G2E-P5A-D2-QA — Qualification Authority Admission Pre-Implementation

- **Status:** SPEC_PASS_IMPLEMENTATION_REQUIRED
- **Qualified candidate:** `e771faccb8b4370e6720d34f9905c2504846f96f`
- **Authoritative workflow:** `35603911135` / job `106346284252` — PASS
- **Evidence artifact:** `10641056299`; digest `sha256:c3fadfc2a42f75f9d252ec13b48877bc064276b2f52ef08e9167c2f489b9e740`
- **Result:** D2-F01 is resolved at the specification level by separating qualification authority from capability evidence. A future canonical `QualificationAuthorityGrant` is frozen as exact-proof/attempt/manifest/target-capability/AuthorityPolicy bound, single-attempt, non-operational, path-scoped, and incapable of implying capability availability.
- **P1.4 preservation:** normal `required_capability_ids` and manifest authority ceiling semantics remain unchanged. Qualification targets are separate; authority outside the manifest ceiling is admissible only through the exact qualification grant and parent AuthorityPolicy.
- **P5-FX-001 frozen grant scope:** role `qualification_executor`; targets `repository_read`, `repository_write`; authority `READ_FROZEN_FIXTURE`, `WRITE_DESIGNATED_OUTPUT`; reads `input.json`, `TASK.md`; write `result.json`; network/interactive approval false.
- **Implementation boundary:** no core/runtime/script implementation, no final D2 AgentBinding, no model turn, no Codex runtime adapter, no ChatGPT P5B work.
- **Next:** P1.5 — Qualification Attempt Authority, bounded provider-neutral schema/governance implementation followed by P1/P1.4/P2/P3/P4/P1.5 exact-SHA qualification.


### G2E-P1.5 — Qualification Attempt Authority

- **Status:** PASS
- **Qualified candidate:** `6e9c518671c3f9ba140daa798458b37bee83647c`
- **Authoritative workflow:** `35607098718` / job `106356752615` — PASS
- **Evidence artifact:** `10642236550`; digest `sha256:cbc71ccc50363860ee817d434f206d6655f5adb0299a07b116eeb064e6f00a12`
- **Result:** canonical `QualificationAuthorityGrant`, optional qualification fields on AgentBinding, and explicit `validate_qualification_agent_binding_identity` are qualified. Normal P1.4 semantics remain fail-closed and unchanged for operational bindings.
- **D2-F01:** resolved at the schema/governance prerequisite level without marking unavailable capabilities AVAILABLE or widening the D1 manifest authority ceiling.
- **Qualification semantics:** already-qualified prerequisites remain in `required_capability_ids`; unavailable capabilities under test live only in `qualification_target_capability_ids`; exact bounded attempt authority is supplied only by `qualification_authority_ref` under the exact AuthorityPolicy.
- **Implementation boundary:** provider-neutral only; no D2 outcome/model turn, Codex runtime adapter or ChatGPT P5B work.
- **Next:** materialize exact P5-FX-001 AuthorityPolicy + QualificationAuthorityGrant + final D2 AgentBinding + pre-dispatch attempt identity, then run a final zero-fresh admission qualification before any model turn.


### G2E-P5A-D2 — Final Zero-Fresh Admission

- **Status:** FINAL_ADMISSION_PASS
- **Qualified candidate:** `75e10b5a68616c2f48bf1b091a850daa8b0da60d`
- **Authoritative workflow:** `35608071469` / job `106359996540` — PASS
- **Evidence artifact:** `10642813459`; digest `sha256:f2bdebc1f5f272c9465bf9961375bbbd2086b1ab23304a480fa87a95c6ff26f3`
- **Exact AuthorityPolicy:** `p5a-d2-p5-fx-001-authority-policy@p5-fx-001-v1#8bf59660f19437120d2b26169b0bf7dc7670a5e075e0252ac951c8ad0aa20971`
- **Exact QualificationAuthorityGrant:** `p5a-d2-p5-fx-001-qualification-grant@p5-fx-001-v1#656cb4c2e06518ecf7d2da668b03d4f6084ebd2ed2bc03cd3289d3639efdafab`
- **FINAL D2 AgentBinding:** `p5a-d2-final-agent-binding@p5-fx-001-v1#472eb3a0573c093a8b7cb63b1dc320b4292f1c30b6d6dfd493f29014472999e1`
- **Pre-dispatch attempt:** `p5a-d2-predispatch-attempt-envelope@p5-fx-001-v1#34369e7eacd0ad03a3ca4433c2ad0d643de9a1057ed7bcbc1729d10e33511ea3`; attempt ID `p5a-d2-p5-fx-001-attempt-001`; state `LOCKED`.
- **Execution config hash:** `740d5303d29b757e47571bc50b6367770296f7186a5528cef25adbb806669c3a`
- **Result:** the entire prospective P5-FX-001 authority/identity graph materialized deterministically and independently re-verified under P1.5. P1/P1.4/P1.5/P2/P3/P4 regressions PASS; no fresh D2 outcome or model turn existed before the lock.
- **Capability boundary:** `repository_read` and `repository_write` remain unavailable before D2. Grant/binding admission does not mutate the D1 manifest.
- **Authorization boundary:** exactly one scientific D2 attempt is now authorized under the exact frozen attempt/configuration. Retry, prompt/config drift, broader authority, alternate harness and Codex runtime adapter remain unauthorized.
- **Next:** execute exactly one frozen P5-FX-001 D2 attempt, then freeze resulting evidence before any adjudication or manifest revision.


### G2E-P5A-D2-S3 — Release-Coherent Instrument Successor

- **Status:** FORMALLY CLOSED / TERMINAL INVALID / NO RETRY
- **Study:** `p5a-d2s3-release-coherent-instrument-successor`
- **Attempt:** `p5a-d2s3-p5-fx-001-attempt-001`
- **Official Codex SHA-256:** `444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b`
- **Official helper SHA-256:** `0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4`
- **Execution config:** `df5308888eac7fa0b876f2cd68a51d0f2dd80a1b7c6d556cb04c854067b86e81`
- **Science-001:** pre-dispatch INVALID; attempt not consumed. Bound report SHA-256 `5da2db218c2b14856a5f07262cc840a63288fb81c490160ea83d0175d4cbca87`.
- **Science-002 report SHA-256:** `09e71058bd9e9b4b4fd2e5c4f5f0c412c228932fa183d08dc7d6df4d0fc5e712`
- **Science-002 runner evidence SHA-256:** `ae60858bfd53268fbb43fb5f1166aaa3acd4fe322f23279b139412bb260b8017`
- **Science-002 verification SHA-256:** `528b1fd3460c1efdd180dfab703dc264a5102d44fabf887411dc3f1bbc51c418`
- **Observed dispatch:** `turn/start` sent and accepted; turn id `01a0c981-1518-7eb3-9e5c-4373508655bf`.
- **Frozen adjudication inputs:** attempt consumed=true; turn terminal=false; timeout=false; infrastructure/protocol failure=true; authority violation=false; result absent; retry budget=0; replacement attempt unauthorized.
- **Scientific verdict:** `INVALID` under the preregistered rule because infrastructure/protocol failure prevents terminal executor/result metrics. This is not substantive FAIL and not PASS.
- **Capability consequence:** no functional promotion for `repository_read` or `repository_write`; prior structural official-harness qualification remains structural-only.
- **Resource hygiene:** Science-002 VHDX dismounted and verified detached.
- **No-rescue boundary:** D2-S3 MUST NOT be rerun, repaired into a replacement attempt, or granted timeout/protocol/harness rescue after consumption.
- **Formal adjudication:** `g2e/docs/P5A_D2S3_SCIENCE002_FORMAL_ADJUDICATION.md`
- **Next:** evidence-only post-closure protocol-failure decomposition. Any future model-bearing work requires a new successor study and attempt identity after that decomposition.


### G2E-P5A-D2-S4 — Queue-Safe Scientific Successor

- **Status:** QUALIFIED / ONE LOCAL SCIENTIFIC INVOCATION AUTHORIZED
- **Study:** `p5a-d2s4-queue-safe-scientific-successor`
- **Attempt:** `p5a-d2s4-p5-fx-001-attempt-001`
- **Predecessor:** D2-S3 terminal INVALID / attempt consumed / no retry.
- **Post-closure mechanism:** `CLIENT_QUEUE_OR_READER_FAILURE` / `UNCAUGHT_QUEUE_EMPTY_IN_RPC_CLIENT_NEXT_MESSAGE`.
- **Evidence basis:** post-closure bundle SHA256 `1775c3430692ec4e8037eb1776368d2544f5268d4dd71df77c63f3fca5c6eb66`.
- **Sole mechanism repair:** queue-safe client normalizes bounded-poll `queue.Empty` to `TimeoutError`; task/model/result/authority/timeout/retry semantics unchanged.
- **Official Codex SHA-256:** `444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b`
- **Official helper SHA-256:** `0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4`
- **Queue-safe client blob:** `b861f9fdb2f4af5d30961bb307aa6f943e07964d`
- **Runner blob:** `6d804429e8ab6a9881013149efd08051a7cbb7e4`
- **One-click blob:** `65317fa036472a29be4dd18449bdc35a8eb472e4`
- **Execution config:** `5a933057595e051884293a8f11917f95bed422399e55fd246932d09aeb627726`
- **Qualification run:** `35744866806` — Linux synthetic queue/inherited/P1-P4 PASS; Windows PowerShell 5.1 + official-harness D1 + turn-start schema + P1.5 final admission PASS.
- **Synthetic discriminating test:** terminal notification arriving after >2 seconds and multiple empty one-second polls is consumed successfully.
- **Retry budget:** 0.
- **Attempt-consumption boundary:** durable marker immediately before sole `turn/start` transport write.
- **Lock:** `g2e/docs/P5A_D2S4_SCIENTIFIC_EXECUTION_LOCK.json`
- **Next:** exactly one local D2-S4 scientific execution. No automatic retry after marker creation.


### G2E-P5A-D2-S4 — Science-001 terminal INVALID

- **Status:** FORMALLY CLOSED / TERMINAL INVALID / NO RETRY
- **Study:** `p5a-d2s4-queue-safe-scientific-successor`
- **Attempt:** `p5a-d2s4-p5-fx-001-attempt-001`
- **Source HEAD:** `2f8e42454f87d0dbda0f4dbfa26f384fe822e2cc`
- **Execution config:** `5a933057595e051884293a8f11917f95bed422399e55fd246932d09aeb627726`
- **Top-level report SHA256:** `e98ee53c550e13dd42715c63ca6cbf887aa69396f50c90abc6637a54a3dc9536`
- **Runner evidence SHA256:** `6e1ef9d48bf640a8a285370549771f76048e0280eaf121450f3fa6679c069f5d`
- **Verification SHA256:** `bf0e848c1eba9e8c0bf8a74da5fcf96dbe29898ec26d1ef91d21aca13a7be01b`
- **Observed dispatch:** `turn/start` sent and accepted; turn id `01a0c9af-d523-72f3-84fa-a575e91076b6`.
- **Queue-safe mechanism result:** runner exit 0; turn reached terminal; timeout false. The D2-S3 uncaught-`queue.Empty` mechanism is therefore not the D2-S4 failure mechanism.
- **Terminal status:** `failed`.
- **Result:** absent.
- **Frozen adjudication inputs:** attempt consumed=true; infrastructure/protocol failure=true; authority violation=false; retry budget=0; replacement attempt unauthorized.
- **Scientific verdict:** `INVALID / TERMINAL_INVALID_SERVER_DECLARED_FAILED_TURN`.
- **Capability consequence:** no promotion for `repository_read` or `repository_write`.
- **Resource hygiene:** Science-001 VHDX dismounted and verified detached.
- **No-rescue boundary:** D2-S4 MUST NOT be rerun.
- **Formal adjudication:** `g2e/docs/P5A_D2S4_SCIENCE001_FORMAL_ADJUDICATION.md`
- **Next:** evidence-only post-closure decomposition of the terminal failed record. Any future model-bearing work requires a new successor study and attempt identity after that decomposition.


### G2E-P5A-D2-S4 — Post-closure terminal-failure decomposition

- **Scientific status:** unchanged — FORMALLY CLOSED / INVALID / ATTEMPT CONSUMED / NO RETRY.
- **Post-closure bundle SHA256:** `ad7aef6c621554791213635c802578c5cc0f94f8e2e12381b5e629fd2836be39`.
- **Verification hash finding:** closed as governance transcription defect. The defective expected value had 63 hex characters; the actual 64-hex file hash `bf0e848c1eba9e8c0bf8a74da5fcf96dbe29898ec26d1ef91d21aca13a7be01b` matches the frozen top-level report.
- **Sanitized protocol sequence:** `turn/started → item/started → item/completed → account/rateLimits/updated → thread/status/changed → error → turn/completed(failed)`.
- **Bundle-level mechanism adjudication:** `UNRESOLVED_FROM_EXISTING_BUNDLE` because the sanitizer omitted mechanism-bearing `TurnError` fields (`message`, `codexErrorInfo`, `additionalDetails`, `willRetry`).
- **Existing-local recovery:** justified from immutable Science-001 `codex-home` artifacts only.
- **Recovery scope:** exact thread `01a0c9af-d509-7203-9608-06304738b12e` and turn `01a0c9af-d523-72f3-84fa-a575e91076b6`; sessions/archived_sessions/log + SQLite read-only; auth/config/credentials excluded.
- **Recovery qualification:** run `35750732353` PASS — synthetic session JSONL error recovery, SQLite read-only recovery, secret-redaction, Windows PowerShell 5.1 and P1-P4.
- **Recovery lock:** `g2e/docs/P5A_D2S4_PERSISTED_TURN_ERROR_RECOVERY_LOCK.json`.
- **Next:** exactly one local read-only persisted-error collection. No D2-S5 execution is authorized until recovery identifies a concrete mechanism or returns `UNRESOLVED_FROM_EXISTING_LOCAL_EVIDENCE`.


### G2E-P5A-D2 — Terminal stop after D2-S4 persisted recovery

- **D2 status:** CLOSED / NO D2-S5 AUTHORIZATION.
- **D2-S4 recovery bundle SHA256:** `60a94c50d9eaba65c49840ffeb5861d347aab2298b91d213bb6ea910de6f3a1b`.
- **Recovery JSON SHA256:** `72ad98eb08ac225ac6bbcb21fbbf44852264fe2474bd960db0d8402052572cd8`.
- **Recovery mode:** read-only existing local evidence; Codex=false; RPC=false; VHDX=false; retry=false; forbidden files read=false.
- **Text/session/log recovery:** scanned text files = 0; exact thread/turn matches = 0.
- **SQLite recovery:** six SQLite files inspected read-only; exact thread/turn matches = 0.
- **Final mechanism adjudication:** `UNRESOLVED_FROM_EXISTING_LOCAL_EVIDENCE`.
- **D2-S4 scientific verdict:** unchanged — INVALID / attempt consumed / no retry.
- **Successor decision:** D2-S5 not authorized because no single mechanism-specific prospective change is supported by existing evidence.
- **Terminal stop:** `UNRESOLVED_FROM_EXISTING_LOCAL_EVIDENCE / STOP_MODEL_EXECUTION / NO_D2S5_AUTHORIZATION`.
- **Recovery result:** `g2e/docs/P5A_D2S4_PERSISTED_TURN_ERROR_RECOVERY_RESULT.md`
- **Stop decision:** `g2e/docs/P5A_D2_TERMINAL_STOP_DECISION.md`
- **Future direction if reopened:** a separately identified observability/instrumentation adequacy program, qualified before any model-bearing task.


### G2E-P5A-CODEX-OQ1 — Terminal Error Observability Qualification

- **Status:** PASS / LOCKED / ZERO-MODEL.
- **Purpose:** qualify privacy-safe mechanism evidence for Codex terminal failures before any new functional successor.
- **Qualified candidate:** `bc06d9b75736407fc68018c6d5b81965c756e2bc`.
- **Observability blob:** `b6d3c6fcb671dd166893edd46388c8d69dca9105`.
- **Exact upstream:** `openai/codex@3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`.
- **Preserved mechanism fields:** `TurnError.message`, `codexErrorInfo`, `additionalDetails`, `willRetry`, bounded misalignment fields, turn/thread identity and terminal status.
- **Privacy:** Bearer/API-key/token-like values, secret-bearing object keys and recognizable user-home paths are redacted; raw field/protocol hashes and lengths remain available for integrity.
- **Exact protocol compatibility:** source and JSON schema blobs verified against frozen upstream identities.
- **Qualification run:** `35789231154` — Linux exact-protocol/privacy/P1-P4 PASS; Windows zero-model tests PASS.
- **Artifact:** `10721262192`, digest `sha256:6ca1242dac89398430b164a4392a47e0b5d8419150f40734f566322c48beda26`.
- **Model execution during OQ1:** none.
- **Governance scope correction:** P5A Codex adapter remains OPEN; D2-S4 remains immutable INVALID/consumed/no-retry. The earlier terminal-stop decision is superseded only in scope: no model-bearing successor until observability PASS.
- **Lock:** `g2e/docs/P5A_CODEX_OBSERVABILITY_QUALIFICATION_LOCK.json`.
- **Result:** `g2e/docs/P5A_CODEX_OBSERVABILITY_QUALIFICATION_RESULT.md`.

### G2E-P5A-D2-S5 — Observability-Qualified Functional Successor Design

- **Status:** PREREGISTERED / DESIGN QA PASS / IMPLEMENTATION QUALIFICATION REQUIRED.
- **Study:** `p5a-d2s5-observability-qualified-functional-successor`.
- **Attempt:** `p5a-d2s5-p5-fx-001-attempt-001`.
- **Scientific task:** exact P5-FX-001 unchanged.
- **Execution semantics:** official harness/helper, authority, queue-safe polling, 90 s timeout, zero retry and marker-before-send unchanged.
- **Sole prospective measurement change:** bind exact OQ1 observability blob `b6d3c6fcb671dd166893edd46388c8d69dca9105` into the live protocol recorder.
- **Failed-turn semantics:** still INVALID; observability supplies mechanism evidence only and cannot rescue outcome.
- **Local root if later authorized:** `g2e/.local/P5A-D2S5-SCIENCE-001`.
- **Current model execution authorization:** FALSE.
- **Next:** bounded D2-S5 implementation + zero-model qualification; only an exact post-qualification lock may authorize one local model-bearing attempt.


### G2E-P5A-D2-S5 — Implementation / Zero-Model Qualification PASS

- **Status:** QUALIFIED / EXACT EXECUTION LOCKED / ONE LOCAL SCIENTIFIC ATTEMPT AUTHORIZED.
- **Study:** `p5a-d2s5-observability-qualified-functional-successor`.
- **Attempt:** `p5a-d2s5-p5-fx-001-attempt-001`.
- **Qualified candidate:** `85e5312c032225a317c3116ba9150bf325af4b23`.
- **Qualification workflow:** `35791102414`.
- **Linux:** bounded diff, compile/parser, live-recorder tests, OQ1 tests, inherited queue-safe regression, P1-P4 PASS.
- **Windows:** PowerShell 5.1 parser, wrapper self-test, live-recorder/OQ1 tests, exact official D1 structural discovery and P1.5 admission PASS.
- **Execution config:** `27bf768c7189fc630d04bcc98d8c854c1409151ab42e3ea466c10128aca36240`.
- **Observable client:** `72c77c1fbd1e2c20881723f18ef2f1435ded2b2b`.
- **OQ1 observability:** `b6d3c6fcb671dd166893edd46388c8d69dca9105`.
- **Runner:** `259224a53aac7b79d0607360ba496d07503ef38d`.
- **Verifier:** `094809a2edbb1d1d9a207d53644f9f8f8cb89bb6`.
- **Admission:** `a37e78d28bf9cc59b0e9ee5dc2b41c659e316f92`.
- **One-click:** `175ff9e22a912c4c1a20d66ddc41ff41a36d7077`.
- **Portability repair:** OQ1 identity now binds repository Git object identity rather than checkout byte representation; final candidate passes Linux + Windows.
- **Scientific task:** exact P5-FX-001 unchanged.
- **Timeout:** 90 seconds.
- **Retry budget:** 0.
- **Attempt-consumption boundary:** durable marker immediately before sole `turn/start` transport write.
- **Qualification model turn:** none.
- **Local root:** `g2e/.local/P5A-D2S5-SCIENCE-001`.
- **Execution lock:** `g2e/docs/P5A_D2S5_SCIENTIFIC_EXECUTION_LOCK.json`.
- **Pre-execution QA:** count=0.
- **Next:** exactly one local D2-S5 scientific execution. No automatic retry after marker creation.


### G2E-P5A-D2-S5 — Verifier Identity Repair / Requalification

- **Status:** PASS / SUPERSEDES PRIOR D2-S5 EXECUTION LOCK.
- **Finding:** the prior qualified verifier blob `094809a2edbb1d1d9a207d53644f9f8f8cb89bb6` still bound obsolete observable-client identity `57f5b3e0...`, while runner/admission bound final client `72c77c1...`. A real execution would therefore fail evidence identity admission despite a correct client.
- **Scientific effect:** none; the finding was detected before D2-S5 model execution and before attempt consumption.
- **Repair:** verifier now binds final observable-client blob `72c77c1fbd1e2c20881723f18ef2f1435ded2b2b`; synthetic qualification explicitly asserts verifier client/OQ1 identities.
- **Authoritative qualified candidate:** `2b37ade5dab3f13a55192b674d2531ca4876676b`.
- **Qualification workflow:** `35794109437`.
- **Linux job:** `106969254830` — PASS.
- **Windows job:** `106969254628` — PASS.
- **Artifact:** `10722927391`; digest `sha256:a959761219fe55806b3a1cb959e52e9a537cb3aa3e07174b4c39e1011c0c4421`.
- **Execution config:** unchanged `27bf768c7189fc630d04bcc98d8c854c1409151ab42e3ea466c10128aca36240`.
- **Verifier:** authoritative blob `91b30c10c0626a82989c6f8091155b63d784fa41`.
- **Qualification model turn:** none; scientific attempt remains unconsumed.
- **Lock:** `P5A_D2S5_SCIENTIFIC_EXECUTION_LOCK.json` v2.
- **Next:** exactly one local D2-S5 scientific execution; retry budget remains zero after durable marker creation.


### G2E-P5A-CGW — Codex / ChatGPT Web Bridge Specification Workstream

- **Status:** SPECIFICATION-ONLY / BOUNDED / NO MODEL EXECUTION / NO FUNCTIONAL CLAIM.
- **Workstream:** `p5a-cgw-codex-chatgpt-web-bridge-qualification`.
- **Branch:** `research/p5a-cgw-specification`.
- **GWF base:** `feature/g2e-framework@065960bbe764337da7bca60b9dd0c451e62fa2e4`.
- **Reviewed bridge source:** `miuuyy/codex-chatgpt-web@eaf4f09ae92d4dc4429fa597b0861663138f08f8`; package metadata at reviewed source `5.0.8`.
- **Canonical-route rule:** P5A official Codex remains the canonical/reference route and is not replaced, rescued or credited by P5A-CGW.
- **Official-lane status:** D2 official remains separate; its next admissible infrastructure direction is quota admission. This branch does not authorize or implement that work.
- **Execution-authority invariant:** G2E authorizes the attempt; official Codex remains the execution authority for local task actions; `codex-chatgpt-web` is transport/inference mediation only; ChatGPT Web is the inference surface only.
- **No hidden executor:** the bridge may not widen sandbox/approval/tool authority, execute local side effects independently of Codex, become a second planner/router, or issue G2E verdicts.
- **No silent fallback:** official/native fallback, model substitution, bridge-mode substitution and legacy-connector substitution are forbidden within a frozen attempt.
- **Evidence separation:** P5A-CGW route-specific evidence cannot promote P5A official capabilities; official-route evidence cannot silently promote P5A-CGW.
- **Specification artifacts:** `P5A_CGW_ORIGIN_AND_SCOPE.md`, `P5A_CGW_TRUST_AUTHORITY_OBSERVABILITY_SPEC.md`, `P5A_CGW_ZERO_MODEL_QUALIFICATION_PLAN.md`, `P5A_CGW_SPECIFICATION_LOCK.json`.
- **Current authorization:** implementation=false; zero-model qualification execution=false; browser/model turn=false; scientific attempt=false; comparative study=false.
- **Next:** separately authorize bounded implementation + zero-model/synthetic qualification. Only a PASS of that macro-gate may permit preregistration and exact locking of the first model-bearing P5A-CGW attempt.
