# GWF — DG-P7 Implementation QA

## 1. QA identity

**Qualified implementation HEAD:** `3f993ac639c8cb3147d0dc8d888c8b5266e54914`  
**Frozen specification commit:** `f226eb8e01b2284381ba0e7cf5527518512c7ce7`  
**Frozen specification blob:** `63d2252314e753b7485f1a0249dc011468be275b`  
**Pre-implementation qualification HEAD:** `7a62d97a8059adb08f0ae7be44a1285d8ee18410`  
**Workflow:** `35610704812` PASS

SQLite evidence:
- artifact `10644396006`
- digest `sha256:dd838a1512d649cc1fce18d52b594699ca2e4395a2ca6cac624ba08aefd3d460`

PostgreSQL 17 evidence:
- artifact `10644450806`
- digest `sha256:cdcb6079b3e759286161d653a6e0924988826f8aa715be0400c0ba335cd8f972`

## 2. Bounded implementation surface

Implementation changed exactly:

- `src/gwr/migrations.py`
- `src/gwr/document_authority.py`
- `src/gwr/runtime.py`
- `tests/test_dg_p7_authority.py`
- `tools/run_dg_p7_gate.py`
- `.github/workflows/dg-p7-authority.yml`

No DG-P8 relation subsystem, binding mode, change-set persistence, GAC state, Reference Acquisition state or source mutation was added.

## 3. Persistence QA

PASS.

Exactly one P7 migration was added:

```text
0009_v086_dg_p7_document_authority_claims
        ↓
document_authority_claims
```

The table stores:

- logical owner document;
- exact grant revision provenance;
- normalized scope/key;
- PRIMARY/COMPOSED mode;
- exact composition role/proposal/hash where applicable;
- ACTIVE/RETIRED state;
- grant/retirement proposal references;
- optimistic version;
- timestamps.

Indexes exist for collision-domain and owner lookup.

Not added:

```text
authority-claim Artifact type
composition table
duplicate-authority table
document-relations table
change-set table
```

## 4. Actor authority versus document authority

PASS.

Existing `authority_policies` remain unchanged by authority-claim operations.

They continue to govern actor/action authorization.

Document source-of-truth state exists only in `document_authority_claims`.

The bounded gate snapshots `authority_policies` before and after a grant and proves equality.

## 5. Proposal / Approval / Audit governance

PASS.

PRIMARY, COMPOSED and retirement mutation use:

```text
PROPOSE
    ↓
frozen proposal payload/hash
    ↓
existing approval policy
    ↓
human Approval
    ↓
approved exact proposal
    ↓
claim mutation
    ↓
Audit
```

Runtime proposal dispatch now delegates the three DG-P7 actions to `DocumentAuthorityService` without changing existing CREATE_REVISION dispatch.

Grant audit records exact proposal and approval IDs.

## 6. Claim normalization and identity

PASS.

Collision identity is:

```text
(project_id, authority_scope, authority_key)
```

Scope/key/role/rule identifiers use frozen ASCII/lowercase validation.

Ambiguous Unicode values and empty path components are rejected rather than silently normalized.

## 7. PRIMARY semantics

PASS.

A clean PRIMARY claim is an ACTIVE current-state row with exact logical document and grant revision provenance.

Grant is proposal-backed and evaluated against the current collision domain before transaction commit.

A knowingly introduced effective second PRIMARY cannot be committed through the clean grant service.

Imported/invalid duplicate rows remain representable and detectable because the schema intentionally has no UNIQUE(scope,key) constraint.

## 8. COMPOSED semantics

PASS.

Composition creates all member claims atomically from one approved frozen proposal.

Each row stores:

- same composition proposal reference;
- same exact proposal hash;
- exact member role.

A cluster is clean only when:

- all effective claims are COMPOSED;
- proposal ref/hash are identical;
- proposal project/scope/key match;
- effective member set exactly matches frozen members;
- roles exactly match.

Role mismatch, missing effective member or PRIMARY outsider is detected as collision.

No composition table was added.

## 9. Transaction/serialization QA

PASS on both supported database backends.

SQLite:

- existing `Database.tx()` uses `BEGIN IMMEDIATE`;
- collision-domain evaluation + inserts + re-evaluation + audit commit within that transaction.

