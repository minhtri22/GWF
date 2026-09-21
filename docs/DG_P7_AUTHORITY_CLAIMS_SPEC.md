# GWF — DG-P7 Authority Claims / Duplicate-Authority Specification

## 1. Status

**Item:** DG-P7 — Authority claims + duplicate-authority detection  
**Wave:** 3 — Semantic Documentation Governance  
**Specification state:** FROZEN FOR DOCUMENT QA  
**Implementation state:** NOT_STARTED  
**Authorization state:** PRE-IMPLEMENTATION SPECIFICATION / DEPENDENCY QUALIFICATION ONLY

DG-W2 is formally closed. This document qualifies the semantic mapping for document source-of-truth authority. It does not authorize runtime implementation, migration execution, DG-P8+, Wave-3 closure, GAC, Reference Acquisition or G2E.

## 2. Exact dependency evidence

DG-P7 starts from exact DG-W2 formal-close state:

- DG-W2 final formal-close HEAD: `f14abb9d8d8a591558ac6d4624a498eb32164726`
- DG-W2 final exact-head workflow: `35603521224` PASS
- DG-W2 final evidence artifact: `10641345237`
- final artifact digest: `sha256:2e317a0becd2567a3932154b1d78447802a0672f56df2dde475462311395928e`

Relevant governing/runtime blobs at the exact base:

| Artifact | Git blob |
| --- | --- |
| `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` | `e50d0f17433c6f0ec57f987278a0d24a7bbd4610` |
| `docs/IMPLEMENTATION_7_WAVES_PLAN.md` | `3de3ffdbefeaeb3f644e2c2b6daf5e3b7d46098b` |
| `src/gwr/governance.py` | `0eb8f3eeb7a6ee01512bc778241fa2ee0b42f6a6` |
| `src/gwr/knowledge.py` | `387f98b47575bc889e9bf88057fd010af2dce853` |
| `src/gwr/domain.py` | `387f98b47575bc889e9bf88057fd010af2dce853` is NOT the knowledge blob; exact file blobs are independently verified during document QA. |
| `src/gwr/document_qa.py` | exact base version contains `DUPLICATE_AUTHORITY` and marks it non-waivable |
| `src/gwr/db.py` | exact base schema has no document-authority-claim table |
| `src/gwr/migrations.py` | Wave-2 migration frontier ends at `0008_v086_dg_p5_document_findings` |

The document-QA phase must re-read exact blobs rather than rely on the explanatory table if any listed identity is stale.

## 3. Central semantic question

DG-P7 asks:

> Which parts of document source-of-truth authority can safely reuse existing GWF primitives, and what minimal new persistence is required to represent multiple mutable authority claims without overloading actor authorization, Artifact/Revision, or Evidence semantics?

The governing distinction is:

```text
actor action authority
    !=
document source-of-truth authority
```

Existing `PRIM-AUTHORITY` / `authority_policies` answers:

> "May actor A perform action X on resource Y?"

DG-P7 authority claims answer:

> "Which governed document currently owns proposition/contract key K within scope S?"

These are related governance concerns but are not the same state.

## 4. Semantic-fit matrix

| DG-P7 requirement | Existing primitive | Fit | Decision |
| --- | --- | --- | --- |
| logical authority owner identity | Artifact | exact | reuse document `artifact_id` |
| exact provenance when claim granted | Revision | exact | reuse exact `revision_id` |
| actor permission to grant/retire claims | PRIM-AUTHORITY / authority policies | exact for mutation authorization only | reuse, do not store claims there |
| approval for authority mutation | Proposal / Approval | strong | reuse |
| immutable mutation history | Audit | strong | reuse |
| duplicate-authority QA execution | PRIM-EVIDENCE | strong | reuse existing document validator/QA evidence |
| duplicate-authority finding lifecycle | DocumentFinding | exact | reuse P5 `DUPLICATE_AUTHORITY` |
| clean-state blocking | P6 effective validity | exact | reuse active non-waivable finding -> BLOCKED |
| current set of zero-to-many authority claims per document | Artifact | insufficient cardinality without overload | do not encode into Artifact logical key |
| current claim state | Revision payload | insufficient as logical-document current state; would couple claim lifetime to every content revision | do not use as canonical claim store |
| current claim state | Evidence | insufficient; immutable evidence is observation, not canonical mutable ownership | do not use as claim store |
| current claim state | authority_policies | wrong semantic axis; actor authorization rather than source-of-truth ownership | do not use |
| composition membership/policy | Proposal / Approval frozen payload | sufficient for bounded P7 | reuse; no composition table |

