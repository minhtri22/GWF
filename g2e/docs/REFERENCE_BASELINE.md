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


## GWF Shared Library / GAC reconciliation baseline

The original GAC packing baseline above remains design lineage. The **current G2E↔GWF integration authority** is the reconciled documentation state:

- GWF reconciliation commit: `be7d606c64a97d9525d1f72d744fe5b7a336ff0c`
- reconciliation finding commit: `4ccdecaea6bf3520d2c58552ae1fc4bea548db22`
- DG-P0 implementation/handoff evidence consulted by GWF: `ef322ff0618b83fbfaef40b096cb43f5193d8db0`
- DG-P0 exact-head workflow: `35560831581` — PASS
- GWF reconciliation QA: `PASS / OPEN=0`

Exact reconciled Git blobs recorded by GWF QA:

- GAC Specification: `831a4f9260ff6a1f74d531d9d24a91cdb6feff7e`
- GAC Integration Boundaries: `2fef77627127bf58c6376202f96de681d5b3050a`
- Documentation Governance Specification: `e50d0f17433c6f0ec57f987278a0d24a7bbd4610`
- Reference Acquisition Specification: `110dae0b492b56492c52eec2dfc64a8d2070d966`
- revised 7-Wave Plan: `229decfb067ead7ef38d51012b06abf69cc12fc0`
- GWF reconciliation Findings: `e314098f3a10c2bc15fffe8f3323e8832a91419a`
- reconciled GAC Handoff: `cb5f0c1ef33122a6e997dcaeb29ac588b1f045c9`
- reconciled GAC QA: `624bc36f9012af92711f80b2ee1d6157b358f570`
- cross-document GAC/G2E/7-wave reconciliation QA: `fe5e076c34f7665bb0d6cd354ae779b83e18a29a`

Pinned references:

- [Reconciled GAC Specification](https://github.com/minhtri22/GWF/blob/be7d606c64a97d9525d1f72d744fe5b7a336ff0c/docs/GOVERNED_ARTIFACT_CATALOG_SPEC.md)
- [Reconciled GAC Integration Boundaries](https://github.com/minhtri22/GWF/blob/be7d606c64a97d9525d1f72d744fe5b7a336ff0c/docs/GOVERNED_ARTIFACT_CATALOG_INTEGRATION_BOUNDARIES.md)
- [Reconciled Reference Acquisition](https://github.com/minhtri22/GWF/blob/be7d606c64a97d9525d1f72d744fe5b7a336ff0c/docs/V0.8.6_REFERENCE_ACQUISITION_SPEC.md)
- [Revised 7-Wave Plan](https://github.com/minhtri22/GWF/blob/be7d606c64a97d9525d1f72d744fe5b7a336ff0c/docs/IMPLEMENTATION_7_WAVES_PLAN.md)
- [Reconciliation QA](https://github.com/minhtri22/GWF/blob/be7d606c64a97d9525d1f72d744fe5b7a336ff0c/docs/DOCUMENT_QA_GAC_7_WAVES_RECONCILIATION.md)

Current integration facts:

1. Shared Library is a consumer-facing capability built on GAC, not another canonical store.
2. GAC owns publication/catalog/query/cross-project discovery; G2E owns applicability/reuse/synthesis semantics.
3. Reference Acquisition may query GAC as an internal research discovery channel and preserves exact CatalogQueryExecution/snapshot/CatalogEntry provenance.
4. GAC runtime remains unimplemented at this documentation frontier. Earliest GAC-P0/P1 hard gate is DG-W4 PASS.
5. GAC-P3 optional search is not required for minimum Shared Library readiness.
6. GAC-P4B is the G2E-specific consumer qualification fixture and is non-blocking for GAC core.
