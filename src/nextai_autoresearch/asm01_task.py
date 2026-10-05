"""Preregistered electronic-pen instance memory; no class or writer query key."""
from pathlib import Path
import re

import numpy as np

from .har01_task import Episode, arrays_hash, rng_for
from .utils import load_json, sha256_file, sha256_json


SCREEN_WRITERS = tuple(range(1, 6)) + tuple(range(16, 21))


def parse_native_sample(payload):
    if not isinstance(payload, bytes) or len(payload) > 262144:
        raise ValueError('Native sample byte cap/type')
    lines = [line.strip() for line in payload.decode('ascii').splitlines() if line.strip()]
    if len(lines) < 5 or not lines[0].startswith('CHARACTER_NAME:') or not lines[-1].startswith('END_CHARACTER:'):
        raise ValueError('Native sample header/end grammar')
    if not re.fullmatch(r'STROKE_COUNT:\s*[1-9][0-9]*', lines[1]):
        raise ValueError('Native stroke count grammar')
    count = int(lines[1].split(':',1)[1]); stroke = 0; down = False; points = []; previous = None
    for line in lines[2:-1]:
        fields = line.split()
        if fields[0] in {'PEN_DOWN','PEN_UP'}:
            marker, extra = fields[0], fields[1:]
            if marker == 'PEN_DOWN':
                if down:
                    raise ValueError('Repeated pen-down')
                stroke += 1; down = True; previous = None
                if extra and (len(extra)!=1 or not extra[0].isdigit() or int(extra[0])!=stroke):
                    raise ValueError('Pen-down supplied stroke serial')
            else:
                if not down:
                    raise ValueError('Pen-up without a stroke')
                if extra and (len(extra) not in {1,2} or not all(x.isdigit() for x in extra)
                              or int(extra[-1])!=stroke or (len(extra)==2 and int(extra[0])!=0)):
                    raise ValueError('Pen-up supplied state/stroke')
                down = False; previous = None
            continue
        if not down or len(fields)!=4 or not all(re.fullmatch(r'[0-9]+',x) for x in fields):
            raise ValueError('Native point grammar')
        x,y,state,serial=map(int,fields)
        if not 0<=x<=4392 or not 0<=y<=4868 or state!=1 or serial!=stroke:
            raise ValueError('Native point bounds/state/stroke')
        if (x,y)!=previous:
            points.append((x,y)); previous=(x,y)
        if len(points)>32768:
            raise ValueError('Native point cap')
    if down or stroke!=count or len(points)<4:
        raise ValueError('Incomplete or degenerate native sample')
    result=np.asarray(points,dtype=np.float32)
    # Both legal views must be feasible before any fit, including the adverse view.
    for view in ('write','nominal','adverse'):
        transform(result,view)
    return result


def transform(path, view, mean=None, scale=None):
    if not isinstance(path,np.ndarray) or path.ndim!=2 or path.shape[1]!=2 or path.dtype!=np.float32 or view not in {'write','nominal','adverse'}:
        raise ValueError('Malformed public pen observation')
    selected=path[0 if view=='write' else 1::2].astype(np.float64,copy=True)
    if view=='adverse':
        selected=selected[np.arange(len(selected))%4!=3]
    if len(selected)<2 or not np.isfinite(selected).all():
        raise ValueError('Degenerate native view')
    distance=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(selected,axis=0),axis=1))]
    if distance[-1]<=0:
        raise ValueError('Zero native arc length')
    keep=np.r_[True,np.diff(distance)>0]
    position=np.linspace(0.,distance[-1],32)
    sampled=np.column_stack([np.interp(position,distance[keep],selected[keep,j]) for j in range(2)])
    sampled-=sampled.mean(axis=0)
    rms=np.sqrt(np.mean(np.sum(sampled**2,axis=1)))
    if not np.isfinite(rms) or rms<=0:
        raise ValueError('Zero native RMS')
    return (sampled/(rms*np.sqrt(32))).ravel().astype(np.float32)


def load_unit(root,index,nonce):
    if index not in range(5):
        raise ValueError('Only the five fixed ASM screen pairs are accessible')
    manifest_path=root/'research/data_manifests/ASM01-ACQUISITION-V1.json'
    manifest=load_json(manifest_path)
    task=root/'research/plans/ASM01-PROSPECTIVE-NATIVE-TASK-V1.json'
    study=root/'research/plans/ASM01-FROZEN-SOURCE-SCREEN-V1.json'
    if (manifest.get('complete') is not True or manifest['task_contract_sha256']!=sha256_file(task)
            or manifest['study_sha256']!=sha256_file(study) or manifest['converted_writers']!=list(SCREEN_WRITERS)
            or manifest.get('no_future_writer_coordinates_read') is not True):
        raise ValueError('ASM native acquisition/scope binding mismatch')
    dataset=(root/manifest['dataset_path']).resolve()
    if not dataset.is_relative_to(root.resolve()) or sha256_file(dataset)!=manifest['dataset_sha256']:
        raise ValueError('ASM screen payload changed/outside repository')
    if sha256_file(root/'research/data/asm01_native_v1/publisher.rar')!=manifest['publisher_sha256']:
        raise ValueError('Preserved ASM publisher archive changed')
    selected=[]
    with np.load(dataset,allow_pickle=False) as archive:
        if set(archive.files)!={f'{prefix}_{w}' for w in SCREEN_WRITERS for prefix in ('points','offsets','rows')}:
            raise ValueError('Unexpected future writer in native screen payload')
        for writer in (index+1,index+16):
            points,offsets,rows=(archive[f'{p}_{writer}'].copy() for p in ('points','offsets','rows'))
            if arrays_hash(points,offsets,rows)!=manifest['converted_writer_hashes'][str(writer)] or len(offsets)!=184:
                raise ValueError('Native writer arrays changed')
            paths=tuple(points[offsets[j]:offsets[j+1]].copy() for j in range(183))
            selected.append((paths,rows))
    (train,train_rows),(dev,dev_rows)=selected
    order=rng_for(nonce,'native-fit-validation-calibration').permutation(183)
    result={}
    for name,indices in (('T-fit',order[:64]),('T-validation',order[64:88]),('T-calibration',order[88:])):
        result[name]=(tuple(train[i] for i in indices),train_rows[indices].copy())
    result.update(D=(dev,dev_rows),mean=np.zeros(64,dtype=np.float32),scale=np.ones(64,dtype=np.float32),
                  train_subject=index+1,dev_subject=index+16,train_writer=index+1,dev_writer=index+16,
                  intake_sha256=sha256_file(manifest_path),dataset_sha256=manifest['dataset_sha256'],
                  publisher_sha256=manifest['publisher_sha256'],
                  unique_counts={'T-fit':64,'T-validation':24,'T-calibration':95,'D':183})
    return result


