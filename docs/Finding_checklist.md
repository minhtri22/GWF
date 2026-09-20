# GWF — Finding Checklist: Reference Acquisition + Agent Interoperability Re-audit

## 1. Audit scope

Re-audit target branch: `docs/reference-agent-interop-specs`.

Baseline before remediation: documentation commit `a12f271a0fc7faedb918f96028ef36d66025f7e3`.

Reviewed documents:

- `docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md`
- `docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md`
- `docs/FUTURE_NODE_AGENT_ORCHESTRATION_PARKING_LOT.md`
- `docs/DOCUMENT_QA_REFERENCE_AGENT_INTEROP.md`

Audit dimensions: ambiguity, undefined semantics, cross-document conflict, misleading terminology, governance gaps, research temporal integrity, execution provenance, authority/security boundaries, and future-implementation interpretability.

## 2. Findings and remediation

### F-01 — HIGH — RESOLVED

- **Initial finding:** Reference Acquisition required exact queries but defined no executed-query/retrieval artifact.
- **Remediation:** Added append-only `reference_retrieval_log` with executed query, provider, timing, pagination, candidates, and limitations.
- **Final status:** `RESOLVED`

### F-02 — HIGH — RESOLVED

- **Initial finding:** Two temporal modes left the post-lock/pre-outcome interval undefined.
- **Remediation:** Replaced with `PRE_LOCK`, `LOCKED_PRE_OUTCOME`, and `POST_OUTCOME`, with amendment/freshness rules.
- **Final status:** `RESOLVED`

### F-03 — HIGH — RESOLVED

- **Initial finding:** Paper↔code relation direction conflicted (`IMPLEMENTS` vs inverse `IMPLEMENTED_BY`).
- **Remediation:** Defined subject→object relation direction and rewrote examples to `repo --IMPLEMENTS/REPRODUCES--> paper`.
- **Final status:** `RESOLVED`

### F-04 — HIGH — RESOLVED

- **Initial finding:** Coverage gate treated required-source unavailability too similarly to non-applicability.
- **Remediation:** Added REQUIRED/OPTIONAL source classes and made required-source unavailability blocking unless governed plan amendment occurs.
- **Final status:** `RESOLVED`

### F-05 — MEDIUM — RESOLVED

- **Initial finding:** Query-plan revisions/amendments were not attributable to retrieval events.
- **Remediation:** Added `plan_revision`, `amendment_policy`, and log linkage by plan revision.
- **Final status:** `RESOLVED`

### F-06 — MEDIUM — RESOLVED

- **Initial finding:** Canonical source identity and exact inspected version/snapshot were conflated.
- **Remediation:** Separated canonical identity from `identity_fingerprint` and documented optional content digest semantics.
- **Final status:** `RESOLVED`

### F-07 — MEDIUM — RESOLVED

- **Initial finding:** Singular `query_ref` could lose multi-query/provider observations for the same reference.
- **Remediation:** Registry now links multiple retrieval observations; observations remain separate in the retrieval log.
- **Final status:** `RESOLVED`

### F-08 — LOW — RESOLVED

- **Initial finding:** `POST_OUTCOME` heading had malformed Markdown/backtick syntax.
- **Remediation:** Corrected while replacing the temporal model.
- **Final status:** `RESOLVED`

### F-09 — HIGH — RESOLVED

- **Initial finding:** Agent Pool resource class and ARC transport could be read as the same abstraction.
- **Remediation:** Separated resource/orchestration class from transport and stated ARC does not provide/free-classify models.
- **Final status:** `RESOLVED`

### F-10 — HIGH — RESOLVED

- **Initial finding:** Dynamic binding did not define when agent identity becomes immutable.
- **Remediation:** Defined resolution before each attempt; resolved binding is immutable within an attempt and reassignment creates a new attempt.
- **Final status:** `RESOLVED`

### F-11 — HIGH — RESOLVED

- **Initial finding:** Frozen binding did not define which identity dimensions are frozen or how equivalence is authorized.
- **Remediation:** Added material identity dimensions and prospective equivalence-policy semantics.
- **Final status:** `RESOLVED`

### F-12 — HIGH — RESOLVED

- **Initial finding:** `AgentExecutionEnvelope.status` was undefined and could be confused with GWF PASS/FAIL.
- **Remediation:** Added conceptual executor lifecycle states and specified executor `SUCCEEDED` ≠ GWF gate PASS/completion.
- **Final status:** `RESOLVED`

### F-13 — MEDIUM — RESOLVED

- **Initial finding:** `local_only_execution` was modeled as a capability although it is a policy constraint.
- **Remediation:** Moved locality/privacy/network/data-residency concepts to execution constraints.
- **Final status:** `RESOLVED`

