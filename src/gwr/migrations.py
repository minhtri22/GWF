from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import hashlib

from .utils import utcnow


@dataclass(frozen=True)
class Migration:
    migration_id: str
    sql: str

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.sql.encode("utf-8")).hexdigest()


MIGRATIONS = [
    Migration(
        "0001_v05_production_foundation",
        """
CREATE TABLE IF NOT EXISTS object_refs(
  ref_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  owner_kind TEXT NOT NULL,
  owner_id TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  content_type TEXT NOT NULL,
  object_key TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(project_id, owner_kind, owner_id, sha256)
);
CREATE TABLE IF NOT EXISTS provider_events(
  provider_event_id TEXT PRIMARY KEY,
  project_id TEXT,
  provider_name TEXT NOT NULL,
  operation TEXT NOT NULL,
  outcome TEXT NOT NULL,
  latency_ms INTEGER,
  error_code TEXT,
  metadata TEXT NOT NULL,
  created_at TEXT NOT NULL
);
""".strip(),
    ),    Migration(
        "0002_v06_identity_multitenancy",
        """
CREATE TABLE IF NOT EXISTS tenants(
  tenant_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  status TEXT NOT NULL,
  created_by_actor_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS workspaces(
  workspace_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  status TEXT NOT NULL,
  created_by_actor_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(tenant_id, name)
);
CREATE TABLE IF NOT EXISTS project_scopes(
  project_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  workspace_id TEXT NOT NULL,
  created_by_actor_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tenant_memberships(
  tenant_id TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  role TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(tenant_id, actor_id)
);
CREATE TABLE IF NOT EXISTS workspace_memberships(
  workspace_id TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  role TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(workspace_id, actor_id)
);
CREATE TABLE IF NOT EXISTS project_memberships(
  project_id TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  role TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY(project_id, actor_id)
);
CREATE TABLE IF NOT EXISTS external_identities(
  external_identity_id TEXT PRIMARY KEY,
  actor_id TEXT NOT NULL,
  provider_id TEXT NOT NULL,
  issuer TEXT NOT NULL,
  subject TEXT NOT NULL,
  email TEXT,
  claims_metadata TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(provider_id, issuer, subject)
);
CREATE TABLE IF NOT EXISTS security_events(
  security_event_id TEXT PRIMARY KEY,
  actor_id TEXT NOT NULL,
  tenant_id TEXT,
  action TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  outcome TEXT NOT NULL,
  metadata TEXT NOT NULL,
  created_at TEXT NOT NULL
);
""".strip(),
    ),
    Migration(
        "0003_v07_distributed_runtime",
        """
CREATE TABLE IF NOT EXISTS worker_nodes(
  worker_id TEXT PRIMARY KEY,
  actor_id TEXT NOT NULL,
  status TEXT NOT NULL,
  capabilities TEXT NOT NULL,
  resources_total TEXT NOT NULL,
  heartbeat_ttl_seconds INTEGER NOT NULL,
  last_heartbeat_at TEXT NOT NULL,
  registered_at TEXT NOT NULL,
  metadata TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS distributed_jobs(
  job_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  workunit_id TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL,
  priority INTEGER NOT NULL,
  required_resources TEXT NOT NULL,
  required_capabilities TEXT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE,
  payload_hash TEXT NOT NULL,
  available_at TEXT NOT NULL,
  lease_worker_id TEXT,
  lease_token TEXT,
  lease_expires_at TEXT,
  attempt_count INTEGER NOT NULL,
  max_attempts INTEGER NOT NULL,
  result_json TEXT,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS job_attempts(
  attempt_id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  attempt_number INTEGER NOT NULL,
  worker_id TEXT NOT NULL,
  lease_token TEXT NOT NULL,
  run_id TEXT,
  status TEXT NOT NULL,
  started_at TEXT NOT NULL,
  heartbeat_at TEXT NOT NULL,
  lease_expires_at TEXT NOT NULL,
  finished_at TEXT,
  error_code TEXT,
  metadata TEXT NOT NULL,
  UNIQUE(job_id, attempt_number)
);
CREATE TABLE IF NOT EXISTS effect_commits(
  effect_key TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  result_json TEXT NOT NULL,
  committed_by_worker_id TEXT NOT NULL,
  committed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scheduler_events(
  event_id TEXT PRIMARY KEY,
  project_id TEXT,
  job_id TEXT,
  worker_id TEXT,
  event_type TEXT NOT NULL,
  metadata TEXT NOT NULL,
  created_at TEXT NOT NULL
);
""".strip(),
    ),

    Migration(
        "0004_v081_domain_project_lifecycle",
        """
CREATE TABLE IF NOT EXISTS domain_packages(
  package_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  domain_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  status TEXT NOT NULL,
  created_by_actor_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(tenant_id, domain_id)
);
CREATE TABLE IF NOT EXISTS domain_package_revisions(
  revision_id TEXT PRIMARY KEY,
  package_id TEXT NOT NULL,
  revision_number INTEGER NOT NULL,
  semantic_version TEXT NOT NULL,
  yaml_text TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  validation_report TEXT NOT NULL,
  status TEXT NOT NULL,
  created_by_actor_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  published_at TEXT,
  UNIQUE(package_id, revision_number)
);
CREATE TABLE IF NOT EXISTS project_domain_bindings(
  project_id TEXT PRIMARY KEY,
  domain_revision_id TEXT NOT NULL,
  bound_by_actor_id TEXT NOT NULL,
  bound_at TEXT NOT NULL
);
""".strip(),
    ),

    Migration(
        "0005_v082_project_governance_agent_protocol",
        """
CREATE TABLE IF NOT EXISTS project_lifecycle(
  project_id TEXT PRIMARY KEY,
  status TEXT NOT NULL,
  archive_requested_at TEXT,
  archived_at TEXT,
  archived_by_actor_id TEXT,
  archive_reason TEXT,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS project_name_history(
  history_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  old_name TEXT NOT NULL,
  new_name TEXT NOT NULL,
  changed_by_actor_id TEXT NOT NULL,
  changed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS skill_packages(
  skill_package_id TEXT PRIMARY KEY,
  skill_id TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  created_by_actor_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS skill_revisions(
  skill_revision_id TEXT PRIMARY KEY,
  skill_package_id TEXT NOT NULL,
  revision_number INTEGER NOT NULL,
  version TEXT NOT NULL,
  markdown TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  tool_requirements TEXT NOT NULL,
  qa_contract TEXT NOT NULL,
  created_by_actor_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(skill_package_id, revision_number)
);
CREATE TABLE IF NOT EXISTS phase_execution_protocols(
  protocol_id TEXT PRIMARY KEY,
  phase_execution_id TEXT NOT NULL UNIQUE,
  project_id TEXT NOT NULL,
  skill_revision_id TEXT NOT NULL,
  skill_hash TEXT NOT NULL,
  recovery_mode TEXT NOT NULL,
  current_stage TEXT NOT NULL,
  status TEXT NOT NULL,
  retry_budget INTEGER NOT NULL,
  retry_count INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS phase_preflights(
  preflight_id TEXT PRIMARY KEY,
  phase_execution_id TEXT NOT NULL,
  status TEXT NOT NULL,
  checks_json TEXT NOT NULL,
  checks_hash TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS phase_plans(
  plan_id TEXT PRIMARY KEY,
  phase_execution_id TEXT NOT NULL,
  revision_number INTEGER NOT NULL,
  objective TEXT NOT NULL,
  steps_json TEXT NOT NULL,
  plan_hash TEXT NOT NULL,
  reason TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(phase_execution_id, revision_number)
);
CREATE TABLE IF NOT EXISTS phase_checklist_items(
  checklist_item_id TEXT PRIMARY KEY,
  plan_id TEXT NOT NULL,
  phase_execution_id TEXT NOT NULL,
  step_index INTEGER NOT NULL,
  title TEXT NOT NULL,
  status TEXT NOT NULL,
  note TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(plan_id, step_index)
);
CREATE TABLE IF NOT EXISTS phase_stage_events(
  event_id TEXT PRIMARY KEY,
  phase_execution_id TEXT NOT NULL,
  stage TEXT NOT NULL,
  event_type TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  message TEXT NOT NULL,
  metadata TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS phase_problem_records(
  problem_id TEXT PRIMARY KEY,
  phase_execution_id TEXT NOT NULL,
  affected_step INTEGER,
  code TEXT NOT NULL,
  summary TEXT NOT NULL,
  detail TEXT NOT NULL,
  severity TEXT NOT NULL,
  status TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS phase_recovery_proposals(
  proposal_id TEXT PRIMARY KEY,
  problem_id TEXT NOT NULL,
  phase_execution_id TEXT NOT NULL,
  action TEXT NOT NULL,
  target_step INTEGER,
  plan_patch TEXT NOT NULL,
  rationale TEXT NOT NULL,
  risk_class TEXT NOT NULL,
  normative_change INTEGER NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS phase_recovery_decisions(
  decision_id TEXT PRIMARY KEY,
  proposal_id TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  decision TEXT NOT NULL,
  reason TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS phase_handoffs(
  handoff_id TEXT PRIMARY KEY,
  phase_execution_id TEXT NOT NULL,
  structured_payload TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  actor_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  markdown TEXT NOT NULL
);
""".strip(),
    ),


    Migration(
        "0006_v083_orchestrator_integration",
        """
CREATE TABLE IF NOT EXISTS domain_skill_bindings(
  binding_id TEXT PRIMARY KEY,
  domain_id TEXT NOT NULL,
  workunit_type TEXT NOT NULL,
  skill_revision_id TEXT NOT NULL,
  skill_hash TEXT NOT NULL,
  required_tools TEXT NOT NULL,
  qa_contract TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(domain_id, workunit_type)
);
CREATE TABLE IF NOT EXISTS phase_handoff_links(
  phase_execution_id TEXT PRIMARY KEY,
  previous_phase_execution_id TEXT,
  previous_handoff_id TEXT,
  handoff_hash TEXT,
  verified_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS project_agent_protocol_settings(
  project_id TEXT PRIMARY KEY,
  recovery_mode TEXT,
  retry_budget INTEGER,
  updated_by_actor_id TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
""".strip(),
    ),


    Migration(
        "0007_v084_github_plugin_sha_qa",
        """
CREATE TABLE IF NOT EXISTS plugin_connections(
  connection_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  plugin_type TEXT NOT NULL,
  external_connection_ref TEXT NOT NULL,
  capabilities TEXT NOT NULL,
  status TEXT NOT NULL,
  metadata TEXT NOT NULL,
  created_by_actor_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(project_id, plugin_type, external_connection_ref)
);
CREATE TABLE IF NOT EXISTS github_repository_bindings(
  binding_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  connection_id TEXT NOT NULL,
  repository_full_name TEXT NOT NULL,
  default_branch TEXT NOT NULL,
  write_policy TEXT NOT NULL,
  allowed_branches TEXT NOT NULL,
  created_by_actor_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(project_id, repository_full_name)
);
CREATE TABLE IF NOT EXISTS github_change_sets(
  change_set_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  binding_id TEXT NOT NULL,
  branch TEXT NOT NULL,
  expected_head_sha TEXT NOT NULL,
  manifest_json TEXT NOT NULL,
  manifest_hash TEXT NOT NULL,
  commit_message TEXT NOT NULL,
  status TEXT NOT NULL,
  created_by_actor_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  committed_sha TEXT,
  verified_at TEXT
);
CREATE TABLE IF NOT EXISTS github_sha_checks(
  check_id TEXT PRIMARY KEY,
  change_set_id TEXT NOT NULL,
  stage TEXT NOT NULL,
  expected_sha TEXT,
  observed_sha TEXT,
  status TEXT NOT NULL,
  details_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
""".strip(),
    ),


    Migration(
        "0008_v086_dg_p5_document_findings",
        """
CREATE TABLE IF NOT EXISTS document_findings(
  finding_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  qa_record_id TEXT NOT NULL,
  subject_revision_id TEXT NOT NULL,
  finding_class TEXT NOT NULL,
  severity TEXT NOT NULL,
  rule_id TEXT NOT NULL,
  location_json TEXT NOT NULL,
  description TEXT NOT NULL,
  evidence_refs_json TEXT NOT NULL,
  fingerprint TEXT NOT NULL,
  status TEXT NOT NULL,
  required_fix TEXT NOT NULL,
  resolution_revision_ref TEXT,
  waiver_ref TEXT,
  version INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
""".strip(),
    ),

    Migration(
        "0009_v086_dg_p7_document_authority_claims",
        """
CREATE TABLE IF NOT EXISTS document_authority_claims(
  claim_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  document_id TEXT NOT NULL,
  authority_scope TEXT NOT NULL,
  authority_key TEXT NOT NULL,
  mode TEXT NOT NULL,
  composition_role TEXT,
  composition_policy_ref TEXT,
  composition_policy_hash TEXT,
  status TEXT NOT NULL,
  granted_revision_id TEXT NOT NULL,
  grant_proposal_id TEXT NOT NULL,
  retired_by_proposal_id TEXT,
  version INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  retired_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_document_authority_collision
  ON document_authority_claims(project_id, authority_scope, authority_key, status);
CREATE INDEX IF NOT EXISTS idx_document_authority_owner
  ON document_authority_claims(document_id, status);
""".strip(),
    ),

    Migration(
        "0010_v086_dg_p8_document_relations",
        """
CREATE TABLE IF NOT EXISTS document_relations(
  relation_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  source_document_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  target_kind TEXT NOT NULL,
  target_ref TEXT NOT NULL,
  invalidation_policy TEXT NOT NULL,
  status TEXT NOT NULL,
  created_revision_id TEXT NOT NULL,
  create_proposal_id TEXT NOT NULL,
  retired_revision_id TEXT,
  retired_by_proposal_id TEXT,
  version INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  retired_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_document_relations_source
  ON document_relations(project_id, source_document_id, status);
CREATE INDEX IF NOT EXISTS idx_document_relations_target
  ON document_relations(project_id, target_kind, target_ref, status);
CREATE INDEX IF NOT EXISTS idx_document_relations_type
  ON document_relations(project_id, relation_type, status);
""".strip(),
    ),

    Migration(
        "0011_v086_dg_p9_relation_binding",
        """
ALTER TABLE document_relations ADD COLUMN target_binding_mode TEXT;
ALTER TABLE document_relations ADD COLUMN target_revision_or_hash TEXT;
""".strip(),
    ),

]


