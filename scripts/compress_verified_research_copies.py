"""Preserve every byte/path while compressing verified local result copies on NTFS."""
from pathlib import Path
import json
import shutil
import subprocess
import time

from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now


root=Path(__file__).resolve().parents[1]
proof=json.loads((root/'research/reviews/FAMILY2-VERIFIED-TEMP-CLEANUP-V1.json').read_text())
clone=Path('C:/Users/NATAN/Documents/ChatGPT/NEXTAI-VALIDATION-20261002').resolve()
targets={}
for path, digest in proof['authoritative_native_and_bundle_hashes'].items():
    p=Path(path).resolve()
    if p.suffix=='.json':
        assert p.parent in {(root/'research/results').resolve(),(clone/'research/results').resolve()}
        targets[p]=digest
for item in proof['paths']:
    base=Path(item['path']).resolve()
    assert base.parent==(clone/'research/tmp').resolve()
    for relative, record in item['files'].items():
        p=(base/relative).resolve()
        assert p.is_relative_to(base)
        if p.suffix=='.json' and record['bytes']>1000000:
            targets[p]=record['sha256']
for p, digest in targets.items():
    assert sha256_file(p)==digest
started=time.monotonic(); before=shutil.disk_usage(root).free; results=[]
for p in targets:
    response=subprocess.run(['compact.exe','/C','/EXE:LZX','/I','/Q',str(p)],capture_output=True,timeout=20)
    assert response.returncode==0, response.stdout+response.stderr
    results.append(dict(path=str(p),returncode=response.returncode,output=response.stdout.decode(errors='replace')))
for p,digest in targets.items():
    assert sha256_file(p)==digest
after=shutil.disk_usage(root).free
receipt=dict(created_at=utc_now(),files_verified=len(targets),content_sha256={str(p):d for p,d in targets.items()},
             disk_free_before=before,disk_free_after=after,space_reclaimed_bytes=after-before,
             elapsed_seconds=time.monotonic()-started,files_deleted=0,all_paths_and_bytes_preserved=True,
             scope='Only the 14 preserved native PVM/HAR results and verified large JSON copies in completed restoration fixtures; no WT files, source states, journals, other projects or OS settings',
             compression='NTFS transparent LZX. Future filesystem read/decompression cost remains inside full measured boundary; historical measured outcomes are unchanged.',results=results)
atomic_write_json(root/'research/reviews/FAMILY2-NTFS-COMPRESSION-V1.json',receipt)
print(json.dumps({k:v for k,v in receipt.items() if k not in {'results','content_sha256'}}))
