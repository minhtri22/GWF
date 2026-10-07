# GWF — Technical Debt Register

## TD-UAT-01 — Installer / UAT architecture separation

**State:** RECORDED / NOT_IMPLEMENTED  
**Recorded after:** DG-P10 final exact-head closure  
**DG-P10 formal-close HEAD:** `a09f79ae74a838d2c5998813560373c849669872`  
**DG-P10 final workflow:** `35671227699` PASS  
**Scope opened:** NO

### Observation

The Windows final closure run showed that the step named `One-click local UAT setup` ran from 07:16:12 to 07:34:29 ICT, approximately **18 minutes 17 seconds**.

The step currently combines:

- Python/venv and dependency installation;
- domain/pilot validation;
- compile checks;
- bounded DG-P10 gate;
- local UAT workspace preparation;
- the full repository pytest suite.

Therefore the current `install.ps1` is not only an installer. It is also acting as a qualification/UAT runner, which makes normal local installation unnecessarily slow and makes progress/hang diagnosis opaque.

### Desired remediation

Separate responsibilities:

```text
install.ps1
  -> environment/dependencies
  -> lightweight compile/smoke check
  -> local configuration / UAT workspace preparation

uat.ps1
  -> bounded local functional/UAT checks

qualification CI
  -> D10 fixtures
  -> targeted regressions
  -> full repository regression
  -> PostgreSQL qualification
  -> Windows UAT
```

The default `install.ps1` should not run the full repository pytest suite.

Each major step should emit elapsed timing so a slow install, slow test, or actual hang can be distinguished.

### Acceptance intent

A future remediation should demonstrate:

- fresh local install remains deterministic;
- default installation no longer executes full qualification;
- full qualification remains available explicitly and remains unchanged in authority;
- local UAT remains independently runnable;
- install/UAT reports preserve exact HEAD and environment identity;
- no DG-P10 semantic/governance behavior is weakened;
- no failed/negative evidence is erased.

### DG-P11 scope note

The current frozen implementation plan defines **DG-P11 as DocumentChangeSet**, including the concrete governed source-mutation boundary inherited from DG-P10.

The user has requested that the next DG-P11 work address this installer/UAT architecture debt instead.

This is recorded as a **scope-change proposal**, not as an already-effective redefinition.

Before DG-P11 is opened, governance must reconcile the identifier/scope through a bounded plan/spec amendment. Until that amendment is explicitly authorized and qualified:

```text
DG-P11 = NOT_STARTED / NOT_AUTHORIZED
existing DG-P11 DocumentChangeSet contract = still authoritative
TD-UAT-01 implementation = NOT_STARTED
DG-P10 formal closure = unchanged
```

### Pre-open user UAT gate

Before any DG-P11 amendment or implementation, the user will pull the exact DG-P10 formal-close HEAD and run local one-click UAT to provide real local evidence.


### Local UAT evidence — 2026-09-22

User local checkout:

- repository path: `D:\WORK\RESEARCH\4.GWF`;
- exact DG-P10 formal-close HEAD: `a09f79ae74a838d2c5998813560373c849669872`;
- working tree before UAT: clean;
- Python: 3.12.10;
- runtime version: 0.8.5.

Observed local run:

- wall-clock elapsed: `00:03:27`;
- install report: PASS;
- research/software domain validation: PASS;
- pilot validation: PASS;
- compileall: PASS;
- full local pytest suite: PASS;
- bounded DG-P10 gate: PASS;
- PostgreSQL local qualification: SKIPPED because no DSN/Docker was available;
- DG-P10 gate verified no DG-P11 change set, no P10 table and no Revision side effect.

Interpretation:

The local warm-environment run is materially faster than the GitHub fresh Windows runner (~18m17s for the same monolithic one-click step), but the architecture debt remains valid because default installation still executes the full repository regression suite and bounded governance gate. Runtime depends strongly on cache/environment state, and the step remains opaque as an installation surface.

The wrapper-captured `$LASTEXITCODE = -1` conflicts with the script's authoritative PASS report and completed PASS checks. This is tracked as part of TD-UAT-01 observability/exit-contract hardening: the PowerShell entry point should expose an explicit process exit contract (0 on success, nonzero on failure), and timing should be emitted per major phase.

This evidence satisfies the user's pre-open local UAT gate. It does not itself authorize or redefine DG-P11.

### Local UAT attempt — harness failure (2026-09-22 08:09 ICT)

The first DG-P0..P10 acceptance-UAT attempt was **INVALID as product evidence**.

Observed:

- exact product HEAD remained `a09f79ae74a838d2c5998813560373c849669872`;
- the research-domain baseline command itself returned PASS;
- the UAT harness then failed before DG-P0..P10 execution because native command output was emitted into the PowerShell function return stream, so `$r` became a mixed array rather than the intended result object;
- no `UAT_REPORT.json` was produced;
- the wrapper's observed process exit code `0` was therefore also invalid as a harness success signal.

This is a UAT-tooling defect, not a GWF runtime/scientific failure. The failed attempt is preserved and must not be counted as PASS or FAIL for DG-P0..P10.

Remediation commit `00951921c6db3660dec1825ac1c00610efa38a53` isolates native output from the function return value, makes console labels Windows-codepage-safe, and forces harness exceptions to exit nonzero.


## TD-UAT-02 — Live server / browser UAT readiness

**State:** RECORDED / UAT HARNESS PROVIDED / PRODUCT GAP OPEN

### User acceptance definition

For this project, UAT means:

```text
install
  -> start the actual GWF server
  -> open a browser
  -> interact with live backend state
  -> inspect/operate delivered product capabilities
```

Pytest, gate scripts and source-level verification are implementation qualification, not user acceptance testing.

### Formal-close product observations

At DG-P10 formal-close HEAD `a09f79ae74a838d2c5998813560373c849669872`:

- `src/gwr/api.py` provides a real FastAPI application factory;
- the repository has no canonical production/local server launcher;
- the installation dependency set does not include `uvicorn`;
- `web/` is a static UAT/demo surface whose build metadata is explicitly non-authoritative;
- existing product HTTP endpoints expose authentication, tenancy/projects, dashboards, lifecycle, agent protocol/recovery and related earlier product surfaces;
- DG-P4 through DG-P10 document-governance services exist in the runtime but are not exposed as product HTTP endpoints, so they cannot yet receive browser-level product UAT without adding an actual product API/UI surface.

### Bounded browser-UAT tooling

Debt branch provides:

- `tools/browser_uat_server.py` — starts the actual `create_app(runtime)` against a disposable local SQLite UAT database and overlays only a transparent `/uat` inspection page;
- `tools/start_browser_uat.ps1` — verifies exact formal-close HEAD, installs `uvicorn` as UAT-only environment tooling if absent, starts localhost server and opens the browser.

The overlay must not be treated as a replacement product UI. It identifies live versus NOT_EXPOSED surfaces explicitly.

No DG-P11 implementation is authorized by this tooling.

## TD-UX-03 — Source preview, isolated execution and explainable experiment replay

**State:** RECORDED / NOT_IMPLEMENTED  
**Scope opened:** NO  
**Implementation authorization:** NONE  
**Sequencing:** after the approved/frozen UI/UX visual baseline; exact BPS/product slice to be separately specified and authorized.

### Product intent

GWF is not only a place to launch research experiments. It must also let an operator inspect, understand and replay the source artifacts that produced research results.

The future product surface therefore needs three linked capabilities:

```text
source artifact
    -> preview
    -> isolated execution
    -> explainable replay
    -> stdout/stderr/evidence/artifacts
```

The initial source-execution scope should prioritize PowerShell and Python experiment code. Additional text/source types may be previewable without execution when separately qualified.

### Source preview contract

The UI should support governed preview of source artifacts such as:

- PowerShell `.ps1`;
- Python `.py`;
- Markdown/text;
- JSON/YAML/configuration;
- experiment logs and evidence snippets.

Preview must preserve exact source identity:

- artifact/document ID where applicable;
- exact revision;
- content/source hash;
- originating repository/path when governed;
- line numbers;
- syntax-aware rendering for supported source languages.

Preview is read-only unless a separately governed source-editing capability is authorized.

### Isolated execution contract

Source execution must not run implicitly in the browser process or directly mutate the host research environment.

A future sandbox runner should provide:

- disposable per-run execution environment;
- Python virtual environment and/or stronger isolation as required by the threat model;
- exact interpreter/runtime identity;
- dependency lock/fingerprint;
- bounded CPU/memory/time;
- controlled filesystem mounts;
- explicit writable output directory;
- network disabled by default unless the experiment contract authorizes it;
- stdout/stderr capture;
- exit code and failure classification;
- produced artifact/evidence capture;
- environment and source hashes bound to the run;
- cleanup without deleting preserved evidence.

The exact isolation mechanism (venv, process sandbox, container, VM, or a tiered combination) is intentionally **not frozen by this debt record**. It requires a separate security/runtime specification before implementation.

### Explainable experiment authoring requirement

