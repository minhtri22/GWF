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

## 5. Documentation Integrity & Governance specification re-audit

### F-24 — HIGH — RESOLVED

- **Initial finding:** `DocumentRecord` had singular authority scope/key fields even though one normative document can legitimately own multiple non-conflicting authority claims.
- **Remediation:** Replaced singular fields with `authority_claims` and defined per-claim scope/key/mode semantics.
- **Final status:** `RESOLVED`

### F-25 — HIGH — RESOLVED

- **Initial finding:** `INTEGRATE` could be misread as a mandatory core dependency or implementation authorization.
- **Remediation:** Defined BUILD/INTEGRATE/OPTIONAL ADAPTER semantics and required core state to remain reconstructable offline.
- **Final status:** `RESOLVED`

### F-26 — MEDIUM — RESOLVED

- **Initial finding:** Lifecycle diagram implied supersession might require passing through deprecation.
- **Remediation:** Defined explicit transitions: ACTIVE may become DEPRECATED or directly SUPERSEDED; both may later archive.
- **Final status:** `RESOLVED`

### F-27 — HIGH — RESOLVED

- **Initial finding:** `WAIVED` finding status did not state whether it can satisfy a clean gate.
- **Remediation:** Defined waiver as distinct from verified resolution and allowed PASS only when gate policy explicitly permits it; non-waivable classes remain blocking.
- **Final status:** `RESOLVED`

### F-28 — MEDIUM — RESOLVED

- **Initial finding:** Change-set classification allowed multiple documents but did not define aggregate governance severity.
- **Remediation:** Added per-document classes plus an effective change class equal to the strongest governance class triggered.
- **Final status:** `RESOLVED`

### F-29 — HIGH — RESOLVED

- **Initial finding:** The phrase “stricter boundary governs” left precedence between Documentation Governance and research study-lock authority too implicit.
- **Remediation:** Made domain research authority non-relaxable by documentation governance and required amendment/new-lineage routing where applicable.
- **Final status:** `RESOLVED`

### F-30 — HIGH — RESOLVED

- **Initial finding:** Security-leak findings required redaction but did not define what evidence may safely persist.
- **Remediation:** Limited persisted evidence to non-reversible fingerprint/classification plus redacted remediation context.
- **Final status:** `RESOLVED`

### F-31 — HIGH — RESOLVED

- **Initial finding:** The spec did not explicitly prevent readers from assuming existing Markdown files are already runtime-governed after document approval.
- **Remediation:** Added a separate adoption/migration boundary and prohibited silent retroactive authority assignment.
- **Final status:** `RESOLVED`

### F-32 — MEDIUM — RESOLVED

- **Initial finding:** External-tool capability statements could become stale and be mistaken for permanent vendor guarantees.
- **Remediation:** Required implementation-time revalidation and version/interface/security pinning for every external adapter.
- **Final status:** `RESOLVED`

### F-33 — MEDIUM — RESOLVED

- **Initial finding:** `MUST_ALIGN_WITH` said changes on either side require review but relation direction/invalidation behavior was not explicit.
- **Remediation:** Defined stored direction for identity with default bidirectional-review invalidation semantics.
- **Final status:** `RESOLVED`

### F-34 — MEDIUM — RESOLVED

- **Initial finding:** The BUILD/INTEGRATE/OPTIONAL ADAPTER matrix named external tools without preserving the capability evidence snapshot that justified those classifications.
- **Remediation:** Added dated official-reference URLs and explicitly scoped them to capability-class evidence, with mandatory revalidation at implementation time.
- **Final status:** `RESOLVED`

### F-35 — HIGH — RESOLVED

- **Initial finding:** `DocumentRelation` did not distinguish a floating logical-document dependency from an exact revision-pinned evidentiary dependency.
- **Remediation:** Added `target_binding_mode: LOGICAL_CURRENT | PINNED_REVISION`, defined semantics, and required exact pinned targets for `VALIDATES` and `GENERATED_FROM`.
- **Final status:** `RESOLVED`

### F-36 — HIGH — RESOLVED

- **Initial finding:** `DocumentQARecord` was modeled simultaneously as a QA run and as an individual finding, making finding lifecycle and run identity ambiguous.
- **Remediation:** Split `DocumentQARecord` (one attributable QA run) from `DocumentFinding` (one finding) and linked findings back to their originating run.
- **Final status:** `RESOLVED`

## 6. Documentation Governance checklist

- [x] A document can own multiple explicit authority claims without duplicate-authority ambiguity.
- [x] BUILD, INTEGRATE, and OPTIONAL ADAPTER have non-overlapping responsibility semantics.
- [x] Core document governance remains reconstructable offline without hosted products.
- [x] Lifecycle transitions distinguish deprecation from supersession.
- [x] Lifecycle and validity remain separate state dimensions.
- [x] Waiver does not silently equal verified resolution.
- [x] Multi-document changes have per-document and effective change classification.
- [x] Research study-lock authority cannot be relaxed by documentation governance.
- [x] Secret findings persist only non-reversible/redacted evidence.
- [x] Existing repository docs are not retroactively treated as migrated runtime records.
- [x] External tool capabilities must be revalidated at adapter implementation/upgrade time.
- [x] MUST_ALIGN_WITH invalidation semantics are explicit.
- [x] Logical-current and exact-revision relation bindings are distinct.
- [x] QA-run identity and individual finding identity are distinct.
- [x] External tool classifications have a dated capability-evidence snapshot.
- [x] No silent cascade editing is allowed.
- [x] External validators report evidence; GWF owns document validity.
- [x] Implementation remains unauthorized.

## 7. Current aggregate status

**OPEN = 0**

All findings F-01 through F-36 recorded in this checklist are resolved. The documentation-governance specification remains specification-only; implementation-specific findings require a future implementation audit.

## 8. Seven-wave implementation plan QA findings

### F-37 — HIGH — RESOLVED

- **Initial finding:** The plan used `PLAN-QA` and wave-gate IDs without defining how those dependencies resolve to exact evidence identities.
- **Remediation:** Defined PLAN-QA, DIG-SPEC and wave-gate control identities and required exact commit/blob/run resolution in handoff.
- **Final status:** `RESOLVED`

### F-38 — MEDIUM — RESOLVED

- **Initial finding:** Complexity ranges such as 1–2 and 3–4 made the “lowest complexity first” priority rule non-deterministic.
- **Remediation:** Converted every item to one integer priority complexity using the conservative upper bound.
- **Final status:** `RESOLVED`

### F-39 — MEDIUM — RESOLVED

- **Initial finding:** Several item-level governing-document references used non-canonical bare filenames, which could become ambiguous during handoff.
- **Remediation:** Normalized governing document references to canonical `docs/...` paths.
- **Final status:** `RESOLVED`

### F-40 — HIGH — RESOLVED

- **Initial finding:** DG-P0 could theoretically qualify using mocked validator behavior without proving a real pinned markdownlint integration.
- **Remediation:** Added a mandatory real pinned markdownlint-cli2 smoke fixture and pinned config hash; mocks/shims alone cannot qualify P0.
- **Final status:** `RESOLVED`

### F-41 — MEDIUM — RESOLVED

- **Initial finding:** Wave 1 exit gate could be read as automatic authorization for P1–P3 once P0 passes.
- **Remediation:** Explicitly marked DG-W1 as a future gate and retained the current authorization stop immediately after DG-P0.
- **Final status:** `RESOLVED`

### F-42 — MEDIUM — RESOLVED

- **Initial finding:** P0 required validator config attribution but did not explicitly require a pinned minimal markdownlint config as part of acceptance evidence.
- **Remediation:** Added minimal config pinning and config content-hash evidence to P0 scope and checklist.
- **Final status:** `RESOLVED`

## 9. Seven-wave plan checklist

- [x] Every implementation item has one deterministic integer complexity level.
- [x] Every item lists HARD/ORDERING/OPTIONAL/EXTERNAL dependencies as applicable.
- [x] Control dependency IDs resolve to exact QA/gate evidence semantics.
- [x] Every item lists governing document paths.
- [x] Every item has an acceptance checklist.
- [x] Every wave has an exit gate.
- [x] Handoff package requirements are explicit.
- [x] DG-P0 requires a real pinned markdownlint smoke test.
- [x] DG-P0 excludes registry/graph/research mutation/auto-fix.
- [x] Current authorization stops after DG-P0.
- [x] Parking-lot items are not accidentally promoted into the active 7-wave plan.
- [x] Implementation remains unauthorized for DG-P1 and later items.

## 10. Current aggregate status after 7-wave plan QA

**OPEN = 0**

All findings F-01 through F-42 recorded in this checklist are resolved.

## 11. DG-P0 implementation findings

### F-43 — MEDIUM — RESOLVED

- **Initial finding:** The first real-tool gate assumed a successful `markdownlint-cli2 --help` probe must exit 0, while pinned markdownlint-cli2 0.23.3 intentionally exits 2 after printing the valid banner.
- **Remediation:** The probe accepts only 0 or 2 when the exact version banner parses successfully; a regression test covers exit-code-2 behavior.
- **Evidence:** run `35560396897` → repair `cc2b15adb8d5ad0a5ee855e77ae93b6043bbe826` → PASS run `35560545865`.
- **Final status:** `RESOLVED`

### F-44 — HIGH — RESOLVED

- **Initial finding:** markdownlint default formatter output may include `[Context: "..."]` with raw source text, which could leak document content or secrets if normalized findings persisted it.
- **Remediation:** Normalized finding messages remove Context excerpts; a regression test verifies `SECRET_TOKEN=abc` is not retained.
- **Final status:** `RESOLVED`

## 12. DG-P0 completion checklist

- [x] PLAN-QA exact dependency PASS.
- [x] DIG-SPEC exact dependency identified.
- [x] markdownlint-cli2 exact version pinned to 0.23.3.
- [x] config identity/hash recorded.
- [x] provider-neutral adapter contract implemented.
- [x] exact subject hashes recorded.
- [x] valid real fixture PASS.
- [x] invalid real fixture emits a structural finding.
- [x] missing validator is NOT_EVALUATED, not document FAIL.
- [x] source mutation is detected.
- [x] raw Context source excerpt is not persisted.
- [x] real pinned executable smoke PASS.
- [x] P0 unit tests 10/10 PASS.
- [x] bounded regression 24/24 PASS.
- [x] compile PASS.
- [x] first failed real-tool run preserved.
- [x] schema/migration changes = NONE.
- [x] handoff records explicit non-scope and rollback.
- [x] authorization frontier stops after DG-P0.

## 13. Current aggregate status after DG-P0

**OPEN = 0**

All findings F-01 through F-44 recorded in this checklist are resolved. DG-P1 remains unauthorized.

## 14. DG-P1 implementation findings

### F-45 — MEDIUM — RESOLVED

- **Initial finding:** Vale exit semantics differ from markdownlint: warning/suggestion findings can exist with process exit code 0, so reusing the P0 assumption “exit 0 means no findings” would silently misclassify prose drift as PASS.
- **Remediation:** `ValeAdapter` derives `content_status` from parsed findings, while process status remains separate; exit 0 with findings is represented as `SUCCEEDED/FINDINGS`.
- **Evidence:** unit fixture `test_vale_warning_findings_can_exit_zero`; real gate contract at workflow `35563206375`.
- **Final status:** `RESOLVED`

### F-46 — HIGH — RESOLVED

- **Initial finding:** Vale JSON includes the raw `Match` source span. Persisting it, or persisting a message that echoes it, could leak document content or reusable secret-like text into normalized evidence.
- **Remediation:** normalized findings never persist `Match`; any exact matched text echoed by `Message` is replaced with `<redacted-match>`. A regression uses `SECRET_TOKEN=abc` to prove generic redaction.
- **Evidence:** `test_vale_secret_like_match_is_redacted`; final implementation head `385016bf6d0c3df512bae6fa8776cca32eac83ee`.
- **Final status:** `RESOLVED`

### F-47 — MEDIUM — RESOLVED

- **Initial finding:** Hashing only `.vale.ini` would not identify the actual prose policy because Vale rule YAML files materially define terminology behavior.
- **Remediation:** DG-P1 records per-file SHA-256 for `.vale.ini` and `styles/GWF/Terminology.yml`, plus a deterministic aggregate configuration-bundle hash.
- **Evidence:** aggregate hash `270b05bb9d8930556595d3d5a805f8dc72145345545250110d3bda2b65bc55d3`; gate checks all identities.
- **Final status:** `RESOLVED`

## 15. DG-P1 completion checklist

