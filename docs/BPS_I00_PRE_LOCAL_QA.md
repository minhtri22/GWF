# BPS-I00 — PRE_LOCAL QA1→QA6 Report

## Current routing-repair status

```text
PROGRAM                    = BPS-I00 ROUTING_RECOVERY
ROUTING_GOVERNANCE_HEAD    = 0188edfb4423e6805f81c61713f0989ad4f7d858
ROUTING_IMPLEMENTATION_HEAD= d789fdbf14c49438d17d945faa2edf190a92eb38
ROUTING_CANDIDATE_HEAD     = fc42c3a5c871a79ef7ed1d0f68fce76635c3b484
APPROVED_VISUAL_BASELINE   = GWF-UI-BASELINE-v1.1 / RETAINED
QA1                        = PASS
QA2                        = PASS
QA3                        = PASS
QA4                        = PASS
QA5                        = PASS
QA6                        = PASS
PRE_LOCAL_PASS             = PASS
FINAL_SLICE_PASS           = NO
USER_LOCAL_UAT             = PENDING_ROUTING
BPS-M01                    = LOCKED
```

This is the current assistant-owned verdict. It authorizes only exact-head BPS-I00 local UAT; it does not open BPS-M01.

## Historical visual-recovery status (superseded by routing finding)

```text
PROGRAM                    = BPS-I00 UI_CONFORMANCE_RECOVERY
BASE_GOVERNANCE_HEAD       = 7cc72fe2eef50460f7f7b3842e6379350e5e493e
PRODUCT_CANDIDATE_HEAD     = 05d0a7ec7c4e8d36cfa99e4ac5e0b7370a863c53
APPROVED_BASELINE          = GWF-UI-BASELINE-v1.1
QA1                        = PASS
QA2                        = PASS
QA3                        = PASS
QA4                        = PASS
QA5                        = PASS
QA6                        = PASS
PRE_LOCAL_PASS             = PASS
FINAL_SLICE_PASS           = NO
USER_LOCAL_UAT             = PENDING
BPS-I01                    = LOCKED
```

This report records assistant-owned QA only. It does **not** claim FINAL_SLICE_PASS and does not replace the mandatory exact-head local browser UAT on the user's Windows machine.

## Governing references

- recovery contract blob: `cd35e73f080871ae8a777da37facc655a1520603`;
- approved visual manifest blob: `f8feb8356ea5c45b3ea6d2c838c47a5007c56e7d`;
- visual-baseline QA blob: `e2c6d49c68fed5a4fd5180173e63d6eda4247427`;
- implementation branch: `feature/bps-i00-product-shell`;
- authorized base: `7cc72fe2eef50460f7f7b3842e6379350e5e493e`.

The manifest gives visual precedence to Governed Knowledge Studio identity, project-centered navigation, professional/compact research workspace, semantic icons, expanded/collapsed sidebar, full-shell Light/Dark parity and future project/document workspace composition. For BPS-I00 it explicitly limits implementation to visual foundation conformance; Documents/Relations/Reader remain future-slice references.

## QA1 — Scope completeness — PASS

Compare `7cc72fe2… → 05d0a7ec…` is strictly bounded to:

- `web/index.html`;
- `web/app.js`;
- `web/styles.css`;
- `tests/test_bps_i00_product_shell.py`.

No `src/gwr`, migration, database, governance or backend semantic file changed. BPS-I01+, Documents, Relations, Reader, GAC/RA/AI functional UI remain unopened.

## QA2 — Shell behavior — PASS

Verified in source/tests and affected/full regression:

- semantic inline SVG icon system replaces first-letter placeholders;
- expanded desktop grid is ~260 px sidebar;
- collapsed rail is ~68 px and changes the actual app grid so workspace width is reclaimed;
- collapsed navigation preserves descriptive `title`/ARIA identity and maturity context;
- System/Light/Dark controls remain presentation-only;
- locked/planned capabilities stay disabled and cannot execute fake actions.

## QA3 — Authoritative-state boundary — PASS

The shell continues to reconstruct from live `/browser/bootstrap`, `/browser/auth/me` and `/ready`. Browser local storage remains limited to theme/sidebar presentation preferences. No legacy `demo-data.json`, `gwr-uat-domains` or `gwr-uat-projects` product authority is present.

## QA4 — Auth/security boundary — PASS

Existing HumanAuthService-backed login/session/logout behavior is unchanged. Full regression confirms browser login still returns no reusable access token, session cookie remains HttpOnly + SameSite=Strict, server restart/session reconstruction remains covered, and bearer API compatibility remains intact.

## QA5 — Targeted + affected/full regression — PASS

Initial negative run preserved:

- candidate `fde9790dc6e9bdf5e688e31f2b3fbeabe3b5823b`;
- run `35824494282`;
- failure: historical static shell snapshot expected literal `LIVE FOUNDATION` in HTML.

