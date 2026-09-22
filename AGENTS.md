# GWF Agent Execution Protocol

## 1. Mandatory first read

This file is the canonical execution/handoff protocol for GWF implementation agents.

For any Browser Product Surface / UI/UX implementation work, **an agent MUST read this file before inspecting, editing, testing, committing, or authorizing product code**.

This rule applies to:

- current BPS slices `BPS-I00…I11`;
- future `BPS-DG*`, `BPS-GAC`, `BPS-RA`, `BPS-CODEX`, or equivalent product-integration slices;
- any handoff/resume of an already-open BPS slice.

A chat summary or prior-agent prose is context only. Repository state and the exact documents below are authoritative.

## 2. Mandatory read set before work

Before touching an active BPS slice, the receiving agent must resolve and read:

1. `AGENTS.md` — this protocol;
2. `docs/IMPLEMENTATION_7_WAVES_PLAN.md` — current execution order and active slice;
3. `docs/UI_UX_PRODUCT_ARCHITECTURE_SPEC.md` — UI/UX implementation contract;
4. `docs/UI_UX_QA.md` — closed coverage/traceability findings;
5. `docs/BROWSER_PRODUCT_SURFACE_SPEC.md` — maturity/authority boundary;
6. the active slice authorization document;
7. any exact backend specification/handoff named by that authorization;
8. `docs/TECHNICAL_DEBT.md` when the active slice touches recorded debt.

The handoff must record the exact Git HEAD and exact blob/SHA identities used for these governing inputs.

## 3. Mandatory acknowledgement before modification

The receiving agent must establish, explicitly in its working notes/handoff state, all of the following before the first product-code mutation:

```text
ACTIVE_SLICE
BASE_HEAD
PROTOCOL_READ = AGENTS.md
PLAN_BLOB
UI_UX_SPEC_BLOB
UI_UX_QA_BLOB
BROWSER_SURFACE_SPEC_BLOB
AUTHORIZATION_BLOB
PREDECESSOR_FINAL_SLICE_PASS_EVIDENCE
ALLOWED_SCOPE
FORBIDDEN_SCOPE
EXPECTED_LOCAL_UAT_SCRIPT
EXPECTED_LOCAL_UAT_REPORT
```

If any required identity is absent, inconsistent or stale, implementation does not start.

## 4. One-slice-at-a-time invariant

Only one BPS implementation slice may be OPEN.

```text
slice N authorized
  -> implement slice N only
  -> assistant QA1→QA6
  -> PRE_LOCAL_PASS
  -> one-click local PS1
  -> returned JSON report
  -> exact-HEAD adjudication
  -> FINAL_SLICE_PASS
  -> only then slice N+1 may open
```

No implementation from a later locked BPS slice is pulled forward because it appears convenient.

## 5. Backend-before-UI invariant

A browser surface may be implemented only for:

- backend/runtime capability already qualified; or
- a bounded API/read projection required to browserize already-qualified capability and explicitly allowed by the active BPS authorization.

A capability whose backend/governance work is not formally qualified remains `PLANNED_BLOCKED`.

Future sequence:

```text
backend spec/gate
  -> backend implementation
  -> backend QA/formal-close
  -> bounded BPS integration slice
  -> QA1→QA6
  -> local PS1/report
  -> FINAL_SLICE_PASS
```

No fake future UI, fake Connect button, fake mutation, or mock authoritative state is accepted.

## 6. Assistant-owned QA1→QA6

The implementation agent/ChatGPT owns these checks before local user handoff.

### QA1 — Scope completeness

- every item frozen for the active slice is implemented;
- no mandatory item is skipped;
- no later-slice feature is implemented without amendment.

### QA2 — Functional correctness

- behavior matches qualified runtime/service semantics;
- statuses, counts, transitions and exact identities are correct;
- positive and negative paths are verified.

### QA3 — Authoritative-state correctness

- backend/database is authoritative;
- refresh/re-entry reconstructs product state;
- localStorage/fixtures/demo JSON/mock state never substitutes for product truth;
- browser-local persistence is limited to presentation preference/transient form state.

### QA4 — Governance and security correctness

- tenant/workspace/project authority is preserved;
- approval/hash/revision/SHA/stale/version checks are preserved;
- archive/read-only/mutation-authority rules are preserved;
- secrets and hidden-resource existence are not leaked.

### QA5 — Automated QA and regression

- targeted tests PASS;
- affected regression PASS;
- full/subsystem gates required by touched code PASS;
- SQLite/PostgreSQL checks run wherever the existing qualified gate requires them;
- negative tests are included.

### QA6 — UI/UX contract conformance

- navigation/information architecture matches the locked spec;
- dark/light/system behavior is correct for implemented surfaces;
- sidebar/routing behavior is correct;
- loading/empty/partial/error/unauthorized/planned states are distinct;
- exact identities remain inspectable/copyable;
- no invented connector/capability/action appears.

All six are mandatory:

```text
QA1 PASS
AND QA2 PASS
AND QA3 PASS
AND QA4 PASS
AND QA5 PASS
AND QA6 PASS
  -> PRE_LOCAL_PASS
```

If any QA fails, the assistant fixes/retests the same slice. The user is not used as a manual defect-discovery loop.

