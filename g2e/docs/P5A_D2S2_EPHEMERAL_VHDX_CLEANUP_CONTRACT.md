# G2E P5A D2-S2 — Ephemeral VHDX Cleanup Contract

## Status

ACTIVE / INFRASTRUCTURE-HYGIENE / NON-SCIENTIFIC

## Problem

Historical D2-S2 preturn packages created isolated VHDX volumes and assigned drive letters, but their
frozen one-click implementations did not detach those VHDX images on every exit path.

Observed mounted historical volumes:

- predecessor: label `G2ED2S2`
- A1: label `G2ED2S2A1`
- A2: isolated A2 VHDX

This is infrastructure resource leakage, not scientific evidence.

## Historical immutability

The frozen predecessor, A1, and A2 one-click blobs MUST NOT be edited retroactively.

Their VHDX files, reports, and evidence remain historical artifacts.

Cleanup means:

- dismount the exact VHDX image;
- release its transient drive letter.

Cleanup MUST NOT mean:

- delete the VHDX;
- delete or modify fixture files;
- delete reports/evidence;
- rewrite historical source;
- mutate scientific state.

## Immediate bounded cleanup

A dedicated cleanup utility may target only these exact repository-local VHDX paths:

1. `g2e/.local/P5A-D2S2/volume/P5A-D2S2-TASK.vhdx`
2. `g2e/.local/P5A-D2S2-A1/volume/P5A-D2S2-A1-TASK.vhdx`
3. `g2e/.local/P5A-D2S2-A2/volume/P5A-D2S2-A2-TASK.vhdx`

For each target it must record:

- file exists;
- attached before;
- action;
- attached after;
- cleanup error if any.

PASS requires every existing target to be detached after cleanup.

## Mandatory successor rule

Every future D2-S2 successor that attaches a VHDX MUST:

1. track whether that exact VHDX was attached by the current run;
2. execute cleanup from a `finally` path;
3. dismount the exact image path before script termination;
4. verify `Attached == false`;
5. record cleanup state in its report;
6. return nonzero if cleanup verification fails.

A successor MUST NOT use `exit` inside the scientific/preturn work body in a way that can bypass cleanup.
It should retain the intended exit code, run `finally`, then exit only after cleanup has completed.

This rule applies equally to PASS, BLOCKED, INVALID, and exception paths.

## Scientific firewall

VHDX detach/release does not authorize:

- `turn/start`;
- scientific attempt consumption;
- runtime adapter execution;
- automatic retry.

It is infrastructure hygiene only.
