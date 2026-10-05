import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.benchmarks import paired_view_mutable_memory_v11 as suite
from nextai_autoresearch.pvm01_fitted_state import export_state, load_state, restore_state
from nextai_autoresearch.research_program import _study_scope, verify_pvm01_fresh_realization
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import sha256_file, sha256_json

ROOT = Path(__file__).resolve().parents[1]
STUDY = json.loads((ROOT/'research/plans/PVM01-FRESH-FINAL-V1.json').read_text())


@pytest.mark.parametrize('change', ['valid', 'missing_role', 'wrong_role', 'legacy_role', 'old_addon', 'old_hash', 'missing_resource'])
def test_final_role_exact_schema_binding_preserves_historical_contracts(change):
    plan = json.loads((ROOT/'research/plans/EXP-20261005-0005.json').read_text())
    validate_document('experiment_plan', plan, ROOT)
    plan['benchmark'] = STUDY['cohort']
    plan['research_program_protocol'].update(_study_scope(STUDY))
    protocol = plan['research_program_protocol']
    if change == 'missing_role': del protocol['evaluation_data_role']
    elif change == 'wrong_role': protocol['evaluation_data_role'] = 'development'
    elif change == 'legacy_role':
        plan = json.loads((ROOT/'research/plans/EXP-20261005-0005.json').read_text())
        plan['research_program_protocol']['evaluation_data_role'] = 'frozen_fresh_final_v1'
    elif change == 'old_addon': protocol['classical_economic_contract_path'] = 'research/plans/PVM01-BASE-REFERENCE-CLASSICAL-ECONOMICS-V1.json'
    elif change == 'old_hash': protocol['classical_economic_contract_sha256'] = '06adddd5263f6fcc1d60df00e74b41e906909413563e1333d0fb78f4edc25ee3'
    elif change == 'missing_resource': del protocol['resource_measurement_version']
    if change == 'valid': validate_document('experiment_plan', plan, ROOT)
    else:
        with pytest.raises(ValidationError): validate_document('experiment_plan', plan, ROOT)


@pytest.mark.parametrize('change', ['valid', 'seed', 'nonce', 'tamper', 'missing', 'scope'])
def test_last_base_reference_units_are_included_before_final_arrays(tmp_path, change):
    ids = [f'EXP-20261004-{i:04d}' for i in range(4, 9)] + [f'EXP-20261005-{i:04d}' for i in range(1, 6)]
    for index, identity in enumerate(ids):
        directory = tmp_path/f'research/laboratory/archive/{identity}-runtime'
        if identity != 'EXP-20261004-0005': directory /= f'research/tmp/{identity}'
        directory.mkdir(parents=True)
        private = directory/'pvm01-private-data.json'
        private.write_text(json.dumps({'experiment_id': identity, 'unit_nonces': [f'{1000+index:064x}']}))
        (directory/'runtime-plan.json').write_text(json.dumps({'experiment_id': identity, 'matrix': {'seeds': [1000+index]}, 'pvm01_private_data_sha256': sha256_file(private)}))
    seeds = list(range(9000, 9005)); nonces = [f'{i:064x}' for i in seeds]
    if change == 'seed': seeds[0] = 1009
    elif change == 'nonce': nonces[0] = f'{1009:064x}'
    elif change == 'tamper': private.write_bytes(private.read_bytes()+b' ')
    elif change == 'missing': private.unlink()
    options = dict(include_latest=True, include_transport=True, include_replication=True,
                   include_dense_noise=True, include_confirmation=change != 'scope', include_base_reference=True)
    if change == 'valid': verify_pvm01_fresh_realization(tmp_path, seeds, nonces, **options)
    else:
        with pytest.raises((ValueError, FileNotFoundError)): verify_pvm01_fresh_realization(tmp_path, seeds, nonces, **options)


def fixture_system(arm='transport_pca'):
    model = torch.nn.Linear(2, 2)
    with torch.no_grad():
        model.weight.fill_(.25); model.bias.fill_(.125)
    return SimpleNamespace(model=model, decoder=None, weights=None,
        projection=np.eye(2, dtype=np.float32), seed=7, arm=arm,
        recipe={'public_fixture': True}, threshold=.85, device=torch.device('cpu'))


