"""One bounded publisher acquisition; decode only ten preregistered screen writers."""
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import subprocess
import time
import urllib.request
import zlib

import numpy as np

from nextai_autoresearch.asm01_task import SCREEN_WRITERS, parse_native_sample, arrays_hash
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now


def archive_index(path,expanded_cap):
    """Read RAR4 headers/sizes only; compressed coordinate payloads are skipped."""
    records=[];total=0;size=path.stat().st_size
    with path.open('rb') as stream:
        if stream.read(7)!=b'Rar!\x1a\x07\x00':
            raise ValueError('Only documented bounded RAR4 intake is supported')
        while stream.tell()<size:
            raw=stream.read(7)
            if len(raw)!=7:
                raise ValueError('Truncated RAR header')
            crc,kind,flags,length=struct.unpack('<HBHH',raw)
            if length<7 or length>65535:
                raise ValueError('Unsafe RAR header size')
            header=raw+stream.read(length-7)
            if len(header)!=length or (zlib.crc32(header[2:])&0xffff)!=crc:
                raise ValueError('RAR header CRC/length')
            packed=0
            if kind==0x74:
                if length<32 or flags&(0x4|0x100):
                    raise ValueError('Encrypted/large/invalid RAR file')
                packed,unpacked,_,_,_,_,_,namesize,_=struct.unpack('<IIBIIBBHI',header[7:32])
                if 32+namesize>length:
                    raise ValueError('RAR filename outside header')
                name=header[32:32+namesize].split(b'\0',1)[0].decode('ascii').replace('\\','/')
                native=PurePosixPath(name)
                if native.is_absolute() or '..' in native.parts or ':' in name or not name:
                    raise ValueError('Unsafe archive path')
                directory=(flags&0xe0)==0xe0
                if not directory:
                    total+=unpacked
                    records.append(dict(path=name,bytes=unpacked))
                    if total>expanded_cap:
                        raise ValueError('RAR expanded footprint cap')
            elif flags&0x8000:
                if length<11:
                    raise ValueError('Missing RAR additional data size')
                packed=struct.unpack('<I',header[7:11])[0]
            if stream.tell()+packed>size:
                raise ValueError('RAR payload outside preserved archive')
            stream.seek(packed,1)
            if kind==0x7b:
                if stream.tell()!=size:
                    raise ValueError('Unexpected trailing RAR data')
                break
    if len({row['path'] for row in records})!=len(records):
        raise ValueError('Duplicate archive filenames')
    return records,total


def identities(records):
    samples={}
    for row in records:
        name=PurePosixPath(row['path']).name
        match=re.fullmatch(r'([0-9]+)\.([0-9]+)\.txt',name,flags=re.IGNORECASE)
        if match:
            character,writer=map(int,match.groups())
            if not 1<=character<=183 or not 1<=writer<=45 or (writer,character) in samples:
                raise ValueError('Duplicate/out-of-range native identity')
            if row['bytes']>262144:
                raise ValueError('Native sample footprint cap')
            samples[writer,character]=row['path']
    if set(samples)!={(writer,character) for writer in range(1,46) for character in range(1,184)}:
        raise ValueError('Publisher must contain45writers x183unique native samples')
    return samples


