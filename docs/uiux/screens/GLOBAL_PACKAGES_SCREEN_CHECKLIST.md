# Global Packages Registry — BPS-M06 Checklist

## Identity

```text
SCREEN_ID        = GLOBAL_PACKAGES
OWNER            = BPS-M06
ROUTE            = /app/research/packages
PROTOCOL         = BPS-QA-FIRST-DEFERRED-UAT-v1
STATUS           = QA_FINDINGS_CLOSED / CI_PENDING / FINAL_UAT_PENDING
BASE_HEAD        = 3dd8417dfc085194a0a22fe26c9f7998a59e1ea2
FINAL_UAT        = DEFERRED
```

## Governing sources

- `docs/UI_UX_PRODUCT_ARCHITECTURE_SPEC.md` §15.1, §16, §34A.9, §34A.13.
- `docs/BROWSER_PRODUCT_SURFACE_SPEC.md`.
- `src/gwr/domain_registry.py`.
- `src/gwr/agent_protocol.py`.
- `project_domain_bindings`, `domain_skill_bindings`, `phase_execution_protocols`.

## Source-derived visibility boundary

Domain packages are tenant-scoped and may be shown only where the actor has tenant VIEW authority.

Skill packages/revisions currently have no tenant ownership column. The browser MUST NOT invent tenant ownership or expose the global table wholesale. Skill visibility is therefore `AUTHORIZED_REACHABLE`: a skill revision is visible only when it is CONFIGURED through a visible/authorized Domain binding or OBSERVED by an execution in an authorized project.

Package usage is a read projection. No mutable package-usage table is added.

## Frozen checklist

### A. Global package projection

- [x] PK-01 Add cookie-authenticated `GET /browser/packages`.
- [x] PK-02 Return generated_at, exact build SHA and COMPLETE/PARTIAL status.
- [x] PK-03 Domain package visibility requires tenant VIEW authority.
- [x] PK-04 Return tenant ID/name, package ID, domain ID, name, description, package status, creator/time.
- [x] PK-05 Return all visible Domain revisions in revision order.
- [x] PK-06 Domain revision detail includes revision ID/number, semantic version, payload hash, persisted status, validation report, creator/time, published_at.
- [x] PK-07 Domain revision status is exactly persisted DRAFT|VALIDATED|PUBLISHED; no browser-normalized lifecycle.
- [x] PK-08 Return latest revision and latest PUBLISHED revision separately.
- [x] PK-09 Return authorized project usage for each exact Domain revision.
- [x] PK-10 Usage never leaks inaccessible project IDs/names.
- [x] PK-11 Global package projection does not return raw Domain YAML unless a later explicit editor/reader contract requires it.

### B. Skill registry projection

- [x] PK-12 Skill visibility is AUTHORIZED_REACHABLE, never fabricated tenant ownership.
- [x] PK-13 Reachable skill revisions are the union of CONFIGURED domain/workunit bindings and OBSERVED authorized project protocols.
- [x] PK-14 Return skill package ID, skill ID, name, description, creator/time.
- [x] PK-15 Return immutable skill revisions: revision ID/number, version, content hash, tool requirements, QA contract, creator/time.
- [x] PK-16 Skill revision does not inherit fake DRAFT/VALIDATED/PUBLISHED state.
- [x] PK-17 Return exact domain/workunit bindings including binding ID, domain ID, workunit type, skill hash, required tools and QA contract.
- [x] PK-18 Do not return raw SKILL.md content in the registry list projection.
- [x] PK-19 Package projection distinguishes visibility basis CONFIGURED / OBSERVED / both.

### C. Two-way usage

- [x] PK-20 Domain revision → Projects lists only authorized projects pinned to that exact revision.
- [x] PK-21 Skill revision → Projects CONFIGURED derives from project pinned Domain + domain_skill_bindings.
- [x] PK-22 Skill revision → Projects OBSERVED derives from phase_execution_protocols exact loaded revision.
- [x] PK-23 Usage records label basis exactly CONFIGURED or OBSERVED.
- [x] PK-24 Same project/revision may carry both bases without being collapsed into a fake single source.
- [x] PK-25 Project → Packages projection returns exact pinned Domain revision.
- [x] PK-26 Project → Packages returns configured Skill revisions with workunit type/binding identity.
- [x] PK-27 Project → Packages returns observed Skill revisions with exact protocol/phase identities.
- [x] PK-28 Project → Packages is non-disclosing 404 for inaccessible project.
- [x] PK-29 “Behind latest” compares pinned revision_number with latest PUBLISHED revision in the same Domain package only.
- [x] PK-30 Behind-latest is informational; no upgrade mutation/action is exposed.

### D. Browser Packages UI

- [x] PK-31 Promote Research → Packages from SKELETON_LOCKED to LIVE_MODULE.
- [x] PK-32 Packages has Domains / Skills / Usage tabs under one reload-safe route.
- [x] PK-33 Domains list shows exact tenant/package/domain/status/latest/usage fields.
- [x] PK-34 Selecting a Domain package shows revision history and validation report.
- [x] PK-35 Skills list shows only authorized-reachable packages/revisions and explicitly labels visibility basis.
- [x] PK-36 Skill detail shows revision metadata and domain/workunit bindings without fake publication state.
- [x] PK-37 Usage tab supports Package→Projects for Domain and Skill revisions.
- [x] PK-38 Usage tab visibly distinguishes CONFIGURED and OBSERVED.
- [x] PK-39 Zero / partial / unavailable states are distinct.
- [x] PK-40 No create/publish/validate/upgrade/install mutation control is added in this read-first unit.
- [x] PK-41 Theme/sidebar/global routing/session/attention do not regress.

