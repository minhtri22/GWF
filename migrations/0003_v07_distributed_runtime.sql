-- GWR v0.7 Distributed Runtime
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
