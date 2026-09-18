# Implementation QA — v0.7

The v0.7 gate runs the entire v0.6 regression chain and then executes dedicated distributed-runtime tests and chaos probes on SQLite and PostgreSQL.

Required checks:

- migration and tables;
- queue durability across runtime restart;
- resource and capability matching;
- global conflict-key exclusion;
- lease heartbeat extension;
- expired-token rejection;
- worker crash to ABANDONED run to requeue to second-worker completion;
- duplicate delivery after effect commit;
- one authoritative effect row;
- enqueue payload-drift rejection;
- scheduler event evidence.

Final evidence is emitted by tools/run_v07_gate.py.
