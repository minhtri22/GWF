# BPS-I00 — PRE_LOCAL_PASS QA Record

## 1. Status

```text
SLICE = BPS-I00
STATE = PRE_LOCAL_PASS_INVALIDATED
QA1 = HISTORICAL_PASS_RECHECK_AFTER_RECOVERY
QA2 = HISTORICAL_PASS_RECHECK_IF_AFFECTED
QA3 = HISTORICAL_PASS_RETAINED_UNLESS_AFFECTED
QA4 = HISTORICAL_PASS_RETAINED_UNLESS_AFFECTED
QA5 = RECHECK_REQUIRED_AFTER_RECOVERY_CODE
QA6 = FAIL_REOPENED_BY_LOCAL_UAT
FINAL_SLICE_PASS = NO
BPS-I01 = LOCKED
```

This record is now **historical evidence only**. Local browser UAT exposed material UI/UX conformance defects, so its former PRE_LOCAL_PASS status is invalidated. It does **not** authorize a new local handoff until the bounded UI-conformance recovery reruns affected QA and produces a new PRE_LOCAL_PASS record.

## 2. Exact implementation identity

Tested implementation branch content:

```text
branch = feature/bps-i00-product-shell
implementation_head_before_evidence_binding = 72816eca803a7afe80d2a722f2d25ebfb71f9613
tested_commit = 78abe9413163b027cb0f5fa6b829a7dce96350fe
tested_tree = 3232ff6dc2fff654d9634275e8d1a4fb9a357a6b
```

The tested commit is the pull-request merge commit used by GitHub Actions and is a direct descendant of the implementation head. Its tree is byte-for-byte identical to the implementation tree.

After QA completion the implementation branch was fast-forwarded to the tested commit so repository HEAD and tested commit are identical before local-UAT tooling is added.

## 3. Governing inputs

- root `AGENTS.md` — canonical BPS QA/handoff protocol;
- `docs/BPS_I00_IMPLEMENTATION_AUTHORIZATION.md`;
- `docs/IMPLEMENTATION_7_WAVES_PLAN.md`;
- `docs/UI_UX_PRODUCT_ARCHITECTURE_SPEC.md`;
- `docs/UI_UX_QA.md`;
- `docs/BROWSER_PRODUCT_SURFACE_SPEC.md`.

No later BPS slice was authorized during this implementation.

## 4. QA1 — Scope completeness

**PASS**

Implementation covers only the authorized BPS-I00 foundation:

- canonical GWF server bootstrap/entry point;
- canonical Windows start/stop/restart/status launcher;
- install/runtime separation;
- live FastAPI-served browser shell;
- browser session transport over existing `HumanAuthService`;
- System/Light/Dark theme;
- collapsible navigation;
- build/domain/backend/readiness identity;
- capability maturity/locked future navigation;
- retirement of static/localStorage simulated product-state acceptance.

Diff from authorization base remains inside allowed families:

- `README.md`;
- `install.ps1`;
- `pyproject.toml`;
- `scripts/`;
- `src/gwr/api.py`, `src/gwr/server.py`;
- `tests/`;
- `tools/` static-UAT compatibility/QA;
- `web/`.

No migration, Domain semantic, DG-P11+, GAC, RA or AI/Codex implementation was introduced.

## 5. QA2 — Functional correctness

**PASS**

Verified behaviors include:

- canonical server constructs the real `GovernedWorkflowRuntime` and real `create_app(runtime)`;
- existing bearer auth remains supported;
- browser login/me/logout uses the existing auth service;
- login response does not expose bearer token;
- logout revokes the underlying session;
- server fails closed on invalid/missing mandatory secret/config;
- `/health`, `/ready`, `/product/meta`, shell and static assets use the same FastAPI product;
- Windows lifecycle supports start/status/restart/stop and refuses ownership-unsafe process handling;
- default installer is runnable-product install mode;
- full qualification remains explicit/backward-compatible.

## 6. QA3 — Authoritative-state correctness

**PASS**

- Browser product truth is backend/API state.
- Legacy `web/demo-data.json` was removed.
- Legacy localStorage product-state keys/simulations were removed.
- Browser local persistence is limited to UI theme/sidebar preference.
- Authenticated session is reconstructed from server-side session state through HttpOnly cookie.
- Refresh does not require JavaScript-readable bearer-token persistence.
- Capability state is served by backend bootstrap, not fabricated from browser storage.

## 7. QA4 — Governance and security correctness

**PASS**

Verified requirements:

- `HumanAuthService` remains authentication/session authority;
- existing bearer API remains valid;
- browser session cookie is HttpOnly and SameSite=Strict;
- no reusable access token is written into JS/localStorage/static asset;
- future product areas are non-actionable `LOCKED` or `PLANNED_BLOCKED`;
- server config fails closed;
- core health does not fabricate uptime;
- Windows launcher tracks process identity/start time and refuses unrelated-process ownership;
- no DG/GAC/RA/AI authority semantics were changed.

BPS-I00 has no business mutation surface, so later-slice CSRF/business-authority work is not pulled forward.

