# G2E P3 Preflight — Package Integrity Completion Finding

## Status

**BLOCKING SEMANTIC FINDING — resolve before P3 Result Package implementation.**

## Baseline

- P1.2 qualified schema: `fe02721b436e94fc7cd34a68f136d6088ca4b411`
- P1.2 evidence closure: `9165a3afd75b7386370e9eb7642ee0579a3d1a5b`

## P3-F04 — HIGH — OPEN — Package external-reference policy lacks exact external-reference inventory

Core Semantics §14 requires verification failure when an immutable external reference cannot be resolved under a policy that requires online resolution.

P1.2 PackageManifest records `external_reference_policy` but no exact list of external references. A P3 verifier would otherwise need an ungoverned convention outside the canonical manifest.

### Required remediation

Add canonical PackageExternalReference entries to PackageManifest with:

- stable ref ID;
- immutable locator;
- optional expected SHA-256;
- whether online resolution is required;
- deterministic uniqueness validation.

The P3 verifier must consume this inventory and fail closed under REQUIRE_RESOLUTION.

- [x] RESOLVED

## Verdict

`OPEN = 0`

**PASS — external-reference integrity inventory is schema-bound; P3 Result Package implementation may open.**
