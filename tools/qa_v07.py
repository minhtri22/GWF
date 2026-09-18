from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from gwr.errors import LeaseLost
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import canonical_json, uid

ROOT = Path(__file__).resolve().parents[1]


def workunit(rt, project, conflict=None):
    wid = uid("wu")
    rt.db.conn.execute(
        "INSERT INTO workunits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (wid, project, "execute_plan", "[]", "[]", "[]", "[]", "[]", '{"role":"operator"}',
         "{}", '{"max_attempts":3}', "{}", canonical_json(conflict or []), "READY", 0),
    )
    rt.db.conn.commit()
    return wid


def actor(rt, project, name):
    return rt.governance.create_actor("AGENT", name, ["operator"], [project])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    checks = []
    with tempfile.TemporaryDirectory() as td:
        rt = GovernedWorkflowRuntime(str(ROOT / "domains" / "example.workflow.yaml"), str(Path(td) / "v07.db"))
        backend = rt.db.backend_name
        required = {"worker_nodes", "distributed_jobs", "job_attempts", "effect_commits", "scheduler_events"}
        tables = set(rt.db.list_tables())
        checks.append({"name": "v07_tables", "pass": required.issubset(tables), "missing": sorted(required - tables)})
        checks.append({"name": "v07_migration", "pass": "0003_v07_distributed_runtime" in rt.db.migrations.status()["applied"]})

        p = rt.create_project("chaos")
        a1 = actor(rt, p, "chaos-1"); a2 = actor(rt, p, "chaos-2")
        w1 = rt.distributed.register_worker(a1, capabilities={"labels": ["python"]}, resources={"cpu": 2, "memory_mb": 1024})
        w2 = rt.distributed.register_worker(a2, capabilities={"labels": ["python"]}, resources={"cpu": 4, "memory_mb": 4096})

        wr = workunit(rt, p)
        jr = rt.distributed.enqueue_workunit(wr, idempotency_key="qa-resource", required_resources={"cpu": 3})
        checks.append({"name": "resource_rejection", "pass": rt.distributed.lease_next(w1) is None})
        lr = rt.distributed.lease_next(w2)
        checks.append({"name": "resource_fit", "pass": bool(lr and lr["job_id"] == jr)})
        rt.distributed.start_job(jr, w2, lr["lease_token"])
        rt.distributed.complete_job(jr, w2, lr["lease_token"], effect_key="qa:resource", result={"ok": True})

        wc = workunit(rt, p)
        jc = rt.distributed.enqueue_workunit(wc, idempotency_key="qa-crash")
        lc = rt.distributed.lease_next(w1)
        started = rt.distributed.start_job(jc, w1, lc["lease_token"])
        rt.db.conn.execute("UPDATE distributed_jobs SET lease_expires_at='2000-01-01T00:00:00+00:00' WHERE job_id=?", (jc,))
        rt.db.conn.commit()
        recovered = rt.distributed.recover_expired_leases()
        run = rt.db.one("SELECT runtime_status FROM runs WHERE run_id=?", (started["run_id"],))
        checks.append({"name": "worker_crash_recovery", "pass": jc in recovered and run["runtime_status"] == "ABANDONED" and rt.distributed.get_job(jc)["status"] == "READY"})
        stale_denied = False
        try:
            rt.distributed.start_job(jc, w1, lc["lease_token"])
        except LeaseLost:
            stale_denied = True
        checks.append({"name": "stale_lease_denied", "pass": stale_denied})

        ld = rt.distributed.lease_next(w2)
        rt.distributed.start_job(jc, w2, ld["lease_token"])
        rt.distributed.commit_effect(jc, w2, ld["lease_token"], "qa:dedupe", {"n": 1})
        rt.db.conn.execute("UPDATE distributed_jobs SET lease_expires_at='2000-01-01T00:00:00+00:00' WHERE job_id=?", (jc,))
        rt.db.conn.commit()
        rt.distributed.recover_expired_leases()
        l3 = rt.distributed.lease_next(w1)
        rt.distributed.start_job(jc, w1, l3["lease_token"])
        dedupe = rt.distributed.commit_effect(jc, w1, l3["lease_token"], "qa:dedupe", {"n": 1})
        final = rt.distributed.complete_job(jc, w1, l3["lease_token"], effect_key="qa:dedupe", result={"n": 1})
        effect_count = rt.db.one("SELECT COUNT(*) n FROM effect_commits WHERE effect_key='qa:dedupe'")["n"]
        checks.append({"name": "duplicate_delivery_idempotent_effect", "pass": dedupe["duplicate"] is True and final["status"] == "SUCCEEDED" and effect_count == 1})

        events = rt.db.one("SELECT COUNT(*) n FROM scheduler_events")["n"]
        checks.append({"name": "scheduler_events", "pass": events >= 8, "count": events})
        rt.close()

    errors = [c for c in checks if not c["pass"]]
    result = {"version": "0.7.0", "backend": backend, "status": "PASS" if not errors else "FAIL", "checks": checks, "errors": errors}
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if not errors else 1)


if __name__ == "__main__":
    main()
