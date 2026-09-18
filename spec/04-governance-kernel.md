# Governance Kernel

## 1. Trách nhiệm

Governance Kernel quản lý **ai là ai, ai được làm gì, thay đổi nào cần approval và mọi hành động quan trọng được audit như thế nào**.

Owner primitives:

- `PRIM-ACTOR`
- `PRIM-AUTHORITY`
- `PRIM-APPROVAL`
- `PRIM-AUDIT`

Cross-kernel dependencies:

- authority scope thường trỏ tới Artifact/Revision từ [Knowledge Kernel](01-knowledge-kernel.md);
- executor actions và runtime commands đến từ [Execution Kernel](02-execution-kernel.md);
- gate/decision/escalation cần governance check từ [Decision Kernel](03-decision-kernel.md);
- roles, policy bundles và approval classes được khai báo bởi [Domain Package](05-domain-package.md).

---

## 2. `PRIM-ACTOR` — Actor

Actor là identity có thể thực hiện hành động.

```text
actor_id
actor_type = HUMAN | AGENT | SERVICE | SYSTEM
principal_id
role_bindings[]
project_scope[]
status
identity_metadata
```

Agent persona không đồng nghĩa authority. Authority luôn được tính từ actor identity + policy + scope.

---

## 3. `PRIM-AUTHORITY` — AuthorityPolicy

AuthorityPolicy xác định actor có được phép gọi một command hoặc tạo một loại mutation hay không.

```text
policy_id
policy_version
subject_selector
resource_selector
actions[]
conditions[]
effect = ALLOW | DENY
priority
```

Actions ví dụ:

```text
READ
PROPOSE
EXECUTE
CREATE_REVISION
APPROVE
CONFIRM
CANCEL
ESCALATE
```

Quy tắc:

- deny có ưu tiên an toàn;
- role prompt không phải security boundary;
- policy được enforce server-side trước mutation/tool execution.

---

## 4. Normative vs evidentiary mutation

### Normative mutation

Thay đổi thứ mà downstream phải tuân theo.

Ví dụ domain-agnostic:

- requirement/rule;
- design/specification;
- baseline;
- plan;
- policy.

Có thể yêu cầu `PRIM-APPROVAL` trước commit.

### Evidentiary mutation

Ghi lại điều đã xảy ra:

- test result;
- run result;
- measurement;
- worklog;
- tool output.

Có thể cho agent/service ghi trực tiếp nếu có authority, nhưng record phải immutable/audited.

Domain Package phân loại mutation class cho artifact/action cụ thể.

---

## 5. `PRIM-APPROVAL` — Approval

Approval là quyết định có thẩm quyền cho một **frozen proposal**, không phải boolean do agent tự truyền.

Canonical flow:

```text
prepare proposal
      ↓
freeze payload + hash
      ↓
human/authorized actor sees exact diff
      ↓
approve proposal_id + hash
      ↓
commit exact frozen payload
```

Fields:

```text
approval_id
proposal_id
proposal_hash
approver_actor_id
decision = APPROVED | REJECTED | EXPIRED | REVOKED
scope
created_at
expires_at?
conditions?
```

Nếu payload thay đổi, approval cũ không còn hợp lệ.

---

## 6. Proposal contract

Dù Proposal không phải canonical primitive riêng, Governance Kernel quản lý lifecycle của proposal cho normative mutation.

```text
proposal_id
proposer_actor_id
action
resource_refs[]
frozen_payload
payload_hash
required_approval_policy
status
created_at
```

Status:

```text
DRAFT
PENDING_APPROVAL
APPROVED
REJECTED
COMMITTED
EXPIRED
```

Commit phải idempotent và exact-match payload hash.

---

## 7. `PRIM-AUDIT` — AuditEvent

AuditEvent là append-only ledger.

```text
event_id
project_id
actor_id
action
resource_type
resource_id
before_version?
after_version?
proposal_id?
approval_id?
run_id?
decision_id?
correlation_id
reason_code
timestamp
metadata_hash
```