def main():
    root=Path(__file__).resolve().parents[1]
    study_path=root/'research/plans/ASM01-FROZEN-SOURCE-SCREEN-V1.json'
    task_path=root/'research/plans/ASM01-PROSPECTIVE-NATIVE-TASK-V1.json'
    study=json.loads(study_path.read_text(encoding='utf-8'));task=json.loads(task_path.read_text(encoding='utf-8'))
    rules=task['intake'];receipt_path=root/'research/data_manifests/ASM01-ACQUISITION-V1.json'
    assert not receipt_path.exists(), 'Intake consumed; no retry'
    assert not any((root/p).exists() for p in ('STOP','PAUSE','research/run.lock'))
    before=shutil.disk_usage(root).free
    if before-rules['maximum_two_root_total_footprint_bytes']<rules['minimum_free_bytes_after_operation']:
        raise RuntimeError(f'Disk blocker: {before} free bytes; footprint335544320; floor10737418240')
    directory=root/'research/data/asm01_native_v1';directory.mkdir(parents=True,exist_ok=True)
    archive=directory/'publisher.rar';partial=directory/'publisher.rar.partial'
    assert not archive.exists() and not partial.exists(), 'Existing acquisition bytes; no retry'
    started=time.perf_counter()
    receipt=dict(created_at=utc_now(),study_sha256=sha256_file(study_path),task_contract_sha256=sha256_file(task_path),
                 url=rules['archive_url'],license='CC BY4.0',license_url='https://creativecommons.org/licenses/by/4.0/',
                 attribution='Baruah and Hazarika(2015), UCI, DOI10.24432/C50C8Q; derived trajectory instance memory, not OCR.',
                 free_space_before_bytes=before,footprint_bound_bytes=rules['maximum_two_root_total_footprint_bytes'],
                 no_download_retry=True,new_registration_or_model_fit=False,complete=False)
    try:
        request=urllib.request.Request(rules['archive_url'],headers={'User-Agent':'NEXTAI licensed local research'})
        count=0
        with urllib.request.urlopen(request,timeout=45) as response,partial.open('xb') as output:
            declared=response.headers.get('Content-Length')
            if declared and int(declared)>rules['download_stream_cap_bytes']:
                raise ValueError('Declared publisher payload exceeds cap')
            receipt['resolved_url']=response.url
            while chunk:=response.read(1024**2):
                count+=len(chunk)
                if count>rules['download_stream_cap_bytes']:
                    raise ValueError('Streamed publisher payload exceeds cap')
                output.write(chunk)
        partial.rename(archive)
        receipt.update(download_bytes=count,publisher_sha256=sha256_file(archive),download_seconds=time.perf_counter()-started)
        records,expanded=archive_index(archive,rules['archive_manifest_and_extraction_cap_bytes'])
        samples=identities(records)
        receipt.update(archive_index_sha256=__import__('hashlib').sha256(json.dumps(records,sort_keys=True).encode()).hexdigest(),
                       expanded_archive_bytes=expanded,native_files=len(samples),writer_count=45,samples_per_writer=183)
        selected=[samples[w,c] for w in SCREEN_WRITERS for c in range(1,184)]
        listing=directory/'selected-screen-members.txt';listing.write_text('\n'.join(selected)+'\n',encoding='ascii',newline='\n')
        extracted=directory/'screen-text';extracted.mkdir()
        # The installed libarchive decompresses only requested outputs. Future members are never extracted or numerically parsed.
        response=subprocess.run(['tar.exe','-xf',str(archive),'-C',str(extracted),'-T',str(listing)],capture_output=True,timeout=120)
        (directory/'extraction.stdout.txt').write_bytes(response.stdout);(directory/'extraction.stderr.txt').write_bytes(response.stderr)
        if response.returncode!=0:
            raise ValueError(f'Bounded native archive extraction failed(exit{response.returncode}); preserved native stderr')
        actual={p.relative_to(extracted).as_posix() for p in extracted.rglob('*') if p.is_file()}
        if actual!=set(selected):
            raise ValueError('Extraction selected-file scope mismatch')
        arrays={};hashes={};sample_hashes={};content_seen=set()
        for writer in SCREEN_WRITERS:
            paths=[];offsets=[0]
            for character in range(1,184):
                path=(extracted/samples[writer,character]).resolve()
                if not path.is_relative_to(extracted.resolve()) or path.is_symlink() or path.stat().st_size>262144:
                    raise ValueError('Unsafe native sample path/size')
                value=parse_native_sample(path.read_bytes())
                digest=arrays_hash(value)
                if digest in content_seen:
                    raise ValueError('Duplicate selected native trajectory; no sample replacement')
                content_seen.add(digest);paths.append(value);offsets.append(offsets[-1]+len(value))
                sample_hashes[f'{writer}:{character}']=sha256_file(path)
            points=np.concatenate(paths);cuts=np.asarray(offsets,dtype=np.int64)
            rows=np.column_stack((np.arange(1,184),np.full(183,writer))).astype(np.int64)
            hashes[str(writer)]=arrays_hash(points,cuts,rows)
            arrays.update({f'points_{writer}':points,f'offsets_{writer}':cuts,f'rows_{writer}':rows})
        dataset=directory/'screen.npz'
        with dataset.open('xb') as output:
            np.savez_compressed(output,**arrays)
        receipt.update(complete=True,converted_writers=list(SCREEN_WRITERS),converted_writer_hashes=hashes,
                       sample_text_sha256=sample_hashes,dataset_path=dataset.relative_to(root).as_posix(),
                       dataset_sha256=sha256_file(dataset),dataset_bytes=dataset.stat().st_size,
                       no_future_writer_coordinates_read=True,future_writer_members_not_extracted=True,
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
