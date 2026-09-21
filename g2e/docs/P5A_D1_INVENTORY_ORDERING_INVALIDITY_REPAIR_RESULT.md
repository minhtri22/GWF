# G2E P5A.1R — Inventory Ordering Invalidity Repair Result

## Verdict

**PASS — BOUNDED INVALIDITY REPAIR QUALIFIED**

This result qualifies only the cross-platform inventory-order validation repair.

It does not adjudicate Codex D1, does not authorize recollection, D2, or a Codex runtime adapter.

## Original immutable evidence

- discovery SHA-256: `ba098a56be39e996488e5a543af8c373199f8b4cc66f922be6d7bc6386c6e860`
- original adjudication: `INVALID`
- original sole reason: `INVENTORY_PATHS_NOT_SORTED`

The original discovery evidence is retained unchanged and must be reused for repaired adjudication.

## Invalidity mechanism

The qualified discovery probe sorts filesystem `Path` objects on the collection host. On Windows this produces Windows path ordering semantics, while the parent adjudicator checked emitted path strings using case-sensitive host-independent `sorted(str)` semantics.

The observed Windows inventory therefore produced a deterministic valid order that the parent Linux-qualified adjudicator incorrectly classified as unsorted.

This is a validator/platform mismatch, not a Codex capability failure.

## Qualified repair candidate

- exact SHA: `4e447ef19a843aa3dd1337c57a9c70b4c1a00de1`
- repair-spec blob: `246a90d468c194ede91e7a2fb87925d971610028`
- repaired adjudicator blob: `b2ba81801d2bfe7a662acb477fa449e16d13fa55`
- repair-test blob: `e36121ef55c572acdf03e951387590706656567f`
- workflow blob: `9ed761d529c24e22ea605ba4b2c5b420ae508a2b`

## Exact qualification workflow

- workflow: `G2E P5A.1R Inventory Ordering Repair`
- run: `35597985704`
- job: `106327133946`
- conclusion: **PASS**
- artifact: `10637389197`
- artifact digest: `sha256:09a599886c44d3d3d2544d6ff61a93205f47c137d8807598caadda97ea6c2130`

The workflow passed:

1. bounded invalidity-repair diff;
2. no G2E/GWF runtime mutation;
3. no discovery-probe mutation;
4. compile;
5. P1 regression;
6. P1.4 regression;
7. P2 regression;
8. P3 regression;
9. P4 regression;
10. P5A preparation regression;
11. parent P5A.1 adjudicator regression;
12. repair-specific Windows/POSIX ordering fixtures;
13. no execution path in adjudicator;
14. machine-readable repair report.

## Repair semantics

The repaired adjudicator now validates inventory ordering using the path semantics corresponding to the recorded discovery platform:

- Windows → `PureWindowsPath` ordering;
- non-Windows → `PurePosixPath` ordering.

The repair does not alter:

- required D1 protocol tokens;
- help/schema-generation requirements;
- initialize-handshake requirements;
- executable/version identity requirements;
- secret/sanitization checks;
- inventory entry validation;
- schema-inventory digest algorithm;
- PASS/FAIL/INVALID scientific meaning;
- D2/runtime authorization.

## No-recollection boundary

Fresh Codex discovery is **NOT AUTHORIZED**.

The next admissible operation is to pull this qualified repair and run the repaired adjudicator exactly once against the original discovery JSON whose SHA-256 is:

`ba098a56be39e996488e5a543af8c373199f8b4cc66f922be6d7bc6386c6e860`

Both the original INVALID adjudication and the repaired adjudication must be retained.

## Next admissible step

```text
qualified P5A.1R repair
        ↓
NO Codex recollection
        ↓
re-adjudicate original immutable discovery once
        ↓
PASS / FAIL / INVALID
```

Only that repaired verdict may determine whether exact Codex AgentCapabilityManifest construction can open.
