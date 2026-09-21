# G2E Core Semantics

**Status:** normative for G2E v0.x specifications.

This document defines shared semantics that component PRDs MUST use. A component PRD may specialize these rules only when it explicitly identifies the specialization and does not weaken a MUST in this document.

## 1. Canonical identity

Every authoritative G2E object MUST contain:

- `schema_version`;
- stable logical ID;
- revision ID where the object is revisable;
- canonical content hash;
- creation/derivation provenance.

Canonical hash profile for v0.x:

1. UTF-8 JSON;
2. Unicode strings normalized to NFC before serialization;
3. object keys sorted lexicographically by Unicode code point;
4. arrays preserve declared semantic order;
5. no insignificant whitespace;
6. no NaN/Infinity;
7. normative non-integer numeric thresholds use decimal strings, not binary floating-point;
8. timestamps use RFC3339 UTC with `Z`;
9. SHA-256 over the canonical bytes.

Unknown schema **major** versions fail closed. Compatible minor-version handling must be declared by the consumer.

Runtime/provider IDs are mappings to a G2E object, not replacements for its canonical G2E ID/hash.

## 2. State namespaces

State namespaces MUST NOT be conflated.

### 2.1 GoalContract lifecycle

`DRAFT | REVIEWED | FROZEN | SUPERSEDED`

### 2.2 Goal verdict

`IN_PROGRESS | ACHIEVED | FALSIFIED | UNRESOLVED | STOPPED`

`INVALID` is not a Goal verdict. Invalid technical attempts do not by themselves invalidate or falsify the user's goal.

### 2.3 Claim lifecycle

`DRAFT | BLOCKED | READY | ACTIVE | CLOSED | SUPERSEDED`

### 2.4 Claim resolution

`UNKNOWN | PASS | FAIL | UNRESOLVED`

Claim lifecycle and resolution are orthogonal.

### 2.5 ProofObligation lifecycle

`DRAFT | REVIEWED | FROZEN | AUTHORIZED | ACTIVE | CLOSED | SUPERSEDED`

### 2.6 ExecutionAttempt state

`CREATED | PREFLIGHT | LOCKED | RUNNING | COMPLETED | EXECUTOR_FAILED | CANCELLED | TIMED_OUT | PREEMPTED`

These are executor states only.

### 2.7 Adjudication verdict

`PASS | FAIL | INVALID | UNRESOLVED`

- PASS: valid admitted evidence satisfies the frozen proof rule.
- FAIL: valid admitted evidence substantively violates a required proof rule.
- INVALID: the attempt cannot answer the proof because execution/protocol/evidence validity failed.
- UNRESOLVED: the attempt is valid but the frozen decision rule cannot decide PASS or FAIL.

## 3. ProofObligation and ExecutionAttempt identity

A `ProofObligation` freezes semantic proof identity: proposition, population/fixture, controls, metrics, thresholds, baselines, resource policy, evidence requirements, and adjudication rules.

An `ExecutionAttempt` is one execution of one frozen ProofObligation. Every attempt has a unique `attempt_id`.

Adjudication is one-shot **per attempt**.

### 3.1 Closure rules

- Attempt PASS: close the ProofObligation PASS; no further equivalent attempt is admissible.
- Attempt FAIL: close the ProofObligation FAIL; no further equivalent attempt is admissible.
- Attempt UNRESOLVED: close the ProofObligation UNRESOLVED. Additional evidence requires a new ProofObligation unless the original frozen proof explicitly defined a bounded multi-part collection.
- Attempt INVALID: does not resolve the target claim and does not automatically close the ProofObligation. A replacement attempt is allowed only when the frozen retry policy permits it and semantic proof identity is unchanged.
- Retry budget exhausted with no valid substantive adjudication: close the ProofObligation UNRESOLVED and retain all INVALID attempt history.

A materially changed threshold, seed/cohort, baseline, target, intervention, evidence rule, artifact, resource equivalence rule, or claim proposition is never an infrastructure retry.

## 4. Claim resolution policy

Every claim that can become terminal MUST freeze a `ClaimResolutionPolicy`.

G2E v0.x supports:

### ALL_REQUIRED

