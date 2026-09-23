# P5A-CGW Q0b Runtime Alignment Successor

## Origin

The first authorized local Q0b collection was structurally healthy but blocked because the installed CGW runtime reports `4.0.7` while the frozen P5A-CGW source/runtime reference requires `5.0.8`.

This workstream is not a functional-attempt rescue. No model turn occurred, no scientific attempt was created or consumed, and the mismatch is independent of task outcome.

## Frozen repair

Exactly one environment change is admissible:

`installed CGW 4.0.7 -> frozen CGW 5.0.8`

The specification is not retargeted to 4.0.7.

## Trust chain

Pinned release:

- repository: `miuuyy/codex-chatgpt-web`
- tag: `v5.0.8`
- source commit: `eaf4f09ae92d4dc4429fa597b0861663138f08f8`
- release installer script SHA-256:
  `117ab8e5bfba36d3f611e9294355afe70936a536bf3305d4fe563edab7c40a71`
- Windows x64 installer asset SHA-256:
  `83224d59506462ab2976f437bfaea96b046d4ed55caa7e1cfd6a3d61de0a8ff3`

The wrapper downloads the exact v5.0.8 installer script, verifies its digest, sets `CODEX_WEB_GPT_VERSION=5.0.8`, and delegates package checksum validation/installation to that frozen upstream installer.

## Preconditions

Before mutation:

- exact observed source runtime must still be `4.0.7`;
- route host must be loopback;
- mode must be `full`;
- connector must be `Codex Native2`;
- auto approval must remain false;
- Codex route must point at the observed CGW port;
- launcher must be quit.

## Postconditions

After alignment:

- config release = `5.0.8`;
- `/healthz` service/version/mode is coherent and accepting turns;
- host/mode/connector/auto-approval invariant preserved;
- Codex route still points at the resulting loopback bridge;
- no model endpoint or Codex turn is invoked.

Only then may the wrapper invoke the already-qualified local Q0b collector once under a new root:

`g2e/.local/P5A-CGW-ZERO-MODEL-Q0B-R2`

## Current authorization

Before CI qualification of this wrapper:

- local runtime mutation: NOT AUTHORIZED
- fresh Q0b collection: NOT AUTHORIZED
- model turn: NOT AUTHORIZED
- functional attempt: NOT AUTHORIZED
- A/B comparison: NOT AUTHORIZED
