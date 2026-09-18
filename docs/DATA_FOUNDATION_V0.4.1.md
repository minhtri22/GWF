# Development Data Foundation v0.4.1

## Purpose

The runtime needed repeatable research inputs before production-platform work. The data foundation intentionally combines two categories:

1. **Pinned public datasets** to exercise the workflow on non-generated observations.
2. **Deterministic synthetic fixtures** to force known PASS, scientific FAIL, PIVOT, leakage, confounding, missingness, and schema-drift paths.

The goal is controlled development evidence, not a claim of external product validation.

## Public dataset snapshots

Three small tabular datasets are pinned locally so the test suite does not depend on live network access:

| ID | Rows | Use in benchmark | Upstream provenance |
|---|---:|---|---|
| `uci_iris` | 150 | group difference on petal length | UCI Iris, DOI `10.24432/C56C76` |
| `uci_wine` | 178 | group difference on alcohol | UCI Wine, DOI `10.24432/C5PC7J` |
| `uci_breast_cancer` | 569 | malignant/benign mean-radius difference | UCI Breast Cancer Wisconsin (Diagnostic), DOI `10.24432/C5DW2B` |

The packaged CSVs were exported from the scikit-learn bundled copies because the QA container had no outbound DNS. `datasets/registry.json` records UCI as the provenance authority, source identifiers, license metadata, row/column counts, and SHA-256 for the pinned snapshot.

## Synthetic fault fixtures

All synthetic data use seed `170917` and are hash-pinned.

| Fixture | Intended behavior |
|---|---|
| `synth_clear_effect` | scientific PASS |
| `synth_null_effect` | legitimate scientific FAIL |
| `synth_underpowered` | insufficient sample → PIVOT |
| `synth_underpowered_augmented` | predeclared post-pivot recovery sample → PASS |
| `synth_leakage` | detect exact target leakage |
| `synth_confounded` | detect an apparent effect induced by confound imbalance |
| `synth_missingness` | detect excessive target missingness |
| `synth_schema_drift_v1/v2` | detect schema contract drift |

Synthetic fixtures are intentionally simple. Their value is that the expected failure location and recovery decision are known before the runtime sees the data.

## Research reliability benchmark

`benchmarks/research_reliability.yaml` defines six end-to-end research cases and four quality cases.

Expected terminal research outcomes:

- Iris: PASS
- Wine: PASS
- Breast Cancer Wisconsin (Diagnostic): PASS
- synthetic clear effect: PASS
- synthetic null effect: FAIL
- synthetic underpowered: one PIVOT then PASS

The quality cases require detection of `TARGET_LEAKAGE`, `HIGH_TARGET_MISSINGNESS`, `CRITICAL_CONFOUND`, and `SCHEMA_DRIFT`.

## Reproducibility rules

Every dataset is resolved through `DatasetRegistry`, which validates the registered SHA-256 before use. Research verification runs bind the input hash to the statistical result. A changed dataset is therefore a changed experimental input rather than a transparent replacement.

## Limitations

This suite is a development benchmark. The public datasets are small, well-known tabular datasets and the synthetic fixtures have intentionally controlled structure. Passing the suite demonstrates orchestration, data-integrity, quality-gate, PASS/FAIL/PIVOT, checkpoint and recovery behavior; it does not establish general scientific validity across arbitrary domains or prove market/product fit.
