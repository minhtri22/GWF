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
