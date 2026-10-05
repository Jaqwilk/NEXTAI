from pathlib import Path
p=Path('research/tmp/pvm01_fresh_final_publish_v1.py');s=p.read_text()
s=s.replace('import gzip,json,shutil,subprocess,time','import gzip,json,shutil,subprocess,time,zipfile')
needle="script=b/'scripts/restore_pvm01_fresh_final_result.py';assert not script.exists()"
block='''state_root=b/f'research/tmp/{eid}/fitted-source';state_bundle=b/f'research/results/{eid}.fitted-state.zip';assert not state_bundle.exists()
state_files={path.relative_to(state_root).as_posix():path for path in sorted(state_root.rglob('*')) if path.is_file()}
assert len(state_files)==50 and sum(path.stat().st_size for path in state_files.values())<=54067200
with zipfile.ZipFile(state_bundle,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for relative,path in state_files.items():archive.writestr(relative,path.read_bytes())
assert state_bundle.stat().st_size<=10485760
state_publication=b/f'research/laboratory/{eid}-fitted-state-publication-V1.json';assert not state_publication.exists()
atomic_write_json(state_publication,{'experiment_id':eid,'source_study_path':'research/plans/PVM01-FRESH-FINAL-V1.json','source_study_sha256':sha256_file(b/'research/plans/PVM01-FRESH-FINAL-V1.json'),'bundle_path':state_bundle.relative_to(b).as_posix(),'bundle_sha256':sha256_file(state_bundle),'bundle_bytes':state_bundle.stat().st_size,'expanded_bytes':sum(path.stat().st_size for path in state_files.values()),'files':{rel:{'bytes':path.stat().st_size,'sha256':sha256_file(path)} for rel,path in state_files.items()},'exports':25,'before_final_data':True,'no_source_refit':True,'no_training_final_arrays_labels_nonce_optimizer_episode_memory':True})
'''
assert s.count(needle)==1;s=s.replace(needle,block+needle,1)
needle='    print("Exact saved resource journals available for frozen reanalysis:",len(jobs))'
block='''    import zipfile
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
            if not re.fullmatch(r"pvm01_tc_(?:transport_pca|transport_pca_untrained|transport_pca_shuffled|ridge_pca_scan|dense_cached_cpu)_s[0-4]/(?:metadata.json|parameters.npz)",name):
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
'''
assert s.count(needle)==1;s=s.replace(needle,block+needle,1)
needle="shutil.copyfile(publication,lab/publication.name);shutil.copyfile(bundle,dest/bundle.name)"
s=s.replace(needle,needle+"\n    shutil.copyfile(state_publication,lab/state_publication.name);shutil.copyfile(state_bundle,dest/state_bundle.name)\n    for path in (b/f'research/laboratory/archive/{eid}-runtime/research/tmp/{eid}').glob('*.fits.jsonl'):\n        target=root/f'research/laboratory/archive/{eid}-runtime/research/tmp/{eid}'/path.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)",1)
s=s.replace("('good','bad-existing','bad-resource-existing')", "('good','bad-existing','bad-resource-existing','bad-fitted-existing')")
needle="    prefix=b/f'research/reviews/PVM01-FRESH-FINAL-publication-{label}-V1'"
s=s.replace(needle,"    if label=='bad-fitted-existing':\n        fitted=root/f'research/tmp/{eid}/fitted-source'/next(iter(state_files));fitted.parent.mkdir(parents=True,exist_ok=True);fitted.write_bytes(bad)\n"+needle,1)
s=s.replace("    else:assert run.returncode!=0 and resource.read_bytes()==bad and sha256_file(dest/native.name)==metadata['native_sha256']", "    elif label=='bad-resource-existing':assert run.returncode!=0 and resource.read_bytes()==bad and sha256_file(dest/native.name)==metadata['native_sha256']\n    else:assert run.returncode!=0 and fitted.read_bytes()==bad and sha256_file(dest/native.name)==metadata['native_sha256']")
s=s.replace("        assert len(resource_rows)==85", "        assert len(resource_rows)==85\n        assert all(sha256_file(root/f'research/tmp/{eid}/fitted-source'/name)==sha256_file(path) for name,path in state_files.items())\n        assert len(list((root/f'research/tmp/{eid}').glob('*.fits.jsonl')))==25")
s=s.replace("footprint=3*native.stat().st_size+64*1024**2","footprint=4*native.stat().st_size+128*1024**2")
p.write_text(s,encoding='utf-8',newline='\n')
# This extra small lossless source-state package is scientific provenance, not an additional fit.
p=Path('research/tmp/pvm01_fresh_final_integrate_v1.py');s=p.read_text().replace("exact={", "exact={'research/results/EXP-20261005-0006.fitted-state.zip',",1);p.write_text(s,encoding='utf-8',newline='\n')
print('Bounded lossless source-state publication/restoration and nonoverwrite fixtures prepared')