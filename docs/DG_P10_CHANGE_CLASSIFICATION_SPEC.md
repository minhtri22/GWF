# GWF — DG-P10 Governed Change Classification Specification

## 1. Status and authorization boundary

**Item:** DG-P10 — Change classification  
**Wave:** 3 — Semantic Documentation Governance  
**Specification state:** FROZEN FOR DOCUMENT QA  
**Implementation state:** NOT_STARTED  
**Authorization state:** PRE-IMPLEMENTATION SPECIFICATION / DEPENDENCY QUALIFICATION ONLY

DG-P9 is formally closed. This specification qualifies how one proposed governed-document revision is classified before authoritative completion.

It does **not** authorize:

- runtime implementation;
- schema migration;
- revision mutation;
- DocumentChangeSet persistence;
- relation-aware impact propagation;
- automatic stale/validity mutation;
- authority retirement or grant;
- lifecycle mutation;
- append-only enforcement;
- generated-only enforcement;
- DG-P11+;
- DG-W3 closure;
- GAC;
- Reference Acquisition;
- G2E.

A separate explicit bounded implementation authorization is required after exact document QA.

## 2. Exact governance frontier

DG-P10 starts from exact DG-P9 final formal-close state:

- DG-P9 final formal-close HEAD: `7a081bd8f1f2218859963e304230a8904f56a6eb`
- final exact-head workflow: `35629863163` PASS
- final SQLite evidence artifact: `10653207627`
- SQLite digest: `sha256:670cc925b42cc348613311e35e251914b5f475c1133d7c0f4c7476569be331e0`
- final PostgreSQL 17 evidence artifact: `10654077365`
- PostgreSQL digest: `sha256:cdafd4bdb59a44feff1e998ff3afa8e67e700d12c9971640caaac1280af6d351`

DG-P9 is the ordering/governance frontier. DG-P10 does not semantically depend on relation binding to classify one document change.

## 3. Hard dependency qualification

The roadmap previously listed only DG-P4 + DG-P7 as DG-P10 hard dependencies.

That is insufficient for the full §13 contract because §13 requires QA to escalate classification, and DG-P5 is the qualified owner of exact-revision QA/finding persistence including the `CHANGE_CLASS_MISMATCH` finding class.

DG-P10 therefore freezes these hard dependencies:

### DG-P4 — exact governed document / revision identity

- final formal-close HEAD: `a11d9ad205272c4c16c49eddb398dee4c8a0ff05`
- final exact-head workflow: `35582578994` PASS
- final evidence artifact: `10630264812`
- digest: `sha256:8dda51c10fceb3b4dfefc119346196c62432bd557b818c1748fa49c5b5c4732b`

DG-P4 supplies stable document identity, exact base Revision identity and exact proposed source identity.

### DG-P5 — QA / finding semantics

- final formal-close HEAD: `58a4cf5f0ca33ca8e15513eb07234dc575b097bc`
- final exact-head workflow: `35585295768` PASS
- final evidence artifact: `10632085985`
- digest: `sha256:a357ba058012ace76d52e5749b83a537759fcfd4215aa74c6355ee722c5ce4a5`

DG-P5 supplies immutable QA Evidence, finding attribution and `CHANGE_CLASS_MISMATCH` vocabulary.

### DG-P7 — document authority semantics

- final formal-close HEAD: `cf143d959b338e8d77811f5b2b79789ccbbb20aa`
- final exact-head workflow: `35611830804` PASS
- final SQLite artifact: `10644398017`
- SQLite digest: `sha256:fba2d1bfc994670522ea27cd1bcb7eeb2c346132ee8802d5ee0ba53693af6945`
- final PostgreSQL artifact: `10644037882`
- PostgreSQL digest: `sha256:f3740de876167d21252e2bf1937dc0650a36dbc923323f059c194aed1756e23c`

DG-P7 supplies explicit authority scope/key semantics needed to identify authority-ownership and supersession triggers without treating actor authority as document authority.

## 4. Exact inspected state

Relevant frozen/runtime state at the DG-P9 closure frontier:

