# G2E P5A D2-S2 A2 — Binary Component Lineage Read-Only Diagnostic

## Status

SPEC-LOCKED / ZERO-SCIENCE / READ-ONLY-BINARY-LINEAGE

Baseline:

- branch: `feature/g2e-framework`
- exact baseline HEAD: `dee2b0ed53dee3c07b4a49db28496a001b9a22a8`
- bound sandbox-state evidence SHA256:
  `f74b1007c8a08268961b4b3286ec150025c1d6183798c689e2a6ce5a0b399be7`

## 1. Purpose

Determine whether the local Windows sandbox setup failure is caused by binary-component skew between the
already-frozen `codex.exe` and the setup helper selected by the frozen resolver.

## 2. Frozen executable

Expected `codex.exe` path:

`%LOCALAPPDATA%\Programs\OpenAI\Codex\bin\codex.exe`

Expected SHA256:

`a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8`

The collector must fail closed if the executable hash differs.

## 3. Exact helper resolver model

Reproduce the exact candidate priority of frozen source
`openai/codex@3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`,
`helper_materialization::bundled_executable_path_for_exe`:

For the running/frozen `codex.exe` path:

1. direct sibling:
   `<exe-dir>\codex-windows-sandbox-setup.exe`
2. if `<exe-dir>` basename is `bin`:
   `<package-dir>\codex-resources\codex-windows-sandbox-setup.exe`
3. `<exe-dir>\codex-resources\codex-windows-sandbox-setup.exe`

If none exists, repeat the same lookup against the canonicalized executable path.

The first existing regular file is the resolved helper candidate.

## 4. Allowed observations

For `codex.exe` and every unique helper candidate path:

- sanitized path;
- existence;
- file size;
- SHA256;
- FileVersion;
- ProductVersion;
- ASCII marker presence for:
  - `interactive-provision`
  - `full`
  - `provision-only`
  - `read-acls-only`

Also return:

- resolver candidate type/order;
- exact candidate selected by frozen-source priority;
- whether more than one helper candidate exists;
- whether selected helper ProductVersion/FileVersion matches Codex version metadata when comparable.

No binary content is returned.

## 5. Sanitization

Replace the user profile prefix with `<USERPROFILE>`.

Do not return usernames outside that sanitized path.

## 6. Prohibitions

The collector MUST NOT:

- execute `codex.exe`;
- execute any helper;
- invoke App Server;
- send RPC;
- modify, copy, delete, rename, or replace binaries;
- touch VHD/VHDX;
- change PATH;
- change ACL/firewall/users/groups;
- authorize `turn/start`;
- authorize or consume a scientific attempt.

## 7. Output

Write one file:

`g2e/.local/P5A-D2S2-A2/return/P5A_D2S2_A2_BINARY_COMPONENT_LINEAGE_<UTC>.json`

The output must include:

- `evidence_return_only=true`;
- `turn_start_request_sent=false`;
- `scientific_attempt_consumed=false`.

## 8. Qualification

PASS requires:

- PowerShell parser PASS;
- Windows resolver self-test PASS;
- static read-only scope tests PASS;
- exact frozen codex hash embedded;
- P1/P1.4/P1.5/P2/P3/P4 regressions PASS.

A PASS authorizes exactly one local read-only binary lineage diagnostic.
