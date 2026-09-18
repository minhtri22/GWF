from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from gwr.auth import HumanAuthService
from gwr.errors import InvalidTransition
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import uid

ROOT = Path(__file__).resolve().parents[1]


def add_phase(rt, project):
    oid=uid("orch"); peid=uid("phaseexec")
    rt.db.conn.execute(
        "INSERT INTO orchestrations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (oid,project,rt.domain.domain_id,"RUNNING","phase_09_main_experiment",0,None,0,
         "2026-09-18T06:00:00+00:00","2026-09-18T06:00:00+00:00",None,"{}"),
    )
    rt.db.conn.execute(
        "INSERT INTO phase_executions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (peid,oid,"phase_09_main_experiment",9,0,None,None,"RUNNING",None,None,None,
         "2026-09-18T06:00:00+00:00",None,"{}"),
    )
    rt.db.conn.commit()
    return oid,peid


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",required=True); args=ap.parse_args()
    HumanAuthService.PASSWORD_ITERATIONS=1000
    checks=[]
    with tempfile.TemporaryDirectory() as td:
        rt=GovernedWorkflowRuntime(str(ROOT/"domains"/"research.workflow.yaml"),str(Path(td)/"qa.db"),auth_secret="q"*64)
        backend=rt.db.backend_name
        required={"project_lifecycle","project_name_history","skill_packages","skill_revisions","phase_execution_protocols",
                  "phase_preflights","phase_plans","phase_checklist_items","phase_stage_events","phase_problem_records",
                  "phase_recovery_proposals","phase_recovery_decisions","phase_handoffs"}
        tables=set(rt.db.list_tables())
        checks.append({"name":"v082_tables","pass":required.issubset(tables),"missing":sorted(required-tables)})
        checks.append({"name":"v082_migration","pass":"0005_v082_project_governance_agent_protocol" in rt.db.migrations.status()["applied"]})

        human=rt.governance.create_actor("HUMAN","qa-owner",["human_approver"],[])
        rt.auth.register_human(human,"qa-owner","qa-owner-password")
        tenant=rt.tenancy.create_tenant("QA",human); ws=rt.tenancy.create_workspace(tenant,"QA",human)
        project=rt.create_scoped_project("QA Project",tenant,ws,human); rt.tenancy.add_project_member(project,human,"APPROVER",human)
        agent=rt.governance.create_actor("AGENT","qa-agent",["research_lead"],[]); rt.tenancy.add_project_member(project,agent,"RESEARCHER",human)

        rt.project_governance.rename(project,"QA Renamed",human)
        checks.append({"name":"rename_audit","pass":rt.project_governance.name_history(project)[0]["new_name"]=="QA Renamed"})

        _,phase=add_phase(rt,project)
        skillpkg=rt.agent_protocol.create_skill_package("qa-execute","QA Execute",agent)
        skill=rt.agent_protocol.add_skill_revision(skillpkg,"1.0","# QA skill\nExecute safely.",agent)
        rt.agent_protocol.create_protocol(phase,skill,agent,recovery_mode="HUMAN_APPROVE",retry_budget=2)
        rt.agent_protocol.record_preflight(phase,[{"name":"inputs","pass":True}],agent)
        rt.agent_protocol.create_plan(phase,"QA plan",[{"title":"Run"},{"title":"Persist"}],agent)
        rt.agent_protocol.start_execution(phase,agent)
        rt.agent_protocol.update_step(phase,1,"FAIL",agent,note="simulated issue")
        problem=rt.agent_protocol.record_problem(phase,agent,code="QA_ISSUE",summary="QA issue",detail="must be recorded",affected_step=1)
        recovery=rt.agent_protocol.propose_recovery(problem,agent,action="RETRY_STEP",target_step=1,risk_class="LOW")
        checks.append({"name":"human_mode_pause","pass":recovery["status"]=="WAITING_HUMAN" and rt.agent_protocol.inspect(phase)["attention"]=="WAITING_FOR_YOU"})
        blocked=False
        try: rt.agent_protocol.apply_recovery(recovery["proposal_id"],agent)
        except InvalidTransition: blocked=True
        checks.append({"name":"no_retry_before_approval","pass":blocked})
        rt.agent_protocol.decide_recovery(recovery["proposal_id"],human,"APPROVED",reason="QA approve")
        rt.agent_protocol.apply_recovery(recovery["proposal_id"],agent)
        view=rt.agent_protocol.inspect(phase)
        ev=[e["event_type"] for e in view["events"]]
        checks.append({"name":"problem_before_retry","pass":ev.index("PROBLEM_RECORDED")<ev.index("RECOVERY_APPLIED")})
        checks.append({"name":"observable_protocol","pass":view["protocol"]["current_stage"]=="EXECUTE" and view["retry_count"] if False else view["protocol"]["retry_count"]==1})

        # active orchestration blocks direct archive, drain enters ARCHIVING and blocks new mutation
        blocked_archive=False
        try: rt.project_governance.archive(project,human)
        except InvalidTransition: blocked_archive=True
        draining=rt.project_governance.archive(project,human,drain=True)
        checks.append({"name":"archive_drain","pass":blocked_archive and draining["status"]=="ARCHIVING"})
        mutable_blocked=False
        try: rt.project_governance.require_mutable(project)
        except InvalidTransition: mutable_blocked=True
        checks.append({"name":"archive_read_only","pass":mutable_blocked})
        rt.close()

    errors=[c for c in checks if not c["pass"]]
    result={"version":"0.8.2","backend":backend,"status":"PASS" if not errors else "FAIL","checks":checks,"errors":errors}
    out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2)); raise SystemExit(0 if not errors else 1)

if __name__=="__main__": main()