- [x] DG-P0 hard dependency PASS.
- [x] reconciled 7-wave/GAC documentation baseline carried into the implementation branch.
- [x] Vale upstream capability revalidated.
- [x] Vale exact version pinned to 3.22.0.
- [x] official release checksum verified in CI.
- [x] adapter reuses `ValidatorExecution` / `ValidatorFinding`.
- [x] exact subject hash recorded.
- [x] exact vocabulary/config identities recorded.
- [x] clean fixture returns `SUCCEEDED/PASS`.
- [x] terminology drift fixture returns `SUCCEEDED/FINDINGS`.
- [x] finding rule/severity/line/column normalized.
- [x] warning/suggestion findings are not lost when Vale exits 0.
- [x] missing Vale executable is `UNAVAILABLE/NOT_EVALUATED`, not document FAIL.
- [x] version mismatch fails closed.
- [x] malformed JSON fails closed.
- [x] source mutation is detected.
- [x] raw `Match` text is not persisted.
- [x] secret-like matched text regression PASS.
- [x] no auto-fix invocation exists.
- [x] P1 unit tests 10/10 PASS.
- [x] real pinned Vale smoke PASS.
- [x] bounded regression 34/34 PASS.
- [x] compile PASS.
- [x] schema/migration changes = NONE.
- [x] no GAC runtime implemented.
- [x] current authorization frontier stops before DG-P2.

## 16. Current aggregate status after DG-P1

**OPEN = 0**

All findings F-01 through F-47 recorded in this checklist are resolved. DG-P2 remains unauthorized.

## 17. DG-P2 implementation findings

### F-48 — MEDIUM — RESOLVED

- **Initial finding:** The first real-tool workflow `35564490278` at implementation commit `1df9341a4b8c6e5daab792c6d3801c9b0ea19006` verified the exact Lychee 0.24.2 archive checksum successfully, but the install step assumed the executable was at the archive root. The upstream release archive actually wraps files in `lychee-x86_64-unknown-linux-gnu/`, so qualification stopped before tests.
- **Remediation:** The workflow now resolves the exact packaged path `lychee-x86_64-unknown-linux-gnu/lychee` and asserts `test -x` before execution.
- **Evidence:** failed run `35564490278` preserved; repair commit `eb71f30916cca08e7df418e1ffbc2e91eca91a13`; repair workflow `35564566332` PASS.
- **Final status:** `RESOLVED`

### F-49 — HIGH — RESOLVED

- **Initial finding:** Lychee exit code 2 represents both ordinary broken links and transport-level failures. Treating exit code 2 alone as a document finding would conflate content invalidity with network/tool uncertainty.
- **Remediation:** `LycheeAdapter` parses the pinned JSON schema. Internal missing-file errors and external HTTP responses with an explicit status code normalize as link findings; external errors without an HTTP code and all timeout-map entries fail closed as `TOOL_ERROR/NOT_EVALUATED` with `NETWORK_FAILURE`.
- **Evidence:** unit fixtures cover internal broken, external HTTP broken, network failure and timeout semantics; real gate `35564566332` verifies `network_failure_not_content_failure=true`.
- **Final status:** `RESOLVED`

### F-50 — HIGH — RESOLVED

- **Initial finding:** Lychee JSON includes complete checked URLs, which may contain sensitive query strings or other source-derived material. Persisting raw URLs in normalized findings would violate the minimum-evidence/privacy boundary.
- **Remediation:** normalized findings persist only rule class, generic message, status code and source location; raw URLs are not copied into finding messages and raw Lychee JSON is not part of `ValidatorExecution`.
- **Evidence:** unit regression uses a secret-like query string; real gate `35564566332` verifies `raw_urls_not_persisted=true`.
- **Final status:** `RESOLVED`

## 18. DG-P2 completion checklist

- [x] DG-P0 hard dependency PASS.
- [x] DG-P1 sequential governance closure verified before advancement.
- [x] Lychee upstream capability/release revalidated.
- [x] exact Lychee version pinned to 0.24.2.
- [x] upstream release tag and commit pinned.
- [x] exact Linux release asset checksum verified.
- [x] Lychee config identity/hash recorded.
- [x] adapter reuses `ValidatorExecution` / `ValidatorFinding`.
- [x] internal and external broken-link findings are distinguishable.
- [x] network/tool failure is distinct from broken-link content findings.
- [x] missing Lychee executable is `UNAVAILABLE/NOT_EVALUATED`.
- [x] version mismatch fails closed.
- [x] malformed JSON fails closed.
- [x] source mutation is detected.
- [x] raw checked URLs are not persisted in normalized findings.
- [x] P2 unit tests 10/10 PASS.
- [x] real pinned Lychee smoke PASS.
- [x] bounded regression 44/44 PASS.
- [x] compile PASS.
- [x] first failed real-tool run preserved.
- [x] schema/migration changes = NONE.
- [x] no document registry/graph/validity runtime implemented.
- [x] no GAC, G2E Library or Reference Acquisition runtime implemented.
- [x] no auto-repair link mutation implemented.
- [x] current authorization frontier stops before DG-P3.

## 19. Current aggregate status after DG-P2

**OPEN = 0**

All findings F-01 through F-50 recorded in this checklist are resolved. DG-P3 remains unauthorized.

## 20. DG-P3 pre-implementation qualification findings

### F-51 — HIGH — RESOLVED

- **Initial finding:** Repository full name and file path are locators that can change. Treating either as immutable identity would make Git evidence ambiguous.
- **Resolution:** DG-P3 successful evidence must bind provider repository ID + exact commit SHA + exact blob SHA. `repository_full_name_at_resolution` and `path_locator` remain attributable locators only.
- **Evidence:** frozen spec commit `f8d18e55d17344f10c0eb45c9d8beb3df6eea279`, blob `e005776db28d57ce1276b07475b9a7f7a5b6be97`.
- **Final status:** `RESOLVED`

### F-52 — HIGH — RESOLVED

- **Initial finding:** v0.8.4 `bind_repository()` requires both `REPO_READ` and `CONTENT_WRITE`, which over-privileges a read-only resolver if reused unchanged.
- **Resolution:** DG-P3 implementation must permit repository binding with `REPO_READ` alone and enforce `CONTENT_WRITE` explicitly at write preparation/execution boundaries. Existing `WORKFLOW_WRITE` and SHA-safe write protections remain unchanged.
- **Evidence:** exact `github_plugin.py` blob `19d3f8ce0baf38675bd0ca7938d781ff1521bca3`; frozen DG-P3 spec §6.
- **Final status:** `RESOLVED`

### F-53 — MEDIUM — RESOLVED

- **Initial finding:** A new Git-evidence store could duplicate Artifact/Revision, ObjectRef or generic Evidence ownership.
- **Resolution:** reuse existing canonical stores; DG-P3 core returns a normalized evidence value and creates no automatic Artifact/Revision/ObjectRef. No new persistence table or migration is justified.
- **Evidence:** `knowledge.py` blob `4f848c2be53451df01b9b91d2705ae3c59aa7bf7`; `object_store.py` blob `d9d8f2ca42ce747b43463f4ca037aae234037d6e`; `execution.py` blob `87dfa05789acc71c7681c3ca1e6e3bd9895025d3`.
- **Final status:** `RESOLVED`

### F-54 — HIGH — RESOLVED

- **Initial finding:** A resolver that silently refreshes expected repository/commit/blob identity after drift would destroy exact-revision provenance.
- **Resolution:** expected repository ID, commit SHA and blob SHA are exact expectations; mismatch fails closed with stale semantics. No automatic refresh, fallback ref or retry-to-PASS is allowed.
- **Evidence:** existing GitHub SHA QA Standard blob `b3e2528c551bd137a0ca6ee063db508f45dab1cf`; frozen DG-P3 spec §§10–12.
- **Final status:** `RESOLVED`

### F-55 — HIGH — RESOLVED

- **Initial finding:** GitHub file/provider responses may include source content while runtime credential resolution contains reusable secrets.
- **Resolution:** normalized DG-P3 evidence excludes raw content and provider response bodies; credential resolution stays runtime-only; audit/error output may contain identity/digest fields but no credential material.
- **Evidence:** `plugins.py` blob `4b1caf00f83250018c07af43541906b245996d7d`; frozen DG-P3 spec §13.
- **Final status:** `RESOLVED`

## 21. DG-P3 pre-implementation qualification checklist

- [x] human explicit authorization gate passed before specification work.
- [x] DG-P2 formal-close base verified.
- [x] exact Documentation Governance revision loaded.
- [x] exact v0.8.4 SHA QA standard/design loaded.
- [x] existing GitHub plugin and REST adapter inspected.
- [x] Artifact/Revision primitives inventoried.
- [x] ObjectRef primitives inventoried.
- [x] generic Evidence persistence inventoried.
- [x] no new canonical store required.
- [x] provider repository-ID gap identified and bounded.
- [x] read-only least-privilege gap identified and bounded.
- [x] resolver request/result contract frozen.
- [x] path explicitly not identity.
- [x] stale repository/commit/blob expectations fail closed.
- [x] F1–F13 fixture matrix frozen.
- [x] raw content excluded from normalized evidence.
- [x] credentials remain runtime-only.
- [x] no schema/migration authorized.
- [x] no document registry/graph/validity runtime authorized.
- [x] no GAC/G2E Library/Reference Acquisition authorized.
- [x] document QA bound to exact DG-P3 spec blob.
- [x] implementation has not started.

## 22. Current aggregate status after DG-P3 pre-implementation qualification

**OPEN = 0**

All findings F-01 through F-55 recorded in this checklist are resolved.

```text
DG-P3 authorization       = PASS
DG-P3 specification       = FROZEN
DG-P3 dependency qualify  = PASS
DG-P3 document QA         = PASS
DG-P3 implementation      = NOT_STARTED
DG-P3 overall             = NOT_YET_PASS
DG-W1                     = OPEN
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```

## 23. DG-P3 implementation findings

### F-56 — MEDIUM — RESOLVED

- **Initial finding:** The first DG-P3 qualification run reached and passed all 14 unit/fixture tests, but the real-provider gate script contained a Python string-literal syntax error, preventing the real GitHub smoke from executing.
- **Resolution:** Corrected only the gate assertion string. The frozen DG-P3 contract, resolver implementation, capability-separation behavior, F1–F13 fixtures and acceptance gates were unchanged.
- **Evidence:** initial run `35576942299` preserved; repair commit `9b4426f4c0d3dd6f39b2e2b2750473fd309b779b`; qualification run `35577009823` PASS.
- **Final status:** `RESOLVED`

## 24. DG-P3 implementation qualification checklist

- [x] implementation started from exact pre-implementation qualification HEAD `20bb90aa791f20a57de861e2458368e7b0ce9a82`.
- [x] frozen specification blob remained `e005776db28d57ce1276b07475b9a7f7a5b6be97`.
- [x] repository binding can operate with `REPO_READ` only.
- [x] write preparation explicitly requires `CONTENT_WRITE`.
- [x] workflow writes still additionally require `WORKFLOW_WRITE`.
- [x] existing SHA-safe write path regression preserved.
- [x] provider repository-ID read implemented.
- [x] exact repository/commit/blob resolver implemented.
- [x] path remains locator, not immutable identity.
- [x] no Artifact/Revision/ObjectRef is created automatically.
- [x] no schema/migration added.
- [x] F1–F13 fixture matrix PASS.
- [x] 14/14 DG-P3 unit/fixture tests PASS.
- [x] real GitHub exact-identity smoke PASS.
- [x] real repository ID = `1374857546`.
- [x] read-only write attempt denied.
- [x] raw content absent from normalized evidence.
- [x] credential material absent from normalized evidence.
- [x] deterministic exact resolution PASS.
- [x] bounded regression 54/54 PASS.
- [x] compile PASS.
- [x] failed first qualification run preserved.
- [x] evidence artifact `10627989044` recorded.
- [x] GAC remains locked.
- [x] DG-W1 has not been opened/closed by this implementation.

## 25. Current aggregate status after DG-P3 implementation qualification

**OPEN = 0**

All findings F-01 through F-56 recorded in this checklist are resolved.

```text
DG-P3 specification       = FROZEN
DG-P3 implementation      = QUALIFIED_PASS
DG-P3 implementation SHA  = 9b4426f4c0d3dd6f39b2e2b2750473fd309b779b
DG-P3 workflow            = 35577009823 PASS
DG-P3 artifact            = 10627989044
DG-P3 handoff HEAD        = 0331eedf20910b8d3b23018a6f7c86d114258baf
DG-P3 exact-head workflow = 35577202015 PASS
DG-P3 exact-head artifact = 10628478735
DG-P3 overall             = FORMALLY_CLOSED
DG-W1                     = OPEN
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```

