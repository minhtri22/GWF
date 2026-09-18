from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from copy import deepcopy
from pathlib import Path

from gwr.errors import StaleVersion, ValidationError
from gwr.runtime import GovernedWorkflowRuntime


ROOT = Path(__file__).resolve().parents[1]


def blob_sha(content: str) -> str:
    return hashlib.sha1(content.encode("utf-8")).hexdigest()


class GateGitHubAdapter:
    def __init__(self):
        self.branch_heads = {"feature/qa": "a" * 40}
        self.snapshots = {"a" * 40: {"README.md": "before\n"}}
        self.commits = {}
        self.commit_calls = 0
        self.race_on_commit = False

    def get_branch_head(self, repository_full_name, branch):
        return self.branch_heads[branch]

    def get_file(self, repository_full_name, path, ref):
        files = self.snapshots.get(ref, {})
        if path not in files:
            return None
        value = files[path]
        return {"sha": blob_sha(value), "content": value}

    def commit_files(self, repository_full_name, branch, expected_head_sha, message, changes):
        if self.race_on_commit:
            raced = "c" * 40
            self.snapshots[raced] = deepcopy(self.snapshots[self.branch_heads[branch]])
            self.branch_heads[branch] = raced
            self.race_on_commit = False
        current = self.branch_heads[branch]
        if current != expected_head_sha:
            raise StaleVersion("provider stale head", details={"expected": expected_head_sha, "observed": current})
        files = deepcopy(self.snapshots[current])
        for change in changes:
            if change["operation"] == "DELETE":
                files.pop(change["path"], None)
            else:
                files[change["path"]] = change["content"]
        commit_sha = hashlib.sha1((expected_head_sha + message + repr(sorted(files.items()))).encode("utf-8")).hexdigest()
        self.snapshots[commit_sha] = files
        self.commits[commit_sha] = {"parents": [expected_head_sha]}
        self.branch_heads[branch] = commit_sha
        self.commit_calls += 1
        return {"commit_sha": commit_sha, "parent_sha": expected_head_sha}

    def get_commit(self, repository_full_name, commit_sha):
        return self.commits[commit_sha]


def add(checks, name, passed, **metadata):
    checks.append({"name": name, "pass": bool(passed), **metadata})


