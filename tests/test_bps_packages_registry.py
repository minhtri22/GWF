from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from gwr.api import create_app
from gwr.auth import HumanAuthService
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import canonical_json, uid


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"
PASSWORD = "packages-browser-password"


def _runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "example.workflow.yaml"),
        str(tmp_path / "bps-packages.db"),
        auth_secret="p" * 64,
        object_store_root=tmp_path / "objects",
        observability_path=tmp_path / "events.jsonl",
    )
    owner = rt.governance.create_actor("HUMAN", "packages-owner", [], [])
    outsider = rt.governance.create_actor("HUMAN", "packages-outsider", [], [])
    rt.auth.register_human(owner, "packages-owner", PASSWORD)

    tenant = rt.tenancy.create_tenant(
        "Packages Tenant", owner, tenant_id="tenant_packages"
    )
    workspace = rt.tenancy.create_workspace(
        tenant, "Packages Workspace", owner, workspace_id="workspace_packages"
    )
    hidden_tenant = rt.tenancy.create_tenant(
        "Hidden Packages Tenant",
        outsider,
        tenant_id="tenant_packages_hidden",
    )
    hidden_workspace = rt.tenancy.create_workspace(
        hidden_tenant,
        "Hidden Packages Workspace",
        outsider,
        workspace_id="workspace_packages_hidden",
    )
    return (
        rt,
        owner,
        outsider,
        tenant,
        workspace,
        hidden_tenant,
        hidden_workspace,
    )


def _app(rt):
    return create_app(
        rt,
        product_info={
            "product": "Governed Workflow Runtime",
            "version": "test-version",
            "build_sha": "packages-build-sha",
            "domain_id": rt.domain.domain_id,
            "backend": getattr(rt.db, "backend_name", "unknown"),
            "server_mode": "canonical",
        },
        web_root=WEB,
    )


def _login(client):
    response = client.post(
        "/browser/auth/login",
        json={"username": "packages-owner", "password": PASSWORD},
    )
    assert response.status_code == 200


def _skill(rt, actor, skill_id):
    package = rt.agent_protocol.create_skill_package(
        skill_id, skill_id.replace("-", " ").title(), actor,
        description=f"{skill_id} description",
    )
    revision = rt.agent_protocol.add_skill_revision(
        package,
        "1.0.0",
        f"# {skill_id}\nPrivate skill body must not appear in registry list.",
        actor,
        tool_requirements=["python"],
        qa_contract={"requires_evidence": True},
    )
    row = rt.db.one(
        "SELECT content_hash FROM skill_revisions WHERE skill_revision_id=?",
        (revision,),
    )
    return package, revision, row["content_hash"]


def _bind_skill(rt, domain_id, workunit_type, revision, skill_hash):
    binding = "skillbind_" + uid("b")
    rt.db.conn.execute(
        "INSERT INTO domain_skill_bindings VALUES(?,?,?,?,?,?,?,?)",
        (
            binding,
            domain_id,
            workunit_type,
            revision,
            skill_hash,
            canonical_json(["python"]),
            canonical_json({"requires_evidence": True}),
            "2026-09-26T11:00:00+00:00",
        ),
    )
    rt.db.conn.commit()
    return binding


def _phase_protocol(
    rt,
    project,
    revision,
    skill_hash,
    *,
    phase_execution_id,
    phase_id,
):
    orchestration_id = "orch_" + phase_execution_id
    rt.db.conn.execute(
        "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            orchestration_id,
            project,
            rt.domain.domain_id,
            "RUNNING",
            phase_id,
            0,
            None,
            0,
            "2026-09-26T11:10:00+00:00",
            "2026-09-26T11:10:00+00:00",
            None,
            "{}",
        ),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_executions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            phase_execution_id,
            orchestration_id,
            phase_id,
            1,
            0,
            None,
            None,
            "RUNNING",
            None,
            None,
            None,
            "2026-09-26T11:10:01+00:00",
            None,
            "{}",
        ),
    )
    protocol_id = "protocol_" + phase_execution_id
    rt.db.conn.execute(
        "INSERT INTO phase_execution_protocols VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            protocol_id,
            phase_execution_id,
            project,
            revision,
            skill_hash,
            "AUTO",
            "EXECUTE",
            "RUNNING",
            2,
            0,
            "2026-09-26T11:10:02+00:00",
            "2026-09-26T11:10:02+00:00",
        ),
    )
    rt.db.conn.commit()
    return protocol_id, orchestration_id


