# GWF — DG-P5 QA Run + Finding Persistence Handoff

## 1. Scope

This handoff records bounded DG-P5 implementation qualification.

DG-P5 persists exact-revision QA execution and finding lifecycle while reusing existing GWF primitives wherever their semantics are sufficient.

It does not open DG-P6, DG-P11, Wave 3, GAC, Reference Acquisition or G2E Shared Library.

## 2. Frozen input identity

- DG-P4 final formal-close HEAD: `a11d9ad205272c4c16c49eddb398dee4c8a0ff05`
- DG-P5 pre-implementation qualification HEAD: `6d4ab89bfb86426dcf19703ae264f7c009f33015`
- frozen DG-P5 specification commit: `9e846621faf7b1a81c605ad624f4abbc6c354470`
- frozen specification blob: `29ca1c85f665468aade7fc555b634a134af9a46a`
- pre-implementation QA blob: `00bb60db5a1fed06dff3c8dd71018add4f89c67e`

## 3. Implementation identity

- initial implementation commit: `c42800b6d635ba5d90be0b947955ccdfbaeb9f91`
- workflow-path repair / qualified implementation HEAD: `fda9f7b3c5486f629e47f13652a758de158f7d22`

Qualified implementation surface:

- `src/gwr/migrations.py` — one migration for `document_findings`;
- `src/gwr/execution.py` — backward-compatible transactional Evidence extension;
- `src/gwr/domain.py` — reserved core document QA Evidence types;
- `src/gwr/document_qa.py` — QA/finding persistence and lifecycle service;
- `src/gwr/runtime.py` — runtime service binding;
- `tests/test_dg_p5_qa_findings.py` — D5-F1..D5-F20;
- `tools/run_dg_p5_gate.py` — bounded schema/primitive smoke;
- `.github/workflows/dg-p5-qa-finding-persistence.yml` — qualification workflow.

## 4. Schema decision delivered

Exactly one migration/table was added:

```text
0008_v086_dg_p5_document_findings
        ↓
document_findings
```

Not added:

- `document_qa_records`;
- `document_validator_executions`;
- waiver table;
- finding-transition table;
- duplicate Evidence store.

## 5. PRIM-EVIDENCE reuse

Canonical mappings are implemented:

```text
DocumentQARecord.qa_record_id
    = Evidence.evidence_id
    where evidence_type = document_qa_record

ValidatorExecution persisted identity
    = Evidence.evidence_id
    where evidence_type = document_validator_execution
```

Both core evidence IDs are reserved against incompatible domain redefinition.

QA Evidence remains immutable historical evidence.

## 6. Atomic Evidence composition

Existing `ExecutionKernel.add_evidence()` retains its existing default auto-commit behavior.

DG-P5 adds bounded optional capabilities:

- caller-supplied/preallocated evidence identity;
- `commit=False` participation in an outer database transaction.

The P5 QA service uses one transaction for:

```text
validator execution Evidence
        +
0..N document_findings
        +
DocumentQARecord Evidence
        +
audit events
```

Injected finding persistence failure is verified to roll back the complete QA unit.

## 7. Finding lifecycle

Implemented current states:

- `OPEN`
- `RESOLVED_PENDING_VERIFY`
- `VERIFIED_RESOLVED`
- `WAIVED`

Implemented guarded transitions include:

```text
OPEN -> RESOLVED_PENDING_VERIFY
OPEN -> WAIVED
RESOLVED_PENDING_VERIFY -> VERIFIED_RESOLVED
RESOLVED_PENDING_VERIFY -> OPEN
RESOLVED_PENDING_VERIFY -> WAIVED
```

Finding updates use optimistic `version` checks and append audit history.

Direct `OPEN -> VERIFIED_RESOLVED` is rejected.

## 8. Exact-revision freshness and resolution verification

A QA record is current only if its exact subject revision equals the document's current revision.

Creating a new DG-P4 revision does not mutate or transfer old QA.

A finding can become VERIFIED_RESOLVED only when:

- it is pending verification;
- the verifying QA record differs from the originating QA record;
- the verifying QA targets the exact resolution revision;
- the verifying QA is evaluated;
- the verifying QA is later than the origin QA;
- the same finding fingerprint is not emitted by the verifying QA.

## 9. Waiver reuse

Waiver preparation uses existing Proposal.

Human authorization uses existing Approval and domain approval policy.

Applying an approved waiver stores the exact approved `approval_id` as `waiver_ref`.

Minimum non-waivable classes enforced:

- `SECURITY_LEAK`
- `RESEARCH_LOCK_VIOLATION`
- `DUPLICATE_AUTHORITY`

An expired/review-due waiver remains observable but is not treated as effective clean state.

## 10. Qualification evidence

Negative workflow evidence preserved:

- run `35584776602`
- head `c42800b6d635ba5d90be0b947955ccdfbaeb9f91`
- D5-F1..D5-F20: PASS
- schema/primitive gate: PASS
- workflow stopped because the bounded regression step named non-existent test paths.

Qualified run:

- workflow `35584865418`
- exact head `fda9f7b3c5486f629e47f13652a758de158f7d22`
- conclusion: **PASS**
- artifact: `10631014201`
- artifact digest: `sha256:feb5203fafaac98640569a1d0816b6626fe7279214dfed2d41488f819f2c852e`

Results:

- D5-F1..D5-F20: **20/20 PASS**
- bounded schema/primitive smoke: **PASS**
- targeted Evidence/Gate/Failure compatibility regression: **23/23 PASS**
- full repository regression: **PASS**
- compile: **PASS**

Bounded gate additionally proves:

- `document_findings` exists;
- `document_qa_records` does not exist;
- validator-execution table does not exist;
- QARecord is Evidence;
- clean QA can PASS with zero findings;
- document revision remains `UNVERIFIED`;
- P5 creates no Gate or Trace relation side effect.

## 11. Findings

F-64 through F-72 are resolved in `docs/Finding_checklist.md`.

Implementation/troubleshooting history remains in Finding/Handoff documents. `LINEAGE.md` records completed outcomes only.

## 12. Explicit non-scope

DG-P5 did not implement:

- DG-P6 lifecycle/validity mapping;
- documentation BLOCKED semantics;
- document authority;
- typed document relations;
- impact propagation;
- DocumentChangeSet persistence;
- GAC;
- Reference Acquisition;
- G2E;
- bulk migration;
- source auto-fix.

## 13. Formal-close criterion

DG-P5 is implementation-qualified at `fda9f7b3c5486f629e47f13652a758de158f7d22`.

Formal close requires:

1. commit this handoff/finding/plan/lineage package;
2. run the exact DG-P5 workflow on that committed handoff HEAD;
3. require D5-F1..F20, bounded gate, targeted regression, full regression and compile to PASS;
4. preserve exact run/artifact identities.

DG-P6 remains NOT_STARTED until DG-P5 formal close.
