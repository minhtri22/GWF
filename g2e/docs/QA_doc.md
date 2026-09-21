# G2E Documentation Semantic QA — Finding Checklist

## 1. Scope

Audit branch: `feature/g2e-framework`.

Audit baseline:

`64e0fc9280bdaf4a078bc063a6f2c855581f47ce`

This is a **semantic/logic handoff audit**, deeper than the earlier structural P0 document QA. It reviews ambiguity, conflicting definitions, insufficiently frozen contracts, missing state transitions, dependency inconsistencies, evidence/adjudication logic, authority boundaries, runtime portability, and future implementation interpretability.

Reviewed:

- `g2e/README.md`
- `g2e/LINEAGE.md`
- `g2e/docs/ARCHITECTURE_DECISIONS.md`
- `g2e/docs/P0_DOCUMENT_QA.md`
- `g2e/docs/PHASE_PLAN.md`
- `g2e/docs/PRD_INDEX.md`
- `g2e/docs/PRD_01_*.md` through `PRD_14_*.md`

Finding statuses in this initial audit are `OPEN`. A finding may only be marked `RESOLVED` after the remediation is committed and the final QA can point to the exact governing section/file.

---

## 2. Findings

### F-01 — HIGH — OPEN — Claim state conflates workflow lifecycle with epistemic verdict

**Problem:** PRD-02 puts `UNKNOWN/BLOCKED/READY/RUNNING/PASS/FAIL/INVALID/UNRESOLVED/SUPERSEDED` in one state set. This mixes orchestration state with proof outcome. `INVALID` is fundamentally an attempt/adjudication result, while `BLOCKED/READY/RUNNING` are lifecycle states.

**Risk:** retry logic, Next-Step selection, and claim closure can disagree about whether an invalid execution invalidates the claim itself.

**Affected:** PRD-02, PRD-05, PRD-06, PRD-07.

**Required remediation:** define separate normative state namespaces for Claim lifecycle/resolution, Proof lifecycle, ExecutionAttempt state, Adjudication verdict, and Goal verdict.

- [ ] RESOLVED

### F-02 — HIGH — OPEN — No normative rule for multiple proofs/evidence resolving one claim

**Problem:** documents allow multiple proof obligations and conflicting evidence but do not define how a claim becomes PASS/FAIL/UNRESOLVED when more than one proof exists.

**Risk:** an agent/runtime could cherry-pick one favorable proof or last-write-wins evidence.

**Affected:** PRD-02, PRD-04, PRD-05, PRD-12.

**Required remediation:** introduce frozen `ClaimResolutionPolicy` with required proof sets/aggregation semantics; prohibit implicit last-write-wins.

- [ ] RESOLVED

### F-03 — HIGH — OPEN — Goal closure expression is not formalized

**Problem:** Goal Contract says “acceptable terminal outcomes”; Claim Graph says claims map to goal; Result Package says achieved/falsified/unresolved/stopped. No machine-readable expression defines which claim combinations establish achievement or falsification.

**Risk:** final goal verdict can become narrative/agent judgment.

**Affected:** README, PRD-01, PRD-02, PRD-12.

**Required remediation:** define `GoalSatisfactionExpression`/terminal claim mapping and normative Goal verdict semantics.

- [ ] RESOLVED

### F-04 — HIGH — OPEN — Proof Obligation, ExecutionAttempt, and retry identity are underspecified

**Problem:** “one-shot” is tied to a vague “proof-obligation execution identity”. INVALID repair may preserve the obligation or create a new one, but closure rules are not exact.

**Risk:** retry-until-PASS can hide behind new attempts, or technical INVALID can incorrectly close a scientific claim.

**Affected:** PRD-03, PRD-05, PRD-07.

**Required remediation:** define immutable ProofObligation identity, unique ExecutionAttempt identity, adjudication-per-attempt, retry budget, and closure rules for PASS/FAIL/INVALID/UNRESOLVED.

- [ ] RESOLVED

### F-05 — HIGH — OPEN — Dependency graph conflicts between PRD Index and adapter PRDs

**Problem:** PRD Index says PRD-08 hard-depends only on PRD-07. PRD-08 itself lists PRD-09 and PRD-10 as dependencies, while PRD-09/10 link back to PRD-08 for default integration.

**Risk:** circular implementation ordering and ambiguous handoff authorization.

**Affected:** PRD_INDEX, PRD-08, PRD-09, PRD-10.

**Required remediation:** define dependency classes (HARD / CONDITIONAL / CROSS-CUTTING / INTEGRATION or equivalent) and remove circular hard dependencies.

- [ ] RESOLVED

### F-06 — HIGH — OPEN — Lock and outcome-exposure boundaries are not canonical

**Problem:** documents use “execution authorized”, “proof frozen”, “after evidence exposure”, `PRE_LOCK`, `LOCKED_PRE_OUTCOME`, and “post-outcome” without one event model.

**Risk:** an implementation cannot know when changes become prohibited or when a resource becomes spent.

**Affected:** PRD-01, PRD-03, PRD-04, PRD-05, PRD-13.

