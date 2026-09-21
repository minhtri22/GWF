# G2E P0 Documentation QA Checklist

## Scope

This QA covers the G2E foundation specification set on `feature/g2e-framework`.

Required files:

- `g2e/README.md`
- `g2e/LINEAGE.md`
- `g2e/docs/PRD_INDEX.md`
- `g2e/docs/PRD_01_GOAL_CONTRACT.md` through `PRD_14_SECURITY_AUTHORITY.md`
- `g2e/docs/ARCHITECTURE_DECISIONS.md`
- `g2e/docs/PHASE_PLAN.md`

## Acceptance checklist

- [ ] README defines Goal → Claim → Proof → Evidence → Adjudication → Next-Step → Final Result architecture.
- [ ] G2E core is explicitly independent from GWF.
- [ ] GWF is explicitly the default execution/governance backend.
- [ ] Standalone runtime is required and cannot weaken proof invariants.
- [ ] Codex/ChatGPT are first-priority agent-app adapters.
- [ ] Claude and Gemini are later adapters.
- [ ] ARC is modeled as transport, not resource/model identity.
- [ ] Agent/provider/transport/harness identities are separate.
- [ ] Every PRD has Purpose, Dependencies, References, and Acceptance Criteria.
- [ ] Internal G2E dependency links resolve.
- [ ] Referenced GWF documents resolve on the branch baseline.
- [ ] MindForge M0–M4 is reference evidence, not a hard-coded G2E workflow.
- [ ] PASS/FAIL/INVALID/UNRESOLVED semantics are explicit.
- [ ] No-rescue and protected-resource/freshness constraints are explicit.
- [ ] Executor success is not confused with G2E proof PASS.
- [ ] Final Goal Result Package exposes unsupported/failed claims instead of hiding them.
- [ ] Initial implementation phase plan starts with schemas/core before agent adapters.
- [ ] LINEAGE is append-only and excludes transient implementation/test errors.

## Verdict

Pending candidate-document QA.