### F-14 — HIGH — RESOLVED

- **Initial finding:** Delegation observability existed but authority inheritance/no-escalation was unspecified.
- **Remediation:** Added child-authority ≤ parent-authority invariant.
- **Final status:** `RESOLVED`

### F-15 — HIGH — RESOLVED

- **Initial finding:** MCP mutation boundary prohibited dangerous primitives but did not require parity with native governed commands.
- **Remediation:** Required normal GWF authority, idempotency, audit, and verification for mutation-capable MCP operations.
- **Final status:** `RESOLVED`

### F-16 — HIGH — RESOLVED

- **Initial finding:** Secret boundary did not explicitly prohibit credentials from execution envelopes/logs/evidence.
- **Remediation:** Added no-secret-persistence rule and execution-boundary resolution/redaction requirement.
- **Final status:** `RESOLVED`

### F-17 — MEDIUM — RESOLVED

- **Initial finding:** Parking-lot wording could imply ARC=fallback and used vague `premium/stronger/independent` labels.
- **Remediation:** Replaced with resource/transport separation, explicit independence contract, and reassignment/substitution terminology.
- **Final status:** `RESOLVED`

### F-18 — MEDIUM — RESOLVED

- **Initial finding:** QA independence could be inferred merely from using a different agent/resource class.
- **Remediation:** Added Decision F: independence is a prospective governed constraint demonstrated by binding/lineage.
- **Final status:** `RESOLVED`

### F-19 — LOW — RESOLVED

- **Initial finding:** Typo `lormatting` reduced specification clarity.
- **Remediation:** Corrected to `formatting`.
- **Final status:** `RESOLVED`

### F-20 — MEDIUM — RESOLVED

- **Initial finding:** Prior QA report becomes stale after semantic remediation.
- **Remediation:** The QA report is regenerated after final checklist QA with the remediated document identities.
- **Final status:** `RESOLVED`

### F-21 — HIGH — RESOLVED

- **Initial finding:** `provider_or_protocol` in `AgentBinding` conflated provider identity with transport identity.
- **Remediation:** Split the concept into `provider_ref` and `transport_ref`, and stated resource class/provider/transport as separate dimensions.
- **Final status:** `RESOLVED`

### F-22 — MEDIUM — RESOLVED

- **Initial finding:** `reference_query_plan` called itself prospective without defining prospectiveness per acquisition session.
- **Remediation:** Defined a query plan as prospective before each acquisition session, with mode and active plan revision bound to that session.
- **Final status:** `RESOLVED`

### F-23 — HIGH — RESOLVED

- **Initial finding:** `novelty_collision_found` defined pre-lock handling but left locked-pre-outcome and post-outcome handling ambiguous.
- **Remediation:** Defined mode-specific handling: amendment/new lock or stop before outcomes; limitation/follow-up/new lineage after outcomes; never retroactive silent rewrite.
- **Final status:** `RESOLVED`

## 3. Final checklist

- [x] Exact executed research queries have a governed provenance artifact.
- [x] Reference plan revision/amendment lineage is explicit.
- [x] Canonical identity and inspected snapshot identity are distinguishable.
- [x] Paper↔code relation direction is unambiguous.
- [x] Required-source unavailability cannot silently satisfy coverage.
- [x] Temporal acquisition covers pre-lock, locked/pre-outcome, and post-outcome states.
- [x] Query-plan prospectiveness is scoped per acquisition session.
- [x] Novelty-collision handling is explicit in every temporal mode.
- [x] Agent Pool resource class is distinct from ARC transport.
- [x] Provider identity and transport identity are represented separately.
- [x] Harness and Agent Pool execution classes remain distinct.
- [x] Dynamic binding is immutable within an attempt.
- [x] Frozen binding defines material identity/equivalence semantics.
- [x] Executor status cannot be mistaken for GWF gate PASS.
- [x] Capabilities and execution constraints are separate.
- [x] Delegation cannot escalate authority.
- [x] QA independence is a governed contract, not inferred from resource class.
- [x] MCP mutation follows native GWF authority/idempotency/audit/verification.
- [x] Provider secrets cannot persist in bindings, envelopes, logs, evidence, or static UI.
- [x] Parking-lot wording no longer frames Agent Pool as fallback-only.
- [x] Known wording/Markdown defects found by this audit are removed.
- [x] Implementation remains unauthorized.

## 4. Open findings

**OPEN = 0**

No unresolved finding from this audit remains. A future implementation review may discover implementation-specific issues; that does not reopen this documentation checklist unless the specification itself must change.
