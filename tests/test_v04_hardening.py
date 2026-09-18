from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from gwr.auth import HumanAuthService
from gwr.errors import AuthorityDenied
from gwr.real_research import BinomialCoverageExperimentRunner
from gwr.retrieval import (
    CrossrefConnector, DurableRetrievalCache, HttpResponse, ResilientHttpClient, RetrievalPolicy,
)
from gwr.runtime import GovernedWorkflowRuntime
from gwr.stat_verifier import SubprocessStatisticalVerifier


class ScriptedTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0
    def request(self, url, headers, timeout):
        self.calls += 1
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _crossref_payload():
    return json.dumps({"message": {"items": [{
        "DOI": "10.1/demo", "title": ["Wilson score interval"],
        "author": [{"given": "A", "family": "Researcher"}],
        "issued": {"date-parts": [[2020]]}, "URL": "https://doi.org/10.1/demo",
        "type": "journal-article", "publisher": "Demo",
    }]}}).encode()


def test_production_retrieval_retries_429_and_uses_durable_cache(tmp_path):
    transport = ScriptedTransport([
        HttpResponse(429, {"retry-after": "0"}, b"rate limited", "https://api.crossref.org/works"),
        HttpResponse(200, {"content-type": "application/json", "x-rate-limit-limit": "3"}, _crossref_payload(), "https://api.crossref.org/works"),
    ])
    client = ResilientHttpClient(
        user_agent="GWR-Test/0.4 (mailto:qa@example.org)",
        policy=RetrievalPolicy(max_attempts=3, allow_private_hosts=True),
        transport=transport, sleep=lambda _: None,
    )
    cache = DurableRetrievalCache(tmp_path / "cache")
    cr = CrossrefConnector(client, cache, mailto="qa@example.org")
    first = cr.search("Wilson interval", rows=1)
    assert first["records"][0]["doi"] == "10.1/demo"
    assert first["retrieval"]["cache_hit"] is False
    assert transport.calls == 2
    second = cr.search("Wilson interval", rows=1)
    assert second["retrieval"]["cache_hit"] is True
    assert transport.calls == 2


def test_statistical_verifier_is_separate_process_and_recomputes_from_raw_rows():
    metrics = BinomialCoverageExperimentRunner().run_grid([10, 20], [0.1, 0.2, 0.5, 0.8, 0.9])
    # Corrupt aggregates on purpose. The verifier must not trust experiment-process summaries.
    metrics["overall"] = {"wilson_mae": 999, "wald_mae": 0.0001, "mean_improvement": -999}
    result = SubprocessStatisticalVerifier().verify(metrics, min_relative_reduction=0.10)
    assert result["independent_process"] is True
    assert result["worker_pid"] != os.getpid()
    assert result["input_sha256"]
    assert result["result_sha256"]
    assert result["recomputed"]["wilson_mae"] < 1
    assert result["recomputed"]["wald_mae"] < 1


def test_authenticated_human_approval_requires_valid_revocable_session(tmp_path, monkeypatch):
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    root = Path(__file__).parents[1]
    rt = GovernedWorkflowRuntime(str(root / "domains" / "research.workflow.yaml"), str(tmp_path / "auth.db"), auth_secret="x" * 64)
    project = rt.create_project("auth-test")
    proposer = rt.governance.create_actor("AGENT", "lead", ["research_lead"], [project])
    human = rt.governance.create_actor("HUMAN", "alice", ["human_approver"], [project])
    rt.auth.register_human(human, "alice", "correct horse battery staple")
    proposal = rt.governance.prepare_proposal(project, proposer, "CREATE_REVISION", ["demo"], {"demo": True}, "normative_research_change")
    p = rt.db.one("SELECT * FROM proposals WHERE proposal_id=?", (proposal,))
    with pytest.raises(AuthorityDenied):
        rt.auth.authenticate("alice", "wrong password here")
    token = rt.auth.authenticate("alice", "correct horse battery staple")
    aid = rt.governance.approve_proposal_authenticated(proposal, token, p["payload_hash"])
    assert aid
    assert rt.db.one("SELECT status FROM proposals WHERE proposal_id=?", (proposal,))["status"] == "APPROVED"
    rt.auth.revoke(token)
    with pytest.raises(AuthorityDenied):
        rt.auth.verify(token)
    events = rt.governance.query_audit(project)
    assert any(e["action"] == "AUTHENTICATED_APPROVAL" for e in events)
    rt.close()


def test_authenticated_approval_fastapi_surface(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from gwr.api import create_app
    monkeypatch.setattr(HumanAuthService, "PASSWORD_ITERATIONS", 1_000)
    root = Path(__file__).parents[1]
    rt = GovernedWorkflowRuntime(str(root / "domains" / "research.workflow.yaml"), str(tmp_path / "api-auth.db"), auth_secret="z" * 64)
    project = rt.create_project("api-auth-test")
    proposer = rt.governance.create_actor("AGENT", "lead-api", ["research_lead"], [project])
    human = rt.governance.create_actor("HUMAN", "bob", ["human_approver"], [project])
    rt.auth.register_human(human, "bob", "long enough test password")
    proposal = rt.governance.prepare_proposal(project, proposer, "CREATE_REVISION", ["demo"], {"demo": "api"}, "normative_research_change")
    row = rt.db.one("SELECT payload_hash FROM proposals WHERE proposal_id=?", (proposal,))
    client = TestClient(create_app(rt))
    login = client.post('/auth/login', json={"username":"bob","password":"long enough test password"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    approved = client.post(f'/proposals/{proposal}/approve', headers={"Authorization":f"Bearer {token}"}, json={"expected_hash":row["payload_hash"]})
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"
    rt.close()
