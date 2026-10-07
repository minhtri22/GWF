# GWF vNext P2 — Preregistration và đóng băng hợp đồng hồ sơ quản trị miền

**Gate:** `GWF_VNEXT_P2_DOMAIN_GOVERNANCE_PROFILES_PREREGISTRATION_AND_CONTRACT_FREEZE`  
**Trạng thái:** `PREREGISTERED / CONTRACT FROZEN CANDIDATE`  
**Ngày:** 2026-10-07  
**Nhánh:** `pivot/gwf-autonomous-research-stack-v1`  
**P2 bắt đầu tại:** `148cbc1e8f7a929fae44895576f3d713d6b26efa`  
**Định nghĩa máy-đọc (machine-readable definitions):** `docs/pivot/GWF_VNEXT_P2_DOMAIN_GOVERNANCE_PROFILE_DEFINITIONS_V1.json`  
**Blob định nghĩa:** `fe83c0c638baee9912aa6b15f82bee1c19c2267a`

## 1. Mục tiêu

P2 khóa semantics của hồ sơ quản trị miền (domain governance profiles) trên nền kernel P1 đã qualification.

P2 **không triển khai runtime profile thật**.

P2 chỉ trả lời:

1. mỗi profile nghiên cứu/phần mềm cho phép và cấm loại hành động nào;
2. mức tự chủ (autonomy), mutation, protected-resource, lineage, retry/recovery và claim-permission tương ứng;
3. transition nào hợp lệ;
4. transition nào cần phê duyệt con người (human approval);
5. khi nào phải tạo successor thay vì quay ngược profile;
6. ranh giới giữa lỗi vận hành và kết luận khoa học/phát hành.

## 2. Baseline bị khóa

P2 kế thừa nguyên vẹn:

- P1 contract-freeze HEAD: `e62032607af28603d776ea6d4a494fbc250ddd4b`;
- P1 qualified implementation HEAD: `15daa586987734910a5766a23361a021463efe08`;
- P1 execution-lock commit: `e6d8d01a9480ada5f7cbcaeb4354290576487f9e`.

P2 không được thay đổi:

- `GovernanceProfileDefinition` contract của P1;
- `GovernanceTransitionProposal`;
- authority/budget monotonicity;
- `WorkAssignment`;
- `ExecutorBinding`;
- `HumanActionRequest`;
- G2E semantic ownership;
- distinction runtime success ≠ domain/scientific PASS.

## 3. Nguồn domain hiện hữu được dùng để ràng buộc tương thích

P2 đã đọc nhưng **không sửa**:

- `domains/research.workflow.yaml`
  - `domain_id = research.full-cycle`
  - version `0.5.0`;
- `domains/software.workflow.yaml`
  - `domain_id = software.delivery`
  - version `0.1.0`.

Các profile P2 là lớp governance mới phía trên domain package hiện hữu; chúng không tự động thay đổi artifact/gate/workunit semantics cũ.

## 4. Quyết định kiến trúc quan trọng — TRIAGE không phải downgrade

P2 đóng băng quy tắc:

> `TRIAGE` là profile bootstrap/pre-domain-work cho chẩn đoán vận hành, không phải một profile để hạ ngược về sau khi scientific/software lock đã tiến triển.

Do đó:

- nếu đang ở `research.measurement` hoặc `research.confirmatory` mà có lỗi máy, transport, dependency, checkpoint, disk, v.v., recovery diễn ra **trong profile hiện tại** theo `retry_recovery_policy`;
- nếu đang ở `software.qualification` hoặc `software.release`, lỗi vận hành cũng không đổi profile thành triage;
- triage record thuộc operational/audit lineage;
- triage không được biến lỗi hạ tầng thành scientific FAIL hay release FAIL.

Lý do quản trị:

1. tránh mất scientific/release lock chỉ vì lỗi hạ tầng;
2. tránh downgrade để né protected-resource/no-rescue rules;
3. giữ profile hash/transition graph xác định và không chu kỳ (acyclic).

## 5. Transition graph bị khóa

### Nghiên cứu

```text
research.triage
      |
      | AUTO_ALLOWED
      v
research.exploratory
      |
      | AUTO_ALLOWED
      v
research.measurement
      |
      | HUMAN_APPROVAL_REQUIRED
      v
research.confirmatory
```

Không có transition ngược tại chỗ (in-place backward transition).

### Phần mềm

```text
software.triage
      |
      | AUTO_ALLOWED
      v
software.development
      |
      | AUTO_ALLOWED
      v
software.qualification
      |
      | HUMAN_APPROVAL_REQUIRED
      v
software.release
```

Không có transition ngược tại chỗ.

Một edge không tồn tại phải fail-closed.

## 6. Successor thay cho downgrade/no-rescue

