# Decision Kernel

## 1. Trách nhiệm

Decision Kernel quản lý **hệ thống có được đi tiếp hay không, lỗi nghĩa là gì, cần quay lại đâu và làm sao tránh loop vô hạn**.

Nó không sở hữu artifact, không trực tiếp chạy tool và không cấp quyền.

Owner primitives:

- `PRIM-GATE`
- `PRIM-DECISION`
- `PRIM-FAILURE`
- `PRIM-RECOVERY`
- `PRIM-LOOPGUARD`

Cross-kernel dependencies:

- đọc graph/validity/impact từ [Knowledge Kernel](01-knowledge-kernel.md);
- đọc evidence/run/checkpoint từ [Execution Kernel](02-execution-kernel.md);
- đọc actor/authority/approval từ [Governance Kernel](04-governance-kernel.md);
- gate types, failure taxonomy và recovery policies từ [Domain Package](05-domain-package.md).

---

## 2. `PRIM-GATE` — Gate

Gate là hàm deterministic hoặc policy-controlled đánh giá state/evidence.

```text
gate_id
gate_type
scope
required_inputs[]
required_evidence[]
policy_version
result
violation_codes[]
evaluated_refs[]
evaluated_at
```

Canonical result:

```text
PASS
FAIL
BLOCKED
STALE
```

### Semantics

**PASS** — đủ điều kiện đi tiếp.

**FAIL** — có evidence/state chứng minh contract không đạt.

**BLOCKED** — chưa thể đánh giá vì thiếu prerequisite/evidence/approval.

**STALE** — gate từng pass nhưng input revision đã thay đổi; cần re-evaluate.

Gate phải pin exact revision/evidence IDs đã đánh giá.

---

## 3. Gate composition

Gate có thể phụ thuộc gate khác:

```text
ReadinessGate =
  InputValidityGate
  AND AuthorityGate
  AND RequiredEvidenceGate
```

Composition phải tạo explainable violations, không chỉ boolean.

Ví dụ:

```json
{
  "result": "BLOCKED",
  "violations": [
    "INPUT_REVISION_STALE",
    "APPROVAL_MISSING"
  ]
}
```

`APPROVAL_MISSING` map tới `PRIM-APPROVAL` của Governance Kernel.

---

## 4. `PRIM-DECISION` — Decision

Decision là output điều hướng workflow.

```text
decision_id
scope
source_gate_ids[]
source_failure_id?
decision_type
target_ref?
reason_codes[]
created_at
created_by = SYSTEM | POLICY | HUMAN_AUTHORIZED
```

Canonical types:

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

Decision không được suy ra từ keyword tự do trong text. Nếu có model tham gia, model chỉ tạo structured proposal phải validate schema/policy trước khi trở thành Decision authoritative.

---

## 5. `PRIM-FAILURE` — FailureRecord

FailureRecord tách ba khái niệm:

```text
detected_at
root_cause
resume_target
```

Canonical fields:

```text
failure_id
scope_id
failure_class
detected_stage
detected_ref
detected_revision_id?
failed_gate_id?
evidence_ids[]
root_ref?
root_revision_id?
root_status = UNKNOWN | PROPOSED | CONFIRMED
resume_candidate?
severity
signature
status
created_at
resolved_at?
```

Failure signature được dùng cho loop detection:

```text
hash(
  failure_class,
  failed_gate_type,
  root_ref_or_detected_ref,
  normalized_violation_codes,
  stable_evidence_fingerprint
)
```

---

## 6. Root-cause localization

Decision Kernel phải phân biệt:

```text
Detection Point
Root Cause Point
Resume Point
```

### Deterministic routing trước

Ví dụ default core rules:

```text
TOOL_TIMEOUT          → RETRY current WorkUnit
STALE_INPUT           → first stale ancestor
AUTHORITY_DENIED      → ESCALATE/WAIT
APPROVAL_MISSING      → WAIT
MISSING_EVIDENCE      → WAIT or rerun evidence-producing WorkUnit
CONTRACT_MISMATCH     → analyze trace graph
```

### Ambiguous routing sau

Nếu không đủ rule deterministic, Decision Kernel có thể yêu cầu diagnosis proposal từ agent/human nhưng output phải structured:

```text
proposed_root_ref
supporting_evidence[]
contradicting_evidence[]
confidence_band
recommended_decision
```

Policy quyết định khi nào proposal cần human confirmation.

---

## 7. Earliest Invalid Ancestor

Candidate resume point ưu tiên node sớm nhất trong dependency path được xác định là invalid nhưng không vượt quá phạm vi cần thiết.

Khái niệm:

```text
failure detected downstream
      ↓
trace upstream
      ↓
find earliest node whose contract is invalid
      ↓
keep all trusted ancestors
      ↓
invalidate affected descendants
```

Không được mặc định “test fail → sửa code”.

Knowledge Kernel cung cấp graph/validity; Decision Kernel chọn root/resume theo policy và evidence.

---

## 8. `PRIM-RECOVERY` — RecoveryPlan

RecoveryPlan materialize hành động cần thiết để trở lại một trạng thái có thể tiến tiếp.

```text
recovery_id
failure_id
root_ref
resume_target
keep_valid_refs[]
invalidate_refs[]
mark_stale_refs[]
required_revision_actions[]
required_workunits[]
required_retests[]
required_approvals[]
checkpoint_strategy
status
created_at
```

Example shape:

```text
keep:
  upstream trusted revisions

invalidate:
  outputs derived from confirmed invalid root

regenerate:
  minimal affected subgraph

retest:
  directly affected + dependency-required tests

resume:
  first WorkUnit whose inputs become satisfiable after repair
```

`PRIM-RECOVERY` consumes `PRIM-IMPACT` from Knowledge Kernel and schedules work via Execution Kernel.

---

## 9. `PRIM-LOOPGUARD` — LoopGuard

LoopGuard ngăn hệ thống lặp mà không tạo tiến triển.

```text
loopguard_id
scope
failure_signature
same_signature_count
revision_churn_count
retry_count
window
budget
status
```

Escalation examples:

```text
same failure signature >= N
→ ESCALATE

same artifact repeatedly revised without gate improvement
→ ESCALATE

A → B → A decision cycle detected
→ ESCALATE
```

Domain Package có thể cấu hình N/budget nhưng không được vô hiệu hoá loop protection hoàn toàn trong production mode.

---

## 10. Decision sequence

```text
Execution produces Evidence
        ↓
Gate evaluation
   ┌────┴─────┐
 PASS       FAIL/BLOCKED/STALE
  │               │
CONTINUE      classify condition
                  │
          ┌───────┼─────────┐
        WAIT    RETRY     FAILURE
                           │
                     root diagnosis
                           │
                       ImpactSet
                           │
                     RecoveryPlan
                           │
                       LoopGuard
                           │
                 execute / escalate
```

---

## 11. Human involvement

Human không bắt buộc cho mọi Decision.

Policy examples:

```text
runtime timeout retry → automatic
stale revision → automatic rebase/block
normative upstream revision → approval required
ambiguous root cause with high impact → human confirmation
abort/replan high-impact scope → human approval
```

Authority/approval semantics thuộc Governance Kernel.

---

## 12. API contract

```text
EvaluateGate(gate_type, scope)
GetGateStatus(scope)
CreateFailure(candidate)
DiagnoseFailure(failure_id)
ComputeDecision(scope)
CreateRecoveryPlan(failure_id)
EvaluateLoopGuard(scope)
GetPendingDecisions(scope)
ResolveFailure(failure_id, evidence)
```

`DiagnoseFailure` có thể trả `root_status=UNKNOWN`; runtime phải hỗ trợ ambiguity thay vì bịa root cause.

---

## 13. Cross-kernel contract matrix

| Decision concept | Kernel khác | Mapping bắt buộc |
|---|---|---|
| Gate inputs | Knowledge | exact revisions + `PRIM-VALIDITY` |
| Gate evidence | Execution | `PRIM-EVIDENCE` |
| Gate authority precondition | Governance | `PRIM-AUTHORITY` / `PRIM-APPROVAL` |
| Failure trace | Knowledge | `PRIM-TRACE` paths |
| Recovery impact | Knowledge | `PRIM-IMPACT` |
| Recovery execution | Execution | `PRIM-WORKUNIT` + `PRIM-CHECKPOINT` |
| Retry budget | Execution | attempt counts from `PRIM-RUN` |
| Escalation target | Governance | authorized `PRIM-ACTOR` |
| Failure taxonomy | Domain | `PRIM-DOMAIN.failure_types` |
| Gate templates | Domain | `PRIM-DOMAIN.gate_types` |

---

## 14. Acceptance criteria

Decision Kernel đạt v0.1 khi:

1. gate pin exact evaluated revisions/evidence;
2. BLOCKED khác FAIL;
3. failure lưu detection/root/resume riêng;
4. ambiguous root cause không bị ép thành certainty giả;
5. recovery plan chỉ invalidate affected subgraph;
6. retry có loop guard;
7. decision không phụ thuộc free-text keyword parser;
8. high-impact decision có thể buộc human approval theo policy.

