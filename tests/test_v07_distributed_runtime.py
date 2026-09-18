from __future__ import annotations

from pathlib import Path

import pytest

from gwr.errors import IdempotencyConflict, LeaseLost
from gwr.runtime import GovernedWorkflowRuntime
from gwr.utils import canonical_json, uid

ROOT = Path(__file__).parents[1]


def make_runtime(tmp_path, name="dist.db"):
    return GovernedWorkflowRuntime(str(ROOT / "domains" / "example.workflow.yaml"), str(tmp_path / name))


def worker_actor(rt, project, name):
    return rt.governance.create_actor("AGENT", name, ["operator"], [project])


def ready_workunit(rt, project, *, conflict_keys=None, resources=None, required_capabilities=None):
    wid = uid("wu")
    rt.db.conn.execute(
        "INSERT INTO workunits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            wid, project, "execute_plan", canonical_json([]), canonical_json([]), canonical_json([]),
            canonical_json([]), canonical_json([]), canonical_json({"role": "operator"}),
            canonical_json({"resources": resources or {}, "required_capabilities": required_capabilities or []}),
            canonical_json({"max_attempts": 3}), canonical_json({}), canonical_json(conflict_keys or []),
            "READY", 0,
        ),
    )
    rt.db.conn.commit()
    return wid


def test_v07_migration_installs_distributed_tables(tmp_path):
    rt = make_runtime(tmp_path)
    tables = set(rt.db.list_tables())
    assert {"worker_nodes", "distributed_jobs", "job_attempts", "effect_commits", "scheduler_events"}.issubset(tables)
    assert "0003_v07_distributed_runtime" in rt.db.migrations.status()["applied"]
    assert rt.db.migrations.status()["pending"] == []
    rt.close()


def test_durable_queue_survives_runtime_restart(tmp_path):
    path = "durable.db"
    rt = make_runtime(tmp_path, path)
    project = rt.create_project("durable")
    wid = ready_workunit(rt, project)
    job = rt.distributed.enqueue_workunit(wid, idempotency_key="durable-job")
    rt.close()

    rt = make_runtime(tmp_path, path)
    row = rt.distributed.get_job(job)
    assert row["status"] == "READY"
    assert row["workunit_id"] == wid
    assert rt.db.one("SELECT COUNT(*) n FROM scheduler_events WHERE job_id=?", (job,))["n"] >= 1
    rt.close()


def test_resource_scheduler_and_global_conflict_keys(tmp_path):
    rt = make_runtime(tmp_path)
    p = rt.create_project("resources")
    a1 = worker_actor(rt, p, "small")
    a2 = worker_actor(rt, p, "large")
    w1 = rt.distributed.register_worker(a1, capabilities={"labels": ["python"]}, resources={"cpu": 1, "memory_mb": 512})
    w2 = rt.distributed.register_worker(a2, capabilities={"labels": ["python"]}, resources={"cpu": 4, "memory_mb": 4096})
    wu1 = ready_workunit(rt, p, conflict_keys=["gpu:0"])
    j1 = rt.distributed.enqueue_workunit(wu1, idempotency_key="r1", required_resources={"cpu": 2, "memory_mb": 1024}, required_capabilities=["python"])

    # With only the oversized job present, the small worker must reject it.
    assert rt.distributed.lease_next(w1) is None
    l1 = rt.distributed.lease_next(w2)
    assert l1["job_id"] == j1

    # Once gpu:0 is leased by the large worker, a second fitting job using the
    # same conflict key must not be leased by another worker.
    wu2 = ready_workunit(rt, p, conflict_keys=["gpu:0"])
    j2 = rt.distributed.enqueue_workunit(wu2, idempotency_key="r2", required_resources={"cpu": 1}, required_capabilities=["python"])
    assert rt.distributed.lease_next(w1) is None
    rt.distributed.start_job(j1, w2, l1["lease_token"])
    rt.distributed.fail_job(j1, w2, l1["lease_token"], error_code="TEST", retryable=False)
    l2 = rt.distributed.lease_next(w1)
    assert l2["job_id"] == j2
    rt.close()


def test_heartbeat_extends_lease_and_stale_token_is_rejected(tmp_path):
    rt = make_runtime(tmp_path)
    p = rt.create_project("heartbeat")
    a = worker_actor(rt, p, "worker")
    w = rt.distributed.register_worker(a, resources={"cpu": 2, "memory_mb": 1024})
    wu = ready_workunit(rt, p)
    j = rt.distributed.enqueue_workunit(wu, idempotency_key="hb")
    lease = rt.distributed.lease_next(w, lease_seconds=5)
    old = lease["lease_expires_at"]
    new = rt.distributed.heartbeat_job(j, w, lease["lease_token"], lease_seconds=60)
    assert new > old
    rt.db.conn.execute("UPDATE distributed_jobs SET lease_expires_at='2000-01-01T00:00:00+00:00' WHERE job_id=?", (j,))
    rt.db.conn.commit()
    assert j in rt.distributed.recover_expired_leases()
    with pytest.raises(LeaseLost):
        rt.distributed.start_job(j, w, lease["lease_token"])
    rt.close()


