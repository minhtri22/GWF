from __future__ import annotations
import sqlite3
import os
import hashlib
from contextlib import contextmanager
from pathlib import Path

SCHEMA = r'''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, name TEXT NOT NULL, domain_id TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS actors(actor_id TEXT PRIMARY KEY, actor_type TEXT NOT NULL, principal_id TEXT NOT NULL, role_bindings TEXT NOT NULL, project_scope TEXT NOT NULL, status TEXT NOT NULL, identity_metadata TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS human_credentials(credential_id TEXT PRIMARY KEY, actor_id TEXT NOT NULL UNIQUE, username TEXT NOT NULL UNIQUE, password_salt TEXT NOT NULL, password_hash TEXT NOT NULL, iterations INTEGER NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, last_rotated_at TEXT);
CREATE TABLE IF NOT EXISTS auth_sessions(session_id TEXT PRIMARY KEY, actor_id TEXT NOT NULL, token_hash TEXT NOT NULL, issued_at TEXT NOT NULL, expires_at TEXT NOT NULL, revoked_at TEXT, auth_method TEXT NOT NULL, client_metadata TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS authority_policies(policy_id TEXT PRIMARY KEY, policy_version TEXT NOT NULL, subject_selector TEXT NOT NULL, resource_selector TEXT NOT NULL, actions TEXT NOT NULL, conditions TEXT NOT NULL, effect TEXT NOT NULL, priority INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS artifacts(artifact_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, artifact_type TEXT NOT NULL, logical_key TEXT NOT NULL, created_at TEXT NOT NULL, created_by_actor_id TEXT NOT NULL, current_revision_id TEXT, lifecycle_status TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 0, UNIQUE(project_id, logical_key));
CREATE TABLE IF NOT EXISTS revisions(revision_id TEXT PRIMARY KEY, artifact_id TEXT NOT NULL, revision_number INTEGER NOT NULL, structured_payload TEXT NOT NULL, content_hash TEXT NOT NULL, created_by_actor_id TEXT NOT NULL, created_at TEXT NOT NULL, supersedes_revision_id TEXT, status TEXT NOT NULL, validity_state TEXT NOT NULL, UNIQUE(artifact_id, revision_number));
CREATE TABLE IF NOT EXISTS trace_links(trace_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, source_revision_id TEXT NOT NULL, target_kind TEXT NOT NULL, target_id TEXT NOT NULL, relation_type TEXT NOT NULL, strength TEXT NOT NULL, invalidates_on_upstream_supersede INTEGER NOT NULL, propagation_rule TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS impacts(impact_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, trigger_type TEXT NOT NULL, trigger_id TEXT NOT NULL, root_revision_id TEXT NOT NULL, affected_nodes TEXT NOT NULL, reason_codes TEXT NOT NULL, calculated_at TEXT NOT NULL, calculation_policy_version TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS workunits(workunit_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, workunit_type TEXT NOT NULL, input_revision_ids TEXT NOT NULL, output_contracts TEXT NOT NULL, preconditions TEXT NOT NULL, required_gates TEXT NOT NULL, required_authorities TEXT NOT NULL, executor_selector TEXT NOT NULL, execution_policy TEXT NOT NULL, retry_policy TEXT NOT NULL, recovery_policy TEXT NOT NULL, resource_conflict_keys TEXT NOT NULL, status TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY, workunit_id TEXT NOT NULL, attempt_number INTEGER NOT NULL, executor_actor_id TEXT NOT NULL, input_revision_ids TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT, runtime_status TEXT NOT NULL, exit_metadata TEXT, produced_revision_ids TEXT NOT NULL, evidence_ids TEXT NOT NULL, checkpoint_id TEXT, correlation_id TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS evidence(evidence_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, evidence_type TEXT NOT NULL, producer_run_id TEXT, producer_actor_id TEXT NOT NULL, subject_refs TEXT NOT NULL, structured_payload TEXT NOT NULL, content_hash TEXT NOT NULL, created_at TEXT NOT NULL, freshness_metadata TEXT NOT NULL, trust_class TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS gates(gate_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, gate_type TEXT NOT NULL, scope TEXT NOT NULL, required_inputs TEXT NOT NULL, required_evidence TEXT NOT NULL, policy_version TEXT NOT NULL, result TEXT NOT NULL, violation_codes TEXT NOT NULL, evaluated_refs TEXT NOT NULL, evaluated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS decisions(decision_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, scope TEXT NOT NULL, source_gate_ids TEXT NOT NULL, source_failure_id TEXT, decision_type TEXT NOT NULL, target_ref TEXT, reason_codes TEXT NOT NULL, created_at TEXT NOT NULL, created_by TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS failures(failure_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, scope_id TEXT NOT NULL, failure_class TEXT NOT NULL, detected_stage TEXT NOT NULL, detected_ref TEXT NOT NULL, detected_revision_id TEXT, failed_gate_id TEXT, evidence_ids TEXT NOT NULL, root_ref TEXT, root_revision_id TEXT, root_status TEXT NOT NULL, resume_candidate TEXT, severity TEXT NOT NULL, signature TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, resolved_at TEXT);
CREATE TABLE IF NOT EXISTS recoveries(recovery_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, failure_id TEXT NOT NULL, root_ref TEXT NOT NULL, resume_target TEXT NOT NULL, keep_valid_refs TEXT NOT NULL, invalidate_refs TEXT NOT NULL, mark_stale_refs TEXT NOT NULL, required_revision_actions TEXT NOT NULL, required_workunits TEXT NOT NULL, required_retests TEXT NOT NULL, required_approvals TEXT NOT NULL, checkpoint_strategy TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS loopguards(loopguard_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, scope TEXT NOT NULL, failure_signature TEXT NOT NULL, same_signature_count INTEGER NOT NULL, revision_churn_count INTEGER NOT NULL, retry_count INTEGER NOT NULL, window TEXT NOT NULL, budget TEXT NOT NULL, status TEXT NOT NULL, UNIQUE(project_id, scope, failure_signature));
CREATE TABLE IF NOT EXISTS checkpoints(checkpoint_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, scope_id TEXT NOT NULL, created_at TEXT NOT NULL, last_event_id TEXT, active_workunit_ids TEXT NOT NULL, completed_workunit_ids TEXT NOT NULL, current_stage_labels TEXT NOT NULL, valid_revision_ids TEXT NOT NULL, dirty_revision_ids TEXT NOT NULL, stale_revision_ids TEXT NOT NULL, blocking_failure_ids TEXT NOT NULL, pending_decision_ids TEXT NOT NULL, pending_approval_ids TEXT NOT NULL, resume_candidates TEXT NOT NULL, runtime_metadata TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS proposals(proposal_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, proposer_actor_id TEXT NOT NULL, action TEXT NOT NULL, resource_refs TEXT NOT NULL, frozen_payload TEXT NOT NULL, payload_hash TEXT NOT NULL, required_approval_policy TEXT, status TEXT NOT NULL, created_at TEXT NOT NULL, idempotency_key TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS approvals(approval_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, proposal_id TEXT NOT NULL, proposal_hash TEXT NOT NULL, approver_actor_id TEXT NOT NULL, decision TEXT NOT NULL, scope TEXT NOT NULL, created_at TEXT NOT NULL, expires_at TEXT, conditions TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit_events(event_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, actor_id TEXT NOT NULL, action TEXT NOT NULL, resource_type TEXT NOT NULL, resource_id TEXT NOT NULL, before_version TEXT, after_version TEXT, proposal_id TEXT, approval_id TEXT, run_id TEXT, decision_id TEXT, correlation_id TEXT, reason_code TEXT NOT NULL, timestamp TEXT NOT NULL, metadata_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS idempotency(key TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, result_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS orchestrations(orchestration_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, domain_id TEXT NOT NULL, status TEXT NOT NULL, current_phase_id TEXT, generation INTEGER NOT NULL DEFAULT 0, research_outcome TEXT, pivot_count INTEGER NOT NULL DEFAULT 0, started_at TEXT NOT NULL, updated_at TEXT NOT NULL, terminal_checkpoint_id TEXT, metadata TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS phase_executions(phase_execution_id TEXT PRIMARY KEY, orchestration_id TEXT NOT NULL, phase_id TEXT NOT NULL, phase_index INTEGER NOT NULL, generation INTEGER NOT NULL, workunit_id TEXT, run_id TEXT, status TEXT NOT NULL, decision_outcome TEXT, failure_id TEXT, checkpoint_id TEXT, started_at TEXT NOT NULL, finished_at TEXT, metadata TEXT NOT NULL);
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit_events BEGIN SELECT RAISE(ABORT, 'audit_events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit_events BEGIN SELECT RAISE(ABORT, 'audit_events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS revision_content_immutable BEFORE UPDATE OF structured_payload,content_hash,artifact_id,revision_number,created_by_actor_id,created_at,supersedes_revision_id ON revisions BEGIN SELECT RAISE(ABORT, 'revision content is immutable'); END;
'''

