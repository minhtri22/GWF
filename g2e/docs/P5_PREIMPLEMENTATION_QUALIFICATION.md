# G2E P5 — Pre-Implementation Qualification

**Status:** FROZEN CANDIDATE FOR ZERO-IMPLEMENTATION QA  
**Phase:** P5 — Codex and ChatGPT App Profiles  
**Audit baseline:** `660cfbb98ab2066e3fb94adda7657087de9ab26f`  
**Runtime adapters:** NOT AUTHORIZED  
**P4L:** CLOSED / NON-BLOCKING

## 1. Qualification question

P5 pre-implementation qualification asks one bounded question:

> Are the dependencies, identity model, capability-discovery contract, authority/independence rules, fail-closed behavior, and qualification fixture sufficiently frozen to implement Codex and ChatGPT profiles without guessing capability parity or weakening canonical G2E execution semantics?

This qualification does **not** ask whether either app is currently available or capable. Availability is established only by profile-specific discovery evidence from the actual harness. Public/product claims, another app's qualification, or a green unrelated workflow are not capability evidence.

Passing this document's QA does not by itself authorize a Codex or ChatGPT runtime adapter.

---

## 2. Exact authority baseline

G2E authority used by this qualification:

| Authority | Exact blob / evidence |
| --- | --- |
| `PHASE_PLAN.md` | `f8d43320ed615c80f21c0f3bfdfa3f6dd951205d` |
| PRD-09 Agent App Adapters | `22c3a6becd1175d90d840d94ba0dd39d5374578b` |
| PRD-07 Execution Protocol | `8072310b3220f94e765b992d91a1904de67348cb` |
| PRD-08 GWF Adapter | `a0e481e13434e7b2c22df381261cd6820c9bf41a` |
| PRD-14 Security & Authority | `7773f998f50ac252ac92b3d92329789666d57ef9` |
| Core Semantics | `d224652753378d9a6fb6aec94f5344f63a52b0c1` |
| P1 schema implementation blob | `62b4ab6717bc6c0a00f3670c73024df5a6ad41ca` |
| GWF Agent Interoperability Foundation | `fe6669dabc77c03474bbbffc76bb1e8b746c6ffc` |

Qualified execution lineage used as dependency evidence:

- P1 qualified implementation: `2fc077f8bc84f8dbdb42c180b3edc7af9418a6c1`;
- P1.1 DecisionRule prerequisite: `0002790f0ea3da1c6e03b69124e3bfd38741b3b5`;
- P1.2 runtime prerequisite schemas: `fe02721b436e94fc7cd34a68f136d6088ca4b411`;
- P1.3 package-reference integrity: `931b7d23239f625136be12d26564e9f89f8785b9`;
- P2 qualified implementation: `c2fc03a7470b835904252246421e1b8d9a1ec5ef`;
- P3 qualified implementation: `b9345f3cbeba564a0bf666d388d3873d9ffd1191`;
- P4 qualified implementation: `1f6d49957c0c0dffa7b83c11caebed4ab2b90e0b`;
- P4 evidence closure: `fbae7dcf6484556a1acf339f8187f8a2092faef0`;
- P4 post-close integrity: PASS through `dec4c73ad15e9ee0a5883dee4a35bf6f7621bf89`;
- P4L exact capability audit: CLOSED / NOT AUTHORIZED at `660cfbb98ab2066e3fb94adda7657087de9ab26f`.

P4L is conditional and explicitly does not block G2E core/standalone progress. PRD-09 has:

- HARD dependency: PRD-07;
- INTEGRATION dependency: PRD-08 in GWF mode;
- CROSS_CUTTING dependency: PRD-14;
- NORMATIVE dependency: Core Semantics.

Therefore P4L is not a P5 admission dependency.

---

## 3. Dependency qualification

### P5-Q0 — PRD-07 execution semantics

**Resolved:** PASS by existing P1/P2/P3/P4 lineage.

Required invariants already qualified before P5:

- one immutable ProofObligation may have distinct ExecutionAttempt identities;
- executor lifecycle is not a scientific verdict;
- material agent/provider/resource reassignment is visible;
- RetryPolicy remains frozen;
- protected-resource recovery is fail-closed;
- ExecutionResult records app/provider/model/harness/transport identities;
- credentials do not persist.

