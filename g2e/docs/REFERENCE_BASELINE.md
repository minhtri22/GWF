# G2E Reference Baseline

This document pins the primary reference revisions used by the G2E v0.x specification. References are evidence/inputs to the design; they do not override G2E normative semantics.

## GWF baseline

G2E branch origin:

- Repository: `minhtri22/GWF`
- Source branch: `docs/reference-agent-interop-specs`
- Base commit: `f9a638310e095f760b3755583d230d2e65f50f45`

Primary dependency documents at that baseline:

- [GWF README](../../README.md)
- [Agent Interoperability Foundation](../../docs/V0.8.7_AGENT_INTEROPERABILITY_FOUNDATION.md)
- [Reference Acquisition Specification](../../docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md)
- [Documentation Integrity & Governance](../../docs/DOCUMENTATION_INTEGRITY_GOVERNANCE_SPEC.md)
- [7-Wave Implementation Plan](../../docs/IMPLEMENTATION_7_WAVES_PLAN.md)
- [Finding Checklist](../../docs/Finding_checklist.md)
- [Research Domain](../../domains/research.workflow.yaml)
- [Software Domain](../../domains/software.workflow.yaml)
- [DomainSDK](../../src/gwr/domain_sdk.py)
- [Runtime](../../src/gwr/runtime.py)

If G2E later adopts semantics from a newer GWF revision, this file must append or supersede the dependency baseline explicitly; path names alone are not sufficient identity.

## MindForge empirical-method baseline

- Repository: `minhtri22/MindForge`
- Evidence commit: `62141d530832f7694342fe92704a5975bfdbbded`

References:

- [Model-pipeline evidence root](https://github.com/minhtri22/MindForge/tree/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline)
- [M2 trainer/checkpoint result](https://github.com/minhtri22/MindForge/blob/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline/m2/IMPLEMENTATION_RESULT.md)
- [M3 governance result](https://github.com/minhtri22/MindForge/blob/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline/m3/IMPLEMENTATION_RESULT.md)
- [M4 reasoning result](https://github.com/minhtri22/MindForge/blob/62141d530832f7694342fe92704a5975bfdbbded/artifacts/model-training-pipeline/m4/IMPLEMENTATION_RESULT.md)

MindForge phase names are not G2E phases. They are empirical source material for generic proof-governance rules.


## GWF Governed Artifact Catalog packing baseline

G2E Evidence Library Adapter is designed against the documentation-only GWF Governed Artifact Catalog pack:

- Branch: `docs/governed-artifact-catalog-pack`
- Candidate: `4cc187320820ea4ff144130b0b63f6d23e3a9e3b`
- Findings: `94f1db6d7ecf001311d774b729c7a579d65853ab`
- Remediation: `e013a10707815c99bc65fe93bc5716fc1b55e20e`
- QA closure: `194c66c3c215ddcc46a6e26dca32e3fb6eda04c5`

References:

- [GAC Specification](https://github.com/minhtri22/GWF/blob/docs/governed-artifact-catalog-pack/docs/GOVERNED_ARTIFACT_CATALOG_SPEC.md)
- [GAC Integration Boundaries](https://github.com/minhtri22/GWF/blob/docs/governed-artifact-catalog-pack/docs/GOVERNED_ARTIFACT_CATALOG_INTEGRATION_BOUNDARIES.md)
- [GAC Packing QA](https://github.com/minhtri22/GWF/blob/docs/governed-artifact-catalog-pack/docs/GOVERNED_ARTIFACT_CATALOG_QA.md)

This is a **packing-only contract**, not an implemented GWF service. G2E must not assume GAC runtime availability until separately qualified.
