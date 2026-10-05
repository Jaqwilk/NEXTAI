"""Diagnose native archive identity failure using filenames/sizes only, no coordinates."""
from collections import Counter
from pathlib import Path, PurePosixPath
import json
import re

from acquire_asm01 import archive_index
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now

root=Path(__file__).resolve().parents[1]
clone=Path('C:/Users/NATAN/Documents/ChatGPT/NEXTAI-VALIDATION-20261002')
manifest=json.loads((clone/'research/data_manifests/ASM01-ACQUISITION-V1.json').read_text(encoding='utf-8'))
assert manifest['complete'] is False and manifest['error']=='ValueError: Duplicate/out-of-range native identity'
archive=clone/'research/data/asm01_native_v1/publisher.rar'
assert sha256_file(archive)==manifest['publisher_sha256']
records,total=archive_index(archive,134217728)
native=[];other=[];pairs=Counter();writers=Counter();characters=Counter();folders=Counter()
for row in records:
    match=re.fullmatch(r'([0-9]+)\.([0-9]+)\.txt',PurePosixPath(row['path']).name,re.IGNORECASE)
    if match:
        character,writer=map(int,match.groups());native.append(dict(row,character=character,writer=writer))
        pairs[writer,character]+=1;writers[writer]+=1;characters[character]+=1;folders[str(PurePosixPath(row['path']).parent)]+=1
    else:
        other.append(row)
outside=[row for row in native if not 1<=row['character']<=183 or not 1<=row['writer']<=45]
expected={(w,c) for w in range(1,46) for c in range(1,184)}
actual=set(pairs)
receipt=dict(created_at=utc_now(),study_sha256=sha256_file(root/'research/plans/ASM01-FROZEN-SOURCE-SCREEN-V1.json'),
             acquisition_receipt_sha256=sha256_file(clone/'research/data_manifests/ASM01-ACQUISITION-V1.json'),
             publisher_sha256=manifest['publisher_sha256'],archive_files=len(records),expanded_bytes=total,
             native_files=len(native),native_unique_pairs=len(actual),writer_file_counts=dict(sorted(writers.items())),
             character_file_counts=dict(sorted(characters.items())),folder_counts=dict(sorted(folders.items())),
             duplicate_pairs=[dict(writer=w,character=c,copies=n) for (w,c),n in sorted(pairs.items()) if n!=1],
             out_of_range_count=len(outside),out_of_range_filename_examples=outside[:12],
             missing_expected_pair_count=len(expected-actual),missing_expected_pair_examples=[dict(writer=w,character=c) for w,c in sorted(expected-actual)[:12]],
             unexpected_pair_count=len(actual-expected),other_members=other,
             numeric_coordinate_payloads_opened=0,no_archive_reacquisition=True,no_model_fit_or_scoring=True,
             archive_index_sha256=__import__('hashlib').sha256(json.dumps(records,sort_keys=True).encode()).hexdigest())
atomic_write_json(root/'research/reviews/ASM01-INTAKE-HEADER-DIAGNOSIS-V1.json',receipt)
print(json.dumps({k:v for k,v in receipt.items() if k not in {'character_file_counts','folder_counts'}}),flush=True)