def fixture_record(system):
    digest = hashlib.sha256()
    for value in system.model.state_dict().values(): digest.update(value.detach().numpy().tobytes())
    report = {'arm': system.arm, 'seed': 7, 'seed_index': 0,
        'final_encoder_sha256': digest.hexdigest(), 'final_decoder_sha256': None,
        'pca_projection_sha256': hashlib.sha256(system.projection.tobytes()).hexdigest(),
        'calibration_choice': {'threshold': .85}}
    return {'candidate': f'pvm01_tc_{system.arm}_s0', 'seed': 7,
            'fit_report': report, 'fit_report_sha256': sha256_json(report)}


def fixture_protocol(system):
    return {'recipe': system.recipe, 'study_path': 'research/plans/public-fixture.json',
            'study_sha256': 'a'*64}


def test_parameter_copy_roundtrip_preserves_answers_hashes_rng_and_no_fit(tmp_path):
    system = fixture_system(); record = fixture_record(system); before = copy.deepcopy(record)
    torch_state, numpy_state = torch.random.get_rng_state(), np.random.get_state()
    descriptor = export_state(system, tmp_path/'state', record, fixture_protocol(system), record['candidate'], system.arm, 0)
    assert torch.equal(torch_state, torch.random.get_rng_state())
    assert np.array_equal(numpy_state[1], np.random.get_state()[1]) and record == before
    metadata, arrays = load_state(tmp_path/'state')
    restored = fixture_system()
    with torch.no_grad(): restored.model.weight.fill_(0)
    restore_state(restored, metadata, arrays)
    query = torch.tensor([.5, .25])
    assert torch.equal(restored.model(query), system.model(query))
    assert np.array_equal(restored.projection, system.projection) and restored.threshold == system.threshold
    assert descriptor['all_cost_in_fit_phase'] and descriptor['total_bytes'] < 65536
    assert not metadata['training_or_final_arrays_included']
    assert set(arrays) == {'model.weight', 'model.bias', 'projection'}
    with pytest.raises(FileExistsError): export_state(system, tmp_path/'state', record, fixture_protocol(system), record['candidate'], system.arm, 0)


@pytest.mark.parametrize('change', ['parameter_hash', 'report_hash', 'threshold', 'nonfinite', 'float64', 'wrong_role', 'oversize'])
def test_bad_source_state_cannot_be_exported_or_laundered(tmp_path, change):
    system = fixture_system(); record = fixture_record(system)
    if change == 'parameter_hash': system.model.weight.data.fill_(.9)
    elif change == 'report_hash': record['fit_report_sha256'] = '0'*64
    elif change == 'threshold': system.threshold = .5
    elif change == 'nonfinite': system.projection[0, 0] = np.nan
    elif change == 'float64': system.projection = system.projection.astype(np.float64)
    elif change == 'wrong_role': record['candidate'] = 'pvm01_tc_transport_pca_s1'
    elif change == 'oversize': system.projection = np.zeros((1024, 1024), dtype=np.float32)
    with pytest.raises(ValueError): export_state(system, tmp_path/'state', record, fixture_protocol(system), record['candidate'], system.arm, 0)
    assert not (tmp_path/'state').exists()


@pytest.mark.parametrize('change', ['file', 'array_hash', 'extra_key', 'recipe'])
def test_tampered_state_is_rejected_without_optimization(tmp_path, change):
    system = fixture_system(); record = fixture_record(system)
    export_state(system, tmp_path/'state', record, fixture_protocol(system), record['candidate'], system.arm, 0)
    path = tmp_path/'state/metadata.json'; meta = json.loads(path.read_text())
    if change == 'file':
        param = tmp_path/'state/parameters.npz'; param.write_bytes(param.read_bytes()+b'x')
    elif change == 'array_hash': meta['arrays'][0]['sha256'] = '0'*64
    elif change == 'extra_key': meta['arrays'].append(dict(meta['arrays'][0], key='final_labels'))
    elif change == 'recipe': meta['recipe']['private_fixture'] = True
    path.write_text(json.dumps(meta))
    with pytest.raises(ValueError): load_state(tmp_path/'state')