- PASS when every required ProofObligation is PASS.
- FAIL when any required ProofObligation is FAIL and no frozen alternate path can satisfy the claim.
- UNRESOLVED when no required proof FAILs but at least one required proof closes UNRESOLVED or cannot be validly completed.

### ANY_SUFFICIENT

The finite set of sufficient alternative ProofObligations must be frozen before protected outcome exposure.

- PASS when any listed sufficient proof is PASS.
- FAIL only when every frozen alternative is FAIL.
- UNRESOLVED when none PASS and at least one is UNRESOLVED/not validly completed.

Evidence or proof not named by the frozen resolution policy cannot silently become sufficient after outcomes are known.

Conflicting evidence remains in the Evidence Graph; it is resolved only through the frozen policy or a new claim/proof lineage.

## 5. Goal requirements and closure

A FROZEN `GoalContract` contains stable `goal_requirement_id` records describing desired outcomes and falsification-relevant constraints **without referring to Claim IDs that do not exist yet**.

When the Claim Graph is REVIEWED, G2E creates a `GoalClosureContract` bound to:

- exact GoalContract revision/hash;
- exact ClaimGraph revision/hash;
- requirement→claim mappings;
- a `success_expression`;
- a `falsification_expression`;
- terminal-claim set;
- authorized stop policy.

The GoalClosureContract freezes together with `CLAIM_GRAPH_FROZEN`.

Expressions are finite trees using:

- `CLAIM(claim_id, expected_resolution)`;
- `ALL([...])`;
- `ANY([...])`.

Hard-claim dependency graphs are DAGs in v0.x. `NOT` and cyclic/fixed-point semantics are deferred.

Goal evaluation:

- ACHIEVED when `success_expression` evaluates true.
- FALSIFIED when `falsification_expression` evaluates true and success is not true.
- UNRESOLVED when the goal cannot reach ACHIEVED/FALSIFIED under remaining admissible proofs/resources and no authorized STOP was chosen.
- STOPPED only by authorized governance action with reason.
- otherwise IN_PROGRESS.

A single Claim FAIL does not automatically falsify a goal when a frozen alternate path exists.

## 6. Dependency classes

G2E documents/plans use these dependency classes:

- **HARD** — must be satisfied before the dependent component/work may start.
- **CONDITIONAL** — required only when the named capability/path is used.
- **CROSS_CUTTING** — normative policy applies across components but does not impose implementation ordering by itself.
- **INTEGRATION** — needed to connect two already valid components; not a prerequisite for either component's independent core semantics.
- **ORDERING** — roadmap scheduling choice, not an architectural prerequisite.

A dependency must not be described as HARD in one document and optional/integration in another.

## 7. Temporal and freeze events

Normative event order:

```text
GOAL_FROZEN
  ↓
CLAIM_GRAPH_FROZEN + GOAL_CLOSURE_FROZEN
  ↓
PROOF_FROZEN
  ↓
PROOF_AUTHORIZED
  ↓
ATTEMPT_LOCKED
  ↓
(optional) PROTECTED_RESOURCE_RESERVED
  ↓
ATTEMPT_RUNNING
  ↓
OUTCOME_EXPOSED
  ↓
ATTEMPT_ADJUDICATED
  ↓
PROOF_CLOSED
  ↓
CLAIM_RESOLVED
  ↓
GOAL_CLOSED
```

`OUTCOME_EXPOSED` is the first point at which protected/target outcome content becomes available to a human, agent, planner, or downstream decision process. Persistence alone is not sufficient if an actor already observed it.

Reference-acquisition mode `PRE_LOCK` means before `PROOF_FROZEN`; `LOCKED_PRE_OUTCOME` means from `PROOF_FROZEN` through immediately before `OUTCOME_EXPOSED`; `POST_OUTCOME` begins at `OUTCOME_EXPOSED`.

## 8. Protected resources and freshness

Every protected resource has an immutable resource identity and orthogonal policy metadata.

Freshness states:

`FRESH | RESERVED | EXPOSED`

Rules:

1. reservation is durably recorded before protected access begins;
2. if access may have begun but recovery cannot prove non-exposure, recovery fails closed to EXPOSED;
3. exposure is recorded before or atomically with making outcome content available outside the access boundary;
4. EXPOSED never transitions back to FRESH;
5. reuse requires an explicit frozen reuse policy;
6. a resource may be protected without being one-shot; protection and freshness are distinct fields.

