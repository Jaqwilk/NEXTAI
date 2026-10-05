from pathlib import Path
import copy
import json
import struct
import subprocess
import zlib

import numpy as np
import pytest
import torch

from nextai_autoresearch.asm01_task import parse_native_sample, transform, episode, episode_hash, pairs, load_unit, arrays_hash
from nextai_autoresearch.candidates.asm01_core import Candidate, banded_dtw_scores
from nextai_autoresearch.benchmarks.har01_native_memory_v1 import source_state, copy_service_state, scores
from scripts.acquire_asm01 import archive_index, identities


ROOT=Path(__file__).resolve().parents[1]
STUDY=json.loads((ROOT/'research/plans/ASM01-FROZEN-SOURCE-SCREEN-V1.json').read_text(encoding='utf-8'))


def sample(name='discarded-name'):
    rows=['CHARACTER_NAME: '+name,'STROKE_COUNT: 2','PEN_DOWN\t\t\t1']
    rows += [f'{i*10} {i*i} 1 1' for i in range(12)]
    rows += ['PEN_UP\t\t0\t1','PEN_DOWN\t\t\t2']
    rows += [f'{100+i*10} {100+i*i} 1 2' for i in range(8)]
    rows += ['PEN_UP\t\t0\t2','END_CHARACTER: '+name]
    return ('\n'.join(rows)+'\n').encode('ascii')


def fixture_unit():
    t=np.linspace(0,1,40,dtype=np.float32)
    paths=tuple(np.column_stack((1000*t,1000*(np.sin(t*(i+3)/10)+t*t))).astype(np.float32) for i in range(183))
    result={}
    for name,count,writer in (('T-fit',64,1),('T-validation',24,1),('T-calibration',95,1),('D',183,16)):
        result[name]=(paths[:count],np.column_stack((np.arange(1,count+1),np.full(count,writer))))
    result.update(mean=np.zeros(64,dtype=np.float32),scale=np.ones(64,dtype=np.float32),train_subject=1,dev_subject=16)
    return result


def test_publisher_parser_discards_names_and_preserves_native_strokes():
    left=parse_native_sample(sample('a'));right=parse_native_sample(sample('unrelated'))
    np.testing.assert_array_equal(left,right)
    assert left.shape==(20,2) and left.dtype==np.float32
    for view in ('write','nominal','adverse'):
        feature=transform(left,view)
        assert feature.shape==(64,) and feature.dtype==np.float32
        assert np.linalg.norm(feature)==pytest.approx(1.,abs=1e-6)
    assert not np.array_equal(transform(left,'nominal'),transform(left,'adverse'))
    np.testing.assert_allclose(transform(left*2+300,'write'),transform(left,'write'),atol=1e-6)


@pytest.mark.parametrize('bad',[
    sample().replace(b'STROKE_COUNT: 2',b'STROKE_COUNT: 3'),
    sample().replace(b'10 1 1 1',b'10 1 0 1'),
    sample().replace(b'10 1 1 1',b'5000 1 1 1'),
    sample().replace(b'PEN_UP\t\t0\t2\n',b''),
    b'CHARACTER_NAME: x\nSTROKE_COUNT: 1\nPEN_DOWN\n1 1 1 1\nPEN_UP\nEND_CHARACTER: x\n',
])
def test_malformed_or_degenerate_native_sample_stops_without_replacement(bad):
    with pytest.raises(ValueError):
        parse_native_sample(bad)


def test_native_episode_pairing_and_hashes_do_not_depend_on_object_addresses():
    unit=fixture_unit();left=episode(unit,'a'*64,'D',64,4,0);right=episode(unit,'a'*64,'D',64,4,0,condition='adverse')
    assert left.answers==right.answers and left.target_handles==right.target_handles and left.target_sources==right.target_sources
    assert episode_hash(left)==episode_hash(copy.deepcopy(left))
    assert len(left.writes)==64+4*16+16
    assert all('uci-asm:writer16:' in row[4] for row in left.writes)
    assert all(isinstance(query,np.ndarray) and query.shape[1]==2 for query in left.queries)
    assert sum(truth==-1 for truth in left.answers)==16
    with pytest.raises(ValueError,match='fixed ASM screen'):
        load_unit(ROOT,5,'a'*64)


def test_all64_kernel_landmarks_are_distinct_native_fit_samples():
    writes,queries=pairs(fixture_unit(),'b'*64,'T-fit',4096)
    assert writes.shape==queries.shape==(4096,64)
    assert len({arrays_hash(row) for row in queries[:64]})==64
    with pytest.raises(ValueError,match='No D'):
        pairs(fixture_unit(),'b'*64,'D',4096)


