# G2E P0.3 — GWF Shared Library Reconciliation Findings

## Status

**FINDINGS OPEN — remediation required before current G2E↔GWF Library handoff can be considered aligned.**

## Audit identities

G2E branch audited:

- branch: `feature/g2e-framework`
- pre-audit head: `d6b798f489a396ea13e48b5c7e31027b320fc09b`

GWF reconciliation audited:

- branch: `docs/governed-artifact-catalog-pack`
- final reconciliation commit: `be7d606c64a97d9525d1f72d744fe5b7a336ff0c`
- findings: `FD-01..FD-15 = RESOLVED`
- reconciliation QA: `PASS / OPEN=0`

This audit is documentation-only. No G2E/GWF/GAC/Reference Acquisition runtime implementation is authorized.

## Findings

### P03-F01 — HIGH — OPEN — G2E pins the pre-reconciliation GAC baseline

`REFERENCE_BASELINE.md` still treats `194c66c...` as the GAC QA closure and links floating branch documents. GWF has since reconciled ownership, Reference Acquisition, readiness gates and the 7-wave plan at `be7d606c...`.

**Required:** append the exact reconciled commit/blob identities and mark the original pack as historical design lineage rather than the current integration authority.

- [ ] RESOLVED

### P03-F02 — HIGH — OPEN — Shared Library terminology is not mirrored in G2E

GWF now defines **Shared Library** as consumer-facing capability built on GAC; G2E Evidence Library is a semantic consumer/view, not a second physical store.

G2E still uses “Evidence Library” in places without explicitly mapping it to this Shared Library boundary.

**Required:** freeze the same terminology in G2E README/PRD-17/integration mapping.

- [ ] RESOLVED

### P03-F03 — HIGH — OPEN — PRD-13 omits the new internal `GWF_CATALOG` Reference Acquisition channel

GWF Reference Acquisition now supports an internal governed Library/GAC channel with `CatalogQueryExecution`, catalog snapshot and exact CatalogEntry provenance.

G2E PRD-13 currently describes Reference Acquisition primarily as external/current prior-art discovery and PRD-17 as governed-result retrieval.

**Required:** add the internal GAC research channel and its required provenance without conflating it with direct G2E reuse.

- [ ] RESOLVED

### P03-F04 — HIGH — OPEN — Direct G2E Library query vs RA-curated GAC query lacks a routing rule

Both PRD-17 and GWF Reference Acquisition may query the same GAC substrate for different purposes. Without an explicit route, implementations could duplicate discovery logic or force every G2E reuse query through research prior-art curation.

**Required:** define:
- direct PRD-17 route for G2E EvidenceCapsule reuse/synthesis;
- PRD-13/RA route for research prior-art/novelty curation;
- same GAC subject observed via both routes remains one subject identity with multiple observation/provenance records.

- [ ] RESOLVED

### P03-F05 — HIGH — OPEN — `LibraryCapabilityManifest` readiness is too vague for reconciled GWF gates

PRD-17 says GWF GAC must be “implemented and qualified”, but GWF now exposes exact staged gates:
- `DG-W4` before GAC;
- `GAC-P0/P1/P2A/P4A` / `DG-GAC-W5` for minimum Shared Library;
- `GAC-P4B` for G2E consumer qualification;
- `RA-P1C` / `RA-GAC-W6` for the research-curated channel.

**Required:** map capability levels/gates into `LibraryCapabilityManifest` and fail closed by requested operation.

- [ ] RESOLVED

### P03-F06 — HIGH — OPEN — G2E phase plan has no explicit conditional GWF Shared Library integration gate

P1/P2 core semantics can proceed independently, but the plan does not clearly separate:
- G2E schema/engine implementation;
- standalone Library qualification;
- actual GWF GAC consumer integration.

This can be misread as P1 authorization implying GWF Library readiness.

**Required:** add an explicit conditional GWF Library integration phase/subgate that depends on qualified GWF GAC capabilities while leaving G2E P1/P2 unblocked.

- [ ] RESOLVED

### P03-F07 — MEDIUM — OPEN — PRD-17 publication eligibility omitted `ClaimResultPackage`

P0.2 added ClaimResultPackage specifically so terminal Claims can be reused before whole-Goal closure, but PRD-17 still says default publication requires a Goal Result Package or SynthesisResult.

**Required:** include sealed ClaimResultPackage in publication eligibility and preserve package-type identity.

- [ ] RESOLVED

### P03-F08 — HIGH — OPEN — Synthesis can double-observe the same GAC subject through two discovery channels

PRD-16 accepts both GWF catalog query IDs and Reference Acquisition retrieval sessions, but does not explicitly normalize the same exact capsule/subject observed through both into one synthesis candidate identity.

**Required:** separate candidate subject identity from observation/retrieval identity; duplicate observations improve provenance/coverage but never count as multiple studies/results.

- [ ] RESOLVED

### P03-F09 — MEDIUM — OPEN — Core Semantics section numbering is ambiguous

`CORE_SEMANTICS.md` contains both `## 15. Reference baseline` and `## 15. Prior governed evidence...`. Cross-document citations to §15/§16/§17 are therefore ambiguous.

**Required:** renumber the extension sections and update affected references.

- [ ] RESOLVED

### P03-F10 — MEDIUM — OPEN — Cross-system shorthand conflicts with G2E canonical type names

GWF reconciliation prose refers to G2E-owned concepts as `ReuseDecision` and `SynthesisVerdict`. G2E normative schemas use `ReuseDisposition` and `ConvergenceClassification`; G2E deliberately does not create a separate synthesis verdict namespace.

**Required:** publish an explicit terminology mapping:
- GWF prose `ReuseDecision` → G2E canonical `ReuseDisposition`;
- GWF prose `SynthesisVerdict` → non-normative shorthand only; canonical G2E object is `ConvergenceClassification`, while formal conclusions still use Adjudication/Claim/Goal verdicts.

- [ ] RESOLVED

## Pre-remediation verdict

`OPEN = 10`

**FAIL — G2E P0.2 remains historically valid for its audited GWF pack, but current G2E↔GWF Shared Library integration is not yet reconciled to GWF commit `be7d606c...`.**
