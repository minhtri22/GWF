# System GitHub Read Surface — BPS-M07-A Checklist

## Identity

```text
SCREEN_ID        = SYSTEM_GITHUB
OWNER            = BPS-M07
ROUTE            = /app/system/github
PROTOCOL         = BPS-QA-FIRST-DEFERRED-UAT-v1
STATUS           = CHECKLIST_FROZEN / IMPLEMENTATION_PENDING
BASE_HEAD        = 5a1efd6342db49e832d779fd9a536db453cf230a
FINAL_UAT        = DEFERRED
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

- [ ] GH-01 Add cookie-authenticated `GET /browser/github`.
- [ ] GH-02 Projection contains only projects currently visible to the actor.
- [ ] GH-03 Return generated_at, exact build SHA and COMPLETE/PARTIAL query status.
- [ ] GH-04 Return exact project ID/name and tenant/workspace context.
- [ ] GH-05 Return GitHub PluginConnection identity, opaque external connection ref, persisted capabilities/status/non-secret metadata/creator/timestamps.
- [ ] GH-06 Return adapter-attached state as runtime observation, not persisted credential state.
- [ ] GH-07 Return repository binding ID/repository/default branch/write policy/allowed branches/creator/time.
- [ ] GH-08 Return the connection status/capabilities attached to each binding.
- [ ] GH-09 Dangling connection or binding identity makes projection PARTIAL and remains visible as a broken persisted identity.
- [ ] GH-10 Return ChangeSet ID/binding/branch/expected HEAD/manifest/hash/message/status/creator/time/committed SHA/verified_at.
- [ ] GH-11 ChangeSet manifest contains path/operation/expected blob SHA/content SHA-256 only; no file content.
- [ ] GH-12 Return exact SHA-check history with stage/expected/observed/status/details/time.
- [ ] GH-13 `qa_complete` is true only when persisted ChangeSet status is exactly VERIFIED.
- [ ] GH-14 COMMITTED is visibly distinct from VERIFIED.
- [ ] GH-15 STALE and VERIFICATION_FAILED remain distinct persisted states.
- [ ] GH-16 No inaccessible project/connection/binding/ChangeSet identity leaks.

### B. Adapter readiness read

- [ ] GH-17 Add cookie-authenticated exact-binding readiness endpoint.
- [ ] GH-18 Binding must belong to an authorized project; unknown/inaccessible binding is non-disclosing 404.
- [ ] GH-19 DISABLED connection returns disabled readiness without attempting adapter access.
- [ ] GH-20 ACTIVE but unattached connection returns NOT_ATTACHED.
- [ ] GH-21 Missing REPO_READ capability returns CAPABILITY_MISSING.
- [ ] GH-22 Attached adapter without repository-identity method returns IDENTITY_UNSUPPORTED.
- [ ] GH-23 Supported adapter probe returns repository ID/full name and exact default-branch HEAD.
- [ ] GH-24 Repository full-name mismatch is explicit IDENTITY_MISMATCH, never silently accepted.
- [ ] GH-25 Provider/read error is distinct from zero/unattached and never exposes credentials.

### C. Browser GitHub UI

- [ ] GH-26 Promote System → GitHub from SKELETON_LOCKED to LIVE_MODULE.
- [ ] GH-27 Show authoritative authorized-scope project selector/list.
- [ ] GH-28 Show connection status, capabilities and adapter-attached state.
- [ ] GH-29 Show repository bindings including policy/allowlist and exact identity readiness state.
- [ ] GH-30 Readiness check is explicit/on-demand and does not imply connection mutation.
- [ ] GH-31 Show ChangeSets and SHA checks; PREPARED/PREFLIGHT_PASS/COMMITTED/VERIFIED/STALE/VERIFICATION_FAILED remain distinct.
- [ ] GH-32 Show qa_complete only for VERIFIED.
- [ ] GH-33 Zero/PARTIAL/error/unattached/provider-error states are distinct.
- [ ] GH-34 No raw token/password/private key/Authorization field is present.
- [ ] GH-35 No create/disable/bind/prepare/preflight/execute mutation control appears in M07-A.
- [ ] GH-36 Theme/sidebar/session/global routing do not regress.

### D. QA

- [ ] GH-37 Tests prove hidden project GitHub identities do not leak.
- [ ] GH-38 Tests cover no connection, disabled, unattached, capability-missing, identity-unsupported, ready, identity-mismatch and provider-error readiness states.
- [ ] GH-39 Tests cover ChangeSet status distinctions and qa_complete semantics.
- [ ] GH-40 Tests prove manifests omit file content and projection omits runtime credential/adapter objects.
- [ ] GH-41 Existing Bearer GitHub/Plugin APIs remain unchanged.
- [ ] GH-42 No schema, plugin capability, binding policy, SHA-safe write or credential semantics change.
- [ ] GH-43 Findings are recorded/fixed/rechecked until `FAIL=0 OPEN=0 COUNT=0`.

## Initial count

```text
TOTAL = 43
PASS  = 0
FAIL  = 0
OPEN  = 43
COUNT = 43
```
