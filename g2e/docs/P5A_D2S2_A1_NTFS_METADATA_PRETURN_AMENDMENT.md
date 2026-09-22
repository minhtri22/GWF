# G2E P5A D2-S2 A1 — NTFS Metadata Preturn Amendment

## Status

SPEC-LOCKED / ZERO-SCIENCE / PRETURN-INFRASTRUCTURE-ONLY

Baseline:

- branch: `feature/g2e-framework`
- exact baseline HEAD: `1587fcd193456fc62ff602fe0655e9fbffe775e9`
- predecessor blocked report SHA256:
  `f1fbcfbb41f8f726362bd04735355eeb5ea9e923dc018e237b8027d41348e42c`
- scientific attempt remains NOT AUTHORIZED and NOT CONSUMED.

## 1. Unchanged scientific identities

- study: `p5a-d2s2-isolated-volume-root-read-successor`
- attempt: `p5a-d2s2-p5-fx-001-attempt-001`
- profile: `g2e_p5a_d2s2`
- input SHA256:
  `a176454229feef1ce8bd7eab1ea79fbfeff07c229c88123edf862fea9160eef6`
- TASK.md SHA256:
  `4c4aba6a82d540440dfef725b2568afdef4be3b26c3e4e84e2b34c54e6dd460e`
- Codex SHA256:
  `a337b7433ebb351c0165dd074cf2500a20fca9ceab3680a71df593653bf70dc8`

## 2. Fresh local root

A1 MUST use:

`g2e/.local/P5A-D2S2-A1/`

The predecessor root `g2e/.local/P5A-D2S2/` is read-only historical evidence and MUST NOT be deleted,
renamed, reused, or modified by A1.

## 3. Volume-root closure

A1 still uses one fresh 128 MiB dynamically allocated NTFS VHDX and deterministic free-drive selection
R..Z.

The task payload at the isolated drive root is exactly:

- `TASK.md`
- `input.json`

The only additional root entry that MAY exist is:

- `System Volume Information`

If present, it MUST be a directory and is classified as isolated-volume filesystem-support metadata,
not task payload.

No other file or directory is admissible. A1 MUST fail closed on any additional entry.

The preflight MUST separately record:

- exact task payload names;
- filesystem-support metadata names;
- unexpected root names.

## 4. Authority interpretation

`:root = read` remains confined to the fresh A1 VHDX volume. The host repository, user profile, and
ordinary user data remain outside the volume.

A1 does not claim that `System Volume Information` is task data. Its presence is tolerated only because
it is OS/filesystem-created support metadata on the dedicated isolated volume.

Result write authority remains exact to `<isolated-volume-root>\result.json`.

Network remains disabled.

## 5. Frozen no-turn sequence

Allowed App Server sequence remains unchanged through `thread/start`, then STOP.

The A1 preflight and one-click wrapper MUST NOT contain `"turn/start"`.

## 6. Qualification requirements

A1 implementation must prove:

1. new local root is `P5A-D2S2-A1`;
2. predecessor local root is never deleted/reused;
3. task payload closure is exactly two frozen files;
4. optional `System Volume Information` is directory-only;
5. any other root entry blocks;
6. fixture/Codex hashes unchanged;
7. root-read/exact-result-write/network-off profile unchanged;
8. no-turn firewall unchanged;
9. P1/P1.4/P1.5/P2/P3/P4 regressions PASS;
10. exact implementation blobs and CI artifact are locked before local execution.

## 7. Authorization boundary

Qualification PASS authorizes only one fresh local A1 no-turn preturn execution.

It does not authorize `turn/start`, scientific-attempt consumption, repository capability admission, or
runtime-adapter admission.