Khi cần thay đổi semantics đã khóa:

### Nghiên cứu

Ví dụ:

- đổi hypothesis;
- đổi metric;
- đổi threshold;
- đổi cohort;
- đổi seed namespace;
- đổi protocol sau measurement/confirmatory exposure;
- cứu một confirmatory FAIL/SPENT bằng thiết kế mới.

Thì không transition ngược profile hiện tại.

Phải:

```text
old lineage
  -> giữ nguyên terminal/spent state
  -> tạo governed successor subject/revision
  -> successor bắt đầu từ research.exploratory
  -> fresh evidence namespace mới nếu cần
```

### Phần mềm

Nếu qualification/release cần:

- scope expansion;
- product-semantic rewrite;
- candidate architecture change ngoài bounded repair;

thì:

```text
old candidate/release lineage
  -> giữ nguyên
  -> new successor development cycle
```

Bounded repair trong qualification được phép nếu vẫn trong frozen scope, nhưng candidate identity phải đổi và affected QA phải chạy lại.

## 7. Research profiles

### 7.1 `research.triage`

Mục đích:

- diagnose;
- inspect;
- operational repair;
- reroute khi đã pre-authorized;
- recover checkpoint.

Bị cấm:

- scientific normative mutation;
- calibration consumption;
- protected confirmatory consumption;
- formal scientific verdict;
- retroactive preregistration.

Claim ceiling:

`OPERATIONAL_OBSERVATION_ONLY`.

Operational records không được append như scientific PASS/FAIL.

Exact profile hash:

`2aa6068a82ab9b274cd9d9f5700b2166d499d2d8a8554c8b6e23be6b95aa99ef`

### 7.2 `research.exploratory`

Nguyên tắc:

`LARGE_SEARCH_FREEDOM_SMALL_CLAIM_AUTHORITY`.

Được phép:

- create/drop/mutate hypothesis;
- mechanism search;
- exploratory metric changes;
- branches;
- pilots;
- ablations;
- bounded workers;
- retry/replan.

Bị cấm:

- protected confirmatory consumption;
- formal scientific verdict;
- retroactive preregistration;
- deletion of failed lineage.

Claim ceiling:

`EXPLORATORY_FINDING`.

Exact profile hash:

`90114f02baee23f4c6c8ec5eb9b817cd5c3f332dbe014c38595254e20037373d`

### 7.3 `research.measurement`

Measurement semantics được freeze cho current measurement lineage.

Được phép:

- exact frozen measurement execution;
- calibration nếu exact authorized;
- repeated measurement trong budget;
- operational recovery nếu measurement identity không đổi.

Bị cấm:

- protected confirmatory evidence;
- formal scientific verdict;
- silent metric/instrument mutation;
- confirmatory language.

Material change của metric/instrument/protocol không phải retry.

Claim ceiling:

`MEASUREMENT_RESULT`.

Exact profile hash:

`619a6a7ea903b4ad736222d89d92f23bfd58adff36dd31a6c3e69fd3150691a6`

### 7.4 `research.confirmatory`

Đây là profile proof-governance mạnh nhất.

Yêu cầu trước activation:

- measurement protocol frozen;
- metric/instrument lock PASS;
- confirmatory preregistration frozen;
- execution readiness PASS;
- protected-resource plan bound;
- independence policy bound;
- durable human approval `RESEARCH_CONFIRMATORY_ACTIVATION`.

Được phép:

- execute frozen plan;
- collect evidence;
- request independent QA;
- operational recovery chỉ nếu scientific semantics giữ nguyên.

Bị cấm:

- hypothesis/metric/threshold/cohort/seed namespace mutation;
- executor substitution im lặng;
- retroactive preregistration;
- reinterpret terminal verdict.

Protected evidence:

- exact resource set;
- exact consumption budget;
- atomic consumption record;
- raw evidence freeze trước adjudication.

Sau protected outcome exposure:

- no rescue;
- consumed attempt immutable/spent;
- không hidden rerun.

Profile không tự tạo scientific verdict.

Formal verdict thuộc G2E/domain adjudicator.

Claim ceiling của profile:

`CONFIRMATORY_CANDIDATE`.

External/public claim elevation cần HumanActionRequest riêng hoặc authorization đã bind exact payload.

Exact profile hash:

`00487a768af2d3040bc7c847f0933764d84aed0a3e34988ad5876048aa73ca8b`

## 8. Research transition criteria

### triage -> exploratory

Disposition:

`AUTO_ALLOWED`

Bắt buộc:

- `OPERATIONAL_BLOCKER_CLEARED`;
- `SCIENTIFIC_WORK_AUTHORIZED`;
- `PROTECTED_CONFIRMATORY_NAMESPACE_PRISTINE`.

### exploratory -> measurement

Disposition:

`AUTO_ALLOWED`

