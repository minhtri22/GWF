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
