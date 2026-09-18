from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import yaml
from .errors import ValidationError

PRIMITIVES = {"PRIM-ARTIFACT","PRIM-REVISION","PRIM-TRACE","PRIM-VALIDITY","PRIM-IMPACT","PRIM-WORKUNIT","PRIM-RUN","PRIM-CHECKPOINT","PRIM-EVIDENCE","PRIM-GATE","PRIM-DECISION","PRIM-FAILURE","PRIM-RECOVERY","PRIM-LOOPGUARD","PRIM-ACTOR","PRIM-AUTHORITY","PRIM-APPROVAL","PRIM-AUDIT","PRIM-DOMAIN"}

@dataclass
class DomainPackage:
    data: dict
    @property
    def domain_id(self): return self.data["domain_id"]
    def artifact(self, type_id):
        return next((x for x in self.data.get("artifact_types",[]) if x["id"]==type_id), None)
    def trace(self, type_id):
        return next((x for x in self.data.get("trace_types",[]) if x["id"]==type_id), None)
    def workunit(self, type_id):
        return next((x for x in self.data.get("workunit_templates",[]) if x["id"]==type_id), None)
    def gate(self, type_id):
        return next((x for x in self.data.get("gate_types",[]) if x["id"]==type_id), None)
    def failure(self, type_id):
        return next((x for x in self.data.get("failure_types",[]) if x["id"]==type_id), None)
    def approval_policy(self, policy_id):
        return next((x for x in self.data.get("approval_policies",[]) if x["id"]==policy_id), None)
    def workunits(self):
        return list(self.data.get("workunit_templates",[]) or [])
    def evidence(self, type_id):
        return next((x for x in self.data.get("evidence_types",[]) if x["id"]==type_id), None)
    def recovery_policy(self, failure_type):
        return next((x for x in self.data.get("recovery_policies",[]) if x.get("failure_type")==failure_type), None)
    def validate_artifact_payload(self, artifact_type, payload):
        cfg=self.artifact(artifact_type)
        if not cfg: raise ValidationError(f"Unknown artifact type {artifact_type}")
        if not isinstance(payload,dict): raise ValidationError(f"Artifact {artifact_type} payload must be an object")
        missing=[k for k in cfg.get("required_fields",[]) if k not in payload]
        if missing: raise ValidationError(f"Artifact {artifact_type} missing required fields", details={"missing":missing})
        if cfg.get("allowed_outcomes") and payload.get("outcome") not in cfg["allowed_outcomes"]:
            raise ValidationError(f"Artifact {artifact_type} has invalid outcome", details={"allowed":cfg["allowed_outcomes"],"actual":payload.get("outcome")})
        return True


def load_domain(path: str | Path) -> DomainPackage:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    validate_domain(data)
    return DomainPackage(data)

def validate_domain(d: dict) -> None:
    required=["domain_id","version","artifact_types","trace_types","workunit_templates","gate_types","failure_types","recovery_policies","roles","authority_policies","approval_policies"]
    missing=[k for k in required if k not in d]
    if missing: raise ValidationError("Domain package missing required fields", details={"missing":missing})
    for section in ["artifact_types","trace_types","workunit_templates","evidence_types","gate_types","failure_types","recovery_policies","roles","authority_policies","approval_policies"]:
        for item in d.get(section,[]) or []:
            m=item.get("maps_to")
            if m and m not in PRIMITIVES: raise ValidationError(f"Unknown primitive {m}")
    arts={x["id"] for x in d.get("artifact_types",[])}
    gates={x["id"] for x in d.get("gate_types",[])}
    failures={x["id"] for x in d.get("failure_types",[])}
    approvals={x["id"] for x in d.get("approval_policies",[])}
    for a in d.get("artifact_types",[]):
        if a.get("normative") and not a.get("approval_policy"):
            raise ValidationError(f"Normative artifact {a['id']} lacks approval_policy")
        if a.get("approval_policy") and a["approval_policy"] not in approvals:
            raise ValidationError(f"Unknown approval policy {a['approval_policy']}")
    for t in d.get("trace_types",[]):
        if t.get("strength")=="HARD" and "invalidates_on_upstream_supersede" not in t:
            raise ValidationError(f"Hard trace {t['id']} lacks invalidation behavior")
    for w in d.get("workunit_templates",[]):
        for inp in w.get("inputs",[]):
            typ=inp["artifact_type"] if isinstance(inp,dict) else inp
            if typ not in arts: raise ValidationError(f"Workunit {w['id']} references unknown artifact {typ}")
        for out in w.get("outputs",[]):
            typ=out["artifact_type"] if isinstance(out,dict) else out
            if typ not in arts: raise ValidationError(f"Workunit {w['id']} references unknown artifact {typ}")
        if not w.get("required_gate_types") and not w.get("no_gate",False): raise ValidationError(f"Workunit {w['id']} lacks success/readiness gate")
        required_contract=["evidence_required","success_conditions","known_failure_modes","retry_policy","recovery_policy","idempotency_semantics"]
        miss=[k for k in required_contract if k not in w]
        if miss: raise ValidationError(f"Workunit {w['id']} incomplete contract: {miss}")
        for g in w.get("required_gate_types",[]):
            if g not in gates: raise ValidationError(f"Workunit {w['id']} references unknown gate {g}")
    rec_fail={x.get("failure_type") for x in d.get("recovery_policies",[])}
    for f in d.get("failure_types",[]):
        if f.get("retryable") and not f.get("retry_budget") and not d.get("loop_policy",{}).get("same_signature_limit"):
            raise ValidationError(f"Retryable failure {f['id']} lacks retry budget")
        if f["id"] not in failures: raise ValidationError("internal failure registry error")
    for r in d.get("recovery_policies",[]):
        if r.get("failure_type") not in failures: raise ValidationError(f"Recovery references unknown failure {r.get('failure_type')}")
    # detect arbitrary hard dependency cycles in declared artifact dependency rules if present
    graph={a["id"]:list(a.get("hard_dependencies",[])) for a in d.get("artifact_types",[])}
    visiting=set(); visited=set()
    def dfs(n,path):
        if n in visiting: raise ValidationError("Circular hard dependency: "+" -> ".join(path+[n]))
        if n in visited: return
        visiting.add(n)
        for m in graph.get(n,[]): dfs(m,path+[n])
        visiting.remove(n); visited.add(n)
    for n in graph: dfs(n,[])
    for r in d.get("recovery_policies",[]):
        if r.get("high_impact") and not r.get("approval_policy"):
            raise ValidationError(f"High-impact recovery for {r.get('failure_type')} lacks approval_policy")
