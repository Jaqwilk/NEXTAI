from pathlib import Path
import json, shutil, subprocess, time
from nextai_autoresearch.utils import atomic_write_json, sha256_file, utc_now
b=Path.cwd();eid='EXP-20261005-0004'
native=b/f'research/results/{eid}.json';bundle=native.with_suffix('.json.gz')
publication=b/f'research/laboratory/{eid}-publication-V2.json';metadata=json.loads(publication.read_text(encoding='utf-8'))
script=b/'scripts/restore_pvm01_confirmation_result.py'
for path,key in ((native,'native_sha256'),(bundle,'bundle_sha256'),(script,'restoration_script_sha256'),(b/'scripts/restore_pvm01_transport_result.py','frozen_shared_restorer_sha256')):
    assert sha256_file(path)==metadata[key]
failed=json.loads((b/'research/reviews/PVM01-CONFIRMATION-publication-V1.json').read_text(encoding='utf-8'))
assert failed['result']['returncode']==1 and failed['result']['exit_job_active_process_count']==0 and not failed['result']['exit_live_descendant_pids']
old_ignore=b/'.gitignore';raw=old_ignore.read_bytes()
snapshot=json.loads((b/'research/checks/PVM01-CONFIRMATION-history-snapshot-V1.json').read_text(encoding='utf-8'))
assert sha256_file(old_ignore)==snapshot['raw_files']['.gitignore']
before=shutil.disk_usage(b).free;footprint=3*native.stat().st_size+64*1024**2
assert before-footprint>=10*1024**3
out=b/'research/tmp/c315p2';assert not out.exists()
addendum=b/'research/plans/PVM01-CONFIRMATION-PUBLICATION-PATH-ADDENDUM-V1.json'
assert not addendum.exists()
atomic_write_json(addendum,{'created_at':utc_now(),'scope':'No-scoring technical publication conformance completion','failed_receipt':'research/reviews/PVM01-CONFIRMATION-publication-V1.json','failed_receipt_sha256':sha256_file(b/'research/reviews/PVM01-CONFIRMATION-publication-V1.json'),'cause':'Windows fixture destination was 261 characters, beyond the normal file-open boundary','correction':'New distinct shorter ignored fixture directory research/tmp/c315p2; verify and reuse already immutable exact bundle, native result, publication metadata and restoration script','controller_path':'research/tmp/pvm01_confirmation_publication_completion_v2.py','controller_sha256':sha256_file(Path(__file__)),'failed_raw_fixture_preserved':True,'completed_metadata_and_restorer_unchanged':True,'all_costs_charged_within_unchanged_3600s_aux_cap':True,'new_registration_data_model_fit_scoring_or_paid_retry':False,'metrics_gates_source_scientific_controls_unchanged':True})
out.mkdir();commands=[];bad=b'Corrupt existing-record fixture; these exact bytes must be preserved'
rows=[x['execution'] for x in json.loads(native.read_text(encoding='utf-8'))['candidates'] if x.get('execution',{}).get('resource_peaks_path')]
assert len(rows)==85
started=time.monotonic()
for label in ('good','bad-existing','bad-resource-existing'):
    root=out/label;dest=root/'research/results';dest.mkdir(parents=True);lab=root/'research/laboratory';lab.mkdir()
    shutil.copyfile(publication,lab/publication.name);shutil.copyfile(bundle,dest/bundle.name)
    for row in rows:
        relative=Path(row['resource_peaks_path']);source=b/f'research/laboratory/archive/{eid}-runtime'/relative
        target=root/f'research/laboratory/archive/{eid}-runtime'/relative
        assert len(str(target))<250
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    if label=='bad-existing':(dest/native.name).write_bytes(bad)
    if label=='bad-resource-existing':
        shutil.copyfile(native,dest/native.name)
        resource=root/rows[0]['resource_peaks_path'];resource.parent.mkdir(parents=True,exist_ok=True);resource.write_bytes(bad)
    prefix=b/f'research/reviews/PVM01-CONFIRMATION-publication-{label}-V2'
    with prefix.with_suffix('.stdout.txt').open('xb') as stdout,prefix.with_suffix('.stderr.txt').open('xb') as stderr:
        run=subprocess.run(['uv','run','--no-sync','python',str(script),str(root)],cwd=b,stdout=stdout,stderr=stderr)
    if label=='good':
        assert run.returncode==0 and sha256_file(dest/native.name)==metadata['native_sha256']
        assert all(sha256_file(root/row['resource_peaks_path'])==row['resource_peaks_sha256'] for row in rows)
    elif label=='bad-existing':assert run.returncode!=0 and (dest/native.name).read_bytes()==bad
    else:
        assert run.returncode!=0 and resource.read_bytes()==bad and sha256_file(dest/native.name)==metadata['native_sha256']
        assert len(list((root/f'research/tmp/{eid}').glob('*.resources.json')))==1
    commands.append({'label':label,'returncode':run.returncode,'raw_outputs':{p.name:sha256_file(p) for p in (prefix.with_suffix('.stdout.txt'),prefix.with_suffix('.stderr.txt'))}})
archive=b/f'research/laboratory/archive/{eid}-publication-source';assert not archive.exists();archive.mkdir(parents=True)
(archive/'root.gitignore.before.raw').write_bytes(raw);shutil.copyfile(script,archive/script.name)
old_ignore.write_bytes(raw+f'\n# Native independent-confirmation record is versioned losslessly as gzip plus its exact hash.\n/research/results/{eid}.json\n'.encode())
assert sha256_file(native)==metadata['native_sha256'] and sha256_file(bundle)==metadata['bundle_sha256']
after=shutil.disk_usage(b).free;assert after>=10*1024**3
receipt=b/'research/reviews/PVM01-CONFIRMATION-publication-conformance-V2.json';assert not receipt.exists()
atomic_write_json(receipt,{'created_at':utc_now(),'commands':commands,'native_hash':metadata['native_sha256'],'lossless_restoration_exact':True,'all85_trusted_journals_restored_exactly':True,'existing_native_and_resource_records_never_overwritten':True,'failed_V1_preserved':'research/reviews/PVM01-CONFIRMATION-publication-V1.json','technical_path_addendum':addendum.relative_to(b).as_posix(),'new_fit_seed_scoring':False,'free_space_before':before,'bounded_additional_footprint':footprint,'free_space_after':after,'wall_seconds':time.monotonic()-started})
print('Exact result and all85 saved resource journals restored; both non-overwrite fixtures PASS',metadata['native_bytes'],metadata['bundle_bytes'],flush=True)