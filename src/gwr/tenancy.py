from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import AuthorityDenied, NotFound, ValidationError
from .utils import canonical_json, parse_json, uid, utcnow


TENANT_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "OWNER": {"VIEW", "USE", "RUN", "PROPOSE", "REVIEW", "APPROVE", "MANAGE_MEMBERS", "MANAGE_WORKSPACE", "MANAGE_PROJECT"},
    "ADMIN": {"VIEW", "USE", "RUN", "PROPOSE", "REVIEW", "APPROVE", "MANAGE_MEMBERS", "MANAGE_WORKSPACE", "MANAGE_PROJECT"},
    "MEMBER": {"VIEW", "USE", "RUN", "PROPOSE", "REVIEW"},
    "VIEWER": {"VIEW"},
}

WORKSPACE_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "OWNER": {"VIEW", "USE", "RUN", "PROPOSE", "REVIEW", "APPROVE", "MANAGE_MEMBERS", "MANAGE_PROJECT"},
    "ADMIN": {"VIEW", "USE", "RUN", "PROPOSE", "REVIEW", "APPROVE", "MANAGE_MEMBERS", "MANAGE_PROJECT"},
    "MEMBER": {"VIEW", "USE", "RUN", "PROPOSE", "REVIEW"},
    "VIEWER": {"VIEW"},
}

PROJECT_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "OWNER": {"VIEW", "USE", "RUN", "PROPOSE", "REVIEW", "APPROVE", "MANAGE_MEMBERS"},
    "RESEARCH_LEAD": {"VIEW", "USE", "RUN", "PROPOSE", "REVIEW"},
    "RESEARCHER": {"VIEW", "USE", "RUN", "PROPOSE"},
    "REVIEWER": {"VIEW", "REVIEW"},
    "APPROVER": {"VIEW", "APPROVE"},
    "VIEWER": {"VIEW"},
}

ACTION_TO_PERMISSION = {
    "APPROVE": "APPROVE",
    "CONFIRM": "APPROVE",
    "EXECUTE": "RUN",
    "RUN": "RUN",
    "PROPOSE": "PROPOSE",
    "CREATE_REVISION": "PROPOSE",
    "REVIEW": "REVIEW",
    "ESCALATE": "USE",
    "CANCEL": "USE",
}


@dataclass(frozen=True)
class ProjectScope:
    project_id: str
    tenant_id: str
    workspace_id: str


