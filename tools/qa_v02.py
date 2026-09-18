from __future__ import annotations

from pathlib import Path
import ast
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
errors=[]
warnings=[]

def err(x): errors.append(x)
def warn(x): warnings.append(x)

# Parse every Python module/test/tool.
for p in sorted(ROOT.rglob("*.py")):
    try: ast.parse(p.read_text(encoding="utf-8"))
    except Exception as e: err(f"PY_PARSE {p.relative_to(ROOT)}: {e}")

# Research domain structural checks.
d = yaml.safe_load((ROOT/"domains"/"research.workflow.yaml").read_text(encoding="utf-8"))
phases=[w for w in d.get("workunit_templates",[]) if w.get("id","").startswith("phase_")]
if len(phases)!=17: err(f"Expected 17 research phases, found {len(phases)}")
expected=[f"phase_{i:02d}" for i in range(17)]
for i,p in enumerate(phases):
    if not p["id"].startswith(expected[i]): err(f"Phase order mismatch at {i}: {p['id']}")
    cp=p.get("checkpoint_policy",{})
    if not cp.get("after_success"): err(f"{p['id']} lacks after_success checkpoint")
    if not cp.get("on_failure"): err(f"{p['id']} lacks on_failure checkpoint")
    if not p.get("required_gate_types"): err(f"{p['id']} lacks completion gate")
    if not p.get("known_failure_modes"): err(f"{p['id']} lacks failure modes")

outcomes=set(d.get("research_outcome_policy",{}).get("authoritative_values",[]))
if outcomes!={"PASS","FAIL","PIVOT"}: err(f"Outcome contract mismatch: {outcomes}")
cp=d.get("checkpoint_policy",{})
for req in ["AFTER_EVERY_PHASE_PASS","ON_ANY_FAILURE","ON_PASS_FAIL_PIVOT_DECISION"]:
    if req not in cp.get("create",[]): err(f"Missing checkpoint rule {req}")
resume=cp.get("resume",{})
if resume.get("route_by")!="EARLIEST_INVALID_ANCESTOR": err("Resume route must use EARLIEST_INVALID_ANCESTOR")
if resume.get("rerun_mode")!="MINIMAL_AFFECTED_SUBGRAPH": err("Resume must rerun minimal affected subgraph")

# Implementation mapping checks.
required_files=[
    "src/gwr/research_orchestrator.py", "src/gwr/research_demo.py",
    "tests/test_research_orchestrator.py", "tools/run_research_demo.py",
]
for rel in required_files:
    if not (ROOT/rel).exists(): err(f"Missing {rel}")
text=(ROOT/"src/gwr/research_orchestrator.py").read_text(encoding="utf-8")
for token in ["PASS", "FAIL", "PIVOT", "create_checkpoint", "resume", "create_recovery_plan", "apply_recovery_plan", "earliest_resume_artifact"]:
    if token not in text: err(f"Orchestrator missing semantic token {token}")

print(f"research_phases={len(phases)}")
print(f"artifact_types={len(d.get('artifact_types',[]))}")
print(f"gate_types={len(d.get('gate_types',[]))}")
print(f"failure_types={len(d.get('failure_types',[]))}")
print(f"errors={len(errors)} warnings={len(warnings)}")
for x in errors: print("ERROR",x)
for x in warnings: print("WARN",x)
if errors:
    print("RESULT=FAIL")
    raise SystemExit(1)
print("RESULT=PASS")
