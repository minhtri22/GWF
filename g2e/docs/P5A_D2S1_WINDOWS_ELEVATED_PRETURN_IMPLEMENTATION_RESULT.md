# G2E P5A D2-S1 — Elevated Windows Preturn Implementation Result

**Status:** `IMPLEMENTATION_PASS_LOCAL_EXECUTION_REQUIRED`  
**Materializer closure baseline:** `d02e1a93f531ace89f97ea89c8cfb4faa9a5289f`  
**Qualified candidate:** `46d23cfc4ee903b22f4e75e9833b6f210c1374da`  
**Workflow run:** `35644949786`  
**Workflow job:** `106483017569`  
**Artifact:** `10660151258`  
**Artifact digest:** `sha256:eca874b89aa7d90b5d92069c3b9546b23c4a4844d15a4d67bba2bb70940ba47c`

## Exact qualified implementation

```text
scripts/g2e/p5a_d2s1_local_preflight.py
blob 062920e6d27289ec6285fa0e6c2da3d7ffd85a70

tests/g2e/test_p5a_d2s1_local_preflight.py
blob d2e61ce190ef58595d8ccec78e357f59877803d4

.github/workflows/g2e-p5a-d2s1-local-preturn.yml
blob a7131a702adf51161f0334e593b660c2d61e54b4
```

The preflight is bound to:

```text
config.toml sha256
a21289d995d75416ade0f4483bb93f0c54cf1808f0c2ae289c29fe89a9050cd4

execution_config_hash
72874872ea241efecbdd537e0a7fbf0718fd036cf4abd564b27b0bcd03dd81ce
```

## Qualified no-turn sequence

The implementation performs only:

```text
initialize(experimentalApi=true)
windowsSandbox/readiness
if updateRequired:
    windowsSandbox/setupStart(mode=elevated, cwd=exact workspace)
    wait windowsSandbox/setupCompleted(success=true)
windowsSandbox/readiness -> ready
MCP/apps/auth/profile checks
thread/start permissions=g2e_p5a_d2s1
STOP
```

It contains no `turn/start` dispatch.

It also fails closed if elevated setup mutates canonical `config.toml` bytes away from the frozen hash.

## Qualification result

The exact-SHA workflow passed:

- bounded diff;
- compile;
- P1 regression;
- P1.4 regression;
- P1.5 regression;
- P2 regression;
- P3 regression;
- P4 regression;
- elevated no-turn preflight static tests;
- explicit proof of no scientific dispatch token;
- artifact publication.

## Authorization state

```text
model_turn_executed           false
scientific_attempt_authorized false
runtime_adapter_authorized    false
```

This result authorizes one fresh local elevated-sandbox **no-turn preflight** only.

A scientific D2-S1 model turn remains prohibited.
