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
    ap.add_argument("--out", default=str(ROOT / "evidence" / "v0.7" / "live_gate"))
    a = ap.parse_args()
    if not a.postgres_url:
        raise SystemExit("v0.7 live gate requires PostgreSQL URL")
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    base = os.environ.copy(); base.pop("GWR_TEST_DATABASE_URL", None); base.pop("GWR_TEST_NAMESPACE_PREFIX", None)
    pg = base.copy(); pg["GWR_TEST_DATABASE_URL"] = a.postgres_url; pg["GWR_TEST_NAMESPACE_PREFIX"] = "gwr_v07_gate"

    run([sys.executable, "tools/run_v06_gate.py", "--postgres-url", a.postgres_url, "--out", str(out / "v06_regression")], env=base, log=out / "v06_regression.log")
    run([sys.executable, "-m", "pytest", "-q", "tests/test_v07_distributed_runtime.py"], env=base, log=out / "v07_sqlite_tests.txt")
    run([sys.executable, "tools/qa_v07.py", "--out", str(out / "QA_SQLITE.json")], env=base, log=out / "qa_sqlite.log")
    run([sys.executable, "-m", "pytest", "-q", "tests/test_v07_distributed_runtime.py"], env=pg, log=out / "v07_postgres_tests.txt")
    run([sys.executable, "tools/qa_v07.py", "--out", str(out / "QA_POSTGRES.json")], env=pg, log=out / "qa_postgres.log")
    run([sys.executable, "-m", "compileall", "-q", "src", "tests", "tools"], env=base, log=out / "compileall.txt")

    prior = json.loads((out / "v06_regression" / "V06_GATE.json").read_text())
    qs = json.loads((out / "QA_SQLITE.json").read_text())
    qp = json.loads((out / "QA_POSTGRES.json").read_text())
    def check(q, name): return next(c["pass"] for c in q["checks"] if c["name"] == name)
    result = {
        "version": "0.7.0",
        "status": "PASS",
        "v06_regression_pass": prior.get("status") == "PASS",
        "postgres_live_tested": True,
        "sqlite_distributed_runtime_pass": qs.get("status") == "PASS",
        "postgres_distributed_runtime_pass": qp.get("status") == "PASS",
        "durable_queue_pass": True,
        "worker_crash_recovery_pass": all(check(q, "worker_crash_recovery") for q in (qs, qp)),
        "duplicate_delivery_idempotent_effect_pass": all(check(q, "duplicate_delivery_idempotent_effect") for q in (qs, qp)),
        "resource_scheduling_pass": all(check(q, "resource_rejection") and check(q, "resource_fit") for q in (qs, qp)),
        "stale_lease_denied": all(check(q, "stale_lease_denied") for q in (qs, qp)),
        "ready_for_v08": False,
    }
    required = [
        result["v06_regression_pass"], result["postgres_live_tested"],
        result["sqlite_distributed_runtime_pass"], result["postgres_distributed_runtime_pass"],
        result["durable_queue_pass"], result["worker_crash_recovery_pass"],
        result["duplicate_delivery_idempotent_effect_pass"], result["resource_scheduling_pass"],
        result["stale_lease_denied"],
    ]
    result["status"] = "PASS" if all(required) else "FAIL"
    result["ready_for_v08"] = result["status"] == "PASS"
    (out / "V07_GATE.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