def test_worker_crash_requeues_abandons_run_and_second_worker_finishes(tmp_path):
    rt = make_runtime(tmp_path)
    p = rt.create_project("crash")
    a1 = worker_actor(rt, p, "crash-worker")
    a2 = worker_actor(rt, p, "recovery-worker")
    w1 = rt.distributed.register_worker(a1, resources={"cpu": 2, "memory_mb": 1024})
    w2 = rt.distributed.register_worker(a2, resources={"cpu": 2, "memory_mb": 1024})
    wu = ready_workunit(rt, p)
    j = rt.distributed.enqueue_workunit(wu, idempotency_key="crash")
    l1 = rt.distributed.lease_next(w1, lease_seconds=5)
    started = rt.distributed.start_job(j, w1, l1["lease_token"])
    rt.db.conn.execute("UPDATE distributed_jobs SET lease_expires_at='2000-01-01T00:00:00+00:00' WHERE job_id=?", (j,))
    rt.db.conn.commit()
    rt.distributed.recover_expired_leases()
    assert rt.db.one("SELECT runtime_status FROM runs WHERE run_id=?", (started["run_id"],))["runtime_status"] == "ABANDONED"
    assert rt.distributed.get_job(j)["status"] == "READY"

    l2 = rt.distributed.lease_next(w2)
    rt.distributed.start_job(j, w2, l2["lease_token"])
    done = rt.distributed.complete_job(j, w2, l2["lease_token"], effect_key="effect:crash", result={"ok": True})
    assert done["status"] == "SUCCEEDED"
    assert rt.distributed.get_job(j)["attempt_count"] == 2
    assert rt.db.one("SELECT COUNT(*) n FROM effect_commits WHERE job_id=?", (j,))["n"] == 1
    rt.close()


def test_duplicate_delivery_reuses_exactly_once_authoritative_effect(tmp_path):
    rt = make_runtime(tmp_path)
    p = rt.create_project("duplicate")
    a1 = worker_actor(rt, p, "first")
    a2 = worker_actor(rt, p, "second")
    w1 = rt.distributed.register_worker(a1, resources={"cpu": 1, "memory_mb": 256})
    w2 = rt.distributed.register_worker(a2, resources={"cpu": 1, "memory_mb": 256})
    wu = ready_workunit(rt, p)
    j = rt.distributed.enqueue_workunit(wu, idempotency_key="dup")
    l1 = rt.distributed.lease_next(w1)
    rt.distributed.start_job(j, w1, l1["lease_token"])
    first = rt.distributed.commit_effect(j, w1, l1["lease_token"], "effect:dup", {"value": 7})
    assert first["duplicate"] is False

    rt.db.conn.execute("UPDATE distributed_jobs SET lease_expires_at='2000-01-01T00:00:00+00:00' WHERE job_id=?", (j,))
    rt.db.conn.commit()
    rt.distributed.recover_expired_leases()
    l2 = rt.distributed.lease_next(w2)
    rt.distributed.start_job(j, w2, l2["lease_token"])
    replay = rt.distributed.commit_effect(j, w2, l2["lease_token"], "effect:dup", {"value": 7})
    assert replay["duplicate"] is True
    done = rt.distributed.complete_job(j, w2, l2["lease_token"], effect_key="effect:dup", result={"value": 7})
    assert done["duplicate"] is True
    assert rt.db.one("SELECT COUNT(*) n FROM effect_commits WHERE effect_key='effect:dup'")["n"] == 1
    with pytest.raises(IdempotencyConflict):
        rt.distributed.complete_job(j, w2, l2["lease_token"], effect_key="effect:dup", result={"value": 8})
    rt.close()


def test_enqueue_idempotency_rejects_payload_drift(tmp_path):
    rt = make_runtime(tmp_path)
    p = rt.create_project("idempotency")
    wu = ready_workunit(rt, p)
    j1 = rt.distributed.enqueue_workunit(wu, idempotency_key="same", required_resources={"cpu": 1})
    j2 = rt.distributed.enqueue_workunit(wu, idempotency_key="same", required_resources={"cpu": 1})
    assert j1 == j2
    with pytest.raises(IdempotencyConflict):
        rt.distributed.enqueue_workunit(wu, idempotency_key="same", required_resources={"cpu": 2})
    rt.close()
