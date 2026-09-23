# BPS-I00 — UI Conformance Reimplementation Contract

## 1. Status

```text
SLICE                     = BPS-I00
PROGRAM                   = UI_CONFORMANCE_RECOVERY
AUTHORITY                 = AUTHORIZED_BOUNDED_BY_USER
BASE_GOVERNANCE_HEAD      = ebf3504e117cdfa5a3e91b581d1d2f425c97b230
APPROVED_BASELINE         = GWF-UI-BASELINE-v1.1
HISTORICAL_PRE_LOCAL_PASS = INVALIDATED
CODE_STATE                = NOT_STARTED_UNDER_THIS_CONTRACT
FINAL_SLICE_PASS          = NO
BPS-I01                   = LOCKED
```

This contract authorizes correction of the BPS-I00 **visual shell foundation only** after local UAT proved that the first shell implementation did not faithfully match the approved UI/UX direction.

## 2. Goal

Reimplement the browser shell so that it is unmistakably the approved **Governed Knowledge Studio** foundation rather than a restyled legacy v0.8.5 dashboard, while preserving already-qualified canonical server/auth/session/runtime behavior.

## 3. Governing references

- `AGENTS.md`;
- `docs/UI_UX_PRODUCT_ARCHITECTURE_SPEC.md`;
- `docs/uiux/approved/UI_VISUAL_BASELINE_MANIFEST.md`;
- `docs/uiux/approved/GWF_UI_BASELINE_v1_1_APPROVED.jpg`;
- `docs/UI_UX_VISUAL_BASELINE_QA.md` with `OPEN=0`;
- Amendment 1 of `docs/BPS_I00_IMPLEMENTATION_AUTHORIZATION.md`.

## 4. Product-code surface allowed

Primary implementation files:

```text
web/index.html
web/app.js
web/styles.css
tests/test_bps_i00_product_shell.py
```

Additional BPS-I00 browser tests may be added when narrowly necessary.

After new QA1→QA6 PASS, the existing local-UAT script/tests may be updated only as required to test the corrected shell.

No `src/gwr`, migration, database, governance or backend semantic change is authorized by this recovery contract. If one becomes necessary, STOP and amend the contract first.

## 5. Required result

The corrected BPS-I00 shell must demonstrate:

- approved global shell hierarchy and professional/compact visual language;
- semantic icons, not first-letter placeholders;
- ~260 px expanded sidebar and ~68 px collapsed rail;
- collapse reflows the workspace so the released width is usable;
- descriptive tooltip/focus labels and maturity context in collapsed mode;
- full-shell `System | Light | Dark` parity including sidebar/top bar/content;
- project-centered information architecture skeleton;
- locked/planned later capabilities remain non-functional;
- exact runtime/build/backend identity remains inspectable;
- no legacy static/demo/localStorage product authority.

The approved Documents/Relations/Preview composition is a visual **future-slice reference** only. BPS-I00 must not implement functional Documents/Relations/Reader workflows.

## 6. Acceptance

Before a new PRE_LOCAL_PASS:

1. QA1 scope completeness PASS;
2. QA2 shell behavior PASS;
3. QA3 authoritative-state boundary PASS;
4. QA4 auth/security boundary PASS;
5. QA5 targeted + affected/full regression PASS;
6. QA6 visual baseline conformance PASS.

QA6 must include reference-state evidence for desktop:

- Dark / expanded sidebar;
- Dark / collapsed sidebar;
- Light / expanded sidebar;
- Light / collapsed sidebar.

The evidence must show actual workspace reflow, semantic icons/tooltips and full-shell theme parity.

Only then may a new exact-head local UAT be handed to the user.

## 7. Explicit non-scope

```text
NO BPS-I01 functionality
NO Home KPI implementation
NO Projects/Operations functional modules
NO Documents API/UI functionality
NO Relations graph functionality
NO full-screen Reader functionality yet
NO source-code sandbox/replay implementation
NO DG-P11+
NO GAC/RA/AI functional UI
```

Those remain later authorized slices/debt.

## 8. Stop rule

If matching the approved design requires backend semantics or later-slice capability, STOP and request a bounded amendment. Do not fake the capability and do not silently widen BPS-I00.