## 9. Amendments and lineage

Amendments are:

- **EDITORIAL** — wording/formatting that cannot change machine semantics, authority, interpretation, admissibility, or verdict.
- **NORMATIVE** — any change that can alter goal/claim/proof meaning, dependency, baseline, threshold, cohort, protected resource, evidence sufficiency, authority, retry, or final verdict.

Rules:

- Editorial changes create a new document/object revision but may retain lineage when canonical machine semantics are unchanged and verified.
- Normative change before outcome exposure creates a new affected object revision and re-freezes downstream dependencies.
- Normative change after OUTCOME_EXPOSED creates a new proof/study lineage for affected semantics. It never retroactively changes the old adjudication.
- Adding a newly discovered prerequisite after exposure creates a new ClaimGraph revision; prior evidence remains historical, and affected downstream claims return to BLOCKED/UNKNOWN in the new revision rather than rewriting old results.

## 10. Evidence admission and relations

Evidence lifecycle:

`CANDIDATE | ADMITTED | REJECTED | INVALIDATED`

Only ADMITTED evidence may be consumed by adjudication.

Every `EvidenceAdmissionPolicy` specifies:

- accepted evidence/source classes;
- identity/integrity requirements;
- required producer/attempt linkage;
- freshness/protection constraints;
- independence constraints when required;
- redaction/security rules;
- allowed derivation depth;
- missing-data handling.

Reference/context material does not become empirical proof solely because it exists in the Evidence Graph.

Relation direction is subject → object:

- `PRODUCED_BY`: evidence → ExecutionAttempt
- `SUPPORTS`: evidence → Claim/ProofObligation
- `FALSIFIES`: evidence → Claim/ProofObligation
- `VALIDATES`: evidence → exact artifact/contract revision
- `DERIVED_FROM`: derived evidence → source evidence
- `REPRODUCES`: new evidence → prior evidence
- `CONFLICTS_WITH`: evidence → evidence
- `SUPERSEDES`: newer evidence → older evidence

Authoritative evidentiary relations bind immutable IDs/hashes; floating “current” targets are not valid evidentiary bindings.

## 11. Selection policy

Next-Step selection is two-stage.

### Stage A — deterministic admissibility

A candidate is admissible only if all HARD dependencies, authority, freshness, retry, and lineage rules are satisfied.

### Stage B — governed ranking

A frozen `SelectionPolicy` defines an ordered tuple of normalized fields. Default v0.x fields are:

1. `hard_dependencies_unblocked` — descending integer;
2. `protected_resource_cost` — ascending integer (`0=none, 1=reuse-allowed, 2=fresh/protected`);
3. `resource_cost_class` — ascending configured integer;
4. `implementation_complexity` — ascending configured integer;
5. `proof_id` — ascending lexical deterministic tie-break.

“Information gain” or other heuristic agent judgments may be advisory metadata but are not default deterministic ranking fields.

An authorized user may choose another member of the admissible set, but the `SelectionDecision` must record the override/rationale. No authority may select an inadmissible candidate without first making a governed normative amendment.

Minimality is therefore a ranking property, not a validity claim.

## 12. Authority, independence, and disposition

Core authority actions:

- freeze GoalContract;
- freeze ClaimGraph/GoalClosureContract;
- freeze/authorize ProofObligation;
- reserve/expose protected resource;
- execute attempt;
- admit/reject evidence;
- adjudicate;
- approve governance disposition;
- stop goal.

A ProofObligation may declare an `IndependencePolicy` over dimensions such as:

- implementation author vs reviewer;
- planner vs adjudicator;
- agent/provider identity;
- data/outcome exposure;
- execution environment.

Using a different provider alone never proves independence.

The deterministic/machine Adjudication verdict is immutable. Human governance may attach a `GovernanceDisposition` such as `ACCEPT_FOR_USE | REJECT_FOR_USE | REQUEST_NEW_PROOF | STOP`, but the disposition never rewrites PASS/FAIL/INVALID/UNRESOLVED.

Delegated authority cannot exceed parent authority.

## 13. Semantic authority and system of record

G2E core owns **semantic definitions** of Goal/Claim/Proof/Evidence/Adjudication.

