# G2E Architecture Decisions

## ADR-001 — G2E core is independent; GWF is the default runtime

**Decision:** G2E owns goal→claim→proof→evidence→adjudication→resolution→next-step semantics. GWF is the default execution/governance/persistence backend through an adapter.

**Reason:** GWF already solves authority, persistent governed state, recovery, GitHub safety, agent protocol and handoff. Putting the G2E proof-reasoning engine directly in GWF core would conflate workflow runtime with proof planning.

## ADR-002 — Do not hard-code MindForge phases

**Decision:** M0–M4 are empirical reference evidence, not canonical G2E phases.

## ADR-003 — State namespaces are separate

**Decision:** executor state, Adjudication verdict, Claim lifecycle/resolution, Proof lifecycle, and Goal verdict use separate enums defined in Core Semantics.

**Reason:** a completed executor can yield a substantive FAIL; an INVALID attempt does not invalidate a Claim or Goal.

## ADR-004 — Dynamic proof generation, static governance

**Decision:** ProofObligations may be proposed dynamically from current state, but must be reviewed/frozen/authorized before execution. Outcome-dependent semantic mutation creates new governed lineage.

## ADR-005 — GWF execution success is not G2E PASS

**Decision:** backend completion is execution evidence only. Adjudication and Claim resolution remain separate.

## ADR-006 — Agent apps are adapters, never source of truth

**Decision:** Codex and ChatGPT are separate first-priority app profiles; Claude/Gemini follow; ARC is transport, not provider/model/resource identity.

## ADR-007 — Standalone mode is mandatory

**Decision:** G2E can run without GWF using a minimal durable runtime. Standalone may expose fewer capabilities but may not weaken core proof invariants.

## ADR-008 — Semantic authority and persistence authority are separate

**Decision:** G2E defines canonical semantics; the active runtime is the durable system of record. GWF is default. Runtime-specific IDs never replace G2E IDs/hashes.

## ADR-009 — Claim and Goal closure are policy-driven

**Decision:** claims resolve only through frozen ClaimResolutionPolicy; goals close only through GoalClosureContract. Last-write-wins evidence and narrative closure are forbidden.

## ADR-010 — Integrate + qualify before rebuild

**Decision:** mature trainers, evaluators, SCMs, runtimes and agent harnesses should be integrated behind adapters and qualified.

## References

- [G2E README](../README.md)
- [Core Semantics](CORE_SEMANTICS.md)
- [PRD Index](PRD_INDEX.md)
- [Reference Baseline](REFERENCE_BASELINE.md)


## ADR-011 — Library storage is runtime infrastructure; evidence meaning remains G2E

**Decision:** G2E owns EvidenceCapsule, applicability, reuse and synthesis semantics. GWF Governed Artifact Catalog is the default publication/discovery backend through PRD-17.

**Reason:** keeps GWF generic and prevents G2E from building a parallel storage/catalog platform.

## ADR-012 — Prior results never bypass proof semantics

**Decision:** QUALIFIED_REUSE creates/feeds a governed Reuse ProofObligation; prior PASS never directly sets a new Claim PASS.

**Reason:** preserves EvidenceAdmission, Adjudication, ClaimResolution and no-rescue invariants.

## ADR-013 — Synthesis is a governed proof program, not narrative aggregation

**Decision:** cross-study synthesis freezes its evidence universe, inclusion/exclusion, applicability, independence, aggregation and conflict policies before formal selection. ConvergenceClassification is descriptive and separate from core verdict namespaces.

**Reason:** prevents cherry-picking, vote-counting and post-hoc convergence stories.


## ADR-014 — Shared Library is GAC infrastructure plus consumer semantics

**Decision:** “Shared Library” is the consumer-facing GWF capability built on GAC. G2E Evidence Library is the G2E semantic view over that substrate and is not a second canonical store.

## ADR-015 — Direct reuse and research curation are separate GAC consumers

**Decision:** PRD-17 queries GAC directly for G2E EvidenceCapsule reuse/synthesis. PRD-13 uses Reference Acquisition for prior-art/novelty curation, including its GWF_CATALOG channel. One exact subject may have multiple observation records but one canonical subject identity.

## ADR-016 — GWF Library integration is capability-gated, not phase-assumed

**Decision:** G2E core schemas/engines and standalone Library may progress independently. Actual GWF-backed Library integration opens only when the exact requested GAC/Reference Acquisition capability gates are qualified and recorded in LibraryCapabilityManifest.