def make_scoped_project(rt, label):
    human = rt.governance.create_actor("HUMAN", f"{label}-owner", ["human_approver"], [])
    tenant = rt.tenancy.create_tenant(f"{label} tenant", human)
    workspace = rt.tenancy.create_workspace(tenant, f"{label} workspace", human)
    project = rt.create_scoped_project(f"{label} project", tenant, workspace, human)
    agent = rt.governance.create_actor("AGENT", f"{label}-agent", ["research_lead"], [])
    rt.tenancy.add_project_member(project, agent, "RESEARCHER", human)
    return project, human, agent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    checks = []

    with tempfile.TemporaryDirectory() as td:
        rt = GovernedWorkflowRuntime(
            str(ROOT / "domains" / "research.workflow.yaml"),
            str(Path(td) / "qa-v084.db"),
        )
        backend = rt.db.backend_name
        tables = set(rt.db.list_tables())
        required = {
            "plugin_connections",
            "github_repository_bindings",
            "github_change_sets",
            "github_sha_checks",
        }
        add(checks, "v084_tables", required.issubset(tables), missing=sorted(required - tables))
        add(
            checks,
            "v084_migration",
            "0007_v084_github_plugin_sha_qa" in rt.db.migrations.status()["applied"],
        )

        project, human, agent = make_scoped_project(rt, "qa-v084")
        default_recovery = rt.agent_protocol.resolve_recovery_config(project, "phase_09_main_experiment")
        rt.agent_protocol.set_project_defaults(project, human, recovery_mode="HUMAN_APPROVE", retry_budget=2)
        manual_recovery = rt.agent_protocol.resolve_recovery_config(project, "phase_09_main_experiment")
        rt.agent_protocol.set_project_defaults(project, human, recovery_mode="AUTO", retry_budget=2)
        auto_recovery = rt.agent_protocol.resolve_recovery_config(project, "phase_09_main_experiment")
        add(
            checks,
            "recovery_modes_configurable",
            default_recovery["recovery_mode"] == "AUTO"
            and manual_recovery["recovery_mode"] == "HUMAN_APPROVE"
            and auto_recovery["recovery_mode"] == "AUTO",
        )

        secret_blocked = False
        try:
            rt.plugins.create_connection(
                project,
                "github",
                "safe-ref",
                ["REPO_READ"],
                human,
                metadata={"access_token": "must-not-persist"},
            )
        except ValidationError:
            secret_blocked = True
        add(checks, "plugin_secret_persistence_blocked", secret_blocked)

        connection = rt.plugins.create_connection(
            project,
            "github",
            "github-opaque-qa",
            ["REPO_READ", "CONTENT_WRITE"],
            human,
            metadata={"account_label": "qa"},
        )

        workflow_capability_blocked = False
        try:
            provisional_binding = rt.github.bind_repository(
                project,
                connection,
                "example/workflow-policy",
                "main",
                human,
                allowed_branches=["feature/*"],
            )
            rt.github.prepare_change_set(
                project,
                provisional_binding,
                "feature/qa",
                "a" * 40,
                [{"path": ".github/workflows/ci.yml", "operation": "CREATE", "content": "name: ci\n"}],
                "ci: capability check",
                agent,
            )
        except Exception as exc:
            workflow_capability_blocked = "WORKFLOW_WRITE" in str(exc)
        add(checks, "workflow_write_capability_enforced", workflow_capability_blocked)

        adapter = GateGitHubAdapter()
        rt.plugins.attach_runtime_adapter(connection, adapter)
        binding = rt.github.bind_repository(
            project,
            connection,
            "example/research",
            "main",
            human,
            allowed_branches=["feature/*"],
        )

        base = adapter.get_branch_head("example/research", "feature/qa")
        before = adapter.get_file("example/research", "README.md", base)
        changes = [{
            "path": "README.md",
            "operation": "UPDATE",
            "expected_blob_sha": before["sha"],
            "content": "after\n",
        }]
        change_set = rt.github.prepare_change_set(
            project,
            binding,
            "feature/qa",
            base,
            changes,
            "docs: SHA-safe QA",
            agent,
        )
        verified = rt.github.execute(change_set, changes, agent)
        stages = {x["stage"]: x["status"] for x in verified["checks"]}
        add(
            checks,
            "github_sha_safe_commit",
            verified["status"] == "VERIFIED"
            and verified["qa_complete"] is True
            and adapter.commit_calls == 1
            and all(stages.get(stage) == "PASS" for stage in (
                "BRANCH_HEAD_PRE",
                "FILE_BLOB_PRE",
                "BRANCH_HEAD_IMMEDIATE_PRE",
                "COMMIT_PARENT_POST",
                "BRANCH_HEAD_POST",
                "FILE_CONTENT_POST",
            )),
            commit_sha=verified["committed_sha"],
        )

        # New adapter/binding state for provider-side race: preflight passes, provider
        # changes HEAD immediately before atomic ref update.
        race_adapter = GateGitHubAdapter()
        rt.plugins.attach_runtime_adapter(connection, race_adapter)
        race_base = race_adapter.get_branch_head("example/research", "feature/qa")
        race_before = race_adapter.get_file("example/research", "README.md", race_base)
        race_changes = [{
            "path": "README.md",
            "operation": "UPDATE",
            "expected_blob_sha": race_before["sha"],
            "content": "race\n",
        }]
        race_set = rt.github.prepare_change_set(
            project,
            binding,
            "feature/qa",
            race_base,
            race_changes,
            "docs: race QA",
            agent,
        )
        race_adapter.race_on_commit = True
        stale_blocked = False
        try:
            rt.github.execute(race_set, race_changes, agent)
        except StaleVersion:
            stale_blocked = True
        race_view = rt.github.inspect(race_set)
        add(
            checks,
            "provider_race_blocks_write",
            stale_blocked
            and race_view["status"] == "STALE"
            and race_adapter.commit_calls == 0
            and any(x["stage"] == "PROVIDER_EXPECTED_HEAD" and x["status"] == "FAIL" for x in race_view["checks"]),
        )

        rt.close()

    errors = [x for x in checks if not x["pass"]]
    result = {
        "version": "0.8.4",
        "backend": backend,
        "status": "PASS" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
