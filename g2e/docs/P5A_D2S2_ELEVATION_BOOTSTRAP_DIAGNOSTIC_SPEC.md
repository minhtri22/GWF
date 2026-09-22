# P5A D2-S2 Elevation Bootstrap Diagnostic — Bounded Technical Repair

## Status

SPEC-LOCKED / ZERO-SCIENCE / LOCAL-DIAGNOSTIC-ONLY

Baseline before this repair:

- branch: `feature/g2e-framework`
- exact baseline HEAD: `4f61aff2aff5da6a75d696cf758968bcbd697c74`
- D2-S2 scientific attempt remains NOT AUTHORIZED and NOT CONSUMED.
- Existing qualified D2-S2 one-click and preflight blobs are immutable inputs to this diagnostic.

## Observed failure

The qualified D2-S2 one-click prints the UAC handoff message, the unelevated console returns, and no
`g2e/.local/P5A-D2S2/report/P5A_D2S2_ONECLICK_REPORT.json` exists.

The existing one-click creates its report object only after the elevated child has already passed several
bootstrap gates. Therefore an elevated-child failure before report initialization is not observable after
the UAC window closes.

This is a technical observability failure only. It is not a scientific PASS/FAIL and does not consume the
D2-S2 scientific attempt.

## Diagnostic question

Which launcher/elevation or pre-report gate prevents the qualified D2-S2 one-click from reaching its
report-producing phase on the user's Windows host?

## Frozen scope

The diagnostic MAY:

- create a separate local diagnostic directory under `g2e/.local/P5A-D2S2-BOOTSTRAP/`;
- write JSON/Markdown diagnostic reports before UAC;
- self-elevate through UAC;
- inspect current Git identity/worktree state;
- read the existing D2-S2 qualification lock;
- compute Git blob identities for the already-qualified one-click/preflight;
- test existence/hash of the selected Python and Codex executables;
- record whether an old `g2e/.local/P5A-D2S2` root already exists.

The diagnostic MUST NOT:

- invoke Codex or Codex App Server;
- send any RPC request;
- contain or send `turn/start`;
- create, attach, format, or mount any VHD/VHDX;
- invoke `diskpart`;
- read/copy the scientific fixture;
- create or modify `result.json`;
- alter model/task/verifier/retry configuration;
- authorize or consume any scientific attempt.

## Report contract

Primary artifact:

`g2e/.local/P5A-D2S2-BOOTSTRAP/report/P5A_D2S2_ELEVATION_BOOTSTRAP_REPORT.json`

Markdown mirror:

`g2e/.local/P5A-D2S2-BOOTSTRAP/report/P5A_D2S2_ELEVATION_BOOTSTRAP_REPORT.md`

The unelevated parent MUST create the report before requesting UAC. The elevated child MUST update the
same report immediately on entry. The parent MUST record UAC/start failures and the elevated process exit
code after the child exits.

## Adjudication classes

- `DIAGNOSTIC_PASS`: elevation succeeded and every frozen pre-report gate is observable and passes.
- `DIAGNOSTIC_BLOCKED`: one or more pre-report gates fail; report identifies exact gate(s).
- `LAUNCHER_BLOCKED`: UAC/process launch fails or is cancelled; report still exists.
- `DIAGNOSTIC_INTERNAL_ERROR`: diagnostic itself cannot complete its bounded checks; report still exists
  whenever the project-local report path is writable.

None of these classes is a scientific result.

## Next-step rule

After one fresh qualified diagnostic execution, inspect the report exactly once. Any repair to the
qualified D2-S2 one-click must be separately bounded, statically qualified, and locked before local
execution. No scientific model turn is authorized by this diagnostic.
