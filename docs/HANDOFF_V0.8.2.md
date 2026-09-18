# Handoff — GWR v0.8.2

Primary modules:

- src/gwr/project_governance.py
- src/gwr/agent_protocol.py
- src/gwr/process_inspector.py
- src/gwr/api.py
- web/

Run the acceptance gate:

export GWR_TEST_DATABASE_URL=postgresql://...
export PYTHONPATH=src
python tools/run_v082_gate.py --out evidence/v0.8.2/live_gate

Acceptance requires V082_GATE.json status PASS and ready_for_uat true.

UAT focus:

1. rename a project and verify identity is unchanged;
2. archive/restore and verify historical views remain visible;
3. open a running phase and observe breathing activity;
4. inspect LOAD -> PREFLIGHT -> PLAN -> EXECUTE -> VERIFY -> HANDOFF -> COMPLETE;
5. inspect frozen plan/checklist and event log;
6. switch AUTO/HUMAN recovery mode;
7. simulate an issue and verify PROBLEM_RECORDED precedes recovery;
8. in HUMAN mode verify phase pauses until approve/reject;
9. verify archived projects are read-only in the UAT simulation.
