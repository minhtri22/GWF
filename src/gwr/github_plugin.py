from __future__ import annotations

import hashlib
import re
from typing import Any

from .errors import AuthorityDenied, InvalidTransition, NotFound, StaleVersion, ValidationError
from .utils import canonical_json, content_hash, parse_json, uid, utcnow


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _git_sha(value: str, field: str) -> str:
    text = str(value or "").strip().lower()
    if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", text):
        raise ValidationError(
            f"{field} must be a full 40-hex SHA-1 or 64-hex SHA-256",
            details={"field": field},
        )
    return text


class GitHubPluginService:
    """SHA-safe GitHub write path.

    Provider credentials live outside GWF. A host attaches a GitHub adapter to an
    opaque PluginConnection. Every write is optimistic-concurrency controlled by
    branch SHA and, for updates/deletes, file blob SHA. A commit is not considered
    QA-complete until the remote commit, branch head and changed file contents are
    fetched again and verified.
    """

    def __init__(self, db, governance, tenancy, project_governance, plugins):
        self.db = db
        self.gov = governance
        self.tenancy = tenancy
        self.projects = project_governance
        self.plugins = plugins

    def _require_use(self, project_id: str, actor_id: str) -> None:
        self.projects.require_mutable(project_id)
        scope = self.tenancy.scope_for_project(project_id)
        if scope:
            self.tenancy.require_project_access(actor_id, project_id, "USE")
        elif actor_id != "SYSTEM":
            self.gov.authorize(actor_id, "EXECUTE", {"project_id": project_id, "action": "GITHUB_WRITE"})

    def _require_manage(self, project_id: str, actor_id: str) -> None:
        self.projects.require_mutable(project_id)
        actor = self.gov._actor(actor_id)
        if actor["actor_type"] != "HUMAN":
            raise AuthorityDenied("Repository bindings must be managed by a human actor")
        scope = self.tenancy.scope_for_project(project_id)
        if scope:
            self.tenancy.require_project_access(actor_id, project_id, "MANAGE_MEMBERS")
            return
        self.gov.authorize(actor_id, "PROPOSE", {"project_id": project_id, "action": "MANAGE_GITHUB_BINDING"})

    @staticmethod
    def _branch_allowed(branch: str, allowed: list[str]) -> bool:
        for item in allowed:
            if item == branch:
                return True
            if item.endswith("*") and branch.startswith(item[:-1]):
                return True
        return False

    def bind_repository(
        self,
        project_id: str,
        connection_id: str,
        repository_full_name: str,
        default_branch: str,
        actor_id: str,
        *,
        write_policy: str = "FEATURE_BRANCH_ONLY",
        allowed_branches: list[str] | None = None,
    ) -> str:
        self._require_manage(project_id, actor_id)
        connection = self.plugins.get(connection_id)
        if connection["project_id"] != project_id or connection["plugin_type"] != "github":
            raise ValidationError("GitHub connection does not belong to project")
        caps = set(connection["capabilities"])
        if "REPO_READ" not in caps or "CONTENT_WRITE" not in caps:
            raise ValidationError("GitHub repository binding requires REPO_READ and CONTENT_WRITE capabilities")
        repository_full_name = repository_full_name.strip()
        if repository_full_name.count("/") != 1 or any(not x for x in repository_full_name.split("/")):
            raise ValidationError("repository_full_name must be owner/name")
        write_policy = write_policy.upper()
        if write_policy not in {"FEATURE_BRANCH_ONLY", "DIRECT"}:
            raise ValidationError("write_policy must be FEATURE_BRANCH_ONLY or DIRECT")
        allowed = sorted(set(allowed_branches or ["feature/*", "fix/*", "docs/*"]))
        if not allowed:
            raise ValidationError("At least one allowed branch pattern is required")
        binding_id = uid("ghrepo")
        with self.db.tx():
            self.db.conn.execute(
                "INSERT INTO github_repository_bindings VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    binding_id,
                    project_id,
                    connection_id,
                    repository_full_name,
                    default_branch,
                    write_policy,
                    canonical_json(allowed),
                    actor_id,
                    utcnow(),
                ),
            )
            self.gov.append_audit(
                project_id,
                actor_id,
                "GITHUB_REPOSITORY_BOUND",
                "GitHubRepositoryBinding",
                binding_id,
                metadata={
                    "repository_full_name": repository_full_name,
                    "default_branch": default_branch,
                    "write_policy": write_policy,
                    "allowed_branches": allowed,
                },
            )
        return binding_id

    def binding(self, binding_id: str) -> dict[str, Any]:
        row = self.db.one("SELECT * FROM github_repository_bindings WHERE binding_id=?", (binding_id,))
        if not row:
            raise NotFound("GitHub repository binding not found")
        item = dict(row)
        item["allowed_branches"] = parse_json(item["allowed_branches"], [])
        return item

    @staticmethod
    def _normalize_changes(changes: list[dict[str, Any]], *, include_content: bool) -> list[dict[str, Any]]:
        if not changes:
            raise ValidationError("At least one GitHub file change is required")
        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        for raw in changes:
            path = str(raw.get("path") or "").strip().replace("\\", "/")
            if not path or path.startswith("/") or ".." in path.split("/"):
                raise ValidationError("Unsafe repository path", details={"path": path})
            if path in seen:
                raise ValidationError("Duplicate repository path in change set", details={"path": path})
            seen.add(path)
            operation = str(raw.get("operation") or "").upper()
            if operation not in {"CREATE", "UPDATE", "DELETE"}:
                raise ValidationError("operation must be CREATE, UPDATE or DELETE", details={"path": path})
            expected_blob_sha = raw.get("expected_blob_sha")
            if operation in {"UPDATE", "DELETE"} and not expected_blob_sha:
                raise ValidationError(
                    "UPDATE/DELETE requires expected_blob_sha",
                    details={"path": path},
                )
            if operation == "CREATE" and expected_blob_sha:
                raise ValidationError("CREATE must not supply expected_blob_sha", details={"path": path})
            if expected_blob_sha:
                expected_blob_sha = _git_sha(expected_blob_sha, f"expected_blob_sha:{path}")
            item: dict[str, Any] = {
                "path": path,
                "operation": operation,
                "expected_blob_sha": expected_blob_sha,
            }
            if operation != "DELETE":
                content = raw.get("content")
                if not isinstance(content, str):
                    raise ValidationError("CREATE/UPDATE requires UTF-8 text content", details={"path": path})
                item["content_sha256"] = _sha256_text(content)
                if include_content:
                    item["content"] = content
            else:
                item["content_sha256"] = None
            normalized.append(item)
        return normalized

    def prepare_change_set(
        self,
        project_id: str,
        binding_id: str,
        branch: str,
        expected_head_sha: str,
        changes: list[dict[str, Any]],
        commit_message: str,
        actor_id: str,
    ) -> str:
        self._require_use(project_id, actor_id)
        binding = self.binding(binding_id)
        if binding["project_id"] != project_id:
            raise ValidationError("Repository binding does not belong to project")
        branch = branch.strip()
        if not branch:
            raise ValidationError("branch is required")
        if not self._branch_allowed(branch, binding["allowed_branches"]):
            raise AuthorityDenied(
                "Branch is outside repository binding allowlist",
                details={"branch": branch, "allowed": binding["allowed_branches"]},
            )
        if branch == binding["default_branch"]:
            if binding["write_policy"] != "DIRECT":
                raise AuthorityDenied("Direct writes to the default branch are disabled")
            actor = self.gov._actor(actor_id)
            if actor["actor_type"] != "HUMAN":
                raise AuthorityDenied("Direct writes to the default branch require a human actor")
        expected_head_sha = _git_sha(expected_head_sha, "expected_head_sha")
        if not commit_message.strip():
            raise ValidationError("commit_message is required")
        manifest = self._normalize_changes(changes, include_content=False)
        change_set_id = uid("ghchg")
        now = utcnow()
        with self.db.tx():
            self.db.conn.execute(
                "INSERT INTO github_change_sets VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    change_set_id,
                    project_id,
                    binding_id,
                    branch,
                    expected_head_sha,
                    canonical_json(manifest),
                    content_hash(manifest),
                    commit_message.strip(),
                    "PREPARED",
                    actor_id,
                    now,
                    None,
                    None,
                ),
            )
            self.gov.append_audit(
                project_id,
                actor_id,
                "GITHUB_CHANGESET_PREPARED",
                "GitHubChangeSet",
                change_set_id,
                metadata={
                    "repository_full_name": binding["repository_full_name"],
                    "branch": branch,
                    "expected_head_sha": expected_head_sha,
                    "manifest_hash": content_hash(manifest),
                },
            )
        return change_set_id

    def _record_check(
        self,
        change_set_id: str,
        stage: str,
        status: str,
        *,
        expected_sha: str | None = None,
        observed_sha: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> str:
        check_id = uid("ghcheck")
        self.db.conn.execute(
            "INSERT INTO github_sha_checks VALUES(?,?,?,?,?,?,?,?)",
            (
                check_id,
                change_set_id,
                stage,
                expected_sha,
                observed_sha,
                status,
                canonical_json(details or {}),
                utcnow(),
            ),
        )
        return check_id

    def _row(self, change_set_id: str):
        row = self.db.one("SELECT * FROM github_change_sets WHERE change_set_id=?", (change_set_id,))
        if not row:
            raise NotFound("GitHub change set not found")
        return row

    def _mark_stale(self, change_set_id: str) -> None:
        self.db.conn.execute(
            "UPDATE github_change_sets SET status='STALE' WHERE change_set_id=?",
            (change_set_id,),
        )
        self.db.conn.commit()

    def preflight(self, change_set_id: str, actor_id: str) -> dict[str, Any]:
        row = self._row(change_set_id)
        self._require_use(row["project_id"], actor_id)
        if row["status"] != "PREPARED":
            raise InvalidTransition("SHA preflight requires PREPARED change set")
        binding = self.binding(row["binding_id"])
        adapter = self.plugins.adapter(binding["connection_id"], capability="REPO_READ")
        observed_head = adapter.get_branch_head(binding["repository_full_name"], row["branch"])
        with self.db.tx():
            self._record_check(
                change_set_id,
                "BRANCH_HEAD_PRE",
                "PASS" if observed_head == row["expected_head_sha"] else "FAIL",
                expected_sha=row["expected_head_sha"],
                observed_sha=observed_head,
                details={"branch": row["branch"]},
            )
        if observed_head != row["expected_head_sha"]:
            self._mark_stale(change_set_id)
            raise StaleVersion(
                "GitHub branch head changed before commit",
                details={"expected": row["expected_head_sha"], "observed": observed_head},
            )

        manifest = parse_json(row["manifest_json"], [])
        file_results = []
        for item in manifest:
            remote = adapter.get_file(binding["repository_full_name"], item["path"], row["expected_head_sha"])
            observed_blob = remote.get("sha") if remote else None
            if item["operation"] == "CREATE":
                ok = remote is None
                expected_blob = None
            else:
                expected_blob = item["expected_blob_sha"]
                ok = remote is not None and observed_blob == expected_blob
            with self.db.tx():
                self._record_check(
                    change_set_id,
                    "FILE_BLOB_PRE",
                    "PASS" if ok else "FAIL",
                    expected_sha=expected_blob,
                    observed_sha=observed_blob,
                    details={"path": item["path"], "operation": item["operation"]},
                )
            file_results.append({"path": item["path"], "pass": ok, "observed_blob_sha": observed_blob})
            if not ok:
                self._mark_stale(change_set_id)
                raise StaleVersion(
                    "GitHub file SHA changed before commit",
                    details={
                        "path": item["path"],
                        "expected": expected_blob,
                        "observed": observed_blob,
                        "operation": item["operation"],
                    },
                )

        self.db.conn.execute(
            "UPDATE github_change_sets SET status='PREFLIGHT_PASS' WHERE change_set_id=?",
            (change_set_id,),
        )
        self.db.conn.commit()
        return {
            "change_set_id": change_set_id,
            "status": "PREFLIGHT_PASS",
            "expected_head_sha": row["expected_head_sha"],
            "observed_head_sha": observed_head,
            "files": file_results,
        }

    def execute(self, change_set_id: str, changes: list[dict[str, Any]], actor_id: str) -> dict[str, Any]:
        row = self._row(change_set_id)
        self._require_use(row["project_id"], actor_id)
        if row["status"] not in {"PREPARED", "PREFLIGHT_PASS"}:
            raise InvalidTransition("Change set is not executable")
        supplied = self._normalize_changes(changes, include_content=False)
        if content_hash(supplied) != row["manifest_hash"]:
            raise ValidationError("Supplied changes do not match frozen change-set manifest")

        if row["status"] == "PREPARED":
            self.preflight(change_set_id, actor_id)
            row = self._row(change_set_id)

        binding = self.binding(row["binding_id"])
        adapter = self.plugins.adapter(binding["connection_id"], capability="CONTENT_WRITE")

        # Close the race between an earlier preflight and provider write as much as
        # possible. The adapter contract must additionally enforce expected_head_sha
        # atomically when creating the commit/ref update.
        immediate_head = adapter.get_branch_head(binding["repository_full_name"], row["branch"])
        with self.db.tx():
            self._record_check(
                change_set_id,
                "BRANCH_HEAD_IMMEDIATE_PRE",
                "PASS" if immediate_head == row["expected_head_sha"] else "FAIL",
                expected_sha=row["expected_head_sha"],
                observed_sha=immediate_head,
                details={"branch": row["branch"]},
            )
        if immediate_head != row["expected_head_sha"]:
            self._mark_stale(change_set_id)
            raise StaleVersion(
                "GitHub branch head changed after preflight",
                details={"expected": row["expected_head_sha"], "observed": immediate_head},
            )

        payload_changes = self._normalize_changes(changes, include_content=True)
        try:
            result = adapter.commit_files(
                binding["repository_full_name"],
                row["branch"],
                row["expected_head_sha"],
                row["commit_message"],
                payload_changes,
            )
        except StaleVersion as exc:
            observed = None
            try:
                observed = adapter.get_branch_head(binding["repository_full_name"], row["branch"])
            except Exception:
                observed = None
            with self.db.tx():
                self._record_check(
                    change_set_id,
                    "PROVIDER_EXPECTED_HEAD",
                    "FAIL",
                    expected_sha=row["expected_head_sha"],
                    observed_sha=observed,
                    details={"provider_error": str(exc)},
                )
                self.db.conn.execute(
                    "UPDATE github_change_sets SET status='STALE' WHERE change_set_id=?",
                    (change_set_id,),
                )
            raise
        commit_sha = _git_sha(result.get("commit_sha"), "commit_sha")
        parent_sha = _git_sha(result.get("parent_sha"), "parent_sha")
        if parent_sha != row["expected_head_sha"]:
            with self.db.tx():
                self._record_check(
                    change_set_id,
                    "COMMIT_PARENT_POST",
                    "FAIL",
                    expected_sha=row["expected_head_sha"],
                    observed_sha=parent_sha or None,
                    details={"commit_sha": commit_sha},
                )
                self.db.conn.execute(
                    "UPDATE github_change_sets SET status='VERIFICATION_FAILED',committed_sha=? WHERE change_set_id=?",
                    (commit_sha, change_set_id),
                )
            raise StaleVersion(
                "Committed parent SHA does not match frozen expected head",
                details={"expected": row["expected_head_sha"], "observed": parent_sha, "commit_sha": commit_sha},
            )

        self.db.conn.execute(
            "UPDATE github_change_sets SET status='COMMITTED',committed_sha=? WHERE change_set_id=?",
            (commit_sha, change_set_id),
        )
        self.db.conn.commit()
        return self.verify(change_set_id, actor_id)

    def verify(self, change_set_id: str, actor_id: str) -> dict[str, Any]:
        row = self._row(change_set_id)
        self._require_use(row["project_id"], actor_id)
        if row["status"] != "COMMITTED" or not row["committed_sha"]:
            raise InvalidTransition("Post-commit verification requires COMMITTED change set")
        binding = self.binding(row["binding_id"])
        adapter = self.plugins.adapter(binding["connection_id"], capability="REPO_READ")
        commit = adapter.get_commit(binding["repository_full_name"], row["committed_sha"])
        parents = list(commit.get("parents") or [])
        if not parents and commit.get("parent_sha"):
            parents = [commit["parent_sha"]]
        parent_observed = parents[0] if parents else None
        parent_ok = parent_observed == row["expected_head_sha"]
        with self.db.tx():
            self._record_check(
                change_set_id,
                "COMMIT_PARENT_POST",
                "PASS" if parent_ok else "FAIL",
                expected_sha=row["expected_head_sha"],
                observed_sha=parent_observed,
                details={"commit_sha": row["committed_sha"]},
            )
        if not parent_ok:
            self.db.conn.execute(
                "UPDATE github_change_sets SET status='VERIFICATION_FAILED' WHERE change_set_id=?",
                (change_set_id,),
            )
            self.db.conn.commit()
            raise StaleVersion("Post-commit parent SHA verification failed")

        branch_head = adapter.get_branch_head(binding["repository_full_name"], row["branch"])
        head_ok = branch_head == row["committed_sha"]
        with self.db.tx():
            self._record_check(
                change_set_id,
                "BRANCH_HEAD_POST",
                "PASS" if head_ok else "FAIL",
                expected_sha=row["committed_sha"],
                observed_sha=branch_head,
                details={"branch": row["branch"]},
            )
        if not head_ok:
            self.db.conn.execute(
                "UPDATE github_change_sets SET status='VERIFICATION_FAILED' WHERE change_set_id=?",
                (change_set_id,),
            )
            self.db.conn.commit()
            raise StaleVersion("Branch head does not equal committed SHA after write")

        manifest = parse_json(row["manifest_json"], [])
        for item in manifest:
            remote = adapter.get_file(binding["repository_full_name"], item["path"], row["committed_sha"])
            if item["operation"] == "DELETE":
                ok = remote is None
                observed_content_sha = None
            else:
                content = remote.get("content") if remote else None
                observed_content_sha = _sha256_text(content) if isinstance(content, str) else None
                ok = remote is not None and observed_content_sha == item["content_sha256"]
            with self.db.tx():
                self._record_check(
                    change_set_id,
                    "FILE_CONTENT_POST",
                    "PASS" if ok else "FAIL",
                    expected_sha=item["content_sha256"],
                    observed_sha=observed_content_sha,
                    details={"path": item["path"], "operation": item["operation"]},
                )
            if not ok:
                self.db.conn.execute(
                    "UPDATE github_change_sets SET status='VERIFICATION_FAILED' WHERE change_set_id=?",
                    (change_set_id,),
                )
                self.db.conn.commit()
                raise ValidationError(
                    "Post-commit file content verification failed",
                    details={"path": item["path"], "commit_sha": row["committed_sha"]},
                )

        now = utcnow()
        with self.db.tx():
            self.db.conn.execute(
                "UPDATE github_change_sets SET status='VERIFIED',verified_at=? WHERE change_set_id=?",
                (now, change_set_id),
            )
            self.gov.append_audit(
                row["project_id"],
                actor_id,
                "GITHUB_CHANGESET_VERIFIED",
                "GitHubChangeSet",
                change_set_id,
                metadata={
                    "repository_full_name": binding["repository_full_name"],
                    "branch": row["branch"],
                    "expected_head_sha": row["expected_head_sha"],
                    "commit_sha": row["committed_sha"],
                    "manifest_hash": row["manifest_hash"],
                },
            )
        return self.inspect(change_set_id)

    def inspect(self, change_set_id: str) -> dict[str, Any]:
        row = self._row(change_set_id)
        item = dict(row)
        item["manifest"] = parse_json(item.pop("manifest_json"), [])
        item["checks"] = []
        for check in self.db.all(
            "SELECT * FROM github_sha_checks WHERE change_set_id=? ORDER BY created_at,check_id",
            (change_set_id,),
        ):
            c = dict(check)
            c["details"] = parse_json(c.pop("details_json"), {})
            item["checks"].append(c)
        item["qa_complete"] = item["status"] == "VERIFIED"
        return item
