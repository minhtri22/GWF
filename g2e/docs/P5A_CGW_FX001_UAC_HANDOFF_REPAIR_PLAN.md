# P5A-CGW FX001 — V2R5 UAC Handoff Repair

## Trigger

V2R4 parent preflight passed, but the elevated child returned exit code 1 before creating the functional execution report or durable attempt marker.

Observed state:

- parent preflight: PASS;
- elevated child exit: 1;
- final report: absent;
- attempt marker: absent;
- attempt remains unconsumed.

## Mechanism

The UAC handoff still passed multiple resolved paths directly through `Start-Process -ArgumentList`.

At least two frozen paths contain spaces:

- `Codex Web GPT.exe`;
- `AppData\Roaming\Codex Web GPT`.

The elevated child also depended on implicit `git` PATH lookup while Python/Codex/CGW paths were otherwise resolved explicitly.

This creates a pre-marker infrastructure ambiguity: argument tokenization and elevated PATH can terminate the child before the script reaches LocalRoot/report creation.

## Repair

V2R5 is pre-marker infrastructure only.

Before UAC, the parent:

1. resolves exact Python, Codex, Git and CGW launcher paths;
2. validates all existing V2R4 preflight invariants;
3. writes a non-secret handoff JSON under `g2e/.local` containing those exact paths plus BridgeHome/LauncherData;
4. starts the elevated child with only no-space control arguments:
   - ProjectRoot;
   - HandoffConfig;
   - HandoffDiagnostic;
   - ElevatedChild.

The elevated child:

1. loads exact paths from the handoff JSON before relying on PATH;
2. uses the explicit `git.exe` path for all source identity/cleanliness checks;
3. writes a persistent diagnostic JSON on any uncaught elevated-child error, including whether the durable attempt marker exists;
4. exits non-zero on such a trapped failure.

## Scientific contract

Unchanged:

- attempt id;
- CGW 4.0.7 launcher identity;
- Codex binary;
- route/model/mode/connector;
- P5-FX-001 task/result;
- Codex authority;
- marker-before-sole-turn/start consumption boundary;
- retry=0;
- timeout=90s;
- route/browser/MCP evidence contract.

No model/browser/MCP execution is permitted during qualification.

## Qualification

Linux and Windows zero-model QA must prove:

- V2R5 lock guard;
- explicit Git executable use;
- no direct Python/Codex/Git/CGW/Bridge/Launcher path arguments in the UAC argument list;
- handoff JSON load and project-root binding;
- persistent elevated-child diagnostic;
- PowerShell 5.1 parser safety;
- all prior admission/runner/verifier/preregistration regressions PASS.
