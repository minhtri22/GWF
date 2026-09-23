# P5A-CGW FX001 — Launcher Identity Selection Repair

## Trigger

Read-only runtime identity decomposition established:

- registry launcher: `Codex Web GPT.exe`
  - SHA-256 `ac152ad499b1f41b2cafe94a3d05f5d4e4d3cd7ddbb417b9c60b118b08bc3cbb`
  - size `223980032`
  - file/product version `4.0.7` / `4.0.7.0`
- bridge runtime command[0]: `bun.exe`
  - SHA-256 `627d2e4775c24bdedee2cd7ccc18dcadae061e5345274ab6e3c4c797927bfb8f`
  - version `1.4.0`
- bridge config SHA-256 remains exactly
  `f8ba628c60faf5c95409ee3a37ad359f74dd0eb41bb961312b67758f9ba53858`;
- bridge health still identifies exact release `4.0.7`, Full mode, Codex Native2, idle;
- Codex binary still matches frozen SHA-256.

The frozen CGW binary identity was therefore correct. The wrapper defect was allowing a launcher-identity fallback to `runtimeCommand[0]`, then comparing Bun's hash against the frozen launcher hash.

## Repair

The functional wrapper now:

1. resolves only the installed `Codex Web GPT.exe` launcher for the frozen CGW binary identity;
2. never substitutes `runtimeCommand[0]` for launcher identity;
3. fails closed with:
   - `CGW_LAUNCHER_REGISTRY_LOOKUP_FAILED`;
   - `CGW_LAUNCHER_NOT_FOUND`;
   - `CGW_LAUNCHER_HASH_DRIFT`;
4. includes observed/expected hash and path in a hash-drift diagnostic.

The bridge runtime command remains untouched and may continue to use Bun internally.

## Scientific contract

Unchanged: attempt, route, model, mode, connector, runtime release, task, result, authority, consumption boundary, retry=0, timeout=90s, and evidence contract.

The read-only diagnostic and this repair execute no model turn and do not consume the attempt.

## Qualification

Linux and Windows zero-model QA must verify:

- no `runtimeCommand[0]` fallback exists in the functional wrapper;
- V2R3 lock guard is present;
- PowerShell 5.1 parser safety;
- all existing admission/runner/verifier and preregistration regressions remain PASS.