P5 may specialize executor binding but may not reinterpret these rules.

### P5-Q0B — PRD-08 GWF integration

**Resolved:** PASS by P4.

GWF runtime IDs/statuses remain mapping/runtime state only. P5 profiles must feed the same canonical G2E attempt/result/evidence semantics through the base P4 adapter and cannot create a second adjudication path.

---

## 4. Separate profile rule

Codex and ChatGPT are one priority wave but two qualification subjects.

```text
Codex actual harness
      ↓
Codex capability discovery
      ↓
Codex AgentCapabilityManifest
      ↓
Codex AgentBinding
      ↓
Codex qualification evidence

ChatGPT actual harness
      ↓
ChatGPT capability discovery
      ↓
ChatGPT AgentCapabilityManifest
      ↓
ChatGPT AgentBinding
      ↓
ChatGPT qualification evidence
```

Forbidden inference:

```text
Codex supports X
    ⇏
ChatGPT supports X
```

and the reverse is equally forbidden.

A profile may be `AVAILABLE`, `UNAVAILABLE`, or `UNQUALIFIED`; unavailable/unsupported capability is not a failure of another profile.

No P5 document may rank model/app quality. Capability manifests are descriptive only.

---

## 5. Capability discovery contract

Discovery occurs against the **actual harness revision** that will be bound to an attempt.

Every discovery result must record at least:

- `agent_app`;
- profile schema/version;
- discovery record identity/hash;
- harness identity and exact version/revision when available;
- provider identity when material/available;
- model identity when material/available;
- transport identity;
- external session/thread identity support;
- descriptive capabilities;
- execution constraints;
- maximum authority scope;
- credential requirements by opaque reference class only;
- workspace/repository visibility constraints;
- interruption/cancellation support;
- artifact/evidence extraction support;
- structured-output support;
- status/progress support;
- discovery evidence refs;
- known limitations;
- availability state.

Discovery must not persist raw reusable secrets or hidden chain-of-thought.

A capability is `available=true` only when the exact discovery evidence demonstrates it. Absence of evidence is `UNQUALIFIED`, not `true`.

Discovery is repeated when a material harness/app revision changes. Qualification from one app or one harness revision never migrates silently to another.

---

## 6. Pre-implementation schema/reuse audit

### Existing reusable G2E primitives

The current P1 schema already provides:

- `ExecutionAttemptEnvelope.agent_app`;
- `provider_ref`;
- `model_ref`;
- `harness_ref`;
- `transport_ref`;
- `authority_scope`;
- canonical proof/retry/protected-resource references;
- provider-neutral `ExecutionResult` carrying the same executor identity dimensions;
- canonical `IndependencePolicy`;
- canonical `AuthorityPolicy`.

These primitives remain authoritative and MUST be reused.

### P5-F01 — runtime capability identity must not be reused as agent-app identity

Current `RuntimeCapabilityManifest` describes the execution backend and has `runtime_mode = STANDALONE | GWF`.

It does not identify an agent app/harness profile.

**Rule:** P5 MUST NOT encode `codex` or `chatgpt` as a fake runtime backend and MUST NOT reinterpret `RuntimeCapabilityManifest` as an app capability manifest.

**Required prerequisite:** define a canonical **AgentCapabilityManifest** (or an exactly equivalent canonical app-profile capability object) without changing RuntimeCapabilityManifest semantics.

### P5-F02 — canonical AgentBinding identity is missing

PRD-09 requires a normalized AgentBinding that distinguishes:

- app/provider/model/harness/transport identities;
- capabilities;
- execution constraints;
- authority scope;
- `binding_mode: dynamic | frozen`;
- prospective equivalence policy;
- resolved attempt identity.

Current `ExecutionAttemptEnvelope` copies executor identity fields but has no exact canonical `AgentBinding` reference, no binding mode, and no prospective equivalence-policy reference.

The GWF Agent Interoperability document defines AgentBinding only conceptually and explicitly defers implementation.

**Forbidden workaround:** hide binding semantics inside `config_hash`, runtime metadata, a GWF run ID, or free-form evidence.

