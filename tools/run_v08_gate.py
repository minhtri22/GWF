from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd, *, env, log):
    p = subprocess.run(cmd, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    Path(log).parent.mkdir(parents=True, exist_ok=True)
    Path(log).write_text(p.stdout, encoding="utf-8")
    print(p.stdout, end="")
    if p.returncode:
        raise RuntimeError(f"command failed ({p.returncode}): {cmd}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--postgres-url", default=os.environ.get("GWR_TEST_DATABASE_URL"))
    ap.add_argument("--out", default=str(ROOT / "evidence" / "v0.8" / "live_gate"))
    a = ap.parse_args()
    if not a.postgres_url:
        raise SystemExit("v0.8 live gate requires PostgreSQL URL")
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    base = os.environ.copy(); base.pop("GWR_TEST_DATABASE_URL", None); base.pop("GWR_TEST_NAMESPACE_PREFIX", None)
    pg = base.copy(); pg["GWR_TEST_DATABASE_URL"] = a.postgres_url; pg["GWR_TEST_NAMESPACE_PREFIX"] = "gwr_v08_gate"

    run([sys.executable, "tools/run_v07_gate.py", "--postgres-url", a.postgres_url, "--out", str(out / "v07_regression")], env=base, log=out / "v07_regression.log")
    run([sys.executable, "-m", "pytest", "-q", "tests/test_v08_research_product_alpha.py", "tests/test_v08_uat_site.py"], env=base, log=out / "v08_sqlite_tests.txt")
    run([sys.executable, "tools/qa_v08.py", "--out", str(out / "QA_SQLITE.json")], env=base, log=out / "qa_sqlite.log")
    run([sys.executable, "-m", "pytest", "-q", "tests/test_v08_research_product_alpha.py", "tests/test_v08_uat_site.py"], env=pg, log=out / "v08_postgres_tests.txt")
    run([sys.executable, "tools/qa_v08.py", "--out", str(out / "QA_POSTGRES.json")], env=pg, log=out / "qa_postgres.log")
    site = out / "uat_site"
    run([sys.executable, "tools/build_uat_site.py", "--out", str(site), "--commit", os.environ.get("GITHUB_SHA", "gate")], env=base, log=out / "uat_build.log")
    run([sys.executable, "-m", "compileall", "-q", "src", "tests", "tools"], env=base, log=out / "compileall.txt")

    prior = json.loads((out / "v07_regression" / "V07_GATE.json").read_text())
    qs = json.loads((out / "QA_SQLITE.json").read_text())
    qp = json.loads((out / "QA_POSTGRES.json").read_text())
    meta = json.loads((site / "build-meta.json").read_text())
    html = (site / "index.html").read_text(encoding="utf-8")
    required_ui = all(label in html for label in ("Pending approvals", "Failure & recovery", "Distributed runtime", "Domain SDK"))
    result = {
        "version": "0.8.0",
        "status": "PASS",
        "v07_regression_pass": prior.get("status") == "PASS",
        "postgres_live_tested": True,
        "sqlite_product_alpha_pass": qs.get("status") == "PASS",
        "postgres_product_alpha_pass": qp.get("status") == "PASS",
        "domain_sdk_pass": all(next(c["pass"] for c in q["checks"] if c["name"] == "domain_sdk_validate") for q in (qs, qp)),
        "operator_dashboard_pass": all(next(c["pass"] for c in q["checks"] if c["name"] == "dashboard_read_model") for q in (qs, qp)),
        "human_approval_ux_contract_pass": all(next(c["pass"] for c in q["checks"] if c["name"] == "authenticated_exact_hash_rejection") for q in (qs, qp)),
        "failure_recovery_visualization_data_pass": all(next(c["pass"] for c in q["checks"] if c["name"] == "failure_recovery_graph") for q in (qs, qp)),
        "uat_site_build_pass": meta.get("version") in {"0.8.0", "0.8.1"} and meta.get("mode") == "STATIC_UAT" and required_ui,
        "ready_for_uat": False,
    }
    required = [v for k, v in result.items() if k.endswith("_pass")]
    result["status"] = "PASS" if all(required) else "FAIL"
    result["ready_for_uat"] = result["status"] == "PASS"
    (out / "V08_GATE.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
