# QA Report — Governed Workflow Runtime v0.1

## 1. Phạm vi QA

QA tập trung vào yêu cầu: tài liệu không gãy và không mất/thiếu mapping giữa các kernel/Domain Package.

Đã kiểm tra:

1. tồn tại đủ tài liệu bắt buộc;
2. README không chứa các tên nguồn cảm hứng bị loại khỏi README;
3. tất cả local Markdown links trỏ tới file tồn tại;
4. mọi `PRIM-*` reference đều thuộc canonical primitive registry;
5. mỗi primitive có đúng owner document;
6. mỗi kernel document có cross-kernel mapping section;
7. khi một kernel document dùng primitive do kernel khác sở hữu, tài liệu có link tới owner document;
8. Domain Package có mapping tới tất cả primitive families;
9. các contract quan trọng về validity, checkpoint/resume, failure/root/resume, frozen approval và package validation đều hiện diện;
10. README registry chứa đầy đủ canonical primitives.

---

## 2. Kết quả tự động

Validator: `tools/qa_validate.py`

```text
GWR documentation QA
====================
Files checked: 6
Primitive registry entries: 19
Primitive refs found: 19
Errors: 0
Warnings: 0

RESULT: PASS
```

---

## 3. Cross-document integrity

### Knowledge → các kernel khác

PASS:

- Revision creator/approval map sang Governance.
- Revision producer/evidence map sang Execution.
- Failure root/recovery map sang Decision.
- Artifact vocabulary/invalidation semantics map sang Domain Package.

### Execution → các kernel khác

PASS:

- WorkUnit inputs/outputs pin exact Knowledge revisions.
- Readiness dùng Knowledge validity + Decision gates.
- Executor/permission dùng Governance Actor/Authority.
- Recovery/resume dùng Decision RecoveryPlan + Knowledge ImpactSet.
- Template/evidence vocabulary map sang Domain Package.

### Decision → các kernel khác

PASS:

- Gate pin Knowledge revisions và Execution evidence.
- Failure trace dùng Knowledge TraceLink.
- Recovery consumes Knowledge ImpactSet và schedules Execution WorkUnits.
- Authority/approval/escalation map sang Governance.
- Failure taxonomy/gate templates map sang Domain Package.

### Governance → các kernel khác

PASS:

- Resource scope pin Knowledge artifacts/revisions.
- Executor permission pin Execution WorkUnit/Run.
- Gate authority và recovery approval pin Decision constructs.
- Roles/approval classes map sang Domain Package.
- Audit correlation có thể nối revision/run/decision/proposal/approval.

### Domain Package → bốn kernel

PASS:

- Knowledge: Artifact, Revision, Trace, Validity, Impact.
- Execution: WorkUnit, Run, Evidence, Checkpoint.
- Decision: Gate, Decision, Failure, Recovery, LoopGuard.
- Governance: Actor, Authority, Approval, Audit.

Không có primitive domain-specific nào âm thầm thay thế primitive lõi.

---

## 4. Semantic consistency checks

### 4.1 Failure semantics

PASS: các tài liệu thống nhất rằng:

```text
Detection Point != Root Cause Point != Resume Point
```

Knowledge cung cấp graph/validity; Decision xác định root/recovery; Execution thực thi resume; Governance kiểm tra authority.

### 4.2 Resume semantics

PASS: resume không dựa vào transcript hoặc chỉ `stage N`.

Canonical flow thống nhất:

```text
FailureRecord
→ root diagnosis
→ ImpactSet
→ RecoveryPlan
→ validity update
→ Checkpoint
→ recompute READY WorkUnits
→ resume affected subgraph
```

### 4.3 Authority semantics

PASS: agent persona/role prompt không phải authority boundary.

Normative mutation có thể yêu cầu frozen proposal + hash + Approval; payload thay đổi làm approval mất hiệu lực.

### 4.4 Evidence semantics

PASS: runtime/process success không đồng nghĩa WorkUnit/business success. Decision Gate đánh giá authoritative evidence trên exact revisions.

### 4.5 Version/validity semantics

PASS: revision immutable; upstream change có thể propagate `STALE/DIRTY/FAILED`; downstream được tái tạo theo ImpactSet thay vì overwrite lịch sử.

### 4.6 Domain extension semantics

PASS: Domain Package chỉ cấu hình vocabulary/types/templates/policies; không được phá core invariants hoặc sở hữu canonical runtime state.

---

## 5. Primitive ownership audit

| Owner | Primitives | Status |
|---|---|---|
| Knowledge Kernel | `PRIM-ARTIFACT`, `PRIM-REVISION`, `PRIM-TRACE`, `PRIM-VALIDITY`, `PRIM-IMPACT` | PASS |
| Execution Kernel | `PRIM-WORKUNIT`, `PRIM-RUN`, `PRIM-CHECKPOINT`, `PRIM-EVIDENCE` | PASS |
| Decision Kernel | `PRIM-GATE`, `PRIM-DECISION`, `PRIM-FAILURE`, `PRIM-RECOVERY`, `PRIM-LOOPGUARD` | PASS |
| Governance Kernel | `PRIM-ACTOR`, `PRIM-AUTHORITY`, `PRIM-APPROVAL`, `PRIM-AUDIT` | PASS |
| Domain Package | `PRIM-DOMAIN` | PASS |

Không phát hiện primitive có hai owner hoặc reference không có owner.

---

## 6. Những thứ cố ý chưa khóa ở v0.1

Các điểm sau được để mở có chủ đích, không phải mapping bị thiếu:

- database engine và physical schema;
- event bus/transport protocol;
- concrete API wire format;
- UI/IDE integration;
- scheduler implementation;
- distributed locking strategy;
- package signing/distribution;
- domain cụ thể;
- model/provider cụ thể.

Chúng thuộc implementation phase sau khi core runtime model được chấp nhận.

---

## 7. QA verdict

**PASS — internally consistent at specification-model level.**

Không phát hiện:

- broken local document link;
- unregistered primitive;
- missing primitive owner;
- foreign primitive reference không có owner mapping;
- Domain Package thiếu primitive family;
- conflict trực tiếp giữa failure/resume/authority/version semantics của các tài liệu.

Bộ tài liệu hiện phù hợp để làm input cho bước kế tiếp: runtime schemas, event contracts, persistence model và executable P0 acceptance tests.
