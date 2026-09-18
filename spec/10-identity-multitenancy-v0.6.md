# GWR v0.6 — Identity & Multi-tenancy Contract

## Goal

Add a production-facing identity and tenant isolation boundary without changing the research semantics proven in v0.5.1.

Hierarchy:

`Tenant -> Workspace -> Project -> Research Run`

The existing kernels keep `project_id` as their storage partition key. v0.6 introduces an authoritative ownership/membership graph that must be checked before any scoped public access to a project.

## Identity

Two human authentication paths are supported:

1. local password authentication for controlled deployments;
2. OIDC exchange through an injected cryptographic verifier.

OIDC claims are never allowed to select a runtime `actor_id`. The only trusted mapping is persisted as `(provider_id, issuer, subject) -> actor_id`. Provider verifiers are deployment dependencies and must validate signature, issuer, audience and provider-specific requirements before returning claims.

Runtime sessions remain signed, revocable and short-lived. Membership is checked at request time, so revoking project membership invalidates access immediately without waiting for session expiry.

## Tenancy model

Tables added by migration `0002_v06_identity_multitenancy`:

- `tenants`
- `workspaces`
- `project_scopes`
- `tenant_memberships`
- `workspace_memberships`
- `project_memberships`
- `external_identities`
- `security_events`

A tenant-scoped project never trusts legacy `actors.project_scope` by itself. Tenant/workspace/project membership is authoritative. Legacy project scope remains supported only for unscoped v0.5 projects.

## Roles

Tenant roles: `OWNER`, `ADMIN`, `MEMBER`, `VIEWER`.

Workspace roles: `OWNER`, `ADMIN`, `MEMBER`, `VIEWER`.

Project roles: `OWNER`, `RESEARCH_LEAD`, `RESEARCHER`, `REVIEWER`, `APPROVER`, `VIEWER`.

Tenancy authorization and domain governance are separate gates. A caller must pass tenancy scope first, then the existing domain authority policy.

## API isolation

Scoped project endpoints require an authenticated bearer session. Cross-tenant project/proposal access returns 404 to avoid confirming resource existence. Project listings are filtered by authoritative memberships.

## Required QA gates

- v0.5.1 PostgreSQL/research/restart/semantic-equivalence regression remains PASS.
- v0.6 identity/multi-tenancy tests pass on SQLite and PostgreSQL.
- tenant A cannot access or infer tenant B projects;
- manually injecting a project id into legacy `project_scope` cannot bypass tenant membership;
- OIDC actor impersonation through token claims is rejected by subject mapping;
- revoked session is denied;
- revoked project membership takes effect immediately for an otherwise-valid session;
- SQLite and PostgreSQL both apply migration `0002` with no pending migration.
