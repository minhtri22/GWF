# P5A-CGW Q0b Runtime Target Correction — v4.0.7

## Status

**TARGET CORRECTION FROZEN / v5.0.8 ALIGNMENT AUTHORIZATION REVOKED BEFORE LOCAL MUTATION / ZERO-MODEL**

## Operator constraint

For the current P5A-CGW phase, the target deployed runtime is intentionally:

`codex-chatgpt-web v4.0.7`

The machine is not to be upgraded to v5.0.8 in this phase.

The prior v5.0.8 alignment successor was created from an incorrect target-runtime assumption. The local wrapper invocation failed closed at `QUIT_CODEX_WEB_GPT_BEFORE_RUNTIME_ALIGNMENT` before any installer download, runtime mutation, model turn, browser submission, MCP invocation, or scientific-attempt creation.

Therefore the qualified-but-not-executed v5.0.8 alignment authorization is **revoked** and must not be invoked again.

## Exact v4.0.7 provenance frozen now

- upstream repository: `miuuyy/codex-chatgpt-web`
- release tag: `v4.0.7`
- annotated tag object: `425092367f5cbfa33a071e460dbd72215bf0b9fa`
- source commit: `b59d7dc51b84fb1f465ff1d00f5207f3b2b4a494`
- source `src/version.ts`: `4.0.7`
- release published: `2026-08-31`
- Windows x64 launcher asset SHA-256:
  `90f47feaa5c6c17612ac9bee6a49b11b65e0241b046b7380e2c5219792a55354`
- Windows runtime ZIP SHA-256:
  `49f51bed4b85c7d5d54707b09791fa8360f653f97532e0dc16aceeb04d1dd611`

Frozen exact source blobs:

- `src/server.ts`: `af4cd5c3886f119f35efa4fc0e28bd2ecfc48530`
- `src/config.ts`: `1444c64ab66282e72411585392e3d242773a971a`
- `src/chatgpt-web-models.ts`: `dae14ce18737d4bdd7206b3df453b20f30a073ea`
- `src/codex-integration.ts`: `ca7210f0922972ac46bbed94107f5dd65cbc224f`
- `src/codex-integration-route.ts`: `19841e3e0db5f5dfb62007d3669eb1f8adea2798`
- `docs/security-model.md`: `cb1e4db10e462df3cb8040b83207982f6efa833a`
- `src/version.ts`: `328cfba86faf2cccb9e98f35439abdeb5cfb5e5f`

## What is already supported by v4.0.7 source

Static source inspection confirms the core authority model required by P5A-CGW already exists in v4.0.7:

- loopback daemon / Responses route;
- `Codex Native2` connector identity;
- outer Codex turn owns sandbox/approval/tool execution;
- bridge does not become a second planner/router;
- MCP may request only tools advertised by the active outer Codex turn;
- legacy `Codex Native` is not a fallback;
- health/version/mode identity is exposed.

No v5-only feature may be silently imported into the v4.0.7 qualification contract.

## Existing local Q0b evidence

The first local Q0b report observed a healthy v4.0.7 deployment but was marked BLOCKED solely because the then-frozen qualifier expected v5.0.8.

That report is **not retroactively promoted to PASS by this correction alone**.

It may be re-adjudicated only after a dedicated exact-v4.0.7 source/contract qualification passes. Re-adjudication must be read-only and must not create a new browser/model turn.

## Current authorization

- runtime upgrade to v5.0.8: **REVOKED**
- rerun of `p5a_cgw_q0b_align_runtime_5_0_8.ps1`: **FORBIDDEN**
- runtime downgrade/upgrade: **NOT AUTHORIZED**
- v4.0.7 source/contract zero-model qualification: **NEXT**
- read-only re-adjudication of existing Q0b evidence: **ONLY AFTER v4 source qualification PASS**
- first functional P5A-CGW attempt: **NOT AUTHORIZED**
- A/B with P5A official: **NOT AUTHORIZED**
