# P5A-CGW FX001 RP-L1 — Launcher Identity Requalification

Status: ZERO-SCIENCE READ-ONLY DIAGNOSTIC

## Question

The previously qualified launcher identity was:

- SHA256: ac152ad499b1f41b2cafe94a3d05f5d4e4d3cd7ddbb417b9c60b118b08bc3cbb
- size: 223980032
- FileVersion: 4.0.7
- ProductVersion: 4.0.7.0

The current executable at the same path produced SHA256
5bedc89da21594bac53edceedf929b3640ed877a63a6d80fe3d6f0b94bc2182c.

RP-L1 records the current executable's file identity and Authenticode metadata without launching it.

## Safety

Read-only file metadata only.
No process launch.
No TCP listener.
No HTTP.
No Responses request.
No model.
No browser submission.
No MCP.
No scientific attempt.

## Interpretation

A same-version/different-SHA result is diagnostic only and does not automatically qualify the new binary.
