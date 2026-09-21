# PRD-06 — Next-Step Selector

## Purpose

Recompute what remains unproven and select the next admissible ProofObligation/attempt under deterministic admissibility and a frozen SelectionPolicy.

## Stage A — admissibility

A candidate is admissible only when:

- all HARD dependencies are satisfied;
- Claim lifecycle is READY/ACTIVE as appropriate;
- no closed ProofObligation is being replayed;
- RetryPolicy allows a replacement INVALID attempt when applicable;
- freshness/protected-resource rules allow access;
- authority and IndependencePolicy can be satisfied;
- lineage/amendment rules are valid.

The admissible set must be deterministic from canonical state.

## Stage B — ranking/choice

Ranking semantics are normative in [Core Semantics §11](CORE_SEMANTICS.md).

Default SelectionPolicy orders by:

1. hard dependencies unblocked, descending;
2. protected resource cost, ascending;
3. resource cost class, ascending;
4. implementation complexity, ascending;
5. proof ID lexical tie-break.

“Information gain” may be advisory metadata but is not a default deterministic field.

An authorized user may choose a different member of the admissible set; the SelectionDecision records that choice/rationale. An inadmissible candidate requires a prior governed normative amendment.

## Outcome behavior

- PASS: recompute Claim/Goal state and admissible set.
- FAIL: preserve terminal proof result; open a different Claim/proof only if graph/policy permits.
- INVALID: replacement attempt only under the same frozen ProofObligation and retry budget; otherwise no retry.
- UNRESOLVED: close the ProofObligation; further evidence requires a new ProofObligation unless bounded multi-part collection was predeclared.

## Acceptance criteria

1. Selector never chooses unsatisfied HARD dependencies.
2. Same canonical state + SelectionPolicy produces same admissible set/ranking.
3. Protected resources cannot be selected early.
4. FAIL/UNRESOLVED cannot be converted into hidden retries.
5. INVALID retry preserves semantic ProofObligation identity.
6. SelectionDecision records policy hash and any authorized non-default choice.
7. Minimality is treated as ranking, not proof validity.

## Dependencies

- **HARD:** PRD-02 through PRD-05
- **CONDITIONAL:** [PRD-13 Reference Acquisition](PRD_13_REFERENCE_ACQUISITION.md)
- **CROSS_CUTTING:** [PRD-14 Security & Authority](PRD_14_SECURITY_AUTHORITY.md)
- **NORMATIVE:** [Core Semantics](CORE_SEMANTICS.md)

## References

- [G2E README](../README.md)
- [GWF 7-Wave dependency selection model](../../docs/IMPLEMENTATION_7_WAVES_PLAN.md)
