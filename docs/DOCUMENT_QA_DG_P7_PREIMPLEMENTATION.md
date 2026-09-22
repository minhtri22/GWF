# GWF — DG-P7 Pre-Implementation Document QA

## 1. QA identity

**Item:** DG-P7 — Authority claims + duplicate-authority detection  
**Subject:** `docs/DG_P7_AUTHORITY_CLAIMS_SPEC.md`  
**Canonical subject commit:** `f226eb8e01b2284381ba0e7cf5527518512c7ce7`  
**Canonical subject blob:** `63d2252314e753b7485f1a0249dc011468be275b`  
**Dependency base:** DG-W2 final formal-close HEAD `f14abb9d8d8a591558ac6d4624a498eb32164726`  
**Dependency final exact-head workflow:** `35603521224` PASS  
**Dependency final artifact:** `10641345237`  
**Dependency artifact digest:** `sha256:2e317a0becd2567a3932154b1d78447802a0672f56df2dde475462311395928e`  
**QA type:** pre-implementation semantic/dependency qualification  
**Implementation executed:** NO

## 2. Governing requirement verification

Documentation Integrity §9 requires:

- explicit authority claims;
- authority scope + key;
- default one active owner per key;
- multiple non-conflicting claims;
- explicit composition when multiple same-key owners are valid;
- duplicate active authority to produce `DUPLICATE_AUTHORITY`;
- informative summaries not to acquire authority implicitly.

The BUILD/INTEGRATE matrix also requires GWF-native authority/source-of-truth semantics and collision detection.

## 3. Existing primitive semantic-fit verdict

### PRIM-AUTHORITY / authority_policies

**PARTIAL REUSE ONLY.**

Existing authority policies govern actor permission to execute actions.

They do not model document source-of-truth ownership.

Therefore:

```text
actor permission to mutate a claim -> REUSE PRIM-AUTHORITY
claim state itself                 -> DO NOT store in authority_policies
```

### Artifact / Revision

**REUSE FOR OWNER IDENTITY + PROVENANCE.**

- document owner = existing governed_document Artifact;
- exact grant provenance = existing Revision.

They are insufficient as canonical zero-to-many current claim storage.

### Evidence

**REUSE FOR QA/COLLISION EVIDENCE ONLY.**

Evidence remains immutable observation.

It is not current authority ownership state.

### Proposal / Approval / Audit

**REUSE.**

They are sufficient for:

- authority grant authorization;
- retirement authorization;
- exact composition contract payload;
- approval evidence;
- mutation history.

No separate waiver/composition/history table is justified.

## 4. Persistence qualification

PASS.

Exactly one new bounded current-state table is justified:

```text
document_authority_claims
```

Reason:

- one document may own zero-to-many claims;
- claim lifetime is logical-document-level rather than revision-level;
- claims must be individually retired/versioned;
- Evidence cannot act as mutable state;
- authority_policies have the wrong semantic axis;
- Artifact logical identity must not be overloaded;
- collision state must remain observable.

Rejected persistence:

```text
authority_claim Artifact type      REJECTED
document_authority_evidence store  REJECTED
composition_policy table           REJECTED
duplicate_authority table          REJECTED
document authority in policy table REJECTED
```

## 5. Table contract QA

The frozen conceptual table contains:

- claim identity;
- project/document ownership;
- scope/key;
- PRIMARY/COMPOSED mode;
- exact composition ref/hash/role when applicable;
- ACTIVE/RETIRED current status;
- exact grant revision provenance;
- proposal references;
- optimistic version;
- timestamps.

No UNIQUE constraint on `(project,scope,key)` is required because duplicate authority is a representable governance violation and valid composition may have multiple same-key members.

Service-level transactional evaluation is mandatory.

## 6. Claim normalization QA

PASS.

Collision identity is:

```text
(project_id, authority_scope, authority_key)
```

Canonical string normalization is frozen and rejects ambiguous Unicode/confusable variants rather than silently normalizing them.

This makes collision matching deterministic.

## 7. Claim lifecycle QA

PASS.

Frozen lifecycle:

```text
ACTIVE -> RETIRED
```

Scope/key/mode are immutable after grant.

Change = retire old claim + grant new claim.

No deletion is used to hide historical ownership.

Optimistic versioning is required for retirement.

## 8. Effective owner projection QA

PASS.

Effective ownership requires:

- governed_document owner;
- same project;
- claim ACTIVE;
- document lifecycle ACTIVE or DEPRECATED.

Not effective:

- DRAFT;
- IN_REVIEW;
- SUPERSEDED;
- ARCHIVED.

Validity is deliberately not used to silently transfer ownership.

A blocked authority document remains the recorded owner while the scope is unusable for clean governance.

## 9. Informative-document QA

PASS.

The frozen contract never infers authority from:

- title;
- path;
- README status;
- links;
- headings;
- Artifact type;
- lifecycle alone;
- validator PASS;
- document class alone.

Therefore an informative summary without an explicit approved claim remains non-authoritative.

This also preserves the governing statement that document class does not itself grant authority.

## 10. PRIMARY collision QA

PASS.

