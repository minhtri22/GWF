-- Canonical human-readable copy of the migration embedded in src/gwr/migrations.py.
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
