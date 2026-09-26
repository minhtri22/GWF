from __future__ import annotations

from fastapi import FastAPI, HTTPException, Header, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel

from .runtime import GovernedWorkflowRuntime
from .errors import GWRException, AuthorityDenied, NotFound, ValidationError
from .domain_sdk import DomainSDK
from .utils import parse_json
from .product import ProjectDashboardService
import asyncio
import json
import os
import tempfile
import yaml
from pathlib import Path


class LoginBody(BaseModel):
    username: str
    password: str


class OIDCExchangeBody(BaseModel):
    id_token: str


class ApprovalBody(BaseModel):
    expected_hash: str


class RejectBody(BaseModel):
    expected_hash: str
    reason: str = "REJECTED"


class DomainValidationBody(BaseModel):
    yaml_text: str


class DomainPackageCreateBody(BaseModel):
    domain_id: str
    name: str
    description: str = ""


class DomainRevisionBody(BaseModel):
    yaml_text: str


class TenantCreateBody(BaseModel):
    name: str


class WorkspaceCreateBody(BaseModel):
    name: str


class ProjectCreateBody(BaseModel):
    name: str
    project_id: str | None = None
    domain_revision_id: str | None = None


class BrowserProjectCreateBody(BaseModel):
    workspace_id: str
    name: str
    domain_revision_id: str | None = None


class MembershipBody(BaseModel):
    actor_id: str
    role: str


class ProjectRenameBody(BaseModel):
    name: str


class ProjectArchiveBody(BaseModel):
    drain: bool = False
    reason: str = ""


class SkillPackageBody(BaseModel):
    skill_id: str
    name: str
    description: str = ""


class SkillRevisionBody(BaseModel):
    version: str
    markdown: str
    tool_requirements: list[str] = []
    qa_contract: dict = {}


class ProtocolCreateBody(BaseModel):
    skill_revision_id: str
    recovery_mode: str | None = None
    retry_budget: int | None = None


class ProjectAgentProtocolSettingsBody(BaseModel):
    recovery_mode: str | None = None
    retry_budget: int | None = None


class PreflightBody(BaseModel):
    checks: list[dict]


class PlanBody(BaseModel):
    objective: str
    steps: list[dict]
    reason: str = "INITIAL_PLAN"


class StepUpdateBody(BaseModel):
    status: str
    note: str = ""


class ProblemBody(BaseModel):
    code: str
    summary: str
    detail: str
    affected_step: int | None = None
    severity: str = "MEDIUM"


class RecoveryProposalBody(BaseModel):
    action: str
    target_step: int | None = None
    rationale: str = ""
    plan_patch: list[dict] = []
    risk_class: str = "LOW"
    normative_change: bool = False


class RecoveryDecisionBody(BaseModel):
    decision: str
    reason: str = ""


class VerifyBody(BaseModel):
    qa_result: str
    detail: str = ""


class HandoffBody(BaseModel):
    handoff: dict


class PluginConnectionBody(BaseModel):
    plugin_type: str
    external_connection_ref: str
    capabilities: list[str]
    metadata: dict = {}


class GitHubRepositoryBindingBody(BaseModel):
    connection_id: str
    repository_full_name: str
    default_branch: str = "main"
    write_policy: str = "FEATURE_BRANCH_ONLY"
    allowed_branches: list[str] = ["feature/*", "fix/*", "docs/*"]


class GitHubChangeSetBody(BaseModel):
    binding_id: str
    branch: str
    expected_head_sha: str
    changes: list[dict]
    commit_message: str


class GitHubExecuteBody(BaseModel):
    changes: list[dict]


