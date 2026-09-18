# Implementation QA — v0.8

The v0.8 gate nests the entire v0.7 gate, then runs product-specific tests and QA on SQLite and PostgreSQL 17.

Dedicated coverage includes:

- Domain SDK validate/inspect/scaffold;
- dashboard aggregation;
- cross-tenant dashboard concealment;
- exact-hash authenticated rejection;
- proposal decision persistence;
- failure/recovery graph generation;
- static UAT fixture requirements;
- GitHub Pages build output;
- compileall.

The static Pages console is tested as a build artifact but is intentionally not treated as an authenticated runtime backend.