def test_margin_rejects_ambiguous_facts_and_preserves_latest_source():
    model=Candidate(44,'native_raw',STUDY['recipe']);model.threshold=.9;model.margin_threshold=.005
    session=model.new_session(2);key=np.eye(64,dtype=np.float32)[0]
    session.ingest((10,71,key,8,'new'));session.ingest((2,71,key,3,'old'))
    session.ingest((0,72,key.copy(),9,'different'))
    answer=session.answer(key)
    assert answer[0]==-1 and answer[-1] is None and answer[1]==71
    session.ingest((12,72,np.eye(64,dtype=np.float32)[1],9,'other-new'))
    answer=session.answer(key)
    assert answer[0]==8 and answer[-1]=='new'


def test_dtw_matches_independent_scalar_band_and_tie_rule():
    keys=np.stack([transform(parse_native_sample(sample()),view) for view in ('write','nominal')])
    query=keys[0].copy();actual=banded_dtw_scores(keys,query)
    expected=[]
    for key in keys:
        costs={(0,0):(0.,0)}
        for i in range(1,33):
            for j in range(max(1,i-4),min(32,i+4)+1):
                previous=[costs.get(p,(float('inf'),0)) for p in ((i-1,j-1),(i-1,j),(i,j-1))]
                best=min(range(3),key=lambda p:previous[p][0]);value,length=previous[best]
                local=32*sum((float(a)-float(b))**2 for a,b in zip(key.reshape(32,2)[i-1],query.reshape(32,2)[j-1],strict=True))
                costs[i,j]=value+local,length+1
        value,length=costs[32,32];expected.append(1/(1+value/length))
    np.testing.assert_allclose(actual,expected,rtol=1e-12,atol=1e-12)
    assert actual[0]==1


@pytest.mark.parametrize('arm',['source_trained','source_untrained','source_shuffled','source_ridge'])
def test_actual_source_readout_and_service_copy_preserve_original_weights(arm):
    arrays,provenance=source_state(ROOT,arm,0,STUDY)
    model=Candidate(555,arm,STUDY['recipe'],source_arrays=arrays);before=copy.deepcopy(model.source_identity())
    rng=np.random.default_rng(221);write=rng.normal(size=(80,64)).astype(np.float32);query=write*.9
    model.fit(write[:64],query[:64],write[64:],query[64:])
    assert provenance['source_unit']==0 and model.source_identity()==before
    assert model.report['optimizer_steps']==0 and model.report['source_frozen'] is True
    assert copy_service_state(model).source_identity()==before


def test_value_equality_cannot_hide_wrong_current_source():
    value=scores([dict(answer=7,truth=7,source='old',target_source='new',top_handle=1,target_handle=1,top_value=7,stratum='updated')])
    assert value['value_accuracy']==1 and value['accuracy']==value['updated_known_accuracy']==0


def test_public_rar_fixture_and_native_identity_headers(tmp_path):
    def header(body):
        return struct.pack('<H',zlib.crc32(body)&0xffff)+body
    name=b'folder/1.1.txt';payload=sample()
    archive=(b'Rar!\x1a\x07\x00'+header(struct.pack('<BHHHI',0x73,0,13,0,0))+
             header(struct.pack('<BHHIIBIIBBHI',0x74,0x8000,32+len(name),len(payload),len(payload),2,
                                zlib.crc32(payload),0,20,0x30,len(name),0x20)+name)+payload+
             header(struct.pack('<BHH',0x7b,0,7)))
    path=tmp_path/'public-fixture.rar';path.write_bytes(archive)
    index,total=archive_index(path,1048576)
    assert index==[dict(path='folder/1.1.txt',bytes=len(payload))] and total==len(payload)
    listed=subprocess.run(['tar.exe','-tf',str(path)],capture_output=True,timeout=10)
    assert listed.returncode==0 and b'folder/1.1.txt' in listed.stdout
    result=subprocess.run(['tar.exe','-xOf',str(path),'folder/1.1.txt'],capture_output=True,timeout=10)
    assert result.returncode==0 and result.stdout==payload
    records=[dict(path=f'Writer{w}/{c}.{w}.txt',bytes=500) for w in range(1,46) for c in range(1,184)]
    bound=identities(records)
    assert bound[10,132]=='Writer10/132.10.txt'
    with pytest.raises(ValueError,match='45writers'):
        identities(records[:-1])
