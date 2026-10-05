from pathlib import Path
import json,subprocess
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.integrity import freeze_manifest
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.report import write_report
b=Path.cwd();plan=b/'research/plans/PVM01-ROBUSTNESS-CHECKOUT-BYTES-ADDENDUM-V1.json'
assert plan.is_file() and b'\r\n' not in (b/'config/baseline_semantics.json').read_bytes()
before=b/'research/laboratory/archive/PVM01-ROBUSTNESS-checkout-bytes-before-V1'
assert (b/'.gitattributes').read_bytes().startswith((before/'root.gitattributes.before.raw').read_bytes())
arc=b/'research/laboratory/archive/PVM01-ROBUSTNESS-checkout-bytes-failed-V1';arc.mkdir()
for name,source in [('controller.py',b/'research/tmp/pvm01_robustness_checkout_bytes_v1.py'),('current-targeted-native.xml',b/'research/checks/PVM01-ROBUSTNESS-targeted-V1.xml'),('first-checkout-LF.xml',b/'research/tmp/PVM01-ROBUSTNESS-checkout-bytes-true-V1/research/checks/PVM01-ROBUSTNESS-targeted-V1.xml')]:
 (arc/name).write_bytes(source.read_bytes())
append_jsonl(b/'research/events.jsonl',{'event':'laboratory_checkout_bytes_implementation_correction','created_at':utc_now(),'cycle':314,'plan_sha256':sha256_file(plan),'failed_receipt':'research/reviews/PVM01-ROBUSTNESS-checkout-bytes-V1.json','cause':'Git retained cached normalized XML despite newly applied -text. Re-stage only current study check records with --renormalize; no byte mutation of existing evidence or scored retry.','new_data_fit_EXP':False})
current_checks=sorted(p.relative_to(b).as_posix() for p in (b/'research/checks').glob('PVM01-ROBUSTNESS-*') if p.is_file())
subprocess.run(['git','add','--renormalize','--',*current_checks],check=True)
files=['.gitattributes','config/baseline_semantics.json','research/checks/PVM01-ROBUSTNESS-targeted-V1.xml','research/checks/PVM01-ROBUSTNESS-full-V1.xml','research/checks/PVM01-ROBUSTNESS-full-V2.xml']
checks=[]
for policy in ('true','false'):
 root=b/'research/tmp'/f'PVM01-ROBUSTNESS-checkout-bytes-{policy}-V2';root.mkdir()
 subprocess.run(['git','-c','core.autocrlf='+policy,'checkout-index','--prefix='+root.as_posix()+'/', '--',*files],cwd=b,check=True)
 for name in files:assert sha256_file(root/name)==sha256_file(b/name),(policy,name)
 checks.append({'core_autocrlf':policy,'files':{name:sha256_file(root/name) for name in files}})
m=freeze_manifest(b,overwrite=True);write_preflight_certificate(b);write_report(b)
rels=[*m['files'],'research/eval_manifest.json','research/laboratory/preflight_certificate.json'];source=b/'research/laboratory/archive/PVM01-ROBUSTNESS-validation-source-V3'
assert not source.exists()
for name in dict.fromkeys(rels):
 target=source/('root.gitattributes.raw' if name=='.gitattributes' else name);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((b/name).read_bytes())
atomic_write_json(b/'research/checks/PVM01-ROBUSTNESS-validation-source-V3.json',{'created_at':utc_now(),'preregistration_git_commit':'e2342788c37e9bcb7d80db9331e9c2e825c695cf','files':{name:sha256_file(b/name) for name in dict.fromkeys(rels)},'protected_files':len(m['files']),'new_scored_arrays_fit':False,'scientific_recipe_source_unchanged':True})
atomic_write_json(b/'research/reviews/PVM01-ROBUSTNESS-checkout-bytes-conformance-V2.json',{'created_at':utc_now(),'checks':checks,'same_registry_JSON_semantics':True,'same_committed_LF_bytes':True,'native_failed_JUnit_bytes_preserved':True,'old_attributes_prefix_preserved':True,'all_prior_validation_sources_and_failed_check_preserved':True,'new_data_fit_EXP':False})
print('Both checkout policies recover exact protected registry/native JUnit bytes; PASS',flush=True)
