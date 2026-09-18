from pathlib import Path
from gwr.runtime import GovernedWorkflowRuntime
from gwr.research_orchestrator import ResearchOrchestrator
from gwr.real_research import RealResearchExecutor, PaperWebRetriever, BinomialCoverageExperimentRunner, StatisticalVerifier, DEFAULT_PAPERS
from gwr.stat_verifier import SubprocessStatisticalVerifier

ROLES=['research_lead','literature_reviewer','protocol_designer','experimenter','analyst','adversarial_reviewer','reproducibility_reviewer']

def test_exact_coverage_known_behavior():
    r=BinomialCoverageExperimentRunner()
    m=r.run_grid([20],[0.05,0.50,0.95])
    assert len(m['rows'])==3
    assert all(0 <= x['wilson_coverage'] <= 1 for x in m['rows'])
    assert all(0 <= x['wald_coverage'] <= 1 for x in m['rows'])

def test_statistical_verifier_real_grid_passes():
    r=BinomialCoverageExperimentRunner(); v=StatisticalVerifier()
    m=r.run_grid([10,20,40],[round(i/100,2) for i in range(1,100)])
    out=v.verify(m,min_relative_reduction=0.20)
    assert out['pass'] is True
    assert out['relative_mae_reduction'] > 0.20
    assert out['sign_test_p_value'] < 0.05

def test_real_executor_end_to_end_with_semantic_recovery(tmp_path):
    root=Path(__file__).parents[1]
    rt=GovernedWorkflowRuntime(str(root/'domains'/'research.workflow.yaml'),str(tmp_path/'v03.db'))
    project=rt.create_project('real-v03-test')
    actors={role:rt.governance.create_actor('AGENT',role,[role],[project]) for role in ROLES}
    human=rt.governance.create_actor('HUMAN','approver',['human_approver'],[project])
    orch=ResearchOrchestrator(rt,actors,human_approver_id=human)
    ex=RealResearchExecutor(PaperWebRetriever(DEFAULT_PAPERS,allow_live=False),BinomialCoverageExperimentRunner(),SubprocessStatisticalVerifier(),force_live_retrieval_probe=False,recovery_demo=True)
    result=orch.start(project,ex,max_steps=300)
    assert result['status']=='COMPLETED'
    assert result['outcome']=='PASS'
    assert result['generation']==1
    failures=[dict(x) for x in rt.db.all('select * from failures where project_id=?',(project,))]
    assert any(x['failure_class']=='pilot_degenerate' and x['status']=='RESOLVED' for x in failures)
    assert rt.db.one("select count(*) n from recoveries where project_id=?",(project,))['n'] >= 1
    decision=orch._current_revision_by_type(project,'decision_record')['structured_payload']
    assert decision['outcome']=='PASS'
    rt.close()
