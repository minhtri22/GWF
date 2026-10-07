# GWF — DG-P5 QA Run + Finding Persistence Specification

## 1. Status and authorization boundary

**Item:** DG-P5 — QA run + finding persistence  
**Wave:** 2 — Minimal Documentation Kernel  
**Specification state:** FROZEN FOR DOCUMENT QA  
**Implementation state:** NOT_STARTED  
**Dependency:** DG-P0 + DG-P4  
**Base:** DG-P4 final formal-close HEAD `a11d9ad205272c4c16c49eddb398dee4c8a0ff05`

The user explicitly authorized DG-P5 pre-implementation specification / dependency qualification only.

This document determines how far `DocumentQARecord` and `DocumentFinding` can reuse existing GWF primitives before any schema is added.

This document does **not** authorize:

- implementation code;
- migration execution;
- DG-P6 lifecycle/validity mapping;
- document authority;
- document relations;
- Wave 3;
- GAC;
- Reference Acquisition;
- G2E Shared Library.

## 2. Exact dependency evidence

DG-P5 starts from DG-P4 formal-close state:

- DG-P4 formal-close HEAD: `a11d9ad205272c4c16c49eddb398dee4c8a0ff05`
- final exact-head workflow: `35582578994` PASS
- final evidence artifact: `10630264812`
- artifact digest: `sha256:8dda51c10fceb3b4dfefc119346196c62432bd557b818c1748fa49c5b5c4732b`

Exact inspected governing/runtime blobs:

| Artifact | Exact Git blob |
| --- | --- |
| `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` | `e50d0f17433c6f0ec57f987278a0d24a7bbd4610` |
| `docs/IMPLEMENTATION_7_WAVES_PLAN.md` | `86b34a439d1c720a3a07e88aba54b013b7ca3547` |
| `src/gwr/execution.py` | `87dfa05789acc71c7681c3ca1e6e3bd9895025d3` |
| `src/gwr/decision.py` | `bc1320f428bf9279232a7dab0817f3fd71834b5d` |
| `src/gwr/db.py` | `b9825998757423822ab7ffb22bd37dd202f3e30d` |
| `src/gwr/migrations.py` | `db3a9ccc2cc21f5db1cc048b7ed8903ce3822cdb` |
| `src/gwr/governance.py` | `0eb8f3eeb7a6ee01512bc778241fa2ee0b42f6a6` |
| `src/gwr/domain.py` | `f7fc20ec43ab2f447aba3c30a73239370f1b0f27` |
| `src/gwr/document_validation.py` | `31bd854593bbfd962f61d293c732d879a56ead6f` |
| `src/gwr/document_facade.py` | `e5af15059c9c0718da0c4a898cb600966ce5204f` |
| `src/gwr/runtime.py` | `4f81a2258f18b35ad1453aa8ffbe73eb34f4ec03` |

Governing specification §§8.5–8.6 requires:

- one `DocumentQARecord` for one attributable QA run over an exact revision or change set;
- zero-to-many `DocumentFinding` records;
- finding lifecycle remains attributable to the QA run that created it.

§17 requires minimum finding statuses:

- `OPEN`
- `RESOLVED_PENDING_VERIFY`
- `VERIFIED_RESOLVED`
- `WAIVED`

§19 classifies `DocumentQARecord + DocumentFinding lifecycle` as a GWF-native **BUILD** responsibility.

## 3. Existing primitive inventory

### 3.1 PRIM-EVIDENCE

Existing `evidence` storage already provides:

- immutable evidence identity;
- project identity;
- evidence type;
- optional producer run;
- producer actor;
- exact subject references;
- structured payload;
- payload content hash;
- creation time;
- freshness metadata;
- trust class;
- audit emission through `ExecutionKernel.add_evidence()`.

This is a strong semantic match for an immutable QA-run record.

### 3.2 ValidatorExecution / ValidatorFinding

Wave 1 already provides normalized in-memory:

- `ValidatorExecution`;
- `ValidatorFinding`;
- tool/version/config identity;
- exact subject hash;
- execution status;
- content status;
- normalized external findings;
- tool-failure versus document-failure separation.

These are execution outputs, not authoritative persisted QA state.

### 3.3 PRIM-GATE

Existing Gate storage represents a policy evaluation result over required evidence/input revisions.

