# G2E Framework — Lineage

**Policy:** append-only. Add short phase outcomes only after the phase has an authoritative PASS/FAIL/INVALID/UNRESOLVED result. Do not record transient implementation errors, debugging failures, or ordinary test iterations.

## Entries

### G2E-P0 — Foundation Specification

- **Status:** PASS
- **Specification commit:** `636f2959d4e927a0ccd008877fa36da2a4681524`
- **QA commit:** `4aad03c31611888037544cf1f1d5cb16b758f3f1`
- **Result:** G2E established as an independent Goal-to-Evidence core; GWF is the default execution/governance backend; standalone execution remains required.
- **Agent direction:** Codex/ChatGPT first; Claude/Gemini next; ARC is retained as transport for other model-backed agents.
- **Next:** P1 — Core Schemas.


### G2E-P0.1 — Semantic Specification Hardening

- **Status:** PASS
- **Findings audit:** `2fab50299800e9ac437f92aec796b3b104c46cc1`
- **Remediation:** `ed88ec721342456bbb90006b41e2308bdc043fcd`
- **QA:** `affbcbc8c8441d3d10cae0d47620b19e9e3d262f`
- **Result:** 22 semantic/logic findings resolved; state/verdict namespaces, Goal/Claim closure, retry, evidence admission, freshness, authority, dependency and runtime-parity contracts are now frozen for P1 handoff.
- **Next:** P1 — Core Schemas.
