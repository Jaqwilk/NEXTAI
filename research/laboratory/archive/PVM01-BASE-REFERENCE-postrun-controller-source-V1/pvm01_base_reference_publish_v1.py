from pathlib import Path
import gzip,json,shutil,subprocess,time
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
b=Path.cwd();eid='EXP-20261005-0005';native=b/f'research/results/{eid}.json';bundle=native.with_suffix('.json.gz')
assert native.is_file() and not bundle.exists()
before=shutil.disk_usage(b).free;footprint=3*native.stat().st_size+64*1024**2
assert before-footprint>10*1024**3
script=b/'scripts/restore_pvm01_base_reference_result.py';assert not script.exists()
script.write_text('''"""Restore the exact independent-confirmation record with the frozen lossless restorer."""
from pathlib import Path
import json
import shutil
import sys
import restore_pvm01_transport_result as frozen

if __name__ == "__main__":
    frozen.ID = "EXP-20261005-0005"
    frozen.RELATIVE = f"research/results/{frozen.ID}.json"
    root = (Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]).resolve()
    frozen.main(root)
    result = json.loads((root/frozen.RELATIVE).read_text(encoding="utf-8"))
    jobs = []
    for outcome in result["candidates"]:
        execution = outcome.get("execution") or {}
        if "resource_peaks_path" not in execution:
            continue
        relative = Path(execution["resource_peaks_path"])
        expected = Path("research/tmp") / frozen.ID
        if relative.parent != expected or relative.suffixes[-2:] != [".resources", ".json"]:
            raise ValueError("Trusted resource journal path mismatch")
        source = (root/f"research/laboratory/archive/{frozen.ID}-runtime"/relative).resolve()
        target = (root/relative).resolve()
        if not source.is_relative_to(root) or not target.is_relative_to(root) or frozen.digest(source) != execution["resource_peaks_sha256"]:
            raise ValueError("Archived trusted resource journal binding changed")
        if target.exists():
            if frozen.digest(target) != execution["resource_peaks_sha256"]:
                raise ValueError("Existing resource journal differs; preserved without overwrite")
        else:
            jobs.append((source,target))
    footprint = sum(source.stat().st_size for source,target in jobs)
    if footprint > 64*1024**2 or shutil.disk_usage(root).free-footprint < 10*1024**3:
        raise OSError("Resource hydration exceeds bounded footprint or free-space reserve")
    for source,target in jobs:
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("xb") as stream:
            stream.write(source.read_bytes())
        if frozen.digest(target) != frozen.digest(source):
            raise ValueError("Hydrated resource journal hash mismatch")
    print("Exact saved resource journals available for frozen reanalysis:",len(jobs))
''',encoding='utf-8',newline='\n')
started=time.monotonic()
with bundle.open('xb') as target,gzip.GzipFile(filename='',mode='wb',compresslevel=6,mtime=0,fileobj=target) as compressed,native.open('rb') as source:
    shutil.copyfileobj(source,compressed,1024*1024)
assert bundle.stat().st_size<99_000_000
metadata={'created_at':utc_now(),'schema_version':2,'experiment_id':eid,'native_path':native.relative_to(b).as_posix(),'bundle_path':bundle.relative_to(b).as_posix(),'native_sha256':sha256_file(native),'bundle_sha256':sha256_file(bundle),'native_bytes':native.stat().st_size,'bundle_bytes':bundle.stat().st_size,'codec':'lossless gzip/mtime0','native_result_unmodified':True,'restoration_command':'uv run --no-sync python scripts/restore_pvm01_base_reference_result.py','restoration_script_sha256':sha256_file(script),'frozen_shared_restorer_sha256':sha256_file(b/'scripts/restore_pvm01_transport_result.py'),'all_trials_predictions_failures_and_costs_included':True}
publication=b/f'research/laboratory/{eid}-publication-V2.json';assert not publication.exists();atomic_write_json(publication,metadata)
out=b/'research/tmp/c316p1';out.mkdir(parents=True,exist_ok=False);commands=[]
bad=b'Corrupt public existing-record fixture; preserve these bytes'
resource_rows=[x['execution'] for x in json.loads(native.read_text(encoding='utf-8'))['candidates'] if x.get('execution',{}).get('resource_peaks_path')]
for label in ('good','bad-existing','bad-resource-existing'):
    root=out/label;dest=root/'research/results';dest.mkdir(parents=True);lab=root/'research/laboratory';lab.mkdir()
    shutil.copyfile(publication,lab/publication.name);shutil.copyfile(bundle,dest/bundle.name)
    for row in resource_rows:
        relative=Path(row['resource_peaks_path']);source=b/f'research/laboratory/archive/{eid}-runtime'/relative
        target=root/f'research/laboratory/archive/{eid}-runtime'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    if label=='bad-existing':(dest/native.name).write_bytes(bad)
    if label=='bad-resource-existing':
        assert resource_rows
        shutil.copyfile(native,dest/native.name)
        resource=root/resource_rows[0]['resource_peaks_path'];resource.parent.mkdir(parents=True,exist_ok=True);resource.write_bytes(bad)
    prefix=b/f'research/reviews/PVM01-BASE-REFERENCE-publication-{label}-V1'
    with prefix.with_suffix('.stdout.txt').open('xb') as stdout,prefix.with_suffix('.stderr.txt').open('xb') as stderr:
        run=subprocess.run(['uv','run','--no-sync','python',str(script),str(root)],cwd=b,stdout=stdout,stderr=stderr)
    if label=='good':
        assert run.returncode==0 and sha256_file(dest/native.name)==metadata['native_sha256']
        assert len(resource_rows)==85
        assert all(sha256_file(root/row['resource_peaks_path'])==row['resource_peaks_sha256'] for row in resource_rows)
    elif label=='bad-existing':assert run.returncode!=0 and (dest/native.name).read_bytes()==bad
    else:assert run.returncode!=0 and resource.read_bytes()==bad and sha256_file(dest/native.name)==metadata['native_sha256']
    commands.append({'label':label,'returncode':run.returncode,'outputs':{p.name:sha256_file(p) for p in [prefix.with_suffix('.stdout.txt'),prefix.with_suffix('.stderr.txt')]}})
p=b/'.gitignore';raw=p.read_bytes();snapshot=json.loads((b/'research/checks/PVM01-BASE-REFERENCE-history-snapshot-V1.json').read_text(encoding='utf-8'));assert sha256_file(p)==snapshot['raw_files']['.gitignore']
archive=b/f'research/laboratory/archive/{eid}-publication-source';archive.mkdir(parents=True,exist_ok=False);(archive/'root.gitignore.before.raw').write_bytes(raw);shutil.copyfile(script,archive/script.name)
p.write_bytes(raw+f'\n# Native independent-confirmation record is versioned losslessly as gzip plus its exact hash.\n/research/results/{eid}.json\n'.encode())
assert sha256_file(native)==metadata['native_sha256']
after=shutil.disk_usage(b).free;assert after>=10*1024**3
atomic_write_json(b/'research/reviews/PVM01-BASE-REFERENCE-publication-conformance-V1.json',{'created_at':utc_now(),'commands':commands,'native_hash':metadata['native_sha256'],'lossless_restoration_exact':True,'existing_record_never_overwritten':True,'new_fit_seed_scoring':False,'free_space_before':before,'bounded_additional_footprint':footprint,'free_space_after':after,'wall_seconds':time.monotonic()-started})
print('Complete native independent-confirmation result losslessly versioned; exact restoration/non-overwrite PASS',metadata['native_bytes'],metadata['bundle_bytes'],flush=True)
