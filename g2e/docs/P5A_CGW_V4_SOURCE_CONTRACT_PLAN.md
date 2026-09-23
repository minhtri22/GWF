# P5A-CGW — Exact v4.0.7 Source/Contract Qualification

## Status

IMPLEMENTATION CANDIDATE / ZERO-MODEL / READ-ONLY

## Question

Can the already-installed and already-observed codex-chatgpt-web v4.0.7 route satisfy the P5A-CGW trust/authority/observability admission contract without importing v5-only assumptions?

## Frozen source identity

- tag: v4.0.7
- tag object: 425092367f5cbfa33a071e460dbd72215bf0b9fa
- source commit: b59d7dc51b84fb1f465ff1d00f5207f3b2b4a494

The qualifier checks exact Git object identities for the source files that define:

- loopback Responses/health behavior;
- version/config identity;
- Codex Native2 and legacy connector behavior;
- ChatGPT Web model namespace;
- Codex route ownership;
- outer-turn authority and turn-scoped MCP capability;
- fail-closed behavior;
- upstream release-validation limitations.

## v4-only rule

No v5-only contract may be used to qualify v4.0.7.

In particular, the old v5-oriented collector projected fields such as automatic_connector, manual_connector and browser_interaction_mode. Those fields are not used as evidence in the v4 readjudication.

## Existing-evidence rule

The original local report is copied byte-for-byte into the qualification fixture and must retain:

sha256:b91f425a1b92ea0c4cf2d5f1179ecd413cc04b5ac6285034dfd975b446efc2ff

Its internal evidence digest must independently recompute to:

551d6c90c48c0761880d937257189b626d586772030558e34a516d4d80d6a68e

Readjudication is allowed only if:

1. exact v4 source contract PASS;
2. original blocker is exactly CGW_RELEASE_VERSION;
3. all v4-backed config/health/route invariants pass;
4. exact local binary fingerprints remain those already collected;
5. every zero-model/scientific firewall flag remains false.

## Provenance limitation

The local installed Codex Web GPT.exe hash is a fingerprint of the installed executable, not the published NSIS installer asset hash.

This qualification does not claim reproducible-build byte equivalence between installed executable and source/release asset. The binding is:

exact v4 source/tag contract + config/health self-identification + exact installed executable fingerprint

under the already-declared trusted-local-user boundary.

## Outcome vocabulary

- V4_SOURCE_CONTRACT_PASS
- Q0B_PASS_UNDER_CORRECTED_V4_TARGET
- qualification failure with an exact fail-closed mechanism

Even both PASS results do not authorize a model-bearing functional attempt. They authorize only formal closure of the zero-model workstream.
