# GWF vNext P3 — G2E Semantic / Runtime Reconciliation Preregistration and Contract Freeze

**Gate:** `GWF_VNEXT_P3_G2E_SEMANTIC_RUNTIME_RECONCILIATION_PREREGISTRATION_AND_CONTRACT_FREEZE`  
**Date:** 2026-10-07  
**Branch:** `pivot/gwf-autonomous-research-stack-v1`  
**P3 start HEAD:** `2c7dccb4727c665d96bd18d9ef31f1af9d492d6c`  
**Machine-readable reconciliation manifest:** `docs/pivot/GWF_VNEXT_P3_G2E_RECONCILIATION_MANIFEST_V1.json`  
**Manifest blob:** `57917853b838bc1b62da46e7336baa0bcd11bf11`  
**Status:** `PREREGISTERED / CONTRACT FROZEN CANDIDATE`

## 1. Mục tiêu

P3 không triển khai runtime.

P3 chỉ khóa cách G2E semantic plane nối với GWF governance/runtime plane mà không tạo semantic-owner thứ hai.

P3 trả lời chính xác:

1. baseline G2E nào là provider-neutral qualified baseline để tái sử dụng;
2. file nào là canonical core, reusable adapter, qualification test, historical evidence hoặc transport experiment;
3. đối tượng G2E nào giữ semantic authority;
4. đối tượng GWF nào giữ governance/persistence/runtime authority;
5. `G2E AgentBinding` ánh xạ sang `GWF ExecutorBinding` ra sao mà không collision ownership;
6. Goal / Claim / Proof / ExecutionAttempt / Evidence / Adjudication ánh xạ cardinality thế nào;
7. revision/hash/identity của hai hệ thống tách nhau ra sao;
8. protected-resource và evidence-admission bridge fail-closed thế nào;
9. independence/QA reviewer được bảo toàn qua GWF ra sao;
10. điều gì tuyệt đối không được import trong P3.

## 2. Baseline GWF vNext được kế thừa

P3 kế thừa nguyên vẹn:

- P1 governance kernel contract + implementation lock;
- P2 domain-governance-profile contract + implementation lock.

Exact locks:

- P1 lock commit: `e6d8d01a9480ada5f7cbcaeb4354290576487f9e`;
- P2 lock commit: `6893f81a7da9728c909fe05eb44ff572f3ab4bbf`.

P3 không được sửa các locked implementation blobs của P1/P2.

## 3. Canonical qualified G2E baseline

Nguồn G2E được khảo sát:

`research/p5a-cgw-fx001-transport-corrected`

Observed branch head:

`d2ba5a123e2fbefd0138d3f1a7a0dd81373e5b87`

Observed tree:

`02dd219f7291f76fa525fda423b5e5529cfe487f`

P3 **không** dùng branch head đó làm semantic-baseline SHA, vì phần sau của branch chứa actual-harness/CGW/Codex/transport experiments.

Canonical provider-neutral qualified baseline được pin tại:

`6e9c518671c3f9ba140daa798458b37bee83647c`

Tree:

`38df8b7adf3269ce4eb9b2122c0b2c5391a6df18`

Lý do:

- đây là candidate được P1.5 qualification PASS;
- P1.5 giữ nguyên P1.4 semantics;
- P1.5 chưa authorize provider runtime adapter;
- P1.4 đã qualification provider-neutral AgentBinding surface;
- các canonical runtime/core/adapter blobs quan trọng tại baseline này vẫn giống hệt transport-branch head hiện tại.

Qualification chain được pin:

- P1 Core Schemas: `2fc077f8bc84f8dbdb42c180b3edc7af9418a6c1` — PASS;
- P2 Deterministic Core: `c2fc03a7470b835904252246421e1b8d9a1ec5ef` — PASS;
- P3 Standalone Runtime: `b9345f3cbeba564a0bf666d388d3873d9ffd1191` — PASS;
- P4 Base GWF Adapter: `1f6d49957c0c0dffa7b83c11caebed4ab2b90e0b` — PASS;
- P1.4 AgentBinding: `d3cb0bdb5644a9f1cff382450b5476e166759d72` — PASS;
- P1.5 Qualification Authority: `6e9c518671c3f9ba140daa798458b37bee83647c` — PASS.

P3 không reinterpret bất kỳ P5A outcome nào thành qualification của semantic core.

## 4. Exact canonical G2E runtime blobs

Pinned runtime core:

