# G2E P5A D2-S1 — Default-Permissions Materializer Result

**Status:** `IMPLEMENTATION_PASS_LOCAL_PREFLIGHT_REQUIRED`  
**Amendment QA baseline:** `3738205c16b460710e357461c29607ccd59beaea`  
**Qualified candidate:** `cd6875d6b454c6dbab929c183e844a1298af7419`  
**Workflow run:** `35643275525`  
**Workflow job:** `106477516245`  
**Artifact:** `10657909914`  
**Artifact digest:** `sha256:375cceb615770a7c32dc409c2ae9375840ee60c928b7cfb4718a96b29ee4ebb4`

## Exact implementation identities

```text
materializer blob
450a2827a949d936103c138f2d062b04513ac201

tests blob
b308ff1e6a108da808bdda8cf75dda9ee82911ea

workflow blob
d4d12da950859518ba4401306b82035fe2403caf
```

The exact qualified config now includes:

```toml
default_permissions = "g2e_p5a_d2s1"
```

and preserves the same custom profile authority.

## Canonical successor hashes

```text
config.toml sha256
8877cc89ccf5dd6e3cf6c45016ca7e62d93746c8f56db8bb38956eb6ff6e172d

P5A_D2S1_PROFILE_MATERIALIZATION.json sha256
005b19f3ce40b244b7bbde8bde7e65ae938910eb3a01e6049a3b3185b0eb2ced

execution_config_hash
d03e6f6f2c20b757685188e30f4cabd44102b61b74cdacc585bab328647b0367
```

## Qualification result

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

This result supersedes the previous D2-S1 profile pack **for future local preflight and final admission only**.

It authorizes rebinding the no-turn local preflight to the new config/execution hashes.

It does not authorize `turn/start`.
