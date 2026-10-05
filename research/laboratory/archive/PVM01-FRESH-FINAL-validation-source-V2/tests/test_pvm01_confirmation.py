import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.benchmarks import paired_view_mutable_memory_v9 as suite
from nextai_autoresearch.research_program import _study_scope, verify_pvm01_fresh_realization
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import sha256_file
from nextai_autoresearch.worker_resource_peaks import PHASES, VERSION, take_peak_snapshot, validate_peak_record
from nextai_autoresearch.worker_resources import WorkerResources

ROOT=Path(__file__).resolve().parents[1]
STUDY=json.loads((ROOT/'research/plans/PVM01-DENSE-NOISE-CONFIRMATION-V1.json').read_text(encoding='utf-8'))
LIMITS={'max_cuda_reserved_bytes':4096,'fit_seconds_cap':210,'resource_measurement_version':VERSION}


def analyzer(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT/'scripts'))
    spec=importlib.util.spec_from_file_location('confirmation_analysis_fixture',ROOT/'scripts/analyze_pvm01_confirmation.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def record():
    return {'schema_version':1,'version':VERSION,'timed_service_modified':False,
            'snapshots':[{'phase':phase,'cuda_available':True,'cuda_peak_allocated_bytes':i*100,
                          'cuda_peak_reserved_bytes':i*200,'process_rss_bytes':10000+i}
                         for i,phase in enumerate(PHASES)]}


@pytest.mark.parametrize('change',['valid','missing_complete','duplicate','order','decrease','cap','allocated_gt_reserved','bool_bytes','negative','nonfinite','missing_field','availability','wrong_version','timed_service','bad_row','bad_object'])
def test_trusted_resource_evidence_cannot_silently_qualify_invalid_measurements(change):
    value=record(); rows=value['snapshots']
    if change=='missing_complete': rows.pop()
    elif change=='duplicate': rows[2]['phase']='fit'
    elif change=='order': rows[1],rows[2]=rows[2],rows[1]
    elif change=='decrease': rows[-1]['cuda_peak_allocated_bytes']=0
    elif change=='cap': rows[-1]['cuda_peak_reserved_bytes']=4097
    elif change=='allocated_gt_reserved': rows[-1]['cuda_peak_allocated_bytes']=4000
    elif change=='bool_bytes': rows[-1]['process_rss_bytes']=True
    elif change=='negative': rows[-1]['process_rss_bytes']=-1
    elif change=='nonfinite': rows[-1]['process_rss_bytes']=float('nan')
    elif change=='missing_field': del rows[-1]['process_rss_bytes']
    elif change=='availability': rows[-1]['cuda_available']=False
    elif change=='wrong_version': value['version']='legacy'
    elif change=='timed_service': value['timed_service_modified']=True
    elif change=='bad_row': rows[-1]=None
    elif change=='bad_object': value=None
    if change=='valid': assert validate_peak_record(value,LIMITS)
    else:
        with pytest.raises(ValueError): validate_peak_record(value,LIMITS)


def test_partial_peak_history_is_preserved_without_becoming_a_complete_worker():
    value=record(); value['snapshots']=value['snapshots'][:2]
    assert validate_peak_record(value,LIMITS,require_complete=False)
    with pytest.raises(ValueError): validate_peak_record(value,LIMITS)


def test_snapshot_uses_synchronized_cumulative_allocator_counts_and_real_rss():
    calls=[]
    cuda=SimpleNamespace(is_available=lambda:True,synchronize=lambda:calls.append('sync'),max_memory_allocated=lambda:128,max_memory_reserved=lambda:256)
    value=take_peak_snapshot('complete',SimpleNamespace(cuda=cuda),LIMITS)
    assert calls==['sync'] and value['cuda_peak_allocated_bytes']==128 and value['cuda_peak_reserved_bytes']==256 and value['process_rss_bytes']>0
    cuda.max_memory_reserved=lambda:5000
    with pytest.raises(ValueError): take_peak_snapshot('complete',SimpleNamespace(cuda=cuda),LIMITS)


def test_new_snapshots_do_not_change_legacy_phase_schema_or_use_model_counters(tmp_path,monkeypatch):
    output=tmp_path/'worker.json'; limits={**LIMITS,'max_cuda_reserved_bytes':2**32}
    resources=WorkerResources(output,limits,tmp_path/'plan.json')
    resources.torch=SimpleNamespace(cuda=SimpleNamespace(is_available=lambda:False))
    monkeypatch.setattr('nextai_autoresearch.worker_resources.write_device_sample',lambda p,v,r:p.write_text(json.dumps(v),encoding='utf-8'))
    for phase in PHASES: resources.phase(phase)
    evidence=json.loads(output.with_suffix('.resources.json').read_text(encoding='utf-8'))
    assert validate_peak_record(evidence,limits)
    assert all(row['cuda_peak_reserved_bytes']==0 for row in evidence['snapshots'])
    assert set(json.loads(output.with_suffix('.phase.json').read_text(encoding='utf-8')))=={'phase','fit_started','fit_elapsed'}
    legacy=WorkerResources(tmp_path/'legacy.json',{'max_cuda_reserved_bytes':2**32,'fit_seconds_cap':210},tmp_path/'plan.json')
    legacy.phase('initializing')
    assert not legacy.output.with_suffix('.resources.json').exists()


def test_new_cohort_preserves_all_inputs_sinks_and_original_plan(monkeypatch):
    called=[]; monkeypatch.setattr(suite.selected,'run_suite',lambda *a:called.append(a) or 'PASS')
    plan={'benchmark':suite.BENCHMARK_VERSION,'matrix':{'sentinel':[1]}}; original=copy.deepcopy(plan); sinks=[object() for _ in range(4)]
    assert suite.run_suite('candidate',plan,*sinks)=='PASS' and plan==original
    assert called==[('candidate',{**plan,'benchmark':suite.selected.BENCHMARK_VERSION},*sinks)]
    with pytest.raises(ValueError): suite.run_suite('candidate',{'benchmark':suite.selected.BENCHMARK_VERSION},*sinks)


@pytest.mark.parametrize('change',['valid','missing_resource','wrong_resource','old_path','old_hash','old_pair','legacy_resource'])
def test_new_bindings_are_exact_without_widening_old_cohorts(change):
    plan=json.loads((ROOT/'research/plans/EXP-20261005-0003.json').read_text(encoding='utf-8'))
    validate_document('experiment_plan',plan,ROOT); old=copy.deepcopy(plan['research_program_protocol'])
    plan['benchmark']=STUDY['cohort']; plan['research_program_protocol'].update(_study_scope(STUDY))
    if change=='missing_resource': del plan['research_program_protocol']['resource_measurement_version']
    elif change=='wrong_resource': plan['research_program_protocol']['resource_measurement_version']='unchecked'
    elif change=='legacy_resource': plan['benchmark']='paired_view_mutable_memory_v8'; plan['research_program_protocol']=old; plan['research_program_protocol']['resource_measurement_version']=VERSION
    elif change.startswith('old_'):
        for key in ('classical_economic_contract_path','classical_economic_contract_sha256'):
            if change=='old_pair' or change=='old_path' and key.endswith('path') or change=='old_hash' and key.endswith('sha256'): plan['research_program_protocol'][key]=old[key]
    if change=='valid': validate_document('experiment_plan',plan,ROOT)
    else:
        with pytest.raises(ValidationError): validate_document('experiment_plan',plan,ROOT)


@pytest.mark.parametrize('change',['valid','seed','nonce','tamper','missing','scope'])
def test_all_consumed_noise_units_are_checked_before_new_arrays(tmp_path,change):
    identities=[f'EXP-20261004-{i:04d}' for i in range(4,9)]+[f'EXP-20261005-{i:04d}' for i in range(1,4)]
    directories={}
    for i,identity in enumerate(identities):
        directory=tmp_path/f'research/laboratory/archive/{identity}-runtime'
        if identity!='EXP-20261004-0005': directory/=f'research/tmp/{identity}'
        directory.mkdir(parents=True); private=directory/'pvm01-private-data.json'
        private.write_text(json.dumps({'experiment_id':identity,'unit_nonces':[f'{1000+i:064x}']}),encoding='utf-8')
        (directory/'runtime-plan.json').write_text(json.dumps({'experiment_id':identity,'matrix':{'seeds':[1000+i]},'pvm01_private_data_sha256':sha256_file(private)}),encoding='utf-8')
        directories[identity]=directory
    seeds=[9000+i for i in range(5)]; nonces=[f'{9000+i:064x}' for i in range(5)]; latest=directories[identities[-1]]/'pvm01-private-data.json'
    if change=='seed': seeds[0]=1007
    elif change=='nonce': nonces[0]=f'{1007:064x}'
    elif change=='tamper': latest.write_bytes(latest.read_bytes()+b' ')
    elif change=='missing': latest.unlink()
    kwargs={'include_latest':True,'include_transport':True,'include_replication':change!='scope','include_dense_noise':True}
    if change=='valid': verify_pvm01_fresh_realization(tmp_path,seeds,nonces,**kwargs)
    else:
        with pytest.raises((ValueError,FileNotFoundError)): verify_pvm01_fresh_realization(tmp_path,seeds,nonces,**kwargs)


@pytest.mark.parametrize('change',['pass','invalid','missing_peak','failed_reference','failed_classical'])
def test_independent_decision_cannot_pool_selection_or_promote_without_controls(monkeypatch,change):
    analysis={'valid_comparison':change!='invalid','reference_selection':{'adequate_for_prospective_selection':change!='failed_reference'},'selected_classical_route_confirmation':{'screen_qualified':change!='failed_classical'}}
    checks={str(i):True for i in range(85)}
    if change=='missing_peak': checks.pop('0')
    result=analyzer(monkeypatch).independent_decision(analysis,checks)
    assert result['selected_route_independently_confirmed']==(change=='pass')
    assert result['no_promotion'] and result['selection_outcomes_excluded_from_intervals']
    if change in ('invalid','missing_peak'): assert result['decision']=='INCONCLUSIVE comparison'


def test_fit_is_charged_once_and_reuse_means_whole_workloads(monkeypatch):
    reuse=analyzer(monkeypatch).reuse_cost
    value=reuse(12.,2.,1.,3.,[1,4,16])
    assert value['faster_service_break_even_workloads']==5.
    assert value['by_reuse']['4']=={'candidate_seconds':16.,'reference_seconds':14.}
    assert reuse(1.,2.,1.,3.,[1])['faster_service_break_even_workloads']==0.
    assert reuse(1.,2.,4.,3.,[1])['faster_service_break_even_workloads'] is None
    for args in ((float('nan'),2.,1.,3.,[1]),(1.,2.,1.,3.,[0])):
        with pytest.raises(ValueError): reuse(*args)


def test_all_selected_recipes_data_metrics_and_thresholds_are_identical():
    old=json.loads((ROOT/STUDY['parent_evidence']['parent_study_path']).read_text(encoding='utf-8'))
    for key in ('candidates','roles','recipe','matrix','diagnosis_gates','reference_gates','dense_noise_reference_gates','economic_gates','economic_measurement','selected_classical_route_confirmation'):
        assert STUDY[key]==old[key],key
    assert {k:v for k,v in STUDY['data'].items() if k!='tag'}=={k:v for k,v in old['data'].items() if k!='tag'}
    assert all(sha256_file(ROOT/p)==digest for p,digest in STUDY['parent_evidence']['scientific_source_sha256_unchanged'].items())
    assert len(STUDY['candidates'])==85 and len(STUDY['parent_evidence']['scientific_source_sha256_unchanged'])==102
