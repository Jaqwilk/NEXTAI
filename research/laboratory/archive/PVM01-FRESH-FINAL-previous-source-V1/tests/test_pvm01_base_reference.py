import copy
import importlib.util
import json
from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.benchmarks import paired_view_mutable_memory_v10 as suite
from nextai_autoresearch.research_program import _study_scope, verify_pvm01_fresh_realization
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import sha256_file

ROOT = Path(__file__).resolve().parents[1]
STUDY = json.loads((ROOT/'research/plans/PVM01-BASE-REFERENCE-CONFIRMATION-V1.json').read_text(encoding='utf-8'))
CONTROLS = ['ridge', 'ridge32', 'ridge_pca_scan', 'ridge_pca_tree', 'kernel']


def analyzer(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT/'scripts'))
    spec = importlib.util.spec_from_file_location('base_reference_fixture', ROOT/'scripts/analyze_pvm01_base_reference.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def saved_units():
    arms = {}
    costs = {'dense': 10., 'dense_cached_cpu': 10., 'dense_cached_cuda': 10.,
             'ridge_pca_scan': 2., 'transport_pca': 4., 'ridge': 3., 'ridge32': 3.,
             'ridge_pca_tree': 3., 'kernel': 3.}
    for arm, cost in costs.items():
        state = 64 if arm == 'ridge_pca_scan' else 128 if arm == 'transport_pca' else 256
        unit = {'accuracy': 1., 'unknown': 1., 'false_abstention': 0.,
                'full_workload_seconds': cost, 'p95_us': cost, 'state_bytes': state}
        unit['by_K'] = {str(k): copy.deepcopy(unit) for k in (32, 128, 512)}
        arms[arm] = {noise: {str(i): copy.deepcopy(unit) for i in range(5)} for noise in ('0.02', '0.04')}
    return {'valid_comparison': True, 'arms': arms,
            'primary_gates': {**{str(i): True for i in range(8)}, 'all_eight_endpoints': True},
            'reference_selection': {'adequate_for_prospective_selection': False,
                                    'primary_gates': {'0.04:false_abstention': False}}}


def test_distinct_question_keeps_failed_mixed_assay_separate_and_retains_classical_dominators(monkeypatch):
    module = analyzer(monkeypatch)
    value = saved_units(); before = copy.deepcopy(value)
    reference, routes, decision = module.qualification(value, STUDY, CONTROLS)
    assert value == before
    assert reference['adequate_for_economic_comparison']
    assert decision['selected_route_independently_confirmed']
    assert routes['ridge_pca_scan']['reference'] == 'dense_cached_cpu'
    assert len(routes['ridge_pca_scan']['economic_gates']) == 18
    assert len(routes['ridge_pca_scan']['matched_quality_intervals']) == 30
    assert 'ridge_pca_scan' in routes['transport_pca']['matched_quality_dominators']
    assert not decision['neural_route_independently_confirmed']
    assert not decision['mixed_assay_used_as_gate'] and not decision['base_vs_itself_assay_used']
    assert decision['no_promotion'] and decision['selection_outcomes_excluded_from_intervals']


@pytest.mark.parametrize('change', ['invalid', 'mean_accuracy', 'unit_accuracy', 'unknown', 'base_unit_FA', 'missing_unit', 'missing_variant', 'learning', 'missing_learning', 'economic_quality', 'economic_cost', 'economic_unknown'])
def test_reference_learning_quality_absence_and_fullcost_failures_cannot_silently_qualify(monkeypatch, change):
    value = saved_units()
    if change == 'invalid': value['valid_comparison'] = False
    elif change == 'learning': value['primary_gates']['0'] = False
    elif change == 'missing_learning': value['primary_gates'] = {}
    elif change == 'missing_variant': del value['arms']['dense_cached_cuda']
    elif change == 'missing_unit': del value['arms']['dense_cached_cpu']['0.04']['4']
    elif change == 'base_unit_FA': value['arms']['dense_cached_cpu']['0.04']['4']['false_abstention'] = .021
    elif change in ('mean_accuracy', 'unit_accuracy', 'unknown'):
        metric = 'unknown' if change == 'unknown' else 'accuracy'
        indices = range(5) if change == 'mean_accuracy' else [0]
        for index in indices: value['arms']['dense_cached_cpu']['0.04'][str(index)][metric] = .8
    else:
        metric = {'economic_quality': 'accuracy', 'economic_cost': 'full_workload_seconds', 'economic_unknown': 'unknown'}[change]
        for unit in value['arms']['ridge_pca_scan']['0.04'].values():
            for row in unit['by_K'].values(): row[metric] = 20. if change == 'economic_cost' else .8
    reference, routes, decision = analyzer(monkeypatch).qualification(value, STUDY, CONTROLS)
    assert not routes['ridge_pca_scan']['screen_qualified']
    assert not decision['selected_route_independently_confirmed']
    if change in ('invalid', 'mean_accuracy', 'unit_accuracy', 'unknown', 'base_unit_FA', 'missing_unit', 'missing_variant'):
        assert decision['decision'] == 'INCONCLUSIVE base-reference comparison'


def test_new_cohort_is_exact_delegation_with_all_sinks_and_an_untouched_plan(monkeypatch):
    called = []; monkeypatch.setattr(suite.selected, 'run_suite', lambda *args: called.append(args) or 'PASS')
    plan = {'benchmark': suite.BENCHMARK_VERSION, 'matrix': {'sentinel': [1]}}
    before = copy.deepcopy(plan); sinks = [object() for _ in range(4)]
    assert suite.run_suite('candidate', plan, *sinks) == 'PASS' and plan == before
    assert called == [('candidate', {**plan, 'benchmark': suite.selected.BENCHMARK_VERSION}, *sinks)]
    with pytest.raises(ValueError): suite.run_suite('candidate', {'benchmark': suite.selected.BENCHMARK_VERSION}, *sinks)


@pytest.mark.parametrize('change', ['valid', 'missing_resource', 'wrong_resource', 'old_path', 'old_hash', 'old_pair', 'legacy_resource'])
def test_exact_v10_contract_does_not_widen_any_historical_cohort(change):
    plan = json.loads((ROOT/'research/plans/EXP-20261005-0004.json').read_text(encoding='utf-8'))
    validate_document('experiment_plan', plan, ROOT); old = copy.deepcopy(plan['research_program_protocol'])
    plan['benchmark'] = STUDY['cohort']; plan['research_program_protocol'].update(_study_scope(STUDY))
    if change == 'missing_resource': del plan['research_program_protocol']['resource_measurement_version']
    elif change == 'wrong_resource': plan['research_program_protocol']['resource_measurement_version'] = 'unchecked'
    elif change == 'legacy_resource':
        plan['benchmark'] = 'paired_view_mutable_memory_v8'
        plan['research_program_protocol'] = copy.deepcopy(old)
        for key in ('classical_economic_contract_path', 'classical_economic_contract_sha256'): del plan['research_program_protocol'][key]
    elif change.startswith('old_'):
        for key in ('classical_economic_contract_path', 'classical_economic_contract_sha256'):
            if change == 'old_pair' or change == 'old_path' and key.endswith('path') or change == 'old_hash' and key.endswith('sha256'):
                plan['research_program_protocol'][key] = old[key]
    if change == 'valid': validate_document('experiment_plan', plan, ROOT)
    else:
        with pytest.raises(ValidationError): validate_document('experiment_plan', plan, ROOT)


@pytest.mark.parametrize('change', ['valid', 'seed', 'nonce', 'tamper', 'missing', 'scope'])
def test_all_confirmation_units_are_checked_before_new_arrays(tmp_path, change):
    identities = [f'EXP-20261004-{i:04d}' for i in range(4, 9)] + [f'EXP-20261005-{i:04d}' for i in range(1, 5)]
    paths = {}
    for i, identity in enumerate(identities):
        directory = tmp_path/f'research/laboratory/archive/{identity}-runtime'
        if identity != 'EXP-20261004-0005': directory /= f'research/tmp/{identity}'
        directory.mkdir(parents=True); private = directory/'pvm01-private-data.json'
        private.write_text(json.dumps({'experiment_id': identity, 'unit_nonces': [f'{1000+i:064x}']}), encoding='utf-8')
        (directory/'runtime-plan.json').write_text(json.dumps({'experiment_id': identity, 'matrix': {'seeds': [1000+i]}, 'pvm01_private_data_sha256': sha256_file(private)}), encoding='utf-8')
        paths[identity] = directory
    seeds = list(range(9000, 9005)); nonces = [f'{i:064x}' for i in seeds]
    latest = paths[identities[-1]]/'pvm01-private-data.json'
    if change == 'seed': seeds[0] = 1008
    elif change == 'nonce': nonces[0] = f'{1008:064x}'
    elif change == 'tamper': latest.write_bytes(latest.read_bytes()+b' ')
    elif change == 'missing': latest.unlink()
    kwargs = {'include_latest': True, 'include_transport': True, 'include_replication': True,
              'include_dense_noise': change != 'scope', 'include_confirmation': True}
    if change == 'valid': verify_pvm01_fresh_realization(tmp_path, seeds, nonces, **kwargs)
    else:
        with pytest.raises((ValueError, FileNotFoundError)): verify_pvm01_fresh_realization(tmp_path, seeds, nonces, **kwargs)


def test_all_scientific_work_and_thresholds_preserved_with_a_distinct_prospective_reference():
    parent = json.loads((ROOT/STUDY['parent_evidence']['parent_study_path']).read_text(encoding='utf-8'))
    for key in ('candidates', 'roles', 'recipe', 'matrix', 'diagnosis_gates', 'reference_gates', 'dense_noise_reference_gates', 'economic_gates', 'economic_measurement', 'selected_classical_route_confirmation'):
        assert STUDY[key] == parent[key], key
    assert {k:v for k,v in STUDY['data'].items() if k != 'tag'} == {k:v for k,v in parent['data'].items() if k != 'tag'}
    assert all(sha256_file(ROOT/path) == digest for path,digest in STUDY['parent_evidence']['scientific_source_sha256_unchanged'].items())
    assert len(STUDY['candidates']) == 85 and len(STUDY['parent_evidence']['scientific_source_sha256_unchanged']) == 107
    new = copy.deepcopy(STUDY['unaugmented_reference_confirmation']); new['competent_reference'] = 'dense_cached_cpu_mixed'
    assert new == parent['selected_classical_route_confirmation']
    assert STUDY['resources']['fit_seconds_study_cap'] + STUDY['resources']['auxiliary_test_seconds_cap'] == 13800
    assert STUDY['programme_reserves']['fresh_final_and_replication_min_seconds_unspent_after_worst_case_this_study'] == 24000
@pytest.mark.parametrize('change', ['valid', 'hash', 'different_record', 'wrong_directory', 'missing', 'partial'])
def test_saved_trusted_resource_binding_is_verified_before_qualification(tmp_path, monkeypatch, change):
    module = analyzer(monkeypatch)
    identity = 'EXP-resource-fixture'
    path = tmp_path/f'research/tmp/{identity}/worker.resources.json'
    path.parent.mkdir(parents=True)
    record = {'schema_version': 1, 'version': 'cumulative_cuda_phase_peaks_v1', 'timed_service_modified': False,
              'snapshots': [{'phase': phase, 'cuda_available': False, 'cuda_peak_allocated_bytes': 0,
                             'cuda_peak_reserved_bytes': 0, 'process_rss_bytes': 1000}
                            for phase in ('initializing', 'fit', 'evaluation', 'complete')]}
    if change == 'partial': record['snapshots'].pop()
    path.write_text(json.dumps(record), encoding='utf-8')
    execution = {'resource_peaks_path': path.relative_to(tmp_path).as_posix(), 'resource_peaks_sha256': sha256_file(path),
                 'resource_peaks': copy.deepcopy(record)}
    if change == 'hash': execution['resource_peaks_sha256'] = '0'*64
    elif change == 'different_record': execution['resource_peaks']['snapshots'][-1]['process_rss_bytes'] = 2000
    elif change == 'wrong_directory': execution['resource_peaks_path'] = 'research/tmp/elsewhere/worker.resources.json'
    elif change == 'missing': path.unlink()
    value = module.trusted_resource_checks(tmp_path, identity, [{'candidate': 'worker', 'execution': execution}],
                                          {'max_cuda_reserved_bytes': 2**32})
    assert value == {'worker': change == 'valid'}