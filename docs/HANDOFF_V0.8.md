# Handoff — GWR v0.8

Primary product modules:

- src/gwr/domain_sdk.py
- src/gwr/product.py
- src/gwr/api.py
- web/
- tools/build_uat_site.py

Live gate:

export GWR_TEST_DATABASE_URL=postgresql://...
export PYTHONPATH=src
python tools/run_v08_gate.py --out evidence/v0.8/live_gate

Acceptance requires V08_GATE.json status PASS and ready_for_uat true.

GitHub Pages UAT is static and non-authoritative. Do not interpret a local approve/reject click as a backend governance decision.

Keep v0.7 invariants intact: lease expiry remains execution ownership boundary, stale workers cannot commit, retries are at-least-once, and authoritative effect_key commits are exactly-once.

UAT feedback should be recorded against dashboard clarity, approval review ergonomics, recovery comprehension, distributed visibility and Domain SDK usability before moving to public-beta hardening.