## 5. Why existing PRIM-AUTHORITY must not become the claim store

`authority_policies` currently contains:

- subject selector;
- resource selector;
- allowed actions;
- conditions;
- ALLOW/DENY effect;
- priority.

It is evaluated by `GovernanceKernel.authorize()` against an **actor + action + resource** request.

A document claim instead requires:

- owner document;
- authority scope;
- authority key;
- authority mode;
- active/retired claim lifecycle;
- grant provenance;
- composition contract if applicable.

Reusing `authority_policies` for document ownership would:

1. mix actor permissions with source-of-truth ownership;
2. make actor-policy priority accidentally influence document authority;
3. make document collision detection depend on authorization selectors;
4. prevent clean reconstruction of "who owns this authority key?";
5. create ambiguity when the same document has several independent claims.

Therefore DG-P7 reuses PRIM-AUTHORITY only to authorize claim mutations.

## 6. Why Evidence must not be canonical claim state

Evidence is append-only attributable observation.

Authority ownership is current governance state.

Encoding claim grant/retirement as latest-wins Evidence would require:

- ordering evidence to reconstruct state;
- inferring retirement from later evidence;
- ambiguous concurrent grants;
- no optimistic current-state version;
- collision logic over a historical event stream.

Evidence remains appropriate for:

- authority collision scan execution;
- exact inputs examined;
- duplicate/non-duplicate result;
- QA attribution.

It is not the source of current authority ownership.

## 7. Why Artifact/Revision alone are insufficient

### 7.1 Artifact

`Artifact` provides one logical identity and one project-unique logical key.

One governed document may hold multiple authority claims.

Encoding each claim into the document logical key would violate document identity and cardinality.

Creating a second `authority_claim` Artifact type would turn claim metadata into a parallel artifact subsystem and complicate ownership, composition and retirement semantics unnecessarily.

DG-P7 therefore does **not** create an authority-claim Artifact type.

### 7.2 Revision payload

A Revision is immutable and exact.

It is useful as provenance for **when a claim was granted**, but it is not the correct canonical lifetime for logical-document authority.

A document claim can remain owned by the same logical document across editorial/content revisions. Binding the claim exclusively to one current Revision would either:

- silently drop authority on every new revision; or
- require automatic claim copying into each new revision.

Both behaviors would create hidden semantic coupling.

DG-P7 therefore records the exact grant Revision as provenance but stores current claim state separately.

## 8. Minimal persistence decision

Semantic-fit analysis justifies exactly one new current-state table:

```text
document_authority_claims
```

No other P7 table is justified.

Conceptual columns:

```text
claim_id                     PRIMARY KEY
project_id
document_id                  -> existing governed_document Artifact
authority_scope
authority_key
mode                         PRIMARY | COMPOSED
composition_role             nullable unless COMPOSED
composition_policy_ref       nullable unless COMPOSED
composition_policy_hash      nullable unless COMPOSED
status                       ACTIVE | RETIRED
granted_revision_id          exact Revision provenance
grant_proposal_id
retired_by_proposal_id       nullable
version                      optimistic current-state version
created_at
updated_at
retired_at                   nullable
```

Required indexes should support:

- `(project_id, authority_scope, authority_key, status)`;
- `(document_id, status)`.

There is deliberately no database UNIQUE constraint over `(project_id, scope, key)`, because:

