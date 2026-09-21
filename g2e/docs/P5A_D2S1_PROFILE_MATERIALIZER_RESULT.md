# G2E P5A D2-S1 — Profile Materializer Implementation Result

**Status:** `IMPLEMENTATION_PASS_LOCAL_PREFLIGHT_REQUIRED`  
**Qualified candidate:** `71671f66bcb3618b5960f702643441167a5ae32d`  
**Baseline:** `dfc8e438b8b4d91582a97809bc402862a07d29f7`  
**Workflow run:** `35630639385`  
**Workflow job:** `106435710956`  
**Artifact:** `10653818548`  
**Artifact digest:** `sha256:6d9f781026070a194518fd9909ebc21498b6dd20d74a69109c34de275b9c1f7a`

## Qualified identities

```text
study_id
p5a-d2s1-permission-profile-successor

attempt_id
p5a-d2s1-p5-fx-001-attempt-001

permission_profile_id
g2e_p5a_d2s1
```

Exact implementation blobs:

```text
spec
7764ede707b632a18346a650adeb4d1fb23f7f54

zero-fresh QA
31ae7e0a5355e53e6da01cfc7818a8758be57384

materializer
708f1289031c87e681149329e610056f38268327

tests
47f3ef7088201c162fae298f71df1f3ee68679da

workflow
15bdf1e725ab7554d364c5321b83ebff865db16d
```

Canonical materialization identities:

```text
config.toml sha256
449bb9238cb2e3760a4fc16d417ea88e2773e98421bac756f383b8e07ed203fc

P5A_D2S1_PROFILE_MATERIALIZATION.json sha256
32366aaf4d47101730c5a5021bb7c7a5c08a387354019cbb19ddbefbd77eae74

execution_config_hash
08aba89c742da6a6fa08203e9ff4b5542685c05e9a4215673bc509af72af1811
```

## Qualification

The exact-SHA workflow passed:

- bounded-diff enforcement;
- Python compilation;
- P1 regression;
- P1.4 regression;
- P1.5 regression;
- P2 regression;
- P3 regression;
- P4 regression;
- D2-S1 deterministic profile-materializer tests;
- canonical profile-pack materialization;
- independent re-verification;
- artifact publication.

The materializer freezes:

- exact Codex 0.153.4 harness/source/schema identities;
- `experimentalApi=true`;
- named permission profile `g2e_p5a_d2s1`;
- exact read paths for `input.json` and `TASK.md`;
- exact write path for `result.json`;
- network disabled;
- no legacy `sandbox` or `sandboxPolicy` request;
- thread-level named permission selection;
- turn-level inheritance of that already-attested profile;
- zero replacement attempts.

## Authorization state

This result authorizes only the already-preregistered **local no-turn profile-selection preflight**.

It does not authorize a D2-S1 scientific model turn.

Current state:

```text
model_turn_executed          false
fresh_outcome_consumed       false
scientific_attempt_authorized false
runtime_adapter_authorized   false
```

The next required gate is a local preturn qualification on the exact Windows/Codex 0.153.4 environment proving that the custom profile is listed as allowed and accepted by `thread/start` with no model turn.
