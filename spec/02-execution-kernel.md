# Execution Kernel

## 1. Trách nhiệm

Execution Kernel quản lý **công việc nào được chạy, chạy như thế nào, bằng ai/tool nào, tạo evidence gì, checkpoint ở đâu và resume ra sao**.

Nó không định nghĩa artifact semantics, không tự quyết định gate pass/fail và không cấp authority.

Owner primitives:

- `PRIM-WORKUNIT`
- `PRIM-RUN`
- `PRIM-CHECKPOINT`
- `PRIM-EVIDENCE`

Cross-kernel dependencies:

- inputs/outputs là `PRIM-ARTIFACT`/`PRIM-REVISION` — [Knowledge Kernel](01-knowledge-kernel.md);
- readiness phụ thuộc `PRIM-GATE`, `PRIM-DECISION`, `PRIM-RECOVERY` — [Decision Kernel](03-decision-kernel.md);
- executor và quyền gọi tool phụ thuộc `PRIM-ACTOR`, `PRIM-AUTHORITY`, `PRIM-APPROVAL` — [Governance Kernel](04-governance-kernel.md);
- templates, executor types và evidence requirements đến từ `PRIM-DOMAIN` — [Domain Package](05-domain-package.md).

---

## 2. `PRIM-WORKUNIT` — WorkUnit

WorkUnit là đơn vị thực thi nhỏ nhất có contract đầy đủ.

```text
workunit_id
workunit_type
project_id
input_requirements[]
output_contracts[]
preconditions[]
required_gates[]
required_authorities[]
executor_selector
execution_policy
retry_policy
recovery_policy
status
```

Canonical status:

```text
PENDING
READY
RUNNING
BLOCKED
SUCCEEDED
RECOVERY
CANCELLED
```

### WorkUnit contract

Mỗi WorkUnit phải khai báo:

```text
Inputs
Outputs
Preconditions
Executor
Authority
Evidence required
Success conditions
Known failure modes
Retry budget
Recovery hints
Idempotency semantics
```

Không WorkUnit nào được chuyển `READY` nếu input revision không ở validity phù hợp hoặc required gate chưa `PASS`.

---

## 3. `PRIM-RUN` — ExecutionRun

ExecutionRun là một lần cụ thể chạy WorkUnit.

```text
run_id
workunit_id
attempt_number
executor_actor_id
input_revision_ids[]
started_at
finished_at
runtime_status
exit_metadata
produced_revision_ids[]
evidence_ids[]
checkpoint_id?
correlation_id
```

`runtime_status` không đồng nghĩa business success.

Ví dụ:

```text
process exit 0
```

chỉ là runtime fact. Success của WorkUnit vẫn phải được `PRIM-GATE` đánh giá trên evidence và outputs.

Mapping:

- `input_revision_ids` → Knowledge Kernel;
- `executor_actor_id` → Governance Kernel;
- `evidence_ids` → `PRIM-EVIDENCE` trong chính Execution Kernel;
- gate result → Decision Kernel.

---

## 4. `PRIM-EVIDENCE` — Evidence

Evidence là bằng chứng có provenance dùng bởi Gate hoặc audit.

```text
evidence_id
evidence_type
producer_run_id?
producer_actor_id
subject_refs[]
payload_ref | structured_payload
content_hash
created_at
freshness_metadata
trust_class
```

Ví dụ evidence domain-agnostic:

- command result;
- test result;
- build artifact;
- measurement;
- human observation;
- signed approval receipt;
- external validation response.

Evidence classes:

```text
AUTHORITATIVE
SUPPORTED
ADVISORY
UNTRUSTED
```

Gate chỉ được dùng class mà policy cho phép.

---

## 5. `PRIM-CHECKPOINT` — Checkpoint

Checkpoint là snapshot đủ để resume mà không cần replay transcript.

```text
checkpoint_id
project_id
scope_id
created_at
last_event_id
active_workunit_ids[]
completed_workunit_ids[]
current_stage_labels[]
valid_revision_ids[]
dirty_revision_ids[]
stale_revision_ids[]
blocking_failure_ids[]
pending_decision_ids[]
pending_approval_ids[]
resume_candidates[]
runtime_metadata
```

Checkpoint không đóng băng toàn DB; khi resume phải reconcile với current truth.

### Resume rule

```text
checkpoint
  + current Knowledge graph
  + current Decision state
  + current Governance state
  ↓
reconciled resume plan
```

Nếu checkpoint cũ xung đột current revisions, current truth thắng và Decision Kernel phải tái tính route.

---

## 6. Scheduling eligibility

WorkUnit `READY` khi tất cả điều kiện sau đúng:

```text
required input revisions exist
required validity states acceptable
required gates PASS
required approvals valid
required authority available
no blocking failure
no active conflicting run
```

