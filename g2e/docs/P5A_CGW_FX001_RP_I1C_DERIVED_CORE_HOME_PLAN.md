# P5A-CGW FX001 RP-I1C — Derived Core-Home Ownership Binding

Status: ZERO-SCIENCE READ-ONLY DIAGNOSTIC

## Source invariant

For the qualified packaged CGW launcher, `ensurePackagedRuntime()` installs the runtime bundle at:

```
<coreHome>/versions/<version-platform-arch>/
```

and the spawned Responses daemon executable is:

```
<coreHome>/versions/<version-platform-arch>/runtime/bun.exe
```

Therefore the live listener executable path can derive the launcher coreHome without reading process environment.

## Question

Given the live listener executable, derive its actual coreHome and check whether that root's:

- `runtime/launcher-supervisor.json`
- `runtime/launcher-browser.json`
- `config.json`

bind the live listener PID and its launcher parent.

Also classify the launcher profile using direct descriptor/config evidence when present.

## Safety

Read-only files/process metadata plus GET /healthz.
No /v1/responses request, no model, no browser submission, no MCP, no scientific attempt.
