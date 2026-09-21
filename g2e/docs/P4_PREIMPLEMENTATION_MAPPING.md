# G2E P4 — Base GWF Adapter Pre-Implementation Mapping

**Status:** SPECIFICATION FROZEN FOR IMPLEMENTATION  
**Phase:** P4 — Base GWF Adapter  
**Baseline:** `d2e79ae004414d43cfbf8c58020ee501f482c363`  
**P4L/GAC:** CLOSED / OUT OF SCOPE

## 1. Scientific question

P4 asks one question only:

> Does the same canonical G2E execution retain semantic identity and formal result when persisted/executed through GWF instead of the qualified standalone runtime?

GWF is an execution/governance/persistence substrate. It is not a semantic authority for Goal, Claim, Proof, Evidence, Adjudication or Goal verdict.

## 2. Frozen mapping contract

| G2E semantic object/state | GWF representation | Ownership rule |
| --- | --- | --- |
| GoalContract / GoalClosureContract | `Artifact` + immutable `Revision` wrapper | G2E exact ref remains authoritative |
| ClaimGraph / Claim / ProofObligation / frozen policies | `Artifact` + immutable `Revision` wrapper | GWF IDs are mappings only |
| ExecutionAttempt | generic `g2e_execute_proof` WorkUnit/Run plus canonical G2E attempt revisions | GWF runtime status maps only to executor state |
| EvidenceRecord | canonical G2E object plus GWF Evidence payload record | admission/verdict remains G2E-owned |
| Adjudication / ProofResult / Claim/Goal result objects | canonical G2E artifact revisions | never derived from GWF PASS-like state |
| ProtectedResource | canonical G2E revisions persisted in GWF | G2E monotonic freshness semantics remain authoritative |
| Authority | GWF actor/policy checks may be stricter | stricter GWF denial blocks execution; it cannot create a scientific verdict |
| Recovery | GWF checkpoint/runtime state + G2E fail-closed recovery mapping | uncertain protected access maps to EXPOSED |
| Handoff/checkpoint | GWF checkpoint metadata containing exact G2E refs | checkpoint is resumability metadata, not semantic reinterpretation |

## 3. Identity rule

Every persisted canonical object is wrapped as:

```text
mapping_version
schema_kind
g2e_exact_ref
canonical_object
```

The adapter MUST re-parse `canonical_object` with the G2E authoritative parser and MUST verify that the reconstructed exact ref equals `g2e_exact_ref`.

GWF artifact IDs, revision IDs, run IDs, evidence IDs, checkpoint IDs and GWF revision `content_hash` values MUST NOT replace any G2E object ID/revision/hash.

## 4. Generic execution facade

P4 uses one static, reviewed GWF domain contract and one generic `g2e_execute_proof` workunit.

The workunit is runtime-only and MUST:
- accept exact persisted G2E attempt/proof references;
- authorize through normal GWF authority;
- use one GWF run per G2E ExecutionAttempt;
- disable implicit GWF retry expansion (`max_attempts=1` at the workunit level);
- emit provider-neutral ExecutionResult/candidate EvidenceRecord objects;
- never emit G2E PASS/FAIL.

Scientific retry remains governed by the frozen G2E ProofRetryPolicy and P2 core.

## 5. Pre-implementation semantic QA findings

### P4-F01 — Hash-domain mismatch must remain explicit

**Finding:** GWF `content_hash()` and G2E canonical hashing are different hash domains. G2E normalizes Unicode NFC and has its own canonical profile; GWF hashes its runtime payload representation.

**Required remediation:** never compare or substitute GWF revision hash for G2E `content_hash`. Persist and independently verify the complete G2E canonical object inside the mapping wrapper.

### P4-F02 — Runtime success is not scientific PASS

**Finding:** GWF uses runtime/workunit states such as `COMPLETED` and `SUCCEEDED`.

**Required remediation:** adapter maps those states only to G2E ExecutionAttempt/ExecutionResult executor state. Adjudication remains exclusively the P2 deterministic engine.

### P4-F03 — Generic GWF retry could violate frozen G2E retry ownership

**Finding:** GWF WorkUnit/DistributedRuntime can retry according to runtime retry budgets.

**Required remediation:** P4 generic workunit is single-attempt (`max_attempts=1`). Any replacement attempt is created only by G2E under the frozen ProofRetryPolicy.

### P4-F04 — GWF has no native G2E protected-resource freshness semantics

**Finding:** GWF recovery/checkpoint state does not itself prove the G2E FRESH→RESERVED→EXPOSED invariant.

**Required remediation:** protected resources remain canonical G2E objects; P4 applies the P2 protected-resource transition function and fail-closed recovery. No GWF recovery path may map EXPOSED backward to FRESH.

### P4-F05 — GWF persistence approval must not become semantic ownership

**Finding:** GWF artifact revisions and authority policies govern writes, but persistence approval is not G2E scientific approval/adjudication.

**Required remediation:** the static domain treats mapped canonical objects as immutable persistence mirrors; GWF still requires authorized mutation APIs, while semantic validity is verified by G2E `parse_authoritative`.

## 6. Required P4 qualification matrix

Positive parity:
1. canonical Goal/Claim/Proof/policy identity round-trip;
2. standalone vs GWF execution-attempt terminal-state parity;
3. candidate EvidenceRecord and payload digest parity;
4. P2 EvidenceAdmission + Adjudication parity on GWF-produced evidence;
5. protected-resource RESERVED/EXPOSED parity;
6. Claim resolution and Goal verdict parity using the same P2 core;
7. Result Package semantic identity produced from the same canonical objects;
8. checkpoint/handoff carries exact G2E refs without replacing them.

Negative reinterpretation fixtures:
- GWF `SUCCEEDED` cannot become Claim PASS;
- changed canonical hash is rejected;
- wrong GWF mapping to a G2E exact ref is rejected;
- DecisionRule mismatch is rejected by P2;
- EvidenceAdmissionPolicy mismatch is rejected;
- RetryPolicy mismatch cannot expand retries;
- protected-resource backward freshness transition is rejected;
- terminal Adjudication rewrite remains rejected by the qualified storage/semantic path;
- re-sealed false Result Package remains rejected;
- unsupported mapping version fails closed;
- unauthorized GWF actor cannot execute.

## 7. Scope exclusions

P4 MUST NOT implement or call:
- GAC publication/query;
- Shared Library cross-project backend;
- CatalogEntry / CatalogQueryExecution;
- Reference Acquisition catalog bridge;
- P4L capability paths.

## 8. Exit gate

P4 may PASS only after:
- exact-SHA P1/P2/P3 regressions pass;
- exact-SHA P4 adapter suite passes;
- mapping/negative fixtures pass;
- post-CI semantic QA confirms no GWF state became G2E semantic authority;
- evidence is recorded without implementation mutation;
- only then may LINEAGE receive an append-only P4 entry.

Until then the frontier remains P4.
