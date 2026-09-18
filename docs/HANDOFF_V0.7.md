# Handoff — GWR v0.7

Primary code: src/gwr/distributed.py.

Live gate command:

export GWR_TEST_DATABASE_URL=postgresql://...
export PYTHONPATH=src
python tools/run_v07_gate.py --out evidence/v0.7/live_gate

Acceptance requires V07_GATE.json status PASS and ready_for_v08 true.

Do not weaken these invariants in v0.8:

1. lease expiry is the ownership boundary;
2. old lease tokens never regain authority;
3. retries may execute again, but an effect_key may commit once only;
4. worker crash must leave a visible ABANDONED attempt and run;
5. capacity and conflict reservations happen before lease grant;
6. PostgreSQL remains authoritative for distributed state.

Next milestone: v0.8 Research Product Alpha and Domain SDK with operator-facing execution UX.
