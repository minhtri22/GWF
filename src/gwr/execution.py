from __future__ import annotations
from .utils import uid, utcnow, canonical_json, content_hash, parse_json
from .errors import NotFound, ValidationError, InvalidTransition, IdempotencyConflict, StaleVersion

class ExecutionKernel:
    def __init__(self, db, domain, knowledge, decision, governance):
        self.db,self.domain,self.knowledge,self.decision,self.gov=db,domain,knowledge,decision,governance
        self.project_governance=None
    def bind_project_governance(self, service):
        self.project_governance=service
    def create_workunit(self, project_id, workunit_type, input_revision_ids, actor_id):
        if self.project_governance: self.project_governance.require_mutable(project_id)
        t=self.domain.workunit(workunit_type)
        if not t: raise ValidationError(f"Unknown workunit type {workunit_type}")
        self.gov.authorize(actor_id,"EXECUTE",{"workunit_type":workunit_type})
        wid=uid("wu"); retry=t.get("retry_policy",{"max_attempts":1})
        self.db.conn.execute("INSERT INTO workunits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(wid,project_id,workunit_type,canonical_json(input_revision_ids),canonical_json(t.get("outputs",[])),canonical_json(t.get("preconditions",[])),canonical_json(t.get("required_gate_types",[])),canonical_json(t.get("required_authorities",[])),canonical_json({"role":t.get("executor_role")}),canonical_json(t.get("execution_policy",{})),canonical_json(retry),canonical_json(t.get("recovery_policy",{})),canonical_json(t.get("resource_conflict_keys",[])),"PENDING",0)); self.gov.append_audit(project_id,actor_id,"CREATE_WORKUNIT","WorkUnit",wid); self.db.conn.commit(); return wid
    def recompute_readiness(self, workunit_id, gate_results=None):
        w=self.db.one("SELECT * FROM workunits WHERE workunit_id=?",(workunit_id,));
        if not w: raise NotFound("WorkUnit not found")
        blockers=[]
        for rid in parse_json(w["input_revision_ids"],[]):
            st=self.knowledge.get_validity(rid)
            if st!="VALID": blockers.append(f"INPUT_{st}:{rid}")
        required=parse_json(w["required_gates"],[])
        gate_results=gate_results or {}
        for g in required:
            if gate_results.get(g)!="PASS": blockers.append(f"GATE_NOT_PASS:{g}")
        role=parse_json(w["executor_selector"],{}).get("role")
        available=False
        for a in self.db.all("SELECT * FROM actors WHERE status='ACTIVE'"):
            if role and role not in parse_json(a["role_bindings"],[]): continue
            try:
                self.gov.authorize(a["actor_id"],"EXECUTE",{"project_id":w["project_id"],"workunit_type":w["workunit_type"]}); available=True; break
            except Exception: pass
        if not available: blockers.append("EXECUTOR_AUTHORITY_UNAVAILABLE")
        if self.db.one("SELECT 1 FROM failures WHERE scope_id=? AND status!='RESOLVED' LIMIT 1",(workunit_id,)): blockers.append("BLOCKING_FAILURE")
        status="READY" if not blockers else "BLOCKED"
        self.db.conn.execute("UPDATE workunits SET status=?,version=version+1 WHERE workunit_id=?",(status,workunit_id)); self.gov.append_audit(w["project_id"],"SYSTEM","WORKUNIT_READY" if status=="READY" else "WORKUNIT_BLOCKED","WorkUnit",workunit_id,reason_code=";".join(blockers) if blockers else "READY"); self.db.conn.commit(); return {"status":status,"blockers":blockers}
    def _idempotent(self,key,payload_hash):
        if not key:return None
        r=self.db.one("SELECT * FROM idempotency WHERE key=?",(key,));
        if not r:return None
        if r["payload_hash"]!=payload_hash: raise IdempotencyConflict("Idempotency key conflict")
        return parse_json(r["result_json"],{})
    def _store_idempotent(self,key,ph,result):
        if key:self.db.conn.execute("INSERT INTO idempotency VALUES(?,?,?,?)",(key,ph,canonical_json(result),utcnow()))
    def start_run(self, workunit_id, actor_id, expected_workunit_version, idempotency_key, correlation_id):
        ph=content_hash({"workunit_id":workunit_id,"actor_id":actor_id,"expected":expected_workunit_version}); old=self._idempotent(idempotency_key,ph)
        if old:return old
        w=self.db.one("SELECT * FROM workunits WHERE workunit_id=?",(workunit_id,));
        if not w: raise NotFound("WorkUnit not found")
        if self.project_governance: self.project_governance.require_mutable(w["project_id"])
        if w["version"]!=expected_workunit_version: raise StaleVersion("WorkUnit version mismatch")
        if w["status"]!="READY": raise InvalidTransition(f"WorkUnit is {w['status']}, not READY")
        self.gov.authorize(actor_id,"EXECUTE",{"workunit_type":w["workunit_type"]})
        # resource conflict
        keys=set(parse_json(w["resource_conflict_keys"],[]))
        if keys:
            for ar in self.db.all("SELECT wu.resource_conflict_keys FROM runs r JOIN workunits wu ON wu.workunit_id=r.workunit_id WHERE r.runtime_status='RUNNING'"):
                if keys & set(parse_json(ar["resource_conflict_keys"],[])): raise InvalidTransition("Resource conflict with active run")
        attempt=self.db.one("SELECT COUNT(*) c FROM runs WHERE workunit_id=?",(workunit_id,))["c"]+1
        max_attempts=int(parse_json(w["retry_policy"],{}).get("max_attempts",1))
        if attempt>max_attempts: raise InvalidTransition("Retry budget exhausted")
        rid=uid("run"); self.db.conn.execute("INSERT INTO runs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(rid,workunit_id,attempt,actor_id,w["input_revision_ids"],utcnow(),None,"RUNNING",None,canonical_json([]),canonical_json([]),None,correlation_id)); self.db.conn.execute("UPDATE workunits SET status='RUNNING',version=version+1 WHERE workunit_id=?",(workunit_id,)); self.gov.append_audit(w["project_id"],actor_id,"RUN_STARTED","ExecutionRun",rid,run_id=rid,correlation_id=correlation_id); result={"run_id":rid,"attempt_number":attempt}; self._store_idempotent(idempotency_key,ph,result); self.db.conn.commit(); return result
    def add_evidence(self, project_id, evidence_type, actor_id, subject_refs, payload, trust_class="AUTHORITATIVE", producer_run_id=None, *, evidence_id=None, commit=True):
        if trust_class not in {"AUTHORITATIVE","SUPPORTED","ADVISORY","UNTRUSTED"}: raise ValidationError("Invalid trust class")
        eid=evidence_id or uid("ev")
        self.db.conn.execute("INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?,?,?,?)",(eid,project_id,evidence_type,producer_run_id,actor_id,canonical_json(subject_refs),canonical_json(payload),content_hash(payload),utcnow(),canonical_json({}),trust_class))
        if producer_run_id:
            r=self.db.one("SELECT evidence_ids FROM runs WHERE run_id=?",(producer_run_id,))
            if not r: raise NotFound("Producer run not found")
            ids=parse_json(r["evidence_ids"],[])+[eid]; self.db.conn.execute("UPDATE runs SET evidence_ids=? WHERE run_id=?",(canonical_json(ids),producer_run_id))
        self.gov.append_audit(project_id,actor_id,"EVIDENCE_RECORDED","Evidence",eid,run_id=producer_run_id)
        if commit: self.db.conn.commit()
        return eid
    def finish_run(self, run_id, runtime_status, exit_metadata=None, await_gate=False):
        r=self.db.one("SELECT * FROM runs WHERE run_id=?",(run_id,));
        if not r: raise NotFound("Run not found")
        if r["runtime_status"]!="RUNNING": raise InvalidTransition("Run not RUNNING")
        meta=exit_metadata or {}
        next_status=("VERIFYING" if await_gate and runtime_status=="COMPLETED" else ("SUCCEEDED" if runtime_status=="COMPLETED" else "RECOVERY"))
        self.db.conn.execute("UPDATE runs SET runtime_status=?,finished_at=?,exit_metadata=? WHERE run_id=?",(runtime_status,utcnow(),canonical_json(meta),run_id)); self.db.conn.execute("UPDATE workunits SET status=?,version=version+1 WHERE workunit_id=?",(next_status,r["workunit_id"])); w=self.db.one("SELECT project_id FROM workunits WHERE workunit_id=?",(r["workunit_id"],)); self.gov.append_audit(w["project_id"],r["executor_actor_id"],"RUN_SUCCEEDED_RUNTIME" if runtime_status=="COMPLETED" else "RUN_FAILED_RUNTIME","ExecutionRun",run_id,run_id=run_id)
        if runtime_status!="COMPLETED" and meta.get("failure_class"):
            self.decision.record_failure(w["project_id"],r["workunit_id"],meta["failure_class"],"EXECUTION",run_id,evidence_ids=parse_json(r["evidence_ids"],[]),violations=[meta.get("reason","RUNTIME_FAILURE")])
        self.db.conn.commit()

    def prepare_for_execution(self, workunit_id):
        """Research/domain orchestrators use this for postcondition-gate workflows.

        It verifies input validity and executor availability but intentionally does not
        require completion gates to have already passed.
        """
        w=self.db.one("SELECT * FROM workunits WHERE workunit_id=?",(workunit_id,))
        if not w: raise NotFound("WorkUnit not found")
        blockers=[]
        for rid in parse_json(w["input_revision_ids"],[]):
            st=self.knowledge.get_validity(rid)
            if st!="VALID": blockers.append(f"INPUT_{st}:{rid}")
        role=parse_json(w["executor_selector"],{}).get("role")
        available=False
        for a in self.db.all("SELECT * FROM actors WHERE status='ACTIVE'"):
            if role and role not in parse_json(a["role_bindings"],[]): continue
            try:
                self.gov.authorize(a["actor_id"],"EXECUTE",{"project_id":w["project_id"],"workunit_type":w["workunit_type"]})
                available=True; break
            except Exception:
                pass
        if not available: blockers.append("EXECUTOR_AUTHORITY_UNAVAILABLE")
        status="READY" if not blockers else "BLOCKED"
        self.db.conn.execute("UPDATE workunits SET status=?,version=version+1 WHERE workunit_id=?",(status,workunit_id))
        self.gov.append_audit(w["project_id"],"SYSTEM","WORKUNIT_READY" if status=="READY" else "WORKUNIT_BLOCKED","WorkUnit",workunit_id,reason_code=";".join(blockers) if blockers else "READY")
        self.db.conn.commit()
        return {"status":status,"blockers":blockers}

    def finalize_workunit(self, workunit_id, gate_result, gate_id=None):
        w=self.db.one("SELECT * FROM workunits WHERE workunit_id=?",(workunit_id,))
        if not w: raise NotFound("WorkUnit not found")
        if gate_result=="PASS": status="SUCCEEDED"
        elif gate_result=="FAIL": status="RECOVERY"
        else: status="BLOCKED"
        self.db.conn.execute("UPDATE workunits SET status=?,version=version+1 WHERE workunit_id=?",(status,workunit_id))
        self.gov.append_audit(w["project_id"],"SYSTEM","WORKUNIT_FINALIZED","WorkUnit",workunit_id,reason_code=f"{gate_result}:{gate_id or ''}")
        self.db.conn.commit()
        return status

    def get_ready_workunits(self, project_id):
        return [dict(r) for r in self.db.all("SELECT * FROM workunits WHERE project_id=? AND status='READY'",(project_id,))]
    def cancel_run(self, run_id, actor_id, reason):
        r=self.db.one("SELECT * FROM runs WHERE run_id=?",(run_id,))
        if not r: raise NotFound("Run not found")
        self.gov.authorize(actor_id,"CANCEL",{"run_id":run_id})
        if r["runtime_status"]!="RUNNING": raise InvalidTransition("Only running run can be cancelled")
        self.db.conn.execute("UPDATE runs SET runtime_status='CANCELLED',finished_at=?,exit_metadata=? WHERE run_id=?",(utcnow(),canonical_json({"reason":reason}),run_id))
        self.db.conn.execute("UPDATE workunits SET status='CANCELLED',version=version+1 WHERE workunit_id=?",(r["workunit_id"],))
        w=self.db.one("SELECT project_id FROM workunits WHERE workunit_id=?",(r["workunit_id"],)); self.gov.append_audit(w["project_id"],actor_id,"RUN_CANCELLED","ExecutionRun",run_id,run_id=run_id,reason_code=reason); self.db.conn.commit()
    def get_execution_status(self, project_id):
        return {"workunits":[dict(r) for r in self.db.all("SELECT * FROM workunits WHERE project_id=?",(project_id,))],"runs":[dict(r) for r in self.db.all("SELECT r.* FROM runs r JOIN workunits w ON w.workunit_id=r.workunit_id WHERE w.project_id=?",(project_id,))]}

    def create_checkpoint(self, project_id, scope_id, runtime_metadata=None):
        valid=[]; dirty=[]; stale=[]
        for r in self.db.all("SELECT r.revision_id,r.validity_state FROM revisions r JOIN artifacts a ON a.artifact_id=r.artifact_id WHERE a.project_id=? AND a.current_revision_id=r.revision_id",(project_id,)):
            ({"VALID":valid,"DIRTY":dirty,"STALE":stale}.get(r["validity_state"],dirty)).append(r["revision_id"])
        active=[r["workunit_id"] for r in self.db.all("SELECT workunit_id FROM workunits WHERE project_id=? AND status='RUNNING'",(project_id,))]; completed=[r["workunit_id"] for r in self.db.all("SELECT workunit_id FROM workunits WHERE project_id=? AND status='SUCCEEDED'",(project_id,))]; failures=[r["failure_id"] for r in self.db.all("SELECT failure_id FROM failures WHERE project_id=? AND status!='RESOLVED'",(project_id,))]; pending=[r["decision_id"] for r in self.db.all("SELECT decision_id FROM decisions WHERE project_id=? AND decision_type IN ('WAIT','ESCALATE')",(project_id,))]; approvals=[r["proposal_id"] for r in self.db.all("SELECT proposal_id FROM proposals WHERE project_id=? AND status='PENDING_APPROVAL'",(project_id,))]
        last=self.db.one("SELECT event_id FROM audit_events WHERE project_id=? ORDER BY timestamp DESC LIMIT 1",(project_id,)); cid=uid("cp"); resumes=[]
        for f in self.db.all("SELECT resume_candidate FROM failures WHERE project_id=? AND resume_candidate IS NOT NULL AND status!='RESOLVED'",(project_id,)): resumes.append(f["resume_candidate"])
        self.db.conn.execute("INSERT INTO checkpoints VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(cid,project_id,scope_id,utcnow(),last["event_id"] if last else None,canonical_json(active),canonical_json(completed),canonical_json([]),canonical_json(valid),canonical_json(dirty),canonical_json(stale),canonical_json(failures),canonical_json(pending),canonical_json(approvals),canonical_json(resumes),canonical_json(runtime_metadata or {}))); system_actor=self.db.one("SELECT actor_id FROM actors WHERE actor_type='SYSTEM' LIMIT 1"); actor=system_actor["actor_id"] if system_actor else (self.db.one("SELECT actor_id FROM actors LIMIT 1")["actor_id"] if self.db.one("SELECT actor_id FROM actors LIMIT 1") else "SYSTEM"); self.gov.append_audit(project_id,actor,"CHECKPOINT_CREATED","Checkpoint",cid); self.db.conn.commit(); return cid
    def heartbeat_run(self, run_id):
        r=self.db.one("SELECT * FROM runs WHERE run_id=?",(run_id,))
        if not r: raise NotFound("Run not found")
        if r["runtime_status"]!="RUNNING": raise InvalidTransition("Heartbeat requires RUNNING run")
        w=self.db.one("SELECT project_id FROM workunits WHERE workunit_id=?",(r["workunit_id"],)); self.gov.append_audit(w["project_id"],r["executor_actor_id"],"RUN_HEARTBEAT","ExecutionRun",run_id,run_id=run_id); self.db.conn.commit()
    def apply_recovery_plan(self, recovery_id):
        rec=self.db.one("SELECT * FROM recoveries WHERE recovery_id=?",(recovery_id,))
        if not rec: raise NotFound("RecoveryPlan not found")
        if rec["status"] not in {"PLANNED","APPROVED"}: raise InvalidTransition("RecoveryPlan not executable")
        for rid in parse_json(rec["mark_stale_refs"],[]): self.knowledge.set_validity_system(rid,"STALE")
        for wid in parse_json(rec["required_workunits"],[]): self.db.conn.execute("UPDATE workunits SET status='RECOVERY',version=version+1 WHERE workunit_id=?",(wid,))
        self.db.conn.execute("UPDATE recoveries SET status='APPLIED' WHERE recovery_id=?",(recovery_id,)); self.db.conn.commit()
        return self.create_checkpoint(rec["project_id"],rec["failure_id"],{"recovery_id":recovery_id})
    def resume_from_checkpoint(self, checkpoint_id):
        plan=self.reconcile_checkpoint(checkpoint_id)
        c=self.db.one("SELECT * FROM checkpoints WHERE checkpoint_id=?",(checkpoint_id,)); actor=self.db.one("SELECT actor_id FROM actors LIMIT 1")
        if actor: self.gov.append_audit(c["project_id"],actor["actor_id"],"RESUME_STARTED","Checkpoint",checkpoint_id); self.db.conn.commit()
        plan["status"]="RESUME_RECONCILED"
        if actor: self.gov.append_audit(c["project_id"],actor["actor_id"],"RESUME_COMPLETED","Checkpoint",checkpoint_id); self.db.conn.commit()
        return plan

    def reconcile_checkpoint(self, checkpoint_id):
        c=self.db.one("SELECT * FROM checkpoints WHERE checkpoint_id=?",(checkpoint_id,));
        if not c: raise NotFound("Checkpoint not found")
        frontier=self.knowledge.get_validity_frontier(c["project_id"]); return {"checkpoint_id":checkpoint_id,"project_id":c["project_id"],"scope_id":c["scope_id"],"current_valid_revision_ids":frontier["valid"],"current_non_valid":frontier["non_valid"],"pending_approvals":[p["proposal_id"] for p in self.db.all("SELECT proposal_id FROM proposals WHERE project_id=? AND status='PENDING_APPROVAL'",(c["project_id"],))],"resume_candidates":parse_json(c["resume_candidates"],[]),"runtime_metadata":parse_json(c["runtime_metadata"],{})}
