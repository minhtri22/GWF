# G2E P5A D2-S4 — Persisted Turn-Error Recovery

## Status

SPEC-LOCKED / POST-CLOSURE / READ-ONLY / NO SCIENTIFIC RETRY

Prerequisite:

`P5A_D2S4_POSTCLOSURE_TERMINAL_FAILURE_DECOMPOSITION_RESULT.md`

## 1. Objective

Recover already-persisted mechanism-bearing evidence for the exact D2-S4 terminal failed turn without
starting Codex or changing any scientific state.

Exact IDs:

- thread:
  `01a0c9af-d509-7203-9608-06304738b12e`
- turn:
  `01a0c9af-d523-72f3-84fa-a575e91076b6`

## 2. Allowed sources

Read-only inspection of existing local files under:

`g2e/.local/P5A-D2S4-SCIENCE-001/codex-home`

limited to:

- `sessions/**`;
- `archived_sessions/**`;
- `log/**`;
- local SQLite files, opened read-only.

## 3. Forbidden sources

MUST NOT read, copy, emit, or hash as evidence:

- `auth.json`;
- credential stores;
- tokens/API keys;
- `config.toml` contents;
- environment variables containing secrets;
- unrelated threads/sessions;
- arbitrary database rows not linked to the exact thread or turn IDs.

## 4. Required recovery behavior

The extractor MUST:

1. never start Codex/App Server;
2. never send RPC;
3. never mount VHDX;
4. never modify the Science-001 tree;
5. search text/JSONL evidence only for exact thread/turn IDs;
6. inspect SQLite only in read-only mode;
7. emit only matching records/rows;
8. redact bearer tokens, API-key-like values and obvious credential fields;
9. preserve source file path, source SHA256 and line/row provenance;
10. project mechanism-bearing fields where possible:
    - status;
    - error;
    - message;
    - codexErrorInfo;
    - additionalDetails;
    - willRetry;
    - thread/turn IDs;
    - event/method/type.

## 5. Output

Produce one bundle containing:

- deterministic manifest;
- targeted text/session matches;
- targeted SQLite matches;
- source-file hashes;
- explicit booleans showing that Codex/RPC/VHDX/retry were not used.

No successor execution is authorized by this recovery.