class TenantService:
    """Tenant/workspace/project access boundary.

    Project IDs remain the storage-level partition key for the existing kernels.
    This service adds the higher-level Tenant -> Workspace -> Project ownership graph
    and must be consulted before any public/scoped access to a project.
    """

    def __init__(self, db):
        self.db = db

    def _actor(self, actor_id: str):
        row = self.db.one("SELECT * FROM actors WHERE actor_id=?", (actor_id,))
        if not row or row["status"] != "ACTIVE":
            raise AuthorityDenied("Actor is not active")
        return row

    def _security_event(self, actor_id: str, action: str, resource_type: str, resource_id: str,
                        *, tenant_id: str | None = None, outcome: str = "SUCCESS", metadata: dict[str, Any] | None = None):
        self.db.conn.execute(
            "INSERT INTO security_events VALUES(?,?,?,?,?,?,?,?,?)",
            (uid("sec"), actor_id, tenant_id, action, resource_type, resource_id, outcome, canonical_json(metadata or {}), utcnow()),
        )

    def create_tenant(self, name: str, creator_actor_id: str, tenant_id: str | None = None) -> str:
        creator = self._actor(creator_actor_id)
        if creator["actor_type"] != "HUMAN":
            raise AuthorityDenied("Tenant owner must be an authenticated human actor")
        tid = tenant_id or uid("tenant")
        self.db.conn.execute(
            "INSERT INTO tenants VALUES(?,?,?,?,?)",
            (tid, name, "ACTIVE", creator_actor_id, utcnow()),
        )
        self.db.conn.execute(
            "INSERT INTO tenant_memberships VALUES(?,?,?,?,?)",
            (tid, creator_actor_id, "OWNER", "ACTIVE", utcnow()),
        )
        self._security_event(creator_actor_id, "CREATE_TENANT", "Tenant", tid, tenant_id=tid)
        self.db.conn.commit()
        return tid

    def create_workspace(self, tenant_id: str, name: str, actor_id: str, workspace_id: str | None = None) -> str:
        self.require_tenant_access(actor_id, tenant_id, "MANAGE_WORKSPACE")
        wid = workspace_id or uid("workspace")
        self.db.conn.execute(
            "INSERT INTO workspaces VALUES(?,?,?,?,?,?)",
            (wid, tenant_id, name, "ACTIVE", actor_id, utcnow()),
        )
        self.db.conn.execute(
            "INSERT INTO workspace_memberships VALUES(?,?,?,?,?)",
            (wid, actor_id, "OWNER", "ACTIVE", utcnow()),
        )
        self._security_event(actor_id, "CREATE_WORKSPACE", "Workspace", wid, tenant_id=tenant_id)
        self.db.conn.commit()
        return wid

    def bind_project(self, project_id: str, tenant_id: str, workspace_id: str, actor_id: str, *, owner_role: str = "OWNER", commit: bool = True) -> None:
        project = self.db.one("SELECT id FROM projects WHERE id=?", (project_id,))
        if not project:
            raise NotFound("Project not found")
        ws = self.db.one("SELECT * FROM workspaces WHERE workspace_id=?", (workspace_id,))
        if not ws or ws["status"] != "ACTIVE":
            raise NotFound("Workspace not found")
        if ws["tenant_id"] != tenant_id:
            raise ValidationError("Workspace does not belong to tenant")
        self.require_workspace_access(actor_id, workspace_id, "MANAGE_PROJECT")
        if self.db.one("SELECT 1 FROM project_scopes WHERE project_id=?", (project_id,)):
            raise ValidationError("Project is already tenant-scoped")
        self.db.conn.execute(
            "INSERT INTO project_scopes VALUES(?,?,?,?,?)",
            (project_id, tenant_id, workspace_id, actor_id, utcnow()),
        )
        self.db.conn.execute(
            "INSERT INTO project_memberships VALUES(?,?,?,?,?)",
            (project_id, actor_id, owner_role, "ACTIVE", utcnow()),
        )
        self._grant_legacy_project_scope(actor_id, project_id)
        self._security_event(actor_id, "BIND_PROJECT", "Project", project_id, tenant_id=tenant_id, metadata={"workspace_id": workspace_id})
        if commit:
            self.db.conn.commit()

    def scope_for_project(self, project_id: str) -> ProjectScope | None:
        row = self.db.one("SELECT * FROM project_scopes WHERE project_id=?", (project_id,))
        if not row:
            return None
        return ProjectScope(project_id=project_id, tenant_id=row["tenant_id"], workspace_id=row["workspace_id"])

    def add_tenant_member(self, tenant_id: str, actor_id: str, role: str, granted_by_actor_id: str) -> None:
        role = role.upper()
        if role not in TENANT_ROLE_PERMISSIONS:
            raise ValidationError("Invalid tenant role")
        self._actor(actor_id)
        self.require_tenant_access(granted_by_actor_id, tenant_id, "MANAGE_MEMBERS")
        existing = self.db.one("SELECT 1 FROM tenant_memberships WHERE tenant_id=? AND actor_id=?", (tenant_id, actor_id))
        if existing:
            self.db.conn.execute("UPDATE tenant_memberships SET role=?,status='ACTIVE' WHERE tenant_id=? AND actor_id=?", (role, tenant_id, actor_id))
        else:
            self.db.conn.execute("INSERT INTO tenant_memberships VALUES(?,?,?,?,?)", (tenant_id, actor_id, role, "ACTIVE", utcnow()))
        self._security_event(granted_by_actor_id, "ADD_TENANT_MEMBER", "Actor", actor_id, tenant_id=tenant_id, metadata={"role": role})
        self.db.conn.commit()

    def add_workspace_member(self, workspace_id: str, actor_id: str, role: str, granted_by_actor_id: str) -> None:
        role = role.upper()
        if role not in WORKSPACE_ROLE_PERMISSIONS:
            raise ValidationError("Invalid workspace role")
        self._actor(actor_id)
        self.require_workspace_access(granted_by_actor_id, workspace_id, "MANAGE_MEMBERS")
        ws = self.db.one("SELECT tenant_id FROM workspaces WHERE workspace_id=?", (workspace_id,))
        if not ws:
            raise NotFound("Workspace not found")
        existing = self.db.one("SELECT 1 FROM workspace_memberships WHERE workspace_id=? AND actor_id=?", (workspace_id, actor_id))
        if existing:
            self.db.conn.execute("UPDATE workspace_memberships SET role=?,status='ACTIVE' WHERE workspace_id=? AND actor_id=?", (role, workspace_id, actor_id))
        else:
            self.db.conn.execute("INSERT INTO workspace_memberships VALUES(?,?,?,?,?)", (workspace_id, actor_id, role, "ACTIVE", utcnow()))
        self._security_event(granted_by_actor_id, "ADD_WORKSPACE_MEMBER", "Actor", actor_id, tenant_id=ws["tenant_id"], metadata={"workspace_id": workspace_id, "role": role})
        self.db.conn.commit()

    def revoke_tenant_member(self, tenant_id: str, actor_id: str, revoked_by_actor_id: str) -> None:
        self.require_tenant_access(revoked_by_actor_id, tenant_id, "MANAGE_MEMBERS")
        tenant = self.db.one("SELECT tenant_id FROM tenants WHERE tenant_id=?", (tenant_id,))
        if not tenant:
            raise NotFound("Tenant not found")
        self.db.conn.execute(
            "UPDATE tenant_memberships SET status='REVOKED' WHERE tenant_id=? AND actor_id=?",
            (tenant_id, actor_id),
        )
        self._security_event(
            revoked_by_actor_id,
            "REVOKE_TENANT_MEMBER",
            "Actor",
            actor_id,
            tenant_id=tenant_id,
        )
        self.db.conn.commit()

    def revoke_workspace_member(self, workspace_id: str, actor_id: str, revoked_by_actor_id: str) -> None:
        self.require_workspace_access(revoked_by_actor_id, workspace_id, "MANAGE_MEMBERS")
        workspace = self.db.one(
            "SELECT tenant_id FROM workspaces WHERE workspace_id=?",
            (workspace_id,),
        )
        if not workspace:
            raise NotFound("Workspace not found")
        self.db.conn.execute(
            "UPDATE workspace_memberships SET status='REVOKED' WHERE workspace_id=? AND actor_id=?",
            (workspace_id, actor_id),
        )
        self._security_event(
            revoked_by_actor_id,
            "REVOKE_WORKSPACE_MEMBER",
            "Actor",
            actor_id,
            tenant_id=workspace["tenant_id"],
            metadata={"workspace_id": workspace_id},
        )
        self.db.conn.commit()

    def add_project_member(self, project_id: str, actor_id: str, role: str, granted_by_actor_id: str) -> None:
        role = role.upper()
        if role not in PROJECT_ROLE_PERMISSIONS:
            raise ValidationError("Invalid project role")
        self._actor(actor_id)
        self.require_project_access(granted_by_actor_id, project_id, "MANAGE_MEMBERS")
        scope = self.scope_for_project(project_id)
        if not scope:
            raise ValidationError("Project is not tenant-scoped")
        existing = self.db.one("SELECT 1 FROM project_memberships WHERE project_id=? AND actor_id=?", (project_id, actor_id))
        if existing:
            self.db.conn.execute("UPDATE project_memberships SET role=?,status='ACTIVE' WHERE project_id=? AND actor_id=?", (role, project_id, actor_id))
        else:
            self.db.conn.execute("INSERT INTO project_memberships VALUES(?,?,?,?,?)", (project_id, actor_id, role, "ACTIVE", utcnow()))
        self._grant_legacy_project_scope(actor_id, project_id)
        self._security_event(granted_by_actor_id, "ADD_PROJECT_MEMBER", "Actor", actor_id, tenant_id=scope.tenant_id, metadata={"project_id": project_id, "role": role})
        self.db.conn.commit()

    def revoke_project_member(self, project_id: str, actor_id: str, revoked_by_actor_id: str) -> None:
        self.require_project_access(revoked_by_actor_id, project_id, "MANAGE_MEMBERS")
        scope = self.scope_for_project(project_id)
        if not scope:
            raise ValidationError("Project is not tenant-scoped")
        self.db.conn.execute("UPDATE project_memberships SET status='REVOKED' WHERE project_id=? AND actor_id=?", (project_id, actor_id))
        self._security_event(revoked_by_actor_id, "REVOKE_PROJECT_MEMBER", "Actor", actor_id, tenant_id=scope.tenant_id, metadata={"project_id": project_id})
        self.db.conn.commit()

    def _grant_legacy_project_scope(self, actor_id: str, project_id: str) -> None:
        row = self._actor(actor_id)
        scopes = list(parse_json(row["project_scope"], []))
        if project_id not in scopes and "*" not in scopes:
            scopes.append(project_id)
            self.db.conn.execute("UPDATE actors SET project_scope=? WHERE actor_id=?", (canonical_json(scopes), actor_id))

    @staticmethod
    def _allows(role: str | None, permission: str, matrix: dict[str, set[str]]) -> bool:
        return bool(role and permission in matrix.get(role.upper(), set()))

    def require_tenant_access(self, actor_id: str, tenant_id: str, permission: str = "VIEW") -> bool:
        actor = self._actor(actor_id)
        if actor_id == "SYSTEM":
            return True
        row = self.db.one("SELECT role,status FROM tenant_memberships WHERE tenant_id=? AND actor_id=?", (tenant_id, actor_id))
        if not row or row["status"] != "ACTIVE" or not self._allows(row["role"], permission, TENANT_ROLE_PERMISSIONS):
            raise AuthorityDenied("Actor outside tenant scope", details={"tenant_id": tenant_id, "permission": permission})
        return True

    def require_workspace_access(self, actor_id: str, workspace_id: str, permission: str = "VIEW") -> bool:
        actor = self._actor(actor_id)
        if actor_id == "SYSTEM":
            return True
        ws = self.db.one("SELECT * FROM workspaces WHERE workspace_id=?", (workspace_id,))
        if not ws or ws["status"] != "ACTIVE":
            raise NotFound("Workspace not found")
        tm = self.db.one("SELECT role,status FROM tenant_memberships WHERE tenant_id=? AND actor_id=?", (ws["tenant_id"], actor_id))
        if tm and tm["status"] == "ACTIVE" and tm["role"].upper() in {"OWNER", "ADMIN"} and self._allows(tm["role"], permission, TENANT_ROLE_PERMISSIONS):
            return True
        wm = self.db.one("SELECT role,status FROM workspace_memberships WHERE workspace_id=? AND actor_id=?", (workspace_id, actor_id))
        if wm and wm["status"] == "ACTIVE" and self._allows(wm["role"], permission, WORKSPACE_ROLE_PERMISSIONS):
            return True
        raise AuthorityDenied("Actor outside workspace scope", details={"workspace_id": workspace_id, "permission": permission})

    def require_project_access(self, actor_id: str, project_id: str, permission: str = "VIEW") -> bool:
        actor = self._actor(actor_id)
        if actor_id == "SYSTEM":
            return True
        scope = self.scope_for_project(project_id)
        if not scope:
            scopes = set(parse_json(actor["project_scope"], []))
            if project_id in scopes or "*" in scopes:
                return True
            raise AuthorityDenied("Actor outside project scope")
        # A scoped project never trusts legacy project_scope by itself. Membership
        # in tenant/workspace/project is authoritative for tenant isolation.
        tm = self.db.one("SELECT role,status FROM tenant_memberships WHERE tenant_id=? AND actor_id=?", (scope.tenant_id, actor_id))
        if tm and tm["status"] == "ACTIVE" and tm["role"].upper() in {"OWNER", "ADMIN"} and self._allows(tm["role"], permission, TENANT_ROLE_PERMISSIONS):
            return True
        wm = self.db.one("SELECT role,status FROM workspace_memberships WHERE workspace_id=? AND actor_id=?", (scope.workspace_id, actor_id))
        if wm and wm["status"] == "ACTIVE" and self._allows(wm["role"], permission, WORKSPACE_ROLE_PERMISSIONS):
            return True
        pm = self.db.one("SELECT role,status FROM project_memberships WHERE project_id=? AND actor_id=?", (project_id, actor_id))
        if pm and pm["status"] == "ACTIVE" and self._allows(pm["role"], permission, PROJECT_ROLE_PERMISSIONS):
            return True
        raise AuthorityDenied("Actor outside tenant-scoped project", details={"project_id": project_id, "permission": permission})

    def permission_for_governance_action(self, action: str) -> str:
        return ACTION_TO_PERMISSION.get(action, "USE")

    def list_accessible_projects(self, actor_id: str, tenant_id: str | None = None) -> list[dict[str, Any]]:
        self._actor(actor_id)
        rows = self.db.all(
            "SELECT p.id,p.name,p.domain_id,p.created_at,s.tenant_id,s.workspace_id "
            "FROM projects p JOIN project_scopes s ON s.project_id=p.id ORDER BY p.created_at,p.id"
        )
        out = []
        for row in rows:
            if tenant_id and row["tenant_id"] != tenant_id:
                continue
            try:
                self.require_project_access(actor_id, row["id"], "VIEW")
            except AuthorityDenied:
                continue
            out.append(dict(row))
        return out

    def memberships_for_actor(self, actor_id: str) -> dict[str, list[dict[str, Any]]]:
        self._actor(actor_id)
        return {
            "tenants": [dict(r) for r in self.db.all("SELECT * FROM tenant_memberships WHERE actor_id=? AND status='ACTIVE' ORDER BY tenant_id", (actor_id,))],
            "workspaces": [dict(r) for r in self.db.all("SELECT * FROM workspace_memberships WHERE actor_id=? AND status='ACTIVE' ORDER BY workspace_id", (actor_id,))],
            "projects": [dict(r) for r in self.db.all("SELECT * FROM project_memberships WHERE actor_id=? AND status='ACTIVE' ORDER BY project_id", (actor_id,))],
        }