**Required remediation:** define canonical events such as Goal freeze, ClaimGraph freeze, Proof freeze/authorization, ProtectedResource reservation/exposure, Outcome exposure, Adjudication.

- [ ] RESOLVED

### F-07 — HIGH — OPEN — Protected/fresh resource state model is incomplete

**Problem:** freshness is described conceptually but resource identity, reservation, exposure transition, and reuse policy are not defined.

**Risk:** a confirmatory seed/dataset could be observed before its exposure is durably recorded and later misclassified as fresh.

**Affected:** PRD-03, PRD-04, PRD-06, PRD-14.

**Required remediation:** define resource identity + freshness state and require reservation/exposure bookkeeping before or atomically with protected access; exposed resources never become fresh again.

- [ ] RESOLVED

### F-08 — HIGH — OPEN — Amendment/new-lineage rules are discretionary

**Problem:** PRD-01 says semantic amendment after exposure “may require” new lineage; new claims can be added after evidence without exact invalidation rules.

**Risk:** observed outcomes can influence rewritten goals/claims while preserving old authority.

**Affected:** PRD-01, PRD-02, PRD-03, README.

**Required remediation:** classify editorial vs normative amendments; require new revision/lineage for post-outcome changes to propositions, satisfaction mapping, thresholds, baselines, protected cohorts, or other decision semantics.

- [ ] RESOLVED

### F-09 — MEDIUM — OPEN — Claim dependency cycles have an undefined exception

**Problem:** PRD-02 permits “explicitly allowed fixed-point structures” but does not define them.

**Risk:** implementation-specific cycle handling and non-terminating Next-Step logic.

**Affected:** PRD-02.

**Required remediation:** v0.x hard claim dependencies are a DAG. Defer fixed-point/cyclic dependency semantics to a future explicit extension.

- [ ] RESOLVED

### F-10 — HIGH — OPEN — Next-Step ranking is not deterministic/governed enough

**Problem:** preferences such as “high information gain”, “lower complexity/cost”, “smaller/faster” have no normalized values or tie-break rules.

**Risk:** two agents can choose materially different next studies under identical state while both claim policy compliance.

**Affected:** PRD-06.

**Required remediation:** separate deterministic admissibility from preference ranking; define a frozen `SelectionPolicy`, normalized ranking fields, deterministic tie-breaker, and authority for choosing among equally admissible candidates.

- [ ] RESOLVED

### F-11 — MEDIUM — OPEN — “Smallest/minimal proof” is undefined

**Problem:** Proof Planner uses “smallest admissible” and “minimal” without a measurable dimension.

**Risk:** minimality becomes untestable agent prose.

**Affected:** PRD-03, PRD-06.

**Required remediation:** make validity independent from minimality; require explicit resource/complexity/freshness estimates and treat minimality as a selection policy over admissible proofs.

- [ ] RESOLVED

### F-12 — HIGH — OPEN — Evidence trust/admission semantics are undefined

**Problem:** Evidence nodes contain a “trust class”, but classes and admission criteria are not specified. Reference Acquisition can classify external references as direct empirical evidence without a normative admission path.

**Risk:** low-integrity or merely contextual references can accidentally satisfy claims.

**Affected:** PRD-04, PRD-05, PRD-13.

**Required remediation:** define `EvidenceAdmissionPolicy`, integrity/identity requirements, source classes, independence/freshness constraints, and explicit admitted/rejected status.

- [ ] RESOLVED

### F-13 — MEDIUM — OPEN — Evidence relation direction and binding identity are unspecified

**Problem:** relations such as `SUPPORTS`, `VALIDATES`, `DERIVED_FROM`, `REPRODUCES` have names but no subject→object direction or exact-vs-floating binding rule.

**Risk:** incompatible graph implementations and ambiguous provenance traversal.

**Affected:** PRD-04.

**Required remediation:** define relation direction and require immutable target identity for evidentiary relations.

- [ ] RESOLVED

### F-14 — HIGH — OPEN — Executor status can still be confused with proof validity

**Problem:** Execution lifecycle contains `SUCCEEDED | FAILED | INVALIDATED`; `FAILED`/ `INVALIDATED` are not clearly executor-only states and overlap with proof FAIL/INVALID terminology.

**Risk:** backend status can leak into adjudication semantics.

**Affected:** PRD-07, PRD-05.

**Required remediation:** use explicit executor states (e.g. COMPLETED/EXECUTOR_FAILED/CANCELLED/TIMED_OUT/PREEMPTED) and keep proof verdict exclusively in Adjudication.

- [ ] RESOLVED

### F-15 — HIGH — OPEN — Authority, independence, and override semantics are insufficiently locked

**Problem:** roles exist but machine adjudicator vs human reviewer/approver are not clearly separated. Independence is discussed for agents but no `IndependencePolicy` is bound to a proof. Human override is mentioned but not defined.

**Risk:** same agent can design, execute, review and effectively override a result where independent review was expected.

**Affected:** PRD-05, PRD-09, PRD-14.