def _seed(rt, owner, outsider, tenant, workspace, hidden_tenant, hidden_workspace):
    yaml_text = (ROOT / "domains" / "example.workflow.yaml").read_text(
        encoding="utf-8"
    )
    domain_id = rt.domain.domain_id

    package = rt.domains.create_package(
        tenant, domain_id, "Visible Example Domain", owner
    )
    rev1 = rt.domains.add_revision(package, yaml_text, owner)
    rt.domains.publish_revision(rev1, owner)
    project = rt.create_scoped_project(
        "Visible Package Project",
        tenant,
        workspace,
        owner,
        project_id="project_packages",
        domain_revision_id=rev1,
    )
    rev2 = rt.domains.add_revision(package, yaml_text, owner)
    rt.domains.publish_revision(rev2, owner)
    rev3 = "domainrev_packages_draft"
    rt.db.conn.execute(
        "INSERT INTO domain_package_revisions VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (
            rev3,
            package,
            3,
            "draft-3",
            "domain_id: example.workflow\n",
            "draft-payload-hash",
            canonical_json({
                "ok": False,
                "errors": [{"code": "TEST_DRAFT", "message": "persisted draft"}],
                "warnings": [],
                "counts": {},
            }),
            "DRAFT",
            owner,
            "2026-09-26T11:05:00+00:00",
            None,
        ),
    )
    rt.db.conn.commit()

    hidden_package = rt.domains.create_package(
        hidden_tenant, domain_id, "Hidden Example Domain", outsider
    )
    hidden_rev = rt.domains.add_revision(
        hidden_package, yaml_text, outsider
    )
    rt.domains.publish_revision(hidden_rev, outsider)
    hidden_project = rt.create_scoped_project(
        "Hidden Package Project",
        hidden_tenant,
        hidden_workspace,
        outsider,
        project_id="project_packages_hidden",
        domain_revision_id=hidden_rev,
    )

    cfg_pkg, cfg_rev, cfg_hash = _skill(
        rt, owner, "configured-only-skill"
    )
    obs_pkg, obs_rev, obs_hash = _skill(
        rt, owner, "observed-only-skill"
    )
    both_pkg, both_rev, both_hash = _skill(
        rt, owner, "both-basis-skill"
    )
    orphan_pkg, orphan_rev, orphan_hash = _skill(
        rt, owner, "unreferenced-global-skill"
    )

    cfg_binding = _bind_skill(
        rt, domain_id, "configured_only_workunit", cfg_rev, cfg_hash
    )
    both_binding = _bind_skill(
        rt, domain_id, "both_basis_workunit", both_rev, both_hash
    )

    obs_protocol, obs_orch = _phase_protocol(
        rt,
        project,
        obs_rev,
        obs_hash,
        phase_execution_id="phase_packages_observed",
        phase_id="observed_only_workunit",
    )
    both_protocol, both_orch = _phase_protocol(
        rt,
        project,
        both_rev,
        both_hash,
        phase_execution_id="phase_packages_both",
        phase_id="both_basis_workunit",
    )
    hidden_protocol, hidden_orch = _phase_protocol(
        rt,
        hidden_project,
        obs_rev,
        obs_hash,
        phase_execution_id="phase_packages_hidden",
        phase_id="hidden_observed_workunit",
    )

    return {
        "domain_id": domain_id,
        "package": package,
        "rev1": rev1,
        "rev2": rev2,
        "rev3": rev3,
        "project": project,
        "hidden_package": hidden_package,
        "hidden_rev": hidden_rev,
        "hidden_project": hidden_project,
        "configured": {
            "package": cfg_pkg,
            "revision": cfg_rev,
            "hash": cfg_hash,
            "binding": cfg_binding,
        },
        "observed": {
            "package": obs_pkg,
            "revision": obs_rev,
            "hash": obs_hash,
            "protocol": obs_protocol,
            "orchestration": obs_orch,
        },
        "both": {
            "package": both_pkg,
            "revision": both_rev,
            "hash": both_hash,
            "binding": both_binding,
            "protocol": both_protocol,
            "orchestration": both_orch,
        },
        "orphan": {
            "package": orphan_pkg,
            "revision": orphan_rev,
            "hash": orphan_hash,
        },
        "hidden_protocol": hidden_protocol,
        "hidden_orchestration": hidden_orch,
    }


def _package_fixture(tmp_path, monkeypatch):
    values = _runtime(tmp_path, monkeypatch)
    seeded = _seed(*values)
    return values[0], values[1], seeded