## 26. DG-W1 Wave 1 requalification

No new implementation finding was opened by the Wave-1 combined QA.

Requalification on head `bea3cf23dd9b14cde999e9effe13e1cc9e6af1e5` verified:

- DG-P0 real gate PASS;
- DG-P1 real gate PASS;
- DG-P2 real gate PASS;
- DG-P3 real gate PASS;
- shared validator contract compatibility PASS;
- exact tool/version/config fingerprints recorded;
- no authoritative document-state or GAC runtime present;
- compile PASS.

Evidence: workflow `35580447186`, artifact `10630420383`.

**OPEN = 0**

DG-W1 handoff exact-head qualification remains pending.

## 27. DG-W1 formal close

DG-W1 committed handoff HEAD `84383fe2978eff8ab795c7607df6f19360a5ca1f` passed the combined Wave-1 requalification workflow.

- exact-head workflow: `35580636537` PASS
- exact-head artifact: `10629413613`
- artifact digest: `sha256:54b8e518ef51553b6e5be1f428d346551a1c4f7b9b53fe0936c61e592a1cafe2`
- DG-P0/P1/P2/P3: PASS
- exact tool/version/config fingerprints: recorded
- forbidden document/GAC runtime hits: none

**OPEN = 0**

DG-W1 is formally closed. Wave 2 may begin with DG-P4 reuse/spec qualification. GAC remains locked until DG-W4 PASS.

## 28. DG-P4 pre-implementation qualification findings

### F-57 — HIGH — RESOLVED

- **Initial finding:** The plan's bottom `Current authorization frontier` still described DG-P2 as the next item even though the same plan had already formal-closed DG-W1.
- **Resolution:** Update the current frontier to the exact DG-W1 closure and DG-P4 pre-implementation state. Historical completion sections remain unchanged.
- **Final status:** `RESOLVED`

### F-58 — HIGH — RESOLVED

- **Initial finding:** Existing Artifact/Revision storage is reusable, but `KnowledgeKernel.create_artifact()` admits only artifact types declared by the active domain package. A cross-domain document facade therefore cannot use existing storage unchanged.
- **Resolution:** Freeze one reserved core artifact type `governed_document`, admitted through the KnowledgeKernel artifact-config path while reusing the same `artifacts/revisions` tables. No direct DB insert and no parallel registry are permitted. Domain collision with the reserved type fails closed.
- **Evidence:** `knowledge.py` blob `4f848c2be53451df01b9b91d2705ae3c59aa7bf7`; `domain.py` blob `b257a675fbd8ba2da34a3009489e09ad9accc0af`; frozen DG-P4 spec.
- **Final status:** `RESOLVED`

### F-59 — HIGH — RESOLVED

- **Initial finding:** Path or path-derived logical key would make document identity unstable under rename.
- **Resolution:** `document_id = artifact_id`; `logical_key = gwr:document:<explicit stable document_key>`; repository/path remain revision locators only.
- **Final status:** `RESOLVED`

### F-60 — HIGH — RESOLVED

- **Initial finding:** Existing `Revision.content_hash` hashes the structured GWF payload and is not the same identity as the source document bytes or Git blob.
- **Resolution:** Preserve three distinct identities: Revision payload hash, Git blob SHA, and source content SHA-256. DG-P4 revisions must bind the latter two through DG-P3 evidence.
- **Final status:** `RESOLVED`

### F-61 — MEDIUM — RESOLVED

- **Initial finding:** A broad DocumentRecord facade could accidentally pre-implement lifecycle, validity, authority or graph semantics owned by later items.
- **Resolution:** DG-P4 is identity/provenance only. DG-P6 owns lifecycle/validity; DG-P7 owns authority; DG-P8+ own relations/graph semantics.
- **Final status:** `RESOLVED`

### F-62 — HIGH — RESOLVED

- **Initial finding:** Automatically discovering repository Markdown and assigning governed identity at P4 would violate the explicit migration boundary and could silently assign authority.
- **Resolution:** Registration is explicit and one-at-a-time; startup/repository scan creates no governed documents. Bulk migration remains DG-P20.
- **Final status:** `RESOLVED`

## 29. DG-P4 pre-implementation qualification checklist

- [x] DG-W1 final exact-head PASS verified.
- [x] exact KnowledgeKernel/Domain/Governance revisions inspected.
- [x] Artifact storage reuse qualified.
- [x] Revision storage reuse qualified.
- [x] parallel document/revision tables rejected.
- [x] no schema migration justified.
- [x] cross-domain artifact admission gap identified and bounded.
- [x] stable document ID mapped to Artifact ID.
- [x] stable document key is path-independent.
- [x] exact source evidence reuses DG-P3.
- [x] source digest and revision payload hash kept separate.
- [x] existing authority/audit path preserved.
- [x] no direct DB persistence authorized.
- [x] no silent migration authorized.
- [x] lifecycle/validity deferred to DG-P6.
- [x] authority deferred to DG-P7.
- [x] relations/graph deferred to DG-P8+.
- [x] D4-F1..D4-F15 fixture matrix frozen.
- [x] document QA bound to exact DG-P4 spec blob.
- [x] implementation has not started.

## 30. Current aggregate status after DG-P4 pre-implementation qualification

**OPEN = 0**

All findings F-01 through F-62 recorded in this checklist are resolved.

```text
DG-W1                     = FORMALLY_CLOSED
DG-P4 authorization       = PASS
DG-P4 specification       = FROZEN
DG-P4 reuse qualification = PASS
DG-P4 document QA         = PASS
DG-P4 implementation      = NOT_STARTED
DG-P4 overall             = NOT_YET_PASS
DG-W2                     = OPEN
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```

## 31. DG-P4 implementation findings

### F-63 — HIGH — RESOLVED

- **Initial finding:** The first DG-P4 fixture run showed that `PluginConnectionService.attach_runtime_adapter()` required `commit_files` for every GitHub adapter, including `REPO_READ`-only connections. This left the adapter interface more privileged than the capability boundary established by DG-P3.
- **Resolution:** Adapter validation is now capability-specific. Read-only GitHub connections require only read methods; `commit_files` remains mandatory for `CONTENT_WRITE` / `WORKFLOW_WRITE` connections. SHA-safe write execution and capability values were not changed.
- **Negative evidence preserved:** workflow `35582000925` on implementation head `438bed30ef7ed7f05790a063fdd28d36b7eec47f` failed before real-provider execution.
- **Repair evidence:** commits `a992d0906eebc12bf880a16fcef8f0da46466b12` and `633e36eda823adb0cf8cdd9d6d1877c7c4e41300`; final qualification workflow `35582178488` PASS.
- **Final status:** `RESOLVED`

## 32. DG-P4 implementation qualification checklist

- [x] implementation started from exact pre-implementation qualification HEAD `a6d17ceb85006d539025225a2376ff1dc32911b8`.
- [x] frozen specification blob remained `b0034171454d06dbdeec2145ab73d5fb0cee2982`.
- [x] `document_id = artifact_id`.
- [x] document revision ID = underlying `revision_id`.
- [x] reserved core type `governed_document` admitted without domain duplication.
- [x] reserved core-type collision fails closed.
- [x] arbitrary unknown artifact type remains rejected.
- [x] no DocumentRecord / DocumentRevision table added.
- [x] schema/migration changes = NONE.
- [x] stable logical key remains path-independent.
- [x] DG-P3 exact repository/commit/blob identity reused.
- [x] payload hash, Git blob SHA and source SHA-256 remain distinct.
- [x] no raw document content duplicated into facade metadata.
- [x] no silent Markdown migration.
- [x] existing authorization/audit path preserved.
- [x] read-only GitHub adapter does not require write method.
- [x] write-capable GitHub adapter still requires `commit_files`.
- [x] D4-F1..D4-F15 PASS.
- [x] real GitHub document-facade smoke PASS.
- [x] current revision begins `UNVERIFIED`.
- [x] no relation, QA Evidence or Gate created by P4 registration.
- [x] full regression 163/163 PASS.
- [x] compile PASS.
- [x] evidence artifact `10630782224` recorded.
- [x] GAC remains locked.
- [x] DG-P5/P6 have not been implemented.

## 33. Current aggregate status after DG-P4 implementation qualification

**OPEN = 0**

All findings F-01 through F-63 recorded in this checklist are resolved.

```text
DG-W1                     = FORMALLY_CLOSED
DG-P4 specification       = FROZEN
DG-P4 implementation      = QUALIFIED_PASS
DG-P4 implementation SHA  = 633e36eda823adb0cf8cdd9d6d1877c7c4e41300
DG-P4 workflow            = 35582178488 PASS
DG-P4 artifact            = 10630782224
DG-P4 handoff HEAD        = 06e477b83f503c0a2eb0cdff16c33a8687545f1b
DG-P4 exact-head workflow = 35582417034 PASS
DG-P4 exact-head artifact = 10630384626
DG-P4 overall             = FORMALLY_CLOSED
DG-P5                     = NEXT / NOT_STARTED
DG-W2                     = OPEN
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```

## 34. DG-P5 pre-implementation qualification findings

### F-64 — HIGH — RESOLVED

- **Initial finding:** Creating a dedicated `document_qa_records` table would duplicate PRIM-EVIDENCE identity, subject binding, payload hashing, producer attribution, timestamps and audit semantics.
- **Resolution:** `DocumentQARecord.qa_record_id = Evidence.evidence_id` with reserved evidence type `document_qa_record`.
- **Final status:** `RESOLVED`

### F-65 — HIGH — RESOLVED

- **Initial finding:** None of Evidence, FailureRecord, Gate or Artifact/Revision can represent the required mutable DocumentFinding lifecycle without semantic distortion.
- **Resolution:** exactly one dedicated `document_findings` current-state table is justified. It remains linked to the originating QA Evidence row; transition history uses append-only Audit.
- **Final status:** `RESOLVED`

### F-66 — HIGH — RESOLVED

- **Initial finding:** current `ExecutionKernel.add_evidence()` commits internally, so QA Evidence + finding rows cannot be created atomically by composition.
- **Resolution:** implementation must make a bounded transactional extension to the existing Evidence writer while preserving existing `add_evidence()` behavior for all current callers. A duplicate Evidence writer/store is forbidden.
- **Evidence:** `execution.py` blob `87dfa05789acc71c7681c3ca1e6e3bd9895025d3`.
- **Final status:** `RESOLVED`

### F-67 — HIGH — RESOLVED

- **Initial finding:** prior QA PASS could be misread as validating a newly created document revision.
- **Resolution:** QA is current only when its exact subject revision equals the document's current revision. Historical QA is never rewritten or transferred.
- **Final status:** `RESOLVED`

### F-68 — MEDIUM — RESOLVED

- **Initial finding:** the governing specification requires finding severity but does not enumerate severity values.
- **Resolution:** DG-P5 freezes `INFO / LOW / MEDIUM / HIGH / CRITICAL`; unknown values fail closed.
- **Final status:** `RESOLVED`

### F-69 — HIGH — RESOLVED

- **Initial finding:** implementing a standalone finding-waiver store would duplicate approval/authority semantics and risk treating WAIVED as equivalent to verified resolution.
- **Resolution:** reuse existing Proposal/Approval; `waiver_ref` points to approved authority evidence. SECURITY_LEAK, RESEARCH_LOCK_VIOLATION and DUPLICATE_AUTHORITY are non-waivable at minimum. WAIVED remains distinct from VERIFIED_RESOLVED.
- **Final status:** `RESOLVED`

### F-70 — MEDIUM — RESOLVED

- **Initial finding:** cross-domain QA Evidence type names could collide with domain-declared evidence semantics.
- **Resolution:** reserve `document_validator_execution` and `document_qa_record` as core evidence IDs and fail closed on incompatible domain collision.
- **Final status:** `RESOLVED`

### F-71 — HIGH — RESOLVED

- **Initial finding:** the conceptual QA subject contract includes DocumentChangeSet, but DG-P11 has not implemented that object yet.
- **Resolution:** P5 may reserve `DOCUMENT_CHANGE_SET` as a subject kind but must reject unresolved/dangling change-set refs. P5 must not create a parallel placeholder change-set subsystem.
- **Final status:** `RESOLVED`

## 35. DG-P5 pre-implementation qualification checklist

