"""Byte-preserving, finite storage recovery from closed NEXTAI journals only."""
import ctypes
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now


root = Path(__file__).resolve().parents[1]
clone = Path('C:/Users/NATAN/Documents/ChatGPT/NEXTAI-VALIDATION-20261002').resolve()
plan = json.loads((root/'research/plans/ASM01-FROZEN-SOURCE-SCREEN-V1.json').read_text(encoding='utf-8'))
scope = plan['storage_recovery']
started = time.monotonic()
before = shutil.disk_usage(root).free
targets = {}
for project in (root, clone):
    for directory in sorted((project/'research/laboratory/archive').iterdir()):
        if not directory.is_dir() or not re.fullmatch(r'EXP-20261005-000[1-7]-runtime', directory.name):
            continue
        experiment = directory.name.removesuffix('-runtime')
        assert (project/'research/results'/f'{experiment}.json').is_file()
        for file in directory.rglob('*'):
            if file.is_file() and not file.is_symlink() and file.suffix.lower() in {'.json','.jsonl','.txt','.log'} and file.stat().st_size >= 262144:
                assert file.resolve().is_relative_to(directory.resolve())
                targets[file] = dict(bytes=file.stat().st_size, sha256=sha256_file(file))
for directory in sorted((clone/'research/tmp').iterdir()):
    if not directory.is_dir() or not re.fullmatch(r'EXP-20261005-000[1-7]',directory.name):
        continue
    assert (clone/'research/results'/f'{directory.name}.json').is_file()
    for file in directory.rglob('*'):
        if file.is_file() and not file.is_symlink() and file.suffix.lower() in {'.json','.jsonl','.txt','.log'} and file.stat().st_size >= 262144:
            assert file.resolve().is_relative_to(directory.resolve())
            targets[file] = dict(bytes=file.stat().st_size,sha256=sha256_file(file))
assert len(targets) <= scope['file_count_cap']
assert sum(t['bytes'] for t in targets.values()) <= scope['total_logical_bytes_cap']
assert targets
proof = dict(created_at=utc_now(),plan_sha256=sha256_file(root/'research/plans/ASM01-FROZEN-SOURCE-SCREEN-V1.json'),
             files={str(p):v for p,v in targets.items()},disk_free_before=before,files_deleted=0)
atomic_write_json(root/'research/reviews/ASM01-CLOSED-ARCHIVE-COMPRESSION-PROOF-V1.json',proof)
api = ctypes.WinDLL('kernel32',use_last_error=True).GetCompressedFileSizeW
api.argtypes=[ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_ulong)]
api.restype=ctypes.c_ulong
def allocated(path):
    high=ctypes.c_ulong();low=api(str(path),ctypes.byref(high))
    if low==0xffffffff and ctypes.get_last_error():
        raise ctypes.WinError(ctypes.get_last_error())
    return (high.value<<32)+low
before_allocated=sum(allocated(p) for p in targets)
items=list(targets)
for first in range(0,len(items),80):
    command=['compact.exe','/C','/EXE:LZX','/I','/Q',*[str(p) for p in items[first:first+80]]]
    response=subprocess.run(command,capture_output=True,timeout=90)
    assert response.returncode==0, response.stdout+response.stderr
for p,record in targets.items():
    assert p.is_file() and p.stat().st_size==record['bytes'] and sha256_file(p)==record['sha256']
after=shutil.disk_usage(root).free
receipt=dict(created_at=utc_now(),proof_sha256=sha256_file(root/'research/reviews/ASM01-CLOSED-ARCHIVE-COMPRESSION-PROOF-V1.json'),
             logical_bytes=sum(t['bytes'] for t in targets.values()),files_verified=len(targets),files_deleted=0,
             allocated_before=before_allocated,allocated_after=sum(allocated(p) for p in targets),
             disk_free_before=before,disk_free_after=after,space_reclaimed_bytes=after-before,
             elapsed_seconds=time.monotonic()-started,all_paths_and_content_bytes_preserved=True,
             source_states_and_WT_not_touched=True,compression='Transparent NTFS LZX; future reading/decompression stays in measured full cost')
atomic_write_json(root/'research/reviews/ASM01-CLOSED-ARCHIVE-COMPRESSION-V1.receipt.json',receipt)
print(json.dumps(receipt),flush=True)
