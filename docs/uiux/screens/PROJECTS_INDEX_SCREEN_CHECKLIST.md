# Projects Index Screen Checklist — BPS Fast Lane

## Identity

```text
SCREEN_ID        = PROJECTS_INDEX
OWNER            = BPS-M02
ROUTE            = /app/projects
PROTOCOL         = BPS-SCREEN-FAST-LANE-v1
STATUS           = SELF_QA_PASS / USER_UAT_PENDING
BASE_HEAD        = d35c8d498e378784227d9f454fb186885213a7b0
```

## Governing sources reread before implementation

- `docs/BPS_SCREEN_FAST_LANE.md` — one-screen loop and strict-boundary rules.
- `docs/UI_UX_PRODUCT_ARCHITECTURE_SPEC.md`:
  - §2.2 project context;
  - §2.3 browser projection / no second system of record;
  - §2.5 exact identity;
  - §6 Projects index;
  - §34A.2 deterministic product terminology.
- `docs/BROWSER_PRODUCT_SURFACE_SPEC.md`:
  - global Projects placement;
  - identity/tenancy/workspace visibility and authorization requirements.
- `docs/UI_UX_QA.md` — Projects is DIRECT_UI.
- `docs/uiux/approved/UI_VISUAL_BASELINE_MANIFEST.md` — project-centered professional/compact workspace, exact provenance without metadata-console overload.
- Runtime/API code reread:
  - `src/gwr/tenancy.py`;
  - `src/gwr/project_governance.py`;
  - `src/gwr/domain_registry.py`;
  - `src/gwr/product.py`;
  - `src/gwr/api.py`.

## Scope decision

This screen implements the **read-only Projects index (§6.1)**.

The same architecture document also specifies **Project creation (§6.2)**, but creation is an authoritative mutation and its specified destination is Project Overview, which is not yet the current screen. Under `BPS-SCREEN-FAST-LANE-v1`, the Projects index must not silently add that mutation. Therefore this screen:

- does not expose a fake or partially wired Create Project action;
- does not change project lifecycle, membership, domain binding, or authority;
- does not implement Project Overview;
- records Project creation as a separate later bounded/strict action surface rather than pretending §6.2 is complete.

If implementing this index unexpectedly requires a new mutation, schema change, authority/security change, or qualified API semantic change, stop Fast Lane before that mutation.

## Frozen implementation checklist

### A. Authorized Projects projection

- [x] PI-01 Add one authenticated read-only browser Projects projection; frontend does not query the database directly.
- [x] PI-02 Projection owns no authoritative state and performs no mutation.
- [x] PI-03 Return only projects visible to the authenticated actor.
- [x] PI-04 Return a complete-query status plus generated timestamp/build identity so zero results cannot masquerade as unavailable data.
- [x] PI-05 Aggregate index fields server-side; do not create browser N+1 fan-out over project detail APIs.

### B. Required project identity and scope

- [x] PI-06 Show project Name.
- [x] PI-07 Show exact Project ID.
- [x] PI-08 Show authoritative tenant and workspace identity for each project.
- [x] PI-09 Show exact project lifecycle using only `ACTIVE | ARCHIVING | ARCHIVED`.
- [x] PI-10 Show pinned Domain package/revision when one exists; do not imply a floating/latest binding.
- [x] PI-11 Show created date from authoritative project data.

### C. Execution / attention semantics

- [x] PI-12 Show current execution activity separately from lifecycle using exactly `EXECUTING | PAUSED | QUEUED | IDLE`.
- [x] PI-13 `EXECUTING` follows §34A.2: RUNNING run, RUNNING latest orchestration, or LEASED/RUNNING distributed job.
- [x] PI-14 `PAUSED`, `QUEUED`, and `IDLE` follow the deterministic precedence in §34A.2.
- [x] PI-15 Show active RUNNING run count and active distributed job count from authoritative records.
- [x] PI-16 Show pending approval count from visible `PENDING_APPROVAL` proposals.
- [x] PI-17 Show attention-required count by unresolved authoritative record ID using the qualified §34A.2 attention sources.
- [x] PI-18 Show last authoritative project event timestamp/action when present; do not infer activity from last-modified time.

