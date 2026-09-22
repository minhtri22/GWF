# G2E P5A D2-S2 A2 — Config Serialization Preturn Amendment

## Status

SPEC-LOCKED / ZERO-SCIENCE / PRETURN-INFRASTRUCTURE-ONLY

Baseline:

- branch: `feature/g2e-framework`
- exact baseline HEAD: `914881a4340eb4728bd31598027e842c40c72888`
- A1 blocker report SHA256:
  `eb7773a0f813a93a0c251e1f7807a540e7c2487101b6f711b2fe3d666034ce2b`
- scientific attempt remains NOT AUTHORIZED and NOT CONSUMED.

## 1. Scientific identities unchanged

- study: `p5a-d2s2-isolated-volume-root-read-successor`
- attempt: `p5a-d2s2-p5-fx-001-attempt-001`
- profile: `g2e_p5a_d2s2`

Frozen input/task/Codex hashes remain unchanged.

## 2. Fresh A2 local root

A2 MUST use:

`g2e/.local/P5A-D2S2-A2/`

A1 and predecessor local roots are historical evidence and MUST NOT be deleted, reused, renamed, or
modified by A2.

## 3. Only authorized mechanism repair

A2 may replace the overload-sensitive config newline expression with a deterministic string-level
normalizer:

- CRLF -> LF;
- no `System.Char` overload;
- UTF-8 without BOM;
- exactly one final LF appended by the same frozen materializer behavior.

No other config semantic field may change.

## 4. Windows PowerShell 5.1 qualification requirement

A2 MUST include a bounded config-serialization self-test callable without elevation or disk operations.

Qualification MUST execute that self-test on a GitHub `windows-latest` runner using Windows PowerShell,
and prove:

- CRLF input normalizes to LF;
- no CR remains;
- the self-test exits zero;
- no Codex/App Server/VHD/scientific operation is touched.

Ubuntu static/parser qualification alone is insufficient for A2.

## 5. NTFS and authority policy unchanged

The A1 closed-set root policy is preserved exactly:

Task payload:
- `TASK.md`
- `input.json`

Optional filesystem-support metadata:
- `System Volume Information` directory only

Any other root entry blocks.

Authority remains:

- `:root = read` on the dedicated A2 VHDX only;
- exact `result.json` write;
- network disabled.

## 6. No-turn firewall

A2 may proceed only through `thread/start`, then STOP.

The A2 preflight and one-click wrapper MUST NOT contain `"turn/start"`.

## 7. Qualification

PASS requires:

1. bounded A2 diff;
2. Python compile;
3. PowerShell parser PASS;
4. A2 unit qualification PASS;
5. Windows PowerShell config-serialization runtime self-test PASS;
6. P1/P1.4/P1.5/P2/P3/P4 regressions PASS;
7. no-turn proof PASS;
8. predecessor and A1 packages immutable;
9. exact blobs/artifact locked before local execution.

A PASS authorizes exactly one fresh local A2 no-turn preturn execution.
