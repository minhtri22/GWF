const LS_DOMAINS="gwr-uat-domains",LS_PROJECTS="gwr-uat-projects",LS_DECISIONS="gwr-uat-decisions",LS_OVERRIDES="gwr-uat-project-overrides",LS_PROTOCOL="gwr-uat-protocol";
const state={data:null,project:null,view:"dashboard",activeProposal:null,activePhaseIndex:null,domains:JSON.parse(localStorage.getItem(LS_DOMAINS)||"[]"),projects:JSON.parse(localStorage.getItem(LS_PROJECTS)||"[]"),decisions:JSON.parse(localStorage.getItem(LS_DECISIONS)||"{}"),overrides:JSON.parse(localStorage.getItem(LS_OVERRIDES)||"{}"),protocolState:JSON.parse(localStorage.getItem(LS_PROTOCOL)||"{}")};
const $=s=>document.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
const uid=p=>p+"_"+Math.random().toString(36).slice(2,9);
const SECRET_LIKE_PATTERNS=[
 /\bgithub_pat_[A-Za-z0-9_]{20,}\b/i,
 /\bgh[pousr]_[A-Za-z0-9]{20,}\b/i,
 /\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b/i,
 /\bxox[baprs]-[A-Za-z0-9-]{10,}\b/i,
 /\b(api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password|authorization)\b\s*[:=]\s*["']?[A-Za-z0-9_./+=:@-]{12,}/i
];
const containsSensitiveMaterial=value=>SECRET_LIKE_PATTERNS.some(re=>re.test(String(value??"")));
function purgeSensitiveLocalUatState(){
 const before=state.domains.length;
 state.domains=state.domains.filter(d=>!(d.revisions||[]).some(r=>containsSensitiveMaterial(r.yaml_text)));
 if(state.domains.length!==before){
   localStorage.setItem(LS_DOMAINS,JSON.stringify(state.domains));
   return true;
 }
 return false;
}
const badge=s=>{const v=String(s||"").toUpperCase(),good=["PASS","COMPLETED","SUCCEEDED","VALID","ACTIVE","APPROVED","PUBLISHED","VALIDATED"].includes(v),bad=["FAIL","FAILED","ABANDONED","REJECTED"].includes(v),warn=["PAUSED","READY","RUNNING","DIRTY","STALE","PENDING_APPROVAL","RECOVERY_PLANNED","DRAFT"].includes(v);return `<span class="badge ${good?"good":bad?"bad":warn?"warn":""}">${esc(v)}</span>`};
function save(){localStorage.setItem(LS_DOMAINS,JSON.stringify(state.domains));localStorage.setItem(LS_PROJECTS,JSON.stringify(state.projects));localStorage.setItem(LS_DECISIONS,JSON.stringify(state.decisions));localStorage.setItem(LS_OVERRIDES,JSON.stringify(state.overrides));localStorage.setItem(LS_PROTOCOL,JSON.stringify(state.protocolState))}
function defaultDomain(){const d=state.data.product.domain;return {package_id:"domainpkg_demo_research",domain_id:d.domain_id,name:"Research Full Cycle",status:"ACTIVE",revisions:[{revision_id:"domainrev_demo_research_030",revision_number:1,semantic_version:d.version,status:"PUBLISHED",payload_hash:d.fingerprint,yaml_text:"domain_id: research.full-cycle\nversion: 0.3.0\n"}]}}
function allDomains(){return [defaultDomain(),...state.domains]}
function allProjects(){return [...state.data.projects.map(p=>({...p,...(state.overrides[p.id]||{})})),...state.projects.map(p=>({...p,...(state.overrides[p.id]||{})}))]}
function publishedRevisions(){return allDomains().flatMap(d=>(d.revisions||[]).filter(r=>r.status==="PUBLISHED").map(r=>({...r,domain_id:d.domain_id,domain_name:d.name})))}
function effectiveApproval(a){const d=state.decisions[a.proposal_id];return d?{...a,status:d.decision,local:true}:a}
async function init(){
 const purgedSensitiveState=purgeSensitiveLocalUatState();
 const res=await fetch("./demo-data.json",{cache:"no-store"});state.data=await res.json();
 if(purgedSensitiveState) alert("Sensitive-looking material was removed from local UAT storage. Never enter API keys, tokens or passwords on GitHub Pages.");
 $("#projectSelect").addEventListener("change",e=>choose(e.target.value));
 document.querySelectorAll(".nav-item").forEach(b=>b.addEventListener("click",()=>show(b.dataset.view)));
 $("#resetUat").onclick=()=>{if(confirm("Reset all local UAT domains, projects and decisions?")){localStorage.removeItem(LS_DOMAINS);localStorage.removeItem(LS_PROJECTS);localStorage.removeItem(LS_DECISIONS);localStorage.removeItem(LS_OVERRIDES);localStorage.removeItem(LS_PROTOCOL);state.domains=[];state.projects=[];state.decisions={};state.overrides={};state.protocolState={};choose(state.data.projects[0].id)}};
 $("#newDomainBtn").onclick=$("#newDomainBtn2").onclick=openDomainDialog;$("#newProjectBtn").onclick=openProjectDialog;
 $("#saveDomainBtn").onclick=createDomain;$("#createProjectBtn").onclick=createProject;
 $("#approveBtn").onclick=()=>decide("APPROVED");$("#rejectBtn").onclick=()=>decide("REJECTED");
 $("#renameProjectBtn").onclick=renameCurrentProject;$("#archiveProjectBtn").onclick=archiveCurrentProject;
 $("#simulateIssueBtn").onclick=simulateProtocolIssue;$("#approveRecoveryBtn").onclick=approveProtocolRecovery;$("#rejectRecoveryBtn").onclick=rejectProtocolRecovery;
 $("#recoveryModeSelect").onchange=e=>setRecoveryMode(e.target.value);
 choose(allProjects()[0].id);
}
function syncProjects(){const sel=$("#projectSelect"),current=state.project?.id;sel.innerHTML=allProjects().map(p=>`<option value="${esc(p.id)}">${esc(p.name)}${p.local?" · UAT":""}</option>`).join("");if(current)sel.value=current}
function choose(id){state.project=allProjects().find(p=>p.id===id)||allProjects()[0];syncProjects();render()}
function show(v){state.view=v;document.querySelectorAll(".view").forEach(x=>x.classList.remove("active"));$("#view-"+v)?.classList.add("active");document.querySelectorAll(".nav-item").forEach(b=>b.classList.toggle("active",b.dataset.view===v))}
function render(){
 const p=state.project;if(!p)return;syncProjects();
 $("#projectTitle").textContent=p.name;$("#projectStatus").outerHTML=badge(p.status).replace("<span",'<span id="projectStatus"');$("#archiveProjectBtn").textContent=p.status==="ARCHIVED"?"Restore project":"Archive project";$("#projectScope").textContent=`${p.tenant||"UAT Tenant"} / ${p.workspace||"UAT Workspace"} · ${p.id}`;
 const approvals=(p.approvals||[]).map(effectiveApproval),pending=approvals.filter(a=>a.status==="PENDING_APPROVAL");
 $("#approvalCount").textContent=pending.length;
 const m=p.metrics||{pending_approvals:0,open_failures:0,active_jobs:0,phase_executions:(p.phases||[]).length};
 $("#metrics").innerHTML=[["Phase executions",m.phase_executions||0],["Pending approvals",pending.length],["Open failures",m.open_failures||0],["Audit events",p.audit_count||0]].map(([k,v])=>`<div class="metric"><span>${esc(k)}</span><strong>${esc(v)}</strong></div>`).join("");
 const phases=p.phases||[];$("#phaseSummary").textContent=`${phases.filter(x=>x.status==="PASS").length} pass · ${phases.filter(x=>x.status==="FAIL").length} failed`;
 $("#phaseTimeline").innerHTML=phases.length?phases.map((ph,i)=>`<div class="phase clickable" data-phase="${i}"><span class="phase-dot ${phaseDotClass(ph,i)}"></span><div><div class="name">${esc(ph.label)}</div><div class="detail">generation ${ph.generation||0}${ph.detail?" · "+esc(ph.detail):""}</div></div>${badge(ph.status)}</div>`).join(""):'<div class="empty">Project created. No workflow started in static UAT.</div>';
 document.querySelectorAll("[data-phase]").forEach(el=>el.onclick=()=>openPhase(Number(el.dataset.phase)));
 const attention=[];pending.forEach(a=>attention.push(`<div class="attention"><div class="icon">!</div><div><strong>Human approval required</strong><span>${esc(a.action)} · ${esc(a.proposal_id)}</span></div></div>`));(p.failures||[]).filter(f=>f.status!=="RESOLVED").forEach(f=>attention.push(`<div class="attention"><div class="icon">↺</div><div><strong>${esc(f.failure_class)}</strong><span>resume at ${esc(f.resume_candidate)}</span></div></div>`));$("#attentionQueue").innerHTML=attention.join("")||'<div class="empty">No blocking operator action.</div>';
 const pin=p.domain_binding||{domain_id:"research.full-cycle",semantic_version:"0.3.0",domain_revision_id:"domainrev_demo_research_030"};$("#domainPin").innerHTML=`<div class="card-row"><div><strong>${esc(pin.domain_name||pin.domain_id)}</strong><p>${esc(pin.domain_id)} @ ${esc(pin.semantic_version||"0.3.0")}</p></div>${badge("PINNED")}</div><code class="hash">${esc(pin.domain_revision_id)}</code>`;
 $("#frontier").innerHTML=(p.frontier||[]).map(a=>`<span class="artifact-pill ${a.state.toLowerCase()}">${esc(a.name)} · ${esc(a.state)}</span>`).join("")||'<span class="subtle">No artifacts yet.</span>';
 renderProcess();renderApprovals(approvals);renderRecovery();renderDistributed();renderDomains();show(state.view);
}
function renderProcess(){
 const p=state.project,phases=p.phases||[],current=[...phases].reverse().find(x=>["RUNNING","PAUSED"].includes(x.status))||phases.at(-1);
 $("#currentPhaseTitle").textContent=current?current.label:"Not started";$("#currentPhaseCard").innerHTML=current?`${badge(current.status)}<p>Phase: <strong>${esc(current.id)}</strong></p><p>Generation: ${current.generation||0}</p><button class="ghost" id="inspectCurrent">Open Phase Inspector</button>`:'<div class="empty">No phase execution yet.</div>';if(current)$("#inspectCurrent").onclick=()=>openPhase(phases.indexOf(current));
 const maxGen=Math.max(0,...phases.map(x=>x.generation||0));$("#lineageCard").innerHTML=`<div class="mini-metrics"><div class="mini"><span>Generation</span><strong>${maxGen}</strong></div><div class="mini"><span>Attempts</span><strong>${phases.length}</strong></div><div class="mini"><span>Failures</span><strong>${phases.filter(x=>x.status==="FAIL").length}</strong></div></div>`;
 $("#processHistory").innerHTML=phases.length?`<table><thead><tr><th>Gen</th><th>Phase</th><th>Status</th><th>Result</th><th>Action</th></tr></thead><tbody>${phases.map((x,i)=>`<tr><td>${x.generation||0}</td><td>${esc(x.label)}</td><td>${badge(x.status)}</td><td>${esc(x.detail||x.outcome||"—")}</td><td><button class="ghost phase-open" data-i="${i}">Inspect</button></td></tr>`).join("")}</tbody></table>`:'<div class="empty">No process history.</div>';document.querySelectorAll(".phase-open").forEach(b=>b.onclick=()=>openPhase(Number(b.dataset.i)));
 const logs=phases.flatMap((x,i)=>phaseEvents(x,i)).sort((a,b)=>a.time.localeCompare(b.time)).slice(-15).reverse();$("#processLog").innerHTML=logs.length?`<table><thead><tr><th>Time</th><th>Event</th><th>Phase</th><th>Detail</th></tr></thead><tbody>${logs.map(e=>`<tr><td>${esc(e.time)}</td><td>${esc(e.event)}</td><td>${esc(e.phase)}</td><td>${esc(e.detail)}</td></tr>`).join("")}</tbody></table>`:'<div class="empty">No process events.</div>';
}
function phaseEvents(ph,i){if(ph.events)return ph.events;const base=`2026-09-18T03:${String(10+i).padStart(2,"0")}:00Z`;const out=[{time:base,event:"PHASE_STARTED",phase:ph.id,detail:`generation ${ph.generation||0}`}];if(ph.status==="FAIL")out.push({time:base,event:"GATE_BLOCKED",phase:ph.id,detail:ph.detail||"failure recorded"});else if(ph.status==="PASS")out.push({time:base,event:"PHASE_SUCCEEDED",phase:ph.id,detail:ph.detail||"outputs committed"});else out.push({time:base,event:"PHASE_RUNNING",phase:ph.id,detail:ph.detail||"in progress"});return out}
function protocolKey(i){return `${state.project.id}:${i}`}
function defaultProtocol(ph,i){
 const complete=ph.status==="PASS"||ph.status==="COMPLETED", failed=ph.status==="FAIL";
 const stages=["LOAD","PREFLIGHT","PLAN","EXECUTE","VERIFY","HANDOFF","COMPLETE"];
 const current=complete?"COMPLETE":failed?"VERIFY":"EXECUTE";
 const currentIndex=stages.indexOf(current);
 const plan=[
  "Resolve authoritative inputs","Load skill & previous handoff","Verify environment and tools",
  "Execute primary task","Persist outputs & evidence","Run QA / gates","Write handoff"
 ];
 return {mode:"AUTO",attention:complete?"COMPLETE":failed?"NEEDS_ATTENTION":"AI_WORKING",currentStage:current,
   stages:stages.map((s,idx)=>({name:s,status:idx<currentIndex?"DONE":idx===currentIndex?(complete?"DONE":"CURRENT"):"WAITING"})),
   plan:plan.map((title,idx)=>({index:idx+1,title,status:complete?"PASS":idx<3?"PASS":idx===3?"RUNNING":"PENDING",note:""})),
   retryCount:0,pendingRecovery:false,
   events:[{time:new Date(Date.now()-120000).toISOString(),event:"SKILL_LOADED",detail:"Pinned SKILL.md revision loaded"},
           {time:new Date(Date.now()-90000).toISOString(),event:"PREFLIGHT_PASS",detail:"Inputs, authority, tools and resources verified"},
           {time:new Date(Date.now()-60000).toISOString(),event:"PLAN_FROZEN",detail:"Plan revision #1 frozen"},
           {time:new Date(Date.now()-30000).toISOString(),event:complete?"PROTOCOL_COMPLETED":failed?"PROBLEM_RECORDED":"EXECUTION_STARTED",detail:complete?"Handoff and checkpoint committed":failed?(ph.detail||"Issue recorded before recovery"):"Executing plan step 4"}]};
}
function getProtocol(ph,i){const key=protocolKey(i);if(!state.protocolState[key])state.protocolState[key]=defaultProtocol(ph,i);return state.protocolState[key]}
function phaseDotClass(ph,i){const p=getProtocol(ph,i);if(p.attention==="WAITING_FOR_YOU")return "waiting";if(p.attention==="NEEDS_ATTENTION")return "issue";return ph.status.toLowerCase()}
function renderAgentProtocol(ph,i){
 const p=getProtocol(ph,i),done=p.plan.filter(x=>["PASS","SKIPPED"].includes(x.status)).length;
 const attention=p.attention==="AI_WORKING"?'<span class="ai-working"><i class="breathing-dot"></i> AI Working</span>':badge(p.attention.replaceAll("_"," "));
 const problems=p.events.filter(e=>e.event==="PROBLEM_RECORDED");
 return `<div class="card-row"><div>${attention}<p>Stage <strong>${esc(p.currentStage)}</strong> · retry ${p.retryCount}</p></div><div><span class="label">Plan progress</span><strong>${done}/${p.plan.length}</strong></div></div>
 ${problems.length?`<div class="problem-banner"><strong>Issue recorded</strong><p>${esc(problems.at(-1).detail)}</p><span class="subtle">The problem is persisted before retry/replan.</span></div>`:""}
 <div class="protocol-grid"><div><span class="label">Execution protocol</span><div class="protocol-stages">${p.stages.map(s=>`<div class="protocol-stage ${s.status==="CURRENT"?"current":s.status==="DONE"?"done":""}"><span>${esc(s.name)}</span><span>${s.status==="DONE"?"✓":s.status==="CURRENT"?"◉":"○"}</span></div>`).join("")}</div></div>
 <div><span class="label">Frozen plan</span><div class="card">${p.plan.map(s=>`<div class="plan-step"><span class="step-index">${s.index}</span><div><strong>${esc(s.title)}</strong><p>${esc(s.note||"")}</p></div>${badge(s.status)}</div>`).join("")}</div></div></div>
 <span class="label">Operational event log</span><div class="table-wrap"><table><thead><tr><th>Time</th><th>Event</th><th>Detail</th></tr></thead><tbody>${p.events.slice().reverse().map(e=>`<tr><td>${esc(e.time)}</td><td>${esc(e.event)}</td><td>${esc(e.detail)}</td></tr>`).join("")}</tbody></table></div>`;
}
function openPhase(i){
 state.activePhaseIndex=i;
 const ph=(state.project.phases||[])[i];if(!ph)return;const ev=phaseEvents(ph,i);$("#phaseDialogTitle").textContent=ph.label;
 const details=ph.inspector||{inputs:["protocol","experiment_plan"],outputs:ph.status==="FAIL"?[]:["phase_output"],evidence:["execution_evidence"],gates:[{name:"phase_gate",result:ph.status==="FAIL"?"BLOCKED":"PASS"}],checkpoint:ph.status==="FAIL"?"cp_failure_"+i:"cp_"+i};
 const proto=getProtocol(ph,i);$("#recoveryModeSelect").value=proto.mode;
 $("#approveRecoveryBtn").hidden=!proto.pendingRecovery;$("#rejectRecoveryBtn").hidden=!proto.pendingRecovery;
 $("#phaseInspector").innerHTML=renderAgentProtocol(ph,i)+`<hr style="border:0;border-top:1px solid var(--border);margin:18px 0"><div class="review-grid"><div><span class="label">Phase status</span>${badge(ph.status)}</div><div><span class="label">Generation</span><strong>${ph.generation||0}</strong></div></div><div class="grid two"><div><span class="label">Inputs</span><div class="cards compact">${(details.inputs||[]).map(x=>`<div class="card"><strong>${esc(x)}</strong><p>VALID revision</p></div>`).join("")||"—"}</div></div><div><span class="label">Outputs</span><div class="cards compact">${(details.outputs||[]).map(x=>`<div class="card"><strong>${esc(x)}</strong><p>Produced by this attempt</p></div>`).join("")||"—"}</div></div></div><span class="label">Evidence / gates</span><pre class="payload">${esc(JSON.stringify({evidence:details.evidence||[],gates:details.gates||[],failure:ph.status==="FAIL"?(ph.detail||"failure"):null,checkpoint:details.checkpoint||null},null,2))}</pre>`;
 $("#phaseDialog").showModal();
}
function setRecoveryMode(mode){if(state.activePhaseIndex==null)return;const ph=state.project.phases[state.activePhaseIndex],p=getProtocol(ph,state.activePhaseIndex);p.mode=mode;save();openPhase(state.activePhaseIndex)}
function simulateProtocolIssue(){
 if(state.activePhaseIndex==null)return;if(state.project.status==="ARCHIVED")return alert("Archived projects are read-only.");
 const i=state.activePhaseIndex,ph=state.project.phases[i],p=getProtocol(ph,i),now=new Date().toISOString();
 p.attention="NEEDS_ATTENTION";p.events.push({time:now,event:"PROBLEM_RECORDED",detail:"WORKER_TIMEOUT at current plan step; impact recorded before any retry"});
 if(p.mode==="AUTO"){p.events.push({time:new Date(Date.now()+1).toISOString(),event:"RECOVERY_AUTO_APPROVED",detail:"LOW risk, no normative change, retry budget available"});p.events.push({time:new Date(Date.now()+2).toISOString(),event:"RECOVERY_APPLIED",detail:"Retry current step on healthy worker"});p.retryCount++;p.attention="AI_WORKING";p.pendingRecovery=false}
 else{p.events.push({time:new Date(Date.now()+1).toISOString(),event:"RECOVERY_WAITING_HUMAN",detail:"Execution paused. Human approval required before retry."});p.attention="WAITING_FOR_YOU";p.pendingRecovery=true}
 save();render();openPhase(i)
}
function approveProtocolRecovery(){if(state.activePhaseIndex==null)return;const i=state.activePhaseIndex,ph=state.project.phases[i],p=getProtocol(ph,i);if(!p.pendingRecovery)return;p.events.push({time:new Date().toISOString(),event:"RECOVERY_APPROVED",detail:"Human approved recorded recovery proposal"});p.events.push({time:new Date(Date.now()+1).toISOString(),event:"RECOVERY_APPLIED",detail:"Retry resumed after approval"});p.pendingRecovery=false;p.retryCount++;p.attention="AI_WORKING";save();render();openPhase(i)}
function rejectProtocolRecovery(){if(state.activePhaseIndex==null)return;const i=state.activePhaseIndex,ph=state.project.phases[i],p=getProtocol(ph,i);if(!p.pendingRecovery)return;p.events.push({time:new Date().toISOString(),event:"RECOVERY_REJECTED",detail:"Human rejected recovery proposal; phase remains blocked"});p.pendingRecovery=false;p.attention="NEEDS_ATTENTION";save();render();openPhase(i)}
function renameCurrentProject(){const p=state.project;if(!p)return;const name=prompt("Rename project",p.name);if(!name||!name.trim()||name.trim()===p.name)return;state.overrides[p.id]={...(state.overrides[p.id]||{}),name:name.trim()};save();choose(p.id)}
function archiveCurrentProject(){const p=state.project;if(!p)return;if(p.status==="ARCHIVED"){state.overrides[p.id]={...(state.overrides[p.id]||{}),status:"ACTIVE"};save();choose(p.id);return}const active=(p.phases||[]).some(x=>["RUNNING","PAUSED"].includes(x.status));if(active&&!confirm("Project has active work. Static UAT will simulate controlled drain before archive. Continue?"))return;if(!active&&!confirm("Archive project? History, artifacts and logs remain visible; mutations become read-only."))return;state.overrides[p.id]={...(state.overrides[p.id]||{}),status:"ARCHIVED"};save();choose(p.id)}
function renderApprovals(a){$("#approvalList").innerHTML=a.length?a.map(x=>`<div class="card"><div class="card-row"><div><h3>${esc(x.action)}</h3><p>${esc(x.policy)} · ${esc(x.proposal_id)}</p></div>${badge(x.status)}</div><code class="hash">${esc(x.payload_hash)}</code><div class="card-row" style="margin-top:10px"><p>${x.local?"Local UAT decision":"Frozen payload"}</p><button class="ghost review-btn" data-id="${esc(x.proposal_id)}">Review</button></div></div>`).join(""):'<div class="empty">No approval records.</div>';document.querySelectorAll(".review-btn").forEach(b=>b.onclick=()=>openApproval(b.dataset.id))}
function openApproval(id){const a=(state.project.approvals||[]).find(x=>x.proposal_id===id);if(!a)return;state.activeProposal=a;$("#dialogTitle").textContent=a.proposal_id;$("#dialogAction").textContent=a.action;$("#dialogPolicy").textContent=a.policy;$("#dialogHash").textContent=a.payload_hash;$("#dialogPayload").textContent=JSON.stringify(a.payload,null,2);$("#approvalDialog").showModal()}
function decide(decision){const a=state.activeProposal;if(!a)return;state.decisions[a.proposal_id]={decision,at:new Date().toISOString(),hash:a.payload_hash};save();$("#approvalDialog").close();render()}
function renderRecovery(){const f=(state.project.failures||[])[0];if(!f){$("#recoveryGraph").innerHTML='<div class="empty">No failures.</div>';$("#failureList").innerHTML="";return}const r=f.recovery||{};$("#recoveryGraph").innerHTML=[["Detection",f.detected_stage,f.status],["Root",f.root_ref,f.root_status],["Recovery",r.recovery_id,r.status],["Resume",r.resume_target,"TARGET"]].map((x,i)=>`${i?'<span class="graph-arrow">→</span>':""}<div class="graph-node"><span class="kind">${x[0]}</span><strong>${esc(x[1])}</strong><div style="margin-top:7px">${badge(x[2])}</div></div>`).join("");$("#failureList").innerHTML=(state.project.failures||[]).map(x=>`<div class="card"><h3>${esc(x.failure_class)}</h3><p>${esc(x.failure_id)} · root ${esc(x.root_ref)} · resume ${esc(x.resume_candidate)}</p>${badge(x.status)}</div>`).join("")}
function renderDistributed(){const d=state.project.distributed||{jobs:[],workers:[]};$("#jobTable").innerHTML=d.jobs.length?`<table><thead><tr><th>Job</th><th>Work unit</th><th>Status</th><th>Worker</th><th>Attempt</th></tr></thead><tbody>${d.jobs.map(j=>`<tr><td>${esc(j.job_id)}</td><td>${esc(j.workunit)}</td><td>${badge(j.status)}</td><td>${esc(j.worker)}</td><td>${esc(j.attempt)}</td></tr>`).join("")}</tbody></table>`:'<div class="empty">No distributed jobs.</div>';$("#workerList").innerHTML=d.workers.map(w=>`<div class="card"><div class="card-row"><h3>${esc(w.worker_id)}</h3>${badge(w.status)}</div><p>CPU ${esc(w.cpu)} · Memory ${esc(w.memory)}</p><p>${esc((w.labels||[]).join(" · "))}</p></div>`).join("")||'<div class="empty">No workers assigned.</div>'}
function renderDomains(){
 $("#domainRegistry").innerHTML=allDomains().map(d=>`<div class="card"><div class="card-row"><div><h3>${esc(d.name)}</h3><p>${esc(d.domain_id)} · ${d.package_id.startsWith("domainpkg_demo")?"built-in":"local UAT"}</p></div>${badge(d.status)}</div>${(d.revisions||[]).map(r=>`<div class="card-row domain-rev"><span>rev ${r.revision_number} · ${esc(r.semantic_version||"")}</span><span>${badge(r.status)} ${r.status!=="PUBLISHED"&&!d.package_id.startsWith("domainpkg_demo")?`<button class="ghost publish-domain" data-pkg="${d.package_id}" data-rev="${r.revision_id}">Publish</button>`:""}</span></div>`).join("")}</div>`).join("");
 document.querySelectorAll(".publish-domain").forEach(b=>b.onclick=()=>{const d=state.domains.find(x=>x.package_id===b.dataset.pkg),r=d?.revisions.find(x=>x.revision_id===b.dataset.rev);if(r){r.status="PUBLISHED";save();render()}});
}
function openDomainDialog(){const id="uat.domain";$("#domainIdInput").value=id;$("#domainNameInput").value="UAT Domain";$("#domainYamlInput").value=`domain_id: ${id}\nversion: 0.1.0\ndescription: UAT-created domain\nartifact_types: []\ntrace_types: []\nworkunit_templates: []\nevidence_types: []\ngate_types: []\nfailure_types: []\nrecovery_policies: []\nroles: []\nauthority_policies: []\napproval_policies: []\nvalidity_rules: []\nloop_policy: {}\n`;$("#domainDialog").showModal()}
function createDomain(){const id=$("#domainIdInput").value.trim(),name=$("#domainNameInput").value.trim(),yaml=$("#domainYamlInput").value;if(!id||!name||!yaml.includes("domain_id:")||!yaml.includes("version:"))return alert("Domain ID, name and YAML with domain_id/version are required.");if(containsSensitiveMaterial(yaml))return alert("GitHub Pages is public static hosting. Do not enter API keys, tokens, passwords or other secrets here.");if(allDomains().some(d=>d.domain_id===id))return alert("Domain ID already exists.");const version=(yaml.match(/version:\s*([^\n]+)/)||[])[1]?.trim()||"0.1.0";state.domains.push({package_id:uid("domainpkg"),domain_id:id,name,status:"ACTIVE",revisions:[{revision_id:uid("domainrev"),revision_number:1,semantic_version:version,status:"VALIDATED",payload_hash:"uat:"+uid("hash"),yaml_text:yaml}]});save();$("#domainDialog").close();renderDomains();show("domains")}
function openProjectDialog(){const revs=publishedRevisions();$("#projectDomainSelect").innerHTML=revs.map(r=>`<option value="${r.revision_id}">${esc(r.domain_name)} · ${esc(r.semantic_version)}</option>`).join("");$("#projectNameInput").value="New UAT Project";$("#projectDialog").showModal()}
function createProject(){const name=$("#projectNameInput").value.trim(),rid=$("#projectDomainSelect").value,rev=publishedRevisions().find(r=>r.revision_id===rid);if(!name||!rev)return alert("Project name and published domain revision are required.");const p={id:uid("project_uat"),name,tenant:"UAT Tenant",workspace:$("#projectWorkspaceInput").value||"UAT Workspace",status:"READY",local:true,audit_count:1,metrics:{pending_approvals:0,open_failures:0,active_jobs:0,phase_executions:0},phases:[],frontier:[],approvals:[],failures:[],distributed:{workers:[],jobs:[]},domain_binding:{domain_revision_id:rev.revision_id,domain_id:rev.domain_id,domain_name:rev.domain_name,semantic_version:rev.semantic_version,revision_status:"PUBLISHED"}};state.projects.push(p);save();$("#projectDialog").close();choose(p.id);show("dashboard")}
init().catch(err=>{document.body.innerHTML=`<pre style="padding:30px;color:#ff7188">UAT failed: ${esc(err.message)}</pre>`});