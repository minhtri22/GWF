# Implementation QA — v0.8.2

The v0.8.2 gate nests v0.8.1 and all earlier production gates.

Dedicated checks cover:

- migration/table installation on SQLite/PostgreSQL;
- project rename history and audit;
- active-work archive blocking;
- controlled drain to ARCHIVING and read-only enforcement;
- restore to ACTIVE;
- SkillRevision pinning;
- preflight-before-plan;
- plan-before-execution;
- persistent checklist;
- problem-before-retry ordering;
- AUTO low-risk recovery;
- HUMAN_APPROVE pause and human-only approval;
- retry budget accounting;
- checklist-before-QA;
- QA-before-handoff;
- handoff-before-complete;
- observable protocol read model;
- UAT surface markers and breathing animation;
- JavaScript syntax and Python compileall.