def create_app(
    runtime: GovernedWorkflowRuntime,
    *,
    product_info: dict | None = None,
    web_root: str | Path | None = None,
    browser_cookie_secure: bool = False,
) -> FastAPI:
    app = FastAPI(title="Governed Workflow Runtime", version="0.8.5")
    resolved_product_info = {
        "product": "Governed Workflow Runtime",
        "version": "0.8.5",
        "build_sha": "unknown",
        "domain_id": runtime.domain.domain_id,
        "backend": getattr(runtime.db, "backend_name", "unknown"),
        "server_mode": "embedded",
    }
    resolved_product_info.update(product_info or {})
    browser_cookie_name = "gwr_browser_session"
    browser_capabilities = [
        {"id": "home", "label": "Home", "state": "LIVE_MODULE", "slice": "BPS-M01", "route": "/app/home"},
        {"id": "projects", "label": "Projects", "state": "LIVE_MODULE", "slice": "BPS-M02", "route": "/app/projects"},
        {"id": "operations", "label": "Operations", "state": "SKELETON_LOCKED", "slice": "BPS-M03", "route": "/app/operations"},
        {"id": "packages", "label": "Packages", "state": "SKELETON_LOCKED", "slice": "BPS-M06", "route": "/app/research/packages"},
        {"id": "github", "label": "GitHub", "state": "SKELETON_LOCKED", "slice": "BPS-M07", "route": "/app/system/github"},
        {"id": "access", "label": "Access", "state": "LIVE_MODULE", "slice": "BPS-M02", "route": "/app/system/access"},
        {"id": "shared-library", "label": "Shared Library", "state": "PLANNED_BLOCKED", "slice": "BPS-GAC", "route": "/app/shared-library"},
        {"id": "reference-acquisition", "label": "Reference Acquisition", "state": "PLANNED_BLOCKED", "slice": "BPS-RA", "route": "/app/research/reference-acquisition"},
        {"id": "agents", "label": "Agents / Codex", "state": "PLANNED_BLOCKED", "slice": "BPS-CODEX", "route": "/app/agents"},
        {"id": "diagnostics", "label": "Diagnostics", "state": "LIVE_FOUNDATION", "slice": "BPS-I00", "route": "/app/system/diagnostics"},
        {"id": "settings", "label": "Settings", "state": "SKELETON_LOCKED", "slice": "BPS-M07", "route": "/app/system/settings"},
    ]

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

    def browser_principal(request: Request):
        token = request.cookies.get(browser_cookie_name)
        if not token:
            raise HTTPException(status_code=401, detail="browser session required")
        try:
            return token, runtime.auth.verify(token)
        except AuthorityDenied as exc:
            raise HTTPException(status_code=401, detail="browser session invalid or expired") from exc

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

    @app.post('/browser/auth/login')
    def browser_login(body: LoginBody, response: Response):
        try:
            token = runtime.auth.authenticate(body.username, body.password, client_metadata={"client": "browser"})
            principal = runtime.auth.verify(token)
        except AuthorityDenied as exc:
            raise HTTPException(status_code=401, detail="invalid credentials") from exc
        response.set_cookie(
            key=browser_cookie_name,
            value=token,
            max_age=runtime.auth.session_ttl_seconds,
            httponly=True,
            secure=browser_cookie_secure,
            samesite="strict",
            path="/",
        )
        return {
            "ok": True,
            "actor_id": principal.actor_id,
            "principal_id": principal.principal_id,
            "auth_method": principal.auth_method,
            "expires_at": principal.expires_at,
        }

    @app.get('/browser/auth/me')
    def browser_me(request: Request):
        _, principal = browser_principal(request)
        return {
            "actor_id": principal.actor_id,
            "principal_id": principal.principal_id,
            "auth_method": principal.auth_method,
            "expires_at": principal.expires_at,
            "memberships": runtime.tenancy.memberships_for_actor(principal.actor_id),
        }

    @app.post('/browser/auth/logout')
    def browser_logout(request: Request, response: Response):
        token, _ = browser_principal(request)
        runtime.auth.revoke(token)
        response.delete_cookie(browser_cookie_name, path="/")
        return {"ok": True}

    @app.get('/browser/bootstrap')
    def browser_bootstrap(request: Request):
        authenticated = False
        try:
            browser_principal(request)
            authenticated = True
        except HTTPException:
            authenticated = False
        return {
            "product": resolved_product_info,
            "capabilities": browser_capabilities,
            "authenticated": authenticated,
            "shell_authority": "BPS-I00",
        }

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
        project_id = runtime.create_scoped_project(body.name, ws["tenant_id"], workspace_id, principal.actor_id, project_id=body.project_id, domain_revision_id=body.domain_revision_id)
        return {"project_id": project_id, "workspace_id": workspace_id, "tenant_id": ws["tenant_id"], "name": body.name, "domain_binding": runtime.domains.project_binding(project_id)}

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

    product = ProjectDashboardService(runtime)

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

    @app.post('/proposals/{proposal_id}/reject')
    def reject(proposal_id: str, body: RejectBody, authorization: str = Header(...)):
        token, principal = bearer(authorization)
        row = runtime.db.one("SELECT project_id FROM proposals WHERE proposal_id=?", (proposal_id,))
        if not row:
            raise HTTPException(status_code=404, detail="proposal not found")
        if runtime.tenancy.scope_for_project(row["project_id"]):
            try:
                runtime.tenancy.require_project_access(principal.actor_id, row["project_id"], "APPROVE")
            except AuthorityDenied:
                raise HTTPException(status_code=404, detail="proposal not found")
        approval_id = runtime.governance.reject_proposal_authenticated(proposal_id, token, body.expected_hash, body.reason)
        return {"approval_id": approval_id, "proposal_id": proposal_id, "status": "REJECTED", "reason": body.reason}

    @app.get('/health')
    def health():
        return {
            "ok": True,
            "domain": runtime.domain.domain_id,
            "version": resolved_product_info["version"],
            "build_sha": resolved_product_info["build_sha"],
            "backend": getattr(runtime.db, "backend_name", "unknown"),
        }

    @app.get('/ready')
    def ready():
        checks: dict[str, str] = {}
        try:
            runtime.db.one("SELECT 1")
            checks["database"] = "PASS"
            migrations = runtime.db.migrations.status() if getattr(runtime.db, "migrations", None) else {"pending": []}
            pending = list(migrations.get("pending") or [])
            checks["migrations"] = "PASS" if not pending else "FAIL"
            if pending:
                return JSONResponse(
                    status_code=503,
                    content={
                        "ok": False,
                        "core_health": "DEGRADED",
                        "reason": "pending_migrations",
                        "checks": checks,
                        "pending_migrations": pending,
                    },
                )
        except Exception:
            checks["database"] = "FAIL"
            return JSONResponse(
                status_code=503,
                content={"ok": False, "core_health": "UNHEALTHY", "reason": "database_probe_failed", "checks": checks},
            )

        if runtime.object_store is None:
            checks["object_store"] = "FAIL"
            return JSONResponse(
                status_code=503,
                content={"ok": False, "core_health": "DEGRADED", "reason": "object_store_not_configured", "checks": checks},
            )
        try:
            probe = runtime.object_store.put_bytes(
                b"GWF_BPS_I00_READINESS_PROBE_V1",
                content_type="application/vnd.gwf.readiness-probe",
            )
            if not runtime.object_store.verify(probe.sha256):
                raise RuntimeError("object-store hash verification failed")
            checks["object_store"] = "PASS"
        except Exception:
            checks["object_store"] = "FAIL"
            return JSONResponse(
                status_code=503,
                content={"ok": False, "core_health": "DEGRADED", "reason": "object_store_probe_failed", "checks": checks},
            )

        observer_path = getattr(runtime.observer, "path", None)
        if observer_path is None:
            checks["observability"] = "FAIL"
            return JSONResponse(
                status_code=503,
                content={"ok": False, "core_health": "DEGRADED", "reason": "observability_not_configured", "checks": checks},
            )
        temp_path = None
        try:
            observer_parent = Path(observer_path).parent
            observer_parent.mkdir(parents=True, exist_ok=True)
            fd, temp_path = tempfile.mkstemp(prefix="gwr-ready-", dir=str(observer_parent))
            os.close(fd)
            Path(temp_path).write_bytes(b"gwr-observability-ready")
            Path(temp_path).unlink()
            temp_path = None
            runtime.observer.metrics()
            checks["observability"] = "PASS"
        except Exception:
            if temp_path:
                try:
                    Path(temp_path).unlink(missing_ok=True)
                except Exception:
                    pass
            checks["observability"] = "FAIL"
            return JSONResponse(
                status_code=503,
                content={"ok": False, "core_health": "DEGRADED", "reason": "observability_probe_failed", "checks": checks},
            )

        return {
            "ok": True,
            "core_health": "HEALTHY",
            "backend": getattr(runtime.db, "backend_name", "unknown"),
            "build_sha": resolved_product_info["build_sha"],
            "checks": checks,
        }

    @app.get('/browser/home-summary')
    def browser_home_summary(request: Request):
        _, principal = browser_principal(request)
        readiness = ready()
        if isinstance(readiness, JSONResponse):
            readiness_payload = json.loads(readiness.body.decode("utf-8"))
        else:
            readiness_payload = readiness
        return product.home_summary(
            principal.actor_id,
            build_sha=resolved_product_info["build_sha"],
            core_health=str(readiness_payload.get("core_health") or "UNKNOWN"),
        )

    @app.get('/browser/projects-index')
    def browser_projects_index(request: Request):
        _, principal = browser_principal(request)
        return product.projects_index(
            principal.actor_id,
            build_sha=resolved_product_info["build_sha"],
        )

    @app.get('/browser/access-summary')
    def browser_access_summary(request: Request):
        _, principal = browser_principal(request)
        result = product.access_summary(
            principal.actor_id,
            build_sha=resolved_product_info["build_sha"],
        )
        result["session"] = {
            "actor_id": principal.actor_id,
            "principal_id": principal.principal_id,
            "auth_method": principal.auth_method,
            "issued_at": principal.issued_at,
            "expires_at": principal.expires_at,
        }
        return result

    @app.post('/browser/access/tenants')
    def browser_create_tenant(body: TenantCreateBody, request: Request):
        _, principal = browser_principal(request)
        tenant_id = runtime.tenancy.create_tenant(body.name, principal.actor_id)
        return {
            "ok": True,
            "tenant_id": tenant_id,
            "access": product.access_summary(
                principal.actor_id,
                build_sha=resolved_product_info["build_sha"],
            ),
        }

    @app.post('/browser/access/tenants/{tenant_id}/workspaces')
    def browser_create_workspace(tenant_id: str, body: WorkspaceCreateBody, request: Request):
        _, principal = browser_principal(request)
        try:
            runtime.tenancy.require_tenant_access(
                principal.actor_id, tenant_id, "MANAGE_WORKSPACE"
            )
        except (AuthorityDenied, NotFound) as exc:
            raise HTTPException(status_code=404, detail="tenant not found") from exc
        workspace_id = runtime.tenancy.create_workspace(
            tenant_id, body.name, principal.actor_id
        )
        return {
            "ok": True,
            "workspace_id": workspace_id,
            "access": product.access_summary(
                principal.actor_id,
                build_sha=resolved_product_info["build_sha"],
            ),
        }

    @app.post('/browser/access/tenants/{tenant_id}/members')
    def browser_add_tenant_member(tenant_id: str, body: MembershipBody, request: Request):
        _, principal = browser_principal(request)
        try:
            runtime.tenancy.require_tenant_access(
                principal.actor_id, tenant_id, "MANAGE_MEMBERS"
            )
        except (AuthorityDenied, NotFound) as exc:
            raise HTTPException(status_code=404, detail="tenant not found") from exc
        try:
            runtime.tenancy.add_tenant_member(
                tenant_id, body.actor_id, body.role, principal.actor_id
            )
        except AuthorityDenied as exc:
            raise HTTPException(status_code=422, detail="actor is not eligible") from exc
        return {
            "ok": True,
            "access": product.access_summary(
                principal.actor_id,
                build_sha=resolved_product_info["build_sha"],
            ),
        }

    @app.delete('/browser/access/tenants/{tenant_id}/members/{actor_id}')
    def browser_revoke_tenant_member(tenant_id: str, actor_id: str, request: Request):
        _, principal = browser_principal(request)
        try:
            runtime.tenancy.require_tenant_access(
                principal.actor_id, tenant_id, "MANAGE_MEMBERS"
            )
        except (AuthorityDenied, NotFound) as exc:
            raise HTTPException(status_code=404, detail="tenant not found") from exc
        runtime.tenancy.revoke_tenant_member(
            tenant_id, actor_id, principal.actor_id
        )
        return {
            "ok": True,
            "access": product.access_summary(
                principal.actor_id,
                build_sha=resolved_product_info["build_sha"],
            ),
        }

    @app.post('/browser/access/workspaces/{workspace_id}/members')
    def browser_add_workspace_member(workspace_id: str, body: MembershipBody, request: Request):
        _, principal = browser_principal(request)
        try:
            runtime.tenancy.require_workspace_access(
                principal.actor_id, workspace_id, "MANAGE_MEMBERS"
            )
        except (AuthorityDenied, NotFound) as exc:
            raise HTTPException(status_code=404, detail="workspace not found") from exc
        try:
            runtime.tenancy.add_workspace_member(
                workspace_id, body.actor_id, body.role, principal.actor_id
            )
        except AuthorityDenied as exc:
            raise HTTPException(status_code=422, detail="actor is not eligible") from exc
        return {
            "ok": True,
            "access": product.access_summary(
                principal.actor_id,
                build_sha=resolved_product_info["build_sha"],
            ),
        }

    @app.delete('/browser/access/workspaces/{workspace_id}/members/{actor_id}')
    def browser_revoke_workspace_member(workspace_id: str, actor_id: str, request: Request):
        _, principal = browser_principal(request)
        try:
            runtime.tenancy.require_workspace_access(
                principal.actor_id, workspace_id, "MANAGE_MEMBERS"
            )
        except (AuthorityDenied, NotFound) as exc:
            raise HTTPException(status_code=404, detail="workspace not found") from exc
        runtime.tenancy.revoke_workspace_member(
            workspace_id, actor_id, principal.actor_id
        )
        return {
            "ok": True,
            "access": product.access_summary(
                principal.actor_id,
                build_sha=resolved_product_info["build_sha"],
            ),
        }

    @app.post('/browser/access/projects/{project_id}/members')
    def browser_add_project_member(project_id: str, body: MembershipBody, request: Request):
        _, principal = browser_principal(request)
        try:
            runtime.tenancy.require_project_access(
                principal.actor_id, project_id, "MANAGE_MEMBERS"
            )
        except (AuthorityDenied, NotFound) as exc:
            raise HTTPException(status_code=404, detail="project not found") from exc
        try:
            runtime.tenancy.add_project_member(
                project_id, body.actor_id, body.role, principal.actor_id
            )
        except AuthorityDenied as exc:
            raise HTTPException(status_code=422, detail="actor is not eligible") from exc
        return {
            "ok": True,
            "access": product.access_summary(
                principal.actor_id,
                build_sha=resolved_product_info["build_sha"],
            ),
        }

    @app.delete('/browser/access/projects/{project_id}/members/{actor_id}')
    def browser_revoke_project_member(project_id: str, actor_id: str, request: Request):
        _, principal = browser_principal(request)
        try:
            runtime.tenancy.require_project_access(
                principal.actor_id, project_id, "MANAGE_MEMBERS"
            )
        except (AuthorityDenied, NotFound) as exc:
            raise HTTPException(status_code=404, detail="project not found") from exc
        runtime.tenancy.revoke_project_member(
            project_id, actor_id, principal.actor_id
        )
        return {
            "ok": True,
            "access": product.access_summary(
                principal.actor_id,
                build_sha=resolved_product_info["build_sha"],
            ),
        }

    @app.get('/browser/projects/create-options')
    def browser_project_create_options(request: Request):
        _, principal = browser_principal(request)
        return product.project_create_options(
            principal.actor_id,
            build_sha=resolved_product_info["build_sha"],
        )

    @app.post('/browser/projects')
    def browser_create_project(body: BrowserProjectCreateBody, request: Request):
        _, principal = browser_principal(request)
        workspace = runtime.db.one(
            "SELECT workspace_id,tenant_id FROM workspaces "
            "WHERE workspace_id=? AND status='ACTIVE'",
            (body.workspace_id,),
        )
        if not workspace:
            raise HTTPException(status_code=404, detail="workspace not found")
        try:
            runtime.tenancy.require_workspace_access(
                principal.actor_id, body.workspace_id, "MANAGE_PROJECT"
            )
        except (AuthorityDenied, NotFound) as exc:
            raise HTTPException(status_code=404, detail="workspace not found") from exc

        name = (body.name or "").strip()
        if not name:
            raise HTTPException(status_code=422, detail="project name is required")

        if body.domain_revision_id:
            eligible = runtime.db.one(
                "SELECT r.revision_id FROM domain_package_revisions r "
                "JOIN domain_packages p ON p.package_id=r.package_id "
                "WHERE r.revision_id=? AND r.status='PUBLISHED' "
                "AND p.status='ACTIVE' AND p.tenant_id=?",
                (body.domain_revision_id, workspace["tenant_id"]),
            )
            if not eligible:
                raise HTTPException(
                    status_code=422,
                    detail="domain revision is not eligible for selected workspace",
                )

        project_id = runtime.create_scoped_project(
            name,
            workspace["tenant_id"],
            body.workspace_id,
            principal.actor_id,
            domain_revision_id=body.domain_revision_id,
        )
        project_row = next(
            row for row in product.projects_index(
                principal.actor_id,
                build_sha=resolved_product_info["build_sha"],
            )["projects"]
            if row["project_id"] == project_id
        )
        return {
            "ok": True,
            "project": project_row,
            "destination": f"/app/projects/{project_id}/overview",
        }

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

    @app.get('/product/meta')
    def product_meta():
        result = dict(resolved_product_info)
        result["capabilities"] = ["domain_sdk", "domain_registry", "research_study_lock", "software_delivery_domain", "linear_domain_orchestration", "pilot_profiles", "one_click_windows_install", "project_lifecycle", "project_archive", "skill_registry", "observable_agent_protocol", "protocol_driven_orchestration", "handoff_chain", "live_operational_events", "recovery_configuration_hierarchy", "auto_recovery", "human_recovery_approval", "plugin_registry", "github_sha_safe_commit", "standard_sha_qa", "process_inspector", "project_dashboard", "human_approval", "failure_recovery", "distributed_runtime"]
        return result

    @app.get('/product/domains/current')
    def current_domain(authorization: str = Header(...)):
        bearer(authorization)
        return DomainSDK.inspect(runtime.domain.data)

    @app.post('/product/domains/validate')
    def validate_domain_package(body: DomainValidationBody, authorization: str = Header(...)):
        bearer(authorization)
        try:
            data = yaml.safe_load(body.yaml_text)
        except Exception as exc:
            return {"ok": False, "errors": [{"code": "PARSE_ERROR", "message": str(exc)}], "warnings": [], "counts": {}}
        return DomainSDK.validate(data).to_dict()

    @app.post('/product/tenants/{tenant_id}/domains')
    def create_domain_package(tenant_id: str, body: DomainPackageCreateBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        package_id = runtime.domains.create_package(tenant_id, body.domain_id, body.name, principal.actor_id, body.description)
        return {"package_id": package_id, "tenant_id": tenant_id, "domain_id": body.domain_id, "name": body.name}

    @app.get('/product/tenants/{tenant_id}/domains')
    def list_domain_packages(tenant_id: str, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        return {"domains": runtime.domains.list_packages(tenant_id, principal.actor_id)}

    @app.post('/product/domains/{package_id}/revisions')
    def add_domain_revision(package_id: str, body: DomainRevisionBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        revision_id = runtime.domains.add_revision(package_id, body.yaml_text, principal.actor_id)
        return runtime.domains.get_revision(revision_id)

    @app.post('/product/domain-revisions/{revision_id}/validate')
    def validate_registered_domain_revision(revision_id: str, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        return runtime.domains.validate_revision(revision_id, principal.actor_id)

    @app.post('/product/domain-revisions/{revision_id}/publish')
    def publish_domain_revision(revision_id: str, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        return runtime.domains.publish_revision(revision_id, principal.actor_id)

    @app.get('/product/domain-revisions/{revision_id}')
    def get_domain_revision(revision_id: str, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        revision = runtime.domains.get_revision(revision_id)
        runtime.tenancy.require_tenant_access(principal.actor_id, revision["tenant_id"], "VIEW")
        return revision

    @app.get('/product/projects/{project_id}/process')
    def product_process(project_id: str, authorization: str = Header(...)):
        project_principal(project_id, authorization, "VIEW")
        return runtime.process.process(project_id)

    @app.get('/product/orchestrations/{orchestration_id}/phases')
    def product_orchestration_phases(orchestration_id: str, authorization: str = Header(...)):
        row = runtime.db.one("SELECT project_id FROM orchestrations WHERE orchestration_id=?", (orchestration_id,))
        if not row:
            raise HTTPException(status_code=404, detail="orchestration not found")
        project_principal(row["project_id"], authorization, "VIEW")
        return {"phases": runtime.process.phases(orchestration_id)}

    @app.get('/product/phases/{phase_execution_id}')
    def product_phase_detail(phase_execution_id: str, authorization: str = Header(...)):
        row = runtime.db.one("SELECT o.project_id FROM phase_executions p JOIN orchestrations o ON o.orchestration_id=p.orchestration_id WHERE p.phase_execution_id=?", (phase_execution_id,))
        if not row:
            raise HTTPException(status_code=404, detail="phase execution not found")
        project_principal(row["project_id"], authorization, "VIEW")
        return runtime.process.phase_detail(phase_execution_id)

    @app.get('/product/phases/{phase_execution_id}/events')
    def product_phase_events(phase_execution_id: str, authorization: str = Header(...)):
        row = runtime.db.one("SELECT o.project_id FROM phase_executions p JOIN orchestrations o ON o.orchestration_id=p.orchestration_id WHERE p.phase_execution_id=?", (phase_execution_id,))
        if not row:
            raise HTTPException(status_code=404, detail="phase execution not found")
        project_principal(row["project_id"], authorization, "VIEW")
        return {"events": runtime.process.phase_events(phase_execution_id)}

    @app.get('/product/phases/{phase_execution_id}/events/stream')
    async def product_phase_event_stream(
        phase_execution_id: str,
        authorization: str = Header(...),
        last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
        follow: bool = Query(default=True),
        poll_interval_ms: int = Query(default=500, ge=100, le=5000),
    ):
        row = runtime.db.one("SELECT o.project_id FROM phase_executions p JOIN orchestrations o ON o.orchestration_id=p.orchestration_id WHERE p.phase_execution_id=?", (phase_execution_id,))
        if not row:
            raise HTTPException(status_code=404, detail="phase execution not found")
        project_principal(row["project_id"], authorization, "VIEW")

        async def stream():
            seen: set[str] = set()
            if last_event_id:
                prior = runtime.db.all(
                    "SELECT event_id FROM phase_stage_events WHERE phase_execution_id=? ORDER BY created_at,event_id",
                    (phase_execution_id,),
                )
                found = False
                for item in prior:
                    seen.add(item["event_id"])
                    if item["event_id"] == last_event_id:
                        found = True
                        break
                if not found:
                    seen.clear()
            while True:
                emitted = False
                rows = runtime.db.all(
                    "SELECT * FROM phase_stage_events WHERE phase_execution_id=? ORDER BY created_at,event_id",
                    (phase_execution_id,),
                )
                for item in rows:
                    if item["event_id"] in seen:
                        continue
                    payload = {
                        "event_id": item["event_id"],
                        "phase_execution_id": phase_execution_id,
                        "stage": item["stage"],
                        "event_type": item["event_type"],
                        "actor_id": item["actor_id"],
                        "message": item["message"],
                        "metadata": parse_json(item["metadata"], {}),
                        "created_at": item["created_at"],
                    }
                    yield f"id: {item['event_id']}\nevent: {item['event_type']}\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n"
                    seen.add(item["event_id"])
                    emitted = True
                if not follow:
                    break
                phase = runtime.db.one("SELECT status FROM phase_executions WHERE phase_execution_id=?", (phase_execution_id,))
                if phase and phase["status"] in {"SUCCEEDED", "FAILED", "SKIPPED"} and not emitted:
                    break
                await asyncio.sleep(poll_interval_ms / 1000.0)

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.patch('/product/projects/{project_id}')
    def rename_project(project_id: str, body: ProjectRenameBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        project_principal(project_id, authorization, "MANAGE_MEMBERS")
        return runtime.project_governance.rename(project_id, body.name, principal.actor_id)

    @app.post('/product/projects/{project_id}/archive')
    def archive_project(project_id: str, body: ProjectArchiveBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        project_principal(project_id, authorization, "MANAGE_MEMBERS")
        return runtime.project_governance.archive(project_id, principal.actor_id, drain=body.drain, reason=body.reason)

    @app.post('/product/projects/{project_id}/restore')
    def restore_project(project_id: str, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        project_principal(project_id, authorization, "MANAGE_MEMBERS")
        return runtime.project_governance.restore(project_id, principal.actor_id)

    @app.get('/product/projects/{project_id}/lifecycle')
    def project_lifecycle(project_id: str, authorization: str = Header(...)):
        project_principal(project_id, authorization, "VIEW")
        return {
            "lifecycle": runtime.project_governance.status(project_id),
            "name_history": runtime.project_governance.name_history(project_id),
        }

    @app.get('/product/projects/{project_id}/agent-protocol-settings')
    def project_agent_protocol_settings(project_id: str, authorization: str = Header(...)):
        project_principal(project_id, authorization, "VIEW")
        return runtime.agent_protocol.project_defaults(project_id)

    @app.put('/product/projects/{project_id}/agent-protocol-settings')
    def update_project_agent_protocol_settings(project_id: str, body: ProjectAgentProtocolSettingsBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        project_principal(project_id, authorization, "MANAGE_MEMBERS")
        return runtime.agent_protocol.set_project_defaults(
            project_id,
            principal.actor_id,
            recovery_mode=body.recovery_mode,
            retry_budget=body.retry_budget,
        )

    @app.post('/product/projects/{project_id}/plugins')
    def create_plugin_connection(project_id: str, body: PluginConnectionBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        project_principal(project_id, authorization, "MANAGE_MEMBERS")
        connection_id = runtime.plugins.create_connection(
            project_id,
            body.plugin_type,
            body.external_connection_ref,
            body.capabilities,
            principal.actor_id,
            metadata=body.metadata,
        )
        return runtime.plugins.get(connection_id)

    @app.get('/product/projects/{project_id}/plugins')
    def list_plugin_connections(project_id: str, authorization: str = Header(...)):
        project_principal(project_id, authorization, "VIEW")
        return {"plugins": runtime.plugins.list_for_project(project_id)}

    @app.post('/product/plugins/{connection_id}/disable')
    def disable_plugin_connection(connection_id: str, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        connection = runtime.plugins.get(connection_id)
        project_principal(connection["project_id"], authorization, "MANAGE_MEMBERS")
        return runtime.plugins.disable(connection_id, principal.actor_id)

    @app.post('/product/projects/{project_id}/github/repositories')
    def bind_github_repository(project_id: str, body: GitHubRepositoryBindingBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        project_principal(project_id, authorization, "MANAGE_MEMBERS")
        binding_id = runtime.github.bind_repository(
            project_id,
            body.connection_id,
            body.repository_full_name,
            body.default_branch,
            principal.actor_id,
            write_policy=body.write_policy,
            allowed_branches=body.allowed_branches,
        )
        return runtime.github.binding(binding_id)

    @app.post('/product/projects/{project_id}/github/change-sets')
    def prepare_github_change_set(project_id: str, body: GitHubChangeSetBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        project_principal(project_id, authorization, "USE")
        change_set_id = runtime.github.prepare_change_set(
            project_id,
            body.binding_id,
            body.branch,
            body.expected_head_sha,
            body.changes,
            body.commit_message,
            principal.actor_id,
        )
        return runtime.github.inspect(change_set_id)

    @app.post('/product/github/change-sets/{change_set_id}/preflight')
    def preflight_github_change_set(change_set_id: str, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        item = runtime.github.inspect(change_set_id)
        project_principal(item["project_id"], authorization, "USE")
        return runtime.github.preflight(change_set_id, principal.actor_id)

    @app.post('/product/github/change-sets/{change_set_id}/execute')
    def execute_github_change_set(change_set_id: str, body: GitHubExecuteBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        item = runtime.github.inspect(change_set_id)
        project_principal(item["project_id"], authorization, "USE")
        return runtime.github.execute(change_set_id, body.changes, principal.actor_id)

    @app.get('/product/github/change-sets/{change_set_id}')
    def inspect_github_change_set(change_set_id: str, authorization: str = Header(...)):
        item = runtime.github.inspect(change_set_id)
        project_principal(item["project_id"], authorization, "VIEW")
        return item

    @app.post('/product/skills')
    def create_skill(body: SkillPackageBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        sid = runtime.agent_protocol.create_skill_package(body.skill_id, body.name, principal.actor_id, description=body.description)
        return {"skill_package_id": sid, "skill_id": body.skill_id, "name": body.name}

    @app.post('/product/skills/{skill_package_id}/revisions')
    def create_skill_revision(skill_package_id: str, body: SkillRevisionBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        rid = runtime.agent_protocol.add_skill_revision(
            skill_package_id, body.version, body.markdown, principal.actor_id,
            tool_requirements=body.tool_requirements, qa_contract=body.qa_contract,
        )
        return {"skill_revision_id": rid, "skill_package_id": skill_package_id, "version": body.version}

    @app.post('/product/phases/{phase_execution_id}/protocol')
    def create_phase_protocol(phase_execution_id: str, body: ProtocolCreateBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        row = runtime.db.one("SELECT o.project_id FROM phase_executions p JOIN orchestrations o ON o.orchestration_id=p.orchestration_id WHERE p.phase_execution_id=?", (phase_execution_id,))
        if not row:
            raise HTTPException(status_code=404, detail="phase execution not found")
        project_principal(row["project_id"], authorization, "USE")
        pid = runtime.agent_protocol.create_protocol(
            phase_execution_id, body.skill_revision_id, principal.actor_id,
            recovery_mode=body.recovery_mode, retry_budget=body.retry_budget,
        )
        return runtime.agent_protocol.inspect(phase_execution_id)

    @app.post('/product/phases/{phase_execution_id}/preflight')
    def phase_preflight(phase_execution_id: str, body: PreflightBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        return runtime.agent_protocol.record_preflight(phase_execution_id, body.checks, principal.actor_id)

    @app.post('/product/phases/{phase_execution_id}/plan')
    def phase_plan(phase_execution_id: str, body: PlanBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        plan_id = runtime.agent_protocol.create_plan(phase_execution_id, body.objective, body.steps, principal.actor_id, reason=body.reason)
        return {"plan_id": plan_id}

    @app.post('/product/phases/{phase_execution_id}/execute')
    def phase_execute(phase_execution_id: str, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        runtime.agent_protocol.start_execution(phase_execution_id, principal.actor_id)
        return runtime.agent_protocol.inspect(phase_execution_id)

    @app.post('/product/phases/{phase_execution_id}/steps/{step_index}')
    def phase_step(phase_execution_id: str, step_index: int, body: StepUpdateBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        runtime.agent_protocol.update_step(phase_execution_id, step_index, body.status, principal.actor_id, note=body.note)
        return runtime.agent_protocol.inspect(phase_execution_id)

    @app.post('/product/phases/{phase_execution_id}/problems')
    def phase_problem(phase_execution_id: str, body: ProblemBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        problem_id = runtime.agent_protocol.record_problem(
            phase_execution_id, principal.actor_id, code=body.code, summary=body.summary, detail=body.detail,
            affected_step=body.affected_step, severity=body.severity,
        )
        return {"problem_id": problem_id}

    @app.post('/product/problems/{problem_id}/recovery')
    def problem_recovery(problem_id: str, body: RecoveryProposalBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        return runtime.agent_protocol.propose_recovery(
            problem_id, principal.actor_id, action=body.action, target_step=body.target_step,
            rationale=body.rationale, plan_patch=body.plan_patch, risk_class=body.risk_class,
            normative_change=body.normative_change,
        )

    @app.post('/product/recovery-proposals/{proposal_id}/decision')
    def recovery_decision(proposal_id: str, body: RecoveryDecisionBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        decision_id = runtime.agent_protocol.decide_recovery(proposal_id, principal.actor_id, body.decision, reason=body.reason)
        return {"decision_id": decision_id, "proposal_id": proposal_id, "decision": body.decision}

    @app.post('/product/recovery-proposals/{proposal_id}/apply')
    def recovery_apply(proposal_id: str, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        return runtime.agent_protocol.apply_recovery(proposal_id, principal.actor_id)

    @app.post('/product/phases/{phase_execution_id}/verify')
    def phase_verify(phase_execution_id: str, body: VerifyBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        return runtime.agent_protocol.verify(phase_execution_id, principal.actor_id, qa_result=body.qa_result, detail=body.detail)

    @app.post('/product/phases/{phase_execution_id}/handoff')
    def phase_handoff(phase_execution_id: str, body: HandoffBody, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        handoff_id = runtime.agent_protocol.write_handoff(phase_execution_id, principal.actor_id, body.handoff)
        return {"handoff_id": handoff_id}

    @app.post('/product/phases/{phase_execution_id}/complete')
    def phase_complete(phase_execution_id: str, authorization: str = Header(...)):
        _, principal = bearer(authorization)
        runtime.agent_protocol.complete(phase_execution_id, principal.actor_id)
        return runtime.agent_protocol.inspect(phase_execution_id)

    @app.get('/product/phases/{phase_execution_id}/agent-protocol')
    def phase_agent_protocol(phase_execution_id: str, authorization: str = Header(...)):
        row = runtime.db.one("SELECT o.project_id FROM phase_executions p JOIN orchestrations o ON o.orchestration_id=p.orchestration_id WHERE p.phase_execution_id=?", (phase_execution_id,))
        if not row:
            raise HTTPException(status_code=404, detail="phase execution not found")
        project_principal(row["project_id"], authorization, "VIEW")
        return runtime.agent_protocol.inspect(phase_execution_id)

    @app.get('/product/projects/{project_id}/dashboard')
    def product_dashboard(project_id: str, authorization: str = Header(...)):
        project_principal(project_id, authorization, "VIEW")
        return product.summary(project_id)

    @app.get('/product/projects/{project_id}/approvals')
    def product_approvals(project_id: str, authorization: str = Header(...)):
        project_principal(project_id, authorization, "VIEW")
        return {"approvals": product.pending_approvals(project_id)}

    @app.get('/product/projects/{project_id}/failures')
    def product_failures(project_id: str, authorization: str = Header(...)):
        project_principal(project_id, authorization, "VIEW")
        return {"failures": product.failures(project_id), "graph": product.failure_graph(project_id)}

    @app.get('/product/projects/{project_id}/runs')
    def product_runs(project_id: str, authorization: str = Header(...)):
        project_principal(project_id, authorization, "VIEW")
        return {"runs": product.runs(project_id)}

    @app.get('/product/projects/{project_id}/distributed')
    def product_distributed(project_id: str, authorization: str = Header(...)):
        project_principal(project_id, authorization, "VIEW")
        return product.distributed(project_id)

    if web_root is not None:
        static_root = Path(web_root).resolve()
        index_file = static_root / "index.html"
        app_js = static_root / "app.js"
        styles_css = static_root / "styles.css"
        for required in (index_file, app_js, styles_css):
            if not required.is_file():
                raise RuntimeError(f"Required browser shell asset missing: {required}")

        @app.get('/', include_in_schema=False)
        def root_redirect():
            return RedirectResponse(url="/app", status_code=307)

        @app.get('/app', include_in_schema=False)
        @app.get('/app/', include_in_schema=False)
        def browser_app():
            return FileResponse(index_file, media_type="text/html")

        @app.get('/app/{path:path}', include_in_schema=False)
        def browser_app_deep_link(path: str):
            root_segment = path.strip('/').split('/', 1)[0] if path.strip('/') else ""
            if root_segment not in {"home", "projects", "operations", "research", "system", "shared-library", "agents"}:
                raise HTTPException(status_code=404, detail="browser route not found")
            return FileResponse(index_file, media_type="text/html")

        @app.get('/assets/app.js', include_in_schema=False)
        def browser_app_js():
            return FileResponse(app_js, media_type="text/javascript")

        @app.get('/assets/styles.css', include_in_schema=False)
        def browser_styles():
            return FileResponse(styles_css, media_type="text/css")

    return app
