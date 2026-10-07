from __future__ import annotations

import argparse, json, os, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def run(cmd,*,env,log):
    p=subprocess.run(cmd,cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    Path(log).parent.mkdir(parents=True,exist_ok=True); Path(log).write_text(p.stdout,encoding="utf-8"); print(p.stdout,end="")
    if p.returncode: raise RuntimeError(f"command failed ({p.returncode}): {cmd}")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--postgres-url",default=os.environ.get("GWR_TEST_DATABASE_URL")); ap.add_argument("--out",default=str(ROOT/"evidence"/"v0.8.2"/"live_gate")); a=ap.parse_args()
    if not a.postgres_url: raise SystemExit("v0.8.2 live gate requires PostgreSQL URL")
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    base=os.environ.copy(); base.pop("GWR_TEST_DATABASE_URL",None); base.pop("GWR_TEST_NAMESPACE_PREFIX",None)
    pg=base.copy(); pg["GWR_TEST_DATABASE_URL"]=a.postgres_url; pg["GWR_TEST_NAMESPACE_PREFIX"]="gwr_v082_gate"

    run([sys.executable,"tools/run_v081_gate.py","--postgres-url",a.postgres_url,"--out",str(out/"v081_regression")],env=base,log=out/"v081_regression.log")
    run([sys.executable,"-m","pytest","-q","tests/test_v082_project_governance_agent_protocol.py"],env=base,log=out/"v082_sqlite_tests.txt")
    run([sys.executable,"tools/qa_v082.py","--out",str(out/"QA_SQLITE.json")],env=base,log=out/"qa_sqlite.log")
    run([sys.executable,"-m","pytest","-q","tests/test_v082_project_governance_agent_protocol.py"],env=pg,log=out/"v082_postgres_tests.txt")
    run([sys.executable,"tools/qa_v082.py","--out",str(out/"QA_POSTGRES.json")],env=pg,log=out/"qa_postgres.log")
    site=out/"uat_site"
    run([sys.executable,"tools/build_uat_site.py","--out",str(site),"--commit",os.environ.get("GITHUB_SHA","gate")],env=base,log=out/"uat_build.log")
    run([sys.executable,"-m","compileall","-q","src","tests","tools"],env=base,log=out/"compileall.txt")

    prior=json.loads((out/"v081_regression"/"V081_GATE.json").read_text())
    qs=json.loads((out/"QA_SQLITE.json").read_text()); qp=json.loads((out/"QA_POSTGRES.json").read_text())
    meta=json.loads((site/"build-meta.json").read_text(encoding="utf-8")); html=(site/"index.html").read_text(encoding="utf-8"); js=(site/"app.js").read_text(encoding="utf-8"); css=(site/"styles.css").read_text(encoding="utf-8")
    shell_boundary=(meta.get("mode")=="STATIC_SHELL_SNAPSHOT" and meta.get("slice")=="BPS-I00" and meta.get("authoritative_backend") is False and "Governed Knowledge Studio" in html and "/browser/bootstrap" in js and all(m not in js for m in ("simulateProtocolIssue","approveProtocolRecovery","renameCurrentProject","archiveCurrentProject","gwr-uat-projects")))
    def q(q,name): return next(c["pass"] for c in q["checks"] if c["name"]==name)
    result={
      "version":"0.8.2","status":"PASS","v081_regression_pass":prior.get("status")=="PASS","postgres_live_tested":True,
      "sqlite_v082_pass":qs.get("status")=="PASS","postgres_v082_pass":qp.get("status")=="PASS",
      "project_governance_pass":all(q(x,"rename_audit") and q(x,"archive_drain") and q(x,"archive_read_only") for x in (qs,qp)),
      "observable_agent_protocol_pass":all(q(x,"observable_protocol") and q(x,"problem_before_retry") for x in (qs,qp)),
      "human_recovery_mode_pass":all(q(x,"human_mode_pause") and q(x,"no_retry_before_approval") for x in (qs,qp)),
      # Compatibility key now validates absence of legacy simulated mutation UX.
      "uat_observability_ui_pass":shell_boundary,
      "static_shell_boundary_pass":shell_boundary,
      "authoritative_browser_uat":False,
      "ready_for_uat":False,
    }
    required=[v for k,v in result.items() if k.endswith("_pass")]
    result["status"]="PASS" if all(required) else "FAIL"; result["ready_for_uat"]=False
    (out/"V082_GATE.json").write_text(json.dumps(result,indent=2),encoding="utf-8"); print(json.dumps(result,indent=2))
    raise SystemExit(0 if result["status"]=="PASS" else 1)
if __name__=="__main__": main()
