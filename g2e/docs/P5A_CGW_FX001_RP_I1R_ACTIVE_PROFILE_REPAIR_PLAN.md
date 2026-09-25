# P5A-CGW FX001 RP-I1R — Active Profile Instance Binding Repair

Status: ZERO-SCIENCE INSTRUMENTATION REPAIR

## Motivation

The TC-003 route-path causal closure proved that the live service on 127.0.0.1:17841 was the development-profile CGW daemon while the runner watched production-profile evidence roots.

The repaired instrumentation must never choose an evidence root before binding the active listener instance.

## Binding order

```
GET /healthz
  -> exact health PID
  -> sole TCP listener PID
  -> listener process + parent process
  -> enumerate qualified launcher profiles
  -> read each profile's launcher-supervisor.json
  -> require exactly one profile where:
       supervisor.daemonPid == health/listener PID
       supervisor.ownerPid  == listener parent PID
       launcher-browser.json.pid == supervisor.ownerPid
  -> only then select:
       active config.json
       active launcher log root
       active diagnostics root
  -> validate active config semantic contract
  -> GET-only /v1/responses canary
```

## Qualified profiles

For CGW 4.0.7 source commit `b59d7dc51b84fb1f465ff1d00f5207f3b2b4a494`:

- production default core home: `~/.codex-chatgpt-web`
- production default launcher userData: `%APPDATA%/Codex Web GPT`
- development default core home: `~/.codex-chatgpt-web-dev`
- development default launcher userData: `<dev-core-home>/launcher`

The probe may inspect both candidate roots, but exactly one must bind to the live PID chain.

## PASS

`PASS_ACTIVE_PROFILE_INSTANCE_BOUND_ZERO_SCIENCE`

requires:

- exact healthy idle CGW 4.0.7 full-mode service;
- one listener PID and equality with health PID;
- listener process exists and command contains `serve`;
- parent process exists;
- exactly one profile's supervisor binds ownerPid/daemonPid to that process pair;
- same profile's browser descriptor PID binds the launcher owner;
- active config comes from the bound profile and matches host/port/release/mode/browserHost;
- profile purpose rule is valid (production: purpose absent; development: purpose=dev-harness);
- GET `/v1/responses` returns source-defined 426;
- no POST, model, browser submission, or MCP.

## Governance

PASS repairs RP-I1/RP-I2 instrumentation only. It does not authorize a replacement scientific attempt.
