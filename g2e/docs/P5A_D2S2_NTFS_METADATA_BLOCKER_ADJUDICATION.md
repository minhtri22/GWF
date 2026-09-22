# G2E P5A D2-S2 — NTFS Metadata Preturn Blocker Adjudication

## Status

**Verdict:** PRETURN_INFRASTRUCTURE_BLOCKED / SCIENTIFIC ATTEMPT UNUSED  
**Scientific result:** NONE  
**Model turn executed:** FALSE  
**Scientific attempt consumed:** FALSE

## 1. Bound local evidence

Returned report:

- file: `P5A_D2S2_ONECLICK_REPORT.json`
- SHA256: `f1fbcfbb41f8f726362bd04735355eeb5ea9e923dc018e237b8027d41348e42c`
- schema: `G2E-P5A-D2S2-ONECLICK-REPORT-v1`
- source HEAD: `c442911523faa5ab5da6f699909267fa438144c7`
- one-click blob: `1507b716645971ee60b0c2131973a953f98e7036`
- preflight blob: `005bd3ff5f34ea60a05d15baa25a0d4f6e9341c3`
- selected drive: `R:`
- VHDX: `g2e/.local/P5A-D2S2/volume/P5A-D2S2-TASK.vhdx`
- preturn gate: FAIL before App Server preflight
- `turn_start_request_sent=false`
- `scientific_attempt_consumed=false`

Observed diagnostic:

`ISOLATED_VOLUME_PRESTATE_DRIFT:input.json,System Volume Information,TASK.md`

No preflight evidence file was created and no config hash was materialized.

## 2. Classification

The blocker is a preturn infrastructure/specification mismatch.

The frozen implementation assumed that a newly formatted NTFS drive root would contain exactly the two
copied task files. On the observed Windows system, NTFS/Windows materialized the OS-owned directory
`System Volume Information` at the isolated drive root.

This blocker occurred before:

- Codex App Server preflight;
- permission-profile qualification;
- `thread/start`;
- any `turn/start`;
- any scientific result.

Therefore it is not a scientific PASS, FAIL, or INVALID attempt outcome.

## 3. No-rescue boundary

The existing qualified D2-S2 package and its blocked report remain immutable historical evidence.

A repair may not simply ignore arbitrary extra root entries. Any successor preturn package must
prospectively define a closed root-entry policy and separately qualify it before another local run.

The scientific fixture, task semantics, expected result semantics, model/provider identity, Codex
executable hash, network-off contract, and scientific attempt identity remain unchanged.

## 4. Allowed successor direction

A bounded D2-S2 preturn infrastructure amendment may classify only the observed
`System Volume Information` directory as isolated-volume filesystem-support metadata, provided:

1. the VHDX itself remains dedicated to this study;
2. no host repository/user/task data is copied into that metadata directory;
3. the task payload remains exactly `TASK.md` + `input.json`;
4. every other unexpected volume-root entry is a blocker;
5. network remains disabled;
6. result write authority remains exact;
7. no `turn/start` is possible in the successor preturn;
8. the blocked local root is preserved rather than silently reused.

Such a package is an infrastructure amendment before science, not a new scientific attempt.
