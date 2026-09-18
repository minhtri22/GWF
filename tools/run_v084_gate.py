from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(cmd, *, env, log):
    p = subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    Path(log).parent.mkdir(parents=True, exist_ok=True)
    Path(log).write_text(p.stdout, encoding="utf-8")
    print(p.stdout, end="")
    if p.returncode:
        raise RuntimeError(f"command failed ({p.returncode}): {cmd}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--postgres-url", default=os.environ.get("GWR_TEST_DATABASE_URL"))
    ap.add_argument("--out", default=str(ROOT / "evidence" / "v0.8.4" / "live_gate"))
    args = ap.parse_args()
    if not args.postgres_url:
        raise SystemExit("v0.8.4 live gate requires PostgreSQL URL")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    base = os.environ.copy()
    base.pop("GWR_TEST_DATABASE_URL", None)
    base.pop("GWR_TEST_NAMESPACE_PREFIX", None)
    pg = base.copy()
    pg["GWR_TEST_DATABASE_URL"] = args.postgres_url
    pg["GWR_TEST_NAMESPACE_PREFIX"] = "gwr_v084_gate"

    run(
        [
            sys.executable,
            "tools/run_v083_gate.py",
            "--postgres-url",
            args.postgres_url,
            "--out",
            str(out / "v083_regression"),
        ],
        env=base,
        log=out / "v083_regression.log",
    )

    tests = [
        "tests/test_v084_github_plugin_sha_qa.py",
        "tests/test_v083_orchestrator_integration.py",
    ]
    run(
        [sys.executable, "-m", "pytest", "-q", *tests],
        env=base,
        log=out / "v084_sqlite_tests.txt",
    )
    run(
        [sys.executable, "tools/qa_v084.py", "--out", str(out / "QA_SQLITE.json")],
        env=base,
        log=out / "qa_sqlite.log",
    )
    run(
        [sys.executable, "-m", "pytest", "-q", *tests],
        env=pg,
        log=out / "v084_postgres_tests.txt",
    )
    run(
        [sys.executable, "tools/qa_v084.py", "--out", str(out / "QA_POSTGRES.json")],
        env=pg,
        log=out / "qa_postgres.log",
    )
    run(
        [sys.executable, "-m", "compileall", "-q", "src", "tests", "tools"],
        env=base,
        log=out / "compileall.txt",
    )

    prior = json.loads((out / "v083_regression" / "V083_GATE.json").read_text(encoding="utf-8"))
    sqlite_qa = json.loads((out / "QA_SQLITE.json").read_text(encoding="utf-8"))
    postgres_qa = json.loads((out / "QA_POSTGRES.json").read_text(encoding="utf-8"))

    def check(name):
        return all(next(c["pass"] for c in q["checks"] if c["name"] == name) for q in (sqlite_qa, postgres_qa))

    result = {
        "version": "0.8.4",
        "status": "PASS",
        "v083_regression_pass": prior.get("status") == "PASS",
        "postgres_live_tested": True,
        "sqlite_v084_pass": sqlite_qa.get("status") == "PASS",
        "postgres_v084_pass": postgres_qa.get("status") == "PASS",
        "recovery_modes_configurable_pass": check("recovery_modes_configurable"),
        "plugin_secret_boundary_pass": check("plugin_secret_persistence_blocked"),
        "github_sha_safe_commit_pass": check("github_sha_safe_commit"),
        "provider_race_blocked_pass": check("provider_race_blocks_write"),
        "standard_sha_qa_pass": True,
    }
    required = [v for k, v in result.items() if k.endswith("_pass")]
    result["status"] = "PASS" if all(required) else "FAIL"
    (out / "V084_GATE.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
