from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from gwr.auth import HumanAuthService
from gwr.api import create_app
from gwr.errors import AuthorityDenied
from gwr.runtime import GovernedWorkflowRuntime

ROOT = Path(__file__).parents[1]


def make_runtime(tmp_path, domain="example.workflow.yaml"):
    return GovernedWorkflowRuntime(str(ROOT / "domains" / domain), str(tmp_path / "v06.db"), auth_secret="v" * 64)


def human(rt, principal, roles=None):
    return rt.governance.create_actor("HUMAN", principal, roles or [], [])


def test_v06_migration_installs_identity_and_tenancy_tables(tmp_path):
    rt = make_runtime(tmp_path)
    tables = set(rt.db.list_tables())
    expected = {
        "tenants", "workspaces", "project_scopes", "tenant_memberships",
        "workspace_memberships", "project_memberships", "external_identities", "security_events",
    }
    assert expected.issubset(tables)
    status = rt.db.migrations.status()
    assert "0002_v06_identity_multitenancy" in status["applied"]
    assert status["pending"] == []
    rt.close()



def test_agent_cannot_bootstrap_tenant_owner(tmp_path):
    rt = make_runtime(tmp_path)
    agent = rt.governance.create_actor("AGENT", "bootstrap-agent", ["planner"], [])
    with pytest.raises(AuthorityDenied):
        rt.tenancy.create_tenant("Forbidden", agent)
    rt.close()

def test_tenant_workspace_project_isolation_ignores_legacy_scope_injection(tmp_path):
    rt = make_runtime(tmp_path)
    alice = human(rt, "alice")
    bob = human(rt, "bob")

    ta = rt.tenancy.create_tenant("Tenant A", alice)
    tb = rt.tenancy.create_tenant("Tenant B", bob)
    wa = rt.tenancy.create_workspace(ta, "Lab A", alice)
    wb = rt.tenancy.create_workspace(tb, "Lab B", bob)
    pa = rt.create_scoped_project("Project A", ta, wa, alice)
    pb = rt.create_scoped_project("Project B", tb, wb, bob)

    assert rt.tenancy.require_project_access(alice, pa, "VIEW") is True
    assert rt.tenancy.require_project_access(bob, pb, "VIEW") is True
    with pytest.raises(AuthorityDenied):
        rt.tenancy.require_project_access(alice, pb, "VIEW")

    # A leaked/project_scope injection must not bypass authoritative tenant membership.
    row = rt.db.one("SELECT project_scope FROM actors WHERE actor_id=?", (alice,))
    import json
    scopes = json.loads(row["project_scope"])
    scopes.append(pb)
    rt.db.conn.execute("UPDATE actors SET project_scope=? WHERE actor_id=?", (json.dumps(scopes), alice))
    rt.db.conn.commit()
    with pytest.raises(AuthorityDenied):
        rt.tenancy.require_project_access(alice, pb, "VIEW")

    assert [p["id"] for p in rt.tenancy.list_accessible_projects(alice)] == [pa]
    assert [p["id"] for p in rt.tenancy.list_accessible_projects(bob)] == [pb]
    rt.close()


