from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .errors import IdempotencyConflict, InvalidTransition, LeaseLost, NotFound, ValidationError
from .utils import canonical_json, content_hash, parse_json, uid, utcnow


ACTIVE_JOB_STATES = {"LEASED", "RUNNING"}


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _future(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=int(seconds))).isoformat()


def _normalize_resources(value: dict[str, Any] | None) -> dict[str, float]:
    raw = value or {}
    out: dict[str, float] = {}
    for key in ("cpu", "memory_mb", "gpu"):
        v = float(raw.get(key, 0) or 0)
        if v < 0:
            raise ValidationError(f"resource {key} must be non-negative")
        out[key] = v
    return out


class DistributedRuntime:
    """Durable database-backed scheduler/worker coordination for GWR.

    Delivery is at-least-once. Authoritative effects are committed exactly once
    through the effect_commits ledger using an application-supplied effect key.
    """

    def __init__(self, db, execution, governance, observer=None):
        self.db = db
        self.execution = execution
        self.gov = governance
        self.observer = observer
        self.project_governance = None

    def bind_project_governance(self, service):
        self.project_governance = service

    def _emit(self, event: str, **attrs):
        if self.observer:
            self.observer.emit(event, **attrs)

    def _event(self, project_id: str | None, job_id: str | None, worker_id: str | None, event_type: str, metadata=None):
        eid = uid("sched")
        self.db.conn.execute(
            "INSERT INTO scheduler_events VALUES(?,?,?,?,?,?,?)",
            (eid, project_id, job_id, worker_id, event_type, canonical_json(metadata or {}), utcnow()),
        )
        if project_id:
            self.gov.append_audit(
                project_id, "SYSTEM", event_type, "DistributedJob", job_id or eid,
                reason_code=event_type, metadata=metadata or {},
            )
        self._emit(event_type.lower(), project_id=project_id, job_id=job_id, worker_id=worker_id, **(metadata or {}))
        return eid

    def register_worker(self, actor_id: str, *, capabilities=None, resources=None, heartbeat_ttl_seconds: int = 60, metadata=None) -> str:
        actor = self.db.one("SELECT * FROM actors WHERE actor_id=?", (actor_id,))
        if not actor or actor["status"] != "ACTIVE":
            raise NotFound("Active worker actor not found")
        if heartbeat_ttl_seconds < 2:
            raise ValidationError("heartbeat_ttl_seconds must be >= 2")
        wid = uid("worker")
        self.db.conn.execute(
            "INSERT INTO worker_nodes VALUES(?,?,?,?,?,?,?,?,?)",
            (wid, actor_id, "ACTIVE", canonical_json(capabilities or {}), canonical_json(_normalize_resources(resources)),
             int(heartbeat_ttl_seconds), utcnow(), utcnow(), canonical_json(metadata or {})),
        )
        self.db.conn.commit()
        self._emit("worker_registered", worker_id=wid, actor_id=actor_id)
        return wid

    def heartbeat_worker(self, worker_id: str):
        w = self.db.one("SELECT * FROM worker_nodes WHERE worker_id=?", (worker_id,))
        if not w:
            raise NotFound("Worker not found")
        if w["status"] != "ACTIVE":
            raise InvalidTransition("Worker is not ACTIVE")
        self.db.conn.execute("UPDATE worker_nodes SET last_heartbeat_at=? WHERE worker_id=?", (utcnow(), worker_id))
        self.db.conn.commit()

    def set_worker_status(self, worker_id: str, status: str):
        if status not in {"ACTIVE", "DRAINING", "OFFLINE"}:
            raise ValidationError("Invalid worker status")
        if not self.db.one("SELECT 1 FROM worker_nodes WHERE worker_id=?", (worker_id,)):
            raise NotFound("Worker not found")
        self.db.conn.execute("UPDATE worker_nodes SET status=? WHERE worker_id=?", (status, worker_id))
        self.db.conn.commit()

    def _workunit(self, workunit_id: str):
        row = self.db.one("SELECT * FROM workunits WHERE workunit_id=?", (workunit_id,))
        if not row:
            raise NotFound("WorkUnit not found")
        return row

    def enqueue_workunit(
        self,
        workunit_id: str,
        *,
        idempotency_key: str,
        required_resources=None,
        required_capabilities=None,
        priority: int = 0,
        available_at: str | None = None,
        max_attempts: int | None = None,
    ) -> str:
        if not idempotency_key:
            raise ValidationError("idempotency_key is required")
        wu = self._workunit(workunit_id)
        if self.project_governance:
            self.project_governance.require_mutable(wu["project_id"])
        if wu["status"] != "READY":
            raise InvalidTransition(f"WorkUnit is {wu['status']}, not READY")
        execution_policy = parse_json(wu["execution_policy"], {}) or {}
        req_resources = _normalize_resources(required_resources if required_resources is not None else execution_policy.get("resources"))
        req_caps = list(required_capabilities if required_capabilities is not None else execution_policy.get("required_capabilities", []))
        retry = parse_json(wu["retry_policy"], {}) or {}
        attempts = int(max_attempts if max_attempts is not None else retry.get("max_attempts", 1))
        if attempts < 1:
            raise ValidationError("max_attempts must be >= 1")
        payload = {
            "workunit_id": workunit_id,
            "required_resources": req_resources,
            "required_capabilities": sorted(req_caps),
            "priority": int(priority),
            "max_attempts": attempts,
        }
        ph = content_hash(payload)
        existing = self.db.one("SELECT * FROM distributed_jobs WHERE workunit_id=? OR idempotency_key=?", (workunit_id, idempotency_key))
        if existing:
            if existing["payload_hash"] != ph or existing["idempotency_key"] != idempotency_key:
                raise IdempotencyConflict("Distributed enqueue idempotency conflict")
            return existing["job_id"]
        jid = uid("job")
        now = utcnow()
        self.db.conn.execute(
            "INSERT INTO distributed_jobs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (jid, wu["project_id"], workunit_id, "READY", int(priority), canonical_json(req_resources),
             canonical_json(sorted(req_caps)), idempotency_key, ph, available_at or now, None, None, None,
             0, attempts, None, None, now, now),
        )
        self._event(wu["project_id"], jid, None, "JOB_ENQUEUED", {"workunit_id": workunit_id})
        self.db.conn.commit()
        return jid

    def _require_worker(self, worker_id: str):
        w = self.db.one("SELECT * FROM worker_nodes WHERE worker_id=?", (worker_id,))
        if not w:
            raise NotFound("Worker not found")
        if w["status"] != "ACTIVE":
            raise InvalidTransition(f"Worker is {w['status']}, not ACTIVE")
        ttl = int(w["heartbeat_ttl_seconds"])
        if _dt(w["last_heartbeat_at"]) + timedelta(seconds=ttl) < datetime.now(timezone.utc):
            self.db.conn.execute("UPDATE worker_nodes SET status='OFFLINE' WHERE worker_id=?", (worker_id,))
            self.db.conn.commit()
            raise InvalidTransition("Worker heartbeat expired")
        return w

    def _used_resources(self, worker_id: str) -> dict[str, float]:
        used = {"cpu": 0.0, "memory_mb": 0.0, "gpu": 0.0}
        rows = self.db.all(
            "SELECT required_resources FROM distributed_jobs WHERE lease_worker_id=? AND status IN ('LEASED','RUNNING')",
            (worker_id,),
        )
        for row in rows:
            res = _normalize_resources(parse_json(row["required_resources"], {}))
            for key in used:
                used[key] += res[key]
        return used

    @staticmethod
    def _fits(total: dict[str, float], used: dict[str, float], required: dict[str, float]) -> bool:
        return all(used[k] + required[k] <= total[k] for k in ("cpu", "memory_mb", "gpu"))

    @staticmethod
    def _capable(worker, workunit, required_caps: list[str]) -> bool:
        caps = parse_json(worker["capabilities"], {}) or {}
        types = set(caps.get("workunit_types", []) or [])
        labels = set(caps.get("labels", []) or [])
        if types and workunit["workunit_type"] not in types:
            return False
        return set(required_caps).issubset(labels)

    def _conflicts_with_active(self, workunit) -> bool:
        wanted = set(parse_json(workunit["resource_conflict_keys"], []) or [])
        if not wanted:
            return False
        rows = self.db.all(
            "SELECT w.resource_conflict_keys FROM distributed_jobs j "
            "JOIN workunits w ON w.workunit_id=j.workunit_id "
            "WHERE j.status IN ('LEASED','RUNNING')"
        )
        return any(wanted & set(parse_json(row["resource_conflict_keys"], []) or []) for row in rows)

    def lease_next(self, worker_id: str, *, lease_seconds: int = 30):
        if lease_seconds < 1:
            raise ValidationError("lease_seconds must be >= 1")
        self.recover_expired_leases()
        worker = self._require_worker(worker_id)
        total = _normalize_resources(parse_json(worker["resources_total"], {}))
        used = self._used_resources(worker_id)
        now = utcnow()
        candidates = self.db.all(
            "SELECT * FROM distributed_jobs WHERE status='READY' AND available_at<=? "
            "ORDER BY priority DESC, created_at ASC, job_id ASC",
            (now,),
        )
        for job in candidates:
            wu = self._workunit(job["workunit_id"])
            required = _normalize_resources(parse_json(job["required_resources"], {}))
            caps = list(parse_json(job["required_capabilities"], []) or [])
            if not self._fits(total, used, required):
                continue
            if not self._capable(worker, wu, caps):
                continue
            try:
                self.gov.authorize(worker["actor_id"], "EXECUTE", {"project_id": wu["project_id"], "workunit_type": wu["workunit_type"]})
            except Exception:
                continue
            if self._conflicts_with_active(wu):
                continue
            token = uid("lease")
            expires = _future(lease_seconds)
            attempt_no = int(job["attempt_count"]) + 1
            with self.db.tx():
                cur = self.db.conn.execute(
                    "UPDATE distributed_jobs SET status='LEASED',lease_worker_id=?,lease_token=?,lease_expires_at=?,"
                    "attempt_count=?,updated_at=? WHERE job_id=? AND status='READY'",
                    (worker_id, token, expires, attempt_no, utcnow(), job["job_id"]),
                )
                if getattr(cur, "rowcount", 1) != 1:
                    continue
                aid = uid("attempt")
                self.db.conn.execute(
                    "INSERT INTO job_attempts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (aid, job["job_id"], attempt_no, worker_id, token, None, "LEASED", utcnow(), utcnow(), expires, None, None, canonical_json({})),
                )
                self._event(job["project_id"], job["job_id"], worker_id, "JOB_LEASED", {"attempt": attempt_no})
            return {
                "job_id": job["job_id"],
                "workunit_id": job["workunit_id"],
                "lease_token": token,
                "lease_expires_at": expires,
                "attempt_number": attempt_no,
                "required_resources": required,
            }
        return None

    def _active_lease(self, job_id: str, worker_id: str, lease_token: str):
        job = self.db.one("SELECT * FROM distributed_jobs WHERE job_id=?", (job_id,))
        if not job:
            raise NotFound("Distributed job not found")
        if job["status"] not in ACTIVE_JOB_STATES:
            raise LeaseLost(f"Job is {job['status']}, lease is no longer active")
        if job["lease_worker_id"] != worker_id or job["lease_token"] != lease_token:
            raise LeaseLost("Lease token or worker mismatch")
        if not job["lease_expires_at"] or _dt(job["lease_expires_at"]) <= datetime.now(timezone.utc):
            raise LeaseLost("Lease expired")
        return job

    def start_job(self, job_id: str, worker_id: str, lease_token: str):
        job = self._active_lease(job_id, worker_id, lease_token)
        if job["status"] != "LEASED":
            attempt = self.db.one("SELECT * FROM job_attempts WHERE job_id=? AND attempt_number=?", (job_id, job["attempt_count"]))
            return {"job_id": job_id, "run_id": attempt["run_id"], "attempt_number": job["attempt_count"]}
        worker = self._require_worker(worker_id)
        wu = self._workunit(job["workunit_id"])
        result = self.execution.start_run(
            wu["workunit_id"], worker["actor_id"], wu["version"],
            f"distributed:start:{job_id}:{job['attempt_count']}", uid("corr"),
        )
        with self.db.tx():
            self.db.conn.execute("UPDATE distributed_jobs SET status='RUNNING',updated_at=? WHERE job_id=?", (utcnow(), job_id))
            self.db.conn.execute(
                "UPDATE job_attempts SET status='RUNNING',run_id=?,heartbeat_at=? WHERE job_id=? AND attempt_number=?",
                (result["run_id"], utcnow(), job_id, job["attempt_count"]),
            )
            self._event(job["project_id"], job_id, worker_id, "JOB_STARTED", {"run_id": result["run_id"]})
        return {"job_id": job_id, "run_id": result["run_id"], "attempt_number": job["attempt_count"]}

    def heartbeat_job(self, job_id: str, worker_id: str, lease_token: str, *, lease_seconds: int = 30):
        job = self._active_lease(job_id, worker_id, lease_token)
        expires = _future(lease_seconds)
        with self.db.tx():
            self.db.conn.execute("UPDATE distributed_jobs SET lease_expires_at=?,updated_at=? WHERE job_id=?", (expires, utcnow(), job_id))
            self.db.conn.execute(
                "UPDATE job_attempts SET heartbeat_at=?,lease_expires_at=? WHERE job_id=? AND attempt_number=?",
                (utcnow(), expires, job_id, job["attempt_count"]),
            )
            self.db.conn.execute("UPDATE worker_nodes SET last_heartbeat_at=? WHERE worker_id=?", (utcnow(), worker_id))
        return expires

    def commit_effect(self, job_id: str, worker_id: str, lease_token: str, effect_key: str, result: Any):
        if not effect_key:
            raise ValidationError("effect_key is required")
        ph = content_hash(result)
        existing = self.db.one("SELECT * FROM effect_commits WHERE effect_key=?", (effect_key,))
        if existing:
            if existing["payload_hash"] != ph or existing["job_id"] != job_id:
                raise IdempotencyConflict("Effect key reused with different payload or job")
            return {"effect_key": effect_key, "duplicate": True, "result": parse_json(existing["result_json"], {})}
        self._active_lease(job_id, worker_id, lease_token)
        with self.db.tx():
            self.db.conn.execute(
                "INSERT INTO effect_commits VALUES(?,?,?,?,?,?)",
                (effect_key, job_id, ph, canonical_json(result), worker_id, utcnow()),
            )
        return {"effect_key": effect_key, "duplicate": False, "result": result}

    def complete_job(self, job_id: str, worker_id: str, lease_token: str, *, effect_key: str, result: Any):
        ph = content_hash(result)
        effect = self.db.one("SELECT * FROM effect_commits WHERE effect_key=?", (effect_key,))
        job = self.db.one("SELECT * FROM distributed_jobs WHERE job_id=?", (job_id,))
        if not job:
            raise NotFound("Distributed job not found")
        if job["status"] == "SUCCEEDED":
            if not effect or effect["job_id"] != job_id or effect["payload_hash"] != ph:
                raise IdempotencyConflict("Completed job replay does not match committed effect")
            return {"job_id": job_id, "status": "SUCCEEDED", "duplicate": True, "result": parse_json(effect["result_json"], {})}
        job = self._active_lease(job_id, worker_id, lease_token)
        if job["status"] != "RUNNING":
            raise InvalidTransition("Job must be RUNNING before completion")
        if effect:
            if effect["job_id"] != job_id or effect["payload_hash"] != ph:
                raise IdempotencyConflict("Effect replay mismatch")
            duplicate = True
        else:
            duplicate = False
        attempt = self.db.one("SELECT * FROM job_attempts WHERE job_id=? AND attempt_number=?", (job_id, job["attempt_count"]))
        with self.db.tx():
            if not effect:
                self.db.conn.execute(
                    "INSERT INTO effect_commits VALUES(?,?,?,?,?,?)",
                    (effect_key, job_id, ph, canonical_json(result), worker_id, utcnow()),
                )
            if attempt and attempt["run_id"]:
                run = self.db.one("SELECT * FROM runs WHERE run_id=?", (attempt["run_id"],))
                if run and run["runtime_status"] == "RUNNING":
                    self.db.conn.execute(
                        "UPDATE runs SET runtime_status='COMPLETED',finished_at=?,exit_metadata=? WHERE run_id=?",
                        (utcnow(), canonical_json({"distributed_job_id": job_id}), run["run_id"]),
                    )
                    self.db.conn.execute("UPDATE workunits SET status='SUCCEEDED',version=version+1 WHERE workunit_id=?", (run["workunit_id"],))
            self.db.conn.execute(
                "UPDATE job_attempts SET status='SUCCEEDED',finished_at=?,metadata=? WHERE job_id=? AND attempt_number=?",
                (utcnow(), canonical_json({"effect_key": effect_key}), job_id, job["attempt_count"]),
            )
            self.db.conn.execute(
                "UPDATE distributed_jobs SET status='SUCCEEDED',result_json=?,lease_worker_id=NULL,lease_token=NULL,"
                "lease_expires_at=NULL,updated_at=? WHERE job_id=?",
                (canonical_json(result), utcnow(), job_id),
            )
            self._event(job["project_id"], job_id, worker_id, "JOB_SUCCEEDED", {"effect_key": effect_key, "duplicate_effect": duplicate})
        return {"job_id": job_id, "status": "SUCCEEDED", "duplicate": duplicate, "result": result}

    def fail_job(self, job_id: str, worker_id: str, lease_token: str, *, error_code: str, retryable: bool = True, metadata=None):
        job = self._active_lease(job_id, worker_id, lease_token)
        attempt = self.db.one("SELECT * FROM job_attempts WHERE job_id=? AND attempt_number=?", (job_id, job["attempt_count"]))
        retry = retryable and int(job["attempt_count"]) < int(job["max_attempts"])
        next_job = "READY" if retry else "FAILED"
        next_wu = "READY" if retry else "RECOVERY"
        with self.db.tx():
            if attempt and attempt["run_id"]:
                run = self.db.one("SELECT * FROM runs WHERE run_id=?", (attempt["run_id"],))
                if run and run["runtime_status"] == "RUNNING":
                    self.db.conn.execute(
                        "UPDATE runs SET runtime_status='FAILED',finished_at=?,exit_metadata=? WHERE run_id=?",
                        (utcnow(), canonical_json({"error_code": error_code, **(metadata or {})}), run["run_id"]),
                    )
            self.db.conn.execute("UPDATE workunits SET status=?,version=version+1 WHERE workunit_id=?", (next_wu, job["workunit_id"]))
            self.db.conn.execute(
                "UPDATE job_attempts SET status='FAILED',finished_at=?,error_code=?,metadata=? WHERE job_id=? AND attempt_number=?",
                (utcnow(), error_code, canonical_json(metadata or {}), job_id, job["attempt_count"]),
            )
            self.db.conn.execute(
                "UPDATE distributed_jobs SET status=?,last_error=?,lease_worker_id=NULL,lease_token=NULL,"
                "lease_expires_at=NULL,updated_at=? WHERE job_id=?",
                (next_job, error_code, utcnow(), job_id),
            )
            self._event(job["project_id"], job_id, worker_id, "JOB_RETRY_READY" if retry else "JOB_FAILED", {"error_code": error_code})
        return next_job

    def recover_expired_leases(self):
        now = datetime.now(timezone.utc)
        recovered = []
        for worker in self.db.all("SELECT * FROM worker_nodes WHERE status='ACTIVE'"):
            if _dt(worker["last_heartbeat_at"]) + timedelta(seconds=int(worker["heartbeat_ttl_seconds"])) < now:
                self.db.conn.execute("UPDATE worker_nodes SET status='OFFLINE' WHERE worker_id=?", (worker["worker_id"],))
        self.db.conn.commit()
        rows = self.db.all("SELECT * FROM distributed_jobs WHERE status IN ('LEASED','RUNNING') AND lease_expires_at IS NOT NULL")
        for job in rows:
            if _dt(job["lease_expires_at"]) > now:
                continue
            attempt = self.db.one("SELECT * FROM job_attempts WHERE job_id=? AND attempt_number=?", (job["job_id"], job["attempt_count"]))
            retry = int(job["attempt_count"]) < int(job["max_attempts"])
            next_job = "READY" if retry else "FAILED"
            next_wu = "READY" if retry else "RECOVERY"
            with self.db.tx():
                if attempt and attempt["run_id"]:
                    run = self.db.one("SELECT * FROM runs WHERE run_id=?", (attempt["run_id"],))
                    if run and run["runtime_status"] == "RUNNING":
                        self.db.conn.execute(
                            "UPDATE runs SET runtime_status='ABANDONED',finished_at=?,exit_metadata=? WHERE run_id=?",
                            (utcnow(), canonical_json({"reason": "LEASE_EXPIRED", "job_id": job["job_id"]}), run["run_id"]),
                        )
                self.db.conn.execute("UPDATE workunits SET status=?,version=version+1 WHERE workunit_id=?", (next_wu, job["workunit_id"]))
                self.db.conn.execute(
                    "UPDATE job_attempts SET status='ABANDONED',finished_at=?,error_code='LEASE_EXPIRED' "
                    "WHERE job_id=? AND attempt_number=?",
                    (utcnow(), job["job_id"], job["attempt_count"]),
                )
                self.db.conn.execute(
                    "UPDATE distributed_jobs SET status=?,last_error='LEASE_EXPIRED',lease_worker_id=NULL,"
                    "lease_token=NULL,lease_expires_at=NULL,updated_at=? WHERE job_id=?",
                    (next_job, utcnow(), job["job_id"]),
                )
                self._event(
                    job["project_id"], job["job_id"], job["lease_worker_id"],
                    "JOB_LEASE_EXPIRED_REQUEUED" if retry else "JOB_LEASE_EXPIRED_FAILED",
                    {"attempt": job["attempt_count"]},
                )
            recovered.append(job["job_id"])
        return recovered

    def get_job(self, job_id: str) -> dict[str, Any]:
        row = self.db.one("SELECT * FROM distributed_jobs WHERE job_id=?", (job_id,))
        if not row:
            raise NotFound("Distributed job not found")
        out = dict(row)
        out["required_resources"] = parse_json(out["required_resources"], {})
        out["required_capabilities"] = parse_json(out["required_capabilities"], [])
        out["result_json"] = parse_json(out["result_json"], None)
        return out

    def get_worker(self, worker_id: str) -> dict[str, Any]:
        row = self.db.one("SELECT * FROM worker_nodes WHERE worker_id=?", (worker_id,))
        if not row:
            raise NotFound("Worker not found")
        out = dict(row)
        out["capabilities"] = parse_json(out["capabilities"], {})
        out["resources_total"] = parse_json(out["resources_total"], {})
        return out

    def queue_snapshot(self, project_id: str | None = None):
        if project_id:
            rows = self.db.all("SELECT job_id FROM distributed_jobs WHERE project_id=? ORDER BY created_at,job_id", (project_id,))
        else:
            rows = self.db.all("SELECT job_id FROM distributed_jobs ORDER BY created_at,job_id")
        return {
            "jobs": [self.get_job(r["job_id"]) for r in rows],
            "workers": [self.get_worker(r["worker_id"]) for r in self.db.all("SELECT worker_id FROM worker_nodes ORDER BY registered_at,worker_id")],
        }
