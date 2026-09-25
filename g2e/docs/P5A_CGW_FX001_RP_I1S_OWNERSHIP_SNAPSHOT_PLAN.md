# P5A-CGW FX001 RP-I1S — Development Ownership-State Snapshot

Status: ZERO-SCIENCE READ-ONLY DIAGNOSTIC

## Question

The live CGW service is bound to health/listener PID 27240 with launcher parent PID 15604, while the development profile's supervisor and browser descriptor exist but do not bind that process pair.

RP-I1S asks only:

- Which ownerPid / daemonPid / descriptor pid do the development ownership files currently reference?
- Are those referenced PIDs alive?
- What are their process creation times and executable paths?
- Are the supervisor and descriptor from the same launcher generation?
- Are the ownership files older/newer than the live listener process?

## Safety

Read-only local files/process metadata plus GET /healthz.
No /v1/responses request, no model, no browser submission, no MCP, no scientific attempt.

The browser descriptor is projected to non-secret identity fields only; control/helper details are not emitted.
