# GWF — DG-P5 Pre-Implementation Document QA

## 1. QA identity

**Subject:** `docs/DG_P5_QA_FINDING_PERSISTENCE_SPEC.md`  
**Subject commit:** `9e846621faf7b1a81c605ad624f4abbc6c354470`  
**Subject blob:** `29ca1c85f665468aade7fc555b634a134af9a46a`  
**Dependency base:** DG-P4 final formal-close HEAD `a11d9ad205272c4c16c49eddb398dee4c8a0ff05`  
**Dependency final exact-head workflow:** `35582578994` PASS  
**Dependency final artifact:** `10630264812`  
**QA type:** pre-implementation dependency/reuse/schema qualification  
**Implementation executed:** NO

This QA binds only the exact DG-P5 specification blob above.

## 2. Governing requirements verified

The governing Documentation Integrity specification requires:

- one attributable `DocumentQARecord` per exact revision/change-set QA run;
- zero-to-many `DocumentFinding` records;
- finding status lifecycle `OPEN / RESOLVED_PENDING_VERIFY / VERIFIED_RESOLVED / WAIVED`;
- waiver attribution and non-waivable policy classes;
- historical QA to remain exact-revision evidence;
- external validator output to normalize into GWF-native QA state.

The BUILD/INTEGRATE matrix explicitly assigns `DocumentQARecord + DocumentFinding lifecycle` to GWF-native ownership.

## 3. Existing primitive fit matrix

| Candidate | QA record | Validator execution | Finding state | Waiver | Verdict |
| --- | --- | --- | --- | --- | --- |
| PRIM-EVIDENCE | strong fit | strong fit | insufficient: immutable snapshot only | no | reuse for QA/execution |
| PRIM-GATE | insufficient | insufficient | insufficient | no | reject as primary store |
| PRIM-FAILURE | insufficient | insufficient | semantic mismatch | no | reject |
| Artifact/Revision | semantic mismatch | semantic mismatch | semantic mismatch | no | reject |
| Proposal/Approval | no | no | no | strong fit | reuse for waiver |
| Audit | no | no | transition history only | attribution | reuse for history |

## 4. DocumentQARecord reuse proof

PASS.

Existing Evidence already owns the exact semantics required for an immutable attributable QA run:

- identity;
- exact subject refs;
- producer;
- structured payload;
- payload hash;
- timestamp;
- trust classification;
- audit.

Therefore a dedicated `document_qa_records` table would duplicate PRIM-EVIDENCE.

Frozen mapping:

```text
qa_record_id = evidence_id
evidence_type = document_qa_record
subject_refs = exact revision / future exact change set
structured_payload = immutable QA record
trust_class = AUTHORITATIVE as execution record
```

"AUTHORITATIVE" here means authoritative provenance of the recorded QA execution. It does not mean the document is correct.

## 5. ValidatorExecution reuse proof

PASS.

Wave-1 `ValidatorExecution` values are immutable execution facts and map naturally to Evidence of type `document_validator_execution`.

Persisting them separately gives `validator_execution_refs` real immutable identities without creating a validator-execution table.

## 6. DocumentFinding reuse proof

Existing primitives are insufficient.

### Evidence — rejected as current finding state

Evidence is the correct immutable provenance substrate but cannot represent the required mutable lifecycle without rewriting historical evidence.

### FailureRecord — rejected

FailureRecord is bound to domain failure taxonomy, loopguard, recovery routing and root-cause semantics. Mapping documentation findings to it would create false runtime/recovery meaning.

### Gate — rejected

Gate represents policy evaluation, not one independently resolvable finding with resolution/waiver lifecycle.

### Artifact/Revision — rejected

A finding is not a knowledge artifact. Creating Artifact/Revision lineage for every QA finding would create a parallel knowledge subsystem for state that has different semantics.

**Verdict:** one dedicated `document_findings` current-state table is justified.

## 7. Minimal-schema QA

PASS.

Exactly one new table is justified at P5:

`document_findings`

No separate table is justified for:

- QA records;
- validator executions;
- waivers;
- finding transition events.

Existing Evidence, Proposal/Approval and append-only Audit cover those responsibilities.

## 8. Atomicity QA

Current `ExecutionKernel.add_evidence()` commits internally.

That is acceptable for standalone evidence calls but cannot atomically compose:

```text
validator execution Evidence
        +
QA record Evidence
        +
0..N DocumentFinding rows
        +
audit events
```

If QA Evidence commits before a finding insert fails, the QA record could reference missing finding IDs.

The specification therefore correctly requires a **bounded transactional extension of the existing Evidence writer**, not a second evidence implementation.

Existing `add_evidence()` behavior for existing callers must remain unchanged.

## 9. Exact-revision freshness QA

PASS.

P5 freezes freshness by identity rather than mutating old QA:

```text
QA is current for document
iff
qa.subject.revision_id == document.current_revision_id
```

After DG-P4 produces R2:

- QA(R1) remains immutable historical evidence;
- QA(R1) cannot validate R2;
- new QA(R2) is required.

This is compatible with DG-P4 and preserves evidence lineage.

## 10. Finding lifecycle QA

PASS as specification.

Legal minimum transitions:

```text
OPEN -> RESOLVED_PENDING_VERIFY
OPEN -> WAIVED
RESOLVED_PENDING_VERIFY -> VERIFIED_RESOLVED
RESOLVED_PENDING_VERIFY -> OPEN
RESOLVED_PENDING_VERIFY -> WAIVED
```

Direct `OPEN -> VERIFIED_RESOLVED` is forbidden.

Resolution verification requires a later QA record bound to the exact resolution revision; the originating QA cannot self-verify its finding.

Optimistic finding version checks are required.

## 11. Waiver QA

PASS.

Existing Proposal/Approval provides the required attributable authority mechanism. A second waiver subsystem is not justified.

Frozen minimum non-waivable classes:

- `SECURITY_LEAK`
- `RESEARCH_LOCK_VIOLATION`
- `DUPLICATE_AUTHORITY`

WAIVED remains observable and is not equivalent to VERIFIED_RESOLVED.

## 12. Severity vocabulary QA

The governing specification requires severity but does not enumerate values.

The bounded P5 vocabulary:

- INFO
- LOW
- MEDIUM
- HIGH
- CRITICAL

is explicit, deterministic and cross-domain. Unknown values fail closed.

## 13. Reserved evidence identity QA

PASS with bounded implementation requirement.

`document_validator_execution` and `document_qa_record` are cross-domain core Evidence type IDs.

Domain packages must not redefine these names incompatibly.

This is analogous to DG-P4 reserved core artifact protection and does not create new storage.

## 14. Future DocumentChangeSet dependency

DG-P11 does not exist yet.

P5 may reserve `DOCUMENT_CHANGE_SET` as a future subject kind, but implementation must fail closed on unresolved/dangling change-set refs.

P5 must not create a placeholder DocumentChangeSet subsystem to satisfy its own interface.

## 15. Fixture adequacy

D5-F1 through D5-F20 cover:

- Evidence reuse;
- zero-to-many findings;
- exact revision binding;
- prior-PASS invalidation by revision change;
- tool failure separation;
- legal/illegal finding transitions;
- stale finding version;
- exact resolution verification;
- fingerprint stability;
- waiver/approval reuse;
- non-waivable classes;
- waiver expiration semantics;
- transaction rollback;
- reserved evidence collision;
- existing Evidence regression;
- no later-wave state mutation.

**Fixture verdict: PASS.**

## 16. Finding adjudication

- F-64 — duplicate QA persistence risk: resolved by mapping DocumentQARecord to PRIM-EVIDENCE.
- F-65 — finding-state semantic mismatch: resolved by one dedicated current-state table only.
- F-66 — Evidence writer atomicity boundary: resolved by bounded transactional extension requirement.
- F-67 — stale QA transfer risk: resolved by exact current-revision identity check.
- F-68 — severity vocabulary unspecified: resolved by bounded core severity vocabulary.
- F-69 — waiver duplication/authority risk: resolved by Proposal/Approval reuse and non-waivable core classes.
- F-70 — cross-domain Evidence type collision risk: resolved by reserved core evidence IDs.
- F-71 — future DocumentChangeSet dependency risk: resolved by reserved subject kind + fail-closed until DG-P11 exists.

All are specification-resolved. None implies runtime implementation has occurred.

## 17. Scope QA

PASS.

The frozen specification does not authorize:

- DG-P6 validity/lifecycle mutation;
- BLOCKED state mapping;
- authority claims;
- relation graph;
- change classification;
- DocumentChangeSet implementation;
- GAC;
- Reference Acquisition;
- G2E;
- auto-fix/source mutation.

## 18. Document QA verdict

```text
DG-P4 dependency                    = PASS
DocumentQARecord -> PRIM-EVIDENCE   = PASS
ValidatorExecution -> PRIM-EVIDENCE = PASS
DocumentFinding primitive reuse     = INSUFFICIENT
new finding current-state table     = JUSTIFIED
dedicated QA table                  = REJECTED
dedicated validator table           = REJECTED
waiver -> Proposal/Approval         = PASS
history -> append-only Audit        = PASS
Evidence writer atomic extension    = REQUIRED
D5-F1..F20                           = ADEQUATE
findings F-64..F-71                 = RESOLVED
OPEN                                = 0
```

**DG-P5 PRE-IMPLEMENTATION QUALIFICATION: PASS**

Implementation remains NOT_STARTED.
