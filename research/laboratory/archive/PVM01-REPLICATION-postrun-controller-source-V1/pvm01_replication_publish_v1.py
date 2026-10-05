from pathlib import Path
import gzip,json,shutil,subprocess,time
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
b=Path.cwd();eid='EXP-20261005-0002';native=b/f'research/results/{eid}.json';bundle=native.with_suffix('.json.gz')
assert native.is_file() and not bundle.exists()
before=shutil.disk_usage(b).free;footprint=3*native.stat().st_size+64*1024**2
assert before-footprint>10*1024**3
script=b/'scripts/restore_pvm01_replication_result.py';assert not script.exists()
script.write_text('''"""Restore the exact independent-replication record with the frozen lossless restorer."""
from pathlib import Path
import sys
import restore_pvm01_transport_result as frozen

if __name__ == "__main__":
    frozen.ID = "EXP-20261005-0002"
    frozen.RELATIVE = f"research/results/{frozen.ID}.json"
    frozen.main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
''',encoding='utf-8',newline='\n')
started=time.monotonic()
with bundle.open('xb') as target,gzip.GzipFile(filename='',mode='wb',compresslevel=6,mtime=0,fileobj=target) as compressed,native.open('rb') as source:
    shutil.copyfileobj(source,compressed,1024*1024)
assert bundle.stat().st_size<99_000_000
metadata={'created_at':utc_now(),'schema_version':2,'experiment_id':eid,'native_path':native.relative_to(b).as_posix(),'bundle_path':bundle.relative_to(b).as_posix(),'native_sha256':sha256_file(native),'bundle_sha256':sha256_file(bundle),'native_bytes':native.stat().st_size,'bundle_bytes':bundle.stat().st_size,'codec':'lossless gzip/mtime0','native_result_unmodified':True,'restoration_command':'uv run --no-sync python scripts/restore_pvm01_replication_result.py','restoration_script_sha256':sha256_file(script),'frozen_shared_restorer_sha256':sha256_file(b/'scripts/restore_pvm01_transport_result.py'),'all_trials_predictions_failures_and_costs_included':True}
publication=b/f'research/laboratory/{eid}-publication-V2.json';assert not publication.exists();atomic_write_json(publication,metadata)
out=b/'research/tmp/PVM01-REPLICATION-publication-conformance-V1';out.mkdir(parents=True,exist_ok=False);commands=[]
bad=b'Corrupt public existing-record fixture; preserve these bytes'
for label in ('good','bad-existing'):
    root=out/label;dest=root/'research/results';dest.mkdir(parents=True);lab=root/'research/laboratory';lab.mkdir()
    shutil.copyfile(publication,lab/publication.name);shutil.copyfile(bundle,dest/bundle.name)
    if label=='bad-existing':(dest/native.name).write_bytes(bad)
    prefix=b/f'research/reviews/PVM01-REPLICATION-publication-{label}-V1'
    with prefix.with_suffix('.stdout.txt').open('xb') as stdout,prefix.with_suffix('.stderr.txt').open('xb') as stderr:
        run=subprocess.run(['uv','run','--no-sync','python',str(script),str(root)],cwd=b,stdout=stdout,stderr=stderr)
    if label=='good':assert run.returncode==0 and sha256_file(dest/native.name)==metadata['native_sha256']
    else:assert run.returncode!=0 and (dest/native.name).read_bytes()==bad
    commands.append({'label':label,'returncode':run.returncode,'outputs':{p.name:sha256_file(p) for p in [prefix.with_suffix('.stdout.txt'),prefix.with_suffix('.stderr.txt')]}})
p=b/'.gitignore';raw=p.read_bytes();snapshot=json.loads((b/'research/checks/PVM01-REPLICATION-history-snapshot-V1.json').read_text());assert sha256_file(p)==snapshot['raw_files']['.gitignore']
archive=b/f'research/laboratory/archive/{eid}-publication-source';archive.mkdir(parents=True,exist_ok=False);(archive/'root.gitignore.before.raw').write_bytes(raw);shutil.copyfile(script,archive/script.name)
p.write_bytes(raw+f'\n# Native independent replica is versioned losslessly as gzip plus its exact hash.\n/research/results/{eid}.json\n'.encode())
assert sha256_file(native)==metadata['native_sha256']
after=shutil.disk_usage(b).free;assert after>=10*1024**3
atomic_write_json(b/'research/reviews/PVM01-REPLICATION-publication-conformance-V1.json',{'created_at':utc_now(),'commands':commands,'native_hash':metadata['native_sha256'],'lossless_restoration_exact':True,'existing_record_never_overwritten':True,'new_fit_seed_scoring':False,'free_space_before':before,'bounded_additional_footprint':footprint,'free_space_after':after,'wall_seconds':time.monotonic()-started})
print('Complete native independent result losslessly versioned; exact restoration/non-overwrite PASS',metadata['native_bytes'],metadata['bundle_bytes'],flush=True)
