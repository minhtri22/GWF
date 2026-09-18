# Knowledge Kernel

## 1. Trách nhiệm

Knowledge Kernel quản lý **những gì hệ thống biết và mức độ còn đáng tin của chúng**.

Nó không chạy công việc, không quyết định quyền, không tự ra quyết định workflow. Nó cung cấp graph tri thức có version và validity để các kernel khác sử dụng.

Owner primitives:

- `PRIM-ARTIFACT`
- `PRIM-REVISION`
- `PRIM-TRACE`
- `PRIM-VALIDITY`
- `PRIM-IMPACT`

Cross-kernel dependencies:

- nhận execution evidence từ `PRIM-EVIDENCE` — [Execution Kernel](02-execution-kernel.md);
- nhận failure/recovery directives từ `PRIM-FAILURE`, `PRIM-RECOVERY` — [Decision Kernel](03-decision-kernel.md);
- nhận actor/approval context từ `PRIM-ACTOR`, `PRIM-APPROVAL` — [Governance Kernel](04-governance-kernel.md);
- artifact types và dependency semantics được khai báo bởi `PRIM-DOMAIN` — [Domain Package](05-domain-package.md).

---

## 2. `PRIM-ARTIFACT` — Artifact

Artifact là logical identity lâu dài của một work product.

Ví dụ domain-agnostic:

- một yêu cầu;
- một giả thuyết;
- một dataset;
- một bản thiết kế;
- một kịch bản;
- một báo cáo.

Canonical fields:

```text
artifact_id
project_id
artifact_type
logical_key
created_at
created_by_actor_id
current_revision_id
lifecycle_status
```

Artifact không chứa mutable content trực tiếp. Content nằm trong `PRIM-REVISION`.

Mapping:

- `created_by_actor_id` → `PRIM-ACTOR` ([Governance Kernel](04-governance-kernel.md));
- `artifact_type` → được đăng ký trong `PRIM-DOMAIN` ([Domain Package](05-domain-package.md));
- WorkUnit có thể khai báo Artifact như input/output qua `PRIM-WORKUNIT` ([Execution Kernel](02-execution-kernel.md)).

---

## 3. `PRIM-REVISION` — ArtifactRevision

Revision là snapshot bất biến của Artifact.

```text
revision_id
artifact_id
revision_number
content_ref | structured_payload
content_hash
created_by_actor_id
created_at
supersedes_revision_id?
status
```

Quy tắc:

1. không update content của revision đã persist;
2. thay đổi tạo revision mới;
3. `supersedes_revision_id` tạo lineage lịch sử;
4. approval áp dụng đúng revision/hash, không áp dụng mơ hồ cho artifact logical identity.

Mapping:

- normative revision có thể cần `PRIM-APPROVAL` trước khi trở thành usable ([Governance Kernel](04-governance-kernel.md));
- WorkUnit tạo revision mới phải ghi trong `PRIM-RUN` và `PRIM-AUDIT` ([Execution Kernel](02-execution-kernel.md), [Governance Kernel](04-governance-kernel.md));
- Gate đánh giá exact revision IDs qua `PRIM-GATE` ([Decision Kernel](03-decision-kernel.md)).

---

## 4. `PRIM-TRACE` — TraceLink

TraceLink là cạnh có semantics giữa hai revisions hoặc giữa revision và evidence.

Canonical relation types lõi:

```text
DERIVED_FROM
DEPENDS_ON
VALIDATES
IMPLEMENTS
TESTS
SUPERSEDES
AFFECTS
PRODUCED_BY
```

Domain có thể đăng ký relation type bổ sung nhưng phải khai báo:

- hướng dependency;
- có gây invalidation hay không;
- strength: `HARD | SOFT | INFORMATIONAL`;
- propagation rule.

Ví dụ:

```text
Revision B --DERIVED_FROM--> Revision A
```

Nếu relation là hard dependency và A bị supersede theo rule domain, B có thể chuyển `STALE`.

Mapping:

- `PRODUCED_BY` có thể trỏ tới `PRIM-RUN` ([Execution Kernel](02-execution-kernel.md));
- `VALIDATES` thường gắn `PRIM-EVIDENCE` và được `PRIM-GATE` đọc ([Execution Kernel](02-execution-kernel.md), [Decision Kernel](03-decision-kernel.md));
- invalidation semantics lấy từ `PRIM-DOMAIN` ([Domain Package](05-domain-package.md)).

---

## 5. `PRIM-VALIDITY` — ValidityState

Validity mô tả mức độ còn tin cậy của một revision trong current graph.

```text
VALID
STALE
DIRTY
FAILED
UNVERIFIED
SUPERSEDED
```

### Semantics

**VALID** — revision thỏa dependencies/gates bắt buộc hiện hành.

**STALE** — upstream revision/assumption đã thay đổi; revision chưa được chứng minh còn đúng.

**DIRTY** — đang có mutation/revision mới hoặc downstream evidence chưa cập nhật.

**FAILED** — có authoritative evidence chứng minh revision/claim không thỏa contract.

