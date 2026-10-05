from pathlib import Path
import copy
import json

import numpy as np
import pytest
import torch
from jsonschema.exceptions import ValidationError

from nextai_autoresearch.audit import audit_candidate
from nextai_autoresearch.config import load_config
from nextai_autoresearch.research_program import _study_scope
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.utils import atomic_write_json,sha256_file
from nextai_autoresearch.candidates.asm01_core import Candidate


ROOT=Path(__file__).resolve().parents[1]
STUDY_PATH='research/plans/ASM01-FROZEN-SOURCE-SCREEN-V3.json'
STUDY=json.loads((ROOT/STUDY_PATH).read_text(encoding='utf-8'))


def native_plan():
    plan=json.loads((ROOT/'research/plans/EXP-20261005-0006.json').read_text(encoding='utf-8'))
    plan.update(benchmark=STUDY['cohort'],candidates=STUDY['candidates'],matrix=copy.deepcopy(STUDY['matrix']))
    plan['research_program_protocol']=dict(authority_path='research/laboratory/NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1.json',
        program_contract_path=STUDY['program_contract_path'],program_contract_sha256=STUDY['program_contract_sha256'],
        study_path=STUDY_PATH,study_sha256=sha256_file(ROOT/STUDY_PATH),registration_ticket=2,**_study_scope(STUDY))
    return plan


def test_exact_native_schema_preserves_frozen_scales_recipe_confidence_and_controls():
    plan=native_plan();validate_document('experiment_plan',plan,ROOT)
    for alter in ('scale','steps','margin','missing-control'):
        changed=copy.deepcopy(plan)
        if alter=='scale':
            changed['matrix']['knowledge_sizes'][-1]=512
        elif alter=='steps':
            changed['research_program_protocol']['recipe']['alignment_steps']=8192
        elif alter=='margin':
            changed['research_program_protocol']['recipe']['margin_grid']=[0.]
        else:
            changed['candidates'].pop()
        with pytest.raises(ValidationError):
            validate_document('experiment_plan',changed,ROOT)


def test_all45_native_roles_audited_and_private_writer_data_import_forbidden(tmp_path):
    config=load_config(ROOT)
    for name in STUDY['candidates']:
        result=audit_candidate(name,config,ROOT)
        assert result.ok,result.problems
    directory=tmp_path/'src/nextai_autoresearch/candidates';directory.mkdir(parents=True)
    (directory/'native_leak.py').write_text('from nextai_autoresearch.asm01_task_v5 import load_unit\nclass Candidate: pass\n',encoding='utf-8')
    rejected=audit_candidate('native_leak',config,tmp_path)
    assert not rejected.ok and any('evaluator' in problem for problem in rejected.problems)


def test_actual_dense_model_cached_top2_scores_agree_with_full_transformer():
    recipe=dict(STUDY['recipe'],alignment_steps=1,dense_set_steps=2)
    model=Candidate(666,'target_dense',recipe)
    rng=np.random.default_rng(122);writes=rng.normal(size=(40,64)).astype(np.float32);queries=writes.copy()
    sets={size:(np.repeat(writes[None,:size],4,axis=0),np.repeat(queries[None,:8],4,axis=0),
                np.repeat(np.arange(8)[None],4,axis=0)) for size in (16,32)}
    model.fit(writes[:32],queries[:32],writes[32:],queries[32:],sets)
    assert isinstance(model.decoder,torch.nn.TransformerDecoder) and model.report['optimizer_steps']==1
    session=model.new_session(16)
    for i in range(16):
        session.ingest((i,100+i,writes[i],i,f'source:{i}'))
    with torch.inference_mode():
        embedded=torch.nn.functional.normalize(model.model(torch.as_tensor(queries[0])),dim=-1)
        full=model.refine(embedded.reshape(1,1,64),session.cached.keys.reshape(1,16,64))[0,0]
        cached=session.cached.decoded(embedded)
        torch.testing.assert_close(full,cached,rtol=1e-5,atol=1e-5)
        expected=(1+torch.clamp(session.cached.keys@full,-1,1))/2
    handle,score,margin,value=session.ranked(queries[0]);first=int(torch.argmax(expected))
    second=float(torch.topk(expected,2).values[1])
    assert handle==100+first and value==first
    assert score==pytest.approx(float(expected[first]),abs=1e-5) and margin==pytest.approx(float(expected[first])-second,abs=1e-5)


