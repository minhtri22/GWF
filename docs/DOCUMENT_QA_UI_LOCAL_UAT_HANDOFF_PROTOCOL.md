# GWF — UI/UX Local UAT Handoff Protocol QA

## 1. Status

**Target:** `docs/IMPLEMENTATION_7_WAVES_PLAN.md`  
**Target blob:** `ec1b7e65c1eab9290e8d8a6923663e34996517a3`

```text
OPEN_FINDINGS = 0
VERDICT = PASS
```

**PASS — ASSISTANT-QA / LOCAL-UAT RESPONSIBILITY SPLIT LOCKED**

This QA validates the execution protocol only. It does not authorize implementation code.

## 2. Locked responsibility model

```text
Assistant
  implement active slice
    ↓
  QA1 Scope completeness
  QA2 Functional correctness
  QA3 Authoritative-state correctness
  QA4 Governance/security correctness
  QA5 Automated QA/regression
  QA6 UI/UX contract conformance
    ↓
  PRE_LOCAL_PASS
    ↓
  commit one-click PowerShell local-UAT script
    ↓
User
  pull implementation branch
    ↓
  run one PS1
    ↓
  return JSON report
    ↓
Assistant
  exact-HEAD report adjudication
    ↓
FINAL_SLICE_PASS
    ↓
next slice may open
```

## 3. QA checks

1. QA1→QA6 are explicitly assistant-owned: PASS.
2. All six checks are mandatory: PASS.
3. Failure of any QA1→QA6 keeps the same slice open: PASS.
4. User is not asked to diagnose ordinary implementation defects through manual development commands: PASS.
5. `PRE_LOCAL_PASS` exists and requires QA1→QA6 PASS: PASS.
6. PS1 creation occurs only after `PRE_LOCAL_PASS`: PASS.
7. Slice-specific script naming/location is specified under `scripts/uiux/`: PASS.
8. User workflow is pull/update + execute one script: PASS.
9. Script records exact Git HEAD start/end: PASS.
10. Script records branch/remote/worktree/environment identities: PASS.
11. Script rejects invalid dirty tracked-source state: PASS.
12. Script uses canonical installer/runtime path: PASS.
13. Script starts the actual canonical GWF server: PASS.
14. Browser slices open the real local browser product: PASS.
15. Browser-only observations require explicit operator PASS/FAIL: PASS.
16. Mutation slices require authoritative backend re-query after interaction: PASS.
17. Script stops only processes it started: PASS.
18. Logs/evidence are preserved: PASS.
19. JSON report path is deterministic: PASS.
20. JSON report schema fields are specified: PASS.
21. HEAD changing during UAT is a hard failure: PASS.
22. Mandatory failure produces non-zero exit status: PASS.
23. Script cannot alter thresholds/governance/frozen inputs to obtain PASS: PASS.
24. Failed local evidence is preserved rather than overwritten: PASS.
25. Returned report must be adjudicated by ChatGPT: PASS.
26. Returned HEAD must equal expected implementation HEAD: PASS.
27. Local failure keeps slice OPEN: PASS.
28. Local failure requires diagnosis/fix and affected QA1→QA6 rerun: PASS.
29. All BPS-I01→I11 require previous `FINAL_SLICE_PASS`: PASS.
30. BPS-I09 also requires BPS-I08 `FINAL_SLICE_PASS`: PASS.
31. BPS-W0 requires BPS-I00…I11 `FINAL_SLICE_PASS`: PASS.
32. Future BPS slices use the same QA→PS1→report→adjudication loop: PASS.
33. No stale `BPS-Ixx PASS` dependency can bypass local verification: PASS.

## 4. Script-generation rule

No generic placeholder PS1 is accepted as local evidence.

A real slice-specific PS1 is generated **after the slice implementation exists and QA1→QA6 reaches PRE_LOCAL_PASS**, because only then can the script bind to the actual server command, routes, APIs, assertions and browser checklist for that slice.

Therefore the next script to be created will be:

```text
scripts/uiux/bps_i00_local_uat.ps1
```

but only after BPS-I00 implementation + assistant QA1→QA6 PASS.

## 5. Final verdict

```text
OPEN_FINDINGS = 0
READY_FOR_BPS_I00_AUTHORIZATION = true
```