- [x] DG-P4 final formal-close HEAD verified.
- [x] DG-P4 final exact-head workflow `35582578994` PASS verified.
- [x] governing §§8.5–8.6, 17–18 loaded.
- [x] PRIM-EVIDENCE inventoried.
- [x] PRIM-GATE inventoried.
- [x] PRIM-FAILURE inventoried.
- [x] Artifact/Revision fit evaluated.
- [x] Proposal/Approval fit evaluated.
- [x] append-only Audit fit evaluated.
- [x] DocumentQARecord reuse proof PASS.
- [x] ValidatorExecution Evidence reuse proof PASS.
- [x] dedicated QA table rejected.
- [x] dedicated validator-execution table rejected.
- [x] DocumentFinding existing-primitive reuse rejected with semantic reason.
- [x] exactly one new finding state table justified.
- [x] waiver subsystem reuse frozen.
- [x] exact-revision freshness invariant frozen.
- [x] finding lifecycle and legal transitions frozen.
- [x] finding fingerprint requirement frozen.
- [x] Evidence atomic-composition gap bounded.
- [x] D5-F1..D5-F20 frozen.
- [x] no DG-P6 lifecycle/validity mutation authorized.
- [x] no DG-P11 placeholder implementation authorized.
- [x] no GAC/RA/G2E authorized.
- [x] exact document QA bound to DG-P5 spec blob.
- [x] implementation has not started.

## 36. Current aggregate status after DG-P5 pre-implementation qualification

**OPEN = 0**

All findings F-01 through F-71 recorded in this checklist are resolved.

```text
DG-P4                     = FORMALLY_CLOSED
DG-P5 authorization       = PASS
DG-P5 specification       = FROZEN
DG-P5 dependency qualify  = PASS
DG-P5 document QA         = PASS
DG-P5 implementation      = NOT_STARTED
DG-P5 overall             = NOT_YET_PASS
DG-P6                     = NOT_STARTED
DG-W2                     = OPEN
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```

## 37. DG-P5 implementation findings

### F-72 — LOW — RESOLVED

- **Initial finding:** The first DG-P5 qualification workflow referenced two regression test paths that do not exist in the repository, so the workflow stopped after D5-F1..D5-F20 and the bounded schema gate had already passed.
- **Resolution:** Changed only the workflow regression selection to existing test files covering Execution/Evidence/Gate/Failure, Knowledge, Persistence and DG-P4 compatibility. DG-P5 runtime code, migration, frozen specification and acceptance gates were unchanged.
- **Negative evidence preserved:** workflow `35584776602` on head `c42800b6d635ba5d90be0b947955ccdfbaeb9f91`.
- **Repair evidence:** commit `fda9f7b3c5486f629e47f13652a758de158f7d22`; workflow `35584865418` PASS.
- **Final status:** `RESOLVED`

## 38. DG-P5 implementation qualification checklist

- [x] implementation started from exact qualification HEAD `6d4ab89bfb86426dcf19703ae264f7c009f33015`.
- [x] frozen specification blob remained `29ca1c85f665468aade7fc555b634a134af9a46a`.
- [x] migration `0008_v086_dg_p5_document_findings` adds `document_findings`.
- [x] no `document_qa_records` table added.
- [x] no validator-execution table added.
- [x] no waiver table added.
- [x] no finding-transition table added.
- [x] DocumentQARecord persists as PRIM-EVIDENCE.
- [x] ValidatorExecution persists as PRIM-EVIDENCE.
- [x] Evidence writer supports bounded outer transaction participation while existing default behavior remains auto-commit.
- [x] QA creation is atomic across validator Evidence, QA Evidence, findings and audit.
- [x] reserved core Evidence type collision fails closed.
- [x] finding lifecycle + optimistic versioning implemented.
- [x] exact-resolution verification implemented.
- [x] prior QA does not transfer to a new document revision.
- [x] waiver reuses Proposal/Approval.
- [x] minimum non-waivable classes enforced.
- [x] expired/review-due waiver is not effective clean state.
- [x] D5-F1..D5-F20 PASS.
- [x] bounded schema/primitive gate PASS.
- [x] targeted Evidence/Gate/Failure regressions PASS.
- [x] full repository regression PASS.
- [x] compile PASS.
- [x] evidence artifact `10631014201` recorded.
- [x] DG-P6 remains NOT_STARTED.
- [x] no DG-P11 placeholder state introduced.
- [x] GAC remains locked.

## 39. Current aggregate status after DG-P5 implementation qualification

**OPEN = 0**

All findings F-01 through F-72 recorded in this checklist are resolved.

```text
DG-P4                     = FORMALLY_CLOSED
DG-P5 specification       = FROZEN
DG-P5 implementation      = QUALIFIED_PASS
DG-P5 implementation SHA  = fda9f7b3c5486f629e47f13652a758de158f7d22
DG-P5 workflow            = 35584865418 PASS
DG-P5 artifact            = 10631014201
DG-P5 handoff HEAD        = dc4e9d721bf9ee7f8bca16142f239c9fbc8364f9
DG-P5 exact-head workflow = 35585124780 PASS
DG-P5 exact-head artifact = 10631794399
DG-P5 overall             = FORMALLY_CLOSED
DG-P6                     = NEXT / NOT_STARTED
DG-W2                     = OPEN
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```

## 40. DG-P6 pre-implementation qualification findings

### F-73 — HIGH — RESOLVED

- **Initial finding:** Adding documentation `BLOCKED` directly to the kernel-wide `VALIDITY` enum would silently change shared WorkUnit/Gate/impact/recovery semantics for every artifact type.
- **Resolution:** documentation `BLOCKED` is a derived effective validity state. Kernel persisted validity remains in the existing vocabulary and must be non-VALID whenever the document is effectively BLOCKED.
- **Final status:** `RESOLVED`

### F-74 — HIGH — RESOLVED

- **Initial finding:** Lifecycle and validity could be collapsed into one state axis even though the governing specification explicitly separates them.
- **Resolution:** lifecycle reuses `Artifact.lifecycle_status`; persisted revision validity reuses `Revision.validity_state`; document-effective validity is a projection over revision + exact QA/finding state.
- **Final status:** `RESOLVED`

### F-75 — HIGH — RESOLVED

- **Initial finding:** Existing `set_validity_system()` can assign kernel validity but is not an evidence-based document adjudicator and does not itself establish why a document is clean.
- **Resolution:** P6 public semantics use `reconcile_document_validity()`, not arbitrary target-state assignment. VALID may be derived only from exact PASS QA with no blockers; later implementation must audit derived mutations.
- **Final status:** `RESOLVED`

### F-76 — HIGH — RESOLVED

- **Initial finding:** A clean QA run could accidentally erase existing STALE/DIRTY/FAILED kernel facts.
- **Resolution:** QA reconciliation may promote only `UNVERIFIED -> VALID`. STALE/DIRTY/FAILED cannot be cleared by QA alone.
- **Final status:** `RESOLVED`

### F-77 — HIGH — RESOLVED

- **Initial finding:** An effective finding waiver could be mistaken for an automatic clean QA PASS even though the governing policy says waiver-to-PASS is gate-policy-dependent.
- **Resolution:** immutable QA `FAIL` remains effective BLOCKED by default even when findings are effectively waived. A future explicit gate policy is required to authorize otherwise.
- **Final status:** `RESOLVED`

### F-78 — HIGH — RESOLVED

- **Initial finding:** P6 cannot prove safe logical supersession or archival before document authority and typed dependency semantics exist.
- **Resolution:** `SUPERSEDED` and `ARCHIVED` are recognized lifecycle values but public transitions into them are fail-closed/deferred until later governance dependencies can prove authority/dependency retirement.
- **Final status:** `RESOLVED`

### F-79 — HIGH — RESOLVED

- **Initial finding:** Existing old-revision `status='SUPERSEDED'` can be confused with logical document lifecycle `SUPERSEDED`.
- **Resolution:** revision supersession remains immutable revision lineage only; it never automatically changes `Artifact.lifecycle_status`.
- **Final status:** `RESOLVED`

### F-80 — MEDIUM — RESOLVED

- **Initial finding:** `Artifact.lifecycle_status` exists but has no bounded governed transition contract, creating stale-write/history risk if mutated ad hoc.
- **Resolution:** P6 lifecycle transitions must use exact `artifact.version`, increment version, preserve current revision/content and append Audit. No lifecycle event table is added.
- **Final status:** `RESOLVED`

### F-81 — MEDIUM — RESOLVED

- **Initial finding:** P4 creates governed documents as `ACTIVE` while their new revision is `UNVERIFIED`; forcing a DRAFT-first migration would break P4 compatibility and conflate lifecycle with validity.
- **Resolution:** `ACTIVE + UNVERIFIED` is explicitly valid. Existing documents are not bulk rewritten; any future optional initial lifecycle keeps ACTIVE as compatibility default.
- **Final status:** `RESOLVED`

### F-82 — MEDIUM — RESOLVED

- **Initial finding:** the roadmap frontier described DG-P5 as formally closed but still cited its handoff HEAD/run rather than the later final formal-close HEAD `58a4cf5f0ca33ca8e15513eb07234dc575b097bc` and exact-head run `35585295768`.
- **Resolution:** DG-P6 qualification updates the roadmap frontier to the exact DG-P5 formal-close evidence before advancing dependency state.
- **Final status:** `RESOLVED`

## 41. DG-P6 pre-implementation qualification checklist

- [x] exact DG-P5 formal-close HEAD `58a4cf5f0ca33ca8e15513eb07234dc575b097bc` verified.
- [x] DG-P5 final exact-head workflow `35585295768` PASS verified.
- [x] final DG-P5 evidence artifact `10632085985` verified.
- [x] governing Documentation Integrity §§11–12 loaded.
- [x] `Artifact.lifecycle_status` inventoried.
- [x] `Artifact.version` concurrency primitive inventoried.
- [x] `Revision.validity_state` and global VALIDITY inventoried.
- [x] WorkUnit readiness semantics inventoried.
- [x] Gate PASS/FAIL/BLOCKED semantics inventoried.
- [x] P5 exact QA/finding evidence inventoried.
- [x] lifecycle -> Artifact reuse proof PASS.
- [x] revision validity -> existing kernel reuse proof PASS.
- [x] new lifecycle table rejected.
- [x] new validity table rejected.
- [x] global BLOCKED enum extension rejected.
- [x] document-effective validity precedence frozen.
- [x] BLOCKED-to-non-VALID kernel compatibility frozen.
- [x] exact PASS promotion limited to UNVERIFIED -> VALID.
- [x] STALE/DIRTY/FAILED preservation frozen.
- [x] waiver-to-clean-PASS default rejected.
- [x] lifecycle transition subset frozen.
- [x] archive/logical-supersession transitions dependency-gated.
- [x] revision supersession/logical supersession distinction frozen.
- [x] exact-revision QA invalidation reuse frozen.
- [x] zero-migration decision frozen.
- [x] D6-F1..D6-F20 frozen.
- [x] no DG-P7/P8 implementation authorized.
- [x] no DG-W2 closure authorized by this document QA alone.
- [x] no GAC/RA/G2E authorized.
- [x] implementation has not started.

## 42. Current aggregate status after DG-P6 pre-implementation qualification

**OPEN = 0**

All findings F-01 through F-82 recorded in this checklist are resolved.

```text
DG-P5                     = FORMALLY_CLOSED
DG-P5 final closure HEAD  = 58a4cf5f0ca33ca8e15513eb07234dc575b097bc
DG-P5 final exact run     = 35585295768 PASS
DG-P6 authorization       = PASS
DG-P6 specification       = FROZEN
DG-P6 dependency qualify  = PASS
DG-P6 document QA         = PASS
DG-P6 implementation      = NOT_STARTED
DG-P6 overall             = NOT_YET_PASS
DG-W2                     = OPEN
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```

## 43. DG-P6 implementation findings

### F-83 — LOW — RESOLVED

- **Initial finding:** The first DG-P6 implementation fixture D6-F13 referenced gate type `plan_ready`, which does not exist in the frozen research domain. The implementation run therefore stopped at 19/20 fixtures before bounded gate/regression evidence could execute.
- **Negative evidence:** workflow `35598139354` on HEAD `006c198738ef75a915e54c48a7f8400f728a5b25`.
- **Resolution:** Changed only D6-F13 to the existing `prior_art_ready` domain gate and asserted the exact `INPUT_UNVERIFIED` violation. Runtime code, frozen specification, validity vocabulary and zero-migration decision were unchanged.
- **Repair evidence:** commit `5f5121db3e505204452946d31de8dedb3ca5e73e`; workflow `35598284725` PASS.
- **Final status:** `RESOLVED`