| Artifact | Exact Git blob |
| --- | --- |
| `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` | `e50d0f17433c6f0ec57f987278a0d24a7bbd4610` |
| `docs/IMPLEMENTATION_7_WAVES_PLAN.md` | `706cecc2334c9442c57f88facd984d4eafcf3d9c` |
| `docs/DG_P4_DOCUMENT_FACADE_SPEC.md` | `b0034171454d06dbdeec2145ab73d5fb0cee2982` |
| `docs/DG_P5_QA_FINDING_PERSISTENCE_SPEC.md` | `29ca1c85f665468aade7fc555b634a134af9a46a` |
| `docs/DG_P7_AUTHORITY_CLAIMS_SPEC.md` | `63d2252314e753b7485f1a0249dc011468be275b` |
| `src/gwr/db.py` | `b9825998757423822ab7ffb22bd37dd202f3e30d` |
| `src/gwr/document_facade.py` | current DG-P9 closure blob |
| `src/gwr/document_state.py` | `7b9bbd45199904f0ab6b2bad31c51a61d050bd70` |
| `src/gwr/domain.py` | `387f98b47575bc889e9bf88057fd010af2dce853` |
| `src/gwr/knowledge.py` | `2c4ae7f406031613c1bd885aa90b80b3f6f93606` |

The current `revisions` table has no dedicated `change_class` column.

The current `DocumentFacade.revise_document()` resolves an exact source and then immediately calls `KnowledgeKernel.create_revision()`. There is no qualified pre-commit classification gate yet.

## 5. Governing requirements

Documentation Integrity §13 freezes five change classes:

```text
EDITORIAL
CLARIFICATION
NORMATIVE
STRUCTURAL
SUPERSESSION
```

It also requires:

- every governed edit is classified before authoritative completion;
- each document in a future multi-document change set is classified separately;
- future multi-document effective class equals the strongest triggered class;
- proposer may declare a class;
- QA may escalate;
- an agent may not unilaterally downgrade an escalated class;
- ambiguity between CLARIFICATION and NORMATIVE resolves to NORMATIVE until reviewed;
- diff size is not evidence of editorial status.

Documentation Integrity §14 lists change policies but does not itself assign persistence or executable enforcement to DG-P10.

## 6. Central semantic question

DG-P10 asks:

> How can GWF deterministically adjudicate the governance class of one exact proposed governed-document revision **before** it becomes the current Revision, while allowing QA escalation and preventing agent downgrade?

The answer frozen here is:

```text
exact current base Revision
        +
exact proposed source identity
        +
proposer declaration
        +
structured semantic trigger claims
        +
QA escalation signals
        ↓
single-document classification adjudication
        ↓
immutable classification Evidence
        ↓
required governance decision
        ↓
ONLY THEN future revision mutation
```

Classification is a governance adjudication, not a post-hoc label.

## 7. Classification vocabulary

### EDITORIAL

Formatting, spelling, punctuation, layout or presentation with no intended semantic effect.

EDITORIAL must not be inferred merely from a small diff.

### CLARIFICATION

Removes ambiguity or makes an existing contract explicit while claiming no intended normative change.

CLARIFICATION is provisional until semantic QA finds no normative trigger.

### NORMATIVE

Changes a rule, requirement, invariant, threshold, protocol, architecture contract, policy meaning, authority requirement or required behavior.

### STRUCTURAL

Changes document decomposition, stable identity, relation topology, dependency topology, authority ownership shape or other governed structure.

STRUCTURAL classification does not itself execute those structural mutations.

### SUPERSESSION

Introduces replacement authority for a scope/key and retires/replaces prior authority semantics.

SUPERSESSION classification does not itself retire P7 claims, create P8 relations or change lifecycle.

## 8. Governance rank

The governing document says the strongest triggered class wins but does not define an order.

DG-P10 freezes this governance rank:

```text
EDITORIAL      = 0
CLARIFICATION  = 1
NORMATIVE      = 2
STRUCTURAL     = 3
SUPERSESSION   = 4
```

This rank is an adjudication/escalation order, not a claim that every higher class semantically contains every lower class.

