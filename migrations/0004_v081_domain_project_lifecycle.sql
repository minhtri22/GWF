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
