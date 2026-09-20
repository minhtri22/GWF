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
    ap.add_argument("--out", default=str(ROOT / "evidence" / "v0.8.5" / "live_gate"))
    args = ap.parse_args()
    if not args.postgres_url:
        raise SystemExit("v0.8.5 live gate requires PostgreSQL URL")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    base = os.environ.copy()
    base.pop("GWR_TEST_DATABASE_URL", None)
    base.pop("GWR_TEST_NAMESPACE_PREFIX", None)

    pg = base.copy()
    pg["GWR_TEST_DATABASE_URL"] = args.postgres_url
    pg["GWR_TEST_NAMESPACE_PREFIX"] = "gwr_v085_gate"

    run(
        [
            sys.executable,
            "tools/run_v084_gate.py",
            "--postgres-url",
            args.postgres_url,
            "--out",
            str(out / "v084_regression"),
        ],
        env=base,
        log=out / "v084_regression.log",
    )

    tests = [
        "tests/test_v085_domain_skills.py",
        "tests/test_v083_orchestrator_integration.py",
        "tests/test_v084_github_plugin_sha_qa.py",
    ]

    run(
        [sys.executable, "-m", "pytest", "-q", *tests],
        env=base,
        log=out / "v085_sqlite_tests.txt",
    )
    run(
        [sys.executable, "tools/qa_v085.py", "--out", str(out / "QA_SQLITE.json")],
        env=base,
        log=out / "qa_sqlite.log",
    )

    run(
        [sys.executable, "-m", "pytest", "-q", *tests],
        env=pg,
        log=out / "v085_postgres_tests.txt",
    )
    run(
        [sys.executable, "tools/qa_v085.py", "--out", str(out / "QA_POSTGRES.json")],
        env=pg,
        log=out / "qa_postgres.log",
    )

    run(
        [sys.executable, "-m", "compileall", "-q", "src", "tests", "tools"],
        env=base,
        log=out / "compileall.txt",
    )

    prior = json.loads((out / "v084_regression" / "V084_GATE.json").read_text(encoding="utf-8"))
    sqlite_qa = json.loads((out / "QA_SQLITE.json").read_text(encoding="utf-8"))
    postgres_qa = json.loads((out / "QA_POSTGRES.json").read_text(encoding="utf-8"))

    def check(name):
        return all(
            next(c["pass"] for c in q["checks"] if c["name"] == name)
            for q in (sqlite_qa, postgres_qa)
        )

    result = {
        "version": "0.8.5",
        "status": "PASS",
        "v084_regression_pass": prior.get("status") == "PASS",
        "postgres_live_tested": True,
        "sqlite_v085_pass": sqlite_qa.get("status") == "PASS",
        "postgres_v085_pass": postgres_qa.get("status") == "PASS",
        "domain_packages_validate_pass": check("domain_packages_validate"),
        "research_study_lock_pass": check("research_study_lock_contract"),
        "research_governed_execution_pass": check("research_governed_execution"),
        "software_domain_contract_pass": check("software_domain_contract"),
        "software_governed_execution_pass": check("software_governed_execution"),
        "pilot_profiles_pass": check("pilot_profiles"),
        "installer_contract_pass": check("one_click_installer_contract"),
    }
    required = [v for k, v in result.items() if k.endswith("_pass")]
    result["status"] = "PASS" if all(required) else "FAIL"
    (out / "V085_GATE.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
