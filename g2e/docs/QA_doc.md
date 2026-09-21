# G2E Documentation Semantic QA — Finding Checklist

## 1. Scope

Audit branch: `feature/g2e-framework`.

Initial audit baseline:

`64e0fc9280bdaf4a078bc063a6f2c855581f47ce`

Findings-only audit commit:

`2fab50299800e9ac437f92aec796b3b104c46cc1`

Remediation commit under final QA:

`ed88ec721342456bbb90006b41e2308bdc043fcd`

This is the authoritative **semantic/logic handoff QA** for the G2E specification. The older `P0_DOCUMENT_QA.md` is retained as historical structural QA only.

Reviewed:

- `g2e/README.md`
- `g2e/docs/CORE_SEMANTICS.md`
- `g2e/docs/REFERENCE_BASELINE.md`
- `g2e/docs/ARCHITECTURE_DECISIONS.md`
- `g2e/docs/PHASE_PLAN.md`
- `g2e/docs/PRD_INDEX.md`
- `g2e/docs/PRD_01_*.md` through `PRD_14_*.md`
- GWF dependency documents pinned by `REFERENCE_BASELINE.md`
- MindForge M2/M3/M4 reference evidence at pinned commit

---

## 2. Findings and resolution proof

### F-01 — HIGH — RESOLVED — Claim state conflated workflow lifecycle with epistemic verdict

**Resolution:** separated normative state namespaces for GoalContract lifecycle, Goal verdict, Claim lifecycle, Claim resolution, ProofObligation lifecycle, ExecutionAttempt state and Adjudication verdict.

**Proof:** `CORE_SEMANTICS.md §§2–3`; PRD-02; PRD-05; PRD-07.

- [x] RESOLVED

### F-02 — HIGH — RESOLVED — No normative multi-proof Claim resolution rule

**Resolution:** introduced frozen `ClaimResolutionPolicy` with v0.x `ALL_REQUIRED` and `ANY_SUFFICIENT`; last-write-wins/cherry-pick resolution prohibited.

**Proof:** `CORE_SEMANTICS.md §4`; PRD-02; PRD-04.

- [x] RESOLVED

### F-03 — HIGH — RESOLVED — Goal closure was not formalized

**Resolution:** GoalContract now freezes stable Goal requirements without premature Claim IDs. Claim compilation creates a separate `GoalClosureContract` bound to exact GoalContract + ClaimGraph revisions and success/falsification expressions.

**Proof:** `CORE_SEMANTICS.md §5`; PRD-01; PRD-02; PRD-12.

- [x] RESOLVED

### F-04 — HIGH — RESOLVED — ProofObligation / ExecutionAttempt / retry identity unclear

**Resolution:** immutable ProofObligation semantic identity and unique attempt identity are separate. Adjudication is one-shot per attempt. PASS/FAIL/UNRESOLVED close the obligation; INVALID can retry only under frozen RetryPolicy and unchanged proof semantics; exhausted INVALID attempts close UNRESOLVED.

**Proof:** `CORE_SEMANTICS.md §3`; PRD-03; PRD-05; PRD-07.

- [x] RESOLVED

### F-05 — HIGH — RESOLVED — Dependency graph conflict/cycle

**Resolution:** dependency classes are now HARD / CONDITIONAL / CROSS_CUTTING / INTEGRATION / ORDERING. PRD-08 no longer hard-depends on PRD-09/10; producer/evaluator integration no longer creates PRD-04/05↔07 hard cycles.

**Proof:** `CORE_SEMANTICS.md §6`; `PRD_INDEX.md`; PRD-08/09/10.

**QA evidence:** HARD dependency graph cycle check = PASS / DAG.

- [x] RESOLVED

### F-06 — HIGH — RESOLVED — Lock/outcome exposure boundary unclear

**Resolution:** canonical event model added: GOAL_FROZEN → CLAIM_GRAPH/GOAL_CLOSURE_FROZEN → PROOF_FROZEN → PROOF_AUTHORIZED → ATTEMPT_LOCKED → resource reservation → OUTCOME_EXPOSED → adjudication/closure.

**Proof:** `CORE_SEMANTICS.md §7`; PRD-03; PRD-13.

- [x] RESOLVED

### F-07 — HIGH — RESOLVED — Protected/fresh resource state incomplete

**Resolution:** resource freshness state is `FRESH | RESERVED | EXPOSED`; reservation is durable before access; uncertain recovery fails closed to EXPOSED; EXPOSED never becomes FRESH again; reuse policy is explicit.

**Proof:** `CORE_SEMANTICS.md §8`; PRD-07; PRD-14.

