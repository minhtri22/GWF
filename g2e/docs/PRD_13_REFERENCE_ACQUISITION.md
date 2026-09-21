# PRD-13 — Reference Acquisition

## Purpose

Allow G2E to obtain external prior art, specifications, repository evidence and current capability information without contaminating protected study outcomes or creating an ungoverned evidence universe.

## Default strategy

When GWF is the runtime, G2E SHOULD consume the GWF Reference Acquisition capability rather than duplicate it.

G2E adds one semantic layer: acquired references may inform **Goal interpretation, Claim decomposition and Proof design**, but they do not automatically prove the target claim.

## Acquisition modes

G2E must preserve temporal semantics compatible with GWF:

- `PRE_LOCK`;
- `LOCKED_PRE_OUTCOME`;
- `POST_OUTCOME`.

A newly discovered reference that changes the study/claim meaning after lock must route through amendment or new lineage; it cannot silently rewrite the frozen proof.

## Reference record

G2E needs:

- canonical source identity;
- exact inspected snapshot/revision;
- retrieval query/session identity;
- provider;
- timestamp;
- disposition;
- relevant extracted capability/fact;
- relation to claims/proofs;
- content digest where feasible.

## Use classes

References may be classified as:

- prior art/context;
- implementation capability evidence;
- specification authority;
- baseline source;
- direct empirical evidence.

The class determines whether it can support a formal claim.

## Implementation references

For external frameworks/tools, G2E should prefer official docs/source and pin/revalidate capability at implementation time. Examples include trainer, evaluator, converter, runtime and agent-app harness integrations.

## Acceptance criteria

1. Exact executed queries/retrieval sessions are attributable.
2. Canonical source and inspected snapshot are separate.
3. Reference acquisition after outcome exposure cannot rewrite the original proof.
4. A tool capability statement has dated/pinned evidence.
5. GWF mode reuses GWF registry/retrieval primitives.
6. Standalone mode can export equivalent reference records.

## Dependencies

- [PRD-01 Goal Contract](PRD_01_GOAL_CONTRACT.md)
- [PRD-02 Claim Graph](PRD_02_CLAIM_GRAPH.md)
- Cross-cutting [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)

## References

- [GWF Reference Acquisition Specification](../../docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md)
- [GWF 7-Wave plan — Reference Acquisition](../../docs/IMPLEMENTATION_7_WAVES_PLAN.md)
- [GWF Finding checklist — temporal/reference findings](../../docs/Finding_checklist.md)
