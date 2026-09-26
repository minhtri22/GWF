# System GitHub Read Surface — BPS-M07-A Checklist

## Identity

```text
SCREEN_ID        = SYSTEM_GITHUB
OWNER            = BPS-M07
ROUTE            = /app/system/github
PROTOCOL         = BPS-QA-FIRST-DEFERRED-UAT-v1
STATUS           = ASSISTANT_QA_PASS / USER_UAT_PENDING
BASE_HEAD        = 5a1efd6342db49e832d779fd9a536db453cf230a
FINAL_UAT        = PENDING_USER_PF
```

## Governing sources

- `docs/UI_UX_PRODUCT_ARCHITECTURE_SPEC.md` §15.2, §34A.11.
- `docs/BROWSER_PRODUCT_SURFACE_SPEC.md` §14.
- `docs/v0.8.4-github-plugin-sha-qa.md`.
- `docs/GITHUB_SHA_QA_STANDARD.md`.
- `src/gwr/plugins.py`.
- `src/gwr/github_plugin.py`.
- `src/gwr/github_rest_adapter.py`.

## Security/read boundary

M07-A is read-only. GWF stores only an opaque external connection reference plus non-secret metadata/capabilities. Browser reads MUST NOT expose reusable credentials, credential resolver output, Authorization headers, runtime adapter objects or secret material.

Runtime adapter attachment remains host-only.

## Frozen checklist

### A. Authorized GitHub projection

- [x] GH-01 Add cookie-authenticated `GET /browser/github`.
- [x] GH-02 Projection contains only projects currently visible to the actor.
- [x] GH-03 Return generated_at, exact build SHA and COMPLETE/PARTIAL query status.
- [x] GH-04 Return exact project ID/name and tenant/workspace context.
- [x] GH-05 Return GitHub PluginConnection identity, opaque external connection ref, persisted capabilities/status/non-secret metadata/creator/timestamps.
- [x] GH-06 Return adapter-attached state as runtime observation, not persisted credential state.
- [x] GH-07 Return repository binding ID/repository/default branch/write policy/allowed branches/creator/time.
- [x] GH-08 Return the connection status/capabilities attached to each binding.
- [x] GH-09 Dangling connection or binding identity makes projection PARTIAL and remains visible as a broken persisted identity.
- [x] GH-10 Return ChangeSet ID/binding/branch/expected HEAD/manifest/hash/message/status/creator/time/committed SHA/verified_at.
- [x] GH-11 ChangeSet manifest contains path/operation/expected blob SHA/content SHA-256 only; no file content.
- [x] GH-12 Return exact SHA-check history with stage/expected/observed/status/details/time.
- [x] GH-13 `qa_complete` is true only when persisted ChangeSet status is exactly VERIFIED.
- [x] GH-14 COMMITTED is visibly distinct from VERIFIED.
- [x] GH-15 STALE and VERIFICATION_FAILED remain distinct persisted states.
- [x] GH-16 No inaccessible project/connection/binding/ChangeSet identity leaks.

### B. Adapter readiness read

- [x] GH-17 Add cookie-authenticated exact-binding readiness endpoint.
- [x] GH-18 Binding must belong to an authorized project; unknown/inaccessible binding is non-disclosing 404.
- [x] GH-19 DISABLED connection returns disabled readiness without attempting adapter access.
- [x] GH-20 ACTIVE but unattached connection returns NOT_ATTACHED.
- [x] GH-21 Missing REPO_READ capability returns CAPABILITY_MISSING.
- [x] GH-22 Attached adapter without repository-identity method returns IDENTITY_UNSUPPORTED.
- [x] GH-23 Supported adapter probe returns repository ID/full name and exact default-branch HEAD.
- [x] GH-24 Repository full-name mismatch is explicit IDENTITY_MISMATCH, never silently accepted.
- [x] GH-25 Provider/read error is distinct from zero/unattached and never exposes credentials.

### C. Browser GitHub UI

- [x] GH-26 Promote System → GitHub from SKELETON_LOCKED to LIVE_MODULE.
- [x] GH-27 Show authoritative authorized-scope project selector/list.
- [x] GH-28 Show connection status, capabilities and adapter-attached state.
- [x] GH-29 Show repository bindings including policy/allowlist and exact identity readiness state.
- [x] GH-30 Readiness check is explicit/on-demand and does not imply connection mutation.
- [x] GH-31 Show ChangeSets and SHA checks; PREPARED/PREFLIGHT_PASS/COMMITTED/VERIFIED/STALE/VERIFICATION_FAILED remain distinct.
- [x] GH-32 Show qa_complete only for VERIFIED.
- [x] GH-33 Zero/PARTIAL/error/unattached/provider-error states are distinct.
- [x] GH-34 No raw token/password/private key/Authorization field is present.
- [x] GH-35 No create/disable/bind/prepare/preflight/execute mutation control appears in M07-A.
- [x] GH-36 Theme/sidebar/session/global routing do not regress.

