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
