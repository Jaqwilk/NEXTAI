from pathlib import Path
import json,subprocess,shutil
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
from nextai_autoresearch.report import write_report
from nextai_autoresearch.research_program import status
b=Path.cwd();o=b.parent/'NEXTAI';eid='EXP-20261005-0004'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=o).strip()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=o,text=True).strip()=='ecbbb2b3cfebb331944350766e49b3f5f62d23f0'
assert verify_manifest(b)['ok'];verify_preflight_certificate(b)
for cid in ['PVM01-CONFIRMATION-native-analysis-preservation-V1','PVM01-CONFIRMATION-publication-V1','PVM01-CONFIRMATION-report-metadata-V1','PVM01-CONFIRMATION-history-clone-postrun-V1']:
    receipt=json.loads((b/f'research/reviews/{cid}.json').read_text(encoding='utf-8'));assert receipt['result']['returncode']==0 and not receipt['error']
value=status(b);assert value['study_terminal'] and not value['program_closed'] and not value['scoring_authorized']
assert value['continuation_registration_attempts_used']==9
arc=b/f'research/laboratory/archive/{eid}-worker-logs-V1';logs=sorted((b/'research/logs').glob(eid+'*.log'));assert len(logs)==85
for p in logs:
    target=arc/p.name;assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);assert sha256_file(target)==sha256_file(p)
atomic_write_json(b/f'research/laboratory/{eid}-worker-log-archive-V1.json',{'created_at':utc_now(),'experiment_id':eid,'archive':arc.relative_to(b).as_posix(),'files':{p.name:sha256_file(p) for p in logs},'all85_raw_candidate_logs_preserved':True})
arc=b/'research/laboratory/archive/PVM01-CONFIRMATION-postrun-controller-source-V1'
for name in ['pvm01_confirmation_post_v1.py','pvm01_confirmation_publish_v1.py','pvm01_confirmation_report_v1.py','pvm01_confirmation_report_metadata_v1.py','pvm01_confirmation_history_v1.py','pvm01_confirmation_integrate_v1.py']:
    target=arc/name;assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((b/'research/tmp'/name).read_bytes())
write_report(b)
paths=[x for x in subprocess.check_output(['git','ls-files','-m','-o','--exclude-standard','-z']).decode().split('\0') if x]
allowed=('research/REPORT','research/events.jsonl','research/experiments.tsv','research/plan_registry.jsonl','research/state.json','research/eval_manifest.json','research/laboratory/EXP-20261005-0004','research/laboratory/archive/EXP-20261005-0004','research/laboratory/archive/PVM01-CONFIRMATION-','research/laboratory/preflight_certificate','research/laboratory/certificates/','research/manifests/paired_view_mutable_memory_v9','research/reviews/PVM01-CONFIRMATION-','research/reviews/EXP-20261005-0004')
exact={'.gitignore','AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md','config/research.toml','scripts/restore_pvm01_confirmation_result.py','research/plans/EXP-20261005-0004.json','research/results/EXP-20261005-0004.json.gz','research/analyses/EXP-20261005-0004.md','research/analyses/EXP-20261005-0003-CUDA-TELEMETRY-ADDENDUM-V1.md'}
for rel in paths:
    assert rel in exact or rel.startswith(allowed),rel
    assert (b/rel).stat().st_size<99_000_000,rel
for i in range(0,len(paths),100):subprocess.run(['git','add','--',*paths[i:i+100]],check=True)
subprocess.run(['git','-c','core.whitespace=-blank-at-eof,cr-at-eol','diff','--cached','--check'],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['git','commit','-q','-m','Preserve dense-noise intervention, frozen decisions and complete raw provenance'],check=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
subprocess.run(['git','fetch','-q',str(b),'codex/muc03-autonomous-20261004'],cwd=o,check=True)
with (b/'research/tmp/PVM01-CONFIRMATION-original-FF-V1.log').open('xb') as out:
    subprocess.run(['git','merge','--ff-only','FETCH_HEAD'],cwd=o,check=True,stdout=out,stderr=out)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=o,text=True).strip()==head
assert not subprocess.check_output(['git','status','--porcelain'],cwd=o).strip()
print('Independent evidence preserved; original fast-forward:',head,flush=True)