Bounded compatibility repair did not change UI direction or backend semantics.

Qualified candidate `05d0a7ec7c4e8d36cfa99e4ac5e0b7370a863c53`:

- run `35824741746`: SQLite/full regression PASS, compile PASS, PostgreSQL PASS, Windows one-click qualification PASS;
- Windows artifact `10735526412`, digest `sha256:7c9b70516f0e857ba6ca13fd4e5d8270bff438c46a228e63e6e6545dcf40b320`;
- SQLite artifact `10734707992`, digest `sha256:27378f2a15d16a027db18214f3595e33f77048334cf152e9961a1f3acf80d3a2`;
- PostgreSQL artifact `10734711776`, digest `sha256:db28cc6b238677cd63f7a6b4baa77c34a19581c9fab5cb8f193c3d73afa22f9c`;
- run `35824741758`: v0.8.5 Linux gate PASS and Windows installer qualification PASS;
- Windows install artifact `10735277932`, digest `sha256:9cfb5818d6ab9836af4811e35a224f94687f86c42efe16fdd5673201399dce7c`;
- Linux evidence artifact `10734728411`, digest `sha256:50617bb074e6f245c207d40d61d8026e67fb71b59fac3f673f23e23a39345f11`.

Historical DG-P8/DG-W2 pull-request failures were separately inspected and are frozen-gate/later-schema incompatibilities unrelated to the four BPS product files; they are not used as positive BPS evidence.

## QA6 — Approved visual-baseline conformance — PASS

Comparison basis: approved visual baseline v1.1 + manifest, not legacy v0.8.5.

Verified:

- Governed Knowledge Studio/Governed Knowledge Workflow visual identity;
- compact global sidebar + top command/search bar + research-workspace card/panel hierarchy;
- semantic icon navigation in actual implementation source;
- 260→68 desktop layout contract with true workspace reflow;
- full-shell Light/Dark tokens for sidebar, top bar and content;
- visible locked/planned/live maturity without fake functionality;
- future Documents/Relations/Preview/Reader not implemented early.

Assistant reference-state captures, fixed at 1440×900:

| State | SHA-256 |
| --- | --- |
| Dark / expanded | `86a8769bc6cf6ff3d8055c9b3df0895bb061bc73c7020eb5b278dcf23162cd22` |
| Dark / collapsed | `2763a8831593df30caee88b9b1c453121e21b7bb66eab8bd84eae9279f728b59` |
| Light / expanded | `538de37ee39a8e7a6132c36d708cec7ea37f9757c2150d9532c383e949293731` |
| Light / collapsed | `07d81dc704341c887e269625ba5755f466c8c9bf4ead2414492b6c6419ffc263` |

Capture package digest: `sha256:36f67765c56338bfb7d37e96fe426cc99e69065dedb08fc60b45acdccfa2d4bb`.

Container Chromium navigation was blocked by environment policy, so the assistant-side captures use a deterministic renderer/reference-state harness derived from the exact candidate geometry/theme contract. This is not hidden as browser evidence: actual browser rendering/operator behavior remains mandatory in the next local UAT. Source assertions and exact-head regression separately verify the real implementation's semantic SVG icons, tooltip/title path, reflow hook and theme tokens.

## PRE_LOCAL verdict

```text
QA1→QA6       = PASS
PRE_LOCAL_PASS = PASS
NEXT           = exact-head user local UAT only
FINAL_SLICE_PASS = NO
BPS-I01 = LOCKED
```

## Route-skeleton supersession

Operator review after visual recovery explicitly established:

```text
VISUAL_UI_UX = APPROVED
LOCAL_UAT    = NOT_APPROVED
REASON       = top-level navigation did not link to navigable route surfaces
```

The prior PRE_LOCAL_PASS is superseded for I00 final handoff:

```text
PRE_LOCAL_PASS = INVALIDATED_ROUTE_GAP
QA1 = REOPENED
QA2 = REOPENED
QA6 = REOPENED
FINAL_SLICE_PASS = NO
NEXT = bounded BPS-I00 routing repair
```

Positive visual/theme/sidebar/auth/runtime evidence is retained and regression-checked after routing repair.

## Routing repair QA1→QA6 requalification

### QA1 — Scope completeness — PASS

Exact governance base: `0188edfb4423e6805f81c61713f0989ad4f7d858`.

Routing candidate: `fc42c3a5c871a79ef7ed1d0f68fce76635c3b484`.

Changed implementation/harness files are bounded to:

- `src/gwr/api.py` — capability route metadata + canonical `/app/*` shell deep-link fallback;
- `web/index.html` — locked-route and diagnostics route containers;
- `web/app.js` — SPA router/history/route rendering;
- `web/styles.css` — locked-route presentation only;
- `tests/test_bps_i00_product_shell.py`;
- `tests/test_bps_i00_local_uat_script.py`;
- `scripts/uiux/bps_i00_local_uat.ps1`.

