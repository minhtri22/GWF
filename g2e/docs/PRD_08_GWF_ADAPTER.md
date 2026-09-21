# PRD-08 — GWF Adapter

## Purpose

Make GWF the **default execution and governance backend** for G2E without making GWF a hard dependency of the G2E core.

## Architecture boundary

```text
G2E Core
  goal / claim / proof / adjudication
          ↓
      GWF Adapter
          ↓
GWF runtime primitives
  artifacts/revisions
  authority/approval
  phase protocol
  recovery
  GitHub plugin
  domain/skill registry
  handoff
```

G2E remains responsible for proof semantics. GWF remains responsible for governed execution state.

## Adapter responsibilities

The adapter MUST map:

- Goal Contract → governed GWF project/artifact revision;
- Claim/Proof identities → GWF artifacts and traces;
- G2E execution envelope → GWF phase/workunit execution;
- G2E authority requirement → GWF actor/approval policy;
- G2E evidence → GWF evidence/artifact references;
- G2E terminal adjudication → immutable governed decision artifact;
- G2E selection/handoff → GWF checkpoint/handoff state.

The adapter MUST NOT:

- implement claim decomposition inside GWF core;
- silently translate GWF `SUCCEEDED` to G2E PASS;
- weaken G2E no-rescue/freshness semantics;
- require a new GWF domain for every dynamically generated proof.

## Dynamic work

Because G2E generates proof obligations dynamically, the adapter should prefer a generic G2E execution domain/workunit facade over runtime generation of arbitrary trusted domain YAML.

Any dynamic workunit representation must still pass authority, skill, preflight, execution, verification and handoff controls.

## Versioning

The adapter records:

- G2E core version;
- GWF runtime version;
- GWF domain revision if used;
- mapping schema version;
- active agent-interoperability contract revision.

## Acceptance criteria

1. Same G2E Proof Obligation can execute in GWF and standalone modes with equivalent semantic identity.
2. GWF persisted state can reconstruct G2E execution/evidence mapping.
3. No GWF PASS/phase state is confused with G2E claim PASS.
4. Recovery paths respect frozen G2E retry policy.
5. GWF approval/authority remains stricter where applicable.
6. GWF can be upgraded independently when adapter compatibility holds.

## Dependencies

- [PRD-07 Execution Protocol](PRD_07_EXECUTION_PROTOCOL.md)
- [PRD-09 Agent App Adapters](PRD_09_AGENT_APP_ADAPTERS.md)
- [PRD-10 GitHub Adapter](PRD_10_GITHUB_ADAPTER.md)
- [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)

## References

- [GWF README](../../README.md)
- [GWF DomainSDK](../../src/gwr/domain_sdk.py)
- [GWF Runtime](../../src/gwr/runtime.py)
- [GWF Agent Interoperability Foundation](../../docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)
- [GWF 7-Wave implementation plan](../../docs/IMPLEMENTATION_7_WAVES_PLAN.md)