class MigrationManager:
    def __init__(self, db):
        self.db = db

    def ensure_table(self):
        self.db.conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations("
            "migration_id TEXT PRIMARY KEY, checksum TEXT NOT NULL, applied_at TEXT NOT NULL)"
        )
        self.db.conn.commit()

    def applied(self) -> dict[str, str]:
        self.ensure_table()
        return {r["migration_id"]: r["checksum"] for r in self.db.all("SELECT migration_id,checksum FROM schema_migrations")}

    def apply_all(self) -> list[str]:
        self.ensure_table()
        applied = self.applied()
        done: list[str] = []
        for migration in MIGRATIONS:
            existing = applied.get(migration.migration_id)
            if existing:
                if existing != migration.checksum:
                    raise RuntimeError(f"migration checksum mismatch: {migration.migration_id}")
                continue
            with self.db.tx():
                self.db.conn.executescript(migration.sql)
                self.db.conn.execute(
                    "INSERT INTO schema_migrations VALUES(?,?,?)",
                    (migration.migration_id, migration.checksum, utcnow()),
                )
            done.append(migration.migration_id)
        return done

    def status(self) -> dict[str, Any]:
        applied = self.applied()
        return {
            "known": [m.migration_id for m in MIGRATIONS],
            "applied": sorted(applied),
            "pending": [m.migration_id for m in MIGRATIONS if m.migration_id not in applied],
        }
