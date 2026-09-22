# GWF — DG-P10 Change Classification Handoff

## 1. Scope

This handoff records bounded DG-P10 implementation qualification under Amendment 1.

DG-P10 answers three bounded questions for one proposed governed-document revision:

1. what semantic governance class applies;
2. who may authorize the mutation under document role/state + active workflow mode + owner scope;
3. what deterministic archive/version lineage must be frozen.

It does not execute repository source mutation.

## 2. Frozen input identity

- DG-P9 final closure HEAD: `7a081bd8f1f2218859963e304230a8904f56a6eb`
- Amendment 1 reconciled spec commit: `54ca635bcb322902a28f4a987af19c37e14b59ae`
- amended spec blob: `2aeec0ff251567e784372ffb700d11c37fa9a037`
- Documentation Integrity §14 blob: `c1b863784b3ca4bbada7020017818c2340fe5d3b`
- amendment QA HEAD: `5909f289f2426564a6533cfd1453ed6916a3598d`

## 3. Implementation identity

- qualified implementation HEAD: `cc5ec5dc15cf28f7960ddf90a409de7578effe53`
- workflow: `35645249596` PASS

SQLite:
- artifact `10659577518`
- digest `sha256:9f8e75560ca38ac8622aac628fc9f1e1db3c658648ebbaedb2be0faa824b5782`

PostgreSQL 17:
- artifact `10659608214`
- digest `sha256:c6d2a39ffcbe7c9701c717e14f2911f5a03a3cf22f1873c85325b7c051bcdf03`

Windows one-click UAT:
- artifact `10660730609`
- digest `sha256:a7337a7c96120612ce47547532ac427eaf51ff11d5e9bb983a4f34295f0e0139`

## 4. Classification delivered

Exactly five classes:

```text
EDITORIAL
CLARIFICATION
NORMATIVE
STRUCTURAL
SUPERSESSION
```

Classification Evidence is immutable and preserves exact base/proposed identity, QA references, triggers, effective class, workflow mode, owner match and mutation-authority decision.

## 5. Mutation-authority matrix delivered

Document class does not itself decide approver requirements.

Authority consumes:

```text
document role/state
+
active persisted PhaseExecution mode
+
owner scope
+
stronger locks
```

AUTO is limited to owned mutable scope. HUMAN_APPROVE requires human approval. GOV/FROZEN remains blocked until attributable explicit user authorization.

Recovery AUTO semantics are unchanged.

## 6. Version/archive lineage delivered

P10 produces a deterministic plan only:

```text
active vN
  -> archive exact old vN
  -> new active vN+1
  -> human-readable previous-version link
```

Artifact/Revision remains canonical history.

Concrete source mutation remains DG-P11.

## 7. Evidence persistence delivered

No table/migration.

Reserved core PRIM-EVIDENCE type:

```text
document_change_classification
```

No mutable classification-state table exists.

## 8. Enrollment boundary delivered

New enrolled documents may persist:

- document_role;
- governance_state;
- owner phase/workunit;
- document_version;
- previous Revision/archive lineage.

Role and path must agree.

Legacy documents are not silently enrolled or moved.

## 9. Failure preservation

F-142 and F-143 remain documented as resolved negative evidence.

Initial failed workflows remain preserved:

- `35634856064` — enrollment registration wiring regression;
- `35635200766` — Windows fake-validator portability failure.

No failed evidence was deleted or converted into PASS.

## 10. Local one-click UAT

The project README now introduces GWF rather than a release number.

Windows setup:

```powershell
.\install.ps1
```

produces:

```text
.gwr/install/install-report.json
.gwr/install/dg-p10-gate.json
.gwr/uat/UAT.md
.gwr/uat/docs/gov/archive/
.gwr/uat/docs/phase1/archive/
```

The exact one-click path passed GitHub Windows qualification in run `35645249596`.

## 11. Explicit non-scope

DG-P10 does not implement:

- concrete DocumentChangeSet execution;
- archive file creation/deletion;
- multi-document effective-class aggregation;
- impact propagation;
- automatic staleness;
- append-only/supersession execution;
- generated-document provenance;
- DG-W3 closure;
- GAC;
- Reference Acquisition;
- G2E.

## 12. Formal-close criterion

DG-P10 is implementation-qualified at `cc5ec5dc15cf28f7960ddf90a409de7578effe53`.

Formal close requires:

1. commit this implementation QA/handoff/finding/plan/lineage package;
2. rerun the same SQLite/PostgreSQL/Windows qualification on the exact handoff HEAD;
3. require all three jobs PASS;
4. record exact artifacts/digests;
5. commit formal-close state;
6. rerun on final closure HEAD.

DG-P11+ remain unopened throughout formal close.


## 13. Exact-handoff requalification

The committed DG-P10 handoff HEAD `83d7d5c3fcf6a4d4d182af93244bf6e3e1228382` was requalified with the same SQLite/PostgreSQL/Windows workflow.

Workflow:
- `35647135853` PASS

SQLite:
- artifact `10661015045`
- digest `sha256:7fec878f784105e86c9cfed2b4dd888b35cb43e19e83a6e3e91a9ddb5aaeb2ce`

PostgreSQL 17:
- artifact `10660019330`
- digest `sha256:3128253537083b65604c898b80bbf9b08717461280ce24158b69ed1ef523b7ae`

Windows one-click/UAT:
- artifact `10661103663`
- digest `sha256:4f5eec01b8b269d2e92e0b9cd19a9dc18637ce4987b787e36d33c654769b2444`

The exact committed handoff HEAD again passed:

- D10-F1..D10-F20 on SQLite;
- bounded DG-P10 gate;
- P4/P5/P7/P8/P9 targeted regressions;
- full repository regression;
- compile;
- D10/gate on PostgreSQL 17;
- Windows one-click installation;
- full Windows repository tests;
- Windows UAT report assertions and evidence upload.

No runtime/spec/test semantics changed after implementation qualification.

## 14. Formal-close state

DG-P10 now satisfies the formal-close prerequisites at the committed handoff HEAD.

This formal-close state does **not** authorize DG-P11.

A final exact-head workflow on the formal-close commit is required as closure confirmation.

```text
DG-P10 implementation QA       = PASS
DG-P10 exact-handoff requal     = PASS
Finding OPEN                   = 0
DG-P10 formal-close state       = COMMITTED
DG-P11+                         = NOT_STARTED / NOT_AUTHORIZED
DG-W3                           = OPEN / NOT_EXECUTED
GAC                             = LOCKED_UNTIL_DG-W4_PASS
```