- `src/g2e/__init__.py` — `2e72f06a2fd348127666b35d5d872fe9220d6834`;
- `src/g2e/canonical.py` — `964cf296b18d081862d822f8039104d454e68154`;
- `src/g2e/schema_registry.py` — `79075f162673cd1c8e0b8cbd26569b02799b9461`;
- `src/g2e/schemas.py` — `8631f9af598103f6c095fa3981255b9bf4609f64`;
- `src/g2e/engine.py` — `4213f949f10e1f49c977fc22e06ea3a76d787be4`;
- `src/g2e/standalone.py` — `48c44050da96ecdac9061f74092b6af00cfc5694`.

Pinned reusable legacy GWF adapter references:

- `src/g2e/gwf_adapter.py` — `5ae80f28d03893848ec6e693b8c9f6197e87020a`;
- `src/g2e/gwf_domain.py` — `f82766aea584e86ea9cbed714a2c1ba2c28222c1`.

Các file adapter trên **không được import verbatim ở P3**.

P4 adapter target GWF 0.8.5 legacy Artifact/Revision/WorkUnit surfaces. P3 chỉ tái sử dụng semantic rules sau khi reconcile với P1/P2 vNext.

## 5. File classification freeze

Scope được phân loại:

- `g2e/**`;
- `src/g2e/**`;
- `tests/g2e/**`;
- `scripts/g2e/**`;
- `.github/workflows/g2e-*`.

Tree source bị khóa tại `02dd219f...`.

Tổng file trong scope:

`585`

Phân loại:

- `canonical_core`: **31**;
- `reusable_adapter`: **2**;
- `qualification_tests`: **16**;
- `historical_evidence`: **35**;
- `transport_experiment`: **501**;
- unclassified: **0**.

Exact path/blob/category inventory nằm trong machine-readable manifest.

### 5.1 canonical_core

Bao gồm:

- qualified runtime core source;
- normative G2E architecture/core-semantics/PRD documents.

Runtime source chỉ có thể được import sau một P3 implementation qualification riêng.

Normative docs là specification/reference; không phải runtime import.

### 5.2 reusable_adapter

Chỉ:

- `src/g2e/gwf_adapter.py`;
- `src/g2e/gwf_domain.py`.

Reuse mode:

`SELECTIVE_PORT_OR_WRAP_ONLY`

Verbatim import bị cấm cho tới khi requalify against GWF vNext P1/P2.

### 5.3 qualification_tests

Bao gồm P1/P2/P3/P4/P1.4/P1.5 provider-neutral qualification tests/workflows và P5 preimplementation qualification.

Old PASS không tự chuyển thành vNext PASS.

Tests có thể được port/adapt và phải chạy lại.

### 5.4 historical_evidence

Bao gồm lineage, qualification/result/QA/preimplementation evidence không thuộc transport experiment.

Dùng để audit/reference.

Không được execute/import như runtime implementation.

### 5.5 transport_experiment

Bao gồm P5A, CGW, Codex actual-harness experiments, product smoke, route diagnostics/configs/tests/workflows.

Các file này được giữ làm historical execution-environment evidence.

Chúng **không** là canonical semantic baseline và không được nhập vào GWF core/G2E bridge trong P3.

Điều này cũng khóa nguyên tắc:

> cùng dùng MCP/transport không làm hai execution environments trở thành cùng một authority/runtime model.

## 6. Ownership contract

### G2E semantic authority

G2E giữ quyền định nghĩa canonical semantics cho:

- GoalContract;
- GoalClosureContract;
- ClaimGraph;
- Claim;
- ProofObligation;
- ExecutionAttemptEnvelope;
- ExecutionResult;
- AgentCapabilityManifest;
- AgentEquivalencePolicy;
- AgentBinding;
- ProtectedResource;
- EvidenceAdmissionPolicy;
- EvidenceRecord / EvidenceRelation;
- Adjudication;
- ProofResult;
- ClaimResolution;
- GoalVerdict.

GWF ID/state/hash không được thay thế các identity/semantics này.

### GWF governance/runtime authority

GWF giữ:

- GovernanceProfile;
- GovernanceTransitionProposal;
- AuthorityEnvelope;
- BudgetEnvelope;
- WorkAssignment;
- ExecutorBinding;
- ExecutionEnvironmentRef;
- HumanActionRequest;
- durable runtime/persistence mapping;
- operational checkpoint/recovery ledger.

GWF có thể **stricter** hơn G2E về quyền/budget/resource access.

GWF không được tạo scientific PASS/FAIL hay release acceptance từ operational state.

