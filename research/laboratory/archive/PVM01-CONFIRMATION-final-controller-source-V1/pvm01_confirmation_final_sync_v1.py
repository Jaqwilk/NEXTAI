from pathlib import Path
import json,subprocess
from nextai_autoresearch.utils import sha256_file
from nextai_autoresearch.integrity import verify_manifest
from nextai_autoresearch.baseline_semantics import verify_preflight_certificate
from nextai_autoresearch.report import report_provenance_problems
b=Path.cwd();o=b.parent/'NEXTAI'
for name in [p.name for p in sorted((b/'research/tmp').glob('pvm01_confirmation_*.py'))]:
    target=b/'research/laboratory/archive/PVM01-CONFIRMATION-final-controller-source-V1'/name
    assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((b/'research/tmp'/name).read_bytes())
paths=[x for x in subprocess.check_output(['git','ls-files','-m','-o','--exclude-standard','-z']).decode().split('\0') if x]
allowed=('research/reviews/PVM01-CONFIRMATION-integrate-original-','research/reviews/PVM01-CONFIRMATION-history-original-postrun-','research/REPORT','research/events.jsonl','research/laboratory/PVM01-CYCLE-315-','research/laboratory/archive/PVM01-CONFIRMATION-','research/reviews/PVM01-CONFIRMATION-original-')
for rel in paths:
    assert rel.startswith(allowed),rel
    assert (b/rel).stat().st_size<99_000_000,rel
for i in range(0,len(paths),100):subprocess.run(['git','add','--',*paths[i:i+100]],check=True)
subprocess.run(['git','-c','core.whitespace=-blank-at-eof,cr-at-eol','diff','--cached','--check'],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['git','commit','-q','-m','Close paired dense-noise cycle with exact lineage and conserved full costs'],check=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
subprocess.run(['git','fetch','-q',str(b),'codex/muc03-autonomous-20261004'],cwd=o,check=True)
with (b/'research/tmp/PVM01-CONFIRMATION-final-original-FF-V1.log').open('xb') as out:
    subprocess.run(['git','merge','--ff-only','FETCH_HEAD'],cwd=o,check=True,stdout=out,stderr=out)
for root in (b,o):
    current=subprocess.check_output(['git','symbolic-ref','--short','HEAD'],cwd=root,text=True).strip()
    for branch in ('master','main'):
        if branch==current:continue
        ref='refs/heads/'+branch;old=subprocess.check_output(['git','rev-parse',ref],cwd=root,text=True).strip()
        subprocess.run(['git','merge-base','--is-ancestor',old,head],cwd=root,check=True)
        subprocess.run(['git','update-ref',ref,head,old],cwd=root,check=True)
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==head
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=root).strip()
    assert verify_manifest(root)['ok'];verify_preflight_certificate(root)
    assert not report_provenance_problems(root)
    for identity in ('EXP-20261005-0001','EXP-20261005-0002','EXP-20261005-0003','EXP-20261005-0004'):
        pub=json.loads((root/f'research/laboratory/{identity}-publication-V2.json').read_text(encoding='utf-8'))
        assert sha256_file(root/pub['native_path'])==pub['native_sha256']
for ancestor in ['905ed709ad18d3fdc2dac863deb121cefbf1b874','7344683c2c358de262b3e6b26ece0839c234a96a']:
    subprocess.run(['git','merge-base','--is-ancestor',ancestor,head],cwd=o,check=True)
assert subprocess.check_output(['git','remote','get-url','origin'],cwd=o,text=True).strip()=='https://github.com/Jaqwilk/NEXTAI.git'
subprocess.run(['git','push','--atomic','origin','master','main'],cwd=o,check=True)
remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/master','refs/heads/main'],cwd=o,text=True).splitlines()
assert len(remote)==2 and all(row.split()[0]==head for row in remote)
receipt=json.loads((b/'research/laboratory/PVM01-CYCLE-315-COMPLETION-V1.receipt.json').read_text(encoding='utf-8'))
print(json.dumps({'closed_cycle':315,'head':head,'github_master_main_verified':True,'both_roots_clean':True,'study_aux_seconds':receipt['study_auxiliary_seconds_charged'],'study_total_full_wall_and_aux':receipt['full_study_worker_and_auxiliary_charge_seconds'],'remaining_A_seconds':receipt['program_accounting']['fit_seconds_remaining'],'remaining_A_tickets':receipt['stage_a_remaining_new_registrations'],'goal_complete':False}),flush=True)