def test_global_packages_projection_scopes_domains_and_reachable_skills(
    tmp_path, monkeypatch
):
    rt, owner, seeded = _package_fixture(tmp_path, monkeypatch)
    client = TestClient(_app(rt))

    assert client.get("/browser/packages").status_code == 401
    _login(client)

    response = client.get("/browser/packages")
    assert response.status_code == 200
    body = response.json()
    assert body["build_sha"] == "packages-build-sha"
    assert body["query_status"] == "COMPLETE"
    assert body["scope"]["skill_visibility"] == "AUTHORIZED_REACHABLE"

    assert [item["package_id"] for item in body["domains"]] == [
        seeded["package"]
    ]
    domain = body["domains"][0]
    assert domain["tenant_id"] == "tenant_packages"
    assert domain["domain_id"] == seeded["domain_id"]
    assert domain["revision_count"] == 3
    assert domain["latest_revision"]["revision_id"] == seeded["rev3"]
    assert domain["latest_revision"]["status"] == "DRAFT"
    assert domain["latest_published_revision"]["revision_id"] == seeded["rev2"]
    assert domain["latest_published_revision"]["status"] == "PUBLISHED"
    assert domain["authorized_project_usage_count"] == 1
    assert [r["status"] for r in domain["revisions"]] == [
        "PUBLISHED", "PUBLISHED", "DRAFT"
    ]
    assert domain["revisions"][2]["validation_report"]["ok"] is False
    assert domain["revisions"][2]["validation_report"]["errors"][0]["code"] == "TEST_DRAFT"
    assert domain["revisions"][0]["projects"][0]["project_id"] == seeded["project"]
    assert domain["revisions"][0]["projects"][0]["basis"] == "PINNED"
    assert domain["revisions"][1]["projects"] == []
    assert domain["revisions"][2]["projects"] == []

    skill_ids = {item["skill_id"] for item in body["skills"]}
    assert {
        "configured-only-skill",
        "observed-only-skill",
        "both-basis-skill",
    }.issubset(skill_ids)
    assert "unreferenced-global-skill" not in skill_ids

    by_skill = {item["skill_id"]: item for item in body["skills"]}
    assert by_skill["configured-only-skill"]["visibility_bases"] == [
        "CONFIGURED"
    ]
    assert by_skill["observed-only-skill"]["visibility_bases"] == [
        "OBSERVED"
    ]
    assert by_skill["both-basis-skill"]["visibility_bases"] == [
        "CONFIGURED", "OBSERVED"
    ]
    for package in body["skills"]:
        assert package["visibility_scope"] == "AUTHORIZED_REACHABLE"
        assert "tenant_id" not in package
        for revision in package["revisions"]:
            assert "status" not in revision
            assert "markdown" not in revision
            assert revision["tool_requirements"] == ["python"]
            assert revision["qa_contract"] == {"requires_evidence": True}

    observed_usage = next(
        revision
        for revision in by_skill["observed-only-skill"]["revisions"]
        if revision["skill_revision_id"] == seeded["observed"]["revision"]
    )["usage"]
    assert [item["basis"] for item in observed_usage] == ["OBSERVED"]
    assert [item["project_id"] for item in observed_usage] == [
        seeded["project"]
    ]
    assert seeded["hidden_project"] not in str(observed_usage)

    both_usage = by_skill["both-basis-skill"]["revisions"][0]["usage"]
    assert {item["basis"] for item in both_usage} == {
        "CONFIGURED", "OBSERVED"
    }
    assert [item["project_id"] for item in both_usage] == [
        seeded["project"], seeded["project"]
    ]

    serialized = str(body)
    assert "yaml_text" not in serialized
    assert "Private skill body must not appear" not in serialized
    assert seeded["hidden_package"] not in serialized
    assert seeded["hidden_rev"] not in serialized
    assert seeded["hidden_project"] not in serialized
    rt.close()


def test_project_packages_is_exact_and_behind_latest_is_informational(
    tmp_path, monkeypatch
):
    rt, owner, seeded = _package_fixture(tmp_path, monkeypatch)
    client = TestClient(_app(rt))
    _login(client)

    response = client.get(
        f"/browser/projects/{seeded['project']}/packages"
    )
    assert response.status_code == 200
    body = response.json()
    assert body["query_status"] == "COMPLETE"
    assert body["project"]["project_id"] == seeded["project"]
    assert body["domain"]["domain_revision_id"] == seeded["rev1"]
    assert body["domain"]["revision_number"] == 1
    assert body["domain"]["latest_published_revision"]["revision_id"] == seeded["rev2"]
    assert body["domain"]["latest_published_revision"]["revision_number"] == 2
    assert body["domain"]["revisions_behind_latest"] == 1
    assert body["domain"]["bound_by_actor_id"] == owner

    configured = body["skills"]["configured"]
    observed = body["skills"]["observed"]
    assert {
        seeded["configured"]["revision"],
        seeded["both"]["revision"],
    }.issubset({item["skill_revision_id"] for item in configured})
    assert {item["basis"] for item in configured} == {"CONFIGURED"}
    assert all(item["hash_matches_revision"] is True for item in configured)

    assert {
        seeded["observed"]["revision"],
        seeded["both"]["revision"],
    }.issubset({item["skill_revision_id"] for item in observed})
    assert {item["basis"] for item in observed} == {"OBSERVED"}
    assert all(item["hash_matches_revision"] is True for item in observed)
    assert {
        "phase_packages_observed", "phase_packages_both"
    }.issubset({item["phase_execution_id"] for item in observed})

    assert client.get(
        f"/browser/projects/{seeded['hidden_project']}/packages"
    ).status_code == 404
    rt.close()


