# v0.6 Handoff

## Implemented

- Tenant -> Workspace -> Project hierarchy.
- Tenant/workspace/project memberships with separate role matrices.
- Scoped project access enforcement integrated into GovernanceKernel.
- Scoped project creation while preserving legacy unscoped projects.
- OIDC provider-verifier registration, external identity binding and OIDC session exchange.
- Dynamic membership checks on every scoped request.
- Cross-tenant resource concealment in FastAPI endpoints.
- Security event trail for tenancy administration.
- Migration `0002_v06_identity_multitenancy` on SQLite/PostgreSQL.
- Dedicated v0.6 test and QA gates.

## Deliberately deferred

- Production JWKS/OIDC discovery/network adapter: deployment-specific verifier remains injected.
- SCIM/user provisioning.
- Enterprise SSO administration UI.
- Tenant billing/quota.
- PostgreSQL row-level security. v0.6 enforces isolation in the runtime/service boundary; RLS can be defense-in-depth later.
- Distributed execution/worker leases: v0.7.

## Next milestone

Only after `V06_GATE.json` is PASS should development move to v0.7 Distributed Runtime.