## 8. QA5 — Automated QA and regression

**PASS**

### DG-P10 Change Classification — run 35722291283

Run conclusion: **SUCCESS**  
Run head SHA: `72816eca803a7afe80d2a722f2d25ebfb71f9613`  
Tested tree: identical to `78abe9413163b027cb0f5fa6b829a7dce96350fe`.

Jobs:

- SQLite: PASS
  - D10-F1..D10-F20 PASS;
  - bounded DG-P10 gate PASS;
  - targeted regressions PASS;
  - **full regression PASS**;
  - compile PASS.
- PostgreSQL: PASS
  - PostgreSQL 17 PASS;
  - bounded PostgreSQL gate PASS.
- Windows one-click: PASS
  - installer parser PASS;
  - one-click local setup PASS;
  - install/UAT report assertion PASS.

Artifacts:

- `10692485406` — `gwr-dg-p10-sqlite-evidence`;
- `10691418224` — `gwr-dg-p10-postgres-evidence`;
- `10693366732` — `gwr-dg-p10-windows-uat`.

### v0.8.5 Domain Skills Installer Pilot — run 35722291555

Run conclusion: **SUCCESS**

Jobs:

- Linux gate PASS;
- v0.8.5 ready assertion PASS;
- Windows installer PASS;
- Windows full local qualification PASS;
- install report assertion PASS.

Artifacts:

- `10691797919` — `gwr-v085-gate-evidence`;
- `10693251600` — `gwr-v085-windows-install`.

### Historical workflow failures not attributed to BPS-I00

Two historical standalone workflows still fail for pre-existing reason:

1. **DG-P8 Typed Document Relations Gate**
   - current P8 tests themselves pass;
   - legacy `run_dg_p8_gate.py` invokes relation preparation without current P9 binding semantics and fails `Invalid target_binding_mode`;
   - this is a stale historical gate against the later P9/P10 codebase, not an I00 regression.

2. **DG-W2 Wave 2 Requalification Gate**
   - P4/P5/P6 component checks pass;
   - the frozen historical W2 schema assertion rejects later Wave-3 tables `document_authority_claims` and `document_relations` as unexpected;
   - this is expected when running frozen W2 isolation logic against the later formally closed product, not an I00 regression.

Neither failing workflow is weakened or edited to force PASS.

## 9. QA6 — UI/UX contract conformance

**PASS**

Verified against the locked UI/UX contract:

- new research/SaaS shell replaces the static demo;
- System/Light/Dark mode exists;
- sidebar collapse/expand exists;
- global information architecture is present;
- I01+ areas are visible only as locked/planned maturity entries;
- no Home KPI/business dashboard was pulled into I00;
- no document graph/library/project business workflow was pulled forward;
- exact runtime/build/domain/backend identity is inspectable;
- unavailable/planned states are explicit;
- shell assets contain no static fake business data;
- product browser surface is served by the canonical FastAPI application.

## 10. PRE_LOCAL_PASS adjudication

All six mandatory assistant-owned checks PASS:

```text
QA1 PASS
AND QA2 PASS
AND QA3 PASS
AND QA4 PASS
AND QA5 PASS
AND QA6 PASS
        ↓
PRE_LOCAL_PASS
```

Therefore creation of the slice-specific local-UAT handoff script is now authorized:

```text
scripts/uiux/bps_i00_local_uat.ps1
```

## 11. Remaining gate

BPS-I00 is **not** FINAL_SLICE_PASS.

Required next sequence:

```text
commit one-click local-UAT PS1
    ↓
user pulls branch
    ↓
user runs exactly one PS1
    ↓
script emits BPS-I00_LOCAL_UAT_REPORT.json
    ↓
user returns JSON report
    ↓
ChatGPT exact-HEAD adjudication
    ↓
FINAL_SLICE_PASS or remain OPEN
```

BPS-I01 remains LOCKED.

## 12. Local-UAT supersession / QA6 reopen

The initial assistant-owned QA6 checked the presence of a new shell, theme control, collapse control and navigation, but did not perform sufficiently strict visual/design conformance against a frozen approved baseline.

Local UAT exposed that existence did not imply conformance.

Normative recovery inputs:

- `docs/uiux/approved/UI_VISUAL_BASELINE_MANIFEST.md`;
- `docs/UI_UX_VISUAL_BASELINE_QA.md`;
- `docs/BPS_I00_UI_REIMPLEMENTATION_CONTRACT.md`;
- Amendment 1 of `docs/BPS_I00_IMPLEMENTATION_AUTHORIZATION.md`.

Until the recovery implementation passes a new QA1→QA6 cycle:

```text
PRE_LOCAL_PASS = INVALID
QA6 = REOPENED
LOCAL_UAT = NOT_ACCEPTED_AS_FINAL_PASS
FINAL_SLICE_PASS = NO
BPS-I01 = LOCKED
```

Historical runtime/server/auth evidence remains useful negative/positive evidence, but no PASS is transferred across the recovery code commit.