@pytest.mark.parametrize('arm,grid',[('target_ridge_pca',6),('target_kernel',12)])
def test_target_classical_gridfits_keep64_distinct_landmarks_and_full_pca_grid(arm,grid):
    rng=np.random.default_rng(112);values=rng.normal(size=(96,64)).astype(np.float32)
    model=Candidate(777,arm,STUDY['recipe']);model.fit(values[:64],values[:64],values[64:],values[64:])
    assert len(model.report['classical_grid'])==grid and np.isfinite(model.weights).all()
    if arm=='target_kernel':
        assert len(model.landmarks)==64 and len({row.tobytes() for row in model.landmarks})==64
    else:
        assert len(model.report['pca_grid'])==6


def test_train_only_calibration_uses_all144_pairs_and_rejects_absent_margin():
    model=Candidate(44,'native_raw',STUDY['recipe']);key=np.eye(64,dtype=np.float32)
    model.fit(key[:2],key[:2],key[:2],key[:2])
    model.calibrate([(((0,71,key[0],7,'source:a'),(1,72,key[1],8,'source:b')),
                       np.stack([key[0],key[1],key[2]]),((7,'source:a'),(8,'source:b'),(-1,None)))])
    assert len(model.report['calibration_grid'])==144 and model.report['calibration_feasible'] is True
    assert model.report['calibration_choice']['accuracy']==1 and model.margin_threshold==.005


def test_serialized_native_worker_stops_at_trusted_boundary_before_arrays_or_fit(tmp_path,monkeypatch):
    from nextai_autoresearch import worker_resources
    from nextai_autoresearch.worker import run_worker
    from nextai_autoresearch.benchmarks import asm01_native_memory_v3 as benchmark
    class FitBoundary(Exception):
        pass
    phases=[]
    class TestResources:
        def __init__(self,*args):
            pass
        def start(self):
            phases.append('start')
        def phase(self,name):
            phases.append(name);assert name=='fit';raise FitBoundary('Serialized ASM worker reached pre-fit boundary')
        def close(self):
            phases.append('close')
    plan=native_plan();plan['experiment_id']='EXP-20990101-9999';plan['matrix']['seeds']=[101,102,103,104,105]
    for relative in (STUDY_PATH,STUDY['task_contract_path']):
        target=tmp_path/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/relative).read_bytes())
    private=tmp_path/'research/tmp'/plan['experiment_id']/'asm01-private-data.json'
    atomic_write_json(private,dict(experiment_id=plan['experiment_id'],unit_nonces=[f'{i:064x}' for i in range(5)]))
    plan.update(asm01_private_data_path=str(private),asm01_private_data_sha256=sha256_file(private))
    monkeypatch.setattr(benchmark,'project_root',lambda:tmp_path)
    monkeypatch.setattr(worker_resources,'WorkerResources',TestResources)
    monkeypatch.setattr(torch.cuda,'is_available',lambda:True)
    monkeypatch.setattr(benchmark,'load_unit',lambda *args:pytest.fail('Native arrays before boundary'))
    runtime,output=tmp_path/'runtime.json',tmp_path/'worker.json';atomic_write_json(runtime,plan)
    assert run_worker(runtime,'asm01_source_trained_s0',output)==1
    result=json.loads(output.read_text());assert result['error_type']=='FitBoundary' and result['trials']==[]
    assert 'asm01_native_memory_v3.py' in result['traceback'] and phases==['start','fit','close']
    assert not output.with_suffix('.fits.jsonl').exists() and not output.with_suffix('.data.jsonl').exists()
