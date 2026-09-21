# GWF — DG-W2 Wave 2 Exit-Gate Handoff

## 1. Scope

DG-W2 closes the Minimal Documentation Kernel wave only after DG-P4, DG-P5 and DG-P6 are requalified together on one exact repository HEAD.

No Wave-3 implementation is part of this handoff.

## 2. Dependency chain

```text
DG-W1 FORMALLY_CLOSED
    ↓
DG-P4 FORMALLY_CLOSED
    ↓
DG-P5 FORMALLY_CLOSED
    ↓
DG-P6 FORMALLY_CLOSED
    ↓
DG-W2 combined requalification
```

DG-P6 formal-close dependency:

- HEAD `0c09d16e6a1fe6e01081015f2d7490ba07e58316`
- exact-head workflow `35598967419` PASS
- artifact `10637877732`

## 3. DG-W2 qualification identity

- QA infrastructure initial HEAD: `d5307d116b81f95bf8ee386685846522487cb249`
- workflow-newline repair / qualified QA HEAD: `bdce1392db5e54597a12e5de02d4d916aa081b6f`
- workflow: `35602717476` PASS
- evidence artifact: `10638479929`
- digest: `sha256:9fd5937a0c87dd51c9f6b10148bcea64fe1c0e65a9431b788a5933a7bd3f0f15`

## 4. Same-head component evidence

DG-P4, P5 and P6 each returned PASS from the exact same Wave-2 checkout.

P4 additionally used a real GitHub read against exact commit `bdce1392...` and repository ID `1374857546`.

The component gate artifacts are bundled with `DG_W2_QA.json` in the DG-W2 evidence artifact.

## 5. Cross-wave proof

The integrated gate proves:

```text
D / R1 / QA(R1) PASS
    ↓
R1 VALID
    ↓
same D gets R2
    ↓
R1 SUPERSEDED
R2 UNVERIFIED
QA(R1) not current
    ↓
QA(R2) FAIL + finding
    ↓
R2 effective BLOCKED
R2 kernel non-VALID
```

Therefore exact QA validity is revision-scoped and cannot leak across revisions.

## 6. Persistent ownership after Wave 2

```text
Document identity       Artifact
Revision identity       Revision
QA record               Evidence
Validator execution     Evidence
Finding current state   document_findings
Waiver                   Proposal/Approval
History                  Audit
Lifecycle                Artifact.lifecycle_status
Kernel validity          Revision.validity_state
Document BLOCKED         derived effective projection
```

No duplicate DocumentRecord/DocumentRevision/QA/validity/lifecycle subsystem exists.

## 7. Schema decisions

```text
P4: no migration
P5: one migration -> document_findings
P6: no migration
```

No later-wave schema is admitted by DG-W2.

## 8. Wave-3 boundary

DG-W2 qualification does not implement or pre-authorize:

- DG-P7 authority claims;
- duplicate-authority detection;
- DG-P8 typed document relations;
- DG-P9+;
- GAC;
- Reference Acquisition;
- G2E.

Only after DG-W2 is formally closed may Wave-3 pre-implementation work be considered under a separate authorization.

## 9. Negative evidence

Run `35602654364` is preserved.

It failed before job creation because the newly generated workflow file contained literal escaped newline sequences.

Repair commit `bdce1392...` changed only workflow newline serialization.

## 10. Formal-close criterion

DG-W2 qualification is PASS at `bdce1392db5e54597a12e5de02d4d916aa081b6f`.

Formal close requires:

1. commit this QA/handoff/finding/plan/lineage package;
2. rerun the same DG-W2 workflow on that exact handoff HEAD;
3. require same-head P4/P5/P6, cross-wave gate, regressions, full suite and compile to PASS;
4. record exact workflow and artifact identities;
5. commit formal-close state;
6. re-run the same gate on the final closure HEAD.

Until then Wave 3 remains unopened.


## 11. Exact-handoff qualification

The committed DG-W2 handoff HEAD `be02cdd7eaeadc0534631f15fbe183ddb4b6c7f3` was requalified with the same combined Wave-2 gate.

- exact-head workflow: `35603196674`
- conclusion: **PASS**
- evidence artifact: `10640780655`
- artifact digest: `sha256:1c52ad48c2d4b38995325b4b34e55520dd0ed24d772f6b20fe3d7e14176525db`

The exact committed handoff HEAD again passed:

- combined D4/D5/D6 fixtures;
- real P4 provider gate;
- P5/P6 component gates;
- cross-wave exact-revision invalidation;
- no-duplicate-subsystem/schema checks;
- targeted regressions;
- full regression;
- compile.

**DG-W2 status: FORMALLY CLOSED.**

Wave 3 is dependency-unlocked only. DG-P7/P8 remain NOT_STARTED / NOT_AUTHORIZED. GAC remains locked until DG-W4 PASS.