def pairs(unit,nonce,split,count):
    if split not in {'T-fit','T-validation'}:
        raise ValueError('No D/calibration fitting')
    paths,_=unit[split]
    if count<len(paths):
        raise ValueError('All distinct fit/validation samples precede replacement draws')
    selected=np.r_[np.arange(len(paths)),rng_for(nonce,split).integers(len(paths),size=count-len(paths))]
    return (np.stack([transform(paths[i],'write') for i in selected]),
            np.stack([transform(paths[i],'nominal') for i in selected]))


def episode(unit,nonce,split,size,updates,index,query_count=64,condition='nominal'):
    if split not in {'T-fit','T-calibration','D'} or size not in {16,32,64} or updates not in {0,1,4}:
        raise ValueError('ASM scope: no reserved writer access')
    if condition not in {'nominal','adverse'} or (split!='D' and condition!='nominal'):
        raise ValueError('No adverse training/calibration')
    paths,row_ids=unit[split]
    rng=rng_for(nonce,f'episode|{split}|{size}|{updates}|{index}|{query_count}')
    known=query_count*3//4; absent=query_count-known
    selection=rng.choice(len(paths),size+absent,replace=False)
    present,unknown=selection[:size],selection[size:]
    handles=rng.permutation(size)+int(rng.integers(100000,1000000000))
    values=rng.integers(0,16,size=size)
    writer=unit['dev_subject'] if split=='D' else unit['train_subject']
    def source(i,tick):
        sample,actual_writer=row_ids[present[i]]
        if actual_writer!=writer:
            raise ValueError('Native provenance/writer mismatch')
        return f'uci-asm:writer{writer}:sample{int(sample)}:version{tick}'
    sources=[source(i,i) for i in range(size)]
    writes=[(i,int(handles[i]),paths[present[i]].copy(),int(values[i]),sources[i]) for i in range(size)]
    first=tuple(writes);changed=rng.choice(size,size//4,replace=False) if updates else np.array([],dtype=int);tick=size
    for _ in range(updates):
        for i in changed:
            values[i]=(values[i]+int(rng.integers(1,16)))%16;sources[i]=source(i,tick)
            writes.append((tick,int(handles[i]),paths[present[i]].copy(),int(values[i]),sources[i]));tick+=1
    if updates:
        writes.extend(first[i] for i in changed)
        retained=np.setdiff1d(np.arange(size),changed)
        chosen=np.r_[rng.choice(changed,known//2),rng.choice(retained,known-known//2)]
        strata=['updated']*(known//2)+['retained']*(known-known//2)
    else:
        chosen=rng.choice(size,known);strata=['retained']*known
    queries=[paths[present[i]].copy() for i in chosen]+[paths[i].copy() for i in unknown]
    answers=[int(values[i]) for i in chosen]+[-1]*absent
    targets=[int(handles[i]) for i in chosen]+[None]*absent
    actual_sources=[sources[i] for i in chosen]+[None]*absent
    strata+=['absent']*absent;order=rng.permutation(query_count)
    return Episode(tuple(writes),tuple(queries[i] for i in order),tuple(answers[i] for i in order),
                   tuple(targets[i] for i in order),tuple(actual_sources[i] for i in order),
                   tuple(strata[i] for i in order),condition)


def prepared_calibration(unit,item):
    writes=tuple((t,h,transform(w,'write'),v,s) for t,h,w,v,s in item.writes)
    queries=np.stack([transform(w,item.condition) for w in item.queries])
    return writes,queries,tuple(zip(item.answers,item.target_sources,strict=True))


def training_sets(unit,nonce):
    result={}
    for size in (16,32):
        contexts,queries,targets=[],[],[]
        for index in range(128):
            item=episode(unit,nonce,'T-fit',size,0,index,8)
            writes,observations,_=prepared_calibration(unit,item)
            lookup={row[1]:i for i,row in enumerate(writes)}
            contexts.append(np.stack([row[2] for row in writes]));queries.append(observations)
            targets.append([lookup.get(handle,size) for handle in item.target_handles])
        result[size]=np.array(contexts),np.array(queries),np.array(targets,dtype=np.int64)
    return result


def episode_hash(item):
    return sha256_json(dict(writes=[(t,h,arrays_hash(w),v,s) for t,h,w,v,s in item.writes],
                           queries=[arrays_hash(w) for w in item.queries],answers=item.answers,
                           handles=item.target_handles,sources=item.target_sources,
                           strata=item.strata,condition=item.condition))
