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
