# P5A-CGW Q0b Runtime Alignment Qualification Result

## Status

**QUALIFIED / ONE LOCAL RUNTIME ALIGNMENT + ONE FRESH Q0b COLLECTION AUTHORIZED / NO MODEL EXECUTION**

Authoritative candidate:

`1239140ccec6e91865eea3afb82398fb33008ecd`

Qualification:

- run `35802645056` — PASS
- Linux job `106996238511` — PASS
- Windows job `106996239193` — PASS

Qualified component identities:

- alignment wrapper: `cbbd99ed902ea7ff62fca4e3c9695c133c00b98c`
- static tests: `54a7f70aa27d6184718d50b21225626ae1f0df3d`
- workflow: `5f3dba290f7f08669410ec173d5a86122b399699`
- plan: `1c2951c9e4286403a02174ad1c94a96ecb98cc10`

## Qualified repair

The only permitted local environment mutation is:

`CGW 4.0.7 -> CGW 5.0.8`

The frozen P5A-CGW specification remains at 5.0.8. Retargeting it to the observed 4.0.7 runtime is prohibited.

Pinned trust chain:

- upstream source: `miuuyy/codex-chatgpt-web@eaf4f09ae92d4dc4429fa597b0861663138f08f8`
- installer script SHA-256:
  `117ab8e5bfba36d3f611e9294355afe70936a536bf3305d4fe563edab7c40a71`
- Windows x64 installer asset SHA-256:
  `83224d59506462ab2976f437bfaea96b046d4ed55caa7e1cfd6a3d61de0a8ff3`

The wrapper never resolves `latest`.

## Qualification evidence

Linux verified:

- PowerShell parser;
- 8 bounded static alignment tests;
- exact v5.0.8 GitHub release metadata/digests;
- full regression of the existing P5A-CGW zero-model qualifier suite.

Windows verified:

- Windows PowerShell parser;
- the same alignment static tests;
- no model-bearing endpoint invocation;
- no `turn/start` path.

The first workflow run `35802584279` is non-authoritative. It failed only because the workflow installed `pytest` before repository dependencies, causing `tests/conftest.py` to fail importing `yaml`. The wrapper itself had already parsed successfully. The repair changed workflow dependency order only.

## Local authorization

Exactly one invocation of:

`scripts/g2e/p5a_cgw_q0b_align_runtime_5_0_8.ps1`

is authorized.

It requires the Codex Web GPT launcher process to be quit before mutation.

If alignment reaches healthy 5.0.8 while preserving route/mode/connector/approval invariants, the wrapper invokes exactly one fresh Q0b collector under:

`g2e/.local/P5A-CGW-ZERO-MODEL-Q0B-R2`

Still forbidden throughout:

- `/v1/models`
- `/v1/responses`
- Codex model turn
- ChatGPT browser submission
- MCP tool invocation
- scientific attempt
- P5A official fallback
- A/B comparison

Even if fresh Q0b returns `LOCAL_ZERO_MODEL_ADMISSION_PASS`, no functional attempt is automatically authorized. The fresh reports must be admitted and the zero-model workstream formally closed first.
