# P5A-CGW FX001 — Project-local coherent Codex 0.153.4 repair

## Confirmed mechanism

The local installation is mixed-build:

- the selected Windows sandbox helper is byte-identical to the official `rust-v0.153.4` x86_64 Windows helper;
- the local `codex.exe` is not byte-identical to the official `rust-v0.153.4` x86_64 Windows Codex binary;
- the local sender emits `interactive-provision`, while the selected official 0.153.4 helper only accepts the older mode set.

The scientific attempt remains pre-marker and unconsumed.

## Repair principle

Do not mutate the global Codex installation and do not patch one helper in place.

Prepare a project-local, official, internally coherent `rust-v0.153.4` package and bind GWF only to that package after zero-model qualification.

## Official frozen package

Tag: `rust-v0.153.4`
Tag commit: `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`

Windows x86_64 package:
`codex-package-x86_64-pc-windows-msvc.tar.gz`

Package SHA-256:
`a6ef3442cb12766a88b39311d79244289e4f9763e2c53ff4fbebc2cb653cc5f3`

Expected contained identities:

- `codex.exe`: `444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b`
- `codex-windows-sandbox-setup.exe`: `0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4`

## Qualification gate

Before any local attempt rearm:

1. download the exact official package;
2. verify package SHA-256;
3. extract into an isolated temporary/project-local directory;
4. require exactly one `codex.exe` and exactly one `codex-windows-sandbox-setup.exe`;
5. verify both contained hashes;
6. verify `codex --version` reports 0.153.4;
7. perform no model request, browser submission, MCP invocation, or sandbox setup.

Only after this package-coherence gate passes may a successor execution lock bind the same still-unconsumed attempt to the project-local Codex binary.

## Non-goals

- no global installer repair;
- no alpha/pre-release adoption;
- no manual helper replacement;
- no scientific rerun during qualification.