It is **not** a QA-run record because:

- it does not own validator-execution details;
- it does not own finding lifecycle;
- gate types are domain-declared;
- it represents an adjudication result, not the normalized QA execution record itself.

Future gates may consume DocumentQARecord evidence. DG-P5 must not replace DocumentQARecord with Gate.

### 3.4 PRIM-FAILURE

Existing FailureRecord represents operational/domain execution failure.

It includes:

- domain failure class;
- runtime stage;
- loopguard coupling;
- recovery routing;
- root-cause workflow;
- status values such as `OPEN`, `RECOVERY_PLANNED`, `RESOLVED`.

It is not semantically compatible with Documentation finding lifecycle.

Using FailureRecord for DocumentFinding would incorrectly couple documentation findings to runtime recovery, domain failure taxonomies and loopguard behavior.

### 3.5 Artifact / Revision

Artifact/Revision represents governed knowledge lineage.

A DocumentFinding is not a knowledge artifact and must not create a parallel artifact lineage merely to obtain mutable status.

### 3.6 Proposal / Approval

Existing proposal/approval primitives already provide:

- attributable proposal identity;
- human approval;
- proposal hash;
- scope;
- decision;
- conditions;
- optional expiration;
- audit attribution.

These primitives are suitable for governed finding waiver authorization.

### 3.7 Append-only Audit

Existing `audit_events` is append-only and records:

- actor;
- action;
- resource identity;
- before/after version fields;
- proposal/approval refs;
- reason code;
- timestamp;
- metadata hash.

It is sufficient to preserve finding state-transition attribution when transition action names and versions are explicit.

## 4. Reuse verdict — DocumentQARecord

### 4.1 Verdict

**DocumentQARecord MUST reuse PRIM-EVIDENCE.**

A dedicated `document_qa_records` table is not justified.

Canonical mapping:

```text
DocumentQARecord.qa_record_id
    = Evidence.evidence_id

Evidence.evidence_type
    = "document_qa_record"

Evidence.subject_refs
    = exact governed document revision
      OR future exact DocumentChangeSet identity

Evidence.structured_payload
    = DocumentQARecord payload

Evidence.content_hash
    = canonical QA record payload hash

Evidence.producer_actor_id
    = actor/service that assembled the QA record

Evidence.trust_class
    = AUTHORITATIVE
      meaning authoritative record of what QA executed,
      not an assertion that the document content is correct
```

### 4.2 Reserved core evidence types

DG-P5 freezes two cross-domain core evidence type IDs:

```text
document_validator_execution
document_qa_record
```

A domain package must not redefine these IDs with incompatible semantics.

The implementation may add bounded core-evidence collision validation, analogous to DG-P4 reserved core artifact protection.

No new evidence table is authorized.

## 5. Persisted ValidatorExecution model

Each persisted external/local validator execution should reuse PRIM-EVIDENCE:

```text
Evidence.evidence_type = "document_validator_execution"
```

Minimum payload:

```text
schema = "DG-P5-VALIDATOR-EXECUTION-v1"
validator_id
validator_version
config_hash
execution_status
content_status
error_code
subject:
  document_id
  revision_id
  source_content_sha256
  path_locator
normalized_findings[]
started_at
finished_at
```

Rules:

1. exact governed `revision_id` is required;
2. subject hash/path from the external adapter alone is insufficient;
3. raw tool stdout/stderr is not required in core persisted payload;
4. secrets/credentials are forbidden;
5. tool outage remains `UNAVAILABLE` / `TOOL_ERROR` with content `NOT_EVALUATED`;
6. tool failure must not fabricate a document finding.

## 6. DocumentQARecord payload contract

Minimum immutable payload:

```text
schema = "DG-P5-QA-RECORD-v1"
subject:
  kind = DOCUMENT_REVISION | DOCUMENT_CHANGE_SET
  document_id
  exact_subject_id
qa_policy_ref:
  policy_id
  policy_version
  policy_hash
validator_execution_refs[]
finding_refs[]
overall_status
started_at
finished_at
verified_by
verified_at
```

### 6.1 Subject binding

For P5 implementation:

- `DOCUMENT_REVISION` is executable because DG-P4 exists;
- `DOCUMENT_CHANGE_SET` is a reserved exact-subject kind for future DG-P11;
- P5 must fail closed if a change-set subject cannot be resolved to a real governed object;
- no dangling/fabricated change-set refs are accepted merely to exercise the enum.

### 6.2 QA overall status

P5 freezes minimum QA-run statuses:

- `PASS`
- `FAIL`
- `NOT_EVALUATED`

Interpretation:

- `PASS`: required QA execution completed and policy permits clean pass;
- `FAIL`: QA execution completed and policy found one or more findings that prevent clean pass;
- `NOT_EVALUATED`: required QA layer/tool could not produce a valid evaluation.

Operational/document lifecycle `BLOCKED` belongs to DG-P6 and later gate semantics; P5 must not preempt it.

### 6.3 Immutability

A QA record is immutable after creation.

Later finding resolution or waiver does not rewrite the original QA record.

The original run remains historical evidence of what was observed at that exact subject revision.

## 7. Reuse verdict — DocumentFinding

### 7.1 Verdict

**DocumentFinding cannot be represented faithfully by existing mutable primitives.**

Rejected alternatives:

- PRIM-EVIDENCE: immutable snapshot; no finding lifecycle state;
- PRIM-FAILURE: wrong operational semantics and lifecycle;
- PRIM-GATE: adjudication result, not finding entity;
- Artifact/Revision: wrong knowledge semantics and unnecessary lineage;
- Proposal/Approval alone: authorization evidence, not finding state.

Therefore **one dedicated GWF-native finding state table is justified**.

### 7.2 Minimum new table

Conceptual schema:

```text
document_findings
  finding_id                 PRIMARY KEY
  project_id
  qa_record_id               # PRIM-EVIDENCE id, type=document_qa_record
  subject_revision_id
  finding_class
  severity
  rule_id
  location_json
  description
  evidence_refs_json
  fingerprint
  status
  required_fix
  resolution_revision_ref    NULL
  waiver_ref                 NULL
  version                    INTEGER
  created_at
  updated_at
```

No `document_qa_records` table is permitted by this qualification.

No dedicated finding-transition table is required at P5 because current state is stored in `document_findings` and transition history is attributable through append-only `audit_events`.

## 8. Finding class and severity

### 8.1 Finding classes

P5 accepts the governing §17 class vocabulary, including:

- `STRUCTURAL_ERROR`
- `BROKEN_REFERENCE`
- `UNRESOLVED_DEPENDENCY`
- `DEPENDENCY_CYCLE`
- `STALE_DEPENDENCY`
- `UNDEFINED_TERM`
- `TERMINOLOGY_DRIFT`
- `SEMANTIC_CONTRADICTION`
- `DUPLICATE_AUTHORITY`
- `INVALID_SUPERSESSION`
- `CHANGE_CLASS_MISMATCH`
- `IMPLEMENTATION_DRIFT`
- `SCHEMA_API_DRIFT`
- `APPEND_ONLY_VIOLATION`
- `RESEARCH_LOCK_VIOLATION`
- `MISSING_PROVENANCE`
- `SECURITY_LEAK`
- `GENERATED_ARTIFACT_DRIFT`

P5 does not implement the later-wave detectors for all classes. It only persists normalized findings correctly when an authorized QA layer emits them.

### 8.2 Severity

The governing document requires a severity field but does not enumerate values.

DG-P5 freezes the core severity vocabulary:

```text
INFO
LOW
MEDIUM
HIGH
CRITICAL
```

Unknown severity values fail closed.

## 9. Finding fingerprint

Each finding requires a deterministic fingerprint to distinguish the same unresolved issue across verification runs.

Minimum fingerprint material:

```text
finding_class
rule_id
normalized location
normalized issue key
```

Description prose must not be the sole identity input.

The fingerprint is not a global finding identity. `finding_id` remains the durable entity created by the originating QA run.

## 10. Finding lifecycle

Allowed states:

```text
OPEN
RESOLVED_PENDING_VERIFY
VERIFIED_RESOLVED
WAIVED
```

Minimum transitions:

```text
OPEN
  ├──> RESOLVED_PENDING_VERIFY
  └──> WAIVED

RESOLVED_PENDING_VERIFY
  ├──> VERIFIED_RESOLVED
  ├──> OPEN
  └──> WAIVED
```

