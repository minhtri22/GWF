from __future__ import annotations

from typing import Any
import yaml

from .domain import DomainPackage
from .domain_sdk import DomainSDK
from .errors import NotFound, ValidationError, InvalidTransition
from .utils import canonical_json, content_hash, parse_json, uid, utcnow


class DomainRegistryService:
    """Tenant-scoped immutable domain package registry.

    Domain revisions are mutable only while DRAFT. Validation snapshots a structured
    report. Publishing freezes the revision and makes it eligible for project pinning.
    """

    def __init__(self, db, tenancy):
        self.db = db
        self.tenancy = tenancy

    def create_package(self, tenant_id: str, domain_id: str, name: str, actor_id: str, description: str = "") -> str:
        self.tenancy.require_tenant_access(actor_id, tenant_id, "MANAGE_PROJECT")
        if self.db.one("SELECT 1 FROM domain_packages WHERE tenant_id=? AND domain_id=?", (tenant_id, domain_id)):
            raise ValidationError("Domain package already exists in tenant")
        # Validate identifier using SDK without requiring a full package.
        try:
            DomainSDK.scaffold(domain_id, display_name=name)
        except Exception as exc:
            raise ValidationError("Invalid domain_id", details={"domain_id": domain_id, "error": str(exc)})
        pid = uid("domainpkg")
        self.db.conn.execute(
            "INSERT INTO domain_packages VALUES(?,?,?,?,?,?,?,?)",
            (pid, tenant_id, domain_id, name, description, "ACTIVE", actor_id, utcnow()),
        )
        self.db.conn.commit()
        return pid

    def add_revision(self, package_id: str, yaml_text: str, actor_id: str) -> str:
        pkg = self.db.one("SELECT * FROM domain_packages WHERE package_id=?", (package_id,))
        if not pkg:
            raise NotFound("Domain package not found")
        self.tenancy.require_tenant_access(actor_id, pkg["tenant_id"], "MANAGE_PROJECT")
        try:
            data = yaml.safe_load(yaml_text)
        except Exception as exc:
            raise ValidationError("Domain YAML parse failed", details={"error": str(exc)})
        if not isinstance(data, dict):
            raise ValidationError("Domain YAML root must be an object")
        if data.get("domain_id") != pkg["domain_id"]:
            raise ValidationError("Revision domain_id must match package", details={"expected": pkg["domain_id"], "actual": data.get("domain_id")})
        revno = self.db.one("SELECT COALESCE(MAX(revision_number),0)+1 n FROM domain_package_revisions WHERE package_id=?", (package_id,))["n"]
        rid = uid("domainrev")
        report = DomainSDK.validate(data).to_dict()
        status = "VALIDATED" if report["ok"] else "DRAFT"
        self.db.conn.execute(
            "INSERT INTO domain_package_revisions VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (rid, package_id, int(revno), str(data.get("version") or ""), yaml_text, content_hash(data),
             canonical_json(report), status, actor_id, utcnow(), None),
        )
        self.db.conn.commit()
        return rid

    def validate_revision(self, revision_id: str, actor_id: str) -> dict[str, Any]:
        rev = self.db.one(
            "SELECT r.*,p.tenant_id,p.domain_id FROM domain_package_revisions r "
            "JOIN domain_packages p ON p.package_id=r.package_id WHERE r.revision_id=?",
            (revision_id,),
        )
        if not rev:
            raise NotFound("Domain revision not found")
        self.tenancy.require_tenant_access(actor_id, rev["tenant_id"], "MANAGE_PROJECT")
        data = yaml.safe_load(rev["yaml_text"])
        report = DomainSDK.validate(data).to_dict()
        if rev["status"] == "PUBLISHED":
            return report
        self.db.conn.execute(
            "UPDATE domain_package_revisions SET validation_report=?,status=? WHERE revision_id=?",
            (canonical_json(report), "VALIDATED" if report["ok"] else "DRAFT", revision_id),
        )
        self.db.conn.commit()
        return report

    def publish_revision(self, revision_id: str, actor_id: str) -> dict[str, Any]:
        rev = self.db.one(
            "SELECT r.*,p.tenant_id,p.domain_id FROM domain_package_revisions r "
            "JOIN domain_packages p ON p.package_id=r.package_id WHERE r.revision_id=?",
            (revision_id,),
        )
        if not rev:
            raise NotFound("Domain revision not found")
        self.tenancy.require_tenant_access(actor_id, rev["tenant_id"], "MANAGE_PROJECT")
        if rev["status"] == "PUBLISHED":
            return self.get_revision(revision_id)
        report = DomainSDK.validate(yaml.safe_load(rev["yaml_text"])).to_dict()
        if not report["ok"]:
            raise InvalidTransition("Cannot publish invalid domain revision")
        self.db.conn.execute(
            "UPDATE domain_package_revisions SET validation_report=?,status='PUBLISHED',published_at=? WHERE revision_id=?",
            (canonical_json(report), utcnow(), revision_id),
        )
        self.db.conn.commit()
        return self.get_revision(revision_id)

    def get_revision(self, revision_id: str) -> dict[str, Any]:
        row = self.db.one(
            "SELECT r.*,p.domain_id,p.name,p.tenant_id FROM domain_package_revisions r "
            "JOIN domain_packages p ON p.package_id=r.package_id WHERE r.revision_id=?",
            (revision_id,),
        )
        if not row:
            raise NotFound("Domain revision not found")
        out = dict(row)
        out["validation_report"] = parse_json(out["validation_report"], {})
        return out

    def list_packages(self, tenant_id: str, actor_id: str) -> list[dict[str, Any]]:
        self.tenancy.require_tenant_access(actor_id, tenant_id, "VIEW")
        rows = self.db.all("SELECT * FROM domain_packages WHERE tenant_id=? ORDER BY created_at,domain_id", (tenant_id,))
        out = []
        for row in rows:
            item = dict(row)
            item["revisions"] = [
                self.get_revision(r["revision_id"])
                for r in self.db.all("SELECT revision_id FROM domain_package_revisions WHERE package_id=? ORDER BY revision_number", (row["package_id"],))
            ]
            out.append(item)
        return out

    def pin_project(self, project_id: str, revision_id: str, actor_id: str) -> None:
        rev = self.get_revision(revision_id)
        if rev["status"] != "PUBLISHED":
            raise InvalidTransition("Project may only pin a PUBLISHED domain revision")
        scope = self.tenancy.scope_for_project(project_id)
        if not scope:
            raise ValidationError("Project must be tenant-scoped before domain pinning")
        if scope.tenant_id != rev["tenant_id"]:
            raise ValidationError("Domain revision belongs to another tenant")
        self.tenancy.require_project_access(actor_id, project_id, "MANAGE_MEMBERS")
        existing = self.db.one("SELECT 1 FROM project_domain_bindings WHERE project_id=?", (project_id,))
        if existing:
            raise InvalidTransition("Project domain revision is immutable; use an explicit upgrade proposal")
        self.db.conn.execute(
            "INSERT INTO project_domain_bindings VALUES(?,?,?,?)",
            (project_id, revision_id, actor_id, utcnow()),
        )
        self.db.conn.execute("UPDATE projects SET domain_id=? WHERE id=?", (rev["domain_id"], project_id))
        self.db.conn.commit()

    def project_binding(self, project_id: str) -> dict[str, Any] | None:
        row = self.db.one(
            "SELECT b.*,r.revision_number,r.semantic_version,r.payload_hash,r.status AS revision_status,"
            "p.domain_id,p.name AS domain_name FROM project_domain_bindings b "
            "JOIN domain_package_revisions r ON r.revision_id=b.domain_revision_id "
            "JOIN domain_packages p ON p.package_id=r.package_id WHERE b.project_id=?",
            (project_id,),
        )
        return dict(row) if row else None

    def package_for_project(self, project_id: str) -> DomainPackage | None:
        row = self.db.one(
            "SELECT r.yaml_text FROM project_domain_bindings b JOIN domain_package_revisions r "
            "ON r.revision_id=b.domain_revision_id WHERE b.project_id=?",
            (project_id,),
        )
        if not row:
            return None
        return DomainPackage(yaml.safe_load(row["yaml_text"]))
