from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gwr.runtime import GovernedWorkflowRuntime
from gwr.research_orchestrator import ResearchOrchestrator
from gwr.real_research import RealResearchExecutor, BinomialCoverageExperimentRunner, DEFAULT_PAPERS
from gwr.retrieval import (
    CrossrefConnector, DurableRetrievalCache, ProductionPaperRetriever,
    ResilientHttpClient, RetrievalPolicy, WebDocumentConnector,
)
from gwr.stat_verifier import SubprocessStatisticalVerifier
from gwr.utils import parse_json

ROLES = [
    "research_lead", "literature_reviewer", "protocol_designer", "experimenter",
    "analyst", "adversarial_reviewer", "reproducibility_reviewer",
]


def paper_snapshot():
    return [
        {
            "title": r.title, "authors": r.authors, "year": r.year, "url": r.url,
            "doi": r.doi, "summary": r.summary, "source": r.source,
        }
        for r in DEFAULT_PAPERS
    ]


def approve_one(rt, project_id: str, username: str, password: str) -> dict:
    prop = rt.db.one(
        "SELECT * FROM proposals WHERE project_id=? AND status='PENDING_APPROVAL' ORDER BY created_at DESC LIMIT 1",
        (project_id,),
    )
    if not prop:
        raise RuntimeError("runtime paused for human action but no pending proposal exists")
    token = rt.auth.authenticate(username, password, client_metadata={"client": "v0.4-qa-external-human-driver"})
    principal = rt.auth.verify(token)
    approval_id = rt.governance.approve_proposal_authenticated(prop["proposal_id"], token, prop["payload_hash"])
    rt.auth.revoke(token)
    return {
        "proposal_id": prop["proposal_id"], "approval_id": approval_id,
        "action": prop["action"], "approver_actor_id": principal.actor_id,
        "session_id": principal.session_id,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "evidence" / "v0.4" / "real_run"))
    ap.add_argument("--no-recovery-demo", action="store_true")
    ap.add_argument("--crossref-mailto", default=os.environ.get("GWR_CROSSREF_MAILTO", "qa@example.org"))
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    db = out / "runtime.db"
    if db.exists():
        db.unlink()
    cache_dir = out / "retrieval_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    auth_secret = os.environ.get("GWR_AUTH_SECRET") or secrets.token_urlsafe(48)
    qa_password = secrets.token_urlsafe(24)
    rt = GovernedWorkflowRuntime(str(ROOT / "domains" / "research.workflow.yaml"), str(db), auth_secret=auth_secret)
    project = rt.create_project("v0.4-real-binomial-coverage")
    actors = {role: rt.governance.create_actor("AGENT", f"{role}-v04", [role], [project]) for role in ROLES}
    human = rt.governance.create_actor("HUMAN", "qa-authenticated-human", ["human_approver"], [project])
    rt.auth.register_human(human, "qa-human", qa_password)

    policy = RetrievalPolicy(timeout_seconds=2.0, max_attempts=2, backoff_seconds=0.05, max_backoff_seconds=0.1)
    http = ResilientHttpClient(user_agent=f"GWR-Research/0.4 (mailto:{args.crossref_mailto})", policy=policy)
    cache = DurableRetrievalCache(cache_dir)
    crossref = CrossrefConnector(http, cache, mailto=args.crossref_mailto, cache_ttl_seconds=86_400)
    web = WebDocumentConnector(http, cache, cache_ttl_seconds=86_400)
    retriever = ProductionPaperRetriever(crossref, web, offline_records=paper_snapshot())
    verifier = SubprocessStatisticalVerifier(timeout_seconds=30)
    executor = RealResearchExecutor(
        retriever, BinomialCoverageExperimentRunner(), verifier,
        force_live_retrieval_probe=True, recovery_demo=not args.no_recovery_demo,
    )
    orch = ResearchOrchestrator(rt, actors)  # no actor-id shortcut; human actions must be authenticated

    result = orch.start(project, executor, max_steps=400)
    approvals = []
    safety = 0
    while result["status"] == "PAUSED" and result.get("reason") in {"WAITING_APPROVAL", "WAITING_HUMAN_CONFIRMATION"}:
        safety += 1
        if safety > 40:
            raise RuntimeError("too many human approval cycles")
        approvals.append(approve_one(rt, project, "qa-human", qa_password))
        result = orch.resume(result["checkpoint_id"], executor, max_steps=400)

    if result["status"] != "COMPLETED":
        raise RuntimeError(f"unexpected terminal state: {result}")

    oid = result["orchestration_id"]
    orch.write_report(oid, out / "RUNTIME_REPORT.md")
    (out / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (out / "status.json").write_text(json.dumps(orch.get_status(oid), indent=2), encoding="utf-8")
    (out / "audit.json").write_text(json.dumps(rt.governance.query_audit(project), indent=2), encoding="utf-8")

    artifacts = {}
    for row in rt.db.all("SELECT artifact_type,current_revision_id FROM artifacts WHERE project_id=? ORDER BY artifact_type", (project,)):
        artifacts[row["artifact_type"]] = rt.knowledge.get_revision(row["current_revision_id"])["structured_payload"]
    (out / "artifacts.json").write_text(json.dumps(artifacts, indent=2), encoding="utf-8")

    sessions = [dict(r) for r in rt.db.all("SELECT session_id,actor_id,issued_at,expires_at,revoked_at,auth_method,client_metadata FROM auth_sessions ORDER BY issued_at")]
    auth_evidence = {
        "human_actor_id": human,
        "authenticated_approval_count": len(approvals),
        "approvals": approvals,
        "sessions": sessions,
        "all_sessions_revoked_after_use": all(x["revoked_at"] for x in sessions),
        "authenticated_approval_audit_events": sum(1 for e in rt.governance.query_audit(project) if e["action"] == "AUTHENTICATED_APPROVAL"),
    }
    (out / "auth_evidence.json").write_text(json.dumps(auth_evidence, indent=2), encoding="utf-8")

    retrieval_evidence = []
    for ev in rt.db.all("SELECT evidence_type,structured_payload,content_hash FROM evidence WHERE project_id=? AND evidence_type='source_citation_evidence'", (project,)):
        payload = parse_json(ev["structured_payload"], {})
        retrieval_evidence.append({"content_hash": ev["content_hash"], "retrieval": payload.get("retrieval"), "sources": payload.get("sources", [])})
    (out / "retrieval_evidence.json").write_text(json.dumps(retrieval_evidence, indent=2), encoding="utf-8")

    verifier_evidence = artifacts.get("analysis_result", {}).get("verification_manifest", {})
    (out / "verifier_evidence.json").write_text(json.dumps(verifier_evidence, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))
    print(json.dumps({"authenticated_approvals": len(approvals), "verifier": verifier_evidence}, indent=2))
    rt.close()


if __name__ == "__main__":
    main()
