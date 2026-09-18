const state={data:null,project:null,view:"dashboard",activeProposal:null,decisions:JSON.parse(localStorage.getItem("gwr-uat-decisions")||"{}")};
const $=s=>document.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
const badge=s=>{const v=String(s||"").toUpperCase();const cls=["PASS","COMPLETED","SUCCEEDED","VALID","ACTIVE","APPROVED"].includes(v)?"good":["FAIL","FAILED","ABANDONED","REJECTED"].includes(v)?"bad":["PAUSED","READY","RUNNING","DIRTY","STALE","PENDING_APPROVAL","RECOVERY_PLANNED"].includes(v)?"warn":"";return `<span class="badge ${cls}">${esc(v)}</span>`};
function decisionFor(id){return state.decisions[id]}
function effectiveApproval(a){const d=decisionFor(a.proposal_id);return d?{...a,status:d.decision,local:true}:a}
async function init(){
  const res=await fetch("./demo-data.json",{cache:"no-store"}); state.data=await res.json();
  const select=$("#projectSelect"); select.innerHTML=state.data.projects.map(p=>`<option value="${esc(p.id)}">${esc(p.name)}</option>`).join("");
  select.addEventListener("change",()=>choose(select.value));
  document.querySelectorAll(".nav-item").forEach(b=>b.addEventListener("click",()=>show(b.dataset.view)));
  $("#resetUat").addEventListener("click",()=>{localStorage.removeItem("gwr-uat-decisions");state.decisions={};render()});
  $("#approveBtn").addEventListener("click",()=>decide("APPROVED"));
  $("#rejectBtn").addEventListener("click",()=>decide("REJECTED"));
  choose(state.data.projects[0].id);
}
function choose(id){state.project=state.data.projects.find(p=>p.id===id);render()}
function show(view){state.view=view;document.querySelectorAll(".view").forEach(v=>v.classList.remove("active"));$("#view-"+view).classList.add("active");document.querySelectorAll(".nav-item").forEach(b=>b.classList.toggle("active",b.dataset.view===view))}
function render(){
  const p=state.project;if(!p)return;
  $("#projectTitle").textContent=p.name; $("#projectStatus").outerHTML=badge(p.status).replace("<span",'<span id="projectStatus"');$("#projectScope").textContent=`${p.tenant} / ${p.workspace} · ${p.id}`;
  const approvals=p.approvals.map(effectiveApproval); const pending=approvals.filter(a=>a.status==="PENDING_APPROVAL");
  $("#approvalCount").textContent=pending.length;
  $("#metrics").innerHTML=[
    ["Phase executions",p.metrics.phase_executions],["Pending approvals",pending.length],["Open failures",p.metrics.open_failures],["Audit events",p.audit_count]
  ].map(([k,v])=>`<div class="metric"><span>${esc(k)}</span><strong>${esc(v)}</strong></div>`).join("");
  $("#phaseSummary").textContent=`${p.phases.filter(x=>x.status==="PASS").length} pass · ${p.phases.filter(x=>x.status==="FAIL").length} failed`;
  $("#phaseTimeline").innerHTML=p.phases.map(ph=>`<div class="phase"><span class="phase-dot ${ph.status.toLowerCase()}"></span><div><div class="name">${esc(ph.label)}</div><div class="detail">generation ${ph.generation}${ph.detail?" · "+esc(ph.detail):""}</div></div>${badge(ph.status)}</div>`).join("");
  const attention=[];
  pending.forEach(a=>attention.push(`<div class="attention"><div class="icon">!</div><div><strong>Human approval required</strong><span>${esc(a.action)} · ${esc(a.proposal_id)}</span></div></div>`));
  p.failures.filter(f=>f.status!=="RESOLVED").forEach(f=>attention.push(`<div class="attention"><div class="icon">↺</div><div><strong>${esc(f.failure_class)}</strong><span>resume at ${esc(f.resume_candidate)}</span></div></div>`));
  if(!attention.length)attention.push('<div class="empty">No operator actions are blocking this project.</div>');
  $("#attentionQueue").innerHTML=attention.join("");
  $("#frontier").innerHTML=p.frontier.map(a=>`<span class="artifact-pill ${a.state.toLowerCase()}">${esc(a.name)} · ${esc(a.state)}</span>`).join("");
  renderApprovals(approvals);renderRecovery();renderDistributed();renderDomain();show(state.view);
}
function renderApprovals(approvals){
  const el=$("#approvalList");if(!approvals.length){el.innerHTML='<div class="empty">No approval records in this snapshot.</div>';return}
  el.innerHTML=approvals.map(a=>`<div class="card"><div class="card-row"><div><h3>${esc(a.action)}</h3><p>${esc(a.policy)} · ${esc(a.proposal_id)}</p></div>${badge(a.status)}</div><p>Exact hash</p><code class="hash">${esc(a.payload_hash)}</code><div class="card-row" style="margin-top:10px"><p>${a.local?"Local UAT decision — reset to restore snapshot":"Frozen payload available for review"}</p><button class="ghost review-btn" data-id="${esc(a.proposal_id)}">Review</button></div></div>`).join("");
  document.querySelectorAll(".review-btn").forEach(b=>b.addEventListener("click",()=>openApproval(b.dataset.id)));
}
function openApproval(id){
  const a=state.project.approvals.find(x=>x.proposal_id===id);if(!a)return;state.activeProposal=a;
  $("#dialogTitle").textContent=a.proposal_id;$("#dialogAction").textContent=a.action;$("#dialogPolicy").textContent=a.policy;$("#dialogHash").textContent=a.payload_hash;$("#dialogPayload").textContent=JSON.stringify(a.payload,null,2);$("#approvalDialog").showModal();
}
function decide(decision){
  const a=state.activeProposal;if(!a)return;
  state.decisions[a.proposal_id]={decision,at:new Date().toISOString(),hash:a.payload_hash};localStorage.setItem("gwr-uat-decisions",JSON.stringify(state.decisions));$("#approvalDialog").close();render();
}
function renderRecovery(){
  const p=state.project, graph=$("#recoveryGraph");
  if(!p.failures.length){graph.innerHTML='<div class="empty">No failures recorded.</div>';$("#failureList").innerHTML="";return}
  const f=p.failures[0],r=f.recovery;graph.innerHTML=[
    ["Detection",f.detected_stage,f.status],["Root cause",f.root_ref,f.root_status],["Recovery",r.recovery_id,r.status],["Resume",r.resume_target,"TARGET"]
  ].map((x,i)=>`${i?'<span class="graph-arrow">→</span>':""}<div class="graph-node"><span class="kind">${esc(x[0])}</span><strong>${esc(x[1])}</strong><div style="margin-top:7px">${badge(x[2])}</div></div>`).join("");
  $("#failureList").innerHTML=p.failures.map(f=>`<div class="card"><div class="card-row"><div><h3>${esc(f.failure_class)}</h3><p>${esc(f.failure_id)} · ${esc(f.severity)}</p></div>${badge(f.status)}</div><p>Detected at <strong>${esc(f.detected_stage)}</strong></p><p>Root <strong>${esc(f.root_ref)}</strong> · resume <strong>${esc(f.resume_candidate)}</strong></p><p>Mark stale: ${esc((f.recovery.mark_stale||[]).join(", ")||"none")}</p></div>`).join("");
}
function renderDistributed(){
  const d=state.project.distributed;
  $("#jobTable").innerHTML=`<table><thead><tr><th>Job</th><th>Work unit</th><th>Status</th><th>Worker</th><th>Attempt</th></tr></thead><tbody>${d.jobs.map(j=>`<tr><td>${esc(j.job_id)}</td><td>${esc(j.workunit)}</td><td>${badge(j.status)}</td><td>${esc(j.worker)}</td><td>${esc(j.attempt)}</td></tr>`).join("")}</tbody></table>`;
  $("#workerList").innerHTML=d.workers.map(w=>`<div class="card"><div class="card-row"><h3>${esc(w.worker_id)}</h3>${badge(w.status)}</div><p>CPU ${esc(w.cpu)} · Memory ${esc(w.memory)}</p><p>${esc(w.labels.join(" · "))}</p><p>heartbeat ${esc(w.last_heartbeat)}</p></div>`).join("");
}
function renderDomain(){
  const d=state.data.product.domain;$("#domainTitle").textContent=d.domain_id;$("#domainSummary").innerHTML=`<p>${esc(d.description)}</p><p class="subtle">version ${esc(d.version)}</p><code class="hash">${esc(d.fingerprint)}</code>`;
  $("#domainCounts").innerHTML=Object.entries(d.counts).map(([k,v])=>`<div class="mini"><span>${esc(k.replaceAll("_"," "))}</span><strong>${esc(v)}</strong></div>`).join("");
}
init().catch(err=>{document.body.innerHTML=`<pre style="padding:30px;color:#ff7188">UAT console failed to load: ${esc(err.message)}</pre>`});
