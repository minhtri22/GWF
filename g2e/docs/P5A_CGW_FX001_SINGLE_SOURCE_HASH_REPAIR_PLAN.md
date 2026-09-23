# P5A-CGW FX001 — Single-Source Launcher Hash Repair

## Trigger

V2R3 preflight-only produced:

- observed launcher SHA-256:
  `AC152AD499B1F41B2CAFE94A3D05F5D4E4D3CD7DDBB417B9C60B118B08BC3CBB`
- expected launcher SHA-256 printed by wrapper:
  `AC152AD499B1F41B2CAFE94A3D05F5D4E4D3CD7DBB417B9C60B118B08BC3CBB`

Exact source inspection showed the wrapper's duplicated hardcoded expected hash was only 63 characters, while the V2R3 lock contained the correct 64-character frozen hash.

The local runtime did not drift. The preflight remained pre-marker and the reserved attempt stayed unconsumed.

## Repair

V2R4 removes the duplicated launcher-hash literal from the wrapper.

The wrapper now derives:

`ExpectedCgwSha = Lock.launcher_identity.expected_sha256`

and normalizes it with trim + uppercase before comparison.

Before using it, the wrapper requires:

`^[A-F0-9]{64}$`

Otherwise it blocks with:

`LOCK_CGW_LAUNCHER_SHA256_INVALID`.

The launcher resolution rule from V2R3 remains unchanged:

- identity must be `Codex Web GPT.exe`;
- no fallback to `runtimeCommand[0]`;
- Bun may remain the bridge runtime command but is not the frozen CGW launcher identity.

## Scientific contract

Unchanged:

- attempt identity;
- CGW release 4.0.7;
- Codex binary;
- route/model/mode/connector;
- task/result;
- authority;
- durable-marker consumption boundary;
- retry=0;
- timeout=90s;
- evidence requirements.

## Qualification

Linux and Windows zero-model QA must prove:

- wrapper binds V2R4;
- no launcher SHA-256 literal remains in wrapper;
- expected launcher hash is read from the lock;
- lock hash must validate as 64 hexadecimal characters;
- launcher-only identity rule remains enforced;
- PowerShell 5.1 parser and all existing runner/verifier/preregistration regressions remain PASS.
