"""Prospectively corrected archive membership; reuse preserved bytes, no download retry."""
from pathlib import Path,PurePosixPath
import json
import re
import shutil
import subprocess
import time

import numpy as np

if __package__:
    from .acquire_asm01 import archive_index
else:
    from acquire_asm01 import archive_index
from nextai_autoresearch.asm01_task import SCREEN_WRITERS,parse_native_sample,arrays_hash
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now


def canonical_identities(records,exception):
    samples={};excluded=[]
    for row in records:
        path=PurePosixPath(row['path'])
        match=re.fullmatch(r'([0-9]+)\.([0-9]+)\.txt',path.name,re.IGNORECASE)
        if match is None:
            if path.name!='Data_Table.pdf':
                raise ValueError('Unexpected publisher non-native member')
            continue
        character,writer=map(int,match.groups())
        folder=re.fullmatch(r'W([0-9]+)',path.parent.name)
        if folder is None or int(folder[1])!=writer:
            if row!=exception:
                raise ValueError('Unregistered filename/folder disagreement')
            excluded.append(row);continue
        if not 1<=character<=183 or not 1<=writer<=45 or (writer,character) in samples or row['bytes']>262144:
            raise ValueError('Duplicate/missing/out-of-bounds canonical native identity')
        samples[writer,character]=row['path']
    if excluded!=[exception] or set(samples)!={(w,c) for w in range(1,46) for c in range(1,184)}:
        raise ValueError('Exactly45writers x183 canonical samples and one frozen foreign member required')
    return samples


def main():
    root=Path(__file__).resolve().parents[1]
    study_path=root/'research/plans/ASM01-FROZEN-SOURCE-SCREEN-V2.json'
    task_path=root/'research/plans/ASM01-CANONICAL-NATIVE-TASK-V2.json'
    study=json.loads(study_path.read_text(encoding='utf-8'));task=json.loads(task_path.read_text(encoding='utf-8'))
    rules=task['intake'];receipt_path=root/'research/data_manifests/ASM01-ACQUISITION-V2.json'
    assert not receipt_path.exists(),'V2 intake consumed; no retry'
    assert not any((root/p).exists() for p in ('STOP','PAUSE','research/run.lock'))
    before=shutil.disk_usage(root).free
    if before-rules['maximum_two_root_total_footprint_bytes']<rules['minimum_free_bytes_after_operation']:
        raise RuntimeError(f'Disk blocker: {before} free;335544320 footprint;10737418240floor')
    directory=root/'research/data/asm01_native_v1';archive=directory/'publisher.rar'
    failed=json.loads((root/'research/data_manifests/ASM01-ACQUISITION-V1.json').read_text(encoding='utf-8'))
    assert failed['complete'] is False and failed['error']=='ValueError: Duplicate/out-of-range native identity'
    assert sha256_file(archive)==failed['publisher_sha256']==rules['publisher_sha256']
    started=time.perf_counter()
    receipt=dict(created_at=utc_now(),study_sha256=sha256_file(study_path),task_contract_sha256=sha256_file(task_path),
                 publisher_sha256=rules['publisher_sha256'],license='CC BY4.0',license_url='https://creativecommons.org/licenses/by/4.0/',
                 attribution='Baruah and Hazarika(2015), UCI, DOI10.24432/C50C8Q; native trajectory instance memory, not OCR.',
                 preserved_failed_V1_receipt_sha256=sha256_file(root/'research/data_manifests/ASM01-ACQUISITION-V1.json'),
                 no_archive_reacquisition=True,new_download_bytes=0,no_model_fit_or_scoring=True,complete=False,
                 free_space_before_bytes=before,footprint_bound_bytes=rules['maximum_two_root_total_footprint_bytes'])
    try:
        records,expanded=archive_index(archive,rules['archive_manifest_and_extraction_cap_bytes'])
        samples=canonical_identities(records,rules['excluded_foreign_member'])
        receipt.update(archive_index_sha256=__import__('hashlib').sha256(json.dumps(records,sort_keys=True).encode()).hexdigest(),
                       expanded_archive_bytes=expanded,native_legal_files=len(samples),writer_count=45,samples_per_writer=183,
                       excluded_foreign_member=rules['excluded_foreign_member'],excluded_foreign_member_numeric_reads=0)
        selected=[samples[w,c] for w in SCREEN_WRITERS for c in range(1,184)]
        listing=directory/'selected-screen-members-v2.txt';listing.write_text('\n'.join(selected)+'\n',encoding='ascii',newline='\n')
        extracted=directory/'screen-text-v2';extracted.mkdir()
        response=subprocess.run(['tar.exe','-xf',str(archive),'-C',str(extracted),'-T',str(listing)],capture_output=True,timeout=120)
        (directory/'extraction-v2.stdout.txt').write_bytes(response.stdout);(directory/'extraction-v2.stderr.txt').write_bytes(response.stderr)
        if response.returncode:
            raise ValueError(f'Native extraction failed(exit{response.returncode}); stderr preserved')
        if {p.relative_to(extracted).as_posix() for p in extracted.rglob('*') if p.is_file()}!=set(selected):
            raise ValueError('Native selected-file extraction scope mismatch')
        arrays={};hashes={};sample_hashes={};seen=set()
        for writer in SCREEN_WRITERS:
            paths=[];offsets=[0]
            for character in range(1,184):
                path=(extracted/samples[writer,character]).resolve()
                if not path.is_relative_to(extracted.resolve()) or path.is_symlink() or path.stat().st_size>262144:
                    raise ValueError('Unsafe selected native path/size')
                value=parse_native_sample(path.read_bytes());digest=arrays_hash(value)
                if digest in seen:
                    raise ValueError('Duplicate selected native trajectory; no sample replacement')
                seen.add(digest);paths.append(value);offsets.append(offsets[-1]+len(value))
                sample_hashes[f'{writer}:{character}']=sha256_file(path)
            points=np.concatenate(paths);cuts=np.asarray(offsets,dtype=np.int64)
            rows=np.column_stack((np.arange(1,184),np.full(183,writer))).astype(np.int64)
            hashes[str(writer)]=arrays_hash(points,cuts,rows)
            arrays.update({f'points_{writer}':points,f'offsets_{writer}':cuts,f'rows_{writer}':rows})
        dataset=directory/'screen-v2.npz'
        with dataset.open('xb') as output:
            np.savez_compressed(output,**arrays)
        receipt.update(complete=True,converted_writers=list(SCREEN_WRITERS),converted_writer_hashes=hashes,
                       sample_text_sha256=sample_hashes,dataset_path=dataset.relative_to(root).as_posix(),dataset_sha256=sha256_file(dataset),
                       dataset_bytes=dataset.stat().st_size,no_future_writer_coordinates_read=True,future_writer_members_not_extracted=True,
                       no_character_labels_or_Data_Table_read_by_methods=True,within_identity_views_are_dependent=True)
    except BaseException as exc:
        receipt.update(complete=False,error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        receipt.update(full_intake_wall_seconds=time.perf_counter()-started,free_space_after_bytes=shutil.disk_usage(root).free)
        atomic_write_json(receipt_path,receipt)
        print(json.dumps({k:v for k,v in receipt.items() if k not in {'sample_text_sha256','converted_writer_hashes'}}),flush=True)


if __name__=='__main__':
    main()