### D. Projects filters

- [x] PI-19 Provide Active / Archived lifecycle filtering without mutating lifecycle.
- [x] PI-20 Provide tenant/workspace filtering over the actor-authorized result set.
- [x] PI-21 Provide Domain filtering using authoritative package/revision identity.
- [x] PI-22 Provide execution-activity filtering.
- [x] PI-23 Provide Attention Required filtering.
- [x] PI-24 Page filtering is presentation state only; it must not become authoritative product state or imply cross-project search capability.

### E. UI / navigation contract

- [x] PI-25 Render the Projects index as a compact professional research workspace consistent with the approved baseline and existing shell.
- [x] PI-26 Preserve Light/Dark/System, sidebar reflow, semantic icons, Back/Forward, deep-link restoration and auth/session behavior.
- [x] PI-27 Successful empty Projects result is visibly distinct from unavailable/error/unauthorized/partial states.
- [x] PI-28 Mark the Projects route `LIVE_MODULE` only for the index functionality actually implemented.
- [x] PI-29 Do not expose a fake Project Overview/detail action before that destination screen is implemented.
- [x] PI-30 Do not expose fake Create/Rename/Archive/Restore/member/domain-binding actions on this index.
- [x] PI-31 Global/page search remains bounded to authoritative page filtering; no invented GAC-style cross-project document/artifact discovery.

### F. Fast Lane boundary / regression

- [x] PI-32 No database/schema migration is introduced.
- [x] PI-33 No project lifecycle, tenancy, membership, authentication, authorization or Domain binding semantics are changed.
- [x] PI-34 No destructive or authoritative mutation endpoint is added.
- [x] PI-35 Home `SCREEN_PASS` behavior remains intact; shared-shell changes must be rechecked against affected Home/I00 items.

## Self-QA adjudication

```text
TOTAL = 35
PASS  = 35
FAIL  = 0
OPEN  = 0
COUNT = 0
```

Exact implementation candidate:

```text
2b095d1b8c9ed2aa5bc420a78b39f52fe8e65616
```

Evidence:

- `GET /browser/projects-index` is authenticated and returns a read-only server-side projection from actor-authorized projects only.
- Projection includes exact project ID/name, tenant/workspace identity, lifecycle, immutable Domain binding identity, created date, deterministic execution activity, active run/job counts, pending approvals, stable-ID attention count and latest audit event.
- browser filters are transient presentation state only; no filter is persisted as authoritative state.
- Projects capability is `LIVE_MODULE` at the exact index route only; project detail deep-route fallback was removed until Project Workspace exists.
- successful zero-result, filtered-zero, partial and unavailable/error states render distinctly.
- there is no Create/Rename/Archive/Restore/member/domain-binding action and no project-detail action on this screen.
- source diff from the frozen checklist base adds no migration/schema file and no mutation endpoint.
- actor-scoped Home/Projects projections are cleared at the login boundary to prevent stale data crossing browser principals.
- `tests/test_bps_projects_index.py` covers authorization hiding, exact projection semantics, all four execution-activity states, exact Domain pinning, LIVE_MODULE exposure and absence of fake actions/detail deep links.
- existing BPS-I00 shell expectation was updated only for Projects maturity; Home implementation remains unchanged in semantics.
- isolated browser UAT fixture `scripts/bps_projects_uat_fixture.py` uses a temporary database and a localhost cookie host; it does not touch the canonical working DB.

Repository-wide PR workflows for the exact head were queued by GitHub at self-QA time. Fast Lane does not promote queued CI to PASS; the screen self-QA conclusion above is based on bounded source/test-contract review and remains subject to final user browser UAT.

## User UAT rule

User acceptance is the final bounded screen gate and is answered only with:

```text
P = PASS
F = FAIL
```

Any F keeps Projects Index open. All P marks `PROJECTS_INDEX = SCREEN_PASS`.