## 7. PRE_LOCAL_PASS is not final PASS

`PRE_LOCAL_PASS` only authorizes creation of the local-UAT handoff script.

It does not:

- formal-close the slice;
- open the next slice;
- count as operator UAT;
- authorize a new backend phase.

## 8. Mandatory one-click local PowerShell handoff

After PRE_LOCAL_PASS, commit one slice-specific script:

```text
scripts/uiux/bps_iNN_local_uat.ps1
```

Future slice scripts use the same directory with a stable slice-derived name.

The user's normal responsibility is:

```powershell
git fetch --prune origin <implementation-branch>
git switch <implementation-branch>
git pull --ff-only

& ".\scripts\uiux\<slice>_local_uat.ps1"
```

The user should not need a manual sequence of development/test commands.

## 9. Local-UAT script contract

The script must:

1. use strict PowerShell error handling;
2. discover repo root;
3. record HEAD start/end, branch, origin, worktree state, Windows/PowerShell/Python identity and timestamps;
4. reject dirty tracked-source state except explicitly allowlisted local/report paths;
5. invoke the canonical installer/runtime path, not a parallel UAT implementation;
6. run machine-verifiable local checks required by the slice;
7. for browser slices, start the actual canonical GWF server;
8. poll authoritative readiness/health with timeout;
9. open the real local browser product;
10. present a bounded manual browser checklist;
11. collect explicit operator PASS/FAIL only for observations not machine-provable;
12. after browser mutation, re-query authoritative API/backend state;
13. stop only processes it started;
14. preserve logs/stdout/stderr/evidence;
15. emit one machine-readable JSON report under:

```text
.local/<SLICE-ID>/report/<SLICE-ID>_LOCAL_UAT_REPORT.json
```

16. include schema, slice ID, HEAD start/end, clean-state result, environment, machine checks, manual checks, server/API evidence, evidence paths and local verdict;
17. fail if HEAD changes during UAT;
18. exit nonzero for a mandatory failure;
19. never modify thresholds, frozen fixtures, governance/scientific configuration or product semantics to obtain PASS;
20. preserve failed evidence; later reruns produce new evidence rather than erasing history.

API-only slices may omit opening a browser only when the active slice authorization explicitly says browser interaction is not part of that slice. They still use the same exact-HEAD local-report discipline.

## 10. Returned-report adjudication

The user returns the JSON report.

The agent verifies:

- expected report schema;
- mandatory machine checks PASS;
- mandatory manual checks PASS where applicable;
- start/end HEAD identical;
- returned HEAD exactly equals the expected implementation HEAD;
- no invalid dirty-worktree state;
- required evidence/log paths exist;
- no local result contradicts QA1→QA6.

Only then:

```text
FINAL_SLICE_PASS
```

If the local report fails, the slice remains OPEN. Diagnose/fix, rerun affected QA1→QA6, and issue a new local script/report cycle.

## 11. Exact-HEAD and evidence invariant

Never transfer a PASS across commits.

If implementation code changes after PRE_LOCAL_PASS:

- PRE_LOCAL_PASS is invalidated for affected checks;
- affected QA1→QA6 must rerun;
- the local-UAT script/report must bind the new exact HEAD.

Failed evidence is preserved.

## 12. Handoff package contract

Every BPS handoff to another agent must contain:

- active slice and state;
- implementation branch;
- exact HEAD;
- predecessor FINAL_SLICE_PASS evidence;
- exact governing-document blob identities;
- active authorization identity;
- implemented file list;
- outstanding scope;
- QA1→QA6 status and evidence;
- PRE_LOCAL_PASS status;
- local-UAT script path;
- expected JSON report path;
- returned local report/adjudication if one exists;
- known failures/negative evidence;
- explicit next legal action.

The receiving agent must reread the Mandatory read set rather than relying only on this summary.

## 13. Legacy UAT tooling warning

The following governance-branch tools predate canonical BPS implementation:

- `tools/browser_uat_server.py`;
- `tools/start_browser_uat.ps1`;
- `tools/uat_dg_p0_p10_local.ps1`.

They are historical/temporary UAT tooling.

They must **not** be treated as:

- the canonical installed product server;
- the final product UI;
- evidence that BPS-I00 already exists;
- a substitute for the slice-specific `scripts/uiux/*_local_uat.ps1`.

They may be inspected for historical lessons but must not define product architecture.

## 14. Documentation and lineage discipline

- `Finding_checklist.md` is not used as the runtime/BPS implementation tracker.
- Technical debt remains in `docs/TECHNICAL_DEBT.md`.
- `LINEAGE.md` records only final important milestone/gate results, not repair attempts.
- A documentation PASS does not imply implementation authorization.
- An implementation QA PASS does not imply FINAL_SLICE_PASS.
- FINAL_SLICE_PASS does not authorize an unrelated backend phase.

## 15. Stop conditions

Stop implementation and return to governance if:

- active slice authorization is missing/ambiguous;
- exact governing identities cannot be reconstructed;
- implementation requires semantics owned by a future blocked backend item;
- satisfying the UI would require weakening an existing authority/identity/evidence rule;
- scope must expand materially beyond the authorization.

Do not silently broaden the slice.
