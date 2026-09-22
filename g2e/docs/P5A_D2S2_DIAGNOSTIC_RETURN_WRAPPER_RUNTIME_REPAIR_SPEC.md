# P5A D2-S2 Diagnostic Return Wrapper — Runtime Git Invocation Repair

## Status

SPEC-LOCKED / ZERO-SCIENCE / WRAPPER-RUNTIME-REPAIR-ONLY

Baseline:

- branch: `feature/g2e-framework`
- exact baseline HEAD: `c4129a4dc8c30d4bc97de2acbfcfd20d90e68762`
- prior return-wrapper lock remains historical evidence;
- D2-S2 scientific attempt remains NOT AUTHORIZED and NOT CONSUMED.

## Observed runtime failure

On Windows PowerShell 5.1, the qualified return wrapper entered:

`Fetching exact qualified branch state...`

and then failed with Git usage output showing that `git -C <root>` received no Git subcommand.

The wrapper helper was declared as:

`Invoke-Git([string]$Root, [string[]]$Args)`

PowerShell's automatic variable `$args` is case-insensitive with `$Args`. The runtime therefore did not preserve the intended Git argument vector in the helper.

This is a wrapper transport/runtime defect only. No diagnostic execution, model turn, VHD/VHDX operation, or scientific attempt occurred.

## Frozen repair

The repair SHALL:

1. rename the helper array parameter from `$Args` to `$GitArgs`;
2. invoke the helper with explicit named parameters:
   - `-Root $ProjectRoot`
   - `-GitArgs @(...) `;
3. splat only `@GitArgs` into the Git process;
4. add a zero-science `-GitInvocationSelfTest` mode that executes only:
   `git -C <root> rev-parse --is-inside-work-tree`;
5. require CI to execute that self-test against the checked-out repository;
6. preserve exact frozen blobs for:
   - D2-S2 isolated-volume one-click;
   - D2-S2 preflight;
   - elevation bootstrap diagnostic.

## Prohibitions

The repair MUST NOT:

- invoke Codex or Codex App Server;
- send RPC or `turn/start`;
- create/attach/format/mount VHD/VHDX;
- touch scientific fixture content;
- authorize or consume a scientific attempt;
- alter model/task/verifier/retry semantics.

## Qualification

PASS requires:

- PowerShell parser PASS;
- real helper Git invocation self-test PASS;
- wrapper static qualification PASS;
- elevation diagnostic qualification PASS;
- egg-info hygiene qualification PASS;
- frozen D2-S2 static qualification PASS;
- P1/P1.4/P1.5/P2/P3/P4 regressions PASS;
- zero-science token proof PASS;
- frozen blob identity checks PASS.

Adjudication:

`RETURN_WRAPPER_RUNTIME_REPAIR_PASS_LOCAL_EXECUTION_REQUIRED`

A PASS authorizes only one fresh local execution of the repaired diagnostic return wrapper.
