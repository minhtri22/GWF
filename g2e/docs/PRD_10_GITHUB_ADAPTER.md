# PRD-10 — GitHub Adapter

## Purpose

Use GitHub as the default source/evidence/independent-execution ledger for code-centric G2E proofs while keeping G2E core repository-provider neutral.

## Capabilities

The adapter SHOULD support:

- exact repository/branch/commit/blob identity;
- feature-branch creation;
- expected-head safe writes;
- commit verification;
- workflow dispatch/observation;
- job/log evidence capture;
- artifact references;
- compare/ancestry verification;
- evidence-only commit verification;
- release/tag identity where needed.

## Safety model

Every governed write must:

1. freeze expected base/head;
2. prepare explicit file/change scope;
3. execute through an authorized provider;
4. re-fetch resulting commit/ref;
5. verify expected changes and absence of unintended changes.

A commit is not itself proof PASS. GitHub Actions success is execution evidence; G2E adjudication decides the proof claim.

## Evidence patterns

The adapter should natively normalize patterns learned from MindForge:

```text
implementation commit
  ↓
CI on exact SHA
  ↓
authoritative result hashes
  ↓
evidence-only commit
  ↓
compare confirms no code changed after qualification
```

This pattern is optional per proof, not globally mandatory.

## GitHub-independent core

G2E must allow another SCM/executor provider later. Core schemas therefore refer to generic source revisions and external execution references.

## Acceptance criteria

1. Exact commit/blob identity is recorded.
2. Stale expected-head write fails closed.
3. Workflow evidence is bound to exact source SHA.
4. Evidence-only ancestry can be verified.
5. Adapter cannot translate workflow green status directly into proof PASS.
6. Tokens/secrets are never persisted.
7. Read-only acquisition and mutation paths are distinct.

## Dependencies

- [PRD-07 Execution Protocol](PRD_07_EXECUTION_PROTOCOL.md)
- [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)
- Default GWF mode: [PRD-08 GWF Adapter](PRD_08_GWF_ADAPTER.md)

## References

- [GWF GitHub safety overview](../../README.md)
- [GWF GitHub Plugin/SHA QA plan references](../../docs/IMPLEMENTATION_7_WAVES_PLAN.md)
- [MindForge M4 evidence-only closure](https://github.com/minhtri22/MindForge/commit/62141d530832f7694342fe92704a5975bfdbbded)
