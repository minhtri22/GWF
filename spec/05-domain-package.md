# Domain Package

## 1. Vai trò

Domain Package (`PRIM-DOMAIN`) là lớp mapping vocabulary và rules của một lĩnh vực vào runtime lõi.

Mục tiêu:

- thêm domain mới mà không fork bốn kernel;
- giữ một primitive model thống nhất;
- domain-specific semantics phải explicit và machine-readable;
- cho phép UI/agent dùng thuật ngữ tự nhiên của domain nhưng runtime vẫn làm việc trên canonical primitives.

Domain Package **không phải kernel thứ năm**. Nó là declarative extension package được bốn kernel nạp.

---

## 2. Package manifest

Một package tối thiểu:

```text
domain_id
version
compatible_runtime_versions
artifact_types[]
trace_types[]
workunit_templates[]
evidence_types[]
gate_types[]
failure_types[]
recovery_policies[]
roles[]
authority_policies[]
approval_policies[]
validity_rules[]
ui_labels?
```

Mọi entry phải map về primitive owner rõ ràng.

---

## 3. Mapping sang Knowledge Kernel

### Artifact types

```yaml
artifact_types:
  - id: requirement
    maps_to: PRIM-ARTIFACT
    revision_model: PRIM-REVISION
    normative: true
```

Domain chỉ định:

- schema payload;
- required parent/dependency types;
- allowed trace relations;
- invalidation semantics;
- approval class nếu có.

### Trace types

```yaml
trace_types:
  - id: derives_from
    maps_to: PRIM-TRACE
    strength: HARD
    invalidates_on_upstream_supersede: true
```

### Validity rules

```yaml
validity_rules:
  - artifact_type: design
    valid_if:
      - upstream_current
      - required_gate_pass
```

Owner vẫn là [Knowledge Kernel](01-knowledge-kernel.md); package chỉ cấu hình semantics.

---

## 4. Mapping sang Execution Kernel

### WorkUnit templates

```yaml
workunit_templates:
  - id: implement_change
    maps_to: PRIM-WORKUNIT
    inputs:
      - artifact_type: requirement
      - artifact_type: design
    outputs:
      - artifact_type: implementation_evidence
    executor_role: builder
    required_gate_types:
      - ready_to_execute
```

Template phải khai báo:

- input binding;
- output contracts;
- executor role;
- evidence required;
- timeout/retry policy;
- resource conflict keys;
- success gate.

### Evidence types

```yaml
evidence_types:
  - id: automated_test_result
    maps_to: PRIM-EVIDENCE
    trust_class: AUTHORITATIVE
```

Owner vẫn là [Execution Kernel](02-execution-kernel.md). Mỗi lần thực thi template materialize thành `PRIM-RUN`; package có thể cấu hình runtime defaults nhưng không sở hữu run state.

---

## 5. Mapping sang Decision Kernel

### Gate types

```yaml
gate_types:
  - id: ready_to_execute
    maps_to: PRIM-GATE
    required_validity:
      inputs: VALID
    required_approvals:
      - execution_start
```

### Failure taxonomy

```yaml
failure_types:
  - id: specification_mismatch
    maps_to: PRIM-FAILURE
    default_decision: REVISE_UPSTREAM
    root_candidates:
      - specification
      - requirement
```

### Recovery policy

```yaml
recovery_policies:
  - failure_type: specification_mismatch
    maps_to: PRIM-RECOVERY
    invalidation_mode: AFFECTED_SUBGRAPH
    require_root_confirmation: true
```

### Loop budgets

```yaml
loop_policy:
  maps_to: PRIM-LOOPGUARD
  same_signature_limit: 2
  revision_churn_limit: 3
```

Owner vẫn là [Decision Kernel](03-decision-kernel.md). Gate/failure/recovery có thể phát sinh `PRIM-DECISION`; package chỉ cấu hình allowed/default decision classes, không tự commit decision authoritative.

---

## 6. Mapping sang Governance Kernel

### Roles

```yaml
roles:
  - id: reviewer
    maps_to: PRIM-ACTOR
```

Role chỉ là binding helper. Permission thực nằm ở AuthorityPolicy.

### Authority policies

```yaml
authority_policies:
  - role: reviewer
    maps_to: PRIM-AUTHORITY
    allow:
      - action: APPROVE
        resource_type: reviewable_artifact
```

### Approval policies

```yaml
approval_policies:
  - id: normative_change
    maps_to: PRIM-APPROVAL
    requires_actor_type: HUMAN
    prohibit_self_approval: true
```

Owner vẫn là [Governance Kernel](04-governance-kernel.md).

---

## 7. Domain vocabulary adapter

Package có thể cung cấp display names mà không thay canonical primitive.

Ví dụ:

