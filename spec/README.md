# Governed Workflow Runtime v0.1

## 1. Mục tiêu

Governed Workflow Runtime (GWR) là một runtime tổng quát cho công việc nhiều bước, nhiều tác nhân, có bằng chứng, có kiểm soát quyền, có kiểm định, có lỗi, có phục hồi và có thể tiếp tục chính xác từ trạng thái đã biết.

Hệ thống không giả định một domain cụ thể. Một domain chỉ cung cấp vocabulary, artifact types, work-unit templates, gate rules và policy bổ sung thông qua **Domain Package**. Runtime lõi giữ nguyên.

Mục tiêu chính:

- duy trì **source of truth bền vững** ngoài hội thoại;
- biết artifact nào đang `VALID`, `STALE`, `DIRTY`, `FAILED`, `UNVERIFIED` hoặc `SUPERSEDED`;
- biết công việc nào có thể chạy, đang chạy, bị block hay cần phục hồi;
- phân biệt **điểm phát hiện lỗi**, **nguyên nhân gốc**, **điểm resume**;
- buộc quyết định quan trọng phải dựa trên evidence và gate;
- tách execution authority khỏi model/agent cụ thể;
- checkpoint và resume mà không cần replay toàn bộ lịch sử;
- hỗ trợ nhiều domain bằng mapping, không fork runtime.

---

## 2. Bốn kernel và một Domain Package

```text
┌─────────────────────────────────────────────┐
│               Domain Package                │
│ terminology · types · templates · policies │
└─────────────────────────────────────────────┘
                     │ maps to
                     ▼
┌─────────────────────────────────────────────┐
│ Knowledge Kernel                            │
│ artifacts · revisions · traceability       │
│ validity · dependency impact                │
├─────────────────────────────────────────────┤
│ Execution Kernel                            │
│ work units · runs · checkpoints · resume   │
│ retry · concurrency · execution evidence    │
├─────────────────────────────────────────────┤
│ Decision Kernel                             │
│ gates · decisions · failure diagnosis      │
│ recovery plans · loop guards                │
├─────────────────────────────────────────────┤
│ Governance Kernel                           │
│ actors · authority · approval · audit       │
│ policy enforcement                          │
└─────────────────────────────────────────────┘
```

Tài liệu chi tiết:

- [Knowledge Kernel](01-knowledge-kernel.md)
- [Execution Kernel](02-execution-kernel.md)
- [Decision Kernel](03-decision-kernel.md)
- [Governance Kernel](04-governance-kernel.md)
- [Domain Package](05-domain-package.md)
- [QA Report](QA_REPORT.md)

---

## 3. Canonical primitive registry

Mọi tài liệu phải dùng đúng ID và ownership dưới đây. Khi một tài liệu đề cập primitive thuộc kernel khác, tài liệu đó phải trỏ tới owner tương ứng.

| ID | Primitive | Owner | Mô tả ngắn |
|---|---|---|---|
| `PRIM-ARTIFACT` | Artifact | Knowledge | Đơn vị tri thức/work product có định danh |
| `PRIM-REVISION` | ArtifactRevision | Knowledge | Phiên bản bất biến của Artifact |
| `PRIM-TRACE` | TraceLink | Knowledge | Quan hệ dependency/derivation giữa revisions |
| `PRIM-VALIDITY` | ValidityState | Knowledge | Trạng thái tin cậy của revision |
| `PRIM-IMPACT` | ImpactSet | Knowledge | Tập downstream bị ảnh hưởng bởi thay đổi/lỗi |
| `PRIM-WORKUNIT` | WorkUnit | Execution | Đơn vị thực thi có contract |
| `PRIM-RUN` | ExecutionRun | Execution | Một lần thực thi WorkUnit |
| `PRIM-CHECKPOINT` | Checkpoint | Execution | Snapshot phục vụ resume |
| `PRIM-EVIDENCE` | Evidence | Execution | Bằng chứng được tạo bởi execution/tool/human |
| `PRIM-GATE` | Gate | Decision | Hàm đánh giá điều kiện để đi tiếp |
| `PRIM-DECISION` | Decision | Decision | Kết quả điều hướng runtime |
| `PRIM-FAILURE` | FailureRecord | Decision | Bản ghi lỗi đã được chuẩn hoá |
| `PRIM-RECOVERY` | RecoveryPlan | Decision | Kế hoạch quay lại và tái lập validity |
| `PRIM-LOOPGUARD` | LoopGuard | Decision | Chống retry/refine vô hạn |
| `PRIM-ACTOR` | Actor | Governance | Human, agent, service hoặc system identity |
| `PRIM-AUTHORITY` | AuthorityPolicy | Governance | Quyền được phép thực hiện hành động |
| `PRIM-APPROVAL` | Approval | Governance | Xác nhận có thẩm quyền cho thay đổi/transition |
| `PRIM-AUDIT` | AuditEvent | Governance | Ledger append-only của hành động hệ thống |
| `PRIM-DOMAIN` | DomainPackage | Domain Package | Mapping domain vào primitive lõi |