Bắt buộc:

- `MECHANISM_OR_QUESTION_SELECTED`;
- `MEASUREMENT_OBJECT_DEFINED`;
- `MEASUREMENT_PLAN_READY`;
- `PROTECTED_CONFIRMATORY_NAMESPACE_PRISTINE`.

### measurement -> confirmatory

Disposition:

`HUMAN_APPROVAL_REQUIRED`

Human action kind:

`RESEARCH_CONFIRMATORY_ACTIVATION`

Bắt buộc:

- `MEASUREMENT_PROTOCOL_FROZEN`;
- `METRIC_INSTRUMENT_LOCK_PASS`;
- `CONFIRMATORY_PREREGISTRATION_FROZEN`;
- `EXECUTION_READINESS_PASS`;
- `PROTECTED_RESOURCE_PLAN_BOUND`;
- `INDEPENDENCE_POLICY_BOUND`.

## 9. Software profiles

### 9.1 `software.triage`

Được phép:

- repo/build/tooling diagnosis;
- environment repair;
- checkpoint recovery.

Bị cấm:

- product behavior mutation;
- scope expansion;
- merge/deploy/publish;
- release acceptance.

Claim ceiling:

`OPERATIONAL_OBSERVATION_ONLY`.

Exact hash:

`abbf4b6c440b362194e2b760e9c0c6d7a9eded589731ba0199aa72ea7084e724`

### 9.2 `software.development`

Được phép:

- mutate code trong approved scope;
- tests;
- bounded refactor;
- bounded worker fanout;
- repair/retry.

Bị cấm:

- scope expansion không authorization;
- merge/deploy/publish;
- qualification/release acceptance.

Claim ceiling:

`IMPLEMENTATION_RESULT`.

Exact hash:

`a84df83e51d4a598d2a6f53a7b29f93bd407699cc0cc40e3bac01cdaa7dfd949`

### 9.3 `software.qualification`

Scope lock phải frozen.

Được phép:

- tests/regressions;
- independent QA;
- bounded repair trong scope.

Nếu candidate SHA đổi:

- prior candidate QA invalid;
- new candidate identity;
- affected qualification rerun.

Material scope change:

- successor development cycle.

Release acceptance bị cấm.

Claim ceiling:

`QUALIFIED_CANDIDATE`.

Exact hash:

`cb6177440faccbacde9f588bbdf2c80ed61f8728a2b0b2fdb90c5aa2cd3cf2c4`

### 9.4 `software.release`

Candidate SHA frozen.

Được phép:

- read-only exact-SHA verification;
- preauthorized non-destructive packaging;
- propose release.

Bị cấm tự động:

- merge;
- deploy;
- publish;
- destructive external mutation;
- code repair.

Promotion vào release yêu cầu durable human approval.

Profile completion không đồng nghĩa release accepted.

Exact hash:

`7c8ca2a092141297f0da8caf2b80a4fcd04eb830e900a5eface9e11e289d1388`

## 10. Software transition criteria

### triage -> development

`AUTO_ALLOWED`

Bắt buộc:

- `REPOSITORY_BASELINE_VERIFIED`;
- `SOFTWARE_SCOPE_AUTHORIZED`;
- `OPERATIONAL_BLOCKER_CLEARED`.

### development -> qualification

`AUTO_ALLOWED`

Bắt buộc:

- `SOFTWARE_SCOPE_LOCK_FROZEN`;
- `IMPLEMENTATION_CANDIDATE_FROZEN`;
- `LOCAL_TESTS_PASS`;
- `REGRESSION_BASELINE_PASS`;
- `INDEPENDENCE_PLAN_BOUND`.

### qualification -> release

`HUMAN_APPROVAL_REQUIRED`

Human action kind:

`SOFTWARE_RELEASE_PROMOTION`

Bắt buộc:

- `EXACT_CANDIDATE_SHA_FROZEN`;
- `REQUIRED_TEST_MATRIX_PASS`;
- `INDEPENDENT_QA_PASS`;
- `ROLLBACK_PLAN_BOUND`;
- `RELEASE_EFFECT_BOUNDARY_FROZEN`.

## 11. Human approval semantics

Human approval chỉ cho phép hành động/transition/elevation theo exact frozen payload.

Human không được:

- đổi PASS thành FAIL;
- đổi FAIL thành PASS;
- rescue consumed confirmatory evidence;
- thay candidate SHA sau QA mà giữ QA cũ;
- biến runtime success thành domain success.

## 12. Protected resource semantics

P2 research định nghĩa các class:

- `UNPROTECTED`;
- `DEVELOPMENT`;
- `CALIBRATION`;
- `PROTECTED_CONFIRMATORY`;
- `FROZEN_RAW_EVIDENCE`.

