# G2E P5A D2-S2 — Isolated-Volume One-Click Qualification Result

**Status:** `IMPLEMENTATION_PASS_LOCAL_EXECUTION_REQUIRED`  
**Zero-fresh QA baseline:** `e1b1c2e64a8ee341974a5635b831d46cc4f01198`  
**Qualified candidate:** `7d81e183a9e1c895f610fa3c377b54fc0e3e413d`  
**Workflow run:** `35672727732`  
**Workflow job:** `106572590013`  
**Artifact:** `10671393590`  
**Artifact digest:** `sha256:92790a09dece5d24b4ff097a8cd6b879f94e4db536f1249e756108a7e56c8354`

## Exact qualified implementation

```text
scripts/g2e/p5a_d2s2_isolated_volume_oneclick.ps1
blob 1507b716645971ee60b0c2131973a953f98e7036

scripts/g2e/p5a_d2s2_isolated_volume_preflight.py
blob 005bd3ff5f34ea60a05d15baa25a0d4f6e9341c3

tests/g2e/test_p5a_d2s2_isolated_volume_preflight.py
blob a4aa31f4c52998b6eaff7c737740d5a9f2c84ecb

.github/workflows/g2e-p5a-d2s2-isolated-volume.yml
blob 6823cfe52b4f7565c095bed3cf0f1edd202fffb2
```

## Qualification

The exact-SHA workflow passed:

- bounded implementation diff;
- Python compile;
- PowerShell parser validation;
- P1 regression;
- P1.4 regression;
- P1.5 regression;
- P2 regression;
- P3 regression;
- P4 regression;
- D2-S2 static qualification;
- explicit proof that neither local preflight nor one-click wrapper contains `"turn/start"`;
- artifact publication.

## One-click behavior

The runner:

1. verifies a qualification lock;
2. requires a clean worktree;
3. fetches and detaches to the current remote `feature/g2e-framework` HEAD;
4. verifies exact qualified script/preflight blobs;
5. self-elevates through UAC if required;
6. creates a fresh 128 MiB VHDX below `g2e/.local/P5A-D2S2/`;
7. deterministically selects the first unused drive from R..Z;
8. copies and hash-verifies the frozen P5-FX-001 fixture;
9. proves the task volume initially contains only `TASK.md` and `input.json`;
10. creates an elevated permission profile with isolated-volume `:root = read`, exact `result.json` write and network disabled;
11. executes the no-turn App Server preflight;
12. emits both JSON and Markdown reports.

## Report paths

```text
g2e/.local/P5A-D2S2/report/P5A_D2S2_ONECLICK_REPORT.json
g2e/.local/P5A-D2S2/report/P5A_D2S2_ONECLICK_REPORT.md
```

## Authorization state

```text
model_turn_executed           false
scientific_attempt_authorized false
runtime_adapter_authorized    false
```

This result authorizes exactly one fresh local D2-S2 isolated-volume **no-turn preflight**.

It does not authorize a scientific model turn.