Terminal interpretation at P5:

- `VERIFIED_RESOLVED` is resolved;
- `WAIVED` remains observable and is not equivalent to verified resolution;
- an expired/inapplicable waiver is not an effective clean resolution.

Direct transitions that skip verification fail closed.

## 11. Resolution verification

### 11.1 Mark resolved pending verification

Transition to `RESOLVED_PENDING_VERIFY` requires:

- an exact `resolution_revision_ref`;
- the revision belongs to the same governed document;
- actor is authorized for the mutation;
- finding version matches expected version;
- audit event is appended.

### 11.2 Verify resolved

Transition to `VERIFIED_RESOLVED` requires:

- a new `DocumentQARecord`;
- QA subject exactly equals `resolution_revision_ref`;
- QA run is later than the finding's origin QA;
- required QA layer successfully evaluated;
- the finding fingerprint is not emitted as an active finding in the verifying QA run;
- actor/service attribution is recorded.

The originating QA record can never verify its own finding resolution.

## 12. Waiver reuse

P5 must reuse existing Proposal/Approval primitives.

A waiver proposal must freeze at least:

```text
finding_id
expected_finding_version
reason
scope
expiration_or_review_condition
```

When approved:

- finding may transition to `WAIVED`;
- `waiver_ref` stores the approved `approval_id`;
- audit links the transition to proposal/approval identity;
- finding remains queryable/observable.

Core non-waivable minimum classes:

- `SECURITY_LEAK`
- `RESEARCH_LOCK_VIOLATION`
- `DUPLICATE_AUTHORITY`

Policy may add more non-waivable classes later.

P5 must not invent a second waiver/approval subsystem.

## 13. Exact-revision freshness invariant

A QA record validates only the exact subject identity stored in that QA record.

For a governed document:

```text
current_revision_id == qa_record.subject.exact_subject_id
```

is required before that QA record can be considered current for the document.

If DG-P4 creates a new revision:

- old QA record remains immutable historical evidence;
- old findings remain attributable to their original QA run;
- old PASS does not transfer to the new revision;
- a fresh QA run is required.

This satisfies the DG-W2 exact-revision invalidation requirement without mutating historical QA evidence.

## 14. Atomicity requirement

Creating one QA run must be atomic across:

- persisted validator execution Evidence rows;
- DocumentQARecord Evidence row;
- zero-to-many DocumentFinding rows;
- audit events.

A successful QA record must never reference finding IDs that failed to persist.

### 14.1 Bounded Evidence-writer extension

Current `ExecutionKernel.add_evidence()` commits internally, which is insufficient for composing one atomic QA transaction.

DG-P5 implementation may make a bounded core extension so the existing PRIM-EVIDENCE writer can:

- accept a preallocated/caller-supplied evidence ID when required; and/or
- participate in an outer transaction without committing internally.

The public existing behavior of `add_evidence()` must remain unchanged for existing callers.

Implementation must not duplicate Evidence insertion logic in a second persistence subsystem merely to avoid this transaction boundary.

## 15. External validator normalization

Wave-1 validator outputs remain non-authoritative until normalized into a DG-P5 QA run.

Minimum normalization examples:

- markdownlint rule violation → `STRUCTURAL_ERROR`;
- Lychee broken governed/internal/external reference → `BROKEN_REFERENCE`;
- Vale terminology-policy violation → `TERMINOLOGY_DRIFT`.

Original validator `rule_id` remains stored.

A tool error/unavailable execution:

- persists ValidatorExecution evidence if the execution itself is attributable;
- yields QA `NOT_EVALUATED` when required by policy;
- does **not** manufacture a DocumentFinding against the document.

## 16. Query/read model

Minimum service queries:

- get QA record by `qa_record_id`;
- list QA records for exact revision;
- get current QA status for a document only when QA subject equals current revision;
- get finding by `finding_id`;
- list findings by QA record;
- list active findings for exact revision/document;
- inspect finding transition/audit history.

A QA record from an old revision must never appear as current QA for the latest document revision.

## 17. Governance and authority boundary

P5 state-changing operations must preserve:

- project mutable-state checks;
- project/tenant access;
- actor attribution;
- expected-version concurrency for findings;
- append-only audit.

P5 does not add document authority claims.

Finding waiver requires approved Proposal/Approval evidence.