class Database:
    backend_name="sqlite"
    def __init__(self, path: str = ":memory:"):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        from .migrations import MigrationManager
        self.migrations=MigrationManager(self)
        self.migrations.apply_all()
    @contextmanager
    def tx(self):
        try:
            self.conn.execute("BEGIN IMMEDIATE")
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback(); raise
    def one(self, sql, params=()):
        return self.conn.execute(sql, params).fetchone()
    def all(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()
    def list_tables(self) -> list[str]:
        return [r["name"] for r in self.all("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    def close(self):
        self.conn.close()


_TEST_PG_NAMESPACES: set[str] = set()
_TEST_PG_MEMORY_COUNTER = 0

def _test_pg_namespace(target: str) -> tuple[str,bool]:
    global _TEST_PG_MEMORY_COUNTER
    prefix=os.environ.get("GWR_TEST_NAMESPACE_PREFIX","gwr_v051")
    if target == ":memory:":
        _TEST_PG_MEMORY_COUNTER += 1
        key=f"memory-{_TEST_PG_MEMORY_COUNTER}"
    else:
        key=target
    suffix=hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    ns=f"{prefix}_{suffix}"
    first=ns not in _TEST_PG_NAMESPACES
    _TEST_PG_NAMESPACES.add(ns)
    return ns,first

def create_database(target: str = ":memory:"):
    # Test-matrix override: the same runtime/test code can be executed against a
    # real PostgreSQL server while preserving logical database isolation by mapping
    # each file target to a dedicated schema. This override is never implicit in
    # normal product use.
    test_pg=os.environ.get("GWR_TEST_DATABASE_URL")
    if test_pg and not (target.startswith("postgresql://") or target.startswith("postgres://")):
        from .db_backends import PostgresDatabase
        ns,first=_test_pg_namespace(target)
        return PostgresDatabase(test_pg, namespace=ns, reset_namespace=first)
    if target.startswith("postgresql://") or target.startswith("postgres://"):
        from .db_backends import PostgresDatabase
        return PostgresDatabase(target)
    if target.startswith("sqlite:///"):
        target=target[len("sqlite:///"):]
    return Database(target)
