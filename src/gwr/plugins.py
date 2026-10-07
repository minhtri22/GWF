from __future__ import annotations

from typing import Any

from .errors import AuthorityDenied, NotFound, ValidationError
from .utils import canonical_json, parse_json, uid, utcnow


SECRET_FIELD_NAMES = {
    "token",
    "access_token",
    "refresh_token",
    "password",
    "secret",
    "client_secret",
    "private_key",
    "authorization",
    "api_key",
}
SECRET_PREFIXES = ("ghp_", "github_pat_", "gho_", "ghu_", "ghs_", "ghr_", "sk-")
GITHUB_CAPABILITIES = {"REPO_READ", "CONTENT_WRITE", "WORKFLOW_WRITE", "PULL_REQUEST_WRITE", "MERGE_PULL_REQUEST"}


class PluginConnectionService:
    """Persistent plugin connection metadata with runtime-only adapter binding.

    Authentication material is deliberately out of scope for persistence. The
    database stores only an opaque connection reference that a host integration
    can resolve to credentials outside GWF.
    """

    def __init__(self, db, governance, tenancy, project_governance):
        self.db = db
        self.gov = governance
        self.tenancy = tenancy
        self.projects = project_governance
        self._adapters: dict[str, Any] = {}

    def _require_manage(self, project_id: str, actor_id: str) -> None:
        self.projects.require_mutable(project_id)
        actor = self.gov._actor(actor_id)
        if actor["actor_type"] != "HUMAN":
            raise AuthorityDenied("Plugin connections must be managed by a human actor")
        scope = self.tenancy.scope_for_project(project_id)
        if scope:
            self.tenancy.require_project_access(actor_id, project_id, "MANAGE_MEMBERS")
            return
        self.gov.authorize(actor_id, "PROPOSE", {"project_id": project_id, "action": "MANAGE_PLUGIN"})

    @classmethod
    def _assert_no_secret_material(cls, value: Any, *, path: str = "metadata") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = str(key).strip().lower()
                if lowered in SECRET_FIELD_NAMES:
                    raise ValidationError(
                        "Plugin credentials must not be persisted in GWF",
                        details={"field": f"{path}.{key}"},
                    )
                cls._assert_no_secret_material(child, path=f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                cls._assert_no_secret_material(child, path=f"{path}[{index}]")
        elif isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith(SECRET_PREFIXES):
                raise ValidationError(
                    "Plugin credentials must not be persisted in GWF",
                    details={"field": path},
                )

    def create_connection(
        self,
        project_id: str,
        plugin_type: str,
        external_connection_ref: str,
        capabilities: list[str],
        actor_id: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        self._require_manage(project_id, actor_id)
        plugin_type = str(plugin_type).strip().lower()
        if plugin_type not in {"github"}:
            raise ValidationError("Unsupported plugin_type", details={"plugin_type": plugin_type})
        if not external_connection_ref or not str(external_connection_ref).strip():
            raise ValidationError("external_connection_ref is required")
        if str(external_connection_ref).strip().startswith(SECRET_PREFIXES):
            raise ValidationError("external_connection_ref must be an opaque connection id, not a credential")
        caps = sorted({str(x).strip().upper() for x in capabilities if str(x).strip()})
        if not caps:
            raise ValidationError("At least one plugin capability is required")
        if plugin_type == "github":
            unknown = sorted(set(caps) - GITHUB_CAPABILITIES)
            if unknown:
                raise ValidationError("Unsupported GitHub plugin capability", details={"capabilities": unknown})
        metadata = metadata or {}
        self._assert_no_secret_material(metadata)
        existing = self.db.one(
            "SELECT * FROM plugin_connections WHERE project_id=? AND plugin_type=? AND external_connection_ref=?",
            (project_id, plugin_type, external_connection_ref),
        )
        if existing:
            if existing["status"] == "ACTIVE":
                return existing["connection_id"]
            raise ValidationError("Plugin connection already exists but is not active")
        connection_id = uid("pluginconn")
        now = utcnow()
        with self.db.tx():
            self.db.conn.execute(
                "INSERT INTO plugin_connections VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    connection_id,
                    project_id,
                    plugin_type,
                    external_connection_ref,
                    canonical_json(caps),
                    "ACTIVE",
                    canonical_json(metadata),
                    actor_id,
                    now,
                    now,
                ),
            )
            self.gov.append_audit(
                project_id,
                actor_id,
                "PLUGIN_CONNECTION_CREATED",
                "PluginConnection",
                connection_id,
                metadata={"plugin_type": plugin_type, "capabilities": caps},
            )
        return connection_id

    def get(self, connection_id: str) -> dict[str, Any]:
        row = self.db.one("SELECT * FROM plugin_connections WHERE connection_id=?", (connection_id,))
        if not row:
            raise NotFound("Plugin connection not found")
        item = dict(row)
        item["capabilities"] = parse_json(item["capabilities"], [])
        item["metadata"] = parse_json(item["metadata"], {})
        item["adapter_attached"] = connection_id in self._adapters
        return item

    def list_for_project(self, project_id: str) -> list[dict[str, Any]]:
        return [self.get(r["connection_id"]) for r in self.db.all(
            "SELECT connection_id FROM plugin_connections WHERE project_id=? ORDER BY created_at,connection_id",
            (project_id,),
        )]

    def disable(self, connection_id: str, actor_id: str) -> dict[str, Any]:
        row = self.db.one("SELECT * FROM plugin_connections WHERE connection_id=?", (connection_id,))
        if not row:
            raise NotFound("Plugin connection not found")
        self._require_manage(row["project_id"], actor_id)
        with self.db.tx():
            self.db.conn.execute(
                "UPDATE plugin_connections SET status='DISABLED',updated_at=? WHERE connection_id=?",
                (utcnow(), connection_id),
            )
            self.gov.append_audit(
                row["project_id"],
                actor_id,
                "PLUGIN_CONNECTION_DISABLED",
                "PluginConnection",
                connection_id,
            )
        self._adapters.pop(connection_id, None)
        return self.get(connection_id)

    def attach_runtime_adapter(self, connection_id: str, adapter: Any) -> None:
        connection = self.get(connection_id)
        if connection["status"] != "ACTIVE":
            raise ValidationError("Cannot attach adapter to inactive connection")
        if connection["plugin_type"] == "github":
            caps = set(connection["capabilities"])
            required = {"get_branch_head", "get_file", "get_commit"}
            if caps.intersection({"CONTENT_WRITE", "WORKFLOW_WRITE"}):
                required.add("commit_files")
            missing = sorted(name for name in required if not callable(getattr(adapter, name, None)))
            if missing:
                raise ValidationError(
                    "GitHub adapter is incomplete for connection capabilities",
                    details={"missing": missing, "capabilities": sorted(caps)},
                )
        self._adapters[connection_id] = adapter

    def attach_github_rest_adapter(self, connection_id: str, credential_resolver, **adapter_options):
        connection = self.get(connection_id)
        if connection["plugin_type"] != "github":
            raise ValidationError("Connection is not a GitHub plugin")
        if not callable(credential_resolver):
            raise ValidationError("credential_resolver must be callable")
        from .github_rest_adapter import GitHubRestAdapter

        external_ref = connection["external_connection_ref"]

        def token_provider():
            return credential_resolver(external_ref)

        adapter = GitHubRestAdapter(token_provider, **adapter_options)
        self.attach_runtime_adapter(connection_id, adapter)
        return adapter

    def adapter(self, connection_id: str, *, capability: str | None = None):
        connection = self.get(connection_id)
        if connection["status"] != "ACTIVE":
            raise ValidationError("Plugin connection is not active")
        if capability and capability.upper() not in set(connection["capabilities"]):
            raise AuthorityDenied(
                "Plugin connection lacks required capability",
                details={"required": capability.upper(), "connection_id": connection_id},
            )
        adapter = self._adapters.get(connection_id)
        if adapter is None:
            raise ValidationError(
                "Plugin adapter is not attached to this runtime",
                details={"connection_id": connection_id, "external_connection_ref": connection["external_connection_ref"]},
            )
        return adapter