No Home KPI, Project data/action, Operations data, Package Registry data, Project Library, Documents/Reader, Relations graph, GAC/RA/Agents functionality was opened.

### QA2 — Functional routing correctness — PASS

Verified:

- authoritative bootstrap exposes exact `route`, `state`, and owning `slice/module`;
- top-level nav remains clickable for `SKELETON_LOCKED` and `PLANNED_BLOCKED`;
- navigation uses `history.pushState`;
- browser `popstate` restores selected route/nav surface;
- direct recognized `/app/*` deep links return the canonical shell;
- reload resolves route from `window.location.pathname`;
- locked/planned routes render route title, exact path, owner and maturity;
- `/app/system/diagnostics` is the only I00 LIVE foundation route and retains real product/health identity.

### QA3 — Authoritative-state correctness — PASS

Route metadata comes from `/browser/bootstrap`; health from `/ready`; identity/session from `/browser/auth/me`. Browser persistence remains presentation-only theme/sidebar state. No product module entity/count/activity is synthesized in locked/planned surfaces.

### QA4 — Governance/security correctness — PASS

HumanAuthService-backed session and HttpOnly/SameSite behavior are unchanged. Route availability does not imply module authorization. No mutation endpoint or later-module API is called by the I00 router. Locked/planned pages expose only public shell maturity/owner/path metadata.

### QA5 — automated/regression qualification — PASS

Preserved negative evidence:

- first routing implementation HEAD `d789fdbf14c49438d17d945faa2edf190a92eb38`;
- workflow `35837281009` failed because `tests/test_bps_i00_local_uat_script.py` expected literal `route_http_home`, while the script intentionally generated `route_http_<key>` dynamically from the frozen route table;
- the failure was a test-contract assertion mismatch, not router/runtime behavior.

Bounded repair HEAD: `fc42c3a5c871a79ef7ed1d0f68fce76635c3b484`.

Exact-head qualification:

- DG-P10 workflow `35837603192` PASS: Linux targeted/full regression PASS, compile PASS, PostgreSQL PASS, Windows one-click PASS;
- SQLite artifact `10739872984`, digest `sha256:ce1d67cd51fe12cfafe177932a0f3117bfc9c887e7301c40f27f1430e8262b80`;
- PostgreSQL artifact `10739159328`, digest `sha256:3f918567dc7bbd0e10d2ab5c72d2a9269c2cbe99386d83bda9464b34dac190d3`;
- Windows artifact `10741452906`, digest `sha256:7bdf6cfe888cccb2b4aff48a80791dff098d21ea93a8ecadc3a5de22392ad5d0`;
- v0.8.5 workflow `35837603233` PASS: Linux gate PASS + Windows installer PASS;
- Linux evidence artifact `10740455330`, digest `sha256:983c80fa3de3fc3f99af84ad5bd40a3f73d0ba6a317de324a50cdc0d9319b6cb`;
- Windows install artifact `10740277696`, digest `sha256:77c681130fe36ac86970749ad45c1f78e0aa1f9e5d2676209190992fce544222`.

Historical DG-P8/DG-W2 frozen-gate failures remain unrelated and are not counted as positive routing evidence.

### QA6 — UI/UX + navigation contract — PASS

The already user-approved visual baseline is retained. Routing repair does not restyle the shell.

Deterministic exact-candidate routing matrix:

```text
bootstrap routes/module ids       PASS
SKELETON_LOCKED/PLANNED states   PASS
deep-link shell adapter          PASS
semantic clickable nav           PASS
History pushState                PASS
popstate Back/Forward            PASS
reload route restore             PASS
selected nav / aria-current      PASS
route-specific locked surface    PASS
Diagnostics LIVE foundation      PASS
authoritative bootstrap/ready    PASS
no Documents/Relations/Reader    PASS
no Project API/data              PASS
no fake KPI/count/activity       PASS
260→68 workspace reflow          PASS
full-shell Light/Dark tokens     PASS
targeted route tests             PASS
UAT machine route checks         PASS
UAT Back/Forward prompt          PASS
UAT reload prompt                PASS
UAT Diagnostics prompt           PASS
UAT no-fake-data prompt          PASS
TOTAL                            22/22
FAILED                           0
```

The local script now requires operator verification of click navigation, canonical route changes, Back/Forward, reload on `/app/projects`, planned routes, LIVE Diagnostics and absence of fake module content.

## Current PRE_LOCAL verdict

```text
VISUAL_UI_UX_APPROVAL = RETAINED
QA1→QA6               = PASS
PRE_LOCAL_PASS         = PASS
USER_LOCAL_UAT         = PENDING_ROUTING
FINAL_SLICE_PASS       = NO
BPS-M01                = LOCKED
```