### D. QA

- [x] GH-37 Tests prove hidden project GitHub identities do not leak.
- [x] GH-38 Tests cover no connection, disabled, unattached, capability-missing, identity-unsupported, ready, identity-mismatch and provider-error readiness states.
- [x] GH-39 Tests cover ChangeSet status distinctions and qa_complete semantics.
- [x] GH-40 Tests prove manifests omit file content and projection omits runtime credential/adapter objects.
- [x] GH-41 Existing Bearer GitHub/Plugin APIs remain unchanged.
- [x] GH-42 No schema, plugin capability, binding policy, SHA-safe write or credential semantics change.
- [x] GH-43 Findings are recorded/fixed/rechecked until `FAIL=0 OPEN=0 COUNT=0`.

## Initial count

```text
TOTAL = 43
PASS  = 0
FAIL  = 0
OPEN  = 43
COUNT = 43
```

## Assistant self-QA closure — 2026-09-26

Implementation lineage:

```text
0762ec416852545101281e2b3d953558b2e3c1ff  freeze read surface checklist
003cc1b93b289fa743883ff976947fa3f4ce15ac  add authorized read and readiness projections
c3b704ddd50248c61abb43ffc18ed58592baf58a  harden readiness provider responses
634a85023b3da22047fc9a7cd2b384853116fa4d  lock authorized read/readiness contracts
7b569d165950d1afe08ad1f09a07c16d474e1bdd  fix deterministic SHA fixture
ce81c1f05b5bf9b44ea44a82c96befebd810a7bc  render authorized read-only system surface
44f4943624bc142e3bb5fcb14617e01ce5f81e33  close seeded transaction between ChangeSets
```

GitHub-specific finding:

### GH-F01 — RESOLVED

- Initial full-regression execution exposed `sqlite3.OperationalError: cannot start a transaction within a transaction` in the new GitHub test seed.
- Root cause was fixture-only: direct seeded `github_change_sets/github_sha_checks` shaping left an implicit SQLite transaction open before the next service-owned `prepare_change_set()` transaction.
- Repair commits the deterministic seeded state after each loop iteration.
- Recheck on exact HEAD `44f4943624bc142e3bb5fcb14617e01ce5f81e33`, v0.8.4 run `36252737295`: full pytest failure set contains no `tests/test_bps_github_read_surface.py` failures.
- Product GitHub API/readiness semantics were not changed to satisfy this fixture defect.

Other full-regression failures in that run are outside this screen and pre-existed the GitHub implementation path (Home UAT fixture, Operations Runs/Runtime, System Access). They are not reclassified as GitHub findings.

Self-QA evidence:

- authorized cookie-authenticated `GET /browser/github`;
- only actor-visible projects projected;
- exact project/scope, PluginConnection, binding, ChangeSet and SHA-check identities;
- ChangeSet manifest content minimized to path/operation/expected blob/content SHA-256;
- no reusable credential/runtime-adapter object disclosure;
- exact readiness states: DISABLED, NOT_ATTACHED, CAPABILITY_MISSING, IDENTITY_UNSUPPORTED, READY, IDENTITY_MISMATCH, CONNECTION_MISSING and PROVIDER_ERROR;
- provider exceptions sanitized;
- `qa_complete=true` only for persisted VERIFIED ChangeSets;
- COMMITTED remains distinct from VERIFIED; STALE remains distinct from VERIFICATION_FAILED;
- GitHub capability promoted to `LIVE_MODULE`;
- authorized project selector, Connections, Bindings/readiness, ChangeSets and SHA-check UI rendered;
- readiness is explicit/on-demand and read-only;
- zero, PARTIAL, request-error, unattached and provider-error states render distinctly;
- GitHub UI segment contains no POST/PUT/DELETE or product mutation endpoint;
- theme/sidebar/session/global routing patterns remain inherited from the qualified shell;
- scope diff from pre-GitHub HEAD `5a1efd6342db49e832d779fd9a536db453cf230a` touches only the screen checklist, GitHub read projection/readiness, GitHub tests and web shell assets.

```text
TOTAL = 43
PASS  = 43
FAIL  = 0
OPEN  = 0
COUNT = 0

SYSTEM_GITHUB_ASSISTANT_QA = PASS
USER_UAT                  = PENDING
NEXT_SCREEN_ALLOWED       = false
```

## User UAT rule

The user now verifies only observable System → GitHub behavior using:

```text
P = PASS
F = FAIL
```

Any F keeps this screen open. All P marks `SYSTEM_GITHUB = SCREEN_PASS`, after which the next screen may begin.