If multiple independent triggers apply, effective class is the maximum rank.

## 9. Single-document scope boundary

DG-P10 classifies exactly one proposed document revision at a time.

It returns one:

```text
effective_change_class
```

DG-P10 does **not** create or persist a multi-document `DocumentChangeSet`.

Future DG-P11 owns:

- multiple target documents;
- per-document declared/effective classes in one frozen scope;
- change-set-wide `effective_change_class = max(per-document classes)`;
- allowed paths;
- dependency/impact snapshots.

This prevents DG-P10 from preempting DG-P11.

## 10. Exact classification subject

A classification subject must be immutable and attributable before commit.

Minimum subject:

```text
project_id
document_id
base_revision_id
expected_artifact_version
candidate_source:
  provider
  repository_id
  exact_commit_sha
  path_locator
  exact_blob_sha
  content_sha256
classification_policy_version
```

Rules:

1. `base_revision_id` must equal the document's current Revision when classification begins.
2. `expected_artifact_version` must equal the current Artifact version.
3. proposed source identity must be exact; mutable branch/path alone is insufficient.
4. the candidate source must belong to the same governed document mutation context.
5. if current Revision or Artifact version changes before commit, classification is stale and must not authorize the revision.
6. classification of initial document registration is outside DG-P10 because no prior governed base Revision exists.

## 11. Pre-commit invariant

DG-P10 classification must occur before `KnowledgeKernel.create_revision()` mutates the document.

Current P4 behavior:

```text
resolve candidate
        ↓
create Revision immediately
```

is insufficient once P10 is implemented.

Future bounded implementation must introduce:

```text
resolve exact candidate
        ↓
classify / adjudicate / required governance
        ↓
verify base + Artifact version still exact
        ↓
create Revision
```

If classification or governance fails, no new Revision is created and current document state remains unchanged.

P10 does not authorize implementation of that hook in this specification turn.

## 12. Proposer declaration

The proposer must declare exactly one of the five classes.

No implicit default exists.

Missing or unknown class fails closed.

The declaration is a claim, not final authority.

The proposer may also supply structured trigger claims describing intended semantic effects.

## 13. Structured trigger vocabulary

DG-P10 freezes a minimum deterministic trigger set:

```text
SEMANTIC_RULE_CHANGE
REQUIREMENT_CHANGE
INVARIANT_CHANGE
THRESHOLD_CHANGE
PROTOCOL_CHANGE
ARCHITECTURE_CONTRACT_CHANGE
REQUIRED_BEHAVIOR_CHANGE

DOCUMENT_DECOMPOSITION_CHANGE
DOCUMENT_IDENTITY_CHANGE
RELATION_TOPOLOGY_CHANGE
DEPENDENCY_TOPOLOGY_CHANGE
AUTHORITY_OWNERSHIP_CHANGE

AUTHORITY_REPLACEMENT
```

Trigger-to-minimum-class mapping:

- first group => at least NORMATIVE;
- second group => at least STRUCTURAL;
- `AUTHORITY_REPLACEMENT` => SUPERSESSION.

An implementation may add more specific triggers only through an explicit spec amendment. It may not silently weaken these mappings.

## 14. Deterministic adjudication

For one exact subject:

```text
candidate classes =
    proposer declared class
    + minimum classes implied by structured triggers
    + QA escalation classes
    + conservative ambiguity escalation

effective_change_class = max(candidate classes)
```

No byte count, line count, token count or file size participates as a downgrade signal.

## 15. CLARIFICATION versus NORMATIVE ambiguity

If the proposer declares CLARIFICATION and semantic review cannot establish that the existing contract is unchanged:

```text
effective_change_class = NORMATIVE
```

until an authorized review resolves the ambiguity.

The burden is on the clarification claim to remain non-normative.

Absence of a detected rule change is not automatically proof of CLARIFICATION when required semantic QA did not evaluate successfully.

## 16. QA escalation

QA may escalate classification monotonically.

Examples:

- declared EDITORIAL + `CHANGE_CLASS_MISMATCH` indicating changed behavior => at least NORMATIVE;
- declared CLARIFICATION + protocol threshold change => NORMATIVE;
- declared NORMATIVE + relation-topology change => STRUCTURAL;
- any lower class + authority replacement => SUPERSESSION.

QA escalation must be attributable to immutable evidence or normalized QA output.

A tool error / NOT_EVALUATED signal cannot be interpreted as clean confirmation of the lower class.

## 17. Agent downgrade prohibition

Within one exact classification subject:

```text
agent/proposer effective class may stay same or increase
agent/proposer effective class may not decrease after escalation
```

No in-place mutation of historical classification Evidence is allowed.

## 18. Governed human review of over-escalation

The §13 prohibition is specifically against unilateral agent downgrade.

A future implementation may permit a human-authorized lower replacement adjudication only when all are true:

- exact same document/base/candidate source;
- prior classification Evidence is referenced;
- explicit downgrade reason is frozen;
- required Approval is present;
- review evidence specifically addresses the higher-class trigger;
- a new immutable classification Evidence record is created;
- prior Evidence remains historical and observable.

This is not an agent downgrade and is not an in-place rewrite.

No automatic downgrade path is authorized.

## 19. Minimum approval boundary

Current governed-document metadata does not persist a qualified document-level `change_policy`.

P10 must not fabricate policy state or claim full §14 policy enforcement.

Until a separately qualified document-level policy store exists, DG-P10 freezes a conservative core minimum:

```text
effective EDITORIAL      -> classification QA required; no P10-mandated human approval
effective CLARIFICATION  -> classification QA required; no P10-mandated human approval
effective NORMATIVE      -> human approval required before Revision commit
effective STRUCTURAL     -> human approval required before Revision commit
effective SUPERSESSION   -> human approval required before Revision commit
```

This minimum may be strengthened by later explicit policy. Missing policy metadata must never be used to relax NORMATIVE+ governance.

## 20. §14 change-policy boundary

DG-P10 does not make the following policies fully executable:

```text
MUTABLE_WITH_QA
NORMATIVE_WITH_APPROVAL
APPEND_ONLY
GENERATED_ONLY
IMMUTABLE_ARCHIVE
```

Boundary:

- P10 classifies the semantic change;
- P10 can state whether its conservative NORMATIVE+ approval minimum applies;
- P15 owns append-only and supersession execution semantics;
- P16 owns generated-document provenance/enforcement;
- lifecycle/archive mutation remains governed by the qualified lifecycle program and later explicit policy work;
- no caller-provided ungoverned `change_policy` may be trusted as authoritative merely to loosen requirements.

## 21. Persistence reuse verdict

A mutable current-state P10 table is not justified.

Classification is immutable evidence about one exact base/candidate pair.

DG-P10 therefore freezes reuse of `PRIM-EVIDENCE`.

Reserved core evidence type:

```text
document_change_classification
```

Conceptual mapping:

```text
classification_id
    = Evidence.evidence_id

Evidence.evidence_type
    = document_change_classification

Evidence.subject_refs
    = exact document ID
      + exact base Revision ID
      + exact proposed source identity

Evidence.structured_payload
    = immutable classification adjudication

Evidence.trust_class
    = AUTHORITATIVE
```

No `document_change_classifications` table is justified.

## 22. Classification Evidence payload

Minimum immutable payload:

```text
schema = DG-P10-CHANGE-CLASSIFICATION-v1
project_id
document_id
base_revision_id
expected_artifact_version
candidate_source_identity
declared_change_class
declared_triggers[]
qa_escalation_refs[]
ambiguity_status
effective_change_class
governance_rank
approval_required
classification_policy_version
adjudicated_by
adjudicated_at
supersedes_classification_evidence_ref  # optional governed human replacement only
```

The payload contains no raw document body or credentials.

## 23. Revision binding after successful classification

The conceptual `DocumentRevision.change_class` field from the foundation is not currently a database column.

DG-P10 must not add a parallel table merely to reproduce that conceptual field.

A future implementation may extend the immutable governed-document Revision payload for **new revisions only** with:

```text
governance:
  effective_change_class
  classification_evidence_ref
```

Rules:

- no database schema migration is required for this payload extension;
- historical P4 revisions are not backfilled;
- classification Evidence must bind the same exact candidate source identity stored by the new Revision;
- the new Revision must not be committed if the classification subject is stale;
- the Evidence reference makes the classification reconstructable without mutating Evidence.

The exact payload-versioning mechanism is an implementation detail, but silent semantic reinterpretation of old revisions is forbidden.

## 24. P5 finding integration

P5 already reserves `CHANGE_CLASS_MISMATCH` as a valid finding class.

DG-P10 may consume attributable QA escalation signals and may later allow P5 to record a mismatch against committed/current revisions.

P10 must not create a second finding lifecycle.

A P5 finding is not itself the canonical classification record; canonical classification remains immutable `document_change_classification` Evidence.

## 25. Authority and supersession boundary

Classification of STRUCTURAL or SUPERSESSION is descriptive/governance state only.

P10 must not:

- grant or retire P7 authority claims;
- infer authority from document class/path/title;
- create/retire P8 relations;
- change P9 bindings;
- transition lifecycle;
- mark validity;
- create impact propagation;
- archive/delete documents.

Future mutation programs consume the classification; P10 does not execute them.

## 26. No semantic oracle claim

P10 does not claim that a deterministic byte diff can prove semantic class.

The core adjudicator is deterministic over supplied governed signals and evidence.

Semantic validators/reviewers may produce escalation signals.

If required semantic evaluation is unavailable or ambiguous, the system fails conservatively rather than treating the absence of evidence as EDITORIAL/CLARIFICATION proof.

## 27. No diff-size heuristic

Forbidden logic includes:

```text
small diff => EDITORIAL
few lines => CLARIFICATION
large diff => NORMATIVE
rename only => non-structural
```

Diff size may be displayed as diagnostic metadata but must not lower governance class.

## 28. Staleness and concurrency

A classification authorizes only its exact subject.

Before revision commit, implementation must recheck:

- document ID unchanged;
- Artifact current Revision == `base_revision_id`;
- Artifact version == `expected_artifact_version`;
- exact candidate source identity matches classification Evidence;
- any required Approval binds the exact classification Evidence/payload.

Mismatch fails closed.

Classification Evidence remains historical but cannot authorize a different candidate or later base revision.

## 29. No later-wave side effects

DG-P10 classification/adjudication must not create or mutate:

- `DocumentChangeSet`;
- document relations;
- relation bindings;
- TraceLinks;
- impacts;
- validity;
- lifecycle;
- authority claims;
- source files;
- GAC state;
- Reference Acquisition state;
- G2E state.

## 30. Migration decision

Pre-implementation persistence verdict:

```text
new P10 table                         NO
schema migration                      NO
reserve core Evidence type            YES
classification Evidence               YES
new Revision payload governance refs  ALLOWED FOR NEW REVISIONS
historical backfill                   NO
P5 finding lifecycle reuse            YES
Proposal/Approval reuse               YES
DocumentChangeSet                     NO / DG-P11
```

## 31. Frozen fixture matrix

### D10-F1 — exact class vocabulary

Only EDITORIAL, CLARIFICATION, NORMATIVE, STRUCTURAL and SUPERSESSION are legal.

### D10-F2 — governance rank is deterministic

The rank is exactly EDITORIAL < CLARIFICATION < NORMATIVE < STRUCTURAL < SUPERSESSION.

### D10-F3 — no implicit declaration

Missing/unknown declared class fails closed.

### D10-F4 — editorial clean case

Declared EDITORIAL remains EDITORIAL only when no higher trigger/escalation applies and required classification QA evaluated.

### D10-F5 — clarification clean case

Declared CLARIFICATION remains CLARIFICATION only when required semantic review establishes no normative trigger.

### D10-F6 — clarification ambiguity escalates

Unresolved CLARIFICATION versus NORMATIVE ambiguity produces NORMATIVE.

### D10-F7 — normative trigger escalation

An EDITORIAL/CLARIFICATION declaration plus any normative trigger yields at least NORMATIVE.

### D10-F8 — structural trigger escalation

