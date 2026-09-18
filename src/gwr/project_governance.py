from __future__ import annotations

from .errors import InvalidTransition, NotFound, ValidationError
from .utils import uid, utcnow


class ProjectGovernanceService:
    ACTIVE = "ACTIVE"
    ARCHIVING = "ARCHIVING"
    ARCHIVED = "ARCHIVED"

    def __init__(self, db, tenancy, governance):
        self.db = db
        self.tenancy = tenancy
        self.gov = governance

    def ensure(self, project_id: str):
        if not self.db.one("SELECT 1 FROM projects WHERE id=?", (project_id,)):
            raise NotFound("Project not found")
        row = self.db.one("SELECT * FROM project_lifecycle WHERE project_id=?", (project_id,))
        if not row:
            self.db.conn.execute(
                "INSERT INTO project_lifecycle VALUES(?,?,?,?,?,?,?)",
                (project_id, self.ACTIVE, None, None, None, None, utcnow()),
            )
            self.db.conn.commit()
            row = self.db.one("SELECT * FROM project_lifecycle WHERE project_id=?", (project_id,))
        return row

    def status(self, project_id: str) -> dict:
        row = self.ensure(project_id)
        return dict(row)

    def _authorize_manage(self, actor_id: str, project_id: str):
        scope = self.tenancy.scope_for_project(project_id)
        if scope:
            self.tenancy.require_project_access(actor_id, project_id, "MANAGE_MEMBERS")
        elif actor_id != "SYSTEM":
            self.gov.authorize(actor_id, "PROPOSE", {"project_id": project_id, "action": "MANAGE_PROJECT"})

    def rename(self, project_id: str, new_name: str, actor_id: str) -> dict:
        self._authorize_manage(actor_id, project_id)
        self.require_mutable(project_id)
        name = (new_name or "").strip()
        if not name:
            raise ValidationError("Project name is required")
        row = self.db.one("SELECT name FROM projects WHERE id=?", (project_id,))
        if not row:
            raise NotFound("Project not found")
        if row["name"] == name:
            return {"project_id": project_id, "name": name, "unchanged": True}
        hid = uid("pname")
        with self.db.tx():
            self.db.conn.execute("UPDATE projects SET name=? WHERE id=?", (name, project_id))
            self.db.conn.execute(
                "INSERT INTO project_name_history VALUES(?,?,?,?,?,?)",
                (hid, project_id, row["name"], name, actor_id, utcnow()),
            )
            self.gov.append_audit(project_id, actor_id, "PROJECT_RENAMED", "Project", project_id,
                                  reason_code="RENAME", metadata={"old_name": row["name"], "new_name": name})
        return {"project_id": project_id, "name": name, "old_name": row["name"], "unchanged": False}

    def _activity(self, project_id: str) -> dict:
        active_jobs = self.db.one(
            "SELECT COUNT(*) n FROM distributed_jobs WHERE project_id=? AND status IN ('READY','LEASED','RUNNING')",
            (project_id,),
        )["n"]
        active_runs = self.db.one(
            "SELECT COUNT(*) n FROM runs r JOIN workunits w ON w.workunit_id=r.workunit_id "
            "WHERE w.project_id=? AND r.runtime_status='RUNNING'",
            (project_id,),
        )["n"]
        active_orch = self.db.one(
            "SELECT COUNT(*) n FROM orchestrations WHERE project_id=? AND status IN ('RUNNING','PAUSED')",
            (project_id,),
        )["n"]
        return {"active_jobs": int(active_jobs), "active_runs": int(active_runs), "active_orchestrations": int(active_orch)}

    def archive(self, project_id: str, actor_id: str, *, drain: bool = False, reason: str = "") -> dict:
        self._authorize_manage(actor_id, project_id)
        row = self.ensure(project_id)
        if row["status"] == self.ARCHIVED:
            return {"project_id": project_id, "status": self.ARCHIVED, "activity": self._activity(project_id)}
        activity = self._activity(project_id)
        active = sum(activity.values())
        if active and not drain:
            raise InvalidTransition("Project has active execution; use drain=true before archive", details=activity)
        status = self.ARCHIVING if active else self.ARCHIVED
        now = utcnow()
        with self.db.tx():
            self.db.conn.execute(
                "UPDATE project_lifecycle SET status=?,archive_requested_at=?,archived_at=?,archived_by_actor_id=?,archive_reason=?,updated_at=? WHERE project_id=?",
                (status, now, now if status == self.ARCHIVED else None, actor_id, reason, now, project_id),
            )
            self.gov.append_audit(project_id, actor_id, "PROJECT_ARCHIVE_REQUESTED" if status == self.ARCHIVING else "PROJECT_ARCHIVED",
                                  "Project", project_id, reason_code=reason or status, metadata=activity)
        return {"project_id": project_id, "status": status, "activity": activity}

    def refresh_archive(self, project_id: str) -> dict:
        row = self.ensure(project_id)
        if row["status"] != self.ARCHIVING:
            return self.status(project_id)
        activity = self._activity(project_id)
        if sum(activity.values()) == 0:
            now = utcnow()
            with self.db.tx():
                self.db.conn.execute(
                    "UPDATE project_lifecycle SET status='ARCHIVED',archived_at=?,updated_at=? WHERE project_id=?",
                    (now, now, project_id),
                )
                self.gov.append_audit(project_id, "SYSTEM", "PROJECT_ARCHIVED", "Project", project_id,
                                      reason_code="DRAIN_COMPLETE", metadata=activity)
        return self.status(project_id)

    def restore(self, project_id: str, actor_id: str) -> dict:
        self._authorize_manage(actor_id, project_id)
        row = self.ensure(project_id)
        if row["status"] == self.ACTIVE:
            return {"project_id": project_id, "status": self.ACTIVE}
        with self.db.tx():
            self.db.conn.execute(
                "UPDATE project_lifecycle SET status='ACTIVE',archive_requested_at=NULL,archived_at=NULL,"
                "archived_by_actor_id=NULL,archive_reason=NULL,updated_at=? WHERE project_id=?",
                (utcnow(), project_id),
            )
            self.gov.append_audit(project_id, actor_id, "PROJECT_RESTORED", "Project", project_id)
        return {"project_id": project_id, "status": self.ACTIVE}

    def require_mutable(self, project_id: str):
        row = self.ensure(project_id)
        if row["status"] in {self.ARCHIVING, self.ARCHIVED}:
            raise InvalidTransition(f"Project is {row['status']} and is read-only")
        return True

    def name_history(self, project_id: str):
        self.ensure(project_id)
        return [dict(r) for r in self.db.all(
            "SELECT * FROM project_name_history WHERE project_id=? ORDER BY changed_at,history_id", (project_id,)
        )]
