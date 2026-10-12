# GWF vNext P4 — PM WorkAssignment Protocol Implementation Lock Closure

**Gate:** `GWF_VNEXT_P4_PM_WORKASSIGNMENT_PROTOCOL_IMPLEMENTATION_STATIC_PREFLIGHT_AND_EXECUTION_LOCK`  
**Decision:** `PASS / EXECUTION LOCKED`  
**Date:** 2026-10-12

## Qualified implementation

- Contract base: `4cd2e8b10bfbbad04ff820ce7818f7ef4bc83775`
- Qualified implementation HEAD: `bc33e85d3afc70c2bd9595e403c0eb1c982e4979`
- Qualified implementation tree: `e532c78d533a59828a2dace5b5650dd5c4ae3eff`
- GitHub Actions qualification run: `38214150785`
- Qualification job: `114694836703`
- Run conclusion: `success`

The exact implementation diff from the frozen P4 contract base contains only four new P4 implementation/qualification files. P1/P2/P3 locked files and execution-lock artifacts remain unchanged.

## Qualification results

- Static contract/hash/scope/test-matrix/provider-neutrality preflight: **PASS**
- P4 protocol tests: **PASS**
  - 2 positive protocol fixtures
  - 36 preregistered negative tests
- P1/P2/P3 locked regressions: **PASS**
- Core governance regressions: **PASS**
- Python compile preflight: **PASS**

## Locked implementation surface

- `src/gwr/pm_workassignment_vnext.py`
- `tests/test_gwf_vnext_p4_pm_workassignment_protocol.py`
- `scripts/pivot/gwf_vnext_p4_static_preflight.py`
- `.github/workflows/gwf-vnext-p4-pm-workassignment-protocol.yml`

Exact blob identities are frozen in `GWF_VNEXT_P4_EXECUTION_LOCK.json`.

## What P4 now qualifies

P4 now has a provider-neutral implementation for:

- PM-visible governed-state snapshots;
- append-only PM plan revisions;
- worker/QA role requests;
- content-bound WorkAssignment proposals;
- freeze/submit/reject/escalate/supersede proposal lifecycle;
- stale governed-state rejection;
- authority, budget, capability, HumanActionRequest and protected-resource constraints before materialization;
- proposal materialization into the existing P1 `WorkAssignment` contract without PM authorization/dispatch authority;
- exact proposal-to-WorkAssignment linkage;
- durable PM handoff/recovery identity.

The existing P1 `WorkAssignment` remains authoritative and is not redefined.

## Authority boundary preserved

```text
PM  = proposal / decomposition / escalation
G2E = semantic + scientific authority
GWF = governance authorization + durable runtime authority
```

Operational completion still cannot become scientific evidence admission or scientific PASS/FAIL.

## Explicitly still closed

This lock does not authorize:

- RemoteMCP execution-environment adapter;
- Codex/CGW execution-environment adapter;
- provider/model-specific PM runtime;
- Mission Control refactor;
- real research/software project execution;
- protected evidence consumption;
- P5/P6 implementation.

## Local RemoteMCP note

The canonical local checkout on `machine-1` was recovered and its HEAD independently verified at the exact P4 contract base before implementation. A routed `git status` readback later remained pending in the RemoteMCP control plane despite signed heartbeat reporting no active node process. That is operational observability residue only, not a P4 contract/scientific failure, and it is not appended to `LINEAGE.md`.

## Closure

```text
GWF_VNEXT_P4_PM_WORKASSIGNMENT_PROTOCOL_IMPLEMENTATION_STATIC_PREFLIGHT_AND_EXECUTION_LOCK
= PASS_EXECUTION_LOCKED
```

No scientific lineage entry is created by this implementation lock.