**UNVERIFIED** — chưa có đủ evidence/gate để xác nhận.

**SUPERSEDED** — revision đã có revision mới thay thế; vẫn được giữ cho provenance.

Validity không được agent ghi trực tiếp. Chỉ `ValidityEngine` của Knowledge Kernel được thay đổi derived validity dựa trên event authoritative.

---

## 6. `PRIM-IMPACT` — ImpactSet

ImpactSet là kết quả tính downstream ảnh hưởng bởi một thay đổi/failure.

```text
impact_id
trigger_type
trigger_id
root_revision_id
affected_nodes[]
reason_codes[]
calculated_at
calculation_policy_version
```

Mỗi affected node cần:

```text
revision_id
action = KEEP | MARK_STALE | MARK_DIRTY | INVALIDATE | RETEST
reason
trace_path
```

`ImpactSet` là input chính để Decision Kernel tạo **RecoveryPlan** (`PRIM-RECOVERY`).

---

## 7. Invalidation propagation

Algorithm khái niệm:

```text
trigger revision/failure
      ↓
traverse outgoing HARD dependency links
      ↓
apply domain invalidation rules
      ↓
produce ImpactSet
      ↓
update derived ValidityState
      ↓
notify Decision + Execution kernels
```

Không phải mọi downstream đều bị regenerate. `TraceLink` và domain rule quyết định node nào giữ nguyên.

Ví dụ:

```text
A1 ─hard→ B1 ─hard→ C1
A1 ─soft→ D1

A1 superseded

B1 = STALE
C1 = STALE
D1 = VALID hoặc DIRTY tùy domain rule
```

---

## 8. Validity frontier

Validity frontier là biên phân tách giữa phần graph còn trusted và phần cần tái xác minh.

```text
VALID upstream
   ↓
[first non-valid node]  ← frontier
   ↓
STALE / DIRTY / FAILED downstream
```

Decision Kernel dùng frontier để xác định candidate resume point. Execution Kernel dùng frontier để biết WorkUnit nào có thể READY trở lại.

Mapping:

- candidate root/resume → `PRIM-FAILURE`, `PRIM-RECOVERY` ([Decision Kernel](03-decision-kernel.md));
- scheduling eligibility → `PRIM-WORKUNIT` ([Execution Kernel](02-execution-kernel.md)).

---

## 9. Read API contract

Tối thiểu:

```text
GetArtifact(artifact_id)
GetRevision(revision_id)
GetCurrentRevision(artifact_id)
GetTraceGraph(root_revision_id, depth)
GetValidity(revision_id)
GetValidityFrontier(scope)
ComputeImpact(trigger)
GetAffectedSubgraph(impact_id)
```

Không API nào được phép mutate revision cũ.

---

## 10. Write contract

Write vào Knowledge Kernel chỉ qua command đã được Execution + Governance kiểm soát:

```text
CreateArtifact(...)
CreateRevision(...)
CreateTraceLink(...)
```

Preconditions:

- `PRIM-ACTOR` hợp lệ;
- `PRIM-AUTHORITY` cho phép;
- nếu policy yêu cầu: `PRIM-APPROVAL` hợp lệ;
- optimistic version/current revision check pass;
- Domain Package chấp nhận artifact/relation type.

Mọi write tạo `PRIM-AUDIT`.

---

## 11. Failure semantics

Knowledge Kernel không tự kết luận root cause. Nó cung cấp:

- graph;
- trace paths;
- current/superseded revisions;
- validity;
- impact candidates.

`PRIM-FAILURE` do Decision Kernel sở hữu.

Nếu Decision Kernel xác định root revision, Knowledge Kernel tính `ImpactSet` và cập nhật derived validity.

---

## 12. Cross-kernel contract matrix

| Knowledge concept | Kernel khác | Mapping bắt buộc |
|---|---|---|
| Revision creator | Governance | `PRIM-ACTOR` |
| Revision approval | Governance | `PRIM-APPROVAL` + exact hash |
| Revision producer | Execution | `PRIM-RUN` via `PRODUCED_BY` |
| Revision validation | Execution/Decision | `PRIM-EVIDENCE` + `PRIM-GATE` |
| Failure root | Decision | `PRIM-FAILURE.root_revision_id` |
| Recovery scope | Decision | `PRIM-RECOVERY` consumes `PRIM-IMPACT` |
| Resume eligibility | Execution | validity frontier → `PRIM-WORKUNIT` readiness |
| Artifact vocabulary | Domain | `PRIM-DOMAIN.artifact_types` |

---

## 13. Acceptance criteria

Knowledge Kernel đạt v0.1 khi:

1. revision bất biến được enforce;
2. trace graph queryable hai chiều;
3. upstream supersede có thể tạo deterministic ImpactSet;
4. validity không thể bị agent ghi trực tiếp;
5. mọi revision biết creator và provenance;
6. mọi hard dependency có invalidation rule;
7. Decision Kernel có đủ dữ liệu để tìm root/resume mà không cần transcript.

