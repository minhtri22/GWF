from __future__ import annotations
from .utils import uid, utcnow, canonical_json, content_hash, parse_json
from .errors import NotFound, ValidationError, LoopGuardTriggered

class DecisionKernel:
    def __init__(self, db, domain, knowledge, governance): self.db,self.domain,self.knowledge,self.gov=db,domain,knowledge,governance
    def evaluate_gate(self, project_id, gate_type, scope, input_revision_ids, evidence_ids=None, actor_id="SYSTEM"):
        cfg=self.domain.gate(gate_type)
        if not cfg: raise ValidationError(f"Unknown gate type {gate_type}")
        violations=[]; refs=[]
        required_validity=cfg.get("required_validity",{}).get("inputs") or cfg.get("requires",[{}])[0].get("input_validity") if cfg.get("requires") else cfg.get("required_validity",{}).get("inputs")
        required_validity=required_validity or "VALID"
        for rid in input_revision_ids:
            st=self.knowledge.get_validity(rid); refs.append({"revision_id":rid,"validity":st})
            if st!=required_validity: violations.append(f"INPUT_{st}")
        evs=[]
        for eid in evidence_ids or []:
            row=self.db.one("SELECT * FROM evidence WHERE evidence_id=?",(eid,))
            if not row: violations.append("EVIDENCE_MISSING"); continue
            evs.append(eid)
            allowed=cfg.get("allowed_trust_classes",["AUTHORITATIVE","SUPPORTED"])
            if row["trust_class"] not in allowed: violations.append("EVIDENCE_TRUST_INSUFFICIENT")
            payload=parse_json(row["structured_payload"],{})
            if payload.get("pass") is False: violations.append("EVIDENCE_ASSERTION_FAILED")
        req_evidence_types=cfg.get("required_evidence_types",[])
        if req_evidence_types:
            present={self.db.one("SELECT evidence_type FROM evidence WHERE evidence_id=?",(e,))["evidence_type"] for e in evs}
            for typ in req_evidence_types:
                if typ not in present: violations.append(f"MISSING_EVIDENCE:{typ}")
        # Structured gate predicates must be explicitly asserted by evidence.
        # This is still domain-declarative: no free-form LLM text is parsed as a gate result.
        asserted=set()
        for eid in evs:
            row=self.db.one("SELECT structured_payload FROM evidence WHERE evidence_id=?",(eid,))
            payload=parse_json(row["structured_payload"],{}) if row else {}
            asserted.update(payload.get("assertions",[]) or [])
            asserted.update(k for k,v in (payload.get("checks",{}) or {}).items() if v is True)
        for predicate in cfg.get("pass_if",[]) or []:
            if predicate not in asserted:
                violations.append(f"UNASSERTED_PREDICATE:{predicate}")
        result="PASS" if not violations else ("FAIL" if any(v in {"EVIDENCE_ASSERTION_FAILED"} or v.startswith("INPUT_FAILED") for v in violations) else "BLOCKED")
        gid=uid("gate"); self.db.conn.execute("INSERT INTO gates VALUES(?,?,?,?,?,?,?,?,?,?,?)",(gid,project_id,gate_type,canonical_json(scope),canonical_json(input_revision_ids),canonical_json(evs),str(cfg.get("policy_version","1")),result,canonical_json(sorted(set(violations))),canonical_json(refs+[{"evidence_id":e} for e in evs]),utcnow())); self.gov.append_audit(project_id,"SYSTEM","GATE_EVALUATED","Gate",gid,reason_code=result); self.db.conn.commit(); return {"gate_id":gid,"result":result,"violations":sorted(set(violations))}
    def get_gate_status(self, project_id, scope=None):
        rows=self.db.all("SELECT * FROM gates WHERE project_id=? ORDER BY evaluated_at DESC",(project_id,))
        return [dict(r) for r in rows if scope is None or parse_json(r["scope"],{})==scope]

    def create_decision(self, project_id, scope, decision_type, reason_codes, source_gate_ids=None, source_failure_id=None, target_ref=None, created_by="SYSTEM"):
        if decision_type not in {"CONTINUE","RETRY","REVISE_CURRENT","REVISE_UPSTREAM","REPLAN","ESCALATE","ABORT","WAIT"}: raise ValidationError("Invalid decision type")
        did=uid("dec"); self.db.conn.execute("INSERT INTO decisions VALUES(?,?,?,?,?,?,?,?,?,?)",(did,project_id,canonical_json(scope),canonical_json(source_gate_ids or []),source_failure_id,decision_type,target_ref,canonical_json(reason_codes),utcnow(),created_by)); self.gov.append_audit(project_id,"SYSTEM","DECISION_CREATED","Decision",did,decision_id=did,reason_code=decision_type); self.db.conn.commit(); return did
    def record_failure(self, project_id, scope_id, failure_class, detected_stage, detected_ref, evidence_ids=None, detected_revision_id=None, failed_gate_id=None, severity="MEDIUM", violations=None):
        cfg=self.domain.failure(failure_class)
        if not cfg: raise ValidationError(f"Unknown failure class {failure_class}")
        sig=content_hash({"failure_class":failure_class,"gate":failed_gate_id,"detected":detected_ref,"violations":sorted(violations or []),"evidence":sorted(evidence_ids or [])})
        fid=uid("fail"); self.db.conn.execute("INSERT INTO failures VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(fid,project_id,scope_id,failure_class,detected_stage,detected_ref,detected_revision_id,failed_gate_id,canonical_json(evidence_ids or []),None,None,"UNKNOWN",None,severity,sig,"OPEN",utcnow(),None)); self._bump_loopguard(project_id,scope_id,sig); self.gov.append_audit(project_id,"SYSTEM","FAILURE_RECORDED","FailureRecord",fid,reason_code=failure_class); self.db.conn.commit(); return fid
    def _bump_loopguard(self, project_id, scope, signature):
        row=self.db.one("SELECT * FROM loopguards WHERE project_id=? AND scope=? AND failure_signature=?",(project_id,scope,signature)); limit=int(self.domain.data.get("loop_policy",{}).get("same_signature_limit",2))
        if not row:
            self.db.conn.execute("INSERT INTO loopguards VALUES(?,?,?,?,?,?,?,?,?,?)",(uid("loop"),project_id,scope,signature,1,0,0,"runtime",canonical_json({"same_signature_limit":limit}),"OK")); return
        c=row["same_signature_count"]+1; status="ESCALATE" if c>=limit else "OK"; self.db.conn.execute("UPDATE loopguards SET same_signature_count=?, status=? WHERE loopguard_id=?",(c,status,row["loopguard_id"]))
    def loop_status(self, project_id, scope, signature):
        r=self.db.one("SELECT * FROM loopguards WHERE project_id=? AND scope=? AND failure_signature=?",(project_id,scope,signature)); return dict(r) if r else None
    def propose_root(self, failure_id, proposed_root_revision_id, resume_candidate):
        f=self.db.one("SELECT * FROM failures WHERE failure_id=?",(failure_id,))
        if not f: raise NotFound("Failure not found")
        self.db.conn.execute("UPDATE failures SET root_ref=?,root_revision_id=?,root_status='PROPOSED',resume_candidate=? WHERE failure_id=?",(proposed_root_revision_id,proposed_root_revision_id,resume_candidate,failure_id)); self.db.conn.commit()
    def earliest_invalid_ancestor(self, revision_id):
        # TraceLink convention: downstream source -> upstream target. Walk upstream and return earliest non-VALID known node.
        candidates=[]; q=[(revision_id,0)]; seen=set()
        while q:
            rid,depth=q.pop(0)
            if rid in seen: continue
            seen.add(rid); st=self.knowledge.get_validity(rid); candidates.append((depth,rid,st))
            for l in self.db.all("SELECT target_id FROM trace_links WHERE source_revision_id=? AND target_kind='REVISION' AND strength='HARD'",(rid,)):
                q.append((l["target_id"],depth+1))
        invalid=[x for x in candidates if x[2]!="VALID"]
        if not invalid: return None
        return max(invalid,key=lambda x:x[0])[1]

    def confirm_root(self, failure_id, root_revision_id, resume_target, actor_id):
        f=self.db.one("SELECT * FROM failures WHERE failure_id=?",(failure_id,));
        if not f: raise NotFound("Failure not found")
        self.gov.authorize(actor_id,"CONFIRM",{"failure_id":failure_id})
        self.db.conn.execute("UPDATE failures SET root_ref=?,root_revision_id=?,root_status='CONFIRMED',resume_candidate=? WHERE failure_id=?",(root_revision_id,root_revision_id,resume_target,failure_id)); self.db.conn.commit()
    def route_failure(self, failure_id):
        f=self.db.one("SELECT * FROM failures WHERE failure_id=?",(failure_id,));
        if not f: raise NotFound("Failure not found")
        ls=self.loop_status(f["project_id"],f["scope_id"],f["signature"])
        if ls and ls["status"]=="ESCALATE": return "ESCALATE"
        core={"TOOL_TIMEOUT":"RETRY","STALE_INPUT":"REVISE_UPSTREAM","AUTHORITY_DENIED":"ESCALATE","APPROVAL_MISSING":"WAIT","MISSING_EVIDENCE":"WAIT"}
        cfg=self.domain.failure(f["failure_class"])
        return core.get(f["failure_class"], cfg.get("default_decision","REVISE_CURRENT"))
    def diagnose_failure(self, failure_id):
        f=self.db.one("SELECT * FROM failures WHERE failure_id=?",(failure_id,))
        if not f: raise NotFound("Failure not found")
        return {"failure_id":failure_id,"root_status":f["root_status"],"root_ref":f["root_ref"],"resume_candidate":f["resume_candidate"],"recommended_decision":self.route_failure(failure_id)}
    def get_pending_decisions(self, project_id):
        return [dict(r) for r in self.db.all("SELECT * FROM decisions WHERE project_id=? AND decision_type IN ('WAIT','ESCALATE')",(project_id,))]
    def evaluate_loop_guard(self, failure_id):
        f=self.db.one("SELECT * FROM failures WHERE failure_id=?",(failure_id,))
        if not f: raise NotFound("Failure not found")
        return self.loop_status(f["project_id"],f["scope_id"],f["signature"])
    def resolve_failure(self, failure_id, evidence_ids=None):
        f=self.db.one("SELECT * FROM failures WHERE failure_id=?",(failure_id,))
        if not f: raise NotFound("Failure not found")
        self.db.conn.execute("UPDATE failures SET status='RESOLVED',resolved_at=? WHERE failure_id=?",(utcnow(),failure_id)); self.db.conn.commit()

    def compute_decision(self, project_id, scope_id):
        f=self.db.one("SELECT * FROM failures WHERE project_id=? AND scope_id=? AND status!='RESOLVED' ORDER BY created_at DESC LIMIT 1",(project_id,scope_id))
        if f:
            typ=self.route_failure(f["failure_id"]); did=self.create_decision(project_id,{"scope_id":scope_id},typ,[f["failure_class"]],source_failure_id=f["failure_id"],target_ref=f["resume_candidate"]); return did
        return self.create_decision(project_id,{"scope_id":scope_id},"CONTINUE",["NO_BLOCKING_FAILURE"])

    def create_recovery_plan(self, failure_id, impact_id, actor_id=None):
        f=self.db.one("SELECT * FROM failures WHERE failure_id=?",(failure_id,));
        if not f: raise NotFound("Failure not found")
        if f["root_status"]!="CONFIRMED": raise ValidationError("Root cause must be confirmed")
        impact=self.knowledge.get_impact(impact_id); invalid=[n["revision_id"] for n in impact["affected_nodes"] if n["action"] in {"INVALIDATE","MARK_STALE"}]; dirty=[n["revision_id"] for n in impact["affected_nodes"] if n["action"]=="MARK_DIRTY"]
        all_current=self.db.all("SELECT r.revision_id FROM revisions r JOIN artifacts a ON a.artifact_id=r.artifact_id WHERE a.project_id=? AND a.current_revision_id=r.revision_id",(f["project_id"],)); allids={r["revision_id"] for r in all_current}; keep=sorted(allids-set(invalid)-set(dirty))
        rid=uid("rec"); self.db.conn.execute("INSERT INTO recoveries VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(rid,f["project_id"],failure_id,f["root_revision_id"],f["resume_candidate"] or f["root_revision_id"],canonical_json(keep),canonical_json([]),canonical_json(invalid+dirty),canonical_json([{"revision_id":f["root_revision_id"],"action":"REVISE"}]),canonical_json([]),canonical_json([]),canonical_json([]),"AFTER_INVALIDATION","PLANNED",utcnow())); self.db.conn.execute("UPDATE failures SET status='RECOVERY_PLANNED' WHERE failure_id=?",(failure_id,)); self.gov.append_audit(f["project_id"],"SYSTEM","RECOVERY_PLANNED","RecoveryPlan",rid,reason_code=f["failure_class"]); self.db.conn.commit(); return rid
