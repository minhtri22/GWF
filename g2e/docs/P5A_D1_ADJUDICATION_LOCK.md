# G2E P5A.1 — Codex D1 Actual-Harness Adjudication Lock

**Status:** FROZEN CANDIDATE FOR ZERO-FRESH QA  
**Baseline:** `dea34428cb644a221d34a143a738c35b196d3f05`  
**Fresh actual-harness evidence consumed:** NONE  
**Codex runtime adapter:** NOT AUTHORIZED

## 1. Purpose

P5A discovery preparation is already qualified as `PREPARATION_PASS_ACTUAL_HARNESS_PENDING`.

Before any target-machine `P5A_CODEX_DISCOVERY.json` is examined, this document freezes the one-shot D1 adjudication rule. The purpose is to prevent outcome-conditioned rescue, threshold changes, or selective interpretation after actual harness evidence exists.

## 2. Input contract

The sole scientific input is one JSON document emitted by the already-qualified probe:

`scripts/g2e/p5a_codex_discovery.py`

qualified blob:

`5861298808bd4cc91845f1c10ae114709a955e88`

Expected input schema identifier:

`G2E-P5A-CODEX-DISCOVERY-v1`

The adjudicator MUST NOT execute Codex, regenerate schema, access the network, inspect repository contents, or repair the discovery bundle.

## 3. D1 PASS rule

D1 is PASS if and only if all conditions below are true:

1. `schema == G2E-P5A-CODEX-DISCOVERY-v1`;
2. `status == D1_MINIMUM_QUALIFIED`;
3. `secrets_persisted == false`;
4. `functional_task_executed == false`;
5. `codex_version_stdout` is a non-empty string;
6. `executable_path` is a non-empty string;
7. executable identity is represented by either a 64-hex `executable_sha256` or a non-empty explicit `executable_sha256_unavailable_reason`;
8. `app_server_help_exit_code == 0`;
9. `app_server_help_sha256` is 64-hex;
10. `schema_generation_exit_code == 0`;
11. `generated_schema_files` is a non-empty, path-sorted list with unique relative paths, 64-hex hashes, and non-negative sizes;
12. `schema_inventory_digest` equals SHA-256 of the canonical sorted inventory exactly as defined by the qualified probe;
13. every frozen required protocol token is present and true:
    - `initialize`
    - `thread/start`
    - `thread/resume`
    - `turn/start`
    - `item/started`
    - `item/completed`
14. `initialize_handshake.success == true`;
15. sanitized initialize response contains no fields outside `response_id`, `result_present`, and optional `metadata`; metadata contains no fields outside `userAgent`, `platformFamily`, `platformOs`;
16. `errors` is empty.

No optional token is required for minimum D1 PASS.

## 4. D1 FAIL rule

D1 is FAIL when the bundle is structurally valid and attributable to the qualified probe schema but one or more scientific D1 requirements are false, including:

- status is a recognized non-pass discovery state such as `HARNESS_NOT_FOUND`, `VERSION_UNRESOLVED`, `SCHEMA_DISCOVERY_FAILED`, or `D1_MINIMUM_NOT_QUALIFIED`;
- a required protocol token is false;
- initialize handshake failed;
- help/schema generation did not succeed;
- required exact identity field is absent despite otherwise parseable evidence.

FAIL is an actual result. It MUST NOT trigger probe modification, token relaxation, or documentation-based rescue within the same D1 lineage.

## 5. INVALID rule

D1 is INVALID when scientific interpretation is unsafe because the evidence bundle cannot be trusted as the output of the frozen probe contract, including:

- malformed JSON;
- wrong schema identifier;
- contradictory fields, for example `status=D1_MINIMUM_QUALIFIED` while a required token is false;
- duplicate or unsorted schema inventory paths;
- invalid hashes/sizes;
- schema inventory digest mismatch;
- forbidden persisted secret/account fields detected;
- `functional_task_executed` or `secrets_persisted` is not boolean false;
- adjudicator version/input fingerprint cannot be recorded.

INVALID does not imply Codex failure. A new evidence collection may be authorized only after the invalidity mechanism is identified without inspecting desired scientific outcome.

## 6. Forbidden rescue

After first target-harness evidence is produced, the following are prohibited inside this D1 lineage:

- changing required protocol tokens;
- changing PASS/FAIL/INVALID rules;
- treating D0 documentation as substitute evidence;
- selecting a different Codex version because the first version failed;
- rerunning until PASS without a separately justified invalidity reason;
- using ChatGPT capability as corroboration;
- opening D2 or runtime adapter after FAIL/INVALID.

## 7. One-shot adjudicator output

The adjudicator emits a separate JSON result with:

- adjudicator schema/version;
- adjudicator source fingerprint when run from git;
- discovery input SHA-256;
- verdict: `PASS | FAIL | INVALID`;
- reason codes;
- observed Codex version;
- observed executable path/hash status;
- schema inventory digest;
- required token map;
- initialize handshake result;
- `codex_profile_available_for_d1_surface` boolean;
- `d2_authorized` fixed false;
- `runtime_adapter_authorized` fixed false.

Even D1 PASS qualifies only the observed structural surface. It does not qualify task execution.

## 8. Zero-fresh qualification gate

Before target-harness evidence is consumed, exact-SHA QA must prove:

```text
P5A1-Q0 P5A preparation evidence exact
P5A1-Q1 no P5A_CODEX_DISCOVERY.json in repo
P5A1-Q2 PASS/FAIL/INVALID rule frozen
P5A1-Q3 inventory digest recomputation tested
P5A1-Q4 contradiction/secret negative tests
P5A1-Q5 no Codex execution in adjudicator
P5A1-Q6 no src/g2e or src/gwr mutation
P5A1-Q7 P1/P1.4/P2/P3/P4 regressions PASS
```

Only then may the target machine run the frozen discovery probe.

## 9. Next sequence after this lock PASS

```text
P5A.1 D1 adjudication lock PASS
        ↓
ONE target-harness discovery run
        ↓
freeze P5A_CODEX_DISCOVERY.json
        ↓
run frozen one-shot adjudicator
        ↓
PASS / FAIL / INVALID
```

If PASS: construct an exact Codex AgentCapabilityManifest from D1-qualified structural capabilities only, then separately preregister D2 P5-FX-001.

If FAIL: stop P5A Codex profile advancement.

If INVALID: repair only the invalidity mechanism under a new explicit lineage before recollection.
