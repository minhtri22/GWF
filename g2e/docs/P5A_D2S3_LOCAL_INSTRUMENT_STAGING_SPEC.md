# G2E P5A D2-S3 — Local Release-Coherent Instrument Staging

## Status

SPEC-LOCKED / ZERO-SCIENCE / LOCAL-STAGING-ONLY

Prerequisite:

- `P5A_D2S3_S3_I0_OFFICIAL_RELEASE_COHERENCE_LOCK.json`
- S3-I0 verdict:
  `OFFICIAL_RELEASE_COHERENT_LOCAL_STAGING_REQUIRED`

## 1. Purpose

Stage the exact official `rust-v0.153.4` Windows x86_64 Codex executable and setup helper into an
isolated repository-local instrument root without modifying the user's global Codex installation.

This is instrument preparation only.

## 2. Fixed local root

`g2e/.local/P5A-D2S3-INSTRUMENT/`

Final package layout:

`package/bin/codex.exe`

`package/codex-resources/codex-windows-sandbox-setup.exe`

The layout is chosen to match the frozen helper resolver contract for an executable located under a
directory named `bin`.

## 3. Exact release assets

Download only:

1. `codex-x86_64-pc-windows-msvc.exe.zip`
   - archive SHA256:
     `c016b0e6968b78586919c720d2685a03712f6d5f11bcd9d6f92c91eb8c41ba16`
   - extracted executable SHA256:
     `444a3f0008050605cae73cd9b7a2dcac61294062dfaab56dd20430fd6498518b`

2. `codex-windows-sandbox-setup-x86_64-pc-windows-msvc.exe.zip`
   - archive SHA256:
     `256c4deb16946a01a52156e8fd619baec38743ff482741767ab5fdb4079e97cb`
   - extracted helper SHA256:
     `0c3eeb7cee8d2bc4c8644def3c818e8b06760979572dcedc919c38d0f38f64c4`

## 4. Staging behavior

The one-click staging utility may:

- create the fixed D2-S3 instrument root;
- download the two release ZIPs over HTTPS;
- verify archive hashes before extraction;
- extract to a temporary repository-local staging directory;
- locate exactly one expected executable from each archive;
- verify extracted hashes;
- verify the S3-I0 marker matrix;
- copy only the two verified binaries into the final package layout;
- verify final hashes after copy;
- remove only its temporary download/extraction directory;
- write a JSON staging report.

It MUST fail if the final root already exists. No automatic overwrite or rescue is allowed.

## 5. Prohibitions

The staging utility MUST NOT:

- execute `codex.exe`;
- execute the setup helper;
- invoke App Server;
- call RPC;
- create or mount VHD/VHDX;
- access model/auth state;
- modify `%LOCALAPPDATA%\Programs\OpenAI\Codex`;
- modify `%USERPROFILE%\.codex\packages`;
- authorize `turn/start`;
- authorize or consume a scientific attempt.

## 6. Required staging report

`g2e/.local/P5A-D2S3-INSTRUMENT/report/P5A_D2S3_INSTRUMENT_STAGING_REPORT.json`

Required fields include:

- schema;
- source release tag/commit;
- archive hashes;
- extracted hashes;
- final hashes;
- marker matrix;
- final relative layout;
- `global_install_modified=false`;
- `executables_invoked=false`;
- `turn_start_request_sent=false`;
- `scientific_attempt_consumed=false`;
- status.

PASS verdict:

`STAGING_PASS_PLATFORM_PREFLIGHT_GATE_REQUIRED`

## 7. Qualification

Before local execution, CI must prove:

1. parser/static tests PASS;
2. script uses the exact frozen URLs/hashes;
3. global installation paths are absent from mutation operations;
4. no executable/process launch surface exists;
5. temporary cleanup is limited to the staging utility's own temp root;
6. actual end-to-end staging succeeds on a Windows GitHub runner using the official release assets;
7. final layout/hash/marker report matches this contract;
8. P1/P1.4/P1.5/P2/P3/P4 regressions PASS.

A qualification PASS authorizes exactly one local instrument staging execution.

It does not authorize platform preflight or science.
