# G2E P5A.1R — Codex D1 Inventory Ordering Invalidity Repair

**Status:** FROZEN INVALIDITY-REPAIR CANDIDATE  
**Parent lock:** P5A.1 D1 Adjudication Lock  
**Parent qualified adjudicator:** `685739bf607ed456ace1bf723a352ab72a5237d3`  
**Parent adjudicator blob:** `85cc857593a154109cdf5ed749c73f0a2b1e4adb`  
**Original discovery input SHA-256:** `ba098a56be39e996488e5a543af8c373199f8b4cc66f922be6d7bc6386c6e860`  
**Original adjudication:** `INVALID` / `INVENTORY_PATHS_NOT_SORTED`  
**Fresh Codex recollection:** PROHIBITED

## 1. Invalidity mechanism

The first frozen D1 collection reported:

- discovery status `D1_MINIMUM_QUALIFIED`;
- no discovery errors;
- initialize handshake success;
- all six required protocol tokens true;
- deterministic schema-inventory digest `4da66f2fac241c53ec857bf1a5f0f9586a445e39c4b0c4e7b4bdb0b103aa8376`.

The frozen adjudicator nevertheless returned only:

`INVENTORY_PATHS_NOT_SORTED`.

The mechanism is platform-order semantics, not Codex scientific capability:

1. the qualified discovery probe sorts `Path` objects on the collection host;
2. on Windows, `WindowsPath` ordering is case-insensitive / Windows-normalized;
3. the frozen adjudicator validated the emitted string paths with host-independent `sorted(str)` semantics, which are case-sensitive;
4. the observed inventory contains lowercase `codex_app_server_protocol...` entries before uppercase `Command...` entries, which is valid WindowsPath ordering but not Python string ASCII ordering on the adjudication host.

Therefore the INVALID result is attributable to a cross-platform validator mismatch between two already-frozen instruments.

## 2. Scientific non-rescue statement

This repair does **not**:

- change any required protocol token;
- change any D1 PASS capability requirement;
- reinterpret missing evidence as present;
- change executable/version identity;
- change initialize-handshake requirements;
- change schema-generation requirements;
- change secret/sanitization requirements;
- change the schema-inventory digest algorithm;
- regenerate or recollect Codex evidence;
- switch Codex version;
- modify the discovery probe;
- touch D2 or runtime-adapter authorization.

The original discovery JSON remains the only D1 collection input.

## 3. Repair rule

Inventory-order validation must mirror the ordering semantics of the qualified probe on the platform recorded in the discovery bundle.

For `platform.system == Windows`:

- expected order is `PureWindowsPath` ordering over each relative path.

For non-Windows platforms:

- expected order is `PurePosixPath` ordering over each relative path.

The inventory entries themselves and their order remain part of the signed/fingerprinted discovery evidence. The repair only determines whether that observed order is the deterministic order produced by the qualified probe's host path semantics.

## 4. Digest invariance

The inventory digest remains exactly:

`SHA256(canonical_json(generated_schema_files in observed order))`.

No sorting is performed during digest recomputation.

A repaired order check may never make a digest mismatch pass.

## 5. Re-adjudication rule

After this repair is independently qualified on an exact SHA:

1. do not rerun the discovery probe;
2. use the original discovery input with SHA-256 `ba098a56be39e996488e5a543af8c373199f8b4cc66f922be6d7bc6386c6e860`;
3. run the repaired adjudicator exactly once;
4. retain both the original INVALID adjudication and the repaired adjudication;
5. the repaired verdict is valid only for this identified invalidity mechanism.

If any new reason code appears, do not repair further without a new explicit lineage.

## 6. Qualification fixtures

The repair QA must demonstrate:

- Windows probe order with lowercase `codex...` before uppercase `Command...` is accepted when `platform.system=Windows`;
- that same order is rejected when `platform.system=Linux`;
- unsorted Windows order is still rejected;
- duplicate paths are still rejected;
- digest mismatch is still INVALID;
- required-token contradiction is still INVALID;
- secret/account-field detection is unchanged;
- recognized discovery FAIL states remain FAIL;
- no process/Codex/G2E runtime execution path is added.

## 7. Exit gate

```text
P5A.1R spec frozen
        ↓
bounded adjudicator-only patch
        ↓
P1/P1.4/P2/P3/P4/P5A/P5A.1 regressions
        ↓
repair-specific cross-platform ordering tests
        ↓
exact-SHA PASS
        ↓
re-adjudicate original immutable D1 discovery once
```

Only after the repaired re-adjudication may P5A D1 be adjudicated PASS/FAIL/INVALID.