def test_export_precedes_final_data_delegates_sinks_and_restores_constructor(tmp_path, monkeypatch):
    system = fixture_system(); record = fixture_record(system); name = record['candidate']
    class Original:
        def __new__(cls, *args, **kwargs): return system
    module = SimpleNamespace(Candidate=Original)
    monkeypatch.setattr(suite.importlib, 'import_module', lambda *args: module)
    monkeypatch.setattr(suite, 'bound_private_path', lambda plan: {})
    monkeypatch.setattr(suite, 'project_root', lambda: tmp_path)
    events = []
    def delegated(candidate, plan, trial, phase, fit, data):
        assert plan['benchmark'] == suite.selected.BENCHMARK_VERSION
        assert module.Candidate() is system
        phase('fit'); fit(record)
        assert (tmp_path/f'research/tmp/EXP-20261005-9999/fitted-source/{name}/metadata.json').exists()
        phase('evaluation'); data({'split': 'D'}); trial('trial')
        return 'PASS'
    monkeypatch.setattr(suite.selected, 'run_suite', delegated)
    protocol = fixture_protocol(system)
    protocol.update(evaluation_data_role='frozen_fresh_final_v1', roles={name:{'arm':system.arm,'seed_index':0}})
    plan = {'benchmark': suite.BENCHMARK_VERSION, 'experiment_id':'EXP-20261005-9999','research_program_protocol':protocol}
    before = copy.deepcopy(plan)
    sinks = [lambda value, tag=tag: events.append((tag,value)) for tag in ('trial','phase','fit','data')]
    assert suite.run_suite(name, plan, *sinks) == 'PASS' and plan == before
    assert module.Candidate is Original
    assert [tag for tag, _ in events] == ['phase','fit','phase','data','trial']
    assert events[1][1]['source_state_export']['copied_before_final_arrays']


@pytest.mark.parametrize('role', ['development', None])
def test_suite_rejects_unfrozen_role_before_any_constructor_or_arrays(role):
    with pytest.raises(ValueError): suite.run_suite('none', {'benchmark':suite.BENCHMARK_VERSION,'research_program_protocol':{'evaluation_data_role':role}})


def test_every_scientific_field_and_previous_file_stays_unchanged():
    parent = json.loads((ROOT/STUDY['parent_evidence']['parent_study_path']).read_text())
    for key in ('candidates','roles','recipe','matrix','diagnosis_gates','reference_gates','dense_noise_reference_gates',
                'economic_gates','economic_measurement','unaugmented_reference_confirmation','unaugmented_reference_guards',
                'selected_classical_route_confirmation','amortization_report'):
        assert STUDY[key] == parent[key], key
    assert {k:v for k,v in STUDY['data'].items() if k!='tag'} == {k:v for k,v in parent['data'].items() if k!='tag'}
    assert len(STUDY['parent_evidence']['scientific_source_sha256_unchanged']) == 112
    for relative, digest in STUDY['parent_evidence']['scientific_source_sha256_unchanged'].items():
        assert sha256_file(ROOT/relative) == digest, relative
    assert STUDY['fitted_source_state_export']['expected_exports'] == 25