## 44. DG-P6 implementation qualification checklist

- [x] implementation started from exact qualification HEAD `dc14622b8e9ff6b66f643567ff9dda27335c8ab0`.
- [x] frozen specification blob remained `155a0c81c291568dbf7d2ba942a9386484f2dd14`.
- [x] no migration/schema change.
- [x] global KnowledgeKernel VALIDITY unchanged.
- [x] lifecycle service implemented over Artifact.lifecycle_status.
- [x] lifecycle transitions use Artifact.version optimistic concurrency.
- [x] lifecycle transitions append Audit.
- [x] archive/logical-supersession transitions remain deferred/fail-closed.
- [x] document-effective BLOCKED is derived, not persisted globally.
- [x] exact QA/finding state drives reconciliation.
- [x] only UNVERIFIED -> VALID clean promotion is allowed.
- [x] later blockers demote VALID -> UNVERIFIED with audit.
- [x] STALE/DIRTY/FAILED are not cleared by QA alone.
- [x] legacy set_validity_system() compatibility retained.
- [x] DocumentFacade read model exposes lifecycle/kernel/effective state without mutation.
- [x] D6-F1..D6-F20 PASS.
- [x] bounded zero-migration/global-validity gate PASS.
- [x] Knowledge/Execution/Decision/P4/P5 regressions PASS.
- [x] full repository regression PASS.
- [x] compile PASS.
- [x] evidence artifact `10638170391` recorded.
- [x] DG-P7/P8 remain NOT_STARTED.
- [x] DG-W2 remains OPEN.
- [x] GAC remains locked.

## 45. Current aggregate status after DG-P6 implementation qualification

**OPEN = 0**

All findings F-01 through F-83 recorded in this checklist are resolved.

```text
DG-P5                     = FORMALLY_CLOSED
DG-P6 specification       = FROZEN
DG-P6 implementation      = QUALIFIED_PASS
DG-P6 implementation SHA  = 5f5121db3e505204452946d31de8dedb3ca5e73e
DG-P6 workflow            = 35598284725 PASS
DG-P6 artifact            = 10638170391
DG-P6 handoff HEAD        = d25454481f0d972c83225e10d3d09b1bb997faf9
DG-P6 exact-head workflow = 35598699495 PASS
DG-P6 exact-head artifact = 10637792150
DG-P6 overall             = FORMALLY_CLOSED
DG-W2                     = OPEN / NOT_EXECUTED
DG-P7/P8                  = NOT_STARTED
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```

## 46. DG-W2 Wave 2 exit-gate findings

### F-84 — LOW — RESOLVED

- **Initial finding:** The first generated DG-W2 workflow was serialized with literal `\\n` sequences instead of YAML line breaks. GitHub therefore rejected the workflow before creating any job.
- **Negative evidence:** workflow `35602654364` on HEAD `d5307d116b81f95bf8ee386685846522487cb249`; zero jobs created.
- **Resolution:** Normalize workflow newlines only. No gate logic, P4/P5/P6 runtime, schema, frozen specification or acceptance invariant changed.
- **Repair evidence:** commit `bdce1392db5e54597a12e5de02d4d916aa081b6f`; workflow `35602717476` PASS.
- **Final status:** `RESOLVED`

## 47. DG-W2 qualification checklist

- [x] exact DG-P6 formal-close HEAD `0c09d16e6a1fe6e01081015f2d7490ba07e58316` used as base.
- [x] DG-P4, DG-P5 and DG-P6 fixture matrices rerun on one exact HEAD.
- [x] real DG-P4 provider gate PASS on exact Wave-2 HEAD.
- [x] DG-P5 component gate PASS on exact Wave-2 HEAD.
- [x] DG-P6 component gate PASS on exact Wave-2 HEAD.
- [x] document identity remains stable across revision/path change.
- [x] new revision identity is distinct.
- [x] exact QA on R1 does not validate R2.
- [x] R2 begins UNVERIFIED.
- [x] R2 FAIL QA creates finding and effective BLOCKED.
- [x] effective BLOCKED leaves kernel non-VALID.
- [x] global KnowledgeKernel VALIDITY unchanged.
- [x] document_findings is the only Wave-2 documentation-specific table.
- [x] no duplicate document/revision/QA/validity/lifecycle subsystem.
- [x] P4 has no migration.
- [x] P5 has exactly one bounded migration.
- [x] P6 has no migration.
- [x] no Wave-3 authority/relation state created.
- [x] targeted Knowledge/Execution/Decision/Persistence/P4/P5/P6 regressions PASS.
- [x] full repository regression PASS.
- [x] compile PASS.
- [x] evidence artifact `10638479929` recorded.
- [x] DG-P7/P8 remain NOT_STARTED.
- [x] GAC remains locked until DG-W4 PASS.
- [x] committed handoff exact-head requalification PASS — run `35603196674` on `be02cdd7eaeadc0534631f15fbe183ddb4b6c7f3`, artifact `10640780655`.

## 48. Current aggregate state during DG-W2 handoff

**OPEN = 0**

All findings F-01 through F-84 are resolved.

```text
DG-P4                     = FORMALLY_CLOSED / REQUALIFIED_PASS
DG-P5                     = FORMALLY_CLOSED / REQUALIFIED_PASS
DG-P6                     = FORMALLY_CLOSED / REQUALIFIED_PASS
DG-W2 qualification       = PASS
DG-W2 QA HEAD             = bdce1392db5e54597a12e5de02d4d916aa081b6f
DG-W2 workflow            = 35602717476 PASS
DG-W2 artifact            = 10638479929
DG-W2 handoff HEAD        = be02cdd7eaeadc0534631f15fbe183ddb4b6c7f3
DG-W2 exact-head workflow = 35603196674 PASS
DG-W2 exact-head artifact = 10640780655
DG-W2 overall             = FORMALLY_CLOSED
DG-P7/P8                  = NOT_STARTED / NOT_AUTHORIZED
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```

## 49. DG-P7 pre-implementation qualification findings

### F-85 — LOW — RESOLVED

- **Initial finding:** The first frozen DG-P7 spec commit carried an incorrect `knowledge.py` blob identity in its dependency table.
- **Resolution:** Re-read every dependency from exact DG-W2 formal-close lineage and corrected only the metadata identities. Canonical spec is commit `f226eb8e01b2284381ba0e7cf5527518512c7ce7`, blob `63d2252314e753b7485f1a0249dc011468be275b`.
- **Final status:** `RESOLVED`

### F-86 — HIGH — RESOLVED

- **Initial finding:** Existing `PRIM-AUTHORITY` / `authority_policies` could be mistaken for document source-of-truth claim state.
- **Resolution:** Freeze the semantic split: authority_policies govern actor/action permission only; document authority claims are a separate Documentation Governance concept.
- **Final status:** `RESOLVED`

### F-87 — HIGH — RESOLVED

- **Initial finding:** Append-only Evidence could be overloaded as current authority ownership using latest-wins reconstruction.
- **Resolution:** Evidence is reused only for authority collision QA and exact observations; it is not canonical mutable claim state.
- **Final status:** `RESOLVED`

### F-88 — HIGH — RESOLVED

- **Initial finding:** Authority claims could be encoded into document logical keys, copied into every Revision, or modeled as a second authority Artifact type.
- **Resolution:** Artifact/Revision are reused only for owner identity and exact grant provenance. No authority-claim Artifact type is introduced.
- **Final status:** `RESOLVED`

### F-89 — HIGH — RESOLVED

- **Initial finding:** Existing primitives have no clean current-state representation for zero-to-many independently retireable logical-document authority claims.
- **Resolution:** Exactly one bounded `document_authority_claims` table is justified. No additional P7 persistence table is admitted.
- **Final status:** `RESOLVED`

### F-90 — HIGH — RESOLVED

- **Initial finding:** Supporting legitimate same-key composition could lead to a new composition-policy subsystem.
- **Resolution:** Composition policy reuses an approved frozen Proposal/Approval payload + exact hash. No composition table is added.
- **Final status:** `RESOLVED`

### F-91 — HIGH — RESOLVED

- **Initial finding:** A duplicate source-of-truth collision might be waived into a misleading clean state.
- **Resolution:** P7 reuses P5 `DUPLICATE_AUTHORITY`, which is already in `NON_WAIVABLE_CLASSES`.
- **Final status:** `RESOLVED`

### F-92 — HIGH — RESOLVED

- **Initial finding:** Invalidity could accidentally be interpreted as authority transfer or claim retirement.
- **Resolution:** Ownership and validity remain separate. BLOCKED/STALE/UNVERIFIED may make the scope unusable but never silently transfer ownership.
- **Final status:** `RESOLVED`

### F-93 — HIGH — RESOLVED

- **Initial finding:** Separate collision-check and claim-write operations could race and admit a clean duplicate authority state.
- **Resolution:** P7 freezes a transactional collision-domain invariant; collision evaluation and ACTIVE claim insertion must share one serialization boundary with equivalent SQLite/PostgreSQL semantics.
- **Final status:** `RESOLVED`

### F-94 — MEDIUM — RESOLVED

- **Initial finding:** Path/title/README/document-class metadata could be treated as implicit authority.
- **Resolution:** Authority is explicit-approved-claim only. Descriptive class or summary status never creates a claim automatically.
- **Final status:** `RESOLVED`

## 50. DG-P7 pre-implementation qualification checklist

- [x] exact DG-W2 formal-close HEAD `f14abb9d8d8a591558ac6d4624a498eb32164726` verified.
- [x] final DG-W2 exact-head workflow `35603521224` PASS verified.
- [x] final DG-W2 artifact `10641345237` verified.
- [x] governing Documentation Integrity §9 loaded.
- [x] BUILD boundary for source-of-truth authority loaded.
- [x] PRIM-AUTHORITY/authority_policies inventoried.
- [x] Artifact/Revision ownership/provenance primitives inventoried.
- [x] Evidence semantics inventoried.
- [x] Proposal/Approval/Audit semantics inventoried.
- [x] P5 `DUPLICATE_AUTHORITY` + non-waivability verified.
- [x] P6 finding-to-BLOCKED behavior preserved.
- [x] actor authority vs document authority split frozen.
- [x] authority Artifact type rejected.
- [x] Evidence claim-store model rejected.
- [x] authority_policies claim-store model rejected.
- [x] exactly one `document_authority_claims` table justified.
- [x] no composition table.
- [x] no collision table.
- [x] claim ACTIVE -> RETIRED lifecycle frozen.
- [x] optimistic versioning frozen.
- [x] PRIMARY semantics frozen.
- [x] COMPOSED exact Proposal/Approval contract frozen.
- [x] project/scope/key collision identity frozen.
- [x] no implicit informative authority.
- [x] ownership separated from validity.
- [x] transactional collision invariant frozen.
- [x] D7-F1..D7-F20 frozen.
- [x] no DG-P8+ implementation authorized.
- [x] no DG-W3 closure authorized.
- [x] no GAC/RA/G2E authorized.
- [x] implementation has not started.

## 51. Current aggregate status after DG-P7 pre-implementation qualification

**OPEN = 0**

All findings F-01 through F-94 recorded in this checklist are resolved.

```text
DG-W2                     = FORMALLY_CLOSED
DG-P7 authorization       = PREIMPLEMENTATION_ONLY
DG-P7 specification       = FROZEN
DG-P7 spec commit         = f226eb8e01b2284381ba0e7cf5527518512c7ce7
DG-P7 spec blob           = 63d2252314e753b7485f1a0249dc011468be275b
DG-P7 dependency qualify  = PASS
DG-P7 document QA         = PASS
DG-P7 implementation      = NOT_STARTED
DG-P7 overall             = NOT_YET_PASS
DG-P8+                    = NOT_STARTED / NOT_AUTHORIZED
DG-W3                     = OPEN / NOT_EXECUTED
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```

## 52. DG-P7 implementation qualification checklist

