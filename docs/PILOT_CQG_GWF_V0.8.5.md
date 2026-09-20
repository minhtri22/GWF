# CQG + GWF Pilot Plan — v0.8.5

## 1. CQG pilot

Profile: `pilots/cqg.research.yaml`

Target: `minhtri22/CQG`

Mode: **NEXT_STUDY**

Do not attempt to recreate the entire CQG history inside GWF.

At pilot start:

1. fetch current CQG `main`;
2. freeze its exact SHA as parent evidence;
3. reference existing append-only lineage;
4. open one new prospective CQG study under the research v0.5 domain;
5. create the study lock before any fresh-study outcome is inspected;
6. use feature-branch GitHub writes with exact SHA verification;
7. let transient execution failures use AUTO recovery within budget;
8. require human authority for normative/high-impact research changes;
9. adjudicate only against frozen gates;
10. append final result/handoff without rewriting earlier studies.

The pilot is successful if the same CQG scientific discipline can be reproduced without relying on the identity or memory of the agent executing each phase.

## 2. GWF self-upgrade pilot

Profile: `pilots/gwf.self-upgrade.yaml`

Target: `minhtri22/GWF`

Mode: **BOUNDED_SELF_UPGRADE**

Recommended first dogfood target: CI concurrency hygiene.

The change should only reduce superseded duplicate GitHub Actions work. It must not remove or weaken acceptance gates.

Required path:

1. fetch and freeze exact GWF main SHA;
2. lock scope/non-goals;
3. freeze feature-branch change set;
4. implement with SHA-safe GitHub writes;
5. run dedicated/local verification;
6. run PostgreSQL/full regression;
7. perform independent QA;
8. obtain exact candidate SHA + workflow evidence + artifact digest;
9. compare expected main SHA before merge;
10. merge without force;
11. rerun all required workflows on exact merged-main SHA;
12. write release handoff only after exact-main PASS.

## 3. Recovery policy

Default pilot recovery mode is `AUTO`.

This does **not** mean "agent may change anything until it passes".

AUTO is limited to semantically identical, allowed transient retries within budget.

Examples that require replan/new lock/human boundary instead of automatic retry:

- CQG metric/target/threshold/cohort/model changes;
- GWF scope expansion;
- stale GitHub expected SHA;
- security/authority boundary changes;
- changes to normative research/software artifacts.

`HUMAN_APPROVE` may be selected at project/phase level when manual retry authorization is desired.

## 4. Pilot profile commands

Validate:

```powershell
.\.venv\Scripts\python.exe tools\gwr_pilot.py validate pilots\cqg.research.yaml
.\.venv\Scripts\python.exe tools\gwr_pilot.py validate pilots\gwf.self-upgrade.yaml
```

Inspect execution plan without mutation:

```powershell
.\.venv\Scripts\python.exe tools\gwr_pilot.py plan pilots\cqg.research.yaml
.\.venv\Scripts\python.exe tools\gwr_pilot.py plan pilots\gwf.self-upgrade.yaml
```

The profile validator/planner itself does not mutate either target repository.
