# G2E P4 — Base GWF Adapter Result

## Verdict

**PASS**

Qualified implementation SHA:

`1f6d49957c0c0dffa7b83c11caebed4ab2b90e0b`

Qualified baseline:

`d2e79ae004414d43cfbf8c58020ee501f482c363`

Pre-implementation mapping/spec lock:

`9d22109e0a2e2ca865d11018aa05c97dc8d70c24`

## Authoritative qualification

All runs below execute the exact qualified implementation SHA `1f6d49957c0c0dffa7b83c11caebed4ab2b90e0b`.

- P1: run `35584223713`, job `106283704496` — **29/29 PASS**
- P2: run `35584223744`, job `106283704804` — P1 **29/29 PASS** + P2 **43/43 PASS**
- P3: run `35584223806`, job `106283705392` — P1 **29/29 PASS** + P2 **43/43 PASS** + P3 **25/25 PASS**
- P4: run `35584223810`, job `106283705280` — P1 **29/29 PASS** + P2 **43/43 PASS** + P3 **25/25 PASS** + P4 **17/17 PASS**
- compileall for `src/g2e` + `src/gwr`: PASS
- standalone no-GWF-import assertion: PASS
- P4 no-P4L/GAC/Reference-Acquisition import assertion: PASS

## Implemented base GWF mapping

P4 adds a static reviewed GWF domain contract and a base adapter only:

- `src/g2e/gwf_domain.py`
- `src/g2e/gwf_adapter.py`

The adapter persists every canonical G2E object inside a GWF mapping wrapper containing:

```text
mapping_version
schema_kind
g2e_exact_ref
canonical_object
```

The canonical object is re-parsed with the G2E authoritative parser on persistence and load. GWF artifact IDs, revision IDs, run IDs, evidence IDs, checkpoint IDs and GWF content hashes remain runtime mappings and never replace G2E canonical identity.

## Hash-domain separation

P4 explicitly preserves the distinction:

```text
G2E canonical hash
!=
GWF wrapper/runtime hash
```

G2E canonical hashes remain authoritative. A GWF revision that maps the wrong exact G2E ref, an altered canonical object under an existing G2E object/revision, or an unsupported mapping version fails closed.

## Generic execution facade

P4 uses one static `g2e_execute_proof` workunit.

Properties qualified:

- one GWF run maps to one G2E ExecutionAttempt;
- GWF runtime retry expansion is disabled with `max_attempts=1`;
- replacement attempts remain governed by frozen G2E ProofRetryPolicy;
- GWF `COMPLETED` / WorkUnit `SUCCEEDED` map only to executor state;
- scientific PASS/FAIL/INVALID/UNRESOLVED remains owned by the P2 deterministic engine;
- candidate EvidenceRecord payload digests are verified with the G2E canonical hash profile;
- stricter GWF authority can block execution but cannot create a scientific verdict.

## Protected-resource and recovery parity

P4 keeps protected-resource state as canonical G2E objects and applies the P2 state machine.

Qualified behavior includes:

```text
FRESH -> RESERVED -> EXPOSED
```

and uncertain execution recovery:

```text
LOCKED/RUNNING + uncertain protected access
-> PREEMPTED attempt
-> EXPOSED protected resource
```

Backward freshness transitions remain rejected.

## Standalone ↔ GWF parity

The frozen P4 fixtures demonstrate parity for:

- Goal / Claim / Proof and frozen-policy identity;
- ExecutionAttempt terminal identity;
- provider-neutral ExecutionResult fields;
- candidate EvidenceRecord identity and payload digest;
- P2 EvidenceAdmission and Adjudication;
- protected-resource terminal state;
- Claim resolution;
- Goal verdict;
- Result Package semantic manifest.

For the same bounded canonical execution, standalone and GWF produce the same semantic Result Package manifest. The outer PackageSeal may differ by runtime identity/version, which is runtime provenance rather than a new G2E semantic result.

## Restart / persistence reconstruction

A fresh `GovernedWorkflowRuntime` process reopening the same GWF database reconstructs and independently verifies:

- final ExecutionAttempt;
- ExecutionResult;
- EvidenceRecord;
- evidence payload digest;
- checkpoint exact-ref set.

This proves GWF persistence is a reconstructable system of record for the P4 mapping without becoming semantic authority.

## Negative reinterpretation qualification

Qualified fixtures reject or preserve fail-closed behavior for:

- GWF `SUCCEEDED` -> Claim PASS implication;
- changed canonical hash under the same G2E revision;
- wrong GWF revision -> G2E exact-ref mapping;
- unsupported adapter mapping version;
- DecisionRule mismatch;
- EvidenceAdmissionPolicy mismatch;
- RetryPolicy mismatch;
- protected-resource backward freshness transition;
- terminal Adjudication rewrite;
- unauthorized GWF execution;
- checkpoint exact-ref substitution;
- Result Package semantic reinterpretation/re-seal regression through the qualified P3 verifier.

## P3 baseline integrity

All 8 P3-qualified implementation/test/workflow blobs remain byte-identical to the P3 qualification evidence on the P4 qualified SHA.

P4 did not modify the P1-P3 semantic engine, standalone runtime, P1/P2/P3 tests, or P3 workflow to obtain PASS.

## Findings closure

The pre-implementation findings are closed:

- `P4-F01` G2E/GWF hash-domain mismatch — **RESOLVED**
- `P4-F02` runtime success vs scientific PASS — **RESOLVED**
- `P4-F03` runtime retry ownership — **RESOLVED**
- `P4-F04` protected-resource freshness ownership — **RESOLVED**
- `P4-F05` persistence/approval vs semantic ownership — **RESOLVED**

Post-CI QA added and qualified two missing proof surfaces before close:

- fresh-runtime restart reconstruction;
- standalone/GWF Result Package semantic-manifest parity.

No implementation change was required after the final exact-SHA qualification.

## Scope boundary

P4 does **not** implement:

- GAC publication/query;
- Shared Library cross-project backend;
- CatalogEntry/CatalogQueryExecution;
- Reference Acquisition catalog bridge;
- P4L Shared Library integration;
- Codex/ChatGPT profiles;
- GitHub Evidence Adapter.

## Authorization

P4 is formally qualified **PASS**.

P4L remains **CONDITIONAL / CLOSED**. P4 PASS authorizes only an exact capability/dependency audit against `g2e/docs/GWF_LIBRARY_INTEGRATION_MAPPING.md`; it does not authorize P4L implementation by implication.
