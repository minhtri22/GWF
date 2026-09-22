# G2E P5A D2-S2 — Local No-Turn Preturn Execution Authorization

## Status

**Decision:** AUTHORIZE ONE BOUNDED LOCAL PRETURN EXECUTION  
**Scientific model turn:** NOT AUTHORIZED  
**Scientific attempt:** NOT AUTHORIZED / NOT CONSUMED  
**Runtime adapter:** NOT AUTHORIZED

## 1. Authorization basis

This authorization is issued only after fresh local bootstrap evidence returned from the qualified
diagnostic return wrapper.

Bound evidence:

- return schema: `G2E-P5A-D2S2-ELEVATION-BOOTSTRAP-RETURN-v1`
- return file: `P5A_D2S2_ELEVATION_BOOTSTRAP_REPORT_2fe4590d9fa6_20260922T022030175Z.json`
- return-file SHA256: `d007689fb69c82278fe26ea4e3c8fa7090fbfc274744a8145e3563acad2e1c55`
- wrapper exact HEAD: `2fe4590d9fa67a6c184be99f4b5d996889fe504f`
- freshness verified: `true`
- diagnostic status: `DIAGNOSTIC_PASS`
- diagnostic exit code: `0`
- elevated process: PASS / admin token present
- Git worktree excluding local artifacts: CLEAN
- prior `g2e/.local/P5A-D2S2` root: ABSENT
- exact Codex executable hash:
  `a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8`
- qualified one-click blob:
  `1507b716645971ee60b0c2131973a953f98e7036`
- qualified preflight blob:
  `005bd3ff5f34ea60a05d15baa25a0d4f6e9341c3`
- scientific attempt consumed by diagnostic: `false`
- model turn executed by diagnostic: `false`

## 2. Authorized executable

Exactly one fresh local invocation of:

`scripts/g2e/p5a_d2s2_isolated_volume_oneclick.ps1`

The invocation may execute only the already-qualified D2-S2 no-turn preflight contract.

## 3. Authorized operations

The bounded preturn execution may:

1. require/elevate to Administrator;
2. verify the existing D2-S2 one-click qualification lock and exact frozen blobs;
3. require a clean Git worktree and detach to exact remote branch state;
4. create the bounded local root `g2e/.local/P5A-D2S2/`;
5. create, attach, format and mount the 128 MiB isolated VHDX;
6. copy only the frozen P5-FX-001 `TASK.md` and `input.json` into the isolated volume;
7. verify exact fixture hashes;
8. create fresh D2-S2 `CODEX_HOME` and permission profile;
9. start Codex App Server only for no-turn platform qualification;
10. execute the frozen RPC sequence through:
    - `initialize`
    - `windowsSandbox/readiness`
    - conditional `windowsSandbox/setupStart`
    - `mcpServerStatus/list`
    - `app/installed`
    - `account/read`
    - `permissionProfile/list`
    - `thread/start`
11. STOP immediately after thread qualification;
12. write the bounded JSON/Markdown preturn report and evidence.

## 4. Explicit prohibitions

This authorization does **not** permit:

- `turn/start`;
- any model-generated scientific result;
- any D2-S2 scientific attempt consumption;
- retry/rescue of D2 or D2-S1;
- broad host-drive task visibility;
- network access;
- repository read/write scientific claims;
- runtime-adapter admission;
- automatic continuation from `PRETURN_PASS` into science.

## 5. Fail-closed adjudication

Only the frozen preturn verdict family is admissible:

- `PRETURN_PASS`
- `PRETURN_BLOCKED_PLATFORM`
- `PRETURN_BLOCKED_AUTHORITY`
- `PRETURN_INVALID`

Every verdict is pre-scientific.

If the execution produces `PRETURN_PASS`, execution must STOP and the returned report must be adjudicated
before any separate scientific-attempt authorization can exist.

If execution blocks or fails, do not rerun automatically. Preserve the local evidence and adjudicate the
failure first.

## 6. Authorization boundary

This authorization is single-purpose and single-stage:

`DIAGNOSTIC_PASS -> ONE D2-S2 NO-TURN PRETURN EXECUTION -> STOP`

It is not a scientific admission decision.