- [x] implementation started from exact pre-implementation qualification HEAD `7a62d97a8059adb08f0ae7be44a1285d8ee18410`.
- [x] canonical frozen spec remained `f226eb8e01b2284381ba0e7cf5527518512c7ce7` / `63d2252314e753b7485f1a0249dc011468be275b`.
- [x] exactly one migration `0009_v086_dg_p7_document_authority_claims` added.
- [x] exactly one P7 table `document_authority_claims` added.
- [x] no authority Artifact type added.
- [x] no composition table added.
- [x] no duplicate-authority table added.
- [x] existing `authority_policies` unchanged by claim state.
- [x] grant uses Proposal/Approval/Audit.
- [x] PRIMARY collision adjudication implemented.
- [x] COMPOSED exact-contract adjudication implemented.
- [x] claim ACTIVE -> RETIRED lifecycle implemented.
- [x] optimistic claim retirement implemented.
- [x] logical ownership separated from revision validity.
- [x] collision scan emits existing P5 `DUPLICATE_AUTHORITY`.
- [x] no-collision scan emits no synthetic PASS QA.
- [x] `DUPLICATE_AUTHORITY` remains non-waivable.
- [x] P6 effective BLOCKED integration PASS.
- [x] D7-F1..D7-F20 PASS on SQLite.
- [x] D7-F1..D7-F20 PASS on PostgreSQL 17.
- [x] bounded SQLite gate PASS.
- [x] bounded PostgreSQL gate PASS.
- [x] P4/P5/P6 + governance/persistence regressions PASS.
- [x] full repository regression PASS.
- [x] compile PASS.
- [x] SQLite evidence artifact `10644396006` recorded.
- [x] PostgreSQL evidence artifact `10644450806` recorded.
- [x] DG-P8+ remain NOT_STARTED / NOT_AUTHORIZED.
- [x] DG-W3 remains OPEN / NOT_EXECUTED.
- [x] GAC remains locked until DG-W4 PASS.
- [x] committed handoff exact-head requalification PASS — run `35611325233` on `30170e2f0b94f0cde6994c5b9b3ee7c920379688`; SQLite artifact `10643909615`; PostgreSQL artifact `10643409931`.

## 53. Current aggregate state during DG-P7 handoff

**OPEN = 0**

All findings F-01 through F-94 remain resolved; no new implementation finding was required.

```text
DG-W2                     = FORMALLY_CLOSED
DG-P7 specification       = FROZEN
DG-P7 implementation      = QUALIFIED_PASS
DG-P7 implementation SHA  = 3f993ac639c8cb3147d0dc8d888c8b5266e54914
DG-P7 workflow            = 35610704812 PASS
DG-P7 SQLite artifact     = 10644396006
DG-P7 PostgreSQL artifact = 10644450806
DG-P7 handoff HEAD        = 30170e2f0b94f0cde6994c5b9b3ee7c920379688
DG-P7 exact-head workflow = 35611325233 PASS
DG-P7 SQLite artifact     = 10643909615
DG-P7 PostgreSQL artifact = 10643409931
DG-P7 overall             = FORMALLY_CLOSED
DG-P8+                    = NOT_STARTED / NOT_AUTHORIZED
DG-W3                     = OPEN / NOT_EXECUTED
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```

## 54. DG-P8 pre-implementation qualification findings

### F-95 — LOW — RESOLVED

- **Initial finding:** DG-P7 was formally closed at `cf143d959b338e8d77811f5b2b79789ccbbb20aa`, but the roadmap/finding snapshot still cited the earlier handoff exact-head run rather than final closure run `35611830804`.
- **Resolution:** Verified final run `35611830804` PASS on exact formal-close HEAD. Final SQLite artifact is `10644398017` with digest `sha256:fba2d1bfc994670522ea27cd1bcb7eeb2c346132ee8802d5ee0ba53693af6945`; PostgreSQL artifact is `10644037882` with digest `sha256:f3740de876167d21252e2bf1937dc0650a36dbc923323f059c194aed1756e23c`. Roadmap frontier is updated to these exact final identities.
- **Final status:** `RESOLVED`

### F-96 — HIGH — RESOLVED

- **Initial finding:** Existing `TraceLink` could be mistaken for canonical typed document relation state merely because both are graph edges.
- **Resolution:** Freeze two layers: `document_relations` is governed semantic declaration state; `trace_links` remains revision-level operational/provenance state.
- **Final status:** `RESOLVED`

### F-97 — HIGH — RESOLVED

- **Initial finding:** TraceLink source identity is an exact `source_revision_id`, while a semantic document relation normally persists across ordinary revisions of one logical document.
- **Resolution:** P8 relation source is logical governed-document Artifact; exact declaration Revision is provenance only. Later source revisions neither clone nor silently retire the relation.
- **Final status:** `RESOLVED`

### F-98 — HIGH — RESOLVED

- **Initial finding:** TraceLink has no ACTIVE/RETIRED lifecycle, optimistic version, or retirement provenance required for current semantic relation state.
- **Resolution:** Exactly one bounded `document_relations` current-state table is justified.
- **Final status:** `RESOLVED`

### F-99 — HIGH — RESOLVED

- **Initial finding:** Mapping every document relation to TraceLink HARD/SOFT/INFORMATIONAL semantics would erase distinctions such as REFERENCES, bidirectional MUST_ALIGN_WITH, SUPERSEDES, VALIDATES and GENERATED_FROM.
- **Resolution:** Blanket mapping is forbidden. TraceLink projection is deferred until binding + relation-specific semantics are independently qualified.
- **Final status:** `RESOLVED`

### F-100 — HIGH — RESOLVED

- **Initial finding:** P8 could silently choose `LOGICAL_CURRENT` or `PINNED_REVISION`, preempting DG-P9 and potentially allowing VALIDATES/GENERATED_FROM to float.
- **Resolution:** P8 excludes target binding mode and exact target revision/hash from its contract. P9 remains the sole owner of binding semantics.
- **Final status:** `RESOLVED`

### F-101 — HIGH — RESOLVED

- **Initial finding:** Introducing semantic document relations could accidentally create a second generic graph subsystem with node/type/event/projection tables parallel to PRIM-TRACE.
- **Resolution:** P8 justifies one semantic current-state table only. Existing TraceLink remains the future operational projection substrate; no node/type/event/projection table is admitted.
- **Final status:** `RESOLVED`

### F-102 — HIGH — RESOLVED

- **Initial finding:** Markdown hyperlinks, text mentions or existing TraceLinks could be treated as implicit semantic relations.
- **Resolution:** Canonical relations require explicit governed declaration. Automated analysis may propose, never silently create, a relation.
- **Final status:** `RESOLVED`

### F-103 — HIGH — RESOLVED

- **Initial finding:** A P8 `SUPERSEDES` relation could accidentally mutate DG-P7 authority ownership or P6 lifecycle before later supersession governance exists.
- **Resolution:** P8 SUPERSEDES is declaration-only. Authority/lifecycle mutation remains explicitly outside P8.
- **Final status:** `RESOLVED`

## 55. DG-P8 pre-implementation qualification checklist

- [x] exact DG-P7 final formal-close HEAD `cf143d959b338e8d77811f5b2b79789ccbbb20aa` verified.
- [x] final exact-head run `35611830804` PASS verified.
- [x] final SQLite/PostgreSQL artifact identities and digests verified.
- [x] Documentation Integrity §10 loaded.
- [x] DG-P8/DG-P9 roadmap split loaded.
- [x] `trace_links` schema inventoried.
- [x] `create_trace_link()` semantics inventoried.
- [x] `compute_impact()` TraceLink traversal semantics inventoried.
- [x] research-domain trace type registry inventoried.
- [x] TraceLink canonical relation-store model rejected.
- [x] TraceLink future projection-substrate role frozen.
- [x] logical source document identity frozen.
- [x] exact declaration revision provenance frozen.
- [x] relation ACTIVE -> RETIRED lifecycle frozen.
- [x] Proposal/Approval/Audit reuse frozen.
- [x] eight required relation types frozen.
- [x] target-kind vocabulary frozen.
- [x] direction semantics frozen.
- [x] no Markdown/TraceLink inference.
- [x] exactly one `document_relations` table justified.
- [x] no nodes/types/events/projection table.
- [x] P8/P9 binding boundary frozen.
- [x] no TraceLink projection authorized in P8.
- [x] SUPERSEDES authority/lifecycle side effects excluded.
- [x] D8-F1..D8-F20 frozen.
- [x] no DG-P9+ implementation authorized.
- [x] no DG-W3 closure authorized.
- [x] no GAC/RA/G2E authorized.
- [x] implementation has not started.

## 56. Current aggregate status after DG-P8 pre-implementation qualification

**OPEN = 0**

All findings F-01 through F-103 are resolved.

```text
DG-P7                     = FORMALLY_CLOSED
DG-P7 final closure HEAD  = cf143d959b338e8d77811f5b2b79789ccbbb20aa
DG-P7 final exact run     = 35611830804 PASS
DG-P8 authorization       = PREIMPLEMENTATION_ONLY
DG-P8 specification       = FROZEN
DG-P8 spec commit         = 211308141106481104590b3d55cdc8c19d6b6d8e
DG-P8 spec blob           = d6996951522caa061b29f94d1b1f4f579251adaa
DG-P8 dependency qualify  = PASS
DG-P8 document QA         = PASS
DG-P8 implementation      = NOT_STARTED
DG-P8 overall             = NOT_YET_PASS
DG-P9+                    = NOT_STARTED / NOT_AUTHORIZED
DG-W3                     = OPEN / NOT_EXECUTED
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```

## 57. DG-P8 implementation findings

### F-104 — MEDIUM — RESOLVED

- **Initial finding:** Initial DG-P8 run `35621370994` on `2081f730e38dc874c29335f77e441ed794fcb885` passed D8-F1..D8-F20 and the bounded P8 gate on both SQLite and PostgreSQL, but the SQLite targeted regression failed at historical D7-F20 because that test asserted that the downstream `document_relations` table must not exist.
- **Why this was stale:** The P7 invariant was "P7 must not create later-wave relation side effects." Once P8 is explicitly authorized, migration `0010` legitimately creates the table globally. Schema absence is therefore no longer equivalent to "P7 produced no side effect."
- **Resolution:** Repair commit `e784d7f56c0cfdf25ca453da48d570cd202ad0cc` changed only D7-F20. When `document_relations` exists, the test snapshots its project row count, executes P7 authority operations, and requires the count to remain unchanged. P9+/GAC table-absence assertions remain.
- **Non-rescue evidence:** DG-P8 runtime, migration, frozen specification, D8 matrix and workflow were unchanged by the repair.
- **Repair evidence:** workflow `35621561857` PASS.
- **Final status:** `RESOLVED`

## 58. DG-P8 implementation qualification checklist

- [x] implementation started from exact qualification HEAD `cf5a268b58bd9f1bb69df2a4bfeed5a2809380b1`.
- [x] frozen spec commit/blob remained `211308141106481104590b3d55cdc8c19d6b6d8e` / `d6996951522caa061b29f94d1b1f4f579251adaa`.
- [x] exactly one migration `0010_v086_dg_p8_document_relations` added.
- [x] exactly one P8 canonical table `document_relations` added.
- [x] no relation node/type/event/projection/finding table added.
- [x] `KnowledgeKernel` TraceLink runtime unchanged.
- [x] no TraceLink projection.
- [x] required relation types enforced.
- [x] required target kinds enforced.
- [x] logical source document + exact declaration revision provenance implemented.
- [x] relation ACTIVE -> RETIRED implemented.
- [x] optimistic relation retirement implemented.
- [x] Proposal/Approval/Audit reuse implemented.
- [x] exact duplicate ACTIVE relation rejected.
- [x] self-document relation rejected.
- [x] DOCUMENT target project/type integrity enforced.
- [x] no Markdown/TraceLink inference.
- [x] no DG-P9 binding fields/semantics.
- [x] VALIDATES creates no validation Evidence.
- [x] GENERATED_FROM creates no reproducibility Evidence/TraceLink.
- [x] SUPERSEDES creates no P7 authority/lifecycle side effect.
- [x] D8-F1..D8-F20 PASS on SQLite.
- [x] D8-F1..D8-F20 PASS on PostgreSQL 17.
- [x] bounded P8 gate PASS on SQLite.
- [x] bounded P8 gate PASS on PostgreSQL 17.
- [x] Knowledge/Trace/P4/P5/P6/P7 targeted regressions PASS.
- [x] full repository regression PASS.
- [x] compile PASS.
- [x] negative run `35621370994` preserved.
- [x] compatibility repair limited to historical D7-F20 regression.
- [x] qualified run `35621561857` recorded.
- [x] SQLite evidence artifact `10649881388` recorded.
- [x] PostgreSQL evidence artifact `10649322400` recorded.
- [x] DG-P9+ remain NOT_STARTED / NOT_AUTHORIZED.
- [x] DG-W3 remains OPEN / NOT_EXECUTED.
- [x] GAC remains locked until DG-W4 PASS.
- [x] committed handoff exact-head requalification PASS — run `35622268576` on `11eba1b424896b421fc4a32c8a1970dfcf6c34dc`; SQLite artifact `10650102588`; PostgreSQL artifact `10650297246`.