Protected-resource class là domain policy classification; exact resource identity/freshness có thể do G2E hoặc domain artifact sở hữu.

Profile chỉ enforcement quyền truy cập, không định nghĩa lại G2E Evidence semantics.

## 13. Claim permission semantics

`claim_permission_policy` là **ceiling**, không phải verdict engine.

Research:

- TRIAGE -> operational observation only;
- EXPLORATORY -> exploratory finding;
- MEASUREMENT -> measurement result;
- CONFIRMATORY -> confirmatory candidate.

Formal scientific verdict vẫn do adjudicator.

Software:

- TRIAGE -> operational observation;
- DEVELOPMENT -> implementation result;
- QUALIFICATION -> qualified candidate;
- RELEASE -> release candidate.

Release acceptance vẫn cần exact gates/approval; profile state không tự tạo acceptance.

## 14. Hash dependency và transition acyclicity

P1 profile hash bao gồm:

- domain_id;
- profile_id;
- version;
- policy;
- transition_edges.

Transition edge lại chứa exact target profile hash.

Do đó P2 khóa graph một chiều để profile hashes có thể materialize theo thứ tự từ terminal về đầu:

### Research

```text
confirmatory -> hash
measurement  -> embeds confirmatory hash -> hash
exploratory  -> embeds measurement hash  -> hash
triage       -> embeds exploratory hash  -> hash
```

### Software

```text
release       -> hash
qualification -> embeds release hash       -> hash
development   -> embeds qualification hash -> hash
triage        -> embeds development hash   -> hash
```

Backwards semantic change dùng successor policy, không tạo circular profile refs.

## 15. Preregistered implementation negative tests

P2 implementation phải chứng minh ít nhất 30 negative/contract tests được liệt kê trong machine-readable definitions.

Các nhóm bắt buộc:

- protected evidence firewall;
- formal-verdict firewall;
- no-rescue;
- measurement semantic immutability;
- confirmatory activation approval;
- release activation approval;
- candidate SHA invalidation;
- scope-lock enforcement;
- successor requirement;
- domain separation;
- authority/budget non-expansion;
- fail-closed unknown transition;
- UI non-authority;
- provider/model/transport non-semantic;
- no in-place backward transition;
- triage non-downgrade;
- deterministic exact profile hashes.

## 16. P2 PASS criteria

P2 PASS chỉ khi:

1. research/software profile semantics tách biệt;
2. đủ 4 research profiles;
3. đủ 4 software profiles;
4. exact hashes materialize theo P1 hash semantics;
5. transition graph không chu kỳ;
6. confirmatory/release activation cần human approval;
7. protected confirmatory evidence bị chặn trước confirmatory;
8. operational recovery không cần triage downgrade;
9. no-rescue/successor semantics explicit;
10. formal scientific verdict không thuộc profile;
11. release acceptance không thuộc profile completion;
12. P1 authority/budget ceilings không bị nới;
13. không provider/transport/model/UI-specific semantics;
14. không sửa runtime/domain source;
15. implementation negative tests preregistered trước code.

## 17. P2 FAIL criteria

P2 FAIL nếu:

- TRIAGE có thể được dùng để né confirmatory/qualification lock;
- backward transition có thể mutate cùng terminal lineage;
- exploratory/measurement có thể consume protected confirmatory evidence;
- human approval có thể rewrite adjudicated result;
- qualification candidate thay đổi nhưng QA cũ vẫn hợp lệ;
- release profile cho phép code mutation im lặng;
- profile tự tạo scientific/release PASS;
- domain profile mở rộng parent authority/budget;
- exact profile hash không deterministic;
- research/software semantics bị trộn;
- P2 chạm runtime/domain implementation trước contract freeze.

## 18. Implementation lock

Cho đến khi P2 formal QA PASS:

**Được phép trong P2 hiện tại:**

- normative documents;
- machine-readable profile definitions;
- contract consistency QA.

**Chưa được phép:**

- sửa `domains/research.workflow.yaml`;
- sửa `domains/software.workflow.yaml`;
- runtime/schema migration;
- RemoteMCP adapter;
- Codex adapter;
- G2E runtime import/merge;
- Mission Control UI;
- real-project execution;
- protected evidence consumption.

## 19. Frontier sau P2 nếu PASS

Bước hợp lệ tiếp theo sẽ là:

`GWF_VNEXT_P2_DOMAIN_GOVERNANCE_PROFILES_IMPLEMENTATION_STATIC_PREFLIGHT_AND_EXECUTION_LOCK`

Bước đó mới được phép materialize 8 frozen profile definitions vào domain package/runtime integration, thêm exact-hash validator và chạy zero-domain/zero-protected-resource fixtures.

Vẫn chưa được tích hợp RemoteMCP, Codex, G2E runtime hoặc UI ở bước đó.
