# PRD-11 — Standalone Runtime

## Purpose

Allow G2E to operate without GWF while preserving the minimum invariants required for trustworthy goal-to-evidence execution.

Standalone mode exists for portability, bootstrapping and lightweight use. It must not become a weaker “unsafe mode.”

## Minimum standalone services

Standalone mode MUST provide:

- Goal/Claim/Proof persistence;
- canonical hashing/versioning;
- evidence graph persistence;
- execution-attempt ledger;
- adjudication terminality;
- freshness/protected-resource ledger;
- authority mode at least `single_user`;
- retry/amendment enforcement;
- artifact references;
- exportable Goal Result Package.

A filesystem + SQLite implementation is acceptable for v0.x if crash recovery and atomic writes are explicit.

## Compatibility

Standalone logical schemas must match the GWF adapter’s semantic schemas even if storage differs.

Required invariant:

```text
same GoalContract
same ClaimGraph
same ProofObligation
same EvidenceGraph semantics
same Adjudication
```

Moving a project from standalone to GWF must not reinterpret prior verdicts.

## Reduced capabilities

Standalone MAY lack:

- multi-user approval;
- distributed workers;
- rich domain registry;
- advanced tenancy;
- GWF-native GitHub mutation enforcement.

Missing capabilities must be explicit in a `RuntimeCapabilityManifest`; they cannot be silently emulated.

## Acceptance criteria

1. A complete small proof program can run without GWF.
2. Terminal adjudication remains immutable.
3. Protected-resource exposure is persisted across restarts.
4. Atomic/crash-safe persistence is tested.
5. Export/import roundtrip into GWF preserves semantic identities.
6. Unsupported governance capability fails closed where required.

## Dependencies

- [PRD-04 Evidence Graph](PRD_04_EVIDENCE_GRAPH.md)
- [PRD-05 Adjudicator](PRD_05_ADJUDICATOR.md)
- [PRD-07 Execution Protocol](PRD_07_EXECUTION_PROTOCOL.md)
- [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)

## References

- [G2E README](../README.md)
- [GWF Runtime](../../src/gwr/runtime.py)
- [GWF state-authoritative philosophy](../../README.md)
