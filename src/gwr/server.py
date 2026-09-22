from __future__ import annotations

import argparse
import importlib.metadata
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .api import create_app
from .errors import ValidationError
from .runtime import GovernedWorkflowRuntime


class ServerConfigError(RuntimeError):
    pass


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _git_head(root: Path) -> str:
    configured = os.environ.get("GWR_BUILD_SHA")
    if configured:
        return configured.strip()
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def _runtime_version() -> str:
    try:
        return importlib.metadata.version("governed-workflow-runtime")
    except importlib.metadata.PackageNotFoundError:
        return "0.8.5"


@dataclass(frozen=True)
class ServerConfig:
    repo_root: Path
    domain_path: Path
    database_target: str
    auth_secret: str
    object_store_root: Path
    observability_path: Path
    web_root: Path
    host: str = "127.0.0.1"
    port: int = 8765
    browser_cookie_secure: bool = False
    bootstrap_username: str | None = None
    bootstrap_password: str | None = None

    @classmethod
    def from_env(
        cls,
        *,
        repo_root: str | Path | None = None,
        host: str | None = None,
        port: int | None = None,
    ) -> "ServerConfig":
        root = Path(repo_root or os.environ.get("GWR_REPO_ROOT") or _default_repo_root()).resolve()
        domain = Path(os.environ.get("GWR_DOMAIN_PATH") or root / "domains" / "research.workflow.yaml").resolve()
        database = os.environ.get("GWR_DATABASE_URL") or str(root / ".gwr" / "server" / "gwr.db")
        auth_secret = os.environ.get("GWR_AUTH_SECRET") or ""
        object_store = Path(os.environ.get("GWR_OBJECT_STORE_ROOT") or root / ".gwr" / "server" / "objects").resolve()
        observability = Path(os.environ.get("GWR_OBSERVABILITY_PATH") or root / ".gwr" / "server" / "observability.jsonl").resolve()
        web_root = Path(os.environ.get("GWR_WEB_ROOT") or root / "web").resolve()
        secure = (os.environ.get("GWR_BROWSER_COOKIE_SECURE") or "").strip().lower() in {"1", "true", "yes", "on"}
        cfg = cls(
            repo_root=root,
            domain_path=domain,
            database_target=database,
            auth_secret=auth_secret,
            object_store_root=object_store,
            observability_path=observability,
            web_root=web_root,
            host=host or os.environ.get("GWR_HOST") or "127.0.0.1",
            port=int(port or os.environ.get("GWR_PORT") or 8765),
            browser_cookie_secure=secure,
            bootstrap_username=os.environ.get("GWR_BOOTSTRAP_USERNAME") or None,
            bootstrap_password=os.environ.get("GWR_BOOTSTRAP_PASSWORD") or None,
        )
        cfg.validate()
        return cfg

    def validate(self) -> None:
        if not self.domain_path.is_file():
            raise ServerConfigError(f"Domain package not found: {self.domain_path}")
        if not self.web_root.is_dir():
            raise ServerConfigError(f"Web root not found: {self.web_root}")
        if len(self.auth_secret.encode("utf-8")) < 32:
            raise ServerConfigError("GWR_AUTH_SECRET must be configured with at least 32 bytes")
        if not (1 <= int(self.port) <= 65535):
            raise ServerConfigError("GWR port must be between 1 and 65535")
        if bool(self.bootstrap_username) != bool(self.bootstrap_password):
            raise ServerConfigError("GWR_BOOTSTRAP_USERNAME and GWR_BOOTSTRAP_PASSWORD must be supplied together")
        if self.bootstrap_password and len(self.bootstrap_password) < 12:
            raise ServerConfigError("GWR bootstrap password must contain at least 12 characters")


def _ensure_local_bootstrap_human(runtime: GovernedWorkflowRuntime, config: ServerConfig) -> str | None:
    if not config.bootstrap_username:
        return None
    existing = runtime.db.one(
        "SELECT actor_id FROM human_credentials WHERE username=? AND status='ACTIVE'",
        (config.bootstrap_username,),
    )
    if existing:
        return existing["actor_id"]

    actor_id = runtime.governance.create_actor(
        "HUMAN",
        config.bootstrap_username,
        [],
        [],
        identity_metadata={"bootstrap": "local-server"},
    )
    runtime.auth.register_human(actor_id, config.bootstrap_username, config.bootstrap_password or "")
    return actor_id


def build_application(config: ServerConfig):
    runtime = GovernedWorkflowRuntime(
        str(config.domain_path),
        config.database_target,
        auth_secret=config.auth_secret,
        object_store_root=str(config.object_store_root),
        observability_path=str(config.observability_path),
    )
    _ensure_local_bootstrap_human(runtime, config)

    product_info = {
        "product": "Governed Workflow Runtime",
        "version": _runtime_version(),
        "build_sha": _git_head(config.repo_root),
        "domain_id": runtime.domain.domain_id,
        "backend": getattr(runtime.db, "backend_name", "unknown"),
        "server_mode": "canonical",
    }
    app = create_app(
        runtime,
        product_info=product_info,
        web_root=config.web_root,
        browser_cookie_secure=config.browser_cookie_secure,
    )

    @app.on_event("shutdown")
    def _close_runtime() -> None:
        runtime.close()

    return app


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Canonical GWF product server")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--check-config", action="store_true")
    return parser


def main() -> None:
    args = _parser().parse_args()
    try:
        config = ServerConfig.from_env(repo_root=args.repo_root, host=args.host, port=args.port)
    except (ServerConfigError, ValidationError, ValueError) as exc:
        raise SystemExit(f"GWF server configuration error: {exc}") from exc

    if args.check_config:
        print("GWF_SERVER_CONFIG=PASS")
        print(f"repo_root={config.repo_root}")
        print(f"domain={config.domain_path}")
        print(f"database={config.database_target}")
        print(f"web_root={config.web_root}")
        print(f"host={config.host}")
        print(f"port={config.port}")
        return

    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit("uvicorn is required by the canonical GWF server installation") from exc

    app = build_application(config)
    uvicorn.run(app, host=config.host, port=config.port, log_level="info")


if __name__ == "__main__":
    main()