- duplicate authority is a representable governance violation that must remain observable;
- valid COMPOSED ownership may contain more than one claim;
- imported/race-created invalid states must be detectable and blockable rather than becoming unrepresentable.

Mutation services must nevertheless perform transactional collision evaluation before committing a new ACTIVE claim.

## 9. Claim identity and normalization

Authority collision identity is project-local:

```text
(project_id, authority_scope, authority_key)
```

`authority_scope` and `authority_key` are required canonical strings.

Frozen normalization contract:

- trim surrounding whitespace;
- lowercase ASCII;
- length 1..200;
- allowed characters: `a-z 0-9 . _ : - /`;
- first character must be alphanumeric;
- no empty path/token components created by repeated `/`;
- Unicode/confusable variants are rejected rather than silently normalized.

Examples:

```text
scope = research.protocol
key   = execution-amendment

scope = agent.interop
key   = binding
```

A broad scope alone does not collide if authority keys differ.

## 10. Claim lifecycle

P7 claim lifecycle is intentionally minimal:

```text
ACTIVE -> RETIRED
```

Rules:

- grant creates a new ACTIVE claim;
- scope/key/mode are immutable after grant;
- changing scope/key/mode is retire-old + grant-new;
- retirement never deletes history;
- optimistic `version` protects stale claim retirement;
- Audit records grant and retirement;
- grant/retirement must pass project mutable check, actor authorization and approved Proposal.

No automatic silent claim mutation is allowed.

## 11. Effective authority ownership

An ACTIVE claim is an **effective authority owner** only when:

1. the owner exists and is a `governed_document`;
2. the document belongs to the same project;
3. document lifecycle is `ACTIVE` or `DEPRECATED`;
4. claim status is `ACTIVE`.

Lifecycle behavior:

- `DRAFT` / `IN_REVIEW`: claim may exist as approved state but is not an effective current owner;
- `ACTIVE`: claim is eligible;
- `DEPRECATED`: claim remains eligible during bounded transition until explicitly retired/replaced;
- `SUPERSEDED` / `ARCHIVED`: claim is never an effective owner.

Document validity does **not** silently transfer or erase ownership.

A blocked/stale/unverified document may still be the recorded authority owner; the affected scope simply cannot achieve clean governed use until validity/finding obligations are resolved.

This prevents invalidity from accidentally transferring authority to another document.

## 12. Explicit authority only

No document acquires authority because of:

- document class;
- filename/path;
- title;
- Markdown heading;
- README status;
- references/links;
- summary wording;
- current lifecycle alone;
- validator PASS;
- Artifact type alone.

An INFORMATIVE summary without an explicit approved claim owns no authority.

This directly satisfies the "informative summary does not acquire authority" requirement.

Document class may later contribute policy constraints, but P7 does not infer claims from class.

## 13. PRIMARY claims

`PRIMARY` is the default source-of-truth ownership mode.

For one effective collision identity:

```text
(project_id, scope, key)
```

clean authority requires at most one effective PRIMARY owner.

If two or more effective claims exist and the composition exception below does not apply, authority collision QA emits `DUPLICATE_AUTHORITY`.

## 14. COMPOSED claims

Multiple documents may intentionally compose one authority key only under an explicit approved composition contract.

P7 reuses Proposal / Approval rather than creating a composition-policy table.

A composition contract is an approved frozen Proposal whose payload binds:

- exact project;
- authority scope;
- authority key;
- exact member document IDs;
- a unique composition role for each member;
- composition rule identifier/version;
- payload hash.

Every COMPOSED claim must store:

- the same `composition_policy_ref`;
- the exact frozen `composition_policy_hash`;
- its declared `composition_role`.

Same-key multiple claims are non-conflicting only when:

1. every effective claim is `COMPOSED`;
2. every claim references the same approved composition Proposal;
3. every claim binds the exact same proposal hash;
4. effective member set equals the proposal member set;
5. each effective member role matches the frozen proposal;
6. no unlisted PRIMARY/COMPOSED owner exists.

Otherwise the cluster is `DUPLICATE_AUTHORITY`.

