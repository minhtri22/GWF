from __future__ import annotations
from pathlib import Path
from .db import create_database
from .domain import load_domain, DomainPackage
from .governance import GovernanceKernel
from .knowledge import KnowledgeKernel
from .decision import DecisionKernel
from .execution import ExecutionKernel
from .utils import uid, utcnow
from .auth import HumanAuthService
from .object_store import LocalContentAddressedStore, ObjectRefService
from .observability import NullObserver, JsonlObserver
from .tenancy import TenantService
from .distributed import DistributedRuntime
from .domain_registry import DomainRegistryService
from .process_inspector import ProcessInspectorService
from .project_governance import ProjectGovernanceService
from .agent_protocol import AgentExecutionProtocolService
from .plugins import PluginConnectionService
from .github_plugin import GitHubPluginService
from .document_facade import DocumentFacadeService
from .document_qa import DocumentQAService
from .document_state import DocumentLifecycleValidityService
from .document_authority import DocumentAuthorityService
from .document_relation import DocumentRelationService

class GovernedWorkflowRuntime:
    def __init__(self, domain: str|DomainPackage, db_path=":memory:", *, auth_secret=None, object_store_root=None, observer=None, observability_path=None):
        self.domain=load_domain(domain) if not isinstance(domain,DomainPackage) else domain
        self.db=create_database(db_path)
        if observer is not None:
            self.observer=observer
        elif observability_path:
            self.observer=JsonlObserver(observability_path)
        else:
            self.observer=NullObserver()
        self.governance=GovernanceKernel(self.db,self.domain); self.governance.install_domain_policies()
        self.auth=HumanAuthService(self.db, auth_secret)
        self.tenancy=TenantService(self.db)
        self.governance.bind_auth(self.auth)
        self.governance.bind_tenancy(self.tenancy)
        if not self.db.one("SELECT 1 FROM actors WHERE actor_id='SYSTEM'"):
            self.db.conn.execute("INSERT INTO actors VALUES(?,?,?,?,?,?,?)",("SYSTEM","SYSTEM","runtime",'["system"]','["*"]',"ACTIVE",'{}')); self.db.conn.commit()
        self.knowledge=KnowledgeKernel(self.db,self.domain,self.governance)
        self.decision=DecisionKernel(self.db,self.domain,self.knowledge,self.governance)
        self.execution=ExecutionKernel(self.db,self.domain,self.knowledge,self.decision,self.governance)
        self.distributed=DistributedRuntime(self.db,self.execution,self.governance,self.observer)
        self.domains=DomainRegistryService(self.db,self.tenancy)
        self.project_governance=ProjectGovernanceService(self.db,self.tenancy,self.governance)
        self.governance.bind_project_governance(self.project_governance)
        self.knowledge.bind_project_governance(self.project_governance)
        self.execution.bind_project_governance(self.project_governance)
        self.distributed.bind_project_governance(self.project_governance)
        self.agent_protocol=AgentExecutionProtocolService(self.db,self.governance,self.project_governance,self.domain)
        self.agent_protocol.bootstrap_domain_skills()
        self.plugins=PluginConnectionService(self.db,self.governance,self.tenancy,self.project_governance)
        self.github=GitHubPluginService(self.db,self.governance,self.tenancy,self.project_governance,self.plugins)
        self.document_qa=DocumentQAService(
            self.db,
            self.domain,
            self.knowledge,
            self.execution,
            self.governance,
            self.project_governance,
        )
        self.document_state=DocumentLifecycleValidityService(
            self.db,
            self.knowledge,
            self.document_qa,
            self.governance,
            self.project_governance,
        )
        self.document_authority=DocumentAuthorityService(
            self.db,
            self.knowledge,
            self.document_qa,
            self.governance,
            self.project_governance,
        )
        self.document_relations=DocumentRelationService(
            self.db,
            self.knowledge,
            self.governance,
            self.project_governance,
        )
        self.documents=DocumentFacadeService(self.knowledge,self.github,self.document_state)
        self.process=ProcessInspectorService(self)
        self.object_store=None; self.objects=None
        if object_store_root:
            self.object_store=LocalContentAddressedStore(object_store_root)
            self.objects=ObjectRefService(self.db,self.object_store)
        self.observe("runtime_initialized", backend=getattr(self.db,"backend_name","unknown"), domain_id=self.domain.domain_id)
    def observe(self,event,**attrs):
        return self.observer.emit(event,**attrs)
    def create_project(self,name,project_id=None):
        pid=project_id or uid("project")
        self.db.conn.execute("INSERT INTO projects VALUES(?,?,?,?)",(pid,name,self.domain.domain_id,utcnow()))
        self.db.conn.execute("INSERT INTO project_lifecycle VALUES(?,?,?,?,?,?,?)",(pid,"ACTIVE",None,None,None,None,utcnow()))
        self.db.conn.commit()
        self.observe("project_created",project_id=pid,domain_id=self.domain.domain_id)
        return pid
    def create_scoped_project(self,name,tenant_id,workspace_id,actor_id,project_id=None,domain_revision_id=None):
        pid=self.create_project(name,project_id=project_id)
        self.tenancy.bind_project(pid,tenant_id,workspace_id,actor_id)
        if domain_revision_id:
            self.domains.pin_project(pid,domain_revision_id,actor_id)
        self.observe("scoped_project_created",project_id=pid,tenant_id=tenant_id,workspace_id=workspace_id,actor_id=actor_id,domain_revision_id=domain_revision_id)
        return pid
    def attach_blob(self,project_id,owner_kind,owner_id,data,content_type="application/octet-stream"):
        if not self.objects: raise RuntimeError("object store is not configured")
        ref=self.objects.attach_bytes(project_id,owner_kind,owner_id,data,content_type=content_type); self.observe("object_attached",project_id=project_id,owner_kind=owner_kind,owner_id=owner_id,sha256=ref["sha256"],size_bytes=ref["size_bytes"]); return ref
    def commit_approved_proposal(self, proposal_id, actor_id, expected_version=0):
        p=self.governance.require_approved(proposal_id)
        if p["action"]=="CREATE_REVISION": return self.knowledge.commit_revision_from_proposal(proposal_id,actor_id,expected_version)
        if p["action"] in {"DECLARE_DOCUMENT_AUTHORITY","DECLARE_COMPOSED_DOCUMENT_AUTHORITY","RETIRE_DOCUMENT_AUTHORITY"}:
            return self.document_authority.apply_approved_proposal(proposal_id,actor_id)
        if p["action"] in {"DECLARE_DOCUMENT_RELATION","RETIRE_DOCUMENT_RELATION"}:
            return self.document_relations.apply_approved_proposal(proposal_id,actor_id)
        raise ValueError(f"No runtime dispatcher for proposal action {p['action']}")
    def close(self):
        self.observe("runtime_closed")
        self.db.close()
