# BPS-I00 — Bounded Implementation Authorization

## 1. Gate identity

```text
GATE = BPS_I00_BOUNDED_IMPLEMENTATION_AUTHORIZATION
DECISION = PASS
IMPLEMENTATION_AUTHORITY = AUTHORIZED_BOUNDED
SLICE = BPS-I00
NEXT_SLICE = BPS-I01 LOCKED
```

This document authorizes implementation of exactly:

> **BPS-I00 — Canonical product server + shell foundation**

It does not implement BPS-I00 and does not mark the slice PASS.

## 2. Exact authorization basis

Authorization review was performed against governance HEAD:

```text
10918a87def7c89649128d3c089c0e0b0b30ef6c
```

Product semantic ancestor:

```text
DG-P10 formal-close product HEAD
a09f79ae74a838d2c5998813560373c849669872
workflow 35671227699 PASS
```

Mandatory governing inputs:

| Input | Exact identity |
| --- | --- |
| root `AGENTS.md` | blob `6aa443d2e0b8629b924ccd4b01fadcb8549dfc4f` |
| `IMPLEMENTATION_7_WAVES_PLAN.md` | pre-authorization blob `35666c7cb95db6b9f325d9de19e89ff6f8c7a8b6` |
| `UI_UX_PRODUCT_ARCHITECTURE_SPEC.md` | blob `f4000eac36f8c82826c73070234acd23f8ac72fd` |
| `UI_UX_QA.md` | blob `2d4877e4064538dc40480db0715f0bd4b19e495e`, OPEN=0 |
| `BROWSER_PRODUCT_SURFACE_SPEC.md` | blob `1581d5761a07eced3310877c9ccdd0ebef37856f` |
| incremental UI execution-plan QA | blob `db39ffea21cf5878977170b0a2df989cbd31a931`, PASS |
| local-UAT responsibility QA | blob `db8449c34bb83df8314d5f0bb39eeb1bd6eac60d`, PASS |
| `TECHNICAL_DEBT.md` | blob `fabe28d1258584c5fe8708f5eff25ade44625f16` |
| current `pyproject.toml` | blob `cb0be1b22c5e2542ce655799975d394248cccd54` |
| current `install.ps1` | blob `62db3a51d09f5e24c4a61c35a34b1fdd40f6e474` |

User authorization: explicit approval in the current governance turn to execute this bounded implementation authorization gate.

## 3. Baseline adjudication

Comparison from DG-P10 formal-close HEAD `a09f79ae...` to the authorization basis confirms:

- no qualified product semantic changes under `src/gwr/`;
- no migration changes;
- no test-semantic changes;
- no `pyproject.toml` or `install.ps1` product changes;
- governance/documentation evolved;
- three temporary UAT tools were added on the governance branch.

Those temporary tools are:

- `tools/browser_uat_server.py`;
- `tools/start_browser_uat.ps1`;
- `tools/uat_dg_p0_p10_local.ps1`.

They are explicitly **non-authoritative legacy UAT tooling** and do not count as BPS-I00 implementation.

## 4. Dependency review

| Requirement | Result |
| --- | --- |
| DG-P10 formal-close exists | PASS |
| UI/UX architecture frozen | PASS |
| UI/UX coverage QA OPEN=0 | PASS |
| incremental BPS sequence QA | PASS |
| assistant QA/local-UAT protocol QA | PASS |
| canonical handoff protocol available at root | PASS |
| BPS-I00 is current first slice | PASS |
| predecessor FINAL_SLICE_PASS | NOT_APPLICABLE — first BPS slice |
| DG-P11+ remains unauthorized | PASS |
| GAC/RA/AI future UI remains blocked | PASS |

No blocking dependency remains for bounded BPS-I00 implementation.

## 5. Authorized outcome

BPS-I00 implementation may create the minimum product capability necessary to satisfy all of the following.

### 5.1 Canonical installed server

Provide one canonical supported way to start the actual GWF FastAPI product after installation.

It must:

- instantiate the real `GovernedWorkflowRuntime`;
- serve the real `create_app(runtime)`;
- use explicit configuration for Domain/database/auth/runtime inputs;
- have deterministic startup failure for invalid/missing mandatory configuration;
- expose readiness/health;
- have start/stop/restart/status lifecycle suitable for Windows local operation;
- stop only the process started by the canonical launcher;
- not pin itself to a historical UAT HEAD.

A UAT-only uvicorn installation is not acceptable as the canonical product server.

### 5.2 Runtime dependency / entry point

The implementation may update packaging/runtime dependencies and entry points only as required for the canonical server.

A production server dependency such as `uvicorn` may become a normal runtime dependency.

The implementation must not introduce a second web backend.

### 5.3 Installer/runtime separation

BPS-I00 may resolve TD-UAT-01 to the extent required for a usable installed product:

- default install performs environment/dependency setup plus bounded lightweight validation/smoke;
- default install no longer needs to run the full repository regression and DG qualification simply to make the product runnable;
- complete qualification remains explicitly available and unchanged in authority;
- major install stages expose elapsed timing;
- success exits 0; mandatory failure exits nonzero;
- install report retains exact HEAD/environment identity.

Installer changes must not weaken DG-P10 or any existing qualification gate.

### 5.4 Live browser shell

Serve a new authoritative product shell through the canonical server.

Required shell behavior:

- GWF product identity;
- global route skeleton;
- collapsed/expanded sidebar;
- `System | Light | Dark` theme;
- top-level navigation defined by the UI/UX contract;
- project-deep routes may exist only as unavailable/disabled placeholders where their slice is locked;
- future GAC/RA/Agent items show `PLANNED` and have no fake action;
- shell state after refresh comes from product/server/session state plus presentation-only local preferences.

BPS-I00 must **not** implement Home business KPIs or later product modules.

### 5.5 Real authentication/session bootstrap

Login must use existing GWF authentication semantics.

Because browser refresh and secret-safety are both required, BPS-I00 may add a bounded browser-session transport adapter, for example an HttpOnly/SameSite cookie wrapper, provided that:

- `HumanAuthService` remains the authentication authority;
- actor/principal/session identity remains unchanged;
- existing bearer API remains valid;
- no raw reusable credential/token is stored in static assets, `localStorage`, or readable browser persistence;
- logout/revoke uses the existing session revocation semantics;
- tenant/project authorization remains server-side.

No new identity provider or authorization model is authorized.

### 5.6 Build/backend/health identity

The live shell/diagnostic bootstrap must expose non-secret exact identity needed by BPS-I00:

- product version;
- exact Git/build SHA when available from the build/runtime contract;
- Domain identity;
- backend/database kind;
- readiness/core-health state;
- capability maturity required to render locked navigation safely.

No fabricated uptime percentage is authorized.

## 6. Allowed implementation surface

The implementation agent may modify/create only what is reasonably necessary inside these families:

- `pyproject.toml` — server runtime dependency/entry point only;
- `install.ps1` — installer/runtime separation/timing/exit contract;
- `src/gwr/api.py` — bounded browser/session/health/static-shell adapter only;
- new narrowly scoped `src/gwr/*server*.py`, `*product_info*.py`, or equivalent launcher/config helpers;
- `web/` — new shell assets/routes/styles/scripts;
- `scripts/` or `tools/` — canonical server lifecycle support, but not a second product implementation;
- `tests/` — BPS-I00 tests;
- `.gitignore` only if needed for local runtime/report paths;
- `README.md` and BPS-I00 handoff/evidence documentation.

After QA1→QA6 reaches PRE_LOCAL_PASS, this authorization also permits creation of:

```text
scripts/uiux/bps_i00_local_uat.ps1
```

The local-UAT script is **not** created before PRE_LOCAL_PASS.

## 7. Forbidden scope

BPS-I00 must not implement:

- BPS-I01 Home KPIs/Executing Projects/Live Runs/Attention aggregation;
- BPS-I02 Project/Access management UI beyond the minimum authenticated shell context;
- BPS-I03 global Operations UI;
- BPS-I04 Project Overview;
- BPS-I05 execution/recovery UI;
- BPS-I06 Package Registry/Usage;
- BPS-I07 GitHub product UI;
- BPS-I08 Artifact/Revision/Evidence Library;
- BPS-I09 DG product APIs;
- BPS-I10 Documents UI;
- BPS-I11 Document Relations/Lineage;
- DG-P11 or any source-mutation implementation;
- DG-P12+;
- GAC/Shared Library backend or functional UI;
- Reference Acquisition backend or functional UI;
- Agent Interoperability/Codex backend or functional UI;
- new migrations/data model unless a separate bounded amendment is approved;
- scientific/gate thresholds, frozen fixtures, domain semantics, recovery semantics or approval semantics.

Navigation placeholders for later slices are allowed only when visibly disabled/maturity-labelled and non-functional.

## 8. Legacy static/UAT treatment

The current static `web/` UI may be replaced/refactored as part of the new shell.

However:

- old localStorage simulated product state must not survive as authoritative behavior;
- temporary `tools/browser_uat_server.py` must not become the canonical server by renaming;
- temporary UAT overlays must not be counted as product shell completion;
- useful lessons/tests may be ported only if they conform to the new canonical architecture.

## 9. Mandatory QA before local handoff

The active implementation agent must follow root `AGENTS.md`.

BPS-I00 cannot reach PRE_LOCAL_PASS until:

1. QA1 Scope completeness PASS;
2. QA2 Functional correctness PASS;
3. QA3 Authoritative-state correctness PASS;
4. QA4 Governance/security correctness PASS;
5. QA5 automated QA/regression PASS;
6. QA6 UI/UX contract conformance PASS.

Required negative cases include at least:

- server invalid config fails closed;
- unauthorized session cannot obtain protected actor context;
- revoked/expired session cannot reconstruct authenticated UI;
- no JS-readable persisted reusable auth token;
- future navigation cannot execute fake action;
- health/backend failure is not rendered as healthy;
- canonical stop/restart cannot kill unrelated process.

## 10. Local-UAT handoff after PRE_LOCAL_PASS

Only after QA1→QA6 PASS:

```text
create/commit scripts/uiux/bps_i00_local_uat.ps1
```

Expected report:

```text
.local/BPS-I00/report/BPS-I00_LOCAL_UAT_REPORT.json
```

The script/report must satisfy root `AGENTS.md`.

Local browser checks must include:

- canonical install completes;
- canonical server start/status works;
- readiness succeeds;
- actual product shell opens;
- real login succeeds;
- refresh reconstructs authenticated shell/session without JS-readable reusable token persistence;
- dark/light/system behavior;
- sidebar expand/collapse;
- exact build/backend identity;
- future items are disabled/planned;
- stop/restart works;
- returned HEAD remains exact.

The user returns only the generated report/evidence requested by the script; the user is not responsible for manual developer debugging.

## 11. PASS states

Authorization PASS means only:

```text
BPS-I00 implementation may start
```

It does not mean:

```text
PRE_LOCAL_PASS
FINAL_SLICE_PASS
BPS-W0 PASS
BPS-I01 open
```

Those remain future evidence-dependent states.

## 12. Implementation branch rule

Implementation must occur on a dedicated branch:

```text
feature/bps-i00-product-shell
```

The branch must start from the final governance HEAD that records this authorization/plan state and must contain no product implementation before this gate.

## 13. Authorization verdict

```text
BPS_I00_BOUNDED_IMPLEMENTATION_AUTHORIZATION = PASS
BPS_I00_IMPLEMENTATION = AUTHORIZED
BPS_I00_IMPLEMENTATION_STATE = NOT_STARTED
BPS_I01 = LOCKED
DG_P11_PLUS = NOT_AUTHORIZED
GAC_RA_AI_FUNCTIONAL_UI = BLOCKED
```
