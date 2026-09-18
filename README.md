# Governed Workflow Runtime v0.8.2 — Observable Agent Execution

GWR v0.8.2 adds project governance plus a persistent, observable execution protocol for AI-driven phases.

## New in v0.8.2

- Rename Project with immutable project identity and name history.
- Archive / controlled drain / restore.
- Archived projects remain readable but reject new governed mutations/execution.
- Versioned Skill Registry with immutable SKILL.md revisions.
- Per-phase LOAD → PREFLIGHT → PLAN → EXECUTE → VERIFY → HANDOFF → COMPLETE protocol.
- Persistent preflight checks, plan revisions, checklist items and handoffs.
- ProblemRecord must be written before any retry/replan.
- AUTO and HUMAN_APPROVE recovery modes.
- Human approval gate for recovery/backtracking when configured or when AUTO safety policy refuses automatic recovery.
- Process Inspector exposes protocol stage, plan progress, problems, recovery decisions and operational event log.
- GitHub Pages UAT includes breathing activity signal, recovery-mode switch, issue simulation and project rename/archive/restore.

The product surface exposes operational trace only. It does not expose hidden model reasoning.

## Gate

export GWR_TEST_DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME
export PYTHONPATH=src
python tools/run_v082_gate.py --out evidence/v0.8.2/live_gate

Acceptance requires ready_for_uat=true and all nested v0.8.1 → v0.5.1 regression gates PASS.