P7 does not infer composition from document proximity or links.

## 15. Grant and retirement governance

P7 authority mutation must be proposal-backed.

Conceptual actions:

```text
DECLARE_DOCUMENT_AUTHORITY
RETIRE_DOCUMENT_AUTHORITY
DECLARE_COMPOSED_DOCUMENT_AUTHORITY
```

Sequence:

```text
ProjectGovernance.require_mutable
        ↓
GovernanceKernel.authorize(PROPOSE / applicable mutation authority)
        ↓
freeze exact owner document + current revision + claim tuple
        ↓
Proposal / required approval
        ↓
require approved exact payload hash
        ↓
transactional claim mutation
        ↓
Audit
```

The existing authority-policy system determines which actor may propose/approve/execute these governance actions.

It does not become the claim registry.

## 16. Transactional collision rule

P7 must avoid a check-then-write race.

Grant application must evaluate the collision domain and write the claim inside one transaction/serialization boundary.

Required invariant:

```text
read current effective claims for (project, scope, key)
        ↓
validate PRIMARY / COMPOSED contract
        ↓
insert ACTIVE claim
        ↓
re-evaluate resulting cluster
        ↓
commit only with deterministic recorded outcome
```

A knowingly introduced unresolved PRIMARY duplicate must not be represented as a clean successful grant.

Invalid imported/concurrent states must remain detectable by QA and cannot be hidden by uniqueness rejection alone.

Backend implementation strategy is deferred, but SQLite/PostgreSQL behavior must preserve the same invariant.

## 17. Duplicate-authority QA reuse

P7 does not create a new finding subsystem.

Authority scan normalizes through existing P5 QA primitives:

```text
semantic validator execution
    validator_id = gwr-authority-collision
        ↓
document_validator_execution Evidence
        ↓
DocumentQARecord Evidence
        ↓
DUPLICATE_AUTHORITY DocumentFinding
```

`DUPLICATE_AUTHORITY` is already an existing P5 finding class and is already non-waivable.

Each affected current document revision must receive attributable finding evidence sufficient to identify:

- scope;
- key;
- conflicting claim IDs;
- conflicting document IDs;
- composition-policy mismatch reason, if applicable.

No duplicate-authority table is added.

## 18. P6 validity integration boundary

P7 does not add a new validity state.

An OPEN / RESOLVED_PENDING_VERIFY `DUPLICATE_AUTHORITY` finding is already consumed by P6 as a blocking finding.

Therefore:

```text
duplicate authority
      ↓
P5 non-waivable finding
      ↓
P6 document effective BLOCKED
      ↓
kernel cannot remain clean VALID after reconciliation
```

P7 does not directly mutate global validity semantics.

## 19. Revision behavior

Authority claim ownership belongs to the logical document, not to one transient content revision.

`granted_revision_id` records exact provenance of the grant.

Creating a later document revision does not silently create a new claim and does not silently retire an existing claim.

However:

- the new revision begins UNVERIFIED under P4/P6;
- authority/semantic QA for the new revision must be rerun before clean validity;
- P10/P15 will later govern structural/supersession change classification.

This avoids both automatic authority copying and accidental authority loss.

## 20. Scope boundaries

DG-P7 may define only:

- authority-claim persistence contract;
- explicit grant/retire semantics;
- duplicate-authority detection;
- bounded composition contract;
- P5/P6 integration.

DG-P7 must not implement:

- typed document relations (DG-P8);
- LOGICAL_CURRENT / PINNED_REVISION relation semantics (DG-P9);
- change classification (DG-P10);
- DocumentChangeSet (DG-P11);
- source supersession relation execution (DG-P15);
- graph impact propagation;
- GAC;
- Reference Acquisition;
- G2E.

A P7 claim does not imply a P8 `SUPERSEDES` edge.

## 21. Frozen fixture matrix

### D7-F1 — zero claims supported

A governed document may own zero authority claims.

### D7-F2 — one PRIMARY claim