## 59. Current aggregate state during DG-P8 handoff

**OPEN = 0**

All findings F-01 through F-104 are resolved.

```text
DG-P7                     = FORMALLY_CLOSED
DG-P8 specification       = FROZEN
DG-P8 implementation      = QUALIFIED_PASS
DG-P8 implementation SHA  = e784d7f56c0cfdf25ca453da48d570cd202ad0cc
DG-P8 workflow            = 35621561857 PASS
DG-P8 SQLite artifact     = 10649881388
DG-P8 PostgreSQL artifact = 10649322400
DG-P8 handoff HEAD        = 11eba1b424896b421fc4a32c8a1970dfcf6c34dc
DG-P8 exact-head workflow = 35622268576 PASS
DG-P8 SQLite artifact     = 10650102588
DG-P8 PostgreSQL artifact = 10650297246
DG-P8 overall             = FORMALLY_CLOSED
DG-P9+                    = NOT_STARTED / NOT_AUTHORIZED
DG-W3                     = OPEN / NOT_EXECUTED
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```

## 60. DG-P9 pre-implementation qualification findings

### F-105 — LOW — RESOLVED

- **Initial finding:** DG-P8 was finally closed at 4a93e564adf52ae0dfdffabefaef32d431bbef6d, but the roadmap/finding snapshot still cited the earlier handoff run 35622268576 as closure evidence.
- **Resolution:** Verified final exact-head run 35622798852 PASS on the formal-close HEAD. Final SQLite artifact is 10650208254 with digest sha256:f956a6481a689fb01be862cec1c700981b7f3e289e5fa5e72c5b4bcae4580613; PostgreSQL artifact is 10649124278 with digest sha256:807c84a3188190c90db1b8b73de116575f088db2192247414422086dd222468e.
- **Final status:** RESOLVED

### F-106 — HIGH — RESOLVED

- **Initial finding:** Target binding could be modeled as a separate current-state table, splitting one semantic relation across two canonical stores.
- **Resolution:** Binding is part of DocumentRelation meaning. P9 justifies extending document_relations with target_binding_mode and target_revision_or_hash only; no binding table.
- **Final status:** RESOLVED

### F-107 — HIGH — RESOLVED

- **Initial finding:** Existing P8 rows could be silently defaulted to LOGICAL_CURRENT/PINNED_REVISION.
- **Resolution:** Migration must not backfill. NULL means legacy unbound absence and requires explicit governed binding.
- **Final status:** RESOLVED

### F-108 — HIGH — RESOLVED

- **Initial finding:** Relation types had no frozen legality matrix, allowing callers to choose semantically unsafe modes.
- **Resolution:** Freeze relation-specific binding legality matrix in DG-P9 spec.
- **Final status:** RESOLVED

### F-109 — HIGH — RESOLVED

- **Initial finding:** VALIDATES or GENERATED_FROM could float and falsely apply old evidence/provenance to a new target revision.
- **Resolution:** Both are PINNED_REVISION-only and require exact immutable target identity.
- **Final status:** RESOLVED

### F-110 — HIGH — RESOLVED

- **Initial finding:** DERIVED_FROM/SUPERSEDES could lose exact historical identity if allowed to float.
- **Resolution:** Both are PINNED_REVISION-only.
- **Final status:** RESOLVED

### F-111 — HIGH — RESOLVED

- **Initial finding:** A pinned MUST_ALIGN_WITH relation could remain aligned to history while the normative target advances.
- **Resolution:** MUST_ALIGN_WITH is LOGICAL_CURRENT-only.
- **Final status:** RESOLVED

### F-112 — HIGH — RESOLVED

- **Initial finding:** In-place rebinding could rewrite historical graph meaning.
- **Resolution:** Legacy rows may bind once; any later binding change requires retire-old + create-new.
- **Final status:** RESOLVED

### F-113 — HIGH — RESOLVED

- **Initial finding:** Arbitrary non-document tokens could be mislabeled as verified exact/current bindings.
- **Resolution:** External target bindings fail closed without an independently qualified target-kind resolver.
- **Final status:** RESOLVED

### F-114 — HIGH — RESOLVED

- **Initial finding:** LOGICAL_CURRENT resolution could be cached/persisted or consumed later without an exact snapshot, producing pseudo-pin or TOCTOU ambiguity.
- **Resolution:** Resolver returns exact Revision/content hash/Artifact-version snapshot without mutating relation; downstream consumers must freeze their own exact identity.
- **Final status:** RESOLVED

### F-115 — HIGH — RESOLVED

- **Initial finding:** P9 resolution could silently create TraceLinks, impact state, validity changes or Evidence.
- **Resolution:** P9 resolver is pure identity resolution. All propagation/evidence side effects are forbidden and deferred.
- **Final status:** RESOLVED

## 61. DG-P9 pre-implementation qualification checklist

- [x] exact DG-P8 final formal-close HEAD 4a93e564adf52ae0dfdffabefaef32d431bbef6d verified.
- [x] final exact-head run 35622798852 PASS verified.
- [x] final SQLite/PostgreSQL artifacts/digests verified.
- [x] governing Documentation Integrity §10 loaded.
- [x] P8 canonical relation runtime/schema inventoried.
- [x] existing TraceLink/impact semantics inventoried.
- [x] LOGICAL_CURRENT semantics frozen.
- [x] PINNED_REVISION semantics frozen.
- [x] per-relation legality matrix frozen.
- [x] VALIDATES pinned-only.
- [x] GENERATED_FROM pinned-only.
- [x] DERIVED_FROM pinned-only.
- [x] SUPERSEDES pinned-only.
- [x] MUST_ALIGN_WITH current-only.
- [x] DEPENDS_ON/REFERENCES/IMPLEMENTS dual-mode.
- [x] no legacy binding default/backfill.
- [x] one-time legacy bind + no-rebind rule frozen.
- [x] native DOCUMENT current/pinned resolver contract frozen.
- [x] external target resolver fail-closed boundary frozen.
- [x] no new P9 table.
- [x] future schema extension limited to target_binding_mode + target_revision_or_hash on document_relations.
- [x] no TraceLink schema change.
- [x] no binding cache.
- [x] no TraceLink projection.
- [x] no impact/validity/Evidence side effects.
- [x] D9-F1..D9-F20 frozen.
- [x] no DG-P10+ implementation authorized.
- [x] no DG-W3 closure authorized.
- [x] no GAC/RA/G2E authorized.
- [x] implementation has not started.

## 62. Current aggregate status after DG-P9 pre-implementation qualification

**OPEN = 0**

All findings F-01 through F-115 are resolved.

~~~text
DG-P8                     = FORMALLY_CLOSED
DG-P8 final closure HEAD  = 4a93e564adf52ae0dfdffabefaef32d431bbef6d
DG-P8 final exact run     = 35622798852 PASS
DG-P9 authorization       = PREIMPLEMENTATION_ONLY
DG-P9 specification       = FROZEN
DG-P9 spec commit         = 1a9f8737e36392c8a8db49b93c9371ceee16085f
DG-P9 spec blob           = 73e1d7c8c01ea954af2a65e1df1942b4f95738f3
DG-P9 dependency qualify  = PASS
DG-P9 document QA         = PASS
DG-P9 implementation      = NOT_STARTED
DG-P9 overall             = NOT_YET_PASS
DG-P10+                   = NOT_STARTED / NOT_AUTHORIZED
DG-W3                     = OPEN / NOT_EXECUTED
GAC                       = LOCKED_UNTIL_DG-W4_PASS
~~~


## 63. DG-P9 implementation compatibility finding

### F-116 — MEDIUM — RESOLVED

- **Initial finding:** Historical P8 fixtures D8-F13 and D8-F16 asserted that P9 binding columns did not exist in returned relation rows. That assertion was intentionally true before DG-P9 but is phase-bound and would make the authorized additive migration 0011 impossible while not protecting the durable P8 semantic boundary.
- **Resolution:** Preserve the historical P8 invariants instead: pre-P9 external and VALIDATES rows remain representable as legacy rows with NULL binding; they do not create Evidence or TraceLinks; canonical DocumentRelation and TraceLink state remain distinct. P8 regression fixtures were updated only at those phase-bound assertions and all D9-F1..D9-F20 remain frozen.
- **Final status:** RESOLVED

**OPEN = 0**


## 64. DG-P9 implementation qualification checklist

- [x] implementation started from exact qualification HEAD `52ae1ebded1f9a942cee55d6d2ce061b5bcb8290`.
- [x] frozen spec commit/blob remained `1a9f8737e36392c8a8db49b93c9371ceee16085f` / `73e1d7c8c01ea954af2a65e1df1942b4f95738f3`.
- [x] exactly one migration `0011_v086_dg_p9_relation_binding` added.
- [x] migration extends `document_relations` only.
- [x] no new P9 binding/cache/projection table added.
- [x] legacy P8 rows retain NULL binding; no automatic backfill/default.
- [x] new relation declaration requires explicit legal atomic binding.
- [x] one-time `BIND_DOCUMENT_RELATION` implemented with Proposal/Approval/Audit.
- [x] binding mutation uses optimistic `relation.version`.
- [x] rebind rejected; retire-old + create-new remains the semantic change path.
- [x] frozen relation-type legality matrix enforced.
- [x] pinned DOCUMENT Revision ownership enforced.
- [x] LOGICAL_CURRENT DOCUMENT resolver returns exact read snapshot.
- [x] historical pinned Revision remains resolvable after target advances.
- [x] VALIDATES never floats.
- [x] GENERATED_FROM requires exact verified identity.
- [x] unsupported external target resolver fails closed.
- [x] no binding-resolution cache.
- [x] no TraceLink projection.
- [x] no impact/validity/Evidence/finding/authority/lifecycle side effects.
- [x] D9-F1..D9-F20 PASS on SQLite.
- [x] D9-F1..D9-F20 PASS on PostgreSQL 17.
- [x] bounded DG-P9 gate PASS on SQLite and PostgreSQL 17.
- [x] P8/Knowledge/Trace/P4/P5/P6/P7 targeted regressions PASS.
- [x] full repository regression PASS.
- [x] compile PASS.
- [x] compatibility finding F-116 resolved without changing frozen D9 semantics.
- [x] qualified run `35628998000` recorded.
- [x] SQLite evidence artifact `10653386409`, digest `sha256:651c9a59f77d83176cbc452d39a9beebf17c27e2390ef83a96aee85ed29ea160`.
- [x] PostgreSQL evidence artifact `10653461137`, digest `sha256:aff7462c949ce6645bd0edc4ea130cbce884ac424a72234fc79ad8b9dc7b8ae4`.
- [x] DG-P10+ remain NOT_STARTED / NOT_AUTHORIZED.
- [x] DG-W3 remains OPEN / NOT_EXECUTED.
- [x] GAC remains locked until DG-W4 PASS.
- [x] committed handoff exact-head requalification PASS — run `35629583197` on `5f6ecece5bbb15c36b00a35c7a4dbb6b340e0e4e`; SQLite artifact `10653762329`; PostgreSQL artifact `10653647093`.

## 65. Current aggregate state during DG-P9 handoff

**OPEN = 0**

All findings F-01 through F-116 are resolved.

```text
DG-P8                     = FORMALLY_CLOSED
DG-P9 specification       = FROZEN
DG-P9 implementation      = QUALIFIED_PASS
DG-P9 implementation SHA  = 9ffd64a1e9b98ea307ed8f9682b88e26570dc208
DG-P9 workflow            = 35628998000 PASS
DG-P9 SQLite artifact     = 10653386409
DG-P9 PostgreSQL artifact = 10653461137
DG-P9 handoff HEAD        = 5f6ecece5bbb15c36b00a35c7a4dbb6b340e0e4e
DG-P9 exact-head workflow = 35629583197 PASS
DG-P9 SQLite artifact     = 10653762329
DG-P9 PostgreSQL artifact = 10653647093
DG-P9 overall             = FORMALLY_CLOSED
DG-P10+                   = NOT_STARTED / NOT_AUTHORIZED
DG-W3                     = OPEN / NOT_EXECUTED
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```


## 66. DG-P10 pre-implementation qualification findings

### F-117 — LOW — RESOLVED