- [x] RESOLVED

### F-08 — HIGH — RESOLVED — Amendment/new-lineage rules discretionary

**Resolution:** amendments classified EDITORIAL vs NORMATIVE. Normative post-outcome changes create new affected proof/study lineage; old adjudications remain immutable. Newly discovered prerequisites produce a new ClaimGraph revision and do not rewrite old evidence.

**Proof:** `CORE_SEMANTICS.md §9`; PRD-01; PRD-02; README.

- [x] RESOLVED

### F-09 — MEDIUM — RESOLVED — Undefined fixed-point/cycle exception

**Resolution:** v0.x HARD Claim dependencies are strictly a DAG. Fixed-point/cyclic semantics are explicitly deferred.

**Proof:** `CORE_SEMANTICS.md §5`; PRD-02.

- [x] RESOLVED

### F-10 — HIGH — RESOLVED — Next-Step ranking not deterministic/governed

**Resolution:** two-stage selection introduced: deterministic admissibility then frozen SelectionPolicy ranking. Default ranking fields and lexical `proof_id` tie-break are defined. Authorized non-default choice is recorded but must remain inside admissible set.

**Proof:** `CORE_SEMANTICS.md §11`; PRD-06.

- [x] RESOLVED

### F-11 — MEDIUM — RESOLVED — “Smallest/minimal proof” undefined

**Resolution:** minimality is no longer proof validity. Planner emits normalized resource/freshness/complexity estimates; SelectionPolicy ranks admissible proofs.

**Proof:** PRD-03 “Minimality”; `CORE_SEMANTICS.md §11`.

- [x] RESOLVED

### F-12 — HIGH — RESOLVED — Evidence trust/admission undefined

**Resolution:** Evidence lifecycle and frozen `EvidenceAdmissionPolicy` introduced. Only ADMITTED evidence may reach adjudication; source class, integrity, producer linkage, freshness, independence, derivation and redaction rules are explicit.

**Proof:** `CORE_SEMANTICS.md §10`; PRD-04; PRD-13.

- [x] RESOLVED

### F-13 — MEDIUM — RESOLVED — Evidence relation direction/binding unspecified

**Resolution:** relation direction is explicitly subject→object and all authoritative evidentiary relations bind immutable IDs/hashes; floating “current” targets are prohibited.

**Proof:** `CORE_SEMANTICS.md §10`; PRD-04.

- [x] RESOLVED

### F-14 — HIGH — RESOLVED — Executor status overlapped proof verdict

**Resolution:** executor states changed to `COMPLETED | EXECUTOR_FAILED | CANCELLED | TIMED_OUT | PREEMPTED` (plus pre-run states). PASS/FAIL/INVALID/UNRESOLVED exist only in Adjudication.

**Proof:** `CORE_SEMANTICS.md §2.6–2.7`; PRD-07; PRD-05.

- [x] RESOLVED

### F-15 — HIGH — RESOLVED — Authority/independence/override semantics loose

**Resolution:** core authority actions, IndependencePolicy dimensions, separation-of-duty enforcement and immutable machine verdict are defined. Human action is a separate `GovernanceDisposition`, never a verdict rewrite.

**Proof:** `CORE_SEMANTICS.md §12`; PRD-14; PRD-05; PRD-09.

- [x] RESOLVED

### F-16 — MEDIUM — RESOLVED — G2E semantic authority vs GWF source-of-record ambiguous

**Resolution:** G2E owns semantic definitions; selected runtime owns durable persistence. GWF is default system of record; standalone stores the same canonical objects. Runtime IDs are mappings, not semantic replacements.

**Proof:** `CORE_SEMANTICS.md §13`; README §2/§5; PRD-08; PRD-11.

- [x] RESOLVED

### F-17 — MEDIUM — RESOLVED — Standalone→GWF migration identity not frozen

**Resolution:** canonical G2E IDs/hashes must remain unchanged through migration; runtime-specific IDs are separate; incompatible major schema/capability fails closed.

**Proof:** `CORE_SEMANTICS.md §§1,13`; PRD-08; PRD-11.

- [x] RESOLVED

### F-18 — MEDIUM — RESOLVED — Codex/ChatGPT treated as one app surface

**Resolution:** same priority wave retained but separate `Codex` and `ChatGPT` adapter profiles/capability manifests are mandatory. Qualification of one does not imply parity with the other.

**Proof:** README §6; PRD-09; PHASE_PLAN P5.

- [x] RESOLVED

### F-19 — HIGH — RESOLVED — P1/P2 omitted required policy schemas/engines