Approved explicit PRIMARY grant creates one ACTIVE claim owned by the logical document.

### D7-F3 — multiple non-conflicting claims

One document may own multiple ACTIVE claims when `(scope,key)` differs.

### D7-F4 — same broad scope, different keys

Two active documents sharing a broad scope but different keys do not collide.

### D7-F5 — duplicate PRIMARY collision

Two effective PRIMARY claims for the same project/scope/key produce `DUPLICATE_AUTHORITY`.

### D7-F6 — informative summary has no implicit authority

A governed summary/README with no explicit claim remains non-authoritative regardless of title/path/content metadata.

### D7-F7 — actor authority is not document authority

An actor allowed to `CREATE_REVISION` or `PROPOSE` does not cause any document authority claim to exist.

### D7-F8 — authority_policies remain actor authorization only

P7 claim state is absent from `authority_policies`.

### D7-F9 — claim provenance exact

Grant records exact document ID, grant revision ID, proposal ID and audit event.

### D7-F10 — stale claim retirement rejected

Retirement with stale claim version fails closed.

### D7-F11 — retirement preserves history

Retired claim is no longer effective but remains queryable and attributable.

### D7-F12 — draft/in-review claim not effective

Claim owned by DRAFT/IN_REVIEW document does not participate as current authority owner.

### D7-F13 — deprecated owner remains bounded authority

DEPRECATED document may remain the effective owner until explicit retirement/replacement.

### D7-F14 — superseded/archived owner ineffective

SUPERSEDED/ARCHIVED documents cannot be effective authority owners.

### D7-F15 — valid COMPOSED cluster

Multiple same-key claims are non-conflicting only when all bind the same approved exact composition contract and exact member roles.

### D7-F16 — composition mismatch collides

Missing member, extra member, mismatched role, policy ref/hash mismatch or PRIMARY outsider produces `DUPLICATE_AUTHORITY`.

### D7-F17 — duplicate authority is non-waivable

P5 rejects waiver preparation/application for `DUPLICATE_AUTHORITY`.

### D7-F18 — duplicate finding blocks effective validity

Current-revision duplicate finding causes P6 effective BLOCKED/non-clean kernel state.

### D7-F19 — new revision does not silently transfer claim state

Claim remains attached to the logical document; no duplicate claim row is auto-created for a new revision, and the new revision still requires fresh QA.

### D7-F20 — no later-wave side effects

Authority grant/scan creates no P8 relation, P9 binding, P10 classification, P11 change set, GAC entry or automatic source edit.

## 22. Pre-implementation acceptance gate

DG-P7 pre-implementation qualification may PASS only if all are true:

- exact DG-W2 formal-close dependency verified;
- actor authority vs document authority distinction frozen;
- Artifact/Revision reuse boundary frozen;
- Evidence reuse boundary frozen;
- Proposal/Approval/Audit reuse frozen;
- exactly one new `document_authority_claims` table justified;
- no authority Artifact type;
- no composition table;
- no duplicate-authority table;
- duplicate QA reuses P5 finding lifecycle;
- duplicate remains non-waivable;
- P6 BLOCKED integration preserved without validity-enum change;
- claim lifecycle and optimistic versioning frozen;
- composition contract exactness frozen;
- transactional collision invariant frozen;
- D7-F1..D7-F20 frozen;
- DG-P8+ remain unopened;
- implementation remains NOT_STARTED;
- Finding checklist OPEN = 0.

## 23. Expected post-qualification state

If document QA passes:

```text
DG-W2                     = FORMALLY_CLOSED
DG-P7 authorization       = PREIMPLEMENTATION_ONLY
DG-P7 specification       = FROZEN
DG-P7 dependency qualify  = PASS
DG-P7 document QA         = PASS
DG-P7 implementation      = NOT_STARTED
DG-P8+                    = NOT_STARTED / NOT_AUTHORIZED
DG-W3                     = OPEN / NOT_EXECUTED
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```

A separate explicit bounded implementation authorization is required before any migration or runtime code is written.
