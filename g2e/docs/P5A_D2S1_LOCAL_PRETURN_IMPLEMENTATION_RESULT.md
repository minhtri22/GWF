# G2E P5A D2-S1 — Local Preturn Implementation Result

**Status:** `IMPLEMENTATION_PASS_LOCAL_EXECUTION_REQUIRED`  
**Qualified candidate:** `ec6aaa1d296f9eb737d79ef4aa7470f95791a705`  
**Baseline:** `3014692ef75a5ccd707907e1b28a14f273d45dfa`  
**Workflow run:** `35630980327`  
**Workflow job:** `106436822474`  
**Artifact:** `10654433662`  
**Artifact digest:** `sha256:b939301225645cb991ae315955d1ef5b7866680dbe3acb396365417236ed4cc3`

## Exact qualified implementation

```text
scripts/g2e/p5a_d2s1_local_preflight.py
blob a5d5369c4c2ecf042bebc77028deda3b33e6c6d4

tests/g2e/test_p5a_d2s1_local_preflight.py
blob f12923dc2579e92426cb1fa65ba5c8443ab56f75

.github/workflows/g2e-p5a-d2s1-local-preturn.yml
blob c173ed5e3d0c84d9f9205dda7f7d0aca5d62c2fc
```

## Qualification result

The exact-SHA workflow passed:

- bounded implementation diff;
- Python compile;
- P1 regression;
- P1.4 regression;
- P1.5 regression;
- P2 regression;
- P3 regression;
- P4 regression;
- D2-S1 preflight static qualification;
- explicit proof that the preflight source contains no `"turn/start"` dispatch token;
- artifact publication.

The implementation is therefore qualified only for the prospectively specified **local no-turn preflight**.

## Local preflight contract

The local preflight must prove on the exact Windows/Codex 0.153.4 environment:

```text
experimentalApi negotiation    true
configured MCP count           0
installed/callable apps        0
auth ready                     true
profile g2e_p5a_d2s1 present   true
profile allowed                true
thread/start permissions       accepted
thread ID                      present
active profile, if emitted     exact
instructionSources             []
turn/start                     NOT SENT
result.json                    absent
```

All mutable local paths are required to remain under:

```text
D:\WORK\RESEARCH\4.GWF\g2e\.local\P5A-D2S1\
```

## Authorization state

```text
model_turn_executed           false
scientific_attempt_authorized false
runtime_adapter_authorized    false
```

This implementation PASS does **not** establish that the profile is accepted on the user's Windows host. That requires the one no-turn local preflight.

A scientific D2-S1 model turn remains prohibited until:
1. local preflight PASS is frozen;
2. successor final admission is separately materialized and qualified;
3. that final admission explicitly opens one scientific attempt.
