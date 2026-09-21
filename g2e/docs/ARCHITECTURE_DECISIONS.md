# G2E Architecture Decisions

## ADR-001 — G2E core is independent; GWF is the default runtime

**Decision:** G2E owns goal→claim→proof→evidence→adjudication→next-step semantics. GWF is the default execution/governance backend through an adapter.

**Reason:** GWF already solves authority, persistent governed state, recovery, GitHub safety, agent protocol and handoff. Putting the G2E reasoning engine directly in GWF core would conflate workflow runtime with proof planning.

## ADR-002 — Do not hard-code MindForge phases

**Decision:** M0–M4 are empirical reference evidence, not canonical G2E phases.

**Reason:** G2E must work for model engineering, systems research, scientific studies and other technical goals.

## ADR-003 — GWF execution success is not G2E PASS

**Decision:** executor completion and proof adjudication remain separate states.

**Reason:** a valid experiment may complete successfully and scientifically FAIL.

## ADR-004 — Agent apps are adapters, never source of truth

**Decision:** Codex/ChatGPT are first-class priority adapters; Claude/Gemini follow; ARC is a transport for other model agents.

**Reason:** leverage existing harnesses while keeping G2E portable and provider-neutral.

## ADR-005 — Standalone mode is mandatory

**Decision:** G2E can run without GWF using a minimal durable runtime.

**Reason:** avoid architectural lock-in and enable bootstrapping/lightweight adoption. Standalone mode may expose fewer capabilities but may not weaken core proof invariants.

## ADR-006 — Dynamic proof generation, static governance

**Decision:** proof obligations may be generated dynamically from the current claim/evidence graph, but every executable obligation must be frozen before execution.

**Reason:** adaptability is required; post-outcome semantic drift is not.

## ADR-007 — Integrate + qualify before rebuild

**Decision:** mature trainers, evaluators, SCMs, runtimes and agent harnesses should be integrated behind adapters and qualified.

**Reason:** G2E’s differentiator is evidence-governed proof orchestration, not reimplementation of commodity infrastructure.

## References

- [G2E README](../README.md)
- [PRD Index](PRD_INDEX.md)
- [GWF Agent Interoperability Foundation](../../docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)
- [MindForge reference evidence](https://github.com/minhtri22/MindForge/tree/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline)