Execution Kernel không tự tính validity/gate/authority; nó query owner kernel tương ứng.

---

## 7. Retry model

Retry chỉ hợp lệ khi failure classification cho phép.

```text
same WorkUnit
same semantic inputs
new ExecutionRun
attempt_number + 1
```

Retry policy fields:

```text
max_attempts
backoff
retryable_failure_codes[]
same_signature_limit
require_new_evidence
```

Nếu semantic inputs thay đổi, đó không còn là retry; đó là run mới sau revision/recovery.

Decision Kernel sở hữu `PRIM-LOOPGUARD` và có thể chặn retry.

---

## 8. Concurrency và idempotency

Mọi mutating execution command cần:

```text
idempotency_key
expected_revision_or_version
correlation_id
```

Rules:

- cùng `idempotency_key` + cùng payload → trả cùng kết quả;
- cùng key + payload khác → `IDEMPOTENCY_CONFLICT`;
- stale expected version → `STALE_VERSION`;
- WorkUnits xung đột cùng resource key không chạy đồng thời trừ khi domain cho phép.

Domain Package định nghĩa `resource_conflict_keys` nếu cần.

---

## 9. Runtime failure vs semantic failure

### Runtime failure

Ví dụ:

```text
tool unavailable
timeout
process crash
network failure
```

Có thể retry trực tiếp nếu policy cho phép.

### Semantic failure

Ví dụ:

```text
output violates contract
evidence contradicts expected behavior
input assumption invalid
```

Phải tạo `PRIM-FAILURE` ở Decision Kernel.

Execution Kernel không tự map mọi non-zero exit thành root cause nghiệp vụ.

---

## 10. Resume semantics

Resume target không nhất thiết là WorkUnit ngay trước WorkUnit fail.

Flow:

```text
FailureRecord
    ↓
RecoveryPlan
    ↓
Knowledge ImpactSet + validity update
    ↓
Checkpoint
    ↓
recompute READY WorkUnits
    ↓
resume selected subgraph
```

Ví dụ:

```text
WU-5 verification fails
root cause = upstream artifact revision
RecoveryPlan invalidates outputs of WU-3..WU-5 selectively
resume = WU-3 replacement path
```

Execution Kernel chỉ thi hành RecoveryPlan đã hợp lệ.

---

## 11. Execution events

Tối thiểu:

```text
WORKUNIT_READY
RUN_STARTED
RUN_HEARTBEAT
RUN_SUCCEEDED_RUNTIME
RUN_FAILED_RUNTIME
EVIDENCE_RECORDED
CHECKPOINT_CREATED
RUN_CANCELLED
RESUME_STARTED
RESUME_COMPLETED
```

Mọi event quan trọng tạo `PRIM-AUDIT` hoặc correlation tới AuditEvent.

---

## 12. API contract

```text
CreateWorkUnit(template, bindings)
GetReadyWorkUnits(scope)
StartRun(workunit_id, executor_actor_id, idempotency_key)
RecordEvidence(run_id, evidence)
FinishRun(run_id, runtime_result)
CreateCheckpoint(scope)
ResumeFromCheckpoint(checkpoint_id)
CancelRun(run_id, reason)
GetExecutionStatus(scope)
```

`FinishRun(... runtime_result=success)` không tự chuyển business state sang confirmed; Decision Kernel phải đánh giá gate.

---

## 13. Cross-kernel contract matrix

| Execution concept | Kernel khác | Mapping bắt buộc |
|---|---|---|
| WorkUnit input/output | Knowledge | exact `PRIM-REVISION` IDs |
| WorkUnit readiness | Knowledge/Decision | `PRIM-VALIDITY` + `PRIM-GATE` |
| Executor | Governance | `PRIM-ACTOR` |
| Tool permission | Governance | `PRIM-AUTHORITY` |
| Normative start/transition | Governance | `PRIM-APPROVAL` khi policy yêu cầu |
| Run failure | Decision | tạo candidate `PRIM-FAILURE` |
| Resume | Decision/Knowledge | `PRIM-RECOVERY` + `PRIM-IMPACT` |
| Evidence consumer | Decision | `PRIM-GATE` |
| WorkUnit template | Domain | `PRIM-DOMAIN.workunit_templates` |

---

## 14. Acceptance criteria

Execution Kernel đạt v0.1 khi:

1. process success không thể bypass semantic gate;
2. WorkUnit không chạy với stale required inputs;
3. crash/restart có thể resume từ checkpoint;
4. retry phân biệt được runtime failure và semantic failure;
5. stale writer bị chặn;
6. duplicate command idempotent;
7. RecoveryPlan có thể resume một subgraph thay vì chạy lại toàn workflow;
8. mọi run/evidence có provenance đầy đủ.

