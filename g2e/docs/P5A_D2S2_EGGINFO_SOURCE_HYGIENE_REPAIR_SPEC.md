# P5A D2-S2 Source Hygiene Repair — Generated Egg-Info

## Status

SPEC-LOCKED / ZERO-SCIENCE / SOURCE-HYGIENE-ONLY

Baseline:

- branch: `feature/g2e-framework`
- exact baseline HEAD: `54950e2c4f476d205523a378f20adb6e4d01ea02`
- diagnostic result: `DIAGNOSTIC_BLOCKED`
- sole failed gate: `git_worktree_clean_excluding_local`
- observed untracked path: `src/governed_workflow_runtime.egg-info/`
- D2-S2 scientific attempt remains NOT AUTHORIZED and NOT CONSUMED.

## Root cause

The repository uses setuptools with a `src` package layout. Editable/development installation can
materialize generated `*.egg-info/` metadata under `src/`. The repository `.gitignore` does not
currently ignore `*.egg-info/`, so this generated metadata is reported by `git status --porcelain`
and blocks the qualified D2-S2 source-cleanliness gate.

## Frozen repair

The only production-source mutation authorized by this repair is:

- append `*.egg-info/` to the repository root `.gitignore`.

No D2-S2 script, preflight, fixture, model, verifier, retry policy, authority profile, lock, or scientific
configuration may be changed.

## Qualification requirements

The candidate must prove:

1. `.gitignore` contains the exact pattern `*.egg-info/`;
2. a synthetic `src/governed_workflow_runtime.egg-info/PKG-INFO` is ignored by Git;
3. existing frozen D2-S2 one-click and preflight blobs are unchanged;
4. D2-S2 static qualification still passes;
5. P1/P1.4/P1.5/P2/P3/P4 regressions pass;
6. no scientific execution is performed.

## Adjudication

- `SOURCE_HYGIENE_PASS_LOCAL_DIAGNOSTIC_REQUIRED`: all qualification gates pass.
- otherwise: repair remains blocked.

A PASS only authorizes rerunning the already-qualified elevation bootstrap diagnostic. It does not
authorize the D2-S2 scientific attempt or a model turn.
