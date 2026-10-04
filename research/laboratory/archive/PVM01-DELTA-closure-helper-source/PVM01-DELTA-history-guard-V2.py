from pathlib import Path
import json,time,math,subprocess,hashlib
from nextai_autoresearch.research_program import auxiliary_reserve,auxiliary_charge,status
from nextai_autoresearch.utils import sha256_file,atomic_write_json,utc_now
b=Path.cwd();orig=Path('C:/Users/NATAN/Documents/ChatGPT/NEXTAI')
cid='PVM01-DELTA-final-history-prefix-guard-V2'
auxiliary_reserve(b,cid,60);start=time.perf_counter();error=None;checks={}
try:
    snap=json.loads((b/'research/reviews/PVM01-DELTA-startup-history-V1.json').read_text(encoding='utf8'))
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=orig,text=True).strip()==snap['source_head']
    assert not subprocess.check_output(['git','status','--porcelain'],cwd=orig).strip()
    assert not [p for p,h in snap['files'].items() if sha256_file(orig/p)!=h]
    allowed={'.gitattributes','AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md','docs/SCIENTIFIC_PROTOCOL.md','config/research.toml','config/baseline_semantics.json','research/eval_manifest.json','research/laboratory/preflight_certificate.json','research/REPORT.md','research/REPORT.provenance.json','schemas/experiment_plan.schema.json','src/nextai_autoresearch/integrity.py','src/nextai_autoresearch/research_program.py','src/nextai_autoresearch/runner.py','src/nextai_autoresearch/utils.py','tests/test_runner_postseed_durability.py','research/state.json',*snap['append_only_prefixes']}
    changed=set(subprocess.check_output(['git','diff','--name-only',snap['source_head'],'--'],text=True).splitlines())
    deleted=set(subprocess.check_output(['git','diff','--name-only','--diff-filter=D',snap['source_head'],'--'],text=True).splitlines());assert not deleted,deleted
    old_changed=changed & snap['files'].keys();assert not old_changed-allowed,sorted(old_changed-allowed)
    eol=[];violations=[]
    for p,h in snap['files'].items():
        if p in allowed:continue
        target=b/p
        if not target.exists():violations.append(p);continue
        if sha256_file(target)!=h:
            x=(orig/p).read_bytes();y=target.read_bytes()
            if x.replace(b'\r\n',b'\n')!=y.replace(b'\r\n',b'\n'):violations.append(p)
            else:eol.append({'path':p,'original_raw_sha256':h,'clone_raw_sha256':sha256_file(target),'only_preexisting_line_endings':True})
    assert not violations,violations
    for p,s in snap['append_only_prefixes'].items():
        raw=(b/p).read_bytes();assert hashlib.sha256(raw[:s['bytes']]).hexdigest()==s['sha256'],p
        if p.endswith('.jsonl'):
            for line in raw[s['bytes']:].decode('utf8').splitlines():json.loads(line)
        if p=='research/hypothesis_events.jsonl':assert len(raw)==s['bytes']
    for p in ('AGENTS.md','program.md','research/LAB_PLAN.md','docs/CURRENT_STATUS.md','docs/SCIENTIFIC_PROTOCOL.md'):
        assert (b/p).read_text(encoding='utf8').endswith((orig/p).read_text(encoding='utf8')),p
    assert (b/'.gitattributes').read_text(encoding='utf8').startswith((orig/'.gitattributes').read_text(encoding='utf8'))
    assert sha256_file(b/'research/results/EXP-20261004-0006.json')=='d291d33e648ee135611f865fc5496c3150909a956934275f01507bd540a00651'
    p=status(b)
    assert p['registration_attempts_used']==6 and p['continuation_registration_attempts_used']==3 and p['prior_registration_attempts_used']==3 and p['prior_program_closed'] and not p['program_closed'] and not p['paid_run_pending'] and p['study_terminal']
    checks={'original_tracked_files_raw_unchanged':len(snap['files']),'completed_plan_result_analysis_archive_bytes_unchanged':True,'permitted_old_file_changes':sorted(old_changed),'preexisting_EOL_differences':eol,'append_only_prefixes_verified':list(snap['append_only_prefixes']),'historical_authority_sections_preserved':True,'no_deleted_files':True,'program_budget_registration_carry_forward_valid':True,'state_cycle':json.loads((b/'research/state.json').read_text(encoding='utf8'))['cycle_number']}
    print(json.dumps({'status':'PASS','original_files':len(snap['files']),'old_changed':sorted(old_changed),'preexisting_EOL_differences':[x['path'] for x in eol],'prefixes':list(snap['append_only_prefixes'])}),flush=True)
except BaseException as exc:
    error={'type':type(exc).__name__,'message':str(exc)};raise
finally:
    elapsed=time.perf_counter()-start;charge=math.ceil(elapsed);assert charge<=60
    auxiliary_charge(b,cid,charge)
    atomic_write_json(b/'research/reviews'/f'{cid}.json',{'id':cid,'created_at':utc_now(),'elapsed_seconds':elapsed,'charged_seconds':charge,'checks':checks,'error':error,'research_fit_or_new_data':False,'previous_failed_check_preserved':'PVM01-DELTA-final-history-prefix-guard-V1','correction':'The prospective baseline registry path is config/baseline_semantics.json, not jsonl; unchanged allow scope.'})

