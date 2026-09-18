# v0.6 Implementation QA Contract

The final v0.6 gate must run the entire v0.5.1 live PostgreSQL gate unchanged, then execute the v0.6 identity/multi-tenancy suite on both SQLite and PostgreSQL.

Required evidence:

- `V06_GATE.json`
- v0.5.1 regression `POSTGRES_GATE.json`
- SQLite v0.6 pytest log
- PostgreSQL v0.6 pytest log
- `QA_SQLITE.json`
- `QA_POSTGRES.json`
- compileall log

A PASS requires tenant isolation, OIDC subject binding, immediate revocation, both database backends, and the full previous research/restart semantic-equivalence gate.
