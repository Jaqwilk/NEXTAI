from pathlib import Path
import hashlib,json,subprocess
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.integrity import freeze_manifest
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.report import write_report
b=Path.cwd();rel='config/baseline_semantics.json';p=b/rel;before=p.read_bytes()
expected=subprocess.check_output(['git','show','HEAD:'+rel]);assert b'\r\n' in before
assert before.replace(b'\r\n',b'\n')==expected and json.loads(before)==json.loads(expected)
attrs=b/'.gitattributes';oldattrs=attrs.read_bytes()
arc=b/'research/laboratory/archive/PVM01-ROBUSTNESS-checkout-bytes-before-V1';arc.mkdir()
(arc/'baseline_semantics.before.raw').write_bytes(before);(arc/'root.gitattributes.before.raw').write_bytes(oldattrs)
plan=b/'research/plans/PVM01-ROBUSTNESS-CHECKOUT-BYTES-ADDENDUM-V1.json'
assert not plan.exists()
atomic_write_json(plan,{'id':'PVM01-ROBUSTNESS-CHECKOUT-BYTES-ADDENDUM-V1','created_at':utc_now(),'before_implementation':True,'scoring':False,'new_data_fit_EXP':False,'study_sha256':sha256_file(b/'research/plans/PVM01-DENSE-NOISE-ROBUSTNESS-V1.json'),'observed_git_warning':'baseline_semantics CRLF working tree versus LF committed bytes; new raw JUnit checks lack -text policy.','normalization':'Exactly replace CRLF with LF for protected baseline JSON, with JSON-value equality and exact Git-blob byte proof. Append current ROBUSTNESS check-only -text attribute; old attributes remain prefix. No source,metric,threshold,model,recipe,cohort,old result or old budget change.','before_sha256':sha256_file(p),'git_expected_sha256':hashlib.sha256(expected).hexdigest(),'conformance':'Checkout-index under core.autocrlf true and false must recover exact normalized registry and native JUnit bytes. Preserve before bytes and full1198 tests; rerun relevant semantic/metadata checks, refreeze/preflight before registration.'})
append_jsonl(b/'research/events.jsonl',{'event':'laboratory_checkout_bytes_repair_preregistered','created_at':utc_now(),'cycle':314,'plan_path':plan.relative_to(b).as_posix(),'plan_sha256':sha256_file(plan),'before_implementation':True,'new_scored_data_fit_EXP':False})
p.write_bytes(expected)
attrs.write_bytes(oldattrs+b'\n# Preserve native byte hashes of this bounded study\'s JUnit/check records.\nresearch/checks/PVM01-ROBUSTNESS-* -text\n')
assert json.loads(p.read_bytes())==json.loads(before)
files=['.gitattributes',rel,'research/checks/PVM01-ROBUSTNESS-targeted-V1.xml']
subprocess.run(['git','add','--',*files],check=True)
checks=[]
for policy in ('true','false'):
 root=b/'research/tmp'/f'PVM01-ROBUSTNESS-checkout-bytes-{policy}-V1';root.mkdir()
 subprocess.run(['git','-c','core.autocrlf='+policy,'checkout-index','--prefix='+root.as_posix()+'/', '--',*files],cwd=b,check=True)
 for name in files:
  assert sha256_file(root/name)==sha256_file(b/name),(policy,name)
 checks.append({'core_autocrlf':policy,'files':{name:sha256_file(root/name) for name in files}})
m=freeze_manifest(b,overwrite=True);write_preflight_certificate(b);write_report(b)
rels=[*m['files'],'research/eval_manifest.json','research/laboratory/preflight_certificate.json']
source=b/'research/laboratory/archive/PVM01-ROBUSTNESS-validation-source-V3'
for name in dict.fromkeys(rels):
 target=source/('root.gitattributes.raw' if name=='.gitattributes' else name);target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists();target.write_bytes((b/name).read_bytes())
atomic_write_json(b/'research/checks/PVM01-ROBUSTNESS-validation-source-V3.json',{'created_at':utc_now(),'preregistration_git_commit':'e2342788c37e9bcb7d80db9331e9c2e825c695cf','files':{name:sha256_file(b/name) for name in dict.fromkeys(rels)},'protected_files':len(m['files']),'new_scored_arrays_fit':False,'scientific_recipe_source_unchanged':True})
atomic_write_json(b/'research/reviews/PVM01-ROBUSTNESS-checkout-bytes-conformance-V1.json',{'created_at':utc_now(),'checks':checks,'same_registry_JSON_semantics':True,'same_committed_LF_bytes':True,'native_failed_JUnit_bytes_preserved':True,'old_attributes_prefix_preserved':attrs.read_bytes().startswith(oldattrs),'all_prior_validation_sources_preserved':True,'new_data_fit_EXP':False})
print('Protected registry matches Git LF bytes; checkout policies and native JUnit conformance PASS',flush=True)
