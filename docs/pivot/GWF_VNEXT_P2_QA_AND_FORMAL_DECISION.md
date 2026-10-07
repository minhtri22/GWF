# GWF vNext P2 — QA hợp đồng và quyết định chính thức

**Gate:** `GWF_VNEXT_P2_DOMAIN_GOVERNANCE_PROFILES_PREREGISTRATION_AND_CONTRACT_FREEZE`  
**Ngày:** 2026-10-07  
**Nhánh:** `pivot/gwf-autonomous-research-stack-v1`  
**P2 start:** `148cbc1e8f7a929fae44895576f3d713d6b26efa`  
**Definitions blob:** `fe83c0c638baee9912aa6b15f82bee1c19c2267a`  
**Preregistration blob:** `4009b9fe8cb9bb0d48b6dea15b7df528010c7bde`  
**Verdict:** **PASS**  
**OPEN findings:** **0**

## 1. Phạm vi QA

QA P2 chỉ kiểm:

- tính nhất quán giữa P1 contract và P2 profile definitions;
- exact profile hashes;
- transition topology;
- domain separation;
- authority/budget non-expansion;
- protected-resource firewall;
- no-rescue/successor semantics;
- formal-verdict/release-acceptance separation;
- implementation-negative-test preregistration;
- phạm vi diff.

Không có runtime/domain implementation nào được đánh giá hay chạy tại gate này.

## 2. Exact hash QA

Đã recompute độc lập payload hash cho đủ 8 profile bằng đúng semantics P1:

```text
canonical JSON:
  sort_keys = true
  separators = compact
  UTF-8
digest:
  SHA-256
```

Kết quả:

### Research

- `research.triage`
  - `2aa6068a82ab9b274cd9d9f5700b2166d499d2d8a8554c8b6e23be6b95aa99ef`
- `research.exploratory`
  - `90114f02baee23f4c6c8ec5eb9b817cd5c3f332dbe014c38595254e20037373d`
- `research.measurement`
  - `619a6a7ea903b4ad736222d89d92f23bfd58adff36dd31a6c3e69fd3150691a6`
- `research.confirmatory`
  - `00487a768af2d3040bc7c847f0933764d84aed0a3e34988ad5876048aa73ca8b`

### Software

- `software.triage`
  - `abbf4b6c440b362194e2b760e9c0c6d7a9eded589731ba0199aa72ea7084e724`
- `software.development`
  - `a84df83e51d4a598d2a6f53a7b29f93bd407699cc0cc40e3bac01cdaa7dfd949`
- `software.qualification`
  - `cb6177440faccbacde9f588bbdf2c80ed61f8728a2b0b2fdb90c5aa2cd3cf2c4`
- `software.release`
  - `7c8ca2a092141297f0da8caf2b80a4fcd04eb830e900a5eface9e11e289d1388`

Result: **PASS**.

## 3. Transition topology QA

Exact graph recomputed từ target profile refs:

```text
research.triage
 -> research.exploratory
 -> research.measurement
 -> research.confirmatory

software.triage
 -> software.development
 -> software.qualification
 -> software.release
```

Terminal profiles:

- `research.confirmatory`;
- `software.release`.

Không có cycle.

Không có backward in-place edge.

Unknown/missing edge phải fail-closed theo P1.

Result: **PASS**.

## 4. TRIAGE non-downgrade QA

P2 khóa rõ:

- TRIAGE chỉ là bootstrap/pre-domain-work profile;
- lỗi vận hành sau khi đã vào advanced profile dùng recovery policy của profile hiện tại;
- không downgrade chỉ để sửa transport/machine/dependency;
- không dùng triage để né measurement/confirmatory/qualification/release lock.

Điều này giữ nguyên:

- no-rescue;
- protected-resource policy;
- candidate/scientific identity;
- append-only lineage.

Result: **PASS**.

## 5. Research package QA

### TRIAGE

- protected/calibration access bị chặn;
- scientific mutation/verdict bị chặn;
- operational failure không được ghi thành scientific FAIL.

PASS.

### EXPLORATORY

- search/mutation autonomy rộng;
- protected confirmatory evidence bị chặn;
- formal scientific verdict bị chặn;
- failed branches phải được giữ.

PASS.

### MEASUREMENT

- measurement semantics frozen cho current lineage;
- calibration chỉ exact authorized;
- protected confirmatory evidence bị chặn;
- metric/instrument/protocol material change không được coi là retry;
- formal scientific verdict bị chặn.

PASS.

### CONFIRMATORY

- activation cần `RESEARCH_CONFIRMATORY_ACTIVATION`;
- protected-resource plan và independence policy phải bind trước;
- scientific normative mutation bị cấm sau study lock;
- after protected outcome exposure áp dụng no-rescue;
- consumed attempt immutable/spent;
- profile không sở hữu formal verdict;
- formal verdict thuộc G2E/domain adjudicator.

