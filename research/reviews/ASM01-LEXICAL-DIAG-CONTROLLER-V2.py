from pathlib import Path
from datetime import datetime,timezone
from dataclasses import asdict
import os,shutil,zipfile
from nextai_autoresearch.process_supervision import run_bounded
from nextai_autoresearch.research_program import auxiliary_charge
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import atomic_write_json,load_json,sha256_file,utc_now
root=Path.cwd();clone=root.parent/'NEXTAI-VALIDATION-20261002';identity='ASM01-EXPOSED-LEXICAL-DIAGNOSIS-V2'
prefix=root/'research/reviews/ASM01-LEXICAL-DIAG-CONTROLLER-V2';assert not prefix.with_suffix('.started.json').exists()
remaining=(datetime.fromisoformat('2026-10-06T04:03:00+00:00')-datetime.now(timezone.utc)).total_seconds()-90;assert remaining>0
env=os.environ.copy();env.update(PYTHONPATH=str(clone/'src'),NEXTAI_PROJECT_ROOT=str(clone),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
command=[str(clone/'.venv/Scripts/python.exe'),str(clone/'research/reviews/ASM01-LEXICAL-DIAG-CLONE-V2.py')]
atomic_write_json(prefix.with_suffix('.started.json'),{'created_at':utc_now(),'attempt':1,'timeout_seconds':min(60,remaining)})
job=run_bounded(command,cwd=clone,env=env,stdout_path=prefix.with_name(prefix.name+'.stdout.txt'),stderr_path=prefix.with_name(prefix.name+'.stderr.txt'),timeout_seconds=min(60,remaining))
atomic_write_json(prefix.with_suffix('.json'),{'created_at':utc_now(),'job':asdict(job),'complete':job.returncode==0})
for p in (clone/'research/reviews').glob('ASM01-LEXICAL-DIAG-RESULT-V2.*'):shutil.copyfile(p,root/'research/reviews'/p.name)
proof_path=root/'research/reviews/ASM01-LEXICAL-DIAG-RESULT-V2.json';proof=load_json(proof_path) if proof_path.exists() else {'complete':False}
counts=proof.get('opaque_lexical_counts',{});minus=sum(a.get('minus_nonzero',0) for a in counts.get('coordinates',{}).values())
decision='Exact ASM coordinate grammar incompatible; scientific INCONCLUSIVE' if minus else 'Lexical evidence only; no repair authority' if proof['complete'] else 'INCOMPLETE diagnosis; stop unstarted scope'
archive=root/'research/laboratory/archive/ASM01-EXPOSED-LEXICAL-DIAGNOSIS-EVIDENCE-V2.zip'
paths=list((root/'research/reviews').glob('ASM01-LEXICAL-DIAG-*'))+[root/f'research/plans/{identity}.json']+list((root/f'research/preparations/{identity}').glob('*.py'))
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for p in paths:
  if p.is_file():z.write(p,p.relative_to(root).as_posix())
auxiliary_charge(root,identity,360)
receipt={'created_at':utc_now(),'id':identity,'decision':decision,'proof':proof,'job':asdict(job),'charged_seconds':360,'fit':0,'EXP':0,'new_native_samples':0,'coordinate_conversions':0,'retry':False,'whole_clock_start':'2026-10-06T03:57:00Z','deadline':'2026-10-06T04:03:00Z','protected_seconds':47000,'protected_tickets':7,'unprotected_B_seconds_remaining':530.4497597999289,'archive_sha256':sha256_file(archive),'full_goal_status':'ACTIVE, INCOMPLETE'}
out=root/'research/laboratory/ASM01-EXPOSED-LEXICAL-DIAGNOSIS-COMPLETION-V2.receipt.json';atomic_write_json(out,receipt)
append_jsonl(root/'research/events.jsonl',{'event':'maintenance_preparation_closed','created_at':utc_now(),'cycle':334,'plan_id':identity,'receipt_sha256':sha256_file(out),'decision':decision,'fit':0,'EXP':0})
(root/'research/analyses/ASM01-CYCLE334-EXPOSED-LEXICAL-DIAGNOSIS-V1.md').write_text(f'# ASM01 — cykl333: redacted known-file diagnosis\n\nDecyzja: **{decision}**. Prerejestracja separateV2 przed kodem i ponownym odczytem wyłącznie known17:74. Wynik: {counts}. Cztery syntetyczne cases PASS={proof.get("fixture_cases")}. Jedyny boundedjob: {asdict(job)}.\n\nWyłącznie liczności lexicalclasses; zero coordinate/token/name emission, numericconversion, geometry/normalizer invocation, nativecontinuation,NPZ,fit,EXP i retry. Niezerowa ujemna kategoria jest sprzeczna z niezmienionymunsignedXY/bounds0; nie stosowaćabs/clamp/offset lub sample replacement. To intake invalidity, nie learning/transfer/economic null. Old74 exactconformance i1171conversionproof zachowane.\n\nPełny clock03:57–04:03Z:360s inclstartup/code/tests/knownfile/closing/Git. Protected7tickets/47000s intact; unprotectedremaining530.4497598s. FullgoalACTIVE: drugi naukowy transfer, replications/freshfinals i lokalny fact/source/update/UNKNOWN prototype unfinished. Alternatywna uzasadniona rodzina jest dozwolona przezBcontract, lecz screening tylko z unprotectedbudget; protectedreallocation wymagaexplicituserauthority. Existing aggregatebudget/ownaux blockers nadal wymagają prospectivefreeze+conformance. Nie zmieniono scientific gates lub modeli.\n',encoding='utf-8',newline='\n')
print({'decision':decision,'counts':counts,'charged':360,'remaining':530.4497597999289},flush=True)