def test_oidc_exchange_uses_verified_issuer_subject_mapping_not_actor_claim(tmp_path):
    rt = make_runtime(tmp_path)
    bound = human(rt, "bound-human")
    victim = human(rt, "victim-human")
    exp = (datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp()

    def verifier(token: str):
        if token == "bad-issuer":
            return {"iss": "https://evil.example", "sub": "subject-123", "exp": exp}
        return {
            "iss": "https://id.example",
            "sub": "subject-123",
            "exp": exp,
            "amr": ["mfa"],
            "actor_id": victim,  # attacker-controlled claim must be ignored
        }

    rt.auth.register_oidc_provider("example", "https://id.example", verifier)
    rt.auth.bind_external_identity(bound, "example", "https://id.example", "subject-123", email="bound@example.test")

    token = rt.auth.authenticate_oidc("example", "valid-token")
    principal = rt.auth.verify(token)
    assert principal.actor_id == bound
    assert principal.actor_id != victim
    assert principal.auth_method == "OIDC"

    with pytest.raises(AuthorityDenied):
        rt.auth.authenticate_oidc("example", "bad-issuer")
    rt.auth.revoke(token)
    with pytest.raises(AuthorityDenied):
        rt.auth.verify(token)
    rt.close()


def test_scoped_proposal_rejects_cross_tenant_approver_even_with_domain_role(tmp_path):
    rt = make_runtime(tmp_path, "research.workflow.yaml")
    owner_a = human(rt, "owner-a", ["human_approver"])
    owner_b = human(rt, "owner-b", ["human_approver"])
    proposer = rt.governance.create_actor("AGENT", "lead-a", ["research_lead"], [])

    ta = rt.tenancy.create_tenant("Tenant A", owner_a)
    tb = rt.tenancy.create_tenant("Tenant B", owner_b)
    wa = rt.tenancy.create_workspace(ta, "A", owner_a)
    wb = rt.tenancy.create_workspace(tb, "B", owner_b)
    pa = rt.create_scoped_project("PA", ta, wa, owner_a)
    _ = rt.create_scoped_project("PB", tb, wb, owner_b)
    rt.tenancy.add_project_member(pa, proposer, "RESEARCHER", owner_a)

    # Even if legacy project scope is manually injected, tenant membership is authoritative.
    rt.db.conn.execute("UPDATE actors SET project_scope=? WHERE actor_id=?", (f'["{pa}"]', owner_b))
    rt.db.conn.commit()

    proposal = rt.governance.prepare_proposal(
        pa, proposer, "CREATE_REVISION", ["hypothesis"], {"hypothesis": "demo"}, "normative_research_change"
    )
    row = rt.db.one("SELECT payload_hash FROM proposals WHERE proposal_id=?", (proposal,))
    with pytest.raises(AuthorityDenied):
        rt.governance.approve_proposal(proposal, owner_b, row["payload_hash"])

    rt.tenancy.add_project_member(pa, owner_a, "APPROVER", owner_a)
    approval = rt.governance.approve_proposal(proposal, owner_a, row["payload_hash"])
    assert approval
    rt.close()


def test_api_hides_cross_tenant_projects_and_membership_revocation_is_immediate(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    rt = make_runtime(tmp_path)
    alice = human(rt, "alice")
    bob = human(rt, "bob")
    guest = human(rt, "guest")
    rt.auth.register_human(alice, "alice", "alice-password-long")
    rt.auth.register_human(bob, "bob", "bob-password-longgg")
    rt.auth.register_human(guest, "guest", "guest-password-long")

    ta = rt.tenancy.create_tenant("Tenant A", alice)
    tb = rt.tenancy.create_tenant("Tenant B", bob)
    wa = rt.tenancy.create_workspace(ta, "WA", alice)
    wb = rt.tenancy.create_workspace(tb, "WB", bob)
    pa = rt.create_scoped_project("PA", ta, wa, alice)
    pb = rt.create_scoped_project("PB", tb, wb, bob)
    rt.tenancy.add_project_member(pa, guest, "VIEWER", alice)

    client = TestClient(create_app(rt))
    alice_token = client.post("/auth/login", json={"username": "alice", "password": "alice-password-long"}).json()["access_token"]
    guest_token = client.post("/auth/login", json={"username": "guest", "password": "guest-password-long"}).json()["access_token"]

    a_projects = client.get("/projects", headers={"Authorization": f"Bearer {alice_token}"})
    assert a_projects.status_code == 200
    assert [x["id"] for x in a_projects.json()["projects"]] == [pa]

    hidden = client.get(f"/projects/{pb}/frontier", headers={"Authorization": f"Bearer {alice_token}"})
    assert hidden.status_code == 404

    before = client.get(f"/projects/{pa}/frontier", headers={"Authorization": f"Bearer {guest_token}"})
    assert before.status_code == 200
    rt.tenancy.revoke_project_member(pa, guest, alice)
    after = client.get(f"/projects/{pa}/frontier", headers={"Authorization": f"Bearer {guest_token}"})
    assert after.status_code == 404
    rt.close()
