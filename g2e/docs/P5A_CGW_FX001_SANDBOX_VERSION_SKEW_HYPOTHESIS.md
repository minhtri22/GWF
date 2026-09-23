# P5A-CGW FX001 — Windows Sandbox Sender/Helper Version-Skew Hypothesis

## Existing local evidence

The V2R5 sandbox log is exactly 234 bytes with SHA-256:

`9AFD442F2C205C514A5E513A2604AB8EB59D439259AF211D7D151AB896A57858`

and reports:

`helper_request_args_failed: failed to parse payload json: unknown variant interactive-provision, expected one of full, provision-only, read-acls-only`.

The durable attempt marker is absent. The runner records:

- `driver_exception = RuntimeError:PREDISPATCH_SANDBOX_SETUP_FAILED`;
- `turn_start_marker_created = false`;
- `turn_start_request_sent = false`;
- `attempt_consumed = false`.

Predispatch admission is PASS and the frozen CGW/Codex identities remain intact.

## Upstream contract evidence

OpenAI Codex commit:

`1bc8fb16ae53512c0c7723a436e4b11be81ad4a8`

("Separate Windows sandbox provisioning from ACL refresh", 2026-09-02)

introduced `interactive-provision` on both sides of the same contract:

1. orchestrator payload enum gained `InteractiveProvision` and elevated provisioning began emitting it;
2. setup-helper payload enum gained `InteractiveProvision`;
3. helper dispatch treats `InteractiveProvision | ProvisionOnly` as provisioning;
4. an upstream regression test was added to verify that the helper accepts `interactive-provision`.

Therefore a same-build sender/helper pair at or after that change should not reject the variant.

## Candidate mechanism

**H-SBX-VS1: mixed-version or stale bundled Windows sandbox helper.**

The observed sender understands/emits `interactive-provision`, while the selected setup helper parses only the older mode set. This is consistent with an app/helper packaging skew, stale bundled helper, or wrong helper selected from the Codex install layout.

This is an infrastructure hypothesis, not a scientific or route/model hypothesis.

## Codex helper lookup order to inspect

Upstream helper resolution checks, relative to the running `codex.exe`:

1. direct sibling `codex-windows-sandbox-setup.exe`;
2. when `codex.exe` is under a `bin` directory, package-level `codex-resources\codex-windows-sandbox-setup.exe`;
3. `bin\codex-resources\codex-windows-sandbox-setup.exe`;
4. only if no bundled path resolves, fallback name lookup.

No helper execution is required to inspect these candidates.

## Falsification

H-SBX-VS1 is supported if the actually selected/bundled helper identity is older or differs from the Codex executable's packaged release set, especially if its behavior corresponds to the pre-`interactive-provision` enum.

H-SBX-VS1 is falsified if the selected helper is demonstrably the same compatible build that accepts `interactive-provision`; in that case the next decomposition must explain how an incompatible parser was invoked despite helper resolution.

## Next step — existing/read-only identity census only

Collect without execution:

- exact Codex path/hash/version/mtime;
- exact helper candidates in lookup order;
- helper SHA-256, size, file/product version, mtime, Authenticode status;
- whether any isolated `.sandbox-bin` helper exists;
- `setup_error.json` if already present;
- `codex --version` only if desired as read-only process metadata.

Do not delete LocalRoot, do not run sandbox setup, and do not reauthorize or consume the scientific attempt.
