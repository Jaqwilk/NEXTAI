from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import numpy as np
import nextai_autoresearch
from nextai_autoresearch.asm01_inventory_members_v3 import screen_members
from nextai_autoresearch.utils import load_json,sha256_file,atomic_write_json,utc_now
root=Path.cwd();assert root.name=='NEXTAI-VALIDATION-20261002'
assert Path(nextai_autoresearch.__file__).resolve().is_relative_to((root/'src').resolve())
identity='ASM01-POINT-SERIAL-NATIVE-CONFORMANCE-V1';plan_path=root/f'research/plans/{identity}.json'
assert sha256_file(plan_path)=='6db8382e5080fbc4b3b244289bb04bbb6f0f3b7f730b5f12bfef9d3d8da3b8c4'
plan=load_json(plan_path);binding=load_json(root/'research/reviews/ASM01-POINT-SERIAL-NATIVE-SOURCE-BINDINGS-V1.json')
for name,digest in binding['files'].items():assert sha256_file(root/name)==digest,name
for name,digest in plan['parent_file_bindings'].items():assert sha256_file(root/name)==digest,name
for name,b in plan['ledger_prefixes'].items():assert hashlib.sha256((root/'research'/name).read_bytes()[:b['bytes']]).hexdigest()==b['sha256'],name
kind=sys.argv[1];assert kind in {'fixtures','intake'}
if kind=='fixtures':
 prefix=root/'research/reviews/ASM01-NATIVE-CONFORMANCE-FIXTURES-V1';assert not prefix.with_suffix('.json').exists()
 command=[sys.executable,'-m','pytest','-q','-x',plan['fixtures']['existing38'],plan['implementation_paths'][1],f'--junitxml={prefix.with_suffix(".xml")}']
 result=subprocess.run(command,cwd=root,capture_output=True)
 prefix.with_suffix('.stdout.txt').write_bytes(result.stdout);prefix.with_suffix('.stderr.txt').write_bytes(result.stderr)
 cases=ET.parse(prefix.with_suffix('.xml')).findall('.//testcase') if prefix.with_suffix('.xml').exists() else []
 counts={'tests':len(cases),'failures':sum(c.find('failure') is not None for c in cases),'errors':sum(c.find('error') is not None for c in cases),'skipped':sum(c.find('skipped') is not None for c in cases)}
 complete=result.returncode==0 and counts=={'tests':46,'failures':0,'errors':0,'skipped':0}
 atomic_write_json(prefix.with_suffix('.json'),{'created_at':utc_now(),'complete':complete,'counts':counts,'returncode':result.returncode,'plan_sha256':sha256_file(plan_path),'native_bytes':0,'fit':0,'clone_package_path':str(Path(nextai_autoresearch.__file__).resolve())})
 print({'kind':kind,'complete':complete,'counts':counts},flush=True);raise SystemExit(0 if complete else 1)
proof=load_json(root/'research/reviews/ASM01-NATIVE-CONFORMANCE-FIXTURES-V1.json');assert proof['complete'] and proof['counts']['tests']==46
controller=load_json(root/'research/reviews/ASM01-NATIVE-CONFORMANCE-CONTROLLER-fixtures-V1.json');assert controller['complete']
receipt_path=root/'research/data_manifests/ASM01-POINT-SERIAL-NATIVE-CONFORMANCE-V1.json';assert not receipt_path.exists()
receipt={'created_at':utc_now(),'complete':False,'plan_sha256':sha256_file(plan_path),'fixture_receipt_sha256':sha256_file(root/'research/reviews/ASM01-NATIVE-CONFORMANCE-FIXTURES-V1.json'),'source_binding_sha256':sha256_file(root/'research/reviews/ASM01-POINT-SERIAL-NATIVE-SOURCE-BINDINGS-V1.json'),'native_files_attempted':0,'native_files_converted':0,'old74_compared':0,'D_samples_opened':0,'attempted_sample_text_sha256':{},'numeric_values_or_names_emitted':False,'research_fit':0,'EXP':0,'registration':0,'scoring':False,'new_download_or_extraction':False,'no_future_writer_coordinates_read':True}
try:
 assert shutil.disk_usage(root).free-335544320>=10737418240
 listing=root/plan['scope']['listing'];assert sha256_file(listing)==plan['scope']['listing_sha256']
 members=screen_members(root/plan['scope']['source_directory'],listing.read_text(encoding='ascii'))
 receipt['all1830_metadata_validated_before_bytes']=True
 inventory=load_json(root/plan['intake_binding']['inventory_path']);old=load_json(root/plan['intake_binding']['old75_path'])
 assert inventory['complete'] and len(inventory['sample_sha256'])==1830
 assert old['native_files_attempted']==75 and old['native_files_converted']==74
 module_path=root/plan['implementation_paths'][0];spec=importlib.util.spec_from_file_location('asm01_native_conformance_intake',module_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 arrays,hashes=module.collect(members,inventory['sample_sha256'],old['attempted_sample_text_sha256'],receipt)
 assert receipt['native_files_converted']==1830 and receipt['old74_compared']==74 and receipt['D_samples_opened']==915
 directory=root/f'research/data/{identity}';directory.mkdir();dataset=directory/'screen-preparation-v1.npz'
 with dataset.open('xb') as out:np.savez_compressed(out,**arrays)
 receipt.update(complete=True,converted_writers=plan['scope']['writers'],converted_writer_hashes=hashes,dataset_path=dataset.relative_to(root).as_posix(),dataset_sha256=sha256_file(dataset),dataset_bytes=dataset.stat().st_size,license='CC BY4.0; preserved publisher provenance',publisher_sha256=plan['intake_binding']['publisher_sha256'],scientific_readiness=False,active_loader_integration=False)
except Exception as exc:
 receipt.update(complete=False,error_type=type(exc).__name__,error_category=receipt.get('error_category','metadata_or_payload_conformance_failure'))
finally:
 atomic_write_json(receipt_path,receipt)
 print({k:receipt.get(k) for k in ('complete','native_files_attempted','native_files_converted','old74_compared','D_samples_opened','current_sample','error_type','error_category','dataset_sha256')},flush=True)
raise SystemExit(0 if receipt['complete'] else 1)