def test_skill_hash_mismatch_is_partial_not_silently_authoritative(
    tmp_path, monkeypatch
):
    rt, _, seeded = _package_fixture(tmp_path, monkeypatch)
    client = TestClient(_app(rt))
    _login(client)

    rt.db.conn.execute(
        "UPDATE domain_skill_bindings SET skill_hash='wrong-configured-hash' "
        "WHERE binding_id=?",
        (seeded["configured"]["binding"],),
    )
    rt.db.conn.execute(
        "UPDATE phase_execution_protocols SET skill_hash='wrong-observed-hash' "
        "WHERE protocol_id=?",
        (seeded["observed"]["protocol"],),
    )
    rt.db.conn.commit()

    global_body = client.get("/browser/packages").json()
    assert global_body["query_status"] == "PARTIAL"
    configured_revision = next(
        p for p in global_body["skills"]
        if p["skill_id"] == "configured-only-skill"
    )["revisions"][0]
    assert configured_revision["bindings"][0]["hash_matches_revision"] is False
    assert configured_revision["usage"][0]["hash_matches_revision"] is False
    observed_revision = next(
        p for p in global_body["skills"]
        if p["skill_id"] == "observed-only-skill"
    )["revisions"][0]
    assert observed_revision["usage"][0]["hash_matches_revision"] is False

    project_body = client.get(
        f"/browser/projects/{seeded['project']}/packages"
    ).json()
    assert project_body["query_status"] == "PARTIAL"
    cfg = next(
        item for item in project_body["skills"]["configured"]
        if item["skill_revision_id"] == seeded["configured"]["revision"]
    )
    obs = next(
        item for item in project_body["skills"]["observed"]
        if item["skill_revision_id"] == seeded["observed"]["revision"]
    )
    assert cfg["hash_matches_revision"] is False
    assert obs["hash_matches_revision"] is False
    rt.close()


def test_unreferenced_skill_created_by_bearer_api_remains_unexposed(
    tmp_path, monkeypatch
):
    rt, _, seeded = _package_fixture(tmp_path, monkeypatch)
    client = TestClient(_app(rt))
    token = client.post(
        "/auth/login",
        json={"username": "packages-owner", "password": PASSWORD},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    skill = client.post(
        "/product/skills",
        headers=headers,
        json={
            "skill_id": "bearer-unreferenced-skill",
            "name": "Bearer Unreferenced Skill",
            "description": "Compatibility creation",
        },
    )
    assert skill.status_code == 200
    revision = client.post(
        f"/product/skills/{skill.json()['skill_package_id']}/revisions",
        headers=headers,
        json={
            "version": "1.0.0",
            "markdown": "# Bearer Skill\nCompatibility body.",
            "tool_requirements": ["python"],
            "qa_contract": {"requires_evidence": True},
        },
    )
    assert revision.status_code == 200

    domain_list = client.get(
        "/product/tenants/tenant_packages/domains",
        headers=headers,
    )
    assert domain_list.status_code == 200
    assert seeded["package"] in {
        item["package_id"] for item in domain_list.json()["domains"]
    }

    _login(client)
    browser = client.get("/browser/packages")
    assert browser.status_code == 200
    assert "bearer-unreferenced-skill" not in str(browser.json())
    rt.close()

def test_packages_browser_surface_is_live_tabbed_and_read_only():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")
    api = (ROOT / "src" / "gwr" / "api.py").read_text(encoding="utf-8")

    assert 'id="packagesRouteView"' in html
    assert 'data-packages-tab="domains"' in html
    assert 'data-packages-tab="skills"' in html
    assert 'data-packages-tab="usage"' in html
    assert 'id="packagesDomainList"' in html
    assert 'id="packagesSkillList"' in html
    assert 'id="packagesUsageBody"' in html
    assert 'item.id === "packages") renderPackagesRoute(item)' in js
    assert 'await api("/browser/packages")' in js
    assert 'visibility_scope' in js
    assert 'CONFIGURED' in js
    assert 'OBSERVED' in js
    assert "Hash matches revision" in js
    assert '"state": "LIVE_MODULE", "slice": "BPS-M06"' in api

    for forbidden in (
        "Create Domain Package",
        "Publish revision",
        "Validate revision",
        "Upgrade to latest",
        "Install Skill",
        "Create Skill",
    ):
        assert forbidden not in html

