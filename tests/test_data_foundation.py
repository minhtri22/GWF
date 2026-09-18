from pathlib import Path
from gwr.datasets import DatasetRegistry
from gwr.research_benchmark import ResearchBenchmarkSuite
from gwr.tabular_verifier import SubprocessTabularVerifier

ROOT=Path(__file__).resolve().parents[1]

def reg(): return DatasetRegistry(ROOT/'datasets')

def test_all_dataset_hashes_and_shapes_are_pinned():
    r=reg(); assert len(r.ids())==12
    assert all(r.validate_integrity(x)['ok'] for x in r.ids())

def test_real_datasets_have_provenance_and_licenses():
    r=reg()
    for did in ['uci_iris','uci_wine','uci_breast_cancer']:
        m=r.get(did).manifest
        assert m['license']=='CC BY 4.0'; assert m['doi']; assert m['source_url']; assert m['citation']

def test_quality_pathologies_detected_from_data():
    r=reg()
    assert 'TARGET_LEAKAGE' in r.quality_assessment('synth_leakage',target_column='target')['issues']
    assert 'HIGH_TARGET_MISSINGNESS' in r.quality_assessment('synth_missingness',target_column='value',max_target_missing=0.10)['issues']
    assert 'CRITICAL_CONFOUND' in r.quality_assessment('synth_confounded',confounder={'group':'group','value':'value','column':'confounder'})['issues']
    assert 'SCHEMA_DRIFT' in r.quality_assessment('synth_schema_drift_v2',expected_columns=['group','value','row_id'])['issues']

def test_independent_verifier_clear_effect_and_null():
    r=reg(); v=SubprocessTabularVerifier(timeout_seconds=20)
    clear=v.verify(r.load_rows('synth_clear_effect'),{'group_column':'group','value_column':'value','group_a':'A','group_b':'B','min_effect':0.7,'min_per_group':20,'alpha':0.01,'permutations':1000,'seed':170917})
    null=v.verify(r.load_rows('synth_null_effect'),{'group_column':'group','value_column':'value','group_a':'A','group_b':'B','min_effect':0.5,'min_per_group':20,'alpha':0.05,'permutations':1000,'seed':170917})
    assert clear['pass'] and clear['independent_process']; assert not null['pass']

def test_benchmark_definition_has_real_and_synthetic_cases():
    s=ResearchBenchmarkSuite(ROOT/'benchmarks'/'research_reliability.yaml')
    ids=set(s.cases)
    assert {'real_iris_petal_length','real_wine_alcohol','real_breast_radius','synth_clear_effect','synth_null_effect','synth_underpowered_pivot'} <= ids
