# Global Packages Registry — BPS-M06 Checklist

## Identity

```text
SCREEN_ID        = GLOBAL_PACKAGES
OWNER            = BPS-M06
ROUTE            = /app/research/packages
PROTOCOL         = BPS-QA-FIRST-DEFERRED-UAT-v1
STATUS           = CHECKLIST_FROZEN / IMPLEMENTATION_PENDING
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

- [ ] PK-01 Add cookie-authenticated `GET /browser/packages`.
- [ ] PK-02 Return generated_at, exact build SHA and COMPLETE/PARTIAL status.
- [ ] PK-03 Domain package visibility requires tenant VIEW authority.
- [ ] PK-04 Return tenant ID/name, package ID, domain ID, name, description, package status, creator/time.
- [ ] PK-05 Return all visible Domain revisions in revision order.
- [ ] PK-06 Domain revision detail includes revision ID/number, semantic version, payload hash, persisted status, validation report, creator/time, published_at.
- [ ] PK-07 Domain revision status is exactly persisted DRAFT|VALIDATED|PUBLISHED; no browser-normalized lifecycle.
- [ ] PK-08 Return latest revision and latest PUBLISHED revision separately.
- [ ] PK-09 Return authorized project usage for each exact Domain revision.
- [ ] PK-10 Usage never leaks inaccessible project IDs/names.
- [ ] PK-11 Global package projection does not return raw Domain YAML unless a later explicit editor/reader contract requires it.

### B. Skill registry projection

- [ ] PK-12 Skill visibility is AUTHORIZED_REACHABLE, never fabricated tenant ownership.
- [ ] PK-13 Reachable skill revisions are the union of CONFIGURED domain/workunit bindings and OBSERVED authorized project protocols.
- [ ] PK-14 Return skill package ID, skill ID, name, description, creator/time.
- [ ] PK-15 Return immutable skill revisions: revision ID/number, version, content hash, tool requirements, QA contract, creator/time.
- [ ] PK-16 Skill revision does not inherit fake DRAFT/VALIDATED/PUBLISHED state.
- [ ] PK-17 Return exact domain/workunit bindings including binding ID, domain ID, workunit type, skill hash, required tools and QA contract.
- [ ] PK-18 Do not return raw SKILL.md content in the registry list projection.
- [ ] PK-19 Package projection distinguishes visibility basis CONFIGURED / OBSERVED / both.

### C. Two-way usage

- [ ] PK-20 Domain revision → Projects lists only authorized projects pinned to that exact revision.
- [ ] PK-21 Skill revision → Projects CONFIGURED derives from project pinned Domain + domain_skill_bindings.
- [ ] PK-22 Skill revision → Projects OBSERVED derives from phase_execution_protocols exact loaded revision.
- [ ] PK-23 Usage records label basis exactly CONFIGURED or OBSERVED.
- [ ] PK-24 Same project/revision may carry both bases without being collapsed into a fake single source.
- [ ] PK-25 Project → Packages projection returns exact pinned Domain revision.
- [ ] PK-26 Project → Packages returns configured Skill revisions with workunit type/binding identity.
- [ ] PK-27 Project → Packages returns observed Skill revisions with exact protocol/phase identities.
- [ ] PK-28 Project → Packages is non-disclosing 404 for inaccessible project.
- [ ] PK-29 “Behind latest” compares pinned revision_number with latest PUBLISHED revision in the same Domain package only.
- [ ] PK-30 Behind-latest is informational; no upgrade mutation/action is exposed.

### D. Browser Packages UI

- [ ] PK-31 Promote Research → Packages from SKELETON_LOCKED to LIVE_MODULE.
- [ ] PK-32 Packages has Domains / Skills / Usage tabs under one reload-safe route.
- [ ] PK-33 Domains list shows exact tenant/package/domain/status/latest/usage fields.
- [ ] PK-34 Selecting a Domain package shows revision history and validation report.
- [ ] PK-35 Skills list shows only authorized-reachable packages/revisions and explicitly labels visibility basis.
- [ ] PK-36 Skill detail shows revision metadata and domain/workunit bindings without fake publication state.
- [ ] PK-37 Usage tab supports Package→Projects for Domain and Skill revisions.
- [ ] PK-38 Usage tab visibly distinguishes CONFIGURED and OBSERVED.
- [ ] PK-39 Zero / partial / unavailable states are distinct.
- [ ] PK-40 No create/publish/validate/upgrade/install mutation control is added in this read-first unit.
- [ ] PK-41 Theme/sidebar/global routing/session/attention do not regress.

### E. QA

- [ ] PK-42 Tests prove inaccessible tenant Domain packages are absent.
- [ ] PK-43 Tests prove inaccessible project usage is absent even when package/revision is otherwise visible.
- [ ] PK-44 Tests prove unreferenced global Skill package is not leaked.
- [ ] PK-45 Tests cover CONFIGURED-only, OBSERVED-only and both-basis skill usage.
- [ ] PK-46 Tests prove Skill projection has no fake lifecycle/status.
- [ ] PK-47 Tests prove Domain revision payload excludes raw yaml_text.
- [ ] PK-48 Tests prove Project→Packages exact binding and behind-latest semantics.
- [ ] PK-49 Existing Bearer Domain/Skill mutation APIs remain unchanged.
- [ ] PK-50 No schema, package lifecycle, domain binding, skill binding or protocol semantics change.
- [ ] PK-51 Findings are recorded/fixed/rechecked until implementation `FAIL=0 OPEN=0 COUNT=0`.

## Initial count

```text
TOTAL = 51
PASS  = 0
FAIL  = 0
OPEN  = 51
COUNT = 51
```
