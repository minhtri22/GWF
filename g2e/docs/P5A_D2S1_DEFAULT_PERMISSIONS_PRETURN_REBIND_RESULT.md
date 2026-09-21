# G2E P5A D2-S1 — Default-Permissions Preturn Rebind Result

**Status:** `IMPLEMENTATION_PASS_LOCAL_EXECUTION_REQUIRED`  
**Materializer closure baseline:** `183326a7f1fac182ae65dca9693e3e597809e380`  
**Qualified candidate:** `3d66054c6205a4f948a2c47bf2c1205abd41e103`  
**Workflow run:** `35643475732`  
**Workflow job:** `106478182525`  
**Artifact:** `10659113659`  
**Artifact digest:** `sha256:4d4fd2716dd4b8e93c2276938bd0c80f8ac637a24a2dcfd40517a8c729768fcc`

## Exact qualified implementation

```text
scripts/g2e/p5a_d2s1_local_preflight.py
blob f31687db775aaa613bd851bf050855a14dc0800f

tests/g2e/test_p5a_d2s1_local_preflight.py
blob 17af97b6772f911874b7528586349ae5a8451533

.github/workflows/g2e-p5a-d2s1-local-preturn.yml
blob 42044854bb7622a9f6a1d570a6418ddda62b4a3e
```

The preflight is now rebound to the amended canonical hashes:

```text
config.toml sha256
8877cc89ccf5dd6e3cf6c45016ca7e62d93746c8f56db8bb38956eb6ff6e172d

execution_config_hash
d03e6f6f2c20b757685188e30f4cabd44102b61b74cdacc585bab328647b0367
```

## Qualification result

The exact-SHA workflow passed:

- bounded rebind diff;
- compile;
- P1 regression;
- P1.4 regression;
- P1.5 regression;
- P2 regression;
- P3 regression;
- P4 regression;
- no-turn preflight static tests;
- explicit proof that the preflight source contains no `"turn/start"` dispatch token;
- artifact publication.

## Authorization state

```text
model_turn_executed           false
scientific_attempt_authorized false
runtime_adapter_authorized    false
```

This result authorizes a fresh local no-turn preflight only.

The previous local D2-S1 preflight evidence that failed on missing `default_permissions` is historical blocker evidence and MUST NOT be overwritten or reused.

A scientific D2-S1 model turn remains prohibited.
