from pathlib import Path
import gzip,json,shutil,subprocess,time,zipfile
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
b=Path.cwd();eid='EXP-20261005-0006';native=b/f'research/results/{eid}.json';bundle=native.with_suffix('.json.gz')
assert native.is_file() and not bundle.exists()
before=shutil.disk_usage(b).free;footprint=4*native.stat().st_size+128*1024**2
assert before-footprint>10*1024**3
state_root=b/f'research/tmp/{eid}/fitted-source';state_bundle=b/f'research/results/{eid}.fitted-state.zip';assert not state_bundle.exists()
state_files={path.relative_to(state_root).as_posix():path for path in sorted(state_root.rglob('*')) if path.is_file()}
assert len(state_files)==50 and sum(path.stat().st_size for path in state_files.values())<=54067200
with zipfile.ZipFile(state_bundle,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for relative,path in state_files.items():archive.writestr(relative,path.read_bytes())
assert state_bundle.stat().st_size<=10485760
state_publication=b/f'research/laboratory/{eid}-fitted-state-publication-V1.json';assert not state_publication.exists()
atomic_write_json(state_publication,{'experiment_id':eid,'source_study_path':'research/plans/PVM01-FRESH-FINAL-V1.json','source_study_sha256':sha256_file(b/'research/plans/PVM01-FRESH-FINAL-V1.json'),'bundle_path':state_bundle.relative_to(b).as_posix(),'bundle_sha256':sha256_file(state_bundle),'bundle_bytes':state_bundle.stat().st_size,'expanded_bytes':sum(path.stat().st_size for path in state_files.values()),'files':{rel:{'bytes':path.stat().st_size,'sha256':sha256_file(path)} for rel,path in state_files.items()},'exports':25,'before_final_data':True,'no_source_refit':True,'no_training_final_arrays_labels_nonce_optimizer_episode_memory':True})
script=b/'scripts/restore_pvm01_fresh_final_result.py';assert not script.exists()
script.write_text('''"""Restore the exact independent-confirmation record with the frozen lossless restorer."""
from pathlib import Path
import json
import shutil
import sys
import restore_pvm01_transport_result as frozen

if __name__ == "__main__":
    frozen.ID = "EXP-20261005-0006"
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
    import zipfile
    import re
    publication = json.loads((root/f"research/laboratory/{frozen.ID}-fitted-state-publication-V1.json").read_text(encoding="utf-8"))
    bundle_path = root/f"research/results/{frozen.ID}.fitted-state.zip"
    if (publication["experiment_id"] != frozen.ID or publication["bundle_path"] != bundle_path.relative_to(root).as_posix()
            or frozen.digest(bundle_path) != publication["bundle_sha256"] or publication["bundle_bytes"] > 10485760):
        raise ValueError("Fitted-source bundle provenance mismatch")
    jobs = []
    with zipfile.ZipFile(bundle_path) as bundle:
        if set(bundle.namelist()) != set(publication["files"]) or len(bundle.infolist()) != 50:
            raise ValueError("Fitted-source bundle has unexpected or duplicate files")
        if sum(info.file_size for info in bundle.infolist()) > 54067200:
            raise ValueError("Fitted-source expanded payload exceeds bound")
        for name, record in publication["files"].items():
            if not re.fullmatch(r"pvm01_tc_(?:transport_pca|transport_pca_untrained|transport_pca_shuffled|ridge_pca_scan|dense_cached_cpu)_s[0-4]/(?:metadata\\.json|parameters\\.npz)",name):
                raise ValueError("Unexpected fitted-source path")
            target=(root/f"research/tmp/{frozen.ID}/fitted-source"/name).resolve()
            if not target.is_relative_to(root):raise ValueError("Fitted-source path escapes checkout")
            if bundle.getinfo(name).file_size != record["bytes"]:raise ValueError("Fitted-source file size mismatch")
            data=bundle.read(name)
            if frozen.hashlib.sha256(data).hexdigest() != record["sha256"]:raise ValueError("Fitted-source file hash mismatch")
            if target.exists():
                if frozen.digest(target) != record["sha256"]:raise ValueError("Existing fitted source differs; preserved without overwrite")
            else:jobs.append((target,data))
    archive_root=root/f"research/laboratory/archive/{frozen.ID}-runtime/research/tmp/{frozen.ID}"
    for name in sorted({Path(name).parts[0] for name in publication["files"]}):
        source=archive_root/(name+".fits.jsonl");target=root/f"research/tmp/{frozen.ID}"/(name+".fits.jsonl")
        if source.stat().st_size>262144:raise ValueError("Fitted-source journal exceeds bound")
        if target.exists():
            if frozen.digest(target)!=frozen.digest(source):raise ValueError("Existing fitted journal differs; preserved without overwrite")
        else:jobs.append((target,source.read_bytes()))
    footprint=sum(len(data) for target,data in jobs)
    if footprint>64*1024**2 or shutil.disk_usage(root).free-footprint<10*1024**3:
        raise OSError("Fitted-source hydration exceeds bounded disk reserve")
    for target,data in jobs:
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("xb") as handle:handle.write(data)
    print("Exact fitted-source states/journals available without fit:",len(jobs))
    print("Exact saved resource journals available for frozen reanalysis:",len(jobs))
''',encoding='utf-8',newline='\n')
started=time.monotonic()
with bundle.open('xb') as target,gzip.GzipFile(filename='',mode='wb',compresslevel=6,mtime=0,fileobj=target) as compressed,native.open('rb') as source:
    shutil.copyfileobj(source,compressed,1024*1024)
assert bundle.stat().st_size<99_000_000
metadata={'created_at':utc_now(),'schema_version':2,'experiment_id':eid,'native_path':native.relative_to(b).as_posix(),'bundle_path':bundle.relative_to(b).as_posix(),'native_sha256':sha256_file(native),'bundle_sha256':sha256_file(bundle),'native_bytes':native.stat().st_size,'bundle_bytes':bundle.stat().st_size,'codec':'lossless gzip/mtime0','native_result_unmodified':True,'restoration_command':'uv run --no-sync python scripts/restore_pvm01_fresh_final_result.py','restoration_script_sha256':sha256_file(script),'frozen_shared_restorer_sha256':sha256_file(b/'scripts/restore_pvm01_transport_result.py'),'all_trials_predictions_failures_and_costs_included':True}
publication=b/f'research/laboratory/{eid}-publication-V2.json';assert not publication.exists();atomic_write_json(publication,metadata)
out=b/'research/tmp/c317p1';out.mkdir(parents=True,exist_ok=False);commands=[]
bad=b'Corrupt public existing-record fixture; preserve these bytes'
resource_rows=[x['execution'] for x in json.loads(native.read_text(encoding='utf-8'))['candidates'] if x.get('execution',{}).get('resource_peaks_path')]
for label in ('good','bad-existing','bad-resource-existing','bad-fitted-existing'):
    root=out/label;dest=root/'research/results';dest.mkdir(parents=True);lab=root/'research/laboratory';lab.mkdir()
    shutil.copyfile(publication,lab/publication.name);shutil.copyfile(bundle,dest/bundle.name)
    shutil.copyfile(state_publication,lab/state_publication.name);shutil.copyfile(state_bundle,dest/state_bundle.name)
    for path in (b/f'research/laboratory/archive/{eid}-runtime/research/tmp/{eid}').glob('*.fits.jsonl'):
        target=root/f'research/laboratory/archive/{eid}-runtime/research/tmp/{eid}'/path.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    for row in resource_rows:
        relative=Path(row['resource_peaks_path']);source=b/f'research/laboratory/archive/{eid}-runtime'/relative
        target=root/f'research/laboratory/archive/{eid}-runtime'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    if label=='bad-existing':(dest/native.name).write_bytes(bad)
    if label=='bad-resource-existing':
        assert resource_rows
        shutil.copyfile(native,dest/native.name)
        resource=root/resource_rows[0]['resource_peaks_path'];resource.parent.mkdir(parents=True,exist_ok=True);resource.write_bytes(bad)
    if label=='bad-fitted-existing':
        fitted=root/f'research/tmp/{eid}/fitted-source'/next(iter(state_files));fitted.parent.mkdir(parents=True,exist_ok=True);fitted.write_bytes(bad)
    prefix=b/f'research/reviews/PVM01-FRESH-FINAL-publication-{label}-V1'
    with prefix.with_suffix('.stdout.txt').open('xb') as stdout,prefix.with_suffix('.stderr.txt').open('xb') as stderr:
        run=subprocess.run(['uv','run','--no-sync','python',str(script),str(root)],cwd=b,stdout=stdout,stderr=stderr)
    if label=='good':
        assert run.returncode==0 and sha256_file(dest/native.name)==metadata['native_sha256']
        assert len(resource_rows)==85
        assert all(sha256_file(root/f'research/tmp/{eid}/fitted-source'/name)==sha256_file(path) for name,path in state_files.items())
        assert len(list((root/f'research/tmp/{eid}').glob('*.fits.jsonl')))==25
        assert all(sha256_file(root/row['resource_peaks_path'])==row['resource_peaks_sha256'] for row in resource_rows)
    elif label=='bad-existing':assert run.returncode!=0 and (dest/native.name).read_bytes()==bad
    elif label=='bad-resource-existing':assert run.returncode!=0 and resource.read_bytes()==bad and sha256_file(dest/native.name)==metadata['native_sha256']
    else:assert run.returncode!=0 and fitted.read_bytes()==bad and sha256_file(dest/native.name)==metadata['native_sha256']
    commands.append({'label':label,'returncode':run.returncode,'outputs':{p.name:sha256_file(p) for p in [prefix.with_suffix('.stdout.txt'),prefix.with_suffix('.stderr.txt')]}})
p=b/'.gitignore';raw=p.read_bytes();snapshot=json.loads((b/'research/checks/PVM01-FRESH-FINAL-history-snapshot-V1.json').read_text(encoding='utf-8'));assert sha256_file(p)==snapshot['raw_files']['.gitignore']
archive=b/f'research/laboratory/archive/{eid}-publication-source';archive.mkdir(parents=True,exist_ok=False);(archive/'root.gitignore.before.raw').write_bytes(raw);shutil.copyfile(script,archive/script.name)
p.write_bytes(raw+f'\n# Native independent-confirmation record is versioned losslessly as gzip plus its exact hash.\n/research/results/{eid}.json\n'.encode())
assert sha256_file(native)==metadata['native_sha256']
after=shutil.disk_usage(b).free;assert after>=10*1024**3
atomic_write_json(b/'research/reviews/PVM01-FRESH-FINAL-publication-conformance-V1.json',{'created_at':utc_now(),'commands':commands,'native_hash':metadata['native_sha256'],'lossless_restoration_exact':True,'existing_record_never_overwritten':True,'new_fit_seed_scoring':False,'free_space_before':before,'bounded_additional_footprint':footprint,'free_space_after':after,'wall_seconds':time.monotonic()-started})
print('Complete native independent-confirmation result losslessly versioned; exact restoration/non-overwrite PASS',metadata['native_bytes'],metadata['bundle_bytes'],flush=True)