@pytest.mark.parametrize('arm', ['transport_pca', 'ridge_pca_scan', 'dense_cached_cpu'])
def test_real_candidate_constructor_can_restore_compatible_state_without_source_fit(tmp_path, arm):
    # Public fixed initialized parameters only: no task generator, data or optimizer.
    import importlib
    from nextai_autoresearch.candidates.pvm01_core import parameter_hash
    cls = importlib.import_module(f'nextai_autoresearch.candidates.pvm01_tc_{arm}_s0').Candidate
    source = cls(seed=7, arm=arm, recipe=STUDY['recipe'])
    for name in ('model','decoder'):
        module = getattr(source, name, None)
        if module is not None: setattr(source, name, module.to('cpu').eval())
    source.device, source.arm = torch.device('cpu'), arm
    if arm == 'ridge_pca_scan': source.weights = np.ones((65,64), dtype=np.float32)*.001
    source.projection = None if arm == 'dense_cached_cpu' else np.eye(64, dtype=np.float32)[:,:16].copy()
    report = {'arm':arm, 'seed':7, 'seed_index':0, 'calibration_choice':{'threshold':source.threshold},
              'final_encoder_sha256':parameter_hash(source.model) if source.model is not None else None,
              'final_decoder_sha256':parameter_hash(source.decoder) if source.decoder is not None else None}
    if source.projection is not None: report['pca_projection_sha256'] = hashlib.sha256(source.projection.tobytes()).hexdigest()
    if source.weights is not None: report['fp32_ridge_weights_sha256'] = hashlib.sha256(source.weights.tobytes()).hexdigest()
    record = {'candidate':f'pvm01_tc_{arm}_s0','fit_report':report,'fit_report_sha256':sha256_json(report)}
    export_state(source, tmp_path/'state', record, fixture_protocol(source), record['candidate'], arm, 0)
    metadata, arrays = load_state(tmp_path/'state')
    restored = cls(seed=7, arm=arm, recipe=STUDY['recipe'])
    restore_state(restored, metadata, arrays)
    assert restored.arm == arm and restored.device.type == 'cpu'
    assert restored.losses == []  # No fit was used to make the receiver compatible.
    query = np.zeros(64, dtype=np.float32); query[0] = 1
    left, right = source.new_session(1), restored.new_session(1)
    for session in (left, right): session.ingest((0, 1, query, 3))
    assert left.answer(query) == right.answer(query)
    assert left.state_bytes() == right.state_bytes()


@pytest.mark.parametrize('change', ['valid','missing_journal','metadata','undercharged','missing_unit','trial_report'])
def test_all_25_saved_source_exports_are_required_by_final_analysis(tmp_path, monkeypatch, change):
    import importlib.util
    from nextai_autoresearch.pvm01_fitted_state import ARMS
    monkeypatch.syspath_prepend(str(ROOT/'scripts'))
    spec = importlib.util.spec_from_file_location('fresh_final_saved_fixture', ROOT/'scripts/analyze_pvm01_fresh_final.py')
    analysis = importlib.util.module_from_spec(spec); spec.loader.exec_module(analysis)
    identity = 'EXP-20261005-9998'; outcomes = []; protocol = None
    for arm in ARMS:
        for index in range(5):
            system = fixture_system(arm); system.seed += index
            record = fixture_record(system); name = f'pvm01_tc_{arm}_s{index}'
            record['candidate'] = name; record['seed'] = system.seed
            record['fit_report'].update(seed=system.seed, seed_index=index)
            record['fit_report_sha256'] = sha256_json(record['fit_report'])
            if protocol is None: protocol = dict(fixture_protocol(system), roles={})
            protocol['roles'][name] = {'arm':arm,'seed_index':index}
            directory = tmp_path/f'research/tmp/{identity}/fitted-source/{name}'
            descriptor = export_state(system, directory, record, protocol, name, arm, index)
            journal = tmp_path/f'research/tmp/{identity}/{name}.fits.jsonl'
            journal.write_text(json.dumps(dict(record, source_state_export=descriptor))+'\n')
            outcomes.append({'candidate':name,'trials':[{'fit_report':copy.deepcopy(record['fit_report'])}],
                             'execution':{'supervised_fit_seconds':10.}})
    if change == 'missing_journal': journal.unlink()
    elif change == 'metadata':
        path = directory/'metadata.json'; path.write_bytes(path.read_bytes()+b' ')
    elif change == 'undercharged': outcomes[-1]['execution']['supervised_fit_seconds'] = -1
    elif change == 'missing_unit': outcomes.pop()
    elif change == 'trial_report': outcomes[-1]['trials'][0]['fit_report']['seed'] = 8
    value = analysis.fitted_source_checks(tmp_path, identity, outcomes, protocol)
    assert value['complete'] == (change == 'valid')
    assert value['source_refit_or_final_arrays_used_by_analysis'] is False