- **Initial finding:** The authorization-frontier prose still described DG-P9 implementation as NOT_STARTED after DG-P9 had already been formally closed and final closure HEAD `7a081bd8f1f2218859963e304230a8904f56a6eb` passed workflow `35629863163`.
- **Resolution:** DG-P10 binds to the actual final DG-P9 closure HEAD/run/artifacts and the roadmap frontier is corrected before promoting DG-P10 pre-implementation qualification.
- **Final status:** RESOLVED

### F-118 — HIGH — RESOLVED

- **Initial finding:** The roadmap listed DG-P10 HARD dependencies as DG-P4 + DG-P7 only, while §13 requires QA escalation and P5 owns exact QA/finding semantics including `CHANGE_CLASS_MISMATCH`.
- **Resolution:** DG-P5 is added as a DG-P10 HARD dependency. P10 reuses P5 semantics and does not create a second finding lifecycle.
- **Final status:** RESOLVED

### F-119 — HIGH — RESOLVED

- **Initial finding:** Current `DocumentFacade.revise_document()` resolves a candidate and immediately creates the new Revision, leaving no classification gate before authoritative current-state mutation.
- **Resolution:** P10 freezes a pre-commit invariant: resolve exact candidate -> classify/review/approval -> recheck exact base/version -> only then create Revision.
- **Final status:** RESOLVED

### F-120 — HIGH — RESOLVED

- **Initial finding:** §13 says the strongest governance class wins but does not define deterministic ordering.
- **Resolution:** Freeze `EDITORIAL < CLARIFICATION < NORMATIVE < STRUCTURAL < SUPERSESSION` as the governance escalation rank.
- **Final status:** RESOLVED

### F-121 — HIGH — RESOLVED

- **Initial finding:** A low declared class could be treated as clean merely because semantic review failed to produce an escalation.
- **Resolution:** Freeze attributable QA review refs plus `EVALUATED | NOT_EVALUATED`; NOT_EVALUATED cannot authorize Revision commit.
- **Final status:** RESOLVED

### F-122 — HIGH — RESOLVED

- **Initial finding:** The conceptual DocumentRevision change class has no current dedicated revision column, creating pressure for a parallel P10 table or post-hoc mutable label.
- **Resolution:** Classification reuses immutable PRIM-EVIDENCE; new revisions may bind `effective_change_class + classification_evidence_ref` inside immutable payload metadata. No table, migration or historical backfill.
- **Final status:** RESOLVED

### F-123 — HIGH — RESOLVED

- **Initial finding:** §14 lists document change policies but no qualified persisted document-level `change_policy` currently exists.
- **Resolution:** P10 does not claim full §14 enforcement. It freezes a conservative minimum requiring human Approval for NORMATIVE/STRUCTURAL/SUPERSESSION; missing policy metadata cannot relax governance. P15/P16 retain their later responsibilities.
- **Final status:** RESOLVED

### F-124 — HIGH — RESOLVED

- **Initial finding:** QA escalation could later be erased by agent downgrade or in-place rewrite.
- **Resolution:** Agent/proposer classification is monotonic. Any lower human review result requires exact-subject Approval and new immutable Evidence referencing the prior classification.
- **Final status:** RESOLVED

### F-125 — HIGH — RESOLVED

- **Initial finding:** STRUCTURAL/SUPERSESSION labels could be mistaken as authorization to mutate authority, relations, lifecycle or validity.
- **Resolution:** P10 classification has zero such mutation side effects. Execution remains later explicitly authorized work.
- **Final status:** RESOLVED

### F-126 — HIGH — RESOLVED

- **Initial finding:** Implementing change-set-wide effective class in P10 would preempt DG-P11.
- **Resolution:** P10 classifies exactly one document candidate. DG-P11 owns multi-document frozen scope and aggregate effective class.
- **Final status:** RESOLVED

### F-127 — MEDIUM — RESOLVED

- **Initial finding:** Initial document registration has no prior governed base Revision, so forcing it into the five edit classes would invent unsupported semantics.
- **Resolution:** P10 applies to revision of an existing governed document; initial registration remains outside this edit-classification contract.
- **Final status:** RESOLVED

### F-128 — HIGH — RESOLVED

- **Initial finding:** Diff-size heuristics could allow small normative changes to masquerade as EDITORIAL/CLARIFICATION.
- **Resolution:** Byte/line/token/file size is forbidden as a class-lowering signal.
- **Final status:** RESOLVED

### F-129 — HIGH — RESOLVED

- **Initial finding:** A P5 `CHANGE_CLASS_MISMATCH` finding could be mistaken for the canonical change classification record.
- **Resolution:** P5 remains finding/remediation state; P10 canonical classification is immutable `document_change_classification` Evidence.
- **Final status:** RESOLVED

### F-130 — HIGH — RESOLVED

- **Initial finding:** Classification Evidence could be replayed after the base Revision, Artifact version or proposed source changes.
- **Resolution:** Classification binds exact base/version/candidate identity and must be rechecked immediately before commit. Stale classification fails closed.
- **Final status:** RESOLVED

## 67. DG-P10 pre-implementation qualification checklist

- [x] exact DG-P9 final closure HEAD `7a081bd8f1f2218859963e304230a8904f56a6eb` verified.
- [x] final DG-P9 exact-head run `35629863163` PASS verified.
- [x] final DG-P9 SQLite/PostgreSQL artifact identities and digests verified.
- [x] Documentation Integrity §§13-14 loaded.
- [x] DG-P4 exact identity/runtime path inventoried.
- [x] DG-P5 QA/finding semantics inventoried.
- [x] DG-P7 authority semantics inventoried.
- [x] P5 added as DG-P10 HARD dependency.
- [x] five-class vocabulary frozen.
- [x] deterministic governance rank frozen.
- [x] one-document P10 scope frozen.
- [x] exact base Revision + candidate source subject frozen.
- [x] pre-commit classification invariant frozen.
- [x] mandatory explicit declared class frozen.
- [x] structured trigger mapping frozen.
- [x] CLARIFICATION/NORMATIVE ambiguity fails conservatively to NORMATIVE.
- [x] attributable semantic review frozen.
- [x] NOT_EVALUATED cannot authorize commit.
- [x] QA escalation monotonic.
- [x] agent unilateral downgrade forbidden.
- [x] governed human replacement bounded.
- [x] diff-size downgrade heuristics forbidden.
- [x] conservative NORMATIVE+ Approval minimum frozen.
- [x] full §14 policy-enforcement overclaim rejected.
- [x] `document_change_classification` PRIM-EVIDENCE reuse frozen.
- [x] no P10 table.
- [x] no schema migration.
- [x] no historical revision backfill.
- [x] new Revision payload binding limited to classification refs/class for exact candidate.
- [x] P5 finding lifecycle remains canonical.
- [x] STRUCTURAL/SUPERSESSION zero mutation side effects.
- [x] multi-document effective class deferred to DG-P11.
- [x] D10-F1..D10-F20 frozen.
- [x] document QA PASS.
- [x] implementation has not started.
- [x] DG-P11+ remain NOT_STARTED / NOT_AUTHORIZED.
- [x] DG-W3 remains OPEN / NOT_EXECUTED.
- [x] GAC remains locked until DG-W4 PASS.

## 68. Current aggregate status after DG-P10 pre-implementation qualification

**OPEN = 0**

All findings F-01 through F-130 are resolved.

```text
DG-P9                     = FORMALLY_CLOSED
DG-P9 final closure HEAD  = 7a081bd8f1f2218859963e304230a8904f56a6eb
DG-P9 final exact run     = 35629863163 PASS
DG-P10 authorization      = PREIMPLEMENTATION_ONLY
DG-P10 specification      = FROZEN
DG-P10 spec commit        = f5d8544758cfdaeb1867c1fa9f72dab346c387c7
DG-P10 spec blob          = 56a99967ebe815c56341b1668c3acb1a1517d589
DG-P10 dependency qualify = PASS
DG-P10 document QA        = PASS
DG-P10 implementation     = NOT_STARTED
DG-P10 overall            = NOT_YET_PASS
DG-P11+                   = NOT_STARTED / NOT_AUTHORIZED
DG-W3                     = OPEN / NOT_EXECUTED
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```


## 69. DG-P10 Amendment 1 findings

### F-131 — CRITICAL — RESOLVED
- **Finding:** Reusing AUTO/HUMAN_APPROVE for document mutation could silently broaden v0.8.2 recovery AUTO authority.
- **Resolution:** Reuse only the persisted effective mode value/snapshot. Recovery semantics remain unchanged; document mutation uses a separate decision matrix.
- **Final status:** RESOLVED

### F-132 — HIGH — RESOLVED
- **Finding:** The initial P10 NORMATIVE+ unconditional human-approval floor conflicts the authorized model where AUTO owns phase-generated documents.
- **Resolution:** Change class and mutation authority are orthogonal. Authority is decided by role/state + active PhaseExecution mode + ownership + stronger locks.
- **Final status:** RESOLVED

### F-133 — HIGH — RESOLVED
- **Finding:** Exact candidate commit/blob cannot be required before GWF commits agent-generated content.
- **Resolution:** Freeze exact base identity plus proposed path/content SHA-256/version/archive path; resolve exact resulting commit/blob post-write.
- **Final status:** RESOLVED

### F-134 — HIGH — RESOLVED
- **Finding:** AUTO could become project-global without explicit document ownership.
- **Resolution:** AUTO requires matching enrolled owner phase/workunit; unknown/different ownership requires human approval.
- **Final status:** RESOLVED

### F-135 — CRITICAL — RESOLVED
- **Finding:** AUTO could bypass frozen governance.
- **Resolution:** GOV/FROZEN always returns BLOCK_REQUIRES_EXPLICIT_USER_AUTHORIZATION regardless AUTO/HUMAN_APPROVE.
- **Final status:** RESOLVED

### F-136 — HIGH — RESOLVED
- **Finding:** Physical archive/version files could be mistaken for canonical document identity.
- **Resolution:** Artifact/Revision remains canonical; paths/archive are human-readable source lineage.
- **Final status:** RESOLVED

### F-137 — HIGH — RESOLVED
- **Finding:** Implementing CREATE archive + CREATE vN+1 + DELETE old in P10 would preempt DG-P11.
- **Resolution:** P10 computes/freeze-checks the lineage plan only; DG-P11 owns concrete DocumentChangeSet execution.
- **Final status:** RESOLVED

### F-138 — MEDIUM — RESOLVED
- **Finding:** Existing flat-layout documents could be silently migrated into the new hierarchy.
- **Resolution:** Legacy documents require explicit later enrollment/migration; absence of enrollment never grants AUTO.
- **Final status:** RESOLVED

### F-139 — HIGH — RESOLVED
- **Finding:** Re-resolving mutable mode configuration during an edit could change authority mid-phase.
- **Resolution:** The running PhaseExecution's persisted phase_execution_protocols.recovery_mode snapshot is the authoritative document-mode input.
- **Final status:** RESOLVED

### F-140 — HIGH — RESOLVED
- **Finding:** A caller boolean could masquerade as explicit user authorization for GOV/FROZEN.
- **Resolution:** Caller assertions cannot unlock GOV/FROZEN; future unlock requires attributable exact-subject human/user authorization.
- **Final status:** RESOLVED

### F-141 — HIGH — RESOLVED
- **Finding:** Archive overwrite or in-place correction would rewrite historical source lineage.
- **Resolution:** Archive paths are immutable/no-overwrite; corrections are new amendment/correction records.
- **Final status:** RESOLVED

## 70. DG-P10 Amendment 1 QA state

**OPEN = 0**

All findings F-01 through F-141 are resolved.

```text
DG-P9                     = FORMALLY_CLOSED
DG-P10 original spec      = SUPERSEDED_BY_AMENDMENT_1
DG-P10 amended spec       = FROZEN
DG-P10 amended spec HEAD  = 54ca635bcb322902a28f4a987af19c37e14b59ae
DG-P10 amended spec blob  = 2aeec0ff251567e784372ffb700d11c37fa9a037
Documentation §14 blob    = c1b863784b3ca4bbada7020017818c2340fe5d3b
DG-P10 amendment QA       = PASS
serious unresolved impact = NONE
DG-P10 implementation     = AUTHORIZED_BOUNDED / NOT_STARTED
DG-P11+                   = NOT_STARTED / NOT_AUTHORIZED
DG-W3                     = OPEN / NOT_EXECUTED
GAC                       = LOCKED_UNTIL_DG-W4_PASS
```