Two or more effective same-key claims are duplicate authority unless the exact bounded composition exception applies.

The default invariant remains:

```text
one active authoritative owner
per (project, scope, key)
```

## 11. Composition reuse QA

PASS.

P7 does not create a composition table.

An approved frozen Proposal is sufficient to bind:

- project;
- scope;
- key;
- exact member documents;
- unique member roles;
- composition rule identity/version;
- payload hash.

Same-key claims are non-conflicting only when every effective member binds the same exact approved composition contract and member set.

No link or adjacency inference is permitted.

## 12. Duplicate-authority finding reuse QA

PASS.

Existing P5 runtime already defines:

```text
DUPLICATE_AUTHORITY
```

and includes it in:

```text
NON_WAIVABLE_CLASSES
```

Therefore P7 collision detection reuses:

```text
document_validator_execution Evidence
        ↓
DocumentQARecord Evidence
        ↓
DocumentFinding(DUPLICATE_AUTHORITY)
```

No new finding table or collision table is necessary.

## 13. P6 integration QA

PASS.

P6 already treats active DocumentFindings as blockers.

Therefore duplicate authority can flow through existing semantics:

```text
DUPLICATE_AUTHORITY
        ↓
non-waivable P5 finding
        ↓
effective document BLOCKED
        ↓
kernel cannot remain clean VALID
```

No new global validity state is introduced.

## 14. Revision-boundary QA

PASS.

Authority belongs to the logical document.

The claim records the exact revision at which it was granted, but later source revisions do not:

- silently duplicate the claim;
- silently retire the claim;
- silently transfer ownership elsewhere.

The new revision still begins UNVERIFIED and needs fresh exact QA.

This keeps logical authority and revision validity separate.

## 15. Transaction/concurrency QA

PASS as a frozen implementation requirement.

A P7 grant must evaluate the collision domain and insert within one transaction/serialization boundary.

A check-then-write race is forbidden.

The schema intentionally does not hide conflict states behind a UNIQUE constraint because:

- composed claims may legitimately share a key;
- invalid imported/race states must remain observable and adjudicable.

Backend-specific locking is deferred to bounded implementation, but SQLite/PostgreSQL behavior must be semantically equivalent.

## 16. Scope-boundary QA

PASS.

DG-P7 specification does not open:

- DG-P8 typed relations;
- DG-P9 binding modes;
- DG-P10 change classification;
- DG-P11 change sets;
- DG-P15 supersession execution;
- graph propagation;
- GAC;
- Reference Acquisition;
- G2E.

A P7 claim is not a P8 relation.

## 17. Frozen fixture adequacy

D7-F1 through D7-F20 cover:

- zero claims;
- single PRIMARY;
- multiple non-conflicting claims;
- same scope/different keys;
- duplicate PRIMARY;
- no implicit informative authority;
- actor authority != document authority;
- no claim state in authority_policies;
- exact provenance;
- stale retirement;
- retirement history;
- lifecycle effectiveness;
- COMPOSED success/failure;
- non-waivability;
- P6 blocking;
- revision continuity;
- no later-wave side effects.

**Fixture verdict: ADEQUATE.**

## 18. Finding adjudication

- F-85 — incorrect dependency blob identity in initial spec: resolved by exact re-read and canonical spec correction.
- F-86 — actor authorization/document authority conflation: resolved by strict semantic split.
- F-87 — Evidence-as-current-claim-state misuse: resolved by Evidence-only QA role.
- F-88 — Artifact/Revision claim-overload risk: resolved by identity/provenance-only reuse.
- F-89 — current claim persistence gap: resolved by exactly one bounded `document_authority_claims` table.
- F-90 — composition-subsystem duplication risk: resolved by Proposal/Approval frozen contract reuse.
- F-91 — duplicate-authority waiver risk: resolved by existing P5 non-waivable class.
- F-92 — ownership/validity conflation risk: resolved by keeping ownership independent from validity.
- F-93 — concurrent grant race: resolved by frozen transactional collision invariant.
- F-94 — implicit authority inference risk: resolved by explicit-approved-claim-only rule.

All are specification/document-state resolved.

No runtime implementation has occurred.

## 19. Document QA verdict

```text
DG-W2 dependency                        PASS
actor authority reuse boundary          PASS
Artifact/Revision reuse boundary        PASS
Evidence reuse boundary                 PASS
Proposal/Approval/Audit reuse           PASS
new authority Artifact                  REJECTED
new composition table                   REJECTED
new duplicate-authority table           REJECTED
document_authority_claims table         JUSTIFIED / EXACTLY ONE
claim lifecycle                         PASS
collision identity                      PASS
PRIMARY semantics                       PASS
COMPOSED exact-contract semantics       PASS
DUPLICATE_AUTHORITY P5 reuse            PASS
DUPLICATE_AUTHORITY non-waivable        PASS
P6 BLOCKED integration                  PASS
transactional collision invariant       PASS
D7-F1..D7-F20                           ADEQUATE
DG-P8+ opened                           NO
implementation                          NOT_STARTED
Finding OPEN                            0
```

**DG-P7 PRE-IMPLEMENTATION QUALIFICATION: PASS**
