from pathlib import Path
import hashlib,importlib.util,subprocess,sys
import xml.etree.ElementTree as ET
from nextai_autoresearch.utils import load_json,atomic_write_json,sha256_file,utc_now
root=Path.cwd();assert root.name=='NEXTAI-VALIDATION-20261002'
identity='ASM01-EXPOSED-LEXICAL-DIAGNOSIS-V2';plan_path=root/f'research/plans/{identity}.json';plan=load_json(plan_path)
assert sha256_file(plan_path)=='1c138c0d1b3868e247c356c9c2640d5490faca5a1bc0f7c5f6e16d2680a13e48'
for name,digest in plan['parent_bindings'].items():assert sha256_file(root/name)==digest
binding=load_json(root/'research/reviews/ASM01-LEXICAL-DIAG-SOURCE-BINDING-V2.json')
for name,digest in binding['files'].items():assert sha256_file(root/name)==digest
prefix=root/'research/reviews/ASM01-LEXICAL-DIAG-RESULT-V2';assert not prefix.with_suffix('.json').exists()
p=subprocess.run([sys.executable,'-m','pytest','-q','-x',plan['implementation_paths'][1],f'--junitxml={prefix.with_suffix(".xml")}'],cwd=root,capture_output=True)
prefix.with_suffix('.stdout.txt').write_bytes(p.stdout);prefix.with_suffix('.stderr.txt').write_bytes(p.stderr)
cases=ET.parse(prefix.with_suffix('.xml')).findall('.//testcase');assert p.returncode==0 and len(cases)==4 and not any(any(c.find(k) is not None for k in ('error','failure','skipped')) for c in cases)
raw=root/plan['raw_scope']['path']
assert not any(p.is_symlink() or p.is_junction() for p in (raw,*raw.parents)) and raw.stat().st_size<=262144
payload=raw.read_bytes();assert hashlib.sha256(payload).hexdigest()==plan['raw_scope']['sha256']
spec=importlib.util.spec_from_file_location('knownfile_classifier',root/plan['implementation_paths'][0]);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
counts=mod.classify_release(payload);assert counts['point_rows']==175
assert sum(counts['coordinates']['Y'][k] for k in ('exact_minus_zero','other_minus_zero','minus_nonzero'))==3
atomic_write_json(prefix.with_suffix('.json'),{'created_at':utc_now(),'complete':True,'fixture_cases':4,'raw_sha256':plan['raw_scope']['sha256'],'opaque_lexical_counts':counts,'new_native_samples':0,'coordinate_numeric_conversions':0,'geometry_calls':0,'normalizer_calls':0,'fit':0,'EXP':0,'retry':False})
print({'complete':True,'opaque_lexical_counts':counts},flush=True)
