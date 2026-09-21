# G2E P0.2 — Evidence Reuse & Convergence Documentation QA

## Status

**SEMANTIC QA: FAIL / remediation required.**

Candidate commit:

`ca001f806f9306bbd1ba6a57185879b3ec3ee71a`

P1 Core Schemas remains blocked.

## Findings

### P02-F01 — HIGH — OPEN — EvidenceCapsule creates a circular package seal dependency

PRD-12 places `EVIDENCE_CAPSULE.json` inside the Goal Result Package while PRD-15 requires the capsule to bind the source package seal. If the package manifest hashes the capsule, the dependency becomes:

`PACKAGE_SEAL → PACKAGE_MANIFEST → EVIDENCE_CAPSULE → PACKAGE_SEAL`.

**Required:** EvidenceCapsule must be generated as an external/post-seal derivative (or explicitly non-authoritative excluded content). Prefer a sibling derivative outside the sealed source package.

- [ ] RESOLVED

### P02-F02 — HIGH — OPEN — Reuse is unnecessarily blocked until whole Goal closure

PRD-15 requires a sealed Goal Result Package. A long-running Goal may contain a terminal, reusable Claim months before the whole Goal closes.

**Required:** define a sealed `ClaimResultPackage` (or equivalent exact claim-level source package) so terminal Claim results can be published without pretending the entire Goal is terminal.

- [ ] RESOLVED

### P02-F03 — HIGH — OPEN — Synthesis inclusion/quality rules are not explicitly outcome-blind

The SynthesisContract freezes inclusion/exclusion and quality gates but does not forbid criteria based on favorable/unfavorable result direction.

**Risk:** prospective-looking rules could still encode result-direction cherry-picking.

**Required:** inclusion/quality criteria must not depend on result direction/verdict except when the synthesis question explicitly requires a prospectively declared outcome stratum.

- [ ] RESOLVED

### P02-F04 — MEDIUM — OPEN — Library universe completeness/publication bias is not represented

A frozen catalog snapshot can be reproducible while still missing unpublished/failed/unindexed studies.

**Required:** SynthesisUniverse must record coverage scope, known missing sources and publication/selection-bias limitations; inability to justify coverage constrains conclusion strength and may force INSUFFICIENT_EVIDENCE/UNRESOLVED.

- [ ] RESOLVED

### P02-F05 — MEDIUM — OPEN — GWF GAC default backend is documentation-only but runtime capability gating is underspecified

PRD-17 identifies GWF GAC as default backend although GAC has only a packing spec and no implementation.

**Required:** runtime must resolve a LibraryCapabilityManifest. If GAC is unavailable/unqualified, it must fail closed or explicitly select qualified standalone backend; it must never pretend the default backend exists.

- [ ] RESOLVED

## Existing checks

- [x] Prior result cannot directly set current Claim PASS.
- [x] QUALIFIED_REUSE flows through Reuse ProofObligation + EvidenceAdmission.
- [x] FAIL/UNRESOLVED results are eligible; no PASS-only library policy.
- [x] Library evidence remains EXPOSED.
- [x] Applicability binds exact source/target/policy.
- [x] Shared provenance is modeled for anti-double-counting.
- [x] Synthesis universe/inclusion rules freeze prospectively.
- [x] ConvergenceClassification is separate from core verdict namespaces.
- [x] GWF owns catalog infrastructure; G2E owns reuse/synthesis meaning.
- [x] Query failure cannot masquerade as zero results.
- [x] P1 has been re-blocked by README/QA/Phase Plan.

## Verdict

`OPEN = 5`

**FAIL until all findings are resolved.**
