from __future__ import annotations

from fastapi import FastAPI, HTTPException, Header, Query
from pydantic import BaseModel

from .runtime import GovernedWorkflowRuntime
from .errors import GWRException, AuthorityDenied, NotFound, ValidationError


class LoginBody(BaseModel):
    username: str
    password: str


class OIDCExchangeBody(BaseModel):
    id_token: str


class ApprovalBody(BaseModel):
    expected_hash: str


class TenantCreateBody(BaseModel):
    name: str


class WorkspaceCreateBody(BaseModel):
    name: str


class ProjectCreateBody(BaseModel):
    name: str
    project_id: str | None = None


class MembershipBody(BaseModel):
    actor_id: str
    role: str


def create_app(runtime: GovernedWorkflowRuntime) -> FastAPI:
    app = FastAPI(title="Governed Workflow Runtime", version="0.6.0")

    @app.exception_handler(GWRException)
    async def gwr_error(_, exc: GWRException):
        status = 400
        if isinstance(exc, AuthorityDenied):
            status = 403
        elif isinstance(exc, NotFound):
            status = 404
        elif isinstance(exc, ValidationError):
            status = 422
        return __import__('fastapi').responses.JSONResponse(
            status_code=status,
            content={"ok": False, "error": {"code": exc.code, "message": exc.message, "details": exc.details}},
        )

    def bearer(authorization: str | None):
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="bearer token required")
        token = authorization.split(" ", 1)[1].strip()
        return token, runtime.auth.verify(token)

    def project_principal(project_id: str, authorization: str | None, permission: str = "VIEW", *, hide_existence: bool = True):
        scope = runtime.tenancy.scope_for_project(project_id)
        if not scope:
            return None
        try:
            _, principal = bearer(authorization)
            runtime.tenancy.require_project_access(principal.actor_id, project_id, permission)
            return principal
        except (AuthorityDenied, HTTPException):
            if hide_existence:
                raise HTTPException(status_code=404, detail="project not found")
            raise

    @app.post('/auth/login')
    def login(body: LoginBody):
        token = runtime.auth.authenticate(body.username, body.password, client_metadata={"client": "fastapi"})
        principal = runtime.auth.verify(token)
        return {"access_token": token, "token_type": "bearer", "expires_at": principal.expires_at, "actor_id": principal.actor_id, "auth_method": principal.auth_method}

    @app.post('/auth/oidc/{provider_id}/exchange')
    def oidc_exchange(provider_id: str, body: OIDCExchangeBody):
        token = runtime.auth.authenticate_oidc(provider_id, body.id_token, client_metadata={"client": "fastapi"})
        principal = runtime.auth.verify(token)
        return {"access_token": token, "token_type": "bearer", "expires_at": principal.expires_at, "actor_id": principal.actor_id, "auth_method": principal.auth_method}

    @app.get('/auth/me')
    def me(authorization: str = Header(...)):
        _, principal = bearer(authorization)
        return {
            "actor_id": principal.actor_id,
            "principal_id": principal.principal_id,
            "auth_method": principal.auth_method,
            "memberships": runtime.tenancy.memberships_for_actor(principal.actor_id),
        }

    @app.post('/tenants')
    def create_tenant(body: TenantCreateBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        tenant_id = runtime.tenancy.create_tenant(body.name, principal.actor_id)
        return {"tenant_id": tenant_id, "name": body.name}

    @app.post('/tenants/{tenant_id}/workspaces')
    def create_workspace(tenant_id: str, body: WorkspaceCreateBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        workspace_id = runtime.tenancy.create_workspace(tenant_id, body.name, principal.actor_id)
        return {"workspace_id": workspace_id, "tenant_id": tenant_id, "name": body.name}

    @app.post('/workspaces/{workspace_id}/projects')
    def create_scoped_project(workspace_id: str, body: ProjectCreateBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        ws = runtime.db.one("SELECT tenant_id FROM workspaces WHERE workspace_id=? AND status='ACTIVE'", (workspace_id,))
        if not ws:
            raise HTTPException(status_code=404, detail="workspace not found")
        try:
            runtime.tenancy.require_workspace_access(principal.actor_id, workspace_id, "MANAGE_PROJECT")
        except AuthorityDenied:
            raise HTTPException(status_code=404, detail="workspace not found")
        project_id = runtime.create_scoped_project(body.name, ws["tenant_id"], workspace_id, principal.actor_id, project_id=body.project_id)
        return {"project_id": project_id, "workspace_id": workspace_id, "tenant_id": ws["tenant_id"], "name": body.name}

    @app.get('/projects')
    def list_projects(authorization: str = Header(...), tenant_id: str | None = Query(default=None)):
        _, principal = bearer(authorization)
        return {"projects": runtime.tenancy.list_accessible_projects(principal.actor_id, tenant_id=tenant_id)}

    @app.post('/tenants/{tenant_id}/members')
    def add_tenant_member(tenant_id: str, body: MembershipBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        runtime.tenancy.add_tenant_member(tenant_id, body.actor_id, body.role, principal.actor_id)
        return {"tenant_id": tenant_id, "actor_id": body.actor_id, "role": body.role.upper(), "status": "ACTIVE"}

    @app.post('/workspaces/{workspace_id}/members')
    def add_workspace_member(workspace_id: str, body: MembershipBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        runtime.tenancy.add_workspace_member(workspace_id, body.actor_id, body.role, principal.actor_id)
        return {"workspace_id": workspace_id, "actor_id": body.actor_id, "role": body.role.upper(), "status": "ACTIVE"}

    @app.post('/projects/{project_id}/members')
    def add_project_member(project_id: str, body: MembershipBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        runtime.tenancy.add_project_member(project_id, body.actor_id, body.role, principal.actor_id)
        return {"project_id": project_id, "actor_id": body.actor_id, "role": body.role.upper(), "status": "ACTIVE"}

    @app.delete('/projects/{project_id}/members/{actor_id}')
    def revoke_project_member(project_id: str, actor_id: str, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        runtime.tenancy.revoke_project_member(project_id, actor_id, principal.actor_id)
        return {"project_id": project_id, "actor_id": actor_id, "status": "REVOKED"}

    @app.get('/proposals/{proposal_id}')
    def proposal(proposal_id: str, authorization: str | None = Header(default=None)):
        row = runtime.db.one("SELECT proposal_id,project_id,action,resource_refs,frozen_payload,payload_hash,required_approval_policy,status,created_at FROM proposals WHERE proposal_id=?", (proposal_id,))
        if not row:
            raise HTTPException(status_code=404, detail="proposal not found")
        if runtime.tenancy.scope_for_project(row["project_id"]):
            try:
                project_principal(row["project_id"], authorization, "VIEW")
            except HTTPException:
                raise HTTPException(status_code=404, detail="proposal not found")
        return dict(row)

    @app.post('/proposals/{proposal_id}/approve')
    def approve(proposal_id: str, body: ApprovalBody, authorization: str = Header(...)):
        token, principal = bearer(authorization)
        row = runtime.db.one("SELECT project_id FROM proposals WHERE proposal_id=?", (proposal_id,))
        if not row:
            raise HTTPException(status_code=404, detail="proposal not found")
        if runtime.tenancy.scope_for_project(row["project_id"]):
            try:
                runtime.tenancy.require_project_access(principal.actor_id, row["project_id"], "APPROVE")
            except AuthorityDenied:
                raise HTTPException(status_code=404, detail="proposal not found")
        approval_id = runtime.governance.approve_proposal_authenticated(proposal_id, token, body.expected_hash)
        return {"approval_id": approval_id, "proposal_id": proposal_id, "status": "APPROVED"}

    @app.get('/health')
    def health():
        return {"ok": True, "domain": runtime.domain.domain_id, "version": "0.6.0"}

    @app.get('/projects/{project_id}/audit')
    def audit(project_id: str, authorization: str | None = Header(default=None)):
        project_principal(project_id, authorization, "VIEW")
        return runtime.governance.query_audit(project_id)

    @app.get('/projects/{project_id}/frontier')
    def frontier(project_id: str, authorization: str | None = Header(default=None)):
        project_principal(project_id, authorization, "VIEW")
        return runtime.knowledge.get_validity_frontier(project_id)

    @app.get('/checkpoints/{checkpoint_id}/resume')
    def resume(checkpoint_id: str, authorization: str | None = Header(default=None)):
        row = runtime.db.one("SELECT project_id FROM checkpoints WHERE checkpoint_id=?", (checkpoint_id,))
        if not row:
            raise HTTPException(status_code=404, detail="checkpoint not found")
        project_principal(row["project_id"], authorization, "USE")
        return runtime.execution.reconcile_checkpoint(checkpoint_id)

    @app.get('/research/orchestrations/{orchestration_id}')
    def research_status(orchestration_id: str, authorization: str | None = Header(default=None)):
        row = runtime.db.one("SELECT project_id FROM orchestrations WHERE orchestration_id=?", (orchestration_id,))
        if not row:
            raise HTTPException(status_code=404, detail="orchestration not found")
        project_principal(row["project_id"], authorization, "VIEW")
        from .research_orchestrator import ResearchOrchestrator
        return ResearchOrchestrator(runtime, {}, human_approver_id=None).get_status(orchestration_id)

    @app.get('/research/orchestrations/{orchestration_id}/report')
    def research_report(orchestration_id: str, authorization: str | None = Header(default=None)):
        row = runtime.db.one("SELECT project_id FROM orchestrations WHERE orchestration_id=?", (orchestration_id,))
        if not row:
            raise HTTPException(status_code=404, detail="orchestration not found")
        project_principal(row["project_id"], authorization, "VIEW")
        from .research_orchestrator import ResearchOrchestrator
        return {"markdown": ResearchOrchestrator(runtime, {}, human_approver_id=None).render_report(orchestration_id)}

    return app