AuditEvent không thay thế domain state. Nó trả lời:

- ai;
- làm gì;
- lên resource nào;
- từ version nào sang version nào;
- dưới approval/decision/run nào;
- khi nào.

---

## 8. Authority checks trong runtime

### Knowledge write

Trước `CreateRevision`:

```text
Actor authenticated
Authority allows CREATE_REVISION
Domain rule accepts artifact type
Approval valid if normative policy requires
expected current revision matches
```

### Execution start

Trước `StartRun`:

```text
Actor authorized as executor
WorkUnit READY
required approvals valid
resource conflict policy pass
```

### Decision escalation/confirmation

Trước high-impact `REPLAN`, `ABORT`, final confirmation:

```text
Actor has required authority
Decision target matches scope
Approval policy satisfied
```

---

## 9. Separation of duties

Domain có thể yêu cầu actor khác nhau cho:

```text
PROPOSE ≠ APPROVE
EXECUTE ≠ CONFIRM
AUTHOR ≠ VALIDATE
```

Core phải hỗ trợ separation-of-duties rule nhưng không bắt buộc cho mọi domain.

Ví dụ policy:

```text
same actor cannot approve own high-impact proposal
```

---

## 10. Escalation

Decision Kernel có thể tạo `ESCALATE` nhưng Governance Kernel quyết định actor/role nào hợp lệ để nhận.

```text
failure severity HIGH
    ↓
Decision = ESCALATE
    ↓
Governance resolves escalation target
    ↓
pending action assigned to authorized Actor
```

Nếu không có actor đủ quyền, trạng thái phải `BLOCKED`, không bypass.

---

## 11. API contract

```text
AuthenticateActor(...)
Authorize(actor_id, action, resource)
PrepareProposal(...)
ApproveProposal(proposal_id, approver_actor_id, expected_hash)
RejectProposal(...)
CommitApprovedProposal(...)
GetPendingApprovals(scope)
AppendAuditEvent(event)
QueryAudit(scope, filters)
ResolveEscalationTarget(scope, requirement)
```

Approval action không nên được exposed cho cùng untrusted model channel dùng để tạo proposal nếu không có trusted human confirmation boundary.

---

## 12. Cross-kernel contract matrix

| Governance concept | Kernel khác | Mapping bắt buộc |
|---|---|---|
| Resource scope | Knowledge | `PRIM-ARTIFACT` / `PRIM-REVISION` |
| Executor permission | Execution | `PRIM-WORKUNIT` / `PRIM-RUN` |
| Evidence producer identity | Execution | `PRIM-EVIDENCE.producer_actor_id` |
| Gate authority precondition | Decision | `PRIM-GATE` reads authority/approval state |
| Escalation | Decision | `PRIM-DECISION=ESCALATE` → authorized Actor |
| Recovery approval | Decision | high-impact `PRIM-RECOVERY` may require Approval |
| Role vocabulary | Domain | `PRIM-DOMAIN.roles` |
| Approval classes | Domain | `PRIM-DOMAIN.approval_policies` |
| Audit correlation | All | revision/run/decision IDs |

---

## 13. Security invariants

1. Agent-provided `approved=true` không có authority.
2. Approval pin proposal hash.
3. Tool permission server-side.
4. Audit append-only.
5. Identity của human/agent tách biệt.
6. Normative mutation có thể yêu cầu explicit human boundary.
7. Policy version được lưu cùng decision/approval để replay audit.

---

## 14. Acceptance criteria

Governance Kernel đạt v0.1 khi:

1. actor không thể tự nâng quyền qua prompt/payload;
2. approved payload bị sửa sẽ bị reject;
3. high-impact normative mutation có thể bắt buộc human approval;
4. every important mutation có AuditEvent;
5. separation-of-duties policy enforce được;
6. escalation không có authorized target sẽ BLOCKED;
7. audit có thể reconstruct chuỗi proposal → approval → mutation → gate/decision.

