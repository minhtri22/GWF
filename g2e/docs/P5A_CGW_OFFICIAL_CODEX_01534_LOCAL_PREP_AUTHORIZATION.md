# P5A-CGW FX001 — Local official Codex 0.153.4 preparation authorization

The official Windows x86_64 package coherence gate passed on GitHub Actions.

Local preparation is now authorized under these limits:

- create only `g2e/.local/codex-official-0.153.4`;
- download only the frozen official `rust-v0.153.4` package;
- verify archive, Codex and helper SHA-256 values;
- run only `codex --version` from the extracted package;
- produce `QUALIFICATION_REPORT.json`.

Still prohibited:

- no live P5A-CGW dispatch;
- no Windows sandbox setup;
- no model turn;
- no browser/MCP activity;
- no deletion of the existing failed-run LocalRoot;
- no mutation of the global Codex installation;
- no attempt rearm.

After the local qualification report matches the authoritative package identities, a successor execution lock may bind the same unconsumed attempt to the project-local Codex binary.