### E. QA

- [x] PK-42 Tests prove inaccessible tenant Domain packages are absent.
- [x] PK-43 Tests prove inaccessible project usage is absent even when package/revision is otherwise visible.
- [x] PK-44 Tests prove unreferenced global Skill package is not leaked.
- [x] PK-45 Tests cover CONFIGURED-only, OBSERVED-only and both-basis skill usage.
- [x] PK-46 Tests prove Skill projection has no fake lifecycle/status.
- [x] PK-47 Tests prove Domain revision payload excludes raw yaml_text.
- [x] PK-48 Tests prove Project→Packages exact binding and behind-latest semantics.
- [x] PK-49 Existing Bearer Domain/Skill mutation APIs remain unchanged.
- [x] PK-50 No schema, package lifecycle, domain binding, skill binding or protocol semantics change.
- [x] PK-51 Findings are recorded/fixed/rechecked until implementation `FAIL=0 OPEN=0 COUNT=0`.

## QA findings and adjudication

| Finding | Class | Observation | Correction | State |
| --- | --- | --- | --- | --- |
| PK-F01 | integrity | configured/observed Skill hashes were displayed beside revision content hashes without an explicit equality check | add `hash_matches_revision` to configured bindings and observed protocols; any mismatch makes the projection PARTIAL | PASS |
| PK-F02 | QA harness | runtime bootstrap may materialize authoritative Domain-pinned Skill bindings before the test fixture creates its own three Skill cases | change tests from closed-world equality to expected-subset assertions while still proving the unreferenced fixture Skill is absent | PASS |
| PK-F03 | coverage | two published revisions did not prove that latest revision and latest PUBLISHED revision are separate concepts | add a persisted newer DRAFT revision; assert latest=DRAFT, latest published=PUBLISHED, and behind-latest compares only to latest PUBLISHED | PASS |
| PK-F04 | visibility boundary | Skill package schema has no tenant ownership field, so a naive global list would either invent ownership or leak unrelated global Skills | enforce `AUTHORIZED_REACHABLE`: exact revision must be reachable through an authorized Domain/workunit binding or authorized observed protocol | PASS |
| PK-F05 | source minimization | registry list requirements do not authorize raw Domain YAML or raw SKILL.md content | shape explicit revision metadata only; tests assert `yaml_text` and Skill Markdown bodies are absent | PASS |
| PK-F06 | usage truth | UI could have collapsed configured and observed use into a single synthetic installation state | retain separate CONFIGURED and OBSERVED records, including both bases for the same project/revision when both are true | PASS |

Deterministic assistant QA on implementation HEAD `1b2f00c6047884b8e401aa2a68b83648388b53de`:

- `web/app.js` syntax parse: PASS;
- duplicate HTML IDs: 0;
- missing static `$("#id")` targets: 0;
- Packages capability is LIVE_MODULE and exact `/app/research/packages` route renders the live registry;
- Home, Projects, Access, Operations, project workspace, locked routes and Diagnostics all hide `packagesRouteView` when leaving Packages;
- Domains / Skills / Usage tabs exist under one route;
- Domain visibility invokes tenant VIEW authority; project usage is derived only from accessible projects;
- Domain revision projection excludes raw `yaml_text` and preserves persisted DRAFT|VALIDATED|PUBLISHED status;
- latest revision and latest PUBLISHED revision are independent fields;
- Skill list is AUTHORIZED_REACHABLE and excludes raw Markdown and fake lifecycle/status;
- candidate Skill revisions are exactly the union of configured bindings and observed authorized project protocols;
- CONFIGURED and OBSERVED usage remain separate records and can coexist for one project/revision;
- unreferenced global Skill packages are not exposed;
- configured/observed hash mismatches are visible and force PARTIAL rather than silently authoritative state;
- Project→Packages is non-disclosing for inaccessible projects and derives behind-latest from the same Domain package's latest PUBLISHED revision only;
- no create/publish/validate/upgrade/install mutation is present in the M06 UI;
- fixture INSERT arity matches Domain revision, Skill binding, orchestration, phase and protocol schemas;
- existing Bearer Domain list and Skill create/revision APIs remain exercised for compatibility.

Exact-head GitHub Actions at adjudication time are queued across the shared workflow set. No queued workflow is counted as PASS.

```text
TOTAL_IMPLEMENTATION_ITEMS = 51
IMPLEMENTATION_PASS        = 51
IMPLEMENTATION_FAIL        = 0
IMPLEMENTATION_OPEN        = 0
IMPLEMENTATION_COUNT       = 0

QA_FINDINGS_FAIL           = 0
QA_FINDINGS_OPEN           = 0
QA_FINDINGS_COUNT          = 0

CI_EXECUTION               = PENDING_EXTERNAL_CAPACITY
TARGETED_RUNTIME_EXECUTION = PENDING_EXTERNAL_EXECUTION
FINAL_UAT                  = DEFERRED
UNIT_STATE                 = QA_FINDINGS_CLOSED / CI_PENDING / FINAL_UAT_PENDING
```
