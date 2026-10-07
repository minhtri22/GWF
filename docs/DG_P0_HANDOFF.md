# GWF — DG-P0 Handoff: External Validator Foundation + markdownlint

## 1. Item identity

- Wave: **1 — Documentation Validator Foundation**
- Item: **DG-P0 — External Validator Foundation + markdownlint**
- Branch: `v0.8.6-dg-p0-document-validator`
- Planning baseline: `f9a638310e095f760b3755583d230d2e65f50f45`
- Initial implementation commit: `39b282801d80bb07cb4c3786e9d277785c593434`
- Repair/final implementation commit: `cc2b15adb8d5ad0a5ee855e77ae93b6043bbe826`
- Final implementation parent: `39b282801d80bb07cb4c3786e9d277785c593434`

DG-P0 is complete at `cc2b15ad...`. This handoff does not authorize DG-P1.

## 2. Governing-document identities

- `docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md` — Git blob `fb8c4eda276d8d13eb4f76b1947ad1632bf49ab5`
- `docs/IMPLEMENTATION_7_WAVES_PLAN.md` — Git blob `316003f15205ec5b3b5b23ffc6c4895f49474866`
- `docs/DOCUMENT_QA_7_WAVES_PLAN.md` — Git blob `d19ed0a480856796cccdde427b514ac49a1bdbd7`

HARD dependencies:

- **PLAN-QA:** PASS at `f9a638310e095f760b3755583d230d2e65f50f45`.
- **DIG-SPEC:** exact reviewed blob `fb8c4eda276d8d13eb4f76b1947ad1632bf49ab5`.

## 3. External dependency evidence

- Validator: `markdownlint-cli2`
- Exact version: `0.23.3`
- Node requirement: `>=22`
- Revalidated: `2026-09-21`
- Toolchain Git blob: `5e41a2fc7dbcc691101f6b50ac3982ebd11574d2`
- Config Git blob: `af424f28bd6c29f8dbef6ead45adcf72e471acc3`
- Config SHA-256: `cf8eae4e746b5da0976b7ca10462e9a471f3f551eb92e6bc868f0ad39ad45764`

CI installs exact `markdownlint-cli2@0.23.3`; floating `latest` does not qualify P0.

## 4. Implementation contents

- `src/gwr/document_validation.py` — Git blob `a251469619d59e8cdddfd61175e665117ba2afbf`
- `tests/test_document_validation_p0.py` — Git blob `dad78a7217a09c87c8a02ff143a63bd2b187c895`
- `tools/run_dg_p0_gate.py` — Git blob `1db388f21b4be18596a583e602547d804d69c52e`

P0 implements:

- provider-neutral `ValidatorAdapter`;
- normalized `ValidatorExecution` and `ValidatorFinding`;
- `MarkdownlintCli2Adapter`;
- exact subject/config SHA-256;
- validator-version verification;
- separate execution status `SUCCEEDED | TOOL_ERROR | UNAVAILABLE`;
- separate content status `PASS | FINDINGS | NOT_EVALUATED`;
- fail-closed parser behavior;
- source-mutation detection;
- source-context redaction.

Real fixture identities:

- valid subject SHA-256: `68b91e06f2860b3a0076e73dc515d13e2ce6e8e0bd0ed6d8f790ef3a9bef1b7a`
- invalid subject SHA-256: `47901f157bd510ee4b4c37f591a08721f4078221dc5226c8bc891bd212a20dd9`

## 5. Changed files

- `.github/workflows/dg-p0-document-validator.yml`
- `src/gwr/document_validation.py`
- `tests/test_document_validation_p0.py`
- `tests/fixtures/document_validation/valid.md`
- `tests/fixtures/document_validation/invalid.md`
- `tools/document_validation/.markdownlint-cli2.jsonc`
- `tools/document_validation/toolchain.json`
- `tools/run_dg_p0_gate.py`

