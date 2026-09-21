# PRD-10 — GitHub Adapter

## Purpose

Use GitHub as the default source/external-execution/evidence ledger for code-centric proofs while keeping G2E core SCM-provider neutral.

GitHub execution is not automatically “independent”; IndependencePolicy determines independence.

## Capabilities

The adapter SHOULD support:

- exact repo/branch/commit/blob identity;
- safe branch creation;
- expected-head writes;
- commit verification;
- workflow dispatch/observation;
- job/log/artifact evidence capture;
- compare/ancestry verification;
- evidence-only closure verification;
- release/tag identity when needed.

## Safety model

Every governed write:

1. freezes expected base/head;
2. freezes intended file/change scope;
3. executes through authorized credentials/provider;
4. re-fetches resulting commit/ref;
5. verifies expected and unintended changes.

Git commit/workflow success is candidate execution evidence, never automatic proof PASS.

## Evidence-only closure pattern

When a proof chooses this pattern:

```text
implementation SHA
  ↓
workflow on exact SHA
  ↓
admitted result hashes
  ↓
evidence-only commit
  ↓
compare verifies no code mutation after qualification
```

The pattern is optional per ProofObligation.

## Provider-neutral core

Core source identity uses generic revision/artifact references. GitHub-specific fields remain adapter metadata.

## Acceptance criteria

1. Exact source identity recorded.
2. Stale expected-head write fails closed.
3. Workflow evidence binds exact source SHA.
4. Evidence-only ancestry verifiable.
5. GitHub green never maps directly to G2E PASS.
6. Read-only acquisition and mutation paths remain distinct.
7. Tokens/secrets never persist.
8. Independence is never inferred solely from GitHub-hosted execution.

## Dependencies

- **HARD:** [PRD-07 Execution Protocol](PRD_07_EXECUTION_PROTOCOL.md)
- **INTEGRATION:** [PRD-08 GWF Adapter](PRD_08_GWF_ADAPTER.md) in default mode
- **CROSS_CUTTING:** [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)
- **NORMATIVE:** [Core Semantics](CORE_SEMANTICS.md)

## References

- [GWF README](../../README.md)
- [GWF 7-Wave GitHub/revision plan](../../docs/IMPLEMENTATION_7_WAVES_PLAN.md)
- [MindForge M4 evidence-only closure](https://github.com/minhtri22/MindForge/commit/62141d530832f7694342fe92704a5975bfdbbded)