A lower declaration plus identity/relation/dependency/authority-ownership structural trigger yields STRUCTURAL.

### D10-F9 — supersession trigger escalation

`AUTHORITY_REPLACEMENT` yields SUPERSESSION.

### D10-F10 — diff size cannot downgrade

Byte/line/token size has no effect that lowers class.

### D10-F11 — QA escalation is monotonic

QA may raise effective class; agent/proposer cannot lower it in place.

### D10-F12 — governed human replacement only

Any lower replacement after escalation requires explicit human Approval, exact same subject and new immutable Evidence referencing prior classification.

### D10-F13 — exact base required

Classification fails if base Revision is not current or expected Artifact version is stale.

### D10-F14 — exact candidate source required

Mutable ref/path without exact immutable source identity cannot be classified as commit-authorizing Evidence.

### D10-F15 — pre-commit failure has zero revision side effect

Classification/approval failure leaves Artifact current Revision and version unchanged.

### D10-F16 — NORMATIVE+ approval minimum

NORMATIVE, STRUCTURAL and SUPERSESSION require human Approval before Revision commit under the P10 conservative core minimum.

### D10-F17 — Evidence reuse / no table

Classification persists as reserved core `document_change_classification` Evidence and no P10 table is created.

### D10-F18 — exact Revision binding

A successfully committed new Revision binds the same effective class and classification Evidence ref for the exact classified candidate without backfilling history.

### D10-F19 — no structural/supersession execution side effect

STRUCTURAL/SUPERSESSION classification does not mutate authority, relation, binding, lifecycle, impact or validity state.

### D10-F20 — no DG-P11+ side effects

P10 creates no DocumentChangeSet, multi-document aggregation, relation-aware propagation, GAC state or automatic source edit.

## 32. Pre-implementation acceptance gate

DG-P10 pre-implementation qualification may PASS only if all are true:

- exact DG-P9 final formal-close frontier is verified;
- DG-P4 exact identity dependency is verified;
- DG-P5 QA/finding dependency is verified and added to the hard-dependency set;
- DG-P7 authority dependency is verified;
- five-class vocabulary is frozen;
- deterministic governance rank is frozen;
- single-document scope is frozen;
- exact base/candidate subject identity is frozen;
- classification-before-revision-mutation invariant is frozen;
- proposer declaration is mandatory;
- structured trigger-to-minimum-class mapping is frozen;
- CLARIFICATION/NORMATIVE ambiguity resolves conservatively;
- QA escalation is monotonic;
- agent unilateral downgrade is forbidden;
- governed human replacement semantics are bounded and immutable;
- diff-size downgrade heuristics are forbidden;
- NORMATIVE+ minimum approval rule is frozen;
- §14 executable-policy overclaim is rejected;
- P10 classification persistence reuses PRIM-EVIDENCE;
- no new P10 table/migration is justified;
- revision payload binding is limited to new revisions and no historical backfill;
- P5 finding lifecycle remains canonical;
- STRUCTURAL/SUPERSESSION have zero mutation side effects;
- multi-document aggregation remains DG-P11;
- D10-F1..D10-F20 are frozen;
- implementation remains NOT_STARTED;
- DG-P11+ remain NOT_STARTED / NOT_AUTHORIZED;
- DG-W3 remains OPEN / NOT_EXECUTED;
- Finding checklist OPEN = 0.

## 33. Expected post-qualification state

If exact document QA passes:

```text
DG-P9                     = FORMALLY_CLOSED
DG-P10 authorization      = PREIMPLEMENTATION_ONLY
DG-P10 specification      = FROZEN
DG-P10 dependency qualify = PASS
DG-P10 document QA        = PASS
DG-P10 implementation     = NOT_STARTED
DG-P10 overall            = NOT_YET_PASS
DG-P11+                   = NOT_STARTED / NOT_AUTHORIZED
DG-W3                     = OPEN / NOT_EXECUTED
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```

A separate explicit bounded implementation authorization is required before core Evidence registration, classifier/adjudicator runtime, DocumentFacade pre-commit integration, tests or workflow are created.
