# GWF — DG-W2 Wave 2 Requalification QA

## 1. QA identity

**Wave:** 2 — Minimal Documentation Kernel  
**Exit gate:** DG-W2  
**Dependency base:** DG-P6 formal-close HEAD `0c09d16e6a1fe6e01081015f2d7490ba07e58316`  
**Qualified QA HEAD:** `bdce1392db5e54597a12e5de02d4d916aa081b6f`  
**Workflow:** `35602717476` PASS  
**Evidence artifact:** `10638479929`  
**Artifact digest:** `sha256:9fd5937a0c87dd51c9f6b10148bcea64fe1c0e65a9431b788a5933a7bd3f0f15`

This QA requalifies DG-P4, DG-P5 and DG-P6 on one exact HEAD before Wave 3 may be considered.

It does not authorize or implement DG-P7/DG-P8.

## 2. Exact component requalification

All three Wave-2 components were rerun from the same checkout `bdce1392db5e54597a12e5de02d4d916aa081b6f`.

### DG-P4

Real GitHub provider smoke: PASS.

Evidence includes:

- repository: `minhtri22/GWF`;
- repository ID: `1374857546`;
- exact Wave-2 HEAD: `bdce1392db5e54597a12e5de02d4d916aa081b6f`;
- subject path: `docs/DG_P4_DOCUMENT_FACADE_SPEC.md`;
- subject blob: `b0034171454d06dbdeec2145ab73d5fb0cee2982`;
- source content SHA-256: `ee20da4c52d6e5614de29c3118ace395c7583390aea5025b84d2d8f5399a06fc`.

Checks PASS:

- document ID is Artifact ID;
- revision ID is kernel Revision ID;
- reserved `governed_document` type;
- stable logical key is path-independent;
- exact repository/commit/blob/content binding;
- payload hash remains distinct from source-content hash;
- new revision begins UNVERIFIED;
- no QA/Gate/relation side effects during P4 registration.

### DG-P5

Component gate: PASS.

Schema state confirms:

```text
0008_v086_dg_p5_document_findings
```

is the only Wave-2 documentation migration.

Checks PASS:

- `document_findings` exists;
- no `document_qa_records` table;
- no validator-execution table;
- QA record is PRIM-EVIDENCE;
- clean QA PASS may have zero findings;
- P5 alone leaves revision UNVERIFIED;
- no Gate or relation side effect.

### DG-P6

Component gate: PASS.

Global kernel validity remains exactly:

```text
DIRTY
FAILED
STALE
SUPERSEDED
UNVERIFIED
VALID
```

`BLOCKED` remains a derived document-effective state and is not persisted as a global KnowledgeKernel validity value.

No P6 migration or dedicated document-state table exists.

## 3. Unified fixture requalification

The following matrices were run together on the same exact HEAD:

```text
D4-F1..D4-F15
D5-F1..D5-F20
D6-F1..D6-F20
```

Result: PASS.

This proves the component implementations remain mutually compatible after P6 formal close.

## 4. Cross-wave exact-revision invalidation

DG-W2 performs an integrated P4 → P5 → P6 sequence independent of the individual component tests.

Observed sequence:

```text
logical document D
    ↓
R1 created
    ↓
QA(R1) = PASS
    ↓
reconcile R1 -> VALID
    ↓
R2 created for same logical document
    ↓
R1.status = SUPERSEDED
R1.validity = SUPERSEDED
R2.validity = UNVERIFIED
QA(R1) no longer current
effective(R2) = UNVERIFIED
    ↓
QA(R2) = FAIL with one finding
    ↓
effective(R2) = BLOCKED
kernel(R2) != VALID
```

PASS checks:

- document identity stable across R1/R2;
- revision identity changes;
- logical key remains stable despite path change;
- old revision is superseded;
- new revision begins UNVERIFIED;
- old QA cannot validate R2;
- new FAIL QA creates a finding;
- effective BLOCKED keeps kernel non-VALID.

This satisfies the Wave-2 exact-revision invalidation requirement.

## 5. No duplicate knowledge subsystem

PASS.

At the qualified HEAD, the only documentation-specific persistence table is:

```text
document_findings
```

Explicitly absent:

```text
document_records
document_revisions
document_qa_records
document_validator_executions
document_validity
document_lifecycle
document_state
document_waivers
document_authority_claims
document_relations
document_change_sets
catalog_entries
```

Canonical ownership remains:

```text
logical document     -> Artifact
document revision    -> Revision
QA / validator run   -> Evidence
finding current state-> document_findings
waiver authorization -> Proposal / Approval
transition history   -> Audit
lifecycle            -> Artifact.lifecycle_status
kernel validity      -> Revision.validity_state
effective BLOCKED    -> derived projection
```

No parallel knowledge subsystem has been introduced.

## 6. Schema/migration compatibility

Wave-2 schema decision is coherent:

```text
DG-P4 migration = NONE
DG-P5 migration = exactly 0008_v086_dg_p5_document_findings
DG-P6 migration = NONE
```

Applied migration lineage remains:

```text
0001_v05_production_foundation
0002_v06_identity_multitenancy
0003_v07_distributed_runtime
0004_v081_domain_project_lifecycle
0005_v082_project_governance_agent_protocol
0006_v083_orchestrator_integration
0007_v084_github_plugin_sha_qa
0008_v086_dg_p5_document_findings
```

No Wave-3 authority/relation state was created by the cross-wave gate.

## 7. Compatibility regressions

PASS:

- Knowledge;
- Execution;
- Decision;
- Persistence;
- DG-P4;
- DG-P5;
- DG-P6;
- full repository regression;
- compile.

## 8. Negative infrastructure evidence

Initial DG-W2 workflow run:

- run: `35602654364`;
- HEAD: `d5307d116b81f95bf8ee386685846522487cb249`;
- result: FAIL before any job was created.

Cause: workflow content contained literal escaped newline sequences rather than YAML line breaks.

Repair:

- commit `bdce1392db5e54597a12e5de02d4d916aa081b6f`;
- only workflow newline serialization changed;
- gate semantics, acceptance criteria and P4/P5/P6 runtime were unchanged.

The failed run remains negative infrastructure evidence.

## 9. Wave-2 invariant verdict

```text
DG-P4 same-head requalification              PASS
DG-P5 same-head requalification              PASS
DG-P6 same-head requalification              PASS
real P4 source identity                      PASS
exact-revision QA invalidation               PASS
stable logical document identity             PASS
new revision UNVERIFIED                      PASS
old QA not current for new revision          PASS
BLOCKED remains derived                      PASS
global KnowledgeKernel VALIDITY unchanged    PASS
no duplicate knowledge subsystem             PASS
P4 migration                                 NONE
P5 migration                                 EXACTLY ONE / BOUNDED
P6 migration                                 NONE
no Wave-3 state                              PASS
targeted regressions                         PASS
full regression                              PASS
compile                                      PASS
Finding OPEN                                 0
```

**DG-W2 WAVE-2 REQUALIFICATION: PASS**

Formal closure still requires exact-head requalification of the committed handoff package.
