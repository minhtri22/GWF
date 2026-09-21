# PRD-16 — Synthesis & Convergence

## Purpose

Create new governed conclusions from multiple prior studies/results without vote-counting, cherry-picking, hidden inclusion changes, or double-counting shared evidence ancestry.

Synthesis is a G2E proof specialization, not a separate workflow authority.

## 1. Synthesis as a Goal

A synthesis/convergence program is represented as a normal G2E Goal with Claims, ProofObligations, Evidence, Adjudications and GoalClosureContract.

Example:

```text
Goal:
determine whether mechanism X is supported
and under what boundary conditions
        ↓
Claims:
comparability
independence
effect/regime
boundary
alternative explanation
        ↓
Proofs:
library-universe construction
compatibility
provenance clustering
cross-study analysis
conflict decomposition
```

## 2. Discovery versus locked synthesis

Exploratory library/reference search may occur before synthesis lock, but its results are CONTEXT_ONLY for the final synthesis unless subsequently included under the frozen SynthesisContract.

Before formal inclusion/adjudication, freeze:

- synthesis question;
- search universe/library snapshot or cutoff;
- inclusion/exclusion criteria;
- eligible ClaimSignature dimensions;
- quality/integrity gate;
- ApplicabilityPolicy;
- independence/overlap policy;
- aggregation method;
- conflict policy;
- boundary-analysis policy;
- missing-data policy;
- stopping rule;
- expected conclusion classes.

After lock, outcome-dependent changes require a new synthesis revision/lineage.

## 3. SynthesisContract

Required fields:

- `synthesis_id`, revision/hash;
- source Goal/Claim identity;
- question/proposition;
- `SynthesisUniverse`;
- deterministic inclusion/exclusion criteria;
- exact library/catalog snapshot/query definitions;
- temporal cutoff;
- ApplicabilityPolicy;
- required ReuseDisposition (normally SYNTHESIS_INPUT);
- study/capsule quality gate;
- IndependencePolicy;
- provenance clustering rules;
- compatibility grouping rules;
- aggregation method;
- conflict handling;
- boundary detection;
- conclusion-class semantics;
- amendment/no-rescue policy.

## 4. SynthesisUniverse

Universe must be reproducible.

It binds one or more:

- exact GWF catalog snapshot/query execution IDs;
- exact standalone library manifest/hash;
- exact external Reference Acquisition retrieval sessions;
- explicit manual capsule list with authority/provenance.

All candidates and exclusion reasons are retained.

A search backend's changing ranking cannot redefine the frozen universe after lock.

## 5. Inclusion

A capsule enters synthesis only when:

1. exact capsule identity/integrity verified;
2. library/reference source is inside frozen universe;
3. inclusion/exclusion rule passes;
4. ApplicabilityAssessment yields required disposition;
5. source provenance is sufficient;
6. required quality/integrity conditions pass.

Excluded capsules remain in the audit trail with reason codes.

## 6. Independence clustering / double counting

Before aggregation, included capsules are assigned to provenance/independence clusters under the frozen policy.

Shared data, implementation lineage, synthetic cohort, base artifact, prior synthesis ancestry or direct derivation may make results dependent.

A SynthesisResult derived from capsules A/B/C remains transitively dependent on A/B/C. Future synthesis MUST inspect provenance closure so SynthesisResult + A are not counted as independent evidence.

## 7. Compatibility and regimes

Compatibility is dimension-specific.

Synthesis MUST distinguish:

- directly commensurate evidence;
- compatible but stratified evidence;
- incompatible metrics/populations/regimes;
- boundary-relevant differences.

When evidence differs by environment/regime, G2E should prefer explicit stratification/boundary analysis over forcing a single pooled conclusion.

## 8. Aggregation

Allowed aggregation is declared prospectively.

Examples:

- qualitative structured synthesis;
- exact replication consistency;
- stratified effect comparison;
- meta-analysis only when statistical assumptions/metric compatibility are explicitly satisfied;
- boundary/regime decomposition.

Simple PASS-count majority voting is not a valid default aggregation method.

## 9. Conflict handling

Conflicting results do not automatically cancel each other.

The frozen conflict policy may classify whether the conflict indicates:

- method/provenance issue;
- incompatible scope;
- environmental/regime boundary;
- genuine contradiction;
- insufficient evidence.

New post-hoc exclusion of an inconvenient result is prohibited.

## 10. ConvergenceClassification

Synthesis may produce a descriptive `ConvergenceClassification`:

- `CORROBORATED`;
- `CONTRADICTED`;
- `BOUNDARY_IDENTIFIED`;
- `HETEROGENEOUS`;
- `INSUFFICIENT_EVIDENCE`;
- `UNRESOLVED`.

This classification is NOT an Adjudication verdict and NOT a GoalVerdict. It is an output artifact derived under SynthesisContract; normal G2E Claims/GoalClosure still determine PASS/FAIL/ACHIEVED/FALSIFIED.

## 11. SynthesisResult

Must bind:

- SynthesisContract hash;
- exact universe;
- candidates;
- included/excluded capsules + reasons;
- ApplicabilityAssessments;
- independence clusters;
- compatibility/regime groups;
- aggregation outputs;
- conflicts;
- boundaries;
- ConvergenceClassification;
- limitations;
- source capsule/provenance closure;
- implementation/version identity.

A sealed SynthesisResult may generate a new EvidenceCapsule with DERIVED_FROM ancestry to all source capsules.

## 12. No-rescue rules

After synthesis lock and outcome exposure, do not silently change:

- search cutoff/universe;
- inclusion/exclusion;
- quality gate;
- applicability threshold;
- independence clustering rule;
- aggregation method;
- conflict policy;
- conclusion semantics.

A normative change creates a new synthesis lineage.

## Acceptance criteria

1. Synthesis is represented by standard G2E Goal/Claim/Proof semantics.
2. Universe/inclusion rules freeze before formal result selection.
3. Every excluded candidate has a reason.
4. Provenance-dependent studies are not counted as independent by default.
5. SynthesisResult ancestry is transitive.
6. PASS-count voting is not the default.
7. Boundary/regime differences may yield BOUNDARY_IDENTIFIED instead of forced contradiction.
8. ConvergenceClassification never replaces Adjudication/Goal verdict namespaces.
9. Synthesis output can be packaged/published without rewriting source results.

## Dependencies

- **HARD:** [PRD-02 Claim Graph](PRD_02_CLAIM_GRAPH.md), [PRD-03 Proof Planner](PRD_03_PROOF_PLANNER.md), [PRD-04 Evidence Graph](PRD_04_EVIDENCE_GRAPH.md), [PRD-05 Adjudicator](PRD_05_ADJUDICATOR.md), [PRD-06 Next-Step Selector](PRD_06_NEXT_STEP_SELECTOR.md), [PRD-15 Evidence Reuse & Applicability](PRD_15_EVIDENCE_REUSE_APPLICABILITY.md)
- **CONDITIONAL:** [PRD-17 Evidence Library Adapter](PRD_17_EVIDENCE_LIBRARY_ADAPTER.md)
- **CROSS_CUTTING:** [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)
- **NORMATIVE:** [Core Semantics](CORE_SEMANTICS.md)

## References

- [PRD-12 Goal Result Package](PRD_12_RESULT_PACKAGE.md)
- [PRD-13 Reference Acquisition](PRD_13_REFERENCE_ACQUISITION.md)
- [GWF Governed Artifact Catalog pack](https://github.com/minhtri22/GWF/tree/docs/governed-artifact-catalog-pack/docs)