## 7. Canonical identity mapping

Mỗi authoritative G2E object tiếp tục có:

- schema version;
- object ID;
- revision ID;
- G2E canonical content hash;
- provenance.

Runtime mapping có scope:

`(gwf_project_id, mapping_version)`

Rule:

- một G2E exact revision có tối đa một active canonical mirror trong một mapping scope;
- cùng exact ref có thể được mirror ở nhiều runtime/project scope;
- GWF artifact/revision/work assignment/run IDs chỉ là mapping IDs.

Hash domains tách biệt:

`G2E canonical hash != GWF runtime content hash`

Không được compare/substitute hai hash domain như một identity.

## 8. Goal / Claim / Proof mapping

### GoalContract / GoalClosureContract

Semantic owner: G2E.

GWF role:

- persist canonical mirror;
- enforce write/authority;
- retain exact G2E ref.

GWF project không phải GoalContract identity.

### ClaimGraph / Claim

Semantic owner: G2E.

Claim lifecycle/resolution không derive từ GWF job/task/run status.

GWF chỉ persist/index/map exact refs.

### ProofObligation

Một frozen ProofObligation revision có:

`0..N ExecutionAttempt`

nhưng N bị giới hạn bởi frozen retry/multipart policy.

GWF không tự mở rộng attempt count.

## 9. ExecutionAttempt ↔ WorkAssignment cardinality

Trong GWF mode:

> một frozen G2E ExecutionAttempt tương ứng chính xác một GWF WorkAssignment revision cho một dispatch.

WorkAssignment bắt buộc origin-bind:

- exact ProofObligation ref;
- exact ExecutionAttempt ref.

WorkAssignment completion là operational completion.

Nó không tạo Adjudication.

Nếu INVALID technical attempt được frozen retry policy cho phép thay thế:

- new G2E `attempt_id`;
- new WorkAssignment;
- new ExecutorBinding;
- old attempt preserved.

GWF runtime retry không được ngầm tạo scientific replacement attempt.

## 10. G2E AgentBinding ↔ GWF ExecutorBinding

Đây là reconciliation quan trọng nhất.

### 10.1 Semantic ownership

`AgentBinding` vẫn do G2E sở hữu.

Nó xác định semantic execution identity của **một G2E attempt**.

`ExecutorBinding` do GWF sở hữu.

Nó xác định authorized runtime resolution của **một WorkAssignment**.

ExecutorBinding không thay AgentBinding.

### 10.2 Cardinality

Agent-backed G2E attempt:

```text
1 ExecutionAttempt
  ↕
1 AgentBinding
  ↕ reconciliation
1 WorkAssignment
  ↕
1 ExecutorBinding
```

Non-agent G2E attempt:

- AgentBinding có thể bằng 0;
- dispatched GWF WorkAssignment vẫn cần runtime ExecutorBinding theo GWF contract;
- không được bịa một G2E AgentBinding chỉ để phù hợp GWF.

### 10.3 Resolution order

Đóng băng thứ tự:

1. G2E ExecutionAttempt identity tồn tại;
2. G2E AgentBinding resolve prospectively nếu agent-backed;
3. WorkAssignment bind exact proof/attempt refs và freeze/authorize;
4. GWF ExecutorBinding resolve execution environment phù hợp;
5. cross-binding reconciliation PASS;
6. mới dispatch.

Không được dispatch trước cross-binding reconciliation.

### 10.4 Identity projection

Các G2E AgentBinding dimensions:

- agent_app;
- provider_ref;
- model_ref;
- harness_ref;
- transport_ref.

GWF `ExecutorBinding.agent_identity` phải là exact non-widening projection của chúng.

Runtime-observed identity khác không được tự sửa binding.

Nó phải trở thành evidence/finding và material mismatch phải fail closed/new attempt.

### 10.5 Capability domains

Hai capability manifest không được trộn:

1. G2E `AgentCapabilityManifest`:
   - agent/harness capability;
2. GWF `ExecutionEnvironmentRef.capability_manifest_ref`:
   - environment/adapter capability.

Đối với agent-backed attempt:

`ExecutorBinding.capability_manifest_ref`

phải map exact G2E AgentCapabilityManifest.

Nó không được trỏ sang environment capability manifest như một semantic substitute.

GWF additional runtime capabilities có thể làm constraint chặt hơn nhưng không được bỏ required G2E agent capabilities.

### 10.6 Binding modes

Nếu G2E AgentBinding:

`FROZEN`

thì GWF ExecutorBinding bắt buộc:

