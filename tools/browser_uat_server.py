from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from fastapi.responses import HTMLResponse

from gwr.api import create_app
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import uid, utcnow

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HEAD = "a09f79ae74a838d2c5998813560373c849669872"

HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GWF Live Browser UAT</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:0;background:#f6f7f9;color:#17202a}
main{max-width:1100px;margin:28px auto;padding:0 18px}
h1{margin-bottom:4px}.muted{color:#667085}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.card{background:#fff;border:1px solid #dfe3e8;border-radius:10px;padding:16px;margin:14px 0}
.ok{color:#067647;font-weight:700}.bad{color:#b42318;font-weight:700}.warn{color:#b54708;font-weight:700}
button{padding:9px 13px;margin:4px 4px 4px 0;border:1px solid #98a2b3;border-radius:7px;background:#fff;cursor:pointer}
button.primary{background:#175cd3;color:#fff;border-color:#175cd3}
input{padding:9px;border:1px solid #98a2b3;border-radius:7px;width:100%;box-sizing:border-box;margin:4px 0 8px}
pre{background:#101828;color:#eaecf0;padding:12px;border-radius:8px;overflow:auto;max-height:420px}
code{background:#eef2f6;padding:2px 5px;border-radius:4px}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:8px;border-bottom:1px solid #eaecf0}
</style>
</head>
<body>
<main>
<h1>GWF Live Browser UAT</h1>
<p class="muted">This page talks to the live FastAPI runtime on localhost. It is not the static demo site.</p>

<div class="card">
<h2>Runtime identity</h2>
<div id="identity">Loading...</div>
<p><a href="/docs" target="_blank">Open live FastAPI /docs</a> · <a href="/openapi.json" target="_blank">Open OpenAPI JSON</a></p>
</div>

<div class="grid">
<div class="card">
<h2>1. Health</h2>
<button class="primary" onclick="health()">GET /health</button>
<pre id="healthOut"></pre>
</div>

<div class="card">
<h2>2. Login</h2>
<label>Username</label><input id="user" value="operator">
<label>Password</label><input id="pass" type="password" value="operator-password-long">
<button class="primary" onclick="login()">POST /auth/login</button>
<div id="loginState" class="muted">Not logged in</div>
</div>
</div>

<div class="card">
<h2>3. Live product API</h2>
<button onclick="listProjects()">List projects</button>
<button onclick="loadDashboard()">Load seeded dashboard</button>
<button onclick="renameProject()">Rename seeded project</button>
<button onclick="archiveProject()">Archive seeded project</button>
<button onclick="restoreProject()">Restore seeded project</button>
<pre id="apiOut"></pre>
</div>

<div class="card">
<h2>4. Browser-UAT coverage</h2>
<table>
<thead><tr><th>Area</th><th>Live HTTP/browser surface</th><th>Interpretation</th></tr></thead>
<tbody id="coverage"></tbody>
</table>
<p class="muted">A NOT_EXPOSED row means the implementation may exist in the runtime service layer, but this formal-close product does not yet provide a product HTTP endpoint for browser UAT of that capability.</p>
</div>

<div class="card">
<h2>5. UAT decision</h2>
<p>Record what you observe in the browser:</p>
<label><input type="checkbox" id="c1" style="width:auto"> Server starts and health is OK</label><br>
<label><input type="checkbox" id="c2" style="width:auto"> Login succeeds</label><br>
<label><input type="checkbox" id="c3" style="width:auto"> Live projects/dashboard load</label><br>
<label><input type="checkbox" id="c4" style="width:auto"> Rename/archive/restore behave as expected</label><br>
<label><input type="checkbox" id="c5" style="width:auto"> I reviewed the NOT_EXPOSED DG-P4..P10 rows</label><br><br>
<button onclick="decision()">Generate browser UAT note</button>
<pre id="decisionOut"></pre>
</div>
</main>
<script>
let token = "";
let meta = null;

async function call(path, options) {
  options = options || {};
  options.headers = options.headers || {};
  if (token) options.headers["Authorization"] = "Bearer " + token;
  if (options.body && !options.headers["Content-Type"]) options.headers["Content-Type"] = "application/json";
  const r = await fetch(path, options);
  let body;
  const txt = await r.text();
  try { body = JSON.parse(txt); } catch { body = txt; }
  return {status:r.status, ok:r.ok, body:body};
}
function show(id, obj){document.getElementById(id).textContent=JSON.stringify(obj,null,2)}

async function init(){
  const r=await call("/uat/meta");
  meta=r.body;
  const good = meta.actual_head === meta.expected_head;
  document.getElementById("identity").innerHTML =
    "<div>Expected HEAD: <code>"+meta.expected_head+"</code></div>"+
    "<div>Actual HEAD: <code>"+meta.actual_head+"</code></div>"+
    "<div class='"+(good?"ok":"bad")+"'>HEAD "+(good?"MATCH":"MISMATCH")+"</div>"+
    "<div>DB: <code>"+meta.database+"</code></div>"+
    "<div>Seed project: <code>"+meta.project_id+"</code></div>";
  document.getElementById("coverage").innerHTML = meta.coverage.map(function(x){
    const cls=x.status==="LIVE"?"ok":(x.status==="NOT_EXPOSED"?"warn":"bad");
    return "<tr><td>"+x.area+"</td><td class='"+cls+"'>"+x.status+"</td><td>"+x.note+"</td></tr>";
  }).join("");
}
async function health(){show("healthOut",await call("/health"))}
async function login(){
  const r=await call("/auth/login",{method:"POST",body:JSON.stringify({username:document.getElementById("user").value,password:document.getElementById("pass").value})});
  if(r.ok){token=r.body.access_token;document.getElementById("loginState").innerHTML="<span class='ok'>LOGIN PASS</span> actor="+r.body.actor_id}
  else{document.getElementById("loginState").innerHTML="<span class='bad'>LOGIN FAIL</span>";}
  show("apiOut",r);
}
async function listProjects(){show("apiOut",await call("/projects"))}
async function loadDashboard(){show("apiOut",await call("/product/projects/"+meta.project_id+"/dashboard"))}
async function renameProject(){
  const n="Browser UAT "+new Date().toLocaleTimeString();
  show("apiOut",await call("/product/projects/"+meta.project_id,{method:"PATCH",body:JSON.stringify({name:n})}));
}
async function archiveProject(){show("apiOut",await call("/product/projects/"+meta.project_id+"/archive",{method:"POST",body:JSON.stringify({drain:false,reason:"browser UAT"})}))}
async function restoreProject(){show("apiOut",await call("/product/projects/"+meta.project_id+"/restore",{method:"POST"}))}
function decision(){
  const ids=["c1","c2","c3","c4","c5"];
  const checks=ids.map(function(id){return document.getElementById(id).checked});
  const note={
    schema:"GWF-BROWSER-UAT-NOTE-v1",
    head:meta.actual_head,
    time:new Date().toISOString(),
    checks:{
      server_health:checks[0],login:checks[1],live_dashboard:checks[2],
      lifecycle_actions:checks[3],reviewed_not_exposed:checks[4]
    },
    browser_uat_status:checks.slice(0,4).every(Boolean)?"PASS_FOR_EXPOSED_SURFACES":"INCOMPLETE_OR_FAIL",
    dg_p4_p10_product_uat:"BLOCKED_NOT_EXPOSED"
  };
  show("decisionOut",note);
}
init();
</script>
</body>
</html>
"""


def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def build_runtime(db_path: Path):
    if db_path.exists():
        db_path.unlink()
    rt = GovernedWorkflowRuntime(
        str(ROOT / "domains" / "research.workflow.yaml"),
        str(db_path),
        auth_secret="browser-uat-local-secret-value-0123456789abcdef",
    )
    human = rt.governance.create_actor("HUMAN", "operator", ["human_approver"], [])
    rt.auth.register_human(human, "operator", "operator-password-long")
    tenant = rt.tenancy.create_tenant("Browser UAT Tenant", human)
    workspace = rt.tenancy.create_workspace(tenant, "Browser UAT Workspace", human)
    project = rt.create_scoped_project("Browser UAT Project", tenant, workspace, human)
    rt.tenancy.add_project_member(project, human, "APPROVER", human)

    rt.governance.prepare_system_proposal(
        project,
        "CONFIRM_ROOT",
        ["browser-uat"],
        {"source": "browser-uat", "purpose": "live product surface"},
        "human_recovery_confirmation",
    )

    return rt, project


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--expected-head", default=EXPECTED_HEAD)
    args = parser.parse_args()

    actual = git_head()
    if actual != args.expected_head:
        raise SystemExit(
            "HEAD mismatch: expected %s, found %s" % (args.expected_head, actual)
        )

    root = ROOT / ".gwr" / "uat" / "browser"
    root.mkdir(parents=True, exist_ok=True)
    db_path = root / "browser-uat.db"
    rt, project = build_runtime(db_path)
    app = create_app(rt)

    coverage = [
        {"area": "FastAPI server / health", "status": "LIVE", "note": "Actual create_app(runtime)"},
        {"area": "Authentication", "status": "LIVE", "note": "POST /auth/login"},
        {"area": "Projects / dashboard / lifecycle", "status": "LIVE", "note": "Actual product API"},
        {"area": "Agent protocol / recovery API", "status": "LIVE", "note": "Endpoints exist in product API"},
        {"area": "DG-P4 document identity/facade", "status": "NOT_EXPOSED", "note": "Runtime service exists; no product HTTP endpoint"},
        {"area": "DG-P5 QA / findings", "status": "NOT_EXPOSED", "note": "Runtime service exists; no product HTTP endpoint"},
        {"area": "DG-P6 lifecycle / validity", "status": "NOT_EXPOSED", "note": "Runtime service exists; no product HTTP endpoint"},
        {"area": "DG-P7 document authority", "status": "NOT_EXPOSED", "note": "Runtime service exists; no product HTTP endpoint"},
        {"area": "DG-P8 document relations", "status": "NOT_EXPOSED", "note": "Runtime service exists; no product HTTP endpoint"},
        {"area": "DG-P9 relation binding", "status": "NOT_EXPOSED", "note": "Runtime service exists; no product HTTP endpoint"},
        {"area": "DG-P10 change classification / lineage plan", "status": "NOT_EXPOSED", "note": "Runtime service exists; no product HTTP endpoint"},
    ]

    @app.get("/uat", response_class=HTMLResponse, include_in_schema=False)
    def uat_page():
        return HTML

    @app.get("/uat/meta", include_in_schema=False)
    def uat_meta():
        return {
            "expected_head": args.expected_head,
            "actual_head": actual,
            "database": str(db_path),
            "project_id": project,
            "coverage": coverage,
            "authoritative_backend": True,
            "uat_overlay_only": True,
        }

    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            "uvicorn is not installed. Run the PowerShell browser-UAT launcher."
        ) from exc

    print("")
    print("GWF LIVE BROWSER UAT")
    print("HEAD=%s" % actual)
    print("URL=http://%s:%s/uat" % (args.host, args.port))
    print("API_DOCS=http://%s:%s/docs" % (args.host, args.port))
    print("USERNAME=operator")
    print("PASSWORD=operator-password-long")
    print("DB=%s" % db_path)
    print("")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