Experiment code written or materially rewritten by an AI must contain human-readable explanatory annotations sufficient for replay.

At minimum, each experiment-level function or logical execution unit should have an authoring-time explanation describing:

- what the function does;
- why it exists in the experiment;
- important inputs;
- expected outputs/side effects;
- assumptions or invariants that materially affect interpretation.

For Python this may be represented by docstrings/comments; for PowerShell by function-adjacent help/comments. A later specification may define a structured annotation format, but this debt item does not freeze syntax.

AI-generated explanation text is **descriptive metadata**, not scientific evidence and not a substitute for code, tests, provenance, or measured outcomes.

### Static function/comment manifest

Before execution, the runner should statically extract a manifest from the exact source revision.

Minimum conceptual fields:

```text
source_hash
file_path
function_id
function_name
language
start_line
end_line
explanation/comment
parent/module context
```

Extraction must use language-aware parsing rather than regex-only inference for supported languages:

- Python AST for Python;
- PowerShell AST/parser for PowerShell.

If a required experiment function has no usable explanation, the UI must report that absence explicitly. It must not fabricate a replay explanation after the fact and present it as if it existed in the executed source.

### Runtime execution events

The sandbox runner should emit bounded execution events for experiment-owned functions/logical units, for example:

```text
FUNCTION_ENTER
FUNCTION_EXIT
FUNCTION_ERROR
```

Each event should bind at least:

- run/execution identity;
- exact source hash;
- function ID/name;
- source line span;
- timestamp/order;
- call/parent context where available;
- status;
- stdout/stderr/evidence offsets or references.

Instrumentation should focus on governed experiment-owned code. It should not automatically trace every third-party/library function.

### Explainable replay UX

During live execution or later replay, the browser should synchronize:

```text
execution timeline
      |
      +--> active function
      +--> highlighted source lines
      +--> authoring-time explanation/comment
      +--> inputs/context summary
      +--> stdout/stderr
      +--> produced evidence/artifacts
      +--> exit/failure state
```

When execution reaches a function, the operator should be able to see:

- function name;
- source file and line range;
- the exact explanatory comment/docstring extracted from the executed source revision;
- current execution state;
- previous/next experiment-level steps;
- relevant output/evidence generated at that point.

Replay must distinguish clearly between:

1. **source-authored explanation** — text present in the executed revision;
2. **runtime facts** — measured events/output/evidence;
3. **later AI interpretation** — optional analysis generated after execution.

These three layers must never be silently conflated.

### Reproducibility and governance

A replayable run should bind:

```text
source revision/hash
+ function/comment manifest hash
+ sandbox/environment identity
+ dependency identity
+ inputs/configuration
+ execution-event stream
+ outputs/evidence
```

A later edit to comments/docstrings must not rewrite the historical explanation shown for an already completed run. Historical replay resolves against the exact executed source revision and manifest.

### UI direction

The future source workspace should extend the approved Document/Artifact preview model rather than create a separate developer console.

Expected conceptual layout:

```text
Source / artifact list
        |
        +---------------- Source Preview ----------------+
        | line numbers + syntax + active-line highlight |
        +-----------------------------------------------+
        |
        +-- Inspector / Replay
              Preview
              Functions
              Execution
              Output
              Evidence
              History
```

A function navigator should list function names and explanations. During execution/replay the currently active function is highlighted and its explanation is visible without requiring the user to read the entire file.

### Acceptance intent

A future implementation must prove at least:

- exact source revision is previewed;
- Python and PowerShell supported-source parsing is deterministic;
- experiment-level functions receive stable manifest identities;
- missing authoring explanations are surfaced, not silently invented;
- sandbox execution cannot silently mutate the host environment;
- runtime events resolve back to exact source/function spans;
- live execution and historical replay show the same frozen source-authored explanation for the same run;
- function-enter/exit/error state is visible to the operator;
- stdout/stderr and generated artifacts/evidence remain linked to the relevant run/function context;
- historical replay remains valid after the working copy changes;
- no AI explanation is presented as measured scientific evidence.

### Explicit non-scope of this debt record

This record does **not** authorize:

- sandbox/runtime implementation;
- arbitrary code execution from the browser;
- host shell execution;
- source editing;
- automatic dependency installation from untrusted code;
- unrestricted network access;
- hidden chain-of-thought capture/display;
- BPS-I01 or later-slice opening;
- any change to current scientific/governance results.

This item is a frozen product-direction/debt record only. Detailed security model, execution protocol, annotation schema, APIs, UI slice and qualification gates require separate specification and authorization.