`FROZEN`.

Nếu G2E:

`DYNAMIC`

GWF có thể resolve thành DYNAMIC hoặc stricter FROZEN, nhưng sau resolution trong attempt đó vẫn immutable.

Material substitution:

- agent app;
- provider;
- model;
- harness;
- transport;
- material capability identity

phải tuân G2E AgentEquivalencePolicy.

Nếu material thì:

`new ExecutionAttempt + new WorkAssignment + new ExecutorBinding`.

### 10.7 Qualification authority firewall

G2E `QualificationAuthorityGrant` là `QUALIFICATION_ONLY`.

GWF tuyệt đối không được sử dụng grant này như operational authority cho ExecutorBinding/dispatch.

## 11. Authority mapping

G2E AgentBinding `authority_scope` là semantic ceiling.

GWF effective AuthorityEnvelope phải:

`GWF effective authority ⊆ G2E allowed authority`.

GWF có thể từ chối nhiều hơn.

GWF không được cấp thêm quyền vì executor/transport/provider yêu cầu nó.

Human/UI/transport không tạo authority.

## 12. Revision and lineage contract

P3 khóa:

1. G2E object ID/revision/hash luôn canonical.
2. Editorial G2E change tạo revision mới; semantic-equivalence phải verify nếu giữ lineage.
3. Normative pre-outcome change tạo affected revision mới và refreeze downstream dependencies.
4. Normative post-outcome change tạo successor proof/study lineage.
5. Frozen WorkAssignment normative mutation tạo GWF revision/hash mới + reauthorization.
6. WorkAssignment mutation không được silently mutate referenced G2E exact ref.
7. Nếu semantics G2E đổi, G2E successor/revision phải tồn tại trước replacement WorkAssignment.
8. INVALID replacement attempt có attempt ID mới.
9. Material AgentBinding substitution có attempt ID mới.
10. Checkpoint/resume chỉ giữ attempt identity nếu exact refs, semantic configuration và protected-resource state vẫn chứng minh không đổi.

## 13. Protected-resource bridge

Semantic owner:

`G2E ProtectedResource`.

GWF enforcement:

- GovernanceProfile;
- AuthorityEnvelope;
- BudgetEnvelope;
- WorkAssignment protected-resource constraints;
- consumption/recovery ledger.

Exact G2E protected-resource refs phải propagate không đổi.

Freshness:

`FRESH → RESERVED → EXPOSED`

không có transition ngược.

Reservation phải durable trước access.

Exposure phải được ghi trước hoặc atomically với việc outcome trở nên available cho human/agent/downstream process.

Crash/recovery mà không chứng minh được non-exposure:

`EXPOSED_FAIL_CLOSED`.

GWF research profile có thể block resource sớm hơn nhưng không thể làm một access G2E cấm trở thành admissible.

## 14. Evidence-admission bridge

Frozen flow:

```text
runtime/executor output
    ↓
candidate payload + runtime provenance
    ↓
bridge verifies:
  exact attempt
  exact bindings
  environment/resource identity
  payload digest
    ↓
G2E EvidenceRecord = CANDIDATE
    ↓
G2E EvidenceAdmissionPolicy
    ↓
ADMITTED | REJECTED | INVALIDATED
    ↓
only ADMITTED exact refs
    ↓
G2E Adjudication
```

GWF runtime success:

- không imply ADMITTED;
- không imply PASS.

Evidence admission checks tối thiểu:

- source class;
- integrity;
- producer attempt linkage;
- freshness/protection;
- independence;
- derivation depth;
- missing-data behavior.

Rejected/invalidated evidence vẫn được preserve.

## 15. Adjudication ownership

Adjudication vẫn là G2E deterministic semantic output.

Một attempt được adjudicate one-shot.

ProofResult có thể chứa nhiều adjudications chỉ theo frozen INVALID replacement/multipart semantics.

GWF:

- persist immutable mirror;
- giữ governance disposition nếu cần.

Human:

- có thể ACCEPT_FOR_USE / REJECT_FOR_USE / REQUEST_NEW_PROOF / STOP;
- không được rewrite PASS/FAIL/INVALID/UNRESOLVED.

## 16. Independent QA / reviewer mapping

G2E `IndependencePolicy` là authority cho independence semantics.

GWF `WorkAssignment.independence_requirements` mirror exact hoặc stricter policy.

Nếu proof yêu cầu independent reviewer/QA:

- reviewer là một separate governed execution context/attempt;
- có binding riêng;
- phải thỏa exact frozen independence dimensions.

