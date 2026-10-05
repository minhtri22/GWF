# Research Governance Modes Backlog

## Status

```text
BACKLOG_ID        = RESEARCH_GOVERNANCE_MODES_V1
STATE             = DEFERRED / NOT_OPENED
OWNER             = GWF research governance
OPEN_CONDITION    = current Browser Product Surface UI/UX is completed and user explicitly confirms opening this backlog
OUTER_GWF_FLOW    = UNCHANGED
```

## Intent

Keep the existing GWF governance/runtime flow as the outer control plane.  
Allow each research case / hypothesis branch to choose an internal research protocol without replacing global GWF governance.

## Backlogged research protocols

### 1. EMCT

Use the existing E/M/C/T scientific pattern when a case benefits from cheap early falsification and fast hypothesis kill.

Requirements when this backlog is opened:

- protocol is selected per research case/branch, not globally;
- E may be intentionally small/cheap;
- a clear futility or failure result may terminate the branch before expensive downstream work;
- M/C/T transitions remain case-specific scientific transitions;
- GWF must not invent one global semantic meaning for T where the owning research program has not defined it;
- killed branches remain auditable and do not silently disappear from lineage.

### 2. P → R → E → A → M → C

Use the stricter sequence when a case needs prospective scientific contract + independent adjudication.

```text
P  preregistration / scientific contract
↓
R  internal readiness machinery
↓
E  fresh exploratory one-shot
↓
A  independent QA + automatic adjudication
↓
M  mechanism, if opened
↓
C  confirmatory, if opened
```

R is explicitly **not a scientific gate**.

R includes internal machinery such as:

- implementation;
- static preflight;
- dependency repair;
- exact hash binding;
- resource checks;
- execution lock;
- MCP / transport recovery;
- deterministic infrastructure QA.

Agents handle R autonomously. R may remain observable/auditable but must not create user-facing approval burden.

## Required stop conditions

A research agent should stop and surface control to the user only when one of these applies:

1. the scientific contract must change;
2. fresh outcome-bearing evidence is about to be opened/consumed;
3. the case reaches PASS / FAIL / UNRESOLVED;
4. an existing scientific contract explicitly requires another human decision.

Machinery repair alone is not a scientific stop condition.

## Future product work — do not implement before OPEN_CONDITION

When explicitly opened later, evaluate and preregister changes for:

- per-case `research_protocol` / governance-profile identity;
- explicit scientific stage vs machinery/readiness state;
- current verdict and next scientifically allowed transition;
- fresh-evidence boundary state;
- collapsed-by-default machinery timeline in Execution;
- automatic A-stage independent QA/adjudication;
- branch kill/futility closure;
- lineage preservation for killed/unresolved hypotheses;
- protocol-aware Overview / Execution / Research case views;
- migration/compatibility rules for existing projects so historical semantics are not rewritten.

## Non-goals while deferred

Until the user explicitly opens this backlog:

- do not change current GWF governance semantics;
- do not add DB/schema fields for these modes;
- do not change research runtime transitions;
- do not change current Browser Product Surface plan;
- do not reinterpret historical E/M/C/T lineage;
- do not open implementation, migration, or UI work for this backlog.

## Current priority

Finish the already-open Browser Product Surface UI/UX program first.  
The currently open unit remains **BPS-M07-A — System / GitHub read-only surface**.  
Only after the present UI/UX work reaches its current completion/QA boundary and the user confirms may this backlog move from DEFERRED to an opened design/preregistration unit.
