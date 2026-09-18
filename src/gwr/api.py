from __future__ import annotations
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from .runtime import GovernedWorkflowRuntime
from .errors import GWRException


class LoginBody(BaseModel):
    username: str
    password: str


class ApprovalBody(BaseModel):
    expected_hash: str


def create_app(runtime: GovernedWorkflowRuntime) -> FastAPI:
    app=FastAPI(title="Governed Workflow Runtime",version="0.4.0")

    @app.exception_handler(GWRException)
    async def gwr_error(_, exc:GWRException):
        return __import__('fastapi').responses.JSONResponse(status_code=400,content={"ok":False,"error":{"code":exc.code,"message":exc.message,"details":exc.details}})

    @app.post('/auth/login')
    def login(body: LoginBody):
        token=runtime.auth.authenticate(body.username,body.password,client_metadata={"client":"fastapi"})
        principal=runtime.auth.verify(token)
        return {"access_token":token,"token_type":"bearer","expires_at":principal.expires_at,"actor_id":principal.actor_id}

    @app.get('/proposals/{proposal_id}')
    def proposal(proposal_id:str):
        row=runtime.db.one("SELECT proposal_id,project_id,action,resource_refs,frozen_payload,payload_hash,required_approval_policy,status,created_at FROM proposals WHERE proposal_id=?",(proposal_id,))
        if not row: raise HTTPException(status_code=404,detail="proposal not found")
        return dict(row)

    @app.post('/proposals/{proposal_id}/approve')
    def approve(proposal_id:str, body: ApprovalBody, authorization: str=Header(...)):
        if not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=401,detail="bearer token required")
        token=authorization.split(" ",1)[1].strip()
        approval_id=runtime.governance.approve_proposal_authenticated(proposal_id,token,body.expected_hash)
        return {"approval_id":approval_id,"proposal_id":proposal_id,"status":"APPROVED"}

    @app.get('/health')
    def health(): return {"ok":True,"domain":runtime.domain.domain_id}

    @app.get('/projects/{project_id}/audit')
    def audit(project_id:str): return runtime.governance.query_audit(project_id)

    @app.get('/projects/{project_id}/frontier')
    def frontier(project_id:str): return runtime.knowledge.get_validity_frontier(project_id)

    @app.get('/checkpoints/{checkpoint_id}/resume')
    def resume(checkpoint_id:str): return runtime.execution.reconcile_checkpoint(checkpoint_id)

    @app.get('/research/orchestrations/{orchestration_id}')
    def research_status(orchestration_id:str):
        from .research_orchestrator import ResearchOrchestrator
        return ResearchOrchestrator(runtime, {}, human_approver_id=None).get_status(orchestration_id)

    @app.get('/research/orchestrations/{orchestration_id}/report')
    def research_report(orchestration_id:str):
        from .research_orchestrator import ResearchOrchestrator
        return {"markdown": ResearchOrchestrator(runtime, {}, human_approver_id=None).render_report(orchestration_id)}
    return app