## 6. Schema / migration / normative impact

- **Database schema changes:** NONE
- **Database migrations:** NONE
- **Document registry:** NONE
- **Dependency graph runtime:** NONE
- **Research workflow changes:** NONE
- **GitHub Ruleset/CODEOWNERS mutations:** NONE
- **Existing GWF governance semantics changed:** NONE

DG-P0 adds only the bounded validator surface.

## 7. QA lineage

### Failed real-tool run retained

- Run: `35560396897`
- Head: `39b282801d80bb07cb4c3786e9d277785c593434`
- Result: **FAIL**
- Unit tests: PASS
- Real smoke: FAIL with `VERSION_PROBE_FAILED`
- Root cause: pinned `markdownlint-cli2 --help` intentionally returns exit code `2` after printing the valid banner; the first adapter incorrectly required `0`.
- Artifact ID: `10622126199`
- Artifact digest: `sha256:52c7184903040c54557ffc0d85c73336a67700e799f1165f9e1ca917c055973d`

No fixture, threshold, or tool version was changed to obtain a PASS. The executable contract was corrected and regression-tested.

### Repair run PASS

- Run: `35560545865`
- Head: `cc2b15adb8d5ad0a5ee855e77ae93b6043bbe826`
- Result: **PASS**
- P0 unit tests: **10/10 PASS**
- Real pinned markdownlint smoke: **PASS**
- Gate assertion: **PASS**
- Bounded v0.8.4/v0.8.5 regression: **24/24 PASS**
- Compile: **PASS**
- Artifact ID: `10621868111`
- Artifact digest: `sha256:d4a5c6a846e8bb248a9c7be88f7dc7b92837adbf5a20737bcf0f94cbfdbabb88`

## 8. Security / privacy impact

- No raw reusable credential is introduced.
- Raw validator stdout/stderr is not persisted in normalized execution evidence.
- Default markdownlint `[Context: "..."]` source excerpts are stripped before normalized findings are retained.
- A regression test verifies that `SECRET_TOKEN=abc` is absent from the persisted finding message.
- Source content is represented by exact hashes, not copied into normalized evidence.

## 9. Implementation findings

### F-43 — CLI help-exit contract mismatch

The first version probe assumed exit 0. The real pinned CLI returns 2 for `--help` after printing the valid version banner.

Resolution: only `{0,2}` are accepted for the help probe and only when the exact banner parses; every other outcome fails closed.

### F-44 — formatter source-context exposure

The default formatter can emit `[Context: "..."]` containing raw source text.

Resolution: strip Context before normalized persistence and regression-test secret-like content redaction.

## 10. Known limitations

- Built-in markdownlint rule IDs `MD###/alias` are qualified; custom non-`MD###` rule IDs are outside P0.
- Real executable smoke is Linux CI; Windows path parsing is currently a unit fixture.
- No persistent `DocumentQARecord` / `DocumentFinding` exists yet.
- No Vale/Lychee adapter exists yet.
- No document authority, relation, validity, impact, or stale-propagation runtime exists yet.

## 11. Rollback / recovery

There is no DB migration or persisted runtime state. Rollback is code-only:

1. revert `cc2b15adb8d5ad0a5ee855e77ae93b6043bbe826`;
2. revert `39b282801d80bb07cb4c3786e9d277785c593434`; or
3. restore baseline `f9a638310e095f760b3755583d230d2e65f50f45`.

Negative CI evidence remains historical evidence and must not be deleted.

## 12. Explicit non-scope

DG-P0 did not implement document registry/migration, typed relations, lifecycle/validity persistence, stale propagation, no-silent-cascade runtime, Vale/Lychee, GitHub repository enforcement, research-lock integration, Reference Acquisition, MCP/harness/ARC, or node-level agent orchestration.

## 13. Current frontier

```text
DG-P0
  PASS
   ↓
STOP
```

**DG-P1 is not automatically authorized.**
