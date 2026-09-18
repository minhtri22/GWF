from __future__ import annotations
import json
from .utils import uid, utcnow, canonical_json, content_hash, parse_json
from .errors import NotFound, AuthorityDenied, ApprovalMismatch, ValidationError, IdempotencyConflict

class GovernanceKernel:
    def __init__(self, db, domain):
        self.db,self.domain=db,domain
        self.auth=None
        self.tenancy=None
        self.project_governance=None
    def bind_auth(self, auth_service):
        self.auth=auth_service
    def bind_tenancy(self, tenancy_service):
        self.tenancy=tenancy_service
    def bind_project_governance(self, service):
        self.project_governance=service
    def create_actor(self, actor_type, principal_id, roles, project_scope, identity_metadata=None, actor_id=None):
        actor_id=actor_id or uid("actor")
        self.db.conn.execute("INSERT INTO actors VALUES(?,?,?,?,?,?,?)",(actor_id,actor_type,principal_id,canonical_json(roles),canonical_json(project_scope),"ACTIVE",canonical_json(identity_metadata or {}))); self.db.conn.commit(); return actor_id
    def install_domain_policies(self):
        for p in self.domain.data.get("authority_policies",[]):
            pid=p.get("id") or uid("policy")
            subject={"role":p.get("role")} if p.get("role") else p.get("subject_selector",{})
            acts=[x["action"] if isinstance(x,dict) else x for x in p.get("allow",p.get("actions",[]))]
            resource=p.get("resource_selector",{})
            self.db.conn.execute("DELETE FROM authority_policies WHERE policy_id=?",(pid,)); self.db.conn.execute("INSERT INTO authority_policies VALUES(?,?,?,?,?,?,?,?)",(pid,str(p.get("version","1")),canonical_json(subject),canonical_json(resource),canonical_json(acts),canonical_json(p.get("conditions",{})),p.get("effect","ALLOW"),int(p.get("priority",0))))
        self.db.conn.commit()
    def authenticate_actor(self, actor_id):
        a=self._actor(actor_id)
        if a["status"]!="ACTIVE": raise AuthorityDenied("Actor is not active")
        return {"actor_id":a["actor_id"],"actor_type":a["actor_type"],"roles":parse_json(a["role_bindings"],[])}
    def _actor(self, actor_id):
        r=self.db.one("SELECT * FROM actors WHERE actor_id=?",(actor_id,));
        if not r: raise NotFound("Actor not found")
        return r
    def authorize(self, actor_id, action, resource=None):
        a=self._actor(actor_id); roles=set(parse_json(a["role_bindings"],[])); matched_allow=False; resource=resource or {}
        scopes=set(parse_json(a["project_scope"],[]))
        if resource.get("project_id"):
            scoped = self.tenancy.scope_for_project(resource["project_id"]) if self.tenancy else None
            if scoped:
                permission=self.tenancy.permission_for_governance_action(action)
                self.tenancy.require_project_access(actor_id,resource["project_id"],permission)
            elif resource["project_id"] not in scopes and "*" not in scopes:
                raise AuthorityDenied("Actor outside project scope")
        policies=sorted(self.db.all("SELECT * FROM authority_policies"), key=lambda r:r["priority"], reverse=True)
        for p in policies:
            subj=parse_json(p["subject_selector"],{}); acts=set(parse_json(p["actions"],[])); selector=parse_json(p["resource_selector"],{})
            if action not in acts: continue
            role=subj.get("role")
            if role and role not in roles: continue
            if any(resource.get(k)!=v for k,v in selector.items() if k in resource): continue
            if p["effect"]=="DENY": raise AuthorityDenied(f"{actor_id} denied {action}")
            matched_allow=True
        if not matched_allow: raise AuthorityDenied(f"{actor_id} lacks authority {action}", details={"resource":resource or {}})
        return True
    def append_audit(self, project_id, actor_id, action, resource_type, resource_id, **kw):
        event=uid("audit"); metadata_hash=content_hash(kw.get("metadata",{}))
        self.db.conn.execute("INSERT INTO audit_events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(event,project_id,actor_id,action,resource_type,resource_id,kw.get("before_version"),kw.get("after_version"),kw.get("proposal_id"),kw.get("approval_id"),kw.get("run_id"),kw.get("decision_id"),kw.get("correlation_id"),kw.get("reason_code","OK"),utcnow(),metadata_hash)); return event
    def prepare_proposal(self, project_id, proposer_actor_id, action, resource_refs, frozen_payload, required_approval_policy=None, idempotency_key=None):
        if self.project_governance:
            self.project_governance.require_mutable(project_id)
        self.authorize(proposer_actor_id,"PROPOSE",{"action":action,"project_id":project_id})
        ph=content_hash(frozen_payload)
        if idempotency_key:
            row=self.db.one("SELECT * FROM proposals WHERE idempotency_key=?",(idempotency_key,))
            if row:
                if row["payload_hash"]!=ph: raise IdempotencyConflict("Proposal idempotency key reused with different payload")
                return row["proposal_id"]
        pid=uid("prop"); status="PENDING_APPROVAL" if required_approval_policy else "APPROVED"
        self.db.conn.execute("INSERT INTO proposals VALUES(?,?,?,?,?,?,?,?,?,?,?)",(pid,project_id,proposer_actor_id,action,canonical_json(resource_refs),canonical_json(frozen_payload),ph,required_approval_policy,status,utcnow(),idempotency_key)); self.append_audit(project_id,proposer_actor_id,"PREPARE_PROPOSAL","Proposal",pid,proposal_id=pid); self.db.conn.commit(); return pid

    def prepare_system_proposal(self, project_id, action, resource_refs, frozen_payload, required_approval_policy):
        if self.project_governance:
            self.project_governance.require_mutable(project_id)
        ph=content_hash(frozen_payload)
        pid=uid("prop")
        self.db.conn.execute("INSERT INTO proposals VALUES(?,?,?,?,?,?,?,?,?,?,?)",(pid,project_id,"SYSTEM",action,canonical_json(resource_refs),canonical_json(frozen_payload),ph,required_approval_policy,"PENDING_APPROVAL",utcnow(),None))
        self.append_audit(project_id,"SYSTEM","PREPARE_SYSTEM_PROPOSAL","Proposal",pid,proposal_id=pid,reason_code=action)
        self.db.conn.commit()
        return pid

    def approve_proposal_authenticated(self, proposal_id, bearer_token, expected_hash):
        if not self.auth:
            raise AuthorityDenied("Human authentication service is not configured")
        principal=self.auth.verify(bearer_token)
        aid=self.approve_proposal(proposal_id, principal.actor_id, expected_hash)
        p=self.db.one("SELECT project_id FROM proposals WHERE proposal_id=?",(proposal_id,))
        self.append_audit(p["project_id"],principal.actor_id,"AUTHENTICATED_APPROVAL","Proposal",proposal_id,approval_id=aid,reason_code=principal.auth_method,metadata={"session_id":principal.session_id})
        self.db.conn.commit()
        return aid

    def approve_proposal(self, proposal_id, approver_actor_id, expected_hash):
        p=self.db.one("SELECT * FROM proposals WHERE proposal_id=?",(proposal_id,));
        if not p: raise NotFound("Proposal not found")
        self.authorize(approver_actor_id,"APPROVE",{"proposal_id":proposal_id,"project_id":p["project_id"]})
        if p["payload_hash"]!=expected_hash: raise ApprovalMismatch("Proposal hash mismatch")
        policy=self.domain.approval_policy(p["required_approval_policy"]) if p["required_approval_policy"] else None
        if policy:
            a=self._actor(approver_actor_id)
            if policy.get("requires_actor_type") and a["actor_type"]!=policy["requires_actor_type"]: raise AuthorityDenied("Approver actor type invalid")
            if policy.get("prohibit_self_approval") and p["proposer_actor_id"]==approver_actor_id: raise AuthorityDenied("Self approval prohibited")
            if policy.get("requires_role") and policy["requires_role"] not in parse_json(a["role_bindings"],[]): raise AuthorityDenied("Approver role invalid")
        aid=uid("appr")
        self.db.conn.execute("INSERT INTO approvals VALUES(?,?,?,?,?,?,?,?,?,?)",(aid,p["project_id"],proposal_id,expected_hash,approver_actor_id,"APPROVED",canonical_json(parse_json(p["resource_refs"],[])),utcnow(),None,canonical_json({})))
        self.db.conn.execute("UPDATE proposals SET status='APPROVED' WHERE proposal_id=?",(proposal_id,)); self.append_audit(p["project_id"],approver_actor_id,"APPROVE_PROPOSAL","Proposal",proposal_id,proposal_id=proposal_id,approval_id=aid); self.db.conn.commit(); return aid
    def reject_proposal_authenticated(self, proposal_id, bearer_token, expected_hash, reason="REJECTED"):
        if not self.auth:
            raise AuthorityDenied("Human authentication service is not configured")
        principal=self.auth.verify(bearer_token)
        aid=self.reject_proposal(proposal_id, principal.actor_id, expected_hash=expected_hash, reason=reason)
        p=self.db.one("SELECT project_id FROM proposals WHERE proposal_id=?",(proposal_id,))
        self.append_audit(p["project_id"],principal.actor_id,"AUTHENTICATED_REJECTION","Proposal",proposal_id,approval_id=aid,reason_code=principal.auth_method,metadata={"session_id":principal.session_id,"reason":reason})
        self.db.conn.commit()
        return aid

    def reject_proposal(self, proposal_id, actor_id, expected_hash=None, reason="REJECTED"):
        p=self.db.one("SELECT * FROM proposals WHERE proposal_id=?",(proposal_id,))
        if not p: raise NotFound("Proposal not found")
        self.authorize(actor_id,"APPROVE",{"proposal_id":proposal_id,"project_id":p["project_id"]})
        if expected_hash is not None and p["payload_hash"]!=expected_hash:
            raise ApprovalMismatch("Proposal hash mismatch")
        policy=self.domain.approval_policy(p["required_approval_policy"]) if p["required_approval_policy"] else None
        if policy:
            a=self._actor(actor_id)
            if policy.get("requires_actor_type") and a["actor_type"]!=policy["requires_actor_type"]: raise AuthorityDenied("Approver actor type invalid")
            if policy.get("prohibit_self_approval") and p["proposer_actor_id"]==actor_id: raise AuthorityDenied("Self approval prohibited")
            if policy.get("requires_role") and policy["requires_role"] not in parse_json(a["role_bindings"],[]): raise AuthorityDenied("Approver role invalid")
        aid=uid("appr")
        decision_hash=expected_hash or p["payload_hash"]
        self.db.conn.execute("INSERT INTO approvals VALUES(?,?,?,?,?,?,?,?,?,?)",(aid,p["project_id"],proposal_id,decision_hash,actor_id,"REJECTED",canonical_json(parse_json(p["resource_refs"],[])),utcnow(),None,canonical_json({"reason":reason})))
        self.db.conn.execute("UPDATE proposals SET status='REJECTED' WHERE proposal_id=?",(proposal_id,))
        self.append_audit(p["project_id"],actor_id,"REJECT_PROPOSAL","Proposal",proposal_id,proposal_id=proposal_id,approval_id=aid,reason_code=reason)
        self.db.conn.commit()
        return aid
    def resolve_escalation_target(self, project_id, required_action="ESCALATE"):
        for a in self.db.all("SELECT * FROM actors WHERE status='ACTIVE'"):
            if project_id not in parse_json(a["project_scope"],[]): continue
            try:
                self.authorize(a["actor_id"],required_action,{"project_id":project_id}); return a["actor_id"]
            except AuthorityDenied: pass
        return None
    def get_pending_approvals(self, project_id): return [dict(r) for r in self.db.all("SELECT * FROM proposals WHERE project_id=? AND status='PENDING_APPROVAL'",(project_id,))]
    def require_approved(self, proposal_id):
        p=self.db.one("SELECT * FROM proposals WHERE proposal_id=?",(proposal_id,));
        if not p: raise NotFound("Proposal not found")
        if p["status"]!="APPROVED": raise ApprovalMismatch(f"Proposal status is {p['status']}")
        return p
    def query_audit(self, project_id): return [dict(r) for r in self.db.all("SELECT * FROM audit_events WHERE project_id=? ORDER BY timestamp",(project_id,))]
