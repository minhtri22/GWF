# Handoff — GWR v0.8.1

Primary modules:

- src/gwr/domain_registry.py
- src/gwr/process_inspector.py
- src/gwr/api.py
- src/gwr/runtime.py
- web/

Run:

export GWR_TEST_DATABASE_URL=postgresql://...
export PYTHONPATH=src
python tools/run_v081_gate.py --out evidence/v0.8.1/live_gate

Acceptance: V081_GATE.json status PASS and ready_for_uat true.

UAT should cover: create simulated domain, validate/publish, create simulated project pinned to domain revision, inspect current phase, open old failed attempt, inspect phase events/evidence/failure, compare recovery generation, and reset UAT state.