Chỉ đổi provider/model không đủ chứng minh independence.

P3 không hard-code Astra, Sol, Codex, ChatGPT hay model cụ thể vào semantic contract.

Model/harness qualification thuộc execution-environment/agent-profile phase sau.

## 17. Execution-environment separation

P3 giữ separation đã được pivot architecture xác lập.

G2E semantic runtime bridge là provider-neutral.

P5A transport material không được biến thành generic runtime assumption.

Sau này:

- Codex execution environment;
- ChatGPT-native/RemoteMCP execution environment;

có thể có adapter độc lập.

Cùng protocol MCP không đồng nghĩa cùng execution authority.

## 18. Preregistered P3 implementation negative tests

Machine-readable manifest khóa **40 negative tests** trước implementation.

Các nhóm bắt buộc:

- canonical G2E identity preservation;
- hash-domain separation;
- per-scope mapping uniqueness;
- exact Proof/Attempt origin binding;
- 1 attempt : 1 WorkAssignment dispatch;
- no runtime retry expansion;
- runtime completion ≠ admission/PASS;
- AgentBinding/ExecutorBinding ownership separation;
- binding identity/equivalence/capability-domain enforcement;
- qualification-authority firewall;
- authority non-escalation;
- protected-resource monotonic freshness;
- fail-closed exposure recovery;
- evidence admission firewall;
- independence preservation;
- immutable adjudication;
- successor/new-attempt semantics;
- checkpoint exact-ref validation;
- classifier firewall preventing transport/historical files entering runtime core.

## 19. P3 PASS criteria

P3 contract freeze PASS chỉ nếu:

1. exact qualified G2E provider-neutral baseline được pin;
2. exact source blobs được pin;
3. branch-head core drift check PASS;
4. toàn bộ 585 scoped files được classify exactly once;
5. unclassified = 0;
6. transport experiment không được coi là canonical core;
7. semantic ownership G2E/GWF tách rõ;
8. AgentBinding/ExecutorBinding mapping không tạo competing semantic owner;
9. Proof/Attempt/WorkAssignment cardinality rõ;
10. revision/hash domains tách rõ;
11. protected-resource bridge monotonic/fail-closed;
12. evidence admission vẫn G2E-owned;
13. GWF runtime success không tạo semantic PASS;
14. independent QA semantics giữ nguyên;
15. QualificationAuthorityGrant không leak thành operational authority;
16. không code/runtime/domain/import mutation xảy ra trong P3 preregistration;
17. P1/P2 locks không bị sửa;
18. implementation negative tests được preregister trước code.

## 20. P3 FAIL criteria

P3 FAIL nếu bất kỳ điều sau tồn tại:

- dùng P5A transport branch head như semantic baseline thay vì exact qualified provider-neutral baseline;
- import transport experiment vào canonical core;
- GWF ExecutorBinding thay thế G2E AgentBinding;
- GWF Environment capability manifest thay AgentCapabilityManifest;
- một material executor substitution giữ nguyên attempt ID;
- GWF retry tự tạo scientific replacement attempt;
- WorkAssignment COMPLETED tạo G2E PASS;
- GWF Evidence status tự trở thành ADMITTED;
- GWF hash thay G2E hash;
- protected EXPOSED có thể quay lại FRESH/RESERVED;
- human/GWF state rewrite adjudication;
- independence được suy ra chỉ vì đổi model/provider;
- qualification-only grant được dùng cho operational dispatch;
- P3 prereg làm runtime/import/UI/adapter integration.

## 21. Implementation lock

Trong P3 preregistration chỉ được:

- reconciliation manifest;
- normative preregistration;
- contract consistency QA;
- update canonical plan frontier.

Chưa được:

- sửa `src/`;
- import/merge `src/g2e/`;
- port legacy GWF adapter;
- tích hợp RemoteMCP;
- tích hợp Codex;
- refactor Mission Control UI;
- chạy real project;
- consume protected evidence.

## 22. Frontier sau P3 nếu PASS

Bước hợp lệ tiếp theo:

`GWF_VNEXT_P3_G2E_SEMANTIC_RUNTIME_RECONCILIATION_IMPLEMENTATION_STATIC_PREFLIGHT_AND_EXECUTION_LOCK`

Bước đó mới được phép tạo **provider-neutral bridge implementation** theo frozen mapping.

P3 implementation vẫn không tự động mở:

- Codex adapter;
- RemoteMCP adapter;
- Mission Control UI;
- real research run.