---

## 4. Invariants toàn hệ thống

### INV-01 — Revision bất biến

Một `PRIM-REVISION` đã được persist không bị sửa tại chỗ. Thay đổi tạo revision mới và liên kết `supersedes`.

### INV-02 — Không có hidden write

Mọi mutation đều phải đi qua Execution + Governance contract. Model hoặc tool không được ghi trực tiếp persistence ngoài runtime.

### INV-03 — Detection ≠ root cause ≠ resume

`PRIM-FAILURE` phải tách:

- nơi phát hiện;
- nguyên nhân gốc đã xác định/chấp nhận;
- điểm resume.

### INV-04 — Validity được tính từ graph

`PRIM-VALIDITY` không được agent tự gán tuỳ ý. Nó được suy ra từ revision, dependency, gate/evidence và invalidation rules.

### INV-05 — Gate không tin lời tự báo cáo

`PRIM-GATE` chỉ sử dụng state authoritative và `PRIM-EVIDENCE` được runtime chấp nhận.

### INV-06 — Resume từ checkpoint + current truth

Resume không replay transcript. `PRIM-CHECKPOINT` được hydrate cùng current artifact graph và pending governance state.

### INV-07 — Domain không được phá invariants lõi

`PRIM-DOMAIN` có thể mở rộng types/rules/templates nhưng không thể vô hiệu hoá revision immutability, authority enforcement, audit, gate evidence hoặc consistency rules.

### INV-08 — Audit append-only

Mọi transition quan trọng tạo `PRIM-AUDIT`. Audit không dùng làm source of truth nghiệp vụ nhưng là provenance bắt buộc.

---

## 5. Lifecycle tổng quát

```text
Goal
  ↓
Domain Package materializes required artifact/work-unit types
  ↓
Artifacts + revisions enter Knowledge Kernel
  ↓
Execution Kernel schedules eligible WorkUnits
  ↓
Execution produces Evidence
  ↓
Decision Kernel evaluates Gates
  ├─ PASS → next eligible WorkUnit
  ├─ BLOCKED → wait for dependency/approval/evidence
  └─ FAIL → FailureRecord
                ↓
          diagnosis / root cause
                ↓
           RecoveryPlan
                ↓
       Knowledge invalidation
                ↓
           new Checkpoint
                ↓
              resume
```

Governance Kernel bao quanh toàn flow: xác thực Actor, kiểm tra Authority, quản lý Approval và ghi AuditEvent.

---

## 6. Canonical state vocabularies

### Artifact validity

```text
VALID
STALE
DIRTY
FAILED
UNVERIFIED
SUPERSEDED
```

### WorkUnit execution

```text
PENDING
READY
RUNNING
BLOCKED
SUCCEEDED
RECOVERY
CANCELLED
```

### Gate result

```text
PASS
FAIL
BLOCKED
STALE
```

### Decision

```text
CONTINUE
RETRY
REVISE_CURRENT
REVISE_UPSTREAM
REPLAN
ESCALATE
ABORT
WAIT
```

Các state này là vocabulary lõi; domain có thể thêm reason codes nhưng không được đổi semantics.

---

## 7. Điều không thuộc core

Core không quyết định:

- tên cụ thể của artifact trong từng ngành;
- số lượng agent;
- model/provider nào được dùng;
- UI/IDE cụ thể;
- database engine cụ thể;
- CI/test tool cụ thể;
- format tài liệu cụ thể.

Các quyết định đó nằm ở Domain Package hoặc adapter layer.

---

## 8. Definition of Done cho runtime v0.1

Runtime v0.1 đạt mức implementation-ready khi:

1. mọi primitive trong registry có schema và owner duy nhất;
2. mọi cross-kernel reference có contract hai chiều rõ;
3. thay đổi upstream có thể tạo `ImpactSet` và invalidation downstream;
4. failure có thể tạo `RecoveryPlan` và checkpoint resume;
5. WorkUnit không chạy khi gate/authority chưa thoả;
6. normative mutation không thể bypass Approval khi policy yêu cầu;
7. retry/refine loop có budget và signature;
8. crash/restart không làm mất authoritative state;
9. Domain Package có thể thêm một domain mới mà không sửa source core;
10. audit có thể truy ngược ai/điều gì/tại sao đã thay đổi state.