**Resolution:** P1 now includes GoalClosureContract, ClaimResolutionPolicy, EvidenceAdmissionPolicy, ProtectedResource, Retry/Amendment, Selection, Authority/Independence and attempt-envelope schemas. P2 includes Claim resolver, Goal evaluator, evidence admission, freshness engine and deterministic selector.

**Proof:** `PHASE_PLAN.md P1–P2`; PRD_INDEX implementation note.

- [x] RESOLVED

### F-20 — MEDIUM — RESOLVED — Older P0 QA could be mistaken for current handoff QA

**Resolution:** `P0_DOCUMENT_QA.md` is explicitly marked historical structural QA. This `QA_doc.md` is designated current semantic handoff QA.

**Proof:** `P0_DOCUMENT_QA.md`; README document navigation.

- [x] RESOLVED

### F-21 — MEDIUM — RESOLVED — Goal terminal vocabulary inconsistent

**Resolution:** normative Goal verdicts are `IN_PROGRESS | ACHIEVED | FALSIFIED | UNRESOLVED | STOPPED`. INVALID remains attempt-level only and never directly invalidates/falsifies the Goal.

**Proof:** `CORE_SEMANTICS.md §2.2/§5`; README; PRD-12.

- [x] RESOLVED

### F-22 — MEDIUM — RESOLVED — Result-package integrity/sealing underspecified

**Resolution:** non-circular `PACKAGE_MANIFEST.json` + `PACKAGE_SEAL.json` contract added with file hash/size checks, authoritative-file classification and external-reference verification policy.

**Proof:** `CORE_SEMANTICS.md §14`; PRD-12.

- [x] RESOLVED

---

## 3. Final handoff checklist

- [x] Normative Core Semantics exists and is referenced by every component PRD.
- [x] Goal, Claim, Proof, Attempt and Adjudication state namespaces are separated.
- [x] GoalClosureContract and ClaimResolutionPolicy are formalized.
- [x] Proof retry/closure semantics are explicit.
- [x] Dependency classes are explicit and HARD graph is acyclic.
- [x] Temporal lock/outcome-exposure events are canonical.
- [x] Protected-resource freshness is monotonic/fail-closed.
- [x] Evidence admission and relation direction/binding are explicit.
- [x] Selection policy has deterministic admissibility/ranking/tie-break.
- [x] Authority, independence, separation-of-duty and GovernanceDisposition are explicit.
- [x] G2E semantic authority vs runtime system-of-record authority is explicit.
- [x] Standalone↔GWF migration preserves canonical identity.
- [x] Codex and ChatGPT are separate first-priority profiles.
- [x] P1/P2 plan covers required policy schemas and deterministic engines.
- [x] Result Package has non-circular integrity/seal semantics.
- [x] Older structural QA is clearly historical.
- [x] Reference baseline pins GWF base commit and MindForge evidence commit.
- [x] All required G2E/GWF dependency paths exist at remediation commit.
- [x] MindForge M2/M3/M4 reference files resolve at pinned commit.
- [x] Remediation commit changes only `g2e/` paths.
- [x] OPEN findings = 0.

## 4. Final QA evidence

Remediation commit:

`ed88ec721342456bbb90006b41e2308bdc043fcd`

Checks:

- 14/14 component PRDs contain Purpose, Dependencies, References, Acceptance Criteria and Core Semantics linkage.
- HARD dependency graph: **DAG / PASS**.
- Required local dependency/reference paths: **all present**.
- MindForge M2/M3/M4 pinned reference evidence: **all present**.
- Remediation scope outside `g2e/`: **0 files**.
- Legacy contradiction scans:
  - combined Claim lifecycle/verdict enum: absent;
  - fixed-point HARD-dependency exception: absent;
  - executor `SUCCEEDED` proof-like state: absent;
  - Goal INVALID terminal state: absent;
  - Codex/ChatGPT single assumed profile: absent;
  - GitHub “independent execution” assumption: absent;
  - PRD-08 hard cycle to PRD-09/10: absent.

## 5. Verdict

**G2E P0.1 SEMANTIC DOCUMENT QA: PASS (historical scope)**

`OPEN = 0` for P0.1.

P0.2 subsequently added Evidence Reuse, Library and Synthesis/Convergence semantics. [P0.2 Library/Synthesis QA](P0_2_LIBRARY_SYNTHESIS_QA.md) is now **PASS / OPEN=0**.

**Current handoff status:** P1 — Core Schemas is authorized under the combined P0 + P0.1 + P0.2 specification. No implementation has been executed.