PASS.

## 6. Software package QA

### TRIAGE

- chỉ diagnosis/tooling/environment repair không đổi product semantics;
- merge/deploy/publish bị chặn.

PASS.

### DEVELOPMENT

- code mutation chỉ trong approved scope;
- không qualification/release acceptance;
- scope expansion không được tự động.

PASS.

### QUALIFICATION

- scope lock frozen;
- independent QA/test/regression được phép;
- bounded repair làm đổi candidate identity và reset affected QA;
- candidate SHA mới không kế thừa QA cũ;
- release acceptance bị chặn.

PASS.

### RELEASE

- candidate SHA frozen;
- product-code mutation bị chặn;
- merge/deploy/publish/destructive external action không auto-authorized;
- activation cần `SOFTWARE_RELEASE_PROMOTION`;
- profile completion không tự tạo release acceptance.

PASS.

## 7. Successor/no-rescue QA

P2 không dùng backward transition để sửa lineage cũ.

Research material scientific change sau terminal/spent:

```text
new governed successor subject
 -> research.exploratory
 -> fresh evidence namespace when required
```

Software material scope/product change sau qualification/release:

```text
new successor development cycle
```

Prior terminal/candidate/release evidence giữ nguyên.

Result: **PASS**.

## 8. Human authority QA

Human approval:

- có thể authorize confirmatory activation;
- có thể authorize release promotion;
- có thể authorize external/public claim elevation hoặc destructive external effect theo exact payload.

Human không được:

- rewrite adjudicated scientific verdict;
- rescue spent confirmatory evidence;
- giữ QA cũ cho candidate SHA mới;
- biến runtime success thành release/scientific PASS.

Result: **PASS**.

## 9. Provider neutrality QA

Profile definitions không encode:

- RemoteMCP;
- Codex;
- ChatGPT;
- Astra;
- Sol;
- transport-specific execution behavior;
- UI-specific authority.

Provider/model/harness identity sẽ thuộc execution environment/ExecutorBinding phases sau.

Result: **PASS**.

## 10. Domain separation QA

Research dùng:

`domain_id = research.full-cycle`

Software dùng:

`domain_id = software.delivery`

Profile refs giữa hai domain không interchangeable.

Research scientific claim semantics không leak vào software release semantics.

Software acceptance semantics không leak vào research verdict semantics.

Result: **PASS**.

## 11. Negative-test preregistration QA

Machine-readable contract freeze chứa đúng **30** implementation negative tests.

Các test đã được preregister trước mọi P2 implementation.

Result: **PASS**.

## 12. Scope/diff QA

Từ P2 start `148cbc1e8f7a929fae44895576f3d713d6b26efa` đến candidate hiện tại trước QA record, chỉ có:

- `docs/pivot/GWF_VNEXT_P2_DOMAIN_GOVERNANCE_PROFILE_DEFINITIONS_V1.json`;
- `docs/pivot/GWF_VNEXT_P2_DOMAIN_GOVERNANCE_PROFILES_PREREGISTRATION_AND_CONTRACT_FREEZE.md`.

Không đổi:

- `src/`;
- `domains/`;
- `g2e/`;
- `web/`;
- migration/schema;
- RemoteMCP/Codex adapter;
- real project state.

Result: **PASS**.

## 13. Formal disposition

Tất cả P2 contract-freeze criteria đều PASS.

```text
GWF_VNEXT_P2_DOMAIN_GOVERNANCE_PROFILES_PREREGISTRATION_AND_CONTRACT_FREEZE
= PASS
= CONTRACT FROZEN
= FORMALLY CLOSED
```

Đây là PASS về kiến trúc/hợp đồng (architecture/contract) בלבד.

Nó không chứng minh runtime profile implementation đã tồn tại.

## 14. Next authorized frontier

Bước hợp lệ duy nhất tiếp theo:

```text
GWF_VNEXT_P2_DOMAIN_GOVERNANCE_PROFILES_IMPLEMENTATION_STATIC_PREFLIGHT_AND_EXECUTION_LOCK
```

Bước đó mới được phép:

- materialize đúng 8 frozen profile definitions;
- thêm domain-profile binding/lookup cần thiết;
- kiểm exact hash;
- enforce transition conditions;
- enforce triage non-downgrade;
- enforce protected-resource/claim/release firewalls;
- chạy zero-protected-resource fixtures;
- chạy đủ 30 preregistered negative tests;
- bind exact implementation hashes;
- tạo execution lock chỉ sau PASS.

Bước đó vẫn chưa được:

- tích hợp RemoteMCP adapter;
- tích hợp Codex adapter;
- import/merge G2E runtime;
- refactor Mission Control UI;
- chạy real research/software project;
- consume protected confirmatory evidence.
