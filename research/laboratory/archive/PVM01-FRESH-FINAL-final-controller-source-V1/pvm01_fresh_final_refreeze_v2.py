from pathlib import Path
import json
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.integrity import freeze_manifest
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.report import write_report
b=Path.cwd();study_path='research/plans/PVM01-FRESH-FINAL-V1.json';study=json.loads((b/study_path).read_text())
for name,digest in study['parent_evidence']['scientific_source_sha256_unchanged'].items():assert sha256_file(b/name)==digest,name
receipt=json.loads((b/'research/reviews/PVM01-FRESH-FINAL-targeted-V4.json').read_text());assert receipt['result']['returncode']==0 and not receipt['error']
manifest=json.loads((b/'research/eval_manifest.json').read_text());changed=[r for r,h in manifest['files'].items() if sha256_file(b/r)!=h];assert changed==['tests/test_pvm01_fresh_final.py'],changed
rel='research/plans/PVM01-FRESH-FINAL-PRESEED-CONFORMANCE-V1.json';assert not (b/rel).exists()
atomic_write_json(b/rel,{'id':'PVM01-FRESH-FINAL-PRESEED-CONFORMANCE-V1','created_at':utc_now(),'parent_study_path':study_path,'parent_study_sha256':sha256_file(b/study_path),'observation':'Six additional preregistered fitted-state provenance guard tests were added while the first maintenance freeze controller was in flight. The first manifest retained the preceding test hash; its subsequent validation source archive retained the newer test bytes. Both are preserved verbatim. Two earlier auxiliary fixture failures are also retained: nonexistent test filename,then omitted new addon hash in schema enum. No research registration/private arrays/fit/scoring occurred.','repair':'After112 scientific source checks and passing current targeted112 tests,freeze a distinct V2 maintenance certificate/source archive before full regression/readiness. No metric,threshold,recipe,cap,deadline,baseline or historical result changes. Preserve the first manifest/archive,all failed outputs and all charges;no paid retry.','changed_protected_files':changed,'original_manifest_sha256':sha256_file(b/'research/eval_manifest.json'),'first_validation_source_archive':'research/laboratory/archive/PVM01-FRESH-FINAL-validation-source-V1','targeted_receipt_sha256':sha256_file(b/'research/reviews/PVM01-FRESH-FINAL-targeted-V4.json'),'new_private_arrays_fit_registration_scoring':False})
append_jsonl(b/'research/events.jsonl',{'event':'research_program_preseed_conformance_addendum','created_at':utc_now(),'program_id':'NEXTAI-CONTINUATION-20261004-V1','cycle':317,'addendum_path':rel,'addendum_sha256':sha256_file(b/rel),'no_paid_registration_retry':True})
manifest=freeze_manifest(b,overwrite=True);write_preflight_certificate(b);write_report(b)
rels=[*manifest['files'],'research/eval_manifest.json','research/laboratory/preflight_certificate.json'];arc=b/'research/laboratory/archive/PVM01-FRESH-FINAL-validation-source-V2';assert not arc.exists()
for rel in dict.fromkeys(rels):
 target=arc/('root.gitattributes.raw' if rel=='.gitattributes' else rel);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((b/rel).read_bytes());assert sha256_file(target)==sha256_file(b/rel)
prereg=json.loads((b/'research/tmp/PVM01-FRESH-FINAL-preregistration-V1.json').read_text())
atomic_write_json(b/'research/checks/PVM01-FRESH-FINAL-validation-source-V2.json',{'created_at':utc_now(),'preregistration_git_commit':prereg['preregistration_git_commit'],'files':{r:sha256_file(b/r) for r in dict.fromkeys(rels)},'new_scored_arrays_fit_EXP':False,'protected_files':len(manifest['files']),'preseed_conformance_addendum':'research/plans/PVM01-FRESH-FINAL-PRESEED-CONFORMANCE-V1.json'})
print('Distinct pre-seed V2 maintenance freeze; all earlier bytes/failures/charges preserved',flush=True)