**Required prerequisite:** before P5 runtime adapters, introduce a bounded P1-compatible schema patch that:

1. defines canonical `AgentCapabilityManifest`;
2. defines canonical `AgentBinding`;
3. adds an exact `agent_binding_ref` (or semantically equivalent exact canonical reference) to `ExecutionAttemptEnvelope`;
4. requires the copied app/provider/model/harness/transport fields in an attempt/result to be consistent with the resolved binding;
5. freezes binding mode and equivalence policy prospectively;
6. preserves all existing P1–P4 semantics and exact regression behavior.

This prerequisite is designated **P1.4 — Agent Profile / Binding Identity**.

P1.4 is a schema prerequisite only. It is not a Codex or ChatGPT runtime adapter.

---

## 7. Frozen AgentBinding invariants

P1.4/P5 implementation must preserve these invariants:

1. capability discovery precedes binding;
2. binding is resolved before dispatch;
3. resolved binding is immutable within one ExecutionAttempt;
4. material substitution creates a new attempt identity;
5. `DYNAMIC` permits compatible resolution only for a future attempt;
6. `FROZEN` fixes policy-declared material dimensions until governed amendment;
7. equivalence criteria are frozen before observing execution outcome;
8. required capability absence fails closed;
9. authority ceiling may be narrower than app capability;
10. delegated authority never exceeds parent authority;
11. executor success cannot assign Adjudication/Claim PASS;
12. secrets are never canonical payload content.

---

## 8. Prospective independence contract

P5 profile qualification does **not** treat cross-profile agreement as independent scientific confirmation.

For every ProofObligation:

- required independence dimensions come only from its already-frozen `IndependencePolicy`;
- P5 verifies those dimensions before dispatch;
- a different `agent_app`, provider, or model alone never proves independence;
- if required independence cannot be demonstrated prospectively, binding fails closed;
- post-outcome relabeling of dimensions is forbidden.

The P5 functional qualification fixture itself tests adapter attribution and fail-closed behavior; it does not claim scientific independent replication.

---

## 9. Authority and secret boundary

Each profile must distinguish:

- descriptive capability;
- execution constraint;
- authority granted for this attempt.

A capable app may still be inadmissible because of authority, privacy, locality, or proof-policy constraints.

Required rules:

- no self-elevation;
- no mutation of frozen Goal/Claim/Proof semantics;
- no terminal verdict rewrite;
- no hidden expansion of write scope;
- no bypass around GWF authority in default GWF mode;
- provider/app credentials resolved only at the authorized execution boundary;
- no raw secret in AgentCapabilityManifest, AgentBinding, attempt/result, logs, evidence, package, workflow artifact, or static docs;
- provider-native reasoning/hidden chain-of-thought is not required evidence.

---

## 10. Fail-closed matrix

| Condition | Required behavior |
| --- | --- |
| required capability not demonstrated | `UNSUPPORTED_CAPABILITY` / no dispatch |
| actual harness identity differs materially from frozen binding | reject/substitute only by new attempt or governed amendment |
| provider/model identity unavailable but policy marks it material | no dispatch |
| authority scope exceeds granted ceiling | authority denial / no dispatch |
| independence requirement unresolved | no dispatch |
| required credential reference unavailable | executor unavailable; no silent alternate credential |
| external session cannot be attributed where attribution is required | profile unqualified for that operation |
| adapter returns executor success without valid evidence | attempt may complete technically; no scientific PASS implication |
| cancellation/interruption uncertainty | fail closed according to PRD-07/P4 recovery semantics |
| another profile can perform the task | never a silent fallback for a frozen binding |

---

## 11. Frozen P5 qualification fixture — P5-FX-001

### Goal

Exercise one bounded technical proof through each **available and qualified** app profile without hard-coding a final answer into tests.

### Input generation

Fixture ID: `P5-FX-001`.

The qualification harness generates `input.json` deterministically from:

```text
generator_version = p5-fx-001-v1
seed = g2e-p5-agent-profile-v1
count = 32
```

Values are derived by repeated SHA-256 expansion of the seed and converted deterministically to signed integers. The generated canonical `input.json` hash becomes part of the frozen ProofObligation/attempt evidence.

No expected `result.json` literal is stored in the adapter tests.

