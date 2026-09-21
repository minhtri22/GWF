# G2E P5A D2-S1 — Elevated Windows Sandbox Materializer Result

**Status:** `IMPLEMENTATION_PASS_LOCAL_PREFLIGHT_REQUIRED`  
**Amendment QA baseline:** `abb39d0092c8d5cf5b85e07e2d10a637cbe8eb68`  
**Qualified candidate:** `db74aeb24af375e0be2df234a2866be32002aa49`  
**Workflow run:** `35644589058`  
**Workflow job:** `106481827370`  
**Artifact:** `10660085814`  
**Artifact digest:** `sha256:8d1a40fb1884eb8216ddea0f0c00984d8d971a63994ecb8ce603d32c11536f4e`

## Exact implementation identities

```text
materializer blob
63a9cce5e53e779da3de82ace36f18b5dd27788e

tests blob
ec4c596d5be7fbd9d660ff21df6b6e08f6cb84bb

workflow blob
9e9b3dffb8453130e0551c59ea08135595679e9b
```

The exact qualified config now includes both:

```toml
default_permissions = "g2e_p5a_d2s1"

[windows]
sandbox = "elevated"
```

while preserving the same custom task authority.

## Canonical successor hashes

```text
config.toml sha256
a21289d995d75416ade0f4483bb93f0c54cf1808f0c2ae289c29fe89a9050cd4

P5A_D2S1_PROFILE_MATERIALIZATION.json sha256
fda500aca0707b96833e05c9a401d2fc3d00d1428a35f7db6a5f8ce28ac1f027

execution_config_hash
72874872ea241efecbdd537e0a7fbf0718fd036cf4abd564b27b0bcd03dd81ce
```

## Qualification

The exact-SHA workflow passed:

- bounded amendment implementation diff;
- compile;
- P1 regression;
- P1.4 regression;
- P1.5 regression;
- P2 regression;
- P3 regression;
- P4 regression;
- D2-S1 materializer tests;
- canonical re-materialization;
- independent verification;
- artifact publication.

No model turn occurred and no scientific attempt was authorized.

## Authorization

This result authorizes rebinding the local no-turn preflight to:

- the elevated config hash above;
- the elevated execution-config hash above;
- `windowsSandbox/readiness`;
- `windowsSandbox/setupStart(mode=elevated)` when readiness is `updateRequired`;
- a required final readiness state of `ready`.

It does not authorize `turn/start`.
