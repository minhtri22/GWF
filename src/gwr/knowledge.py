from __future__ import annotations
from collections import deque
from .utils import uid, utcnow, canonical_json, content_hash, parse_json
from .errors import NotFound, ValidationError, StaleVersion

VALIDITY={"VALID","STALE","DIRTY","FAILED","UNVERIFIED","SUPERSEDED"}
class KnowledgeKernel:
    def __init__(self, db, domain, governance):
        self.db,self.domain,self.gov=db,domain,governance
        self.project_governance=None
    def bind_project_governance(self, service):
        self.project_governance=service
    def create_artifact(self, project_id, artifact_type, logical_key, actor_id, lifecycle_status="ACTIVE"):
        if self.project_governance: self.project_governance.require_mutable(project_id)
        if not self.domain.artifact(artifact_type): raise ValidationError(f"Unknown artifact type {artifact_type}")
        self.gov.authorize(actor_id,"CREATE_REVISION",{"artifact_type":artifact_type})
        aid=uid("art")
        self.db.conn.execute("INSERT INTO artifacts VALUES(?,?,?,?,?,?,?,?,?)",(aid,project_id,artifact_type,logical_key,utcnow(),actor_id,None,lifecycle_status,0)); self.gov.append_audit(project_id,actor_id,"CREATE_ARTIFACT","Artifact",aid); self.db.conn.commit(); return aid
    def commit_revision_from_proposal(self, proposal_id, actor_id, expected_artifact_version:int):
        p=self.gov.require_approved(proposal_id); payload=parse_json(p["frozen_payload"],{})
        if p["action"]!="CREATE_REVISION": raise ValidationError("Proposal action is not CREATE_REVISION")
        return self.create_revision(payload["artifact_id"], payload["payload"], actor_id, expected_artifact_version, proposal_id=proposal_id)
    def create_revision(self, artifact_id, payload, actor_id, expected_artifact_version:int, proposal_id=None, producer_run_id=None):
        a=self.db.one("SELECT * FROM artifacts WHERE artifact_id=?",(artifact_id,));
        if not a: raise NotFound("Artifact not found")
        if self.project_governance: self.project_governance.require_mutable(a["project_id"])
        self.gov.authorize(actor_id,"CREATE_REVISION",{"artifact_type":a["artifact_type"]})
        art_cfg=self.domain.artifact(a["artifact_type"])
        if art_cfg.get("normative") and not proposal_id: raise ValidationError("Normative revision requires approved proposal")
        if proposal_id: self.gov.require_approved(proposal_id)
        if a["version"]!=expected_artifact_version: raise StaleVersion("Artifact version mismatch",details={"expected":expected_artifact_version,"actual":a["version"]})
        prev=a["current_revision_id"]; num=(self.db.one("SELECT COALESCE(MAX(revision_number),0) m FROM revisions WHERE artifact_id=?",(artifact_id,))["m"]+1)
        rid=uid("rev"); validity="UNVERIFIED"
        self.db.conn.execute("INSERT INTO revisions VALUES(?,?,?,?,?,?,?,?,?,?)",(rid,artifact_id,num,canonical_json(payload),content_hash(payload),actor_id,utcnow(),prev,"CURRENT",validity))
        if prev:
            self.db.conn.execute("UPDATE revisions SET status='SUPERSEDED', validity_state='SUPERSEDED' WHERE revision_id=?",(prev,))
        self.db.conn.execute("UPDATE artifacts SET current_revision_id=?, version=version+1 WHERE artifact_id=?",(rid,artifact_id))
        if producer_run_id:
            self.create_trace_link(a["project_id"],rid,"RUN",producer_run_id,"PRODUCED_BY","INFORMATIONAL",False,"NONE",actor_id,skip_auth=True)
            run=self.db.one("SELECT produced_revision_ids FROM runs WHERE run_id=?",(producer_run_id,))
            if run:
                produced=parse_json(run["produced_revision_ids"],[])
                if rid not in produced:
                    produced.append(rid)
                    self.db.conn.execute("UPDATE runs SET produced_revision_ids=? WHERE run_id=?",(canonical_json(produced),producer_run_id))
        eid=self.gov.append_audit(a["project_id"],actor_id,"CREATE_REVISION","Revision",rid,before_version=prev,after_version=rid,proposal_id=proposal_id,run_id=producer_run_id)
        if proposal_id: self.db.conn.execute("UPDATE proposals SET status='COMMITTED' WHERE proposal_id=?",(proposal_id,))
        self.db.conn.commit()
        impact=None
        if prev: impact=self.compute_impact(a["project_id"],"REVISION_SUPERSEDED",prev,prev,apply=True)
        return {"revision_id":rid,"audit_event_id":eid,"impact_id":impact["impact_id"] if impact else None}
    def create_trace_link(self, project_id, source_revision_id, target_kind, target_id, relation_type, strength, invalidates, propagation_rule, actor_id, skip_auth=False):
        if not skip_auth: self.gov.authorize(actor_id,"CREATE_REVISION",{"trace":relation_type})
        cfg=self.domain.trace(relation_type.lower()) or self.domain.trace(relation_type) or {}
        if strength not in {"HARD","SOFT","INFORMATIONAL"}: raise ValidationError("Invalid trace strength")
        tid=uid("trace"); self.db.conn.execute("INSERT INTO trace_links VALUES(?,?,?,?,?,?,?,?,?,?)",(tid,project_id,source_revision_id,target_kind,target_id,relation_type,strength,1 if invalidates else 0,propagation_rule,utcnow())); self.gov.append_audit(project_id,actor_id,"CREATE_TRACE","TraceLink",tid,reason_code=relation_type); self.db.conn.commit(); return tid
    def get_artifact(self, artifact_id):
        r=self.db.one("SELECT * FROM artifacts WHERE artifact_id=?",(artifact_id,));
        if not r: raise NotFound("Artifact not found")
        return dict(r)
    def get_revision(self, revision_id):
        r=self.db.one("SELECT * FROM revisions WHERE revision_id=?",(revision_id,));
        if not r: raise NotFound("Revision not found")
        d=dict(r); d["structured_payload"]=parse_json(d["structured_payload"],{}); return d
    def get_current_revision(self, artifact_id): return self.get_revision(self.get_artifact(artifact_id)["current_revision_id"])
    def get_validity(self, revision_id): return self.get_revision(revision_id)["validity_state"]
    def set_validity_system(self, revision_id, state):
        if state not in VALIDITY: raise ValidationError("Invalid validity state")
        self.db.conn.execute("UPDATE revisions SET validity_state=? WHERE revision_id=?",(state,revision_id)); self.db.conn.commit()
    def compute_impact(self, project_id, trigger_type, trigger_id, root_revision_id, apply=False):
        # links point downstream source -> upstream target; traverse rows whose target is current upstream revision
        q=deque([(root_revision_id,[root_revision_id])]); seen={root_revision_id}; affected=[]
        while q:
            upstream,path=q.popleft()
            rows=self.db.all("SELECT * FROM trace_links WHERE project_id=? AND target_kind='REVISION' AND target_id=?",(project_id,upstream))
            for l in rows:
                src=l["source_revision_id"]
                if src in seen: continue
                seen.add(src); newpath=path+[src]
                if l["strength"]=="HARD" and l["invalidates_on_upstream_supersede"]:
                    action="MARK_STALE"
                elif l["strength"]=="SOFT": action="MARK_DIRTY"
                else: action="KEEP"
                affected.append({"revision_id":src,"action":action,"reason":f"{l['relation_type']}:{trigger_type}","trace_path":newpath})
                if action in {"MARK_STALE","MARK_DIRTY","INVALIDATE"}: q.append((src,newpath))
        iid=uid("impact")
        self.db.conn.execute("INSERT INTO impacts VALUES(?,?,?,?,?,?,?,?,?)",(iid,project_id,trigger_type,trigger_id,root_revision_id,canonical_json(affected),canonical_json([trigger_type]),utcnow(),"core-0.1"))
        if apply:
            for n in affected:
                if n["action"]=="MARK_STALE": self.db.conn.execute("UPDATE revisions SET validity_state='STALE' WHERE revision_id=? AND validity_state!='SUPERSEDED'",(n["revision_id"],))
                elif n["action"]=="MARK_DIRTY": self.db.conn.execute("UPDATE revisions SET validity_state='DIRTY' WHERE revision_id=? AND validity_state NOT IN ('STALE','SUPERSEDED')",(n["revision_id"],))
        self.gov.append_audit(project_id,"SYSTEM","IMPACT_COMPUTED","ImpactSet",iid,reason_code=trigger_type); self.db.conn.commit(); return {"impact_id":iid,"affected_nodes":affected}
    def get_impact(self, impact_id):
        r=self.db.one("SELECT * FROM impacts WHERE impact_id=?",(impact_id,));
        if not r: raise NotFound("Impact not found")
        d=dict(r); d["affected_nodes"]=parse_json(d["affected_nodes"],[]); return d

    def get_trace_graph(self, root_revision_id, depth=10):
        # Query both dependency directions while preserving edge semantics.
        seen={root_revision_id}; frontier=[(root_revision_id,0)]; edges=[]
        while frontier:
            node,d=frontier.pop(0)
            if d>=depth: continue
            rows=self.db.all("SELECT * FROM trace_links WHERE source_revision_id=? OR (target_kind='REVISION' AND target_id=?)",(node,node))
            for r in rows:
                edge=dict(r); edges.append(edge)
                other=r["target_id"] if r["source_revision_id"]==node and r["target_kind"]=='REVISION' else r["source_revision_id"]
                if other not in seen:
                    seen.add(other); frontier.append((other,d+1))
        return {"root_revision_id":root_revision_id,"nodes":sorted(seen),"edges":edges}
    def get_affected_subgraph(self, impact_id):
        imp=self.get_impact(impact_id)
        return {"impact_id":impact_id,"root_revision_id":imp["root_revision_id"],"affected_nodes":imp["affected_nodes"]}

    def get_validity_frontier(self, project_id):
        rows=self.db.all("SELECT r.revision_id,r.validity_state FROM revisions r JOIN artifacts a ON a.artifact_id=r.artifact_id WHERE a.project_id=? AND a.current_revision_id=r.revision_id",(project_id,))
        return {"valid":[r["revision_id"] for r in rows if r["validity_state"]=="VALID"],"non_valid":[dict(r) for r in rows if r["validity_state"]!="VALID"]}