PostgreSQL:

- P7 acquires `SELECT ... FOR UPDATE` on the project row inside the transaction;
- this serializes P7 claim mutation for the project while preserving duplicate rows as representable data.

The same D7-F1..D7-F20 fixture matrix and bounded gate passed against PostgreSQL 17.

## 10. Claim retirement QA

PASS.

Claim lifecycle:

```text
ACTIVE -> RETIRED
```

Retirement requires:

- approved frozen retirement proposal;
- exact expected claim version;
- optimistic update;
- append-only Audit.

Stale retirement fails closed.

Retired claims remain queryable and cease to be effective owners.

## 11. Lifecycle-effective ownership QA

PASS.

Effective owner projection:

```text
ACTIVE document      -> eligible
DEPRECATED document  -> eligible
DRAFT                 -> not effective
IN_REVIEW             -> not effective
SUPERSEDED            -> not effective
ARCHIVED              -> not effective
```

Authority ownership is not silently transferred by document validity.

## 12. Duplicate-authority QA reuse

PASS.

P7 collision scan does not create a new finding store.

On collision it emits existing P5 primitives:

```text
document_validator_execution Evidence
        ↓
DocumentQARecord Evidence
        ↓
DUPLICATE_AUTHORITY DocumentFinding
```

The gate verifies two imported conflicting effective PRIMARY owners produce two `DUPLICATE_AUTHORITY` findings.

No-collision scan is read-only and emits no QA PASS evidence, preventing an authority-only scan from masking an unrelated content-QA failure in P5/P6 latest-QA semantics.

## 13. Non-waivability and P6 integration

PASS.

Existing P5 `DUPLICATE_AUTHORITY` remains non-waivable.

D7-F17 verifies waiver preparation is rejected.

D7-F18 verifies duplicate-authority finding flows to P6:

```text
DUPLICATE_AUTHORITY
        ↓
OPEN finding
        ↓
document effective BLOCKED
        ↓
kernel no longer clean VALID
```

Global validity vocabulary is unchanged.

## 14. Revision continuity QA

PASS.

A claim belongs to the logical document.

Creating a new document Revision:

- does not duplicate the claim row;
- does not retire the claim;
- preserves the original exact `granted_revision_id` provenance;
- leaves the new revision UNVERIFIED;
- requires fresh QA under existing P4/P5/P6 semantics.

## 15. Frozen fixtures and regression evidence

D7-F1..D7-F20: **20/20 PASS on SQLite**.

D7-F1..D7-F20: **20/20 PASS on PostgreSQL 17**.

SQLite bounded gate: PASS.

PostgreSQL bounded gate: PASS.

Targeted regressions PASS:

- Execution/Decision;
- Knowledge;
- Persistence;
- DG-P4;
- DG-P5;
- DG-P6.

Full repository regression: PASS.

Compile: PASS.

## 16. Finding state

No new implementation defect was discovered in the first qualified run.

The existing cumulative finding ledger remains:

```text
F-01 .. F-94 = RESOLVED
OPEN = 0
```

No artificial finding was introduced solely to create an implementation sequence number.

## 17. Implementation QA verdict

```text
frozen DG-P7 spec preserved                  PASS
migration count                              EXACTLY ONE
document_authority_claims                    PASS
authority_policies semantic isolation        PASS
PRIMARY grant                                PASS
COMPOSED grant                               PASS
Proposal/Approval/Audit                      PASS
optimistic retirement                        PASS
SQLite transaction semantics                 PASS
PostgreSQL serialization semantics           PASS
duplicate-authority QA reuse                 PASS
DUPLICATE_AUTHORITY non-waivable             PASS
P6 BLOCKED integration                       PASS
revision continuity                          PASS
D7-F1..D7-F20 SQLite                         20/20 PASS
D7-F1..D7-F20 PostgreSQL                     20/20 PASS
P4/P5/P6 + governance regressions             PASS
full regression                              PASS
compile                                      PASS
DG-P8+ opened                                NO
DG-W3 closed                                 NO
```

**DG-P7 IMPLEMENTATION QUALIFICATION: PASS**