**Required remediation:** define authority actions, optional/required separation-of-duty policy, prospective independence policy, and `GovernanceDisposition` that never rewrites machine adjudication.

- [ ] RESOLVED

### F-16 — MEDIUM — OPEN — G2E semantic authority vs GWF system-of-record authority is ambiguous

**Problem:** README calls GWF the default authoritative runtime while G2E owns adjudication/goal closure; facts are said to belong to both G2E state and GWF state.

**Risk:** two competing sources of truth.

**Affected:** README, PRD-08, PRD-11.

**Required remediation:** define semantic authority separately from persistence/system-of-record authority. In GWF mode, GWF persists canonical G2E records but may not reinterpret G2E semantics.

- [ ] RESOLVED

### F-17 — MEDIUM — OPEN — Standalone→GWF migration identity is not frozen

**Problem:** PRD-11 requires semantic parity but does not say whether G2E object IDs/hashes remain unchanged or are remapped during import.

**Risk:** migrated project can appear to have a new scientific/proof identity.

**Affected:** PRD-08, PRD-11.

**Required remediation:** canonical G2E identities remain unchanged; runtime-specific IDs are separate references; compatibility failures fail closed.

- [ ] RESOLVED

### F-18 — MEDIUM — OPEN — Codex and ChatGPT app surfaces are treated as one adapter target

**Problem:** docs use “Codex / ChatGPT adapter” as though harness/capabilities are interchangeable.

**Risk:** implementation may assume parity between distinct app surfaces.

**Affected:** README, PRD-09, PHASE_PLAN.

**Required remediation:** keep same priority wave but use separate `agent_app` profiles/bindings and capability discovery; no assumed behavioral parity.

- [ ] RESOLVED

### F-19 — HIGH — OPEN — P1/P2 implementation plan omits required core policy schemas/engines

**Problem:** P1 lists primary objects but omits goal-satisfaction policy, claim-resolution policy, evidence-admission policy, retry/amendment policy, protected-resource policy, authority/independence policy. P2 omits claim resolver and final goal closure evaluator.

**Risk:** implementation begins with insufficient schema coverage and later requires incompatible state migrations.

**Affected:** PHASE_PLAN, PRD_INDEX.

**Required remediation:** expand P1/P2 exit scope before implementation authorization.

- [ ] RESOLVED

### F-20 — MEDIUM — OPEN — Previous P0 QA can be mistaken for current semantic handoff QA

**Problem:** `P0_DOCUMENT_QA.md` says PASS, but it only checked structural/coverage properties and predates this semantic audit.

**Risk:** downstream agent may cite the older PASS and ignore unresolved semantic findings.

**Affected:** P0_DOCUMENT_QA, PRD_INDEX/README navigation.

**Required remediation:** mark it historical structural QA and designate `QA_doc.md` as current semantic handoff QA.

- [ ] RESOLVED

### F-21 — MEDIUM — OPEN — Goal terminal-state vocabulary is inconsistent

**Problem:** README includes “invalidated”; PRD-12 uses achieved/falsified/unresolved/stopped; INVALID is also a proof verdict.

**Risk:** technical invalid execution may incorrectly become terminal goal INVALID.

**Affected:** README, PRD-01, PRD-05, PRD-12.

**Required remediation:** define one normative GoalVerdict vocabulary and explicitly state that proof-attempt INVALID does not by itself invalidate/falsify the goal.

- [ ] RESOLVED

### F-22 — MEDIUM — OPEN — Result package integrity/sealing is underspecified

**Problem:** PRD-12 lists result files but no non-circular manifest/hash/seal rule or missing-reference verification contract.

**Risk:** final result package can be modified without a canonical integrity failure.

**Affected:** PRD-12.

**Required remediation:** define package manifest, content hashes, external/parent seal semantics, and verification behavior without self-referential hashing.

- [ ] RESOLVED

---

## 3. Remediation checklist

- [ ] Define one normative Core Semantics document referenced by every relevant PRD.
- [ ] Separate all lifecycle/verdict namespaces.
- [ ] Define Goal satisfaction and Claim resolution policies.
- [ ] Define ProofObligation vs ExecutionAttempt retry/closure.
- [ ] Normalize dependency classes and remove cycles.
- [ ] Freeze temporal/exposure/freshness semantics.
- [ ] Freeze evidence admission/relation semantics.
- [ ] Freeze selection policy and deterministic tie-break.
- [ ] Freeze authority/independence/override semantics.
- [ ] Freeze system-of-record and standalone migration semantics.
- [ ] Split Codex/ChatGPT app profiles.
- [ ] Expand P1/P2 plan before implementation.
- [ ] Add result-package integrity policy.
- [ ] Re-run cross-document consistency/link/dependency QA.
- [ ] OPEN findings = 0.
- [ ] Final verdict = PASS.

## 4. Current verdict

**SEMANTIC DOCUMENT QA: FAIL / REMEDIATION REQUIRED**

`OPEN = 22`

P1 implementation should remain blocked until this checklist is clean.
