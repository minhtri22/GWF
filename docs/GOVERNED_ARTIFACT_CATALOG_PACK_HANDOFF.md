# GWF Governed Artifact Catalog — Packing / Implementation Handoff

## 1. Package purpose

This is a **packing-only handoff** for a future GWF implementation agent.

It intentionally contains specification, integration boundaries, QA and implementation sequencing only.

## 2. Source baseline

- Repository: `minhtri22/GWF`
- Package branch: `docs/governed-artifact-catalog-pack`
- Base branch: `docs/reference-agent-interop-specs`
- Base commit: `f9a638310e095f760b3755583d230d2e65f50f45`

Separate Documentation Governance P0 implementation branches were inspected for frontier/ownership. No code was copied and this package does not depend on their transient implementation SHAs.

## 3. Package files

- `GOVERNED_ARTIFACT_CATALOG_SPEC.md`
- `GOVERNED_ARTIFACT_CATALOG_INTEGRATION_BOUNDARIES.md`
- `GOVERNED_ARTIFACT_CATALOG_PACK_HANDOFF.md`
- `GOVERNED_ARTIFACT_CATALOG_QA.md`

## 4. Frozen architectural decisions

1. GAC is catalog/index/publication, not a new KnowledgeKernel.
2. GAC binds exact Artifact Revision/ObjectRef/external immutable identities.
3. Existing GWF authority/audit/tenancy are reused.
4. Documentation Governance owns document registry/QA/validity semantics.
5. Reference Acquisition owns external retrieval provenance.
6. Search results are candidate discovery only.
7. G2E owns applicability/reuse/synthesis semantics.
8. Cross-tenant/global sharing is deferred.
9. Search backend is adapterized; no vector/FTS dependency in core.
10. Publication is idempotent by exact subject/scope/policy identity.
11. Search indexes are derived/rebuildable, never system of record.
12. Catalog visibility cannot broaden source permission.
13. Domain metadata is namespaced; GWF does not reinterpret it.
14. This pack authorizes no code.

## 5. Reconciliation required before implementation

Future implementation agent MUST re-read the then-current:

- Documentation Integrity & Governance implementation;
- KnowledgeKernel;
- DB/migrations;
- ObjectRef service;
- tenancy/project governance;
- Reference Acquisition implementation status;
- G2E Evidence Library Adapter contract when available;
- any new catalog/search/index primitives added by intervening GWF releases.

If those differ materially from this pack, create compatibility findings and update the implementation plan before code.

## 6. Recommended implementation entry

Do not start with vector search.

~~~text
exact CatalogEntry contract
        ↓
publish/withdraw exact GWF revisions
        ↓
tenant/workspace/project access
        ↓
deterministic metadata query
        ↓
audit
        ↓
cross-project fixture
~~~

Only after this passes should object/external refs and optional search adapters open.

## 7. Handoff acceptance

Package is ready for implementation only when `GOVERNED_ARTIFACT_CATALOG_QA.md` reports:

- no ownership conflict;
- no implementation/code mutation;
- no duplicate document registry;
- no G2E research semantics in GWF;
- dependency/reference links valid;
- implementation order dependency-safe;
- all findings resolved.

## 8. Explicit stop

After documentation QA PASS:

~~~text
PACK COMPLETE
     ↓
STOP
~~~

Do not implement GAC on this branch.

## 9. References

- [GAC Specification](GOVERNED_ARTIFACT_CATALOG_SPEC.md)
- [Integration Boundaries](GOVERNED_ARTIFACT_CATALOG_INTEGRATION_BOUNDARIES.md)
- [GAC QA](GOVERNED_ARTIFACT_CATALOG_QA.md)
