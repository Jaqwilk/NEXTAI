"""Canonical intake binding; the complete native descriptor/episode math is unchanged."""
import numpy as np
from .asm01_task import (SCREEN_WRITERS, parse_native_sample, transform, pairs, episode, prepared_calibration, training_sets, episode_hash, arrays_hash, rng_for)
from .utils import load_json, sha256_file


def load_unit(root,index,nonce):
    if index not in range(5):
        raise ValueError('Only the five fixed ASM screen pairs are accessible')
    manifest_path=root/'research/data_manifests/ASM01-ACQUISITION-V2.json'
    manifest=load_json(manifest_path)
    task=root/'research/plans/ASM01-CANONICAL-NATIVE-TASK-V2.json'
    study=root/'research/plans/ASM01-FROZEN-SOURCE-SCREEN-V2.json'
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