The selected runtime owns durable **system-of-record persistence**:

- with GWF: GWF is the default persistence/authority runtime for canonical G2E records;
- standalone: the standalone runtime persists the same canonical G2E records.

A runtime adapter may add runtime IDs/state but MUST NOT reinterpret canonical G2E content or verdict semantics.

Migration standalone ↔ GWF preserves G2E IDs/hashes. Runtime-specific IDs are separate mappings.

## 14. Result-package integrity

A Goal Result Package uses:

- `PACKAGE_MANIFEST.json`: sorted path → SHA-256/size entries for authoritative package content, excluding the manifest and seal themselves;
- `PACKAGE_SEAL.json`: hashes the exact canonical `PACKAGE_MANIFEST.json`, identifies framework/runtime versions and signing/attestation identity when available.

Verification fails if:

- a listed file is missing;
- hash/size differs;
- an authoritative file exists outside the manifest without an explicit non-authoritative classification;
- an immutable external reference cannot be resolved when the verification policy requires online resolution.

This avoids self-referential hashing.

## 15. Reference baseline

The exact specification/evidence baselines used to derive these semantics are recorded in [REFERENCE_BASELINE.md](REFERENCE_BASELINE.md).


## 15. Prior governed evidence and EvidenceCapsules

A prior governed result intended for reuse/library publication is represented by an immutable `EvidenceCapsule` generated after sealing an exact source package such as a terminal ClaimResultPackage, Goal Result Package, or sealed synthesis source package.

All prior/library evidence is already `EXPOSED`. Import, publication, migration or reuse MUST NOT transition it to `FRESH`.

A capsule MAY represent PASS, FAIL or UNRESOLVED source results. Favorable-result-only publication is not a valid default library policy.

A capsule binds exact source package seal/hash, source Claim/Proof/evidence identities, ClaimSignature, limitations, regime and provenance ancestry.

The capsule is a post-seal sibling derivative and MUST NOT be included as authoritative content in the source package whose seal it references.

Library retrieval creates candidate prior evidence only; it does not admit evidence or resolve a Claim.

## 16. Applicability and qualified reuse

Prior evidence reuse is prospective and policy-driven.

`ReuseDisposition` v0.x:

- `QUALIFIED_REUSE`;
- `REPLICATION_REQUIRED`;
- `SYNTHESIS_INPUT`;
- `METHOD_REFERENCE`;
- `CONTEXT_ONLY`;
- `INCOMPATIBLE`.

An `ApplicabilityAssessment` binds exact source capsule, exact target Goal/Claim/Proof revision and exact ApplicabilityPolicy.

`QUALIFIED_REUSE` never directly sets Claim resolution. It authorizes a Reuse ProofObligation whose frozen evidence/admission/applicability criteria are adjudicated through the normal G2E proof path.

Reuse evidence still passes EvidenceAdmissionPolicy. Shared ancestry MUST be represented so dependent capsules cannot be counted as independent confirmations merely because they have different capsule IDs.

## 17. Synthesis and convergence

Cross-study synthesis is a normal G2E Goal/proof specialization, not an alternate verdict engine.

A formal synthesis MUST freeze a `SynthesisContract` before formal inclusion/outcome selection. It binds question, evidence universe/library snapshot or retrieval sessions, inclusion/exclusion, outcome-blind quality/integrity rules, applicability, independence/provenance clustering, compatibility/regime grouping, aggregation, conflict/boundary policy, conclusion semantics and no-rescue rules.

The frozen universe also records a CoverageStatement describing searched scopes/sources, known missing/inaccessible channels and publication/selection-bias limitations. Reproducibility of a snapshot does not prove completeness of the evidence universe.

A descriptive `ConvergenceClassification` such as `CORROBORATED | CONTRADICTED | BOUNDARY_IDENTIFIED | HETEROGENEOUS | INSUFFICIENT_EVIDENCE | UNRESOLVED` is an output artifact only. It does NOT replace Adjudication verdict, Claim resolution or Goal verdict.

A SynthesisResult retains transitive ancestry to all included source capsules. Future independence analysis MUST inspect that ancestry to prevent double counting.

A changing search rank/index cannot silently redefine a frozen synthesis universe.
