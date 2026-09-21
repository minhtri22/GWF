# PRD-11 — Standalone Runtime

## Purpose

Run G2E without GWF while preserving the same canonical semantics and minimum governance invariants.

Standalone is portability/bootstrap mode, not a weaker unsafe mode.

## Minimum services

MUST provide:

- canonical object persistence/versioning;
- Goal/Claim/Proof/Evidence graph storage;
- attempt ledger;
- adjudication terminality;
- protected-resource reservation/exposure ledger;
- Retry/Amendment enforcement;
- minimum authority mode (`single_user`);
- RuntimeCapabilityManifest;
- artifact refs;
- sealed Goal Result Package.

Filesystem + SQLite is acceptable for v0.x when atomic/crash recovery is explicit.

## Identity and migration

Canonical G2E IDs/hashes are runtime-independent.

Standalone→GWF migration:

- preserves every canonical G2E ID/hash;
- creates separate runtime mapping IDs;
- preserves adjudications/exposure history;
- records import/export manifest hashes;
- fails closed on incompatible major schema/runtime capability.

No migration may reinterpret a prior verdict.

## Reduced capabilities

Standalone MAY lack multi-user approval, distributed workers, rich domain registry or GWF-native mutation enforcement. Missing capability is explicit in RuntimeCapabilityManifest.

If a ProofObligation requires an unavailable capability (e.g. separation of duty), execution fails closed; standalone may not silently waive it.

## Acceptance criteria

1. Complete bounded proof program runs without GWF.
2. Terminal adjudication immutable across restart.
3. Protected exposure survives crash/restart fail-closed.
4. Atomic persistence tested.
5. Export/import to GWF preserves canonical identities and semantics.
6. Unsupported required governance capability fails closed.
7. Result package integrity verifies independently.

## Dependencies

- **HARD:** [PRD-04 Evidence Graph](PRD_04_EVIDENCE_GRAPH.md), [PRD-05 Adjudicator](PRD_05_ADJUDICATOR.md), [PRD-07 Execution Protocol](PRD_07_EXECUTION_PROTOCOL.md)
- **INTEGRATION:** [PRD-08 GWF Adapter](PRD_08_GWF_ADAPTER.md) for migration/parity
- **CROSS_CUTTING:** [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)
- **NORMATIVE:** [Core Semantics](CORE_SEMANTICS.md)

## References

- [GWF Runtime](../../src/gwr/runtime.py)
- [G2E README](../README.md)
