from __future__ import annotations

import json
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .errors import StaleVersion, ValidationError


class _GitHubHttpError(Exception):
    def __init__(self, status: int, body: str):
        super().__init__(f"GitHub HTTP {status}")
        self.status = status
        self.body = body


class GitHubRestAdapter:
    """Reference GitHub REST adapter for GitHubPluginService.

    The adapter receives a credential provider callback. It never persists the
    credential and asks the provider for a token at request time.
    """

    def __init__(
        self,
        token_provider: Callable[[], str],
        *,
        api_base: str = "https://api.github.com",
        api_version: str = "2026-03-10",
        timeout_seconds: float = 30.0,
    ):
        self._token_provider = token_provider
        self.api_base = api_base.rstrip("/")
        self.api_version = str(api_version).strip()
        if not self.api_version:
            raise ValidationError("GitHub api_version is required")
        self.timeout_seconds = float(timeout_seconds)

    @staticmethod
    def _repo_path(repository_full_name: str) -> str:
        parts = repository_full_name.split("/")
        if len(parts) != 2 or not all(parts):
            raise ValidationError("repository_full_name must be owner/name")
        return "/".join(quote(x, safe="") for x in parts)

    def _request(self, method: str, path: str, payload=None, query=None):
        token = str(self._token_provider() or "").strip()
        if not token:
            raise ValidationError("GitHub credential resolver returned no credential")
        url = self.api_base + path
        if query:
            url += "?" + urlencode(query)
        body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
        req = Request(
            url,
            data=body,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": self.api_version,
                "User-Agent": "gwr-github-plugin",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(req, timeout=self.timeout_seconds) as response:
                raw = response.read()
                if not raw:
                    return {}
                return json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            try:
                body_text = exc.read().decode("utf-8", errors="replace")
            except Exception:
                body_text = ""
            raise _GitHubHttpError(int(exc.code), body_text) from None
        except URLError as exc:
            raise ValidationError("GitHub connection failed", details={"reason": str(exc.reason)}) from None

    def get_repository_identity(self, repository_full_name: str) -> dict:
        repo = self._repo_path(repository_full_name)
        try:
            payload = self._request("GET", f"/repos/{repo}")
        except _GitHubHttpError as exc:
            raise ValidationError(
                "Unable to read GitHub repository identity",
                details={"status": exc.status},
            ) from None
        repository_id = payload.get("id")
        full_name = str(payload.get("full_name") or "").strip()
        if repository_id is None or not full_name:
            raise ValidationError("GitHub repository identity response is incomplete")
        return {"repository_id": repository_id, "full_name": full_name}

    def get_branch_head(self, repository_full_name: str, branch: str) -> str:
        repo = self._repo_path(repository_full_name)
        ref = quote(f"heads/{branch}", safe="/")
        try:
            payload = self._request("GET", f"/repos/{repo}/git/ref/{ref}")
        except _GitHubHttpError as exc:
            raise ValidationError(
                "Unable to read GitHub branch head",
                details={"status": exc.status, "branch": branch},
            ) from None
        sha = ((payload.get("object") or {}).get("sha") or "").strip()
        if not sha:
            raise ValidationError("GitHub branch response did not contain object.sha")
        return sha

    def get_file(self, repository_full_name: str, path: str, ref: str):
        import base64

        repo = self._repo_path(repository_full_name)
        encoded_path = quote(path, safe="/")
        try:
            payload = self._request(
                "GET",
                f"/repos/{repo}/contents/{encoded_path}",
                query={"ref": ref},
            )
        except _GitHubHttpError as exc:
            if exc.status == 404:
                return None
            raise ValidationError(
                "Unable to read GitHub file",
                details={"status": exc.status, "path": path, "ref": ref},
            ) from None
        if payload.get("type") != "file":
            raise ValidationError("GitHub path is not a file", details={"path": path, "type": payload.get("type")})
        encoded = str(payload.get("content") or "").replace("\n", "")
        try:
            content = base64.b64decode(encoded).decode("utf-8")
        except Exception:
            raise ValidationError("GitHub file is not valid UTF-8 text", details={"path": path}) from None
        return {"sha": payload.get("sha"), "content": content}

    def get_commit(self, repository_full_name: str, commit_sha: str):
        repo = self._repo_path(repository_full_name)
        try:
            payload = self._request("GET", f"/repos/{repo}/git/commits/{quote(commit_sha, safe='')}")
        except _GitHubHttpError as exc:
            raise ValidationError(
                "Unable to read GitHub commit",
                details={"status": exc.status, "commit_sha": commit_sha},
            ) from None
        return {
            "sha": payload.get("sha"),
            "parents": [x.get("sha") for x in payload.get("parents", []) if x.get("sha")],
            "tree_sha": ((payload.get("tree") or {}).get("sha")),
        }

    def _base_tree(self, repository_full_name: str, expected_head_sha: str):
        repo = self._repo_path(repository_full_name)
        try:
            commit = self._request("GET", f"/repos/{repo}/git/commits/{quote(expected_head_sha, safe='')}")
        except _GitHubHttpError as exc:
            raise ValidationError(
                "Unable to read GitHub base commit",
                details={"status": exc.status, "expected_head_sha": expected_head_sha},
            ) from None
        tree_sha = ((commit.get("tree") or {}).get("sha") or "").strip()
        if not tree_sha:
            raise ValidationError("GitHub base commit has no tree SHA")
        try:
            tree = self._request(
                "GET",
                f"/repos/{repo}/git/trees/{quote(tree_sha, safe='')}",
                query={"recursive": "1"},
            )
        except _GitHubHttpError as exc:
            raise ValidationError(
                "Unable to read GitHub base tree",
                details={"status": exc.status, "tree_sha": tree_sha},
            ) from None
        entries = {x.get("path"): x for x in tree.get("tree", []) if x.get("path")}
        return tree_sha, entries, bool(tree.get("truncated"))

    def commit_files(
        self,
        repository_full_name: str,
        branch: str,
        expected_head_sha: str,
        message: str,
        changes: list[dict],
    ):
        current = self.get_branch_head(repository_full_name, branch)
        if current != expected_head_sha:
            raise StaleVersion(
                "GitHub branch moved before provider commit",
                details={"expected": expected_head_sha, "observed": current},
            )

        repo = self._repo_path(repository_full_name)
        base_tree_sha, base_entries, truncated = self._base_tree(repository_full_name, expected_head_sha)
        tree_items = []
        for change in changes:
            path = change["path"]
            operation = change["operation"]
            existing = base_entries.get(path)
            if operation in {"UPDATE", "DELETE"}:
                if existing is None:
                    if truncated:
                        raise ValidationError(
                            "GitHub base tree is truncated; cannot safely resolve existing file mode",
                            details={"path": path},
                        )
                    raise StaleVersion("GitHub path disappeared before commit", details={"path": path})
                if existing.get("type") != "blob":
                    raise ValidationError("Only blob files can be updated/deleted", details={"path": path})
                mode = existing.get("mode") or "100644"
            else:
                mode = "100644"

            if operation == "DELETE":
                tree_items.append({"path": path, "mode": mode, "type": "blob", "sha": None})
                continue

            try:
                blob = self._request(
                    "POST",
                    f"/repos/{repo}/git/blobs",
                    {"content": change["content"], "encoding": "utf-8"},
                )
            except _GitHubHttpError as exc:
                raise ValidationError(
                    "GitHub blob creation failed",
                    details={"status": exc.status, "path": path},
                ) from None
            blob_sha = str(blob.get("sha") or "")
            if not blob_sha:
                raise ValidationError("GitHub blob creation returned no SHA", details={"path": path})
            tree_items.append({"path": path, "mode": mode, "type": "blob", "sha": blob_sha})

        try:
            tree = self._request(
                "POST",
                f"/repos/{repo}/git/trees",
                {"base_tree": base_tree_sha, "tree": tree_items},
            )
            tree_sha = str(tree.get("sha") or "")
            commit = self._request(
                "POST",
                f"/repos/{repo}/git/commits",
                {"message": message, "tree": tree_sha, "parents": [expected_head_sha]},
            )
            commit_sha = str(commit.get("sha") or "")
            if not tree_sha or not commit_sha:
                raise ValidationError("GitHub commit construction returned incomplete SHA data")
            ref = quote(f"heads/{branch}", safe="/")
            try:
                self._request(
                    "PATCH",
                    f"/repos/{repo}/git/refs/{ref}",
                    {"sha": commit_sha, "force": False},
                )
            except _GitHubHttpError as exc:
                if exc.status in {409, 422}:
                    raise StaleVersion(
                        "GitHub rejected non-fast-forward ref update",
                        details={"status": exc.status, "expected_head_sha": expected_head_sha},
                    ) from None
                raise ValidationError(
                    "GitHub ref update failed",
                    details={"status": exc.status, "branch": branch},
                ) from None
        except _GitHubHttpError as exc:
            raise ValidationError(
                "GitHub commit operation failed",
                details={"status": exc.status},
            ) from None

        return {"commit_sha": commit_sha, "parent_sha": expected_head_sha}