No external validator may mutate finding state directly.

## 18. Migration decision

### 18.1 Not justified

DG-P5 does **not** justify:

- `document_qa_records` table;
- `document_validator_executions` table;
- duplicate Evidence store;
- duplicate approval/waiver table;
- finding transition event table.

### 18.2 Justified

DG-P5 **does justify one migration** adding:

```text
document_findings
```

because no existing primitive can represent the required mutable finding lifecycle without semantic corruption.

The migration is not executed during this specification phase.

## 19. Frozen fixture matrix

### D5-F1 — QARecord reuses Evidence

A QA run creates one `Evidence` row of type `document_qa_record`; `qa_record_id == evidence_id`.

### D5-F2 — validator execution reuses Evidence

Each persisted validator execution is `document_validator_execution` Evidence bound to exact revision.

### D5-F3 — zero finding PASS

A clean exact revision may produce a PASS QA record with zero DocumentFinding rows.

### D5-F4 — one-to-many findings

One QA record may own multiple findings; every finding references the exact originating QA record.

### D5-F5 — exact revision binding

QA record for revision R1 is current only while document current revision is R1.

### D5-F6 — prior PASS does not transfer

After DG-P4 creates R2, PASS on R1 remains historical and cannot validate R2.

### D5-F7 — tool failure is not document finding

Required validator TOOL_ERROR/UNAVAILABLE produces QA `NOT_EVALUATED` and no fabricated content finding.

### D5-F8 — finding lifecycle legal transition

`OPEN → RESOLVED_PENDING_VERIFY → VERIFIED_RESOLVED` succeeds only with required exact refs and version checks.

### D5-F9 — illegal skip fails

`OPEN → VERIFIED_RESOLVED` directly is rejected.

### D5-F10 — stale finding version fails closed

Concurrent transition with stale finding version raises stale-version semantics.

### D5-F11 — resolution QA must target resolution revision

QA on any other revision cannot verify the finding resolved.

### D5-F12 — originating QA cannot self-verify

The same QA record that created a finding cannot verify that finding resolved.

### D5-F13 — fingerprint persists across verification

Verification checks deterministic finding fingerprint rather than description wording alone.

### D5-F14 — waiver reuses approval

A waivable finding transitions to WAIVED only with an approved matching proposal/approval.

### D5-F15 — non-waivable class rejects waiver

At minimum SECURITY_LEAK, RESEARCH_LOCK_VIOLATION and DUPLICATE_AUTHORITY cannot be waived.

### D5-F16 — expired waiver is not effective clean state

Expired/review-due waiver remains observable and cannot be treated as verified resolution.

### D5-F17 — atomic QA creation

Injected finding persistence failure rolls back validator Evidence, QA Evidence, findings and audit for that QA run.

### D5-F18 — reserved evidence collision rejected

Domain package cannot redefine reserved core document QA evidence types incompatibly.

### D5-F19 — existing Evidence callers preserved

Existing research Evidence behavior/regressions remain unchanged after transactional writer extension.

### D5-F20 — no later-wave state mutation

P5 QA persistence alone does not set document revision VALID/BLOCKED, create authority claims, relations, GAC entries or bulk migration.

## 20. Explicit non-scope

DG-P5 must not implement:

- DG-P6 document lifecycle/validity transitions;
- document `BLOCKED` state;
- authority claims;
- duplicate-authority detector;
- document relations;
- impact propagation;
- change classification;
- DocumentChangeSet persistence;
- GAC;
- Reference Acquisition;
- G2E Shared Library;
- bulk migration;
- automatic source repair;
- external tool auto-fix.

## 21. Qualification verdict

```text
DocumentQARecord
    -> REUSE PRIM-EVIDENCE
    -> no dedicated QA table

ValidatorExecution persistence
    -> REUSE PRIM-EVIDENCE
    -> no dedicated execution table

DocumentFinding
    -> existing primitives semantically insufficient
    -> one dedicated GWF-native state table justified

Waiver
    -> REUSE Proposal/Approval

Finding transition history
    -> REUSE append-only Audit

Evidence atomic composition
    -> bounded existing writer extension required

schema migration
    -> exactly one new table justified:
       document_findings
```

**DG-P5 dependency/reuse specification is ready for exact document QA.**