```yaml
ui_labels:
  artifact: Document
  workunit: Task
  gate: Review Gate
  recovery_plan: Rework Plan
```

Một domain khác có thể dùng tên hoàn toàn khác nhưng vẫn map về cùng primitive IDs.

---

## 8. Package validation

Khi load package, runtime phải validate:

1. mọi `maps_to` nằm trong primitive registry;
2. mọi referenced artifact/workunit/gate/failure type tồn tại;
3. không có circular hard dependency bị cấm;
4. every normative artifact type có mutation/approval class rõ;
5. every WorkUnit có success gate hoặc explicit no-gate policy;
6. every retryable failure có budget;
7. every high-impact recovery có authority/approval rule;
8. every hard TraceLink có invalidation behavior;
9. package không override core invariants.

Package fail validation không được activate.

---

## 9. Example domain-neutral package fragment

```yaml
domain_id: example.workflow
version: 0.1.0

artifact_types:
  - id: intent
    maps_to: PRIM-ARTIFACT
    normative: true

  - id: plan
    maps_to: PRIM-ARTIFACT
    normative: true

  - id: result
    maps_to: PRIM-ARTIFACT
    normative: false

trace_types:
  - id: plan_from_intent
    maps_to: PRIM-TRACE
    from: plan
    to: intent
    strength: HARD
    invalidates_on_upstream_supersede: true

workunit_templates:
  - id: execute_plan
    maps_to: PRIM-WORKUNIT
    inputs: [plan]
    outputs: [result]
    executor_role: operator
    required_gate_types: [plan_ready]


gate_types:
  - id: plan_ready
    maps_to: PRIM-GATE
    requires:
      - input_validity: VALID
      - approval_policy: plan_approval

failure_types:
  - id: result_mismatch
    maps_to: PRIM-FAILURE
    default_decision: REVISE_UPSTREAM

recovery_policies:
  - failure_type: result_mismatch
    maps_to: PRIM-RECOVERY
    invalidation_mode: AFFECTED_SUBGRAPH

roles:
  - id: planner
    maps_to: PRIM-ACTOR
  - id: operator
    maps_to: PRIM-ACTOR
  - id: approver
    maps_to: PRIM-ACTOR

approval_policies:
  - id: plan_approval
    maps_to: PRIM-APPROVAL
    requires_role: approver
```

Fragment này chứng minh Domain Package chỉ cấu hình runtime; không tạo primitive mới cho những khái niệm đã có trong core.

---

## 10. Cross-kernel mapping matrix

| Domain declaration | Canonical primitive | Owner document |
|---|---|---|
| `artifact_types` | `PRIM-ARTIFACT`, `PRIM-REVISION` | [Knowledge Kernel](01-knowledge-kernel.md) |
| `trace_types` | `PRIM-TRACE` | [Knowledge Kernel](01-knowledge-kernel.md) |
| `validity_rules` | `PRIM-VALIDITY`, `PRIM-IMPACT` | [Knowledge Kernel](01-knowledge-kernel.md) |
| `workunit_templates` | `PRIM-WORKUNIT` | [Execution Kernel](02-execution-kernel.md) |
| execution runs | `PRIM-RUN` | [Execution Kernel](02-execution-kernel.md) |
| `evidence_types` | `PRIM-EVIDENCE` | [Execution Kernel](02-execution-kernel.md) |
| checkpoint policy | `PRIM-CHECKPOINT` | [Execution Kernel](02-execution-kernel.md) |
| `gate_types` | `PRIM-GATE` | [Decision Kernel](03-decision-kernel.md) |
| decision policy | `PRIM-DECISION` | [Decision Kernel](03-decision-kernel.md) |
| `failure_types` | `PRIM-FAILURE` | [Decision Kernel](03-decision-kernel.md) |
| `recovery_policies` | `PRIM-RECOVERY` | [Decision Kernel](03-decision-kernel.md) |
| `loop_policy` | `PRIM-LOOPGUARD` | [Decision Kernel](03-decision-kernel.md) |
| `roles` | `PRIM-ACTOR` | [Governance Kernel](04-governance-kernel.md) |
| `authority_policies` | `PRIM-AUTHORITY` | [Governance Kernel](04-governance-kernel.md) |
| `approval_policies` | `PRIM-APPROVAL` | [Governance Kernel](04-governance-kernel.md) |
| audit policy | `PRIM-AUDIT` | [Governance Kernel](04-governance-kernel.md) |

---

## 11. Acceptance criteria

Domain Package spec đạt v0.1 khi:

1. có thể mô tả domain mà không sửa core primitive registry;
2. mọi declaration map về owner kernel duy nhất;
3. artifact dependency có invalidation semantics;
4. WorkUnit có executable contract;
5. gate/failure/recovery mapping đầy đủ;
6. role/authority/approval không trộn lẫn;
7. package invalid bị reject trước activation.