### Task envelope

The app receives the frozen workspace and must produce exactly one candidate output `result.json` containing:

- `count`;
- `sum`;
- `sorted_unique_values`;
- `input_sha256`.

Allowed mutation scope is limited to the designated output path.

No network access is required by the fixture. No secret is required.

### Independent verifier

The verifier reads the generated input and candidate output, recomputes every required field, checks output-path scope, and emits a structured verifier report.

The verifier computes expected values from the input at verification time; it does not compare against a hard-coded candidate output.

### Required execution evidence

For each profile qualification:

- exact ProofObligation ref;
- exact AgentCapabilityManifest ref;
- exact AgentBinding ref;
- ExecutionAttempt ref;
- app/provider/model/harness/transport identities as applicable;
- external session/thread/trace identity when supported/required;
- input hash;
- output artifact hash;
- verifier report hash;
- provider-neutral ExecutionResult;
- candidate EvidenceRecord linked to the attempt;
- redaction record;
- authority decision.

A technically completed fixture still requires normal EvidenceAdmission/Adjudication to produce any proof verdict.

---

## 12. P5 pre-implementation gate matrix

| Gate | Requirement | Candidate state |
| --- | --- | --- |
| P5-Q0 | exact PRD-07 dependency evidence | RESOLVED |
| P5-Q1 | Codex discovery contract frozen independently | FROZEN |
| P5-Q2 | ChatGPT discovery contract frozen independently | FROZEN |
| P5-Q3 | separate manifest semantics frozen | FROZEN; canonical schema prerequisite P1.4 required |
| P5-Q4 | AgentBinding semantics frozen | FROZEN; canonical schema prerequisite P1.4 required |
| P5-Q5 | authority/security boundary frozen | FROZEN |
| P5-Q6 | prospective independence behavior frozen | FROZEN |
| P5-Q7 | fail-closed matrix frozen | FROZEN |
| P5-Q8 | outcome-blind technical proof fixture frozen | FROZEN |
| P5-Q9 | zero-implementation QA | PENDING exact-SHA workflow |

---

## 13. Adjudication rules for this qualification

The zero-implementation QA may return:

### `SPEC_PASS_RUNTIME_BLOCKED`

Use when all P5-Q0..Q9 specification gates pass but one or more explicit prerequisites remain before runtime adapter code.

For the current candidate, P5-F01/P5-F02 intentionally require P1.4 before any Codex/ChatGPT runtime implementation.

### `SPEC_FAIL`

Use when the documents/tests are inconsistent, dependencies are unresolved, scope leaks into runtime implementation, or a required contract remains ambiguous.

### `INVALID`

Use when the workflow did not exercise the exact committed candidate or evidence identity cannot be established.

No outcome may be upgraded because P5 implementation is desirable.

---

## 14. Authorization boundary after zero-implementation QA

If exact-SHA zero-implementation QA passes this candidate:

```text
P5 pre-implementation specification
        PASS
         ↓
P1.4 Agent Profile / Binding Identity
schema-only prerequisite
         ↓
P1/P2/P3/P4 regressions
         ↓
P1.4 qualification PASS ?
         ↓
only then
P5A Codex profile implementation
         ↓
exact harness discovery + profile qualification
         ↓
P5B ChatGPT profile implementation
         ↓
exact harness discovery + profile qualification
         ↓
cross-profile semantic parity / P5 exit gate
```

Codex-first is a sequencing choice for the first harness implementation, consistent with the GWF planning preference. It is not a quality ranking and does not allow Codex evidence to qualify ChatGPT.

P5B must remain independently discoverable/qualifiable.

---

## 15. Zero-implementation scope

This qualification may add only:

- this specification;
- static/semantic qualification tests;
- a qualification workflow;
- evidence/result documents after the workflow;
- append-only lineage after adjudication.

It MUST NOT add or modify:

- Codex runtime adapter code;
- ChatGPT runtime adapter code;
- GWF harness/MCP/ARC runtime code;
- core schema implementation (P1.4 is a subsequent separately qualified step);
- P4L/GAC/Reference Acquisition runtime code.

Until P1.4 passes, **P5 runtime implementation remains NOT AUTHORIZED**.
