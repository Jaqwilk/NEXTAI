from pathlib import Path
from nextai_autoresearch.research_program import status,auxiliary_reserve
from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import load_json,atomic_write_json,sha256_file,utc_now
root=Path.cwd();identity='ASM01-EXPOSED-LEXICAL-DIAGNOSIS-V1';path=root/f'research/plans/{identity}.json';assert not path.exists()
directory=f'research/preparations/{identity}';assert not(root/directory).exists()
wallet=status(root);assert wallet['fit_seconds_remaining']-47000>=300 and not wallet['scoring_authorized']
old='research/data_manifests/ASM01-POINT-SERIAL-NATIVE-CONFORMANCE-V1.json';rawsha=load_json(root/old)['attempted_sample_text_sha256']['17:74']
names=['AGENTS.md','config/research.toml','research/state.json','research/eval_manifest.json','src/nextai_autoresearch/asm01_task.py','src/nextai_autoresearch/asm01_task_v4.py','research/preparations/ASM01-POINT-SERIAL-PREPARATION-V1/normalizer.py',old,'research/laboratory/ASM01-NATIVE-CONFORMANCE-COMPLETION-V1.receipt.json']
plan={'id':identity,'cycle':333,'created_at':utc_now(),'study_kind':'preparation_only','execution_authority':True,'clock_start':'2026-10-06T03:52:00Z','deadline':'2026-10-06T03:57:00Z','auxiliary_seconds_cap':300,'fit_seconds_cap':0,'EXP_cap':0,'registration_cap':0,'question':'Which redacted lexical class distinguishes the already-exposed failed17:74 from frozen accepted coordinate/metadata grammar?',
 'raw_scope':{'UID':'17:74','path':'research/data/asm01_native_v1/screen-text-v3/Online Handwritten Assamese Characters Dataset/W17/74.17.txt','sha256':rawsha,'read_once_only_after_all4fixtures_PASS':True,'already_exposed':True,'expected_point_rows':175,'expected_signedY_rows':3,'new_native_samples_authorized':0},
 'implementation_paths':[f'{directory}/classifier.py',f'{directory}/test_classifier.py'],
 'recipe':'Pure ASCII lexical classifier, bytes<=262144. For each four-token point row classify opaqueX/Y as unsigned,exact_minus_zero,other_minus_zero,minus_nonzero,other; -0 first, other-minus-zero means minus followedonlyzeros, minus-nonzero regex digits andatleastonenonzero. No int/float/Decimal or geometry/normalizer call. State1 and positive/in-range/nondecreasingserial compared usingcanonicaldecimalstrings andlen/lexicalorder only; envelope/count/header/knownmarkers/unknownrows reportedascounts/flags. Outputno tokens/names/coordinates/rowpositions. No repair or continuation.',
 'fixtures':{'ids':['categories','metadata','malformed','provenance'],'total':4,'single_run':True,'shortids':True,'scope':'Syntheticcategorytruth-table, state/serial/headermetadata violations, malformed/type/size/ASCII, pureAST/sourcehash/cloneorigin; no native or fit'},
 'metrics':['exact4syntheticfixturesPASS','oneknownrawSHA','175pointrows and3signedY count agreepriorinventory','counts of frozen lexicalclasses andmetadata violations','oldprotectedhashesunchanged','boundedprocesszero descendants'],
 'decision_rule':'Anyminus_nonzero coordinate confirms incompatibility with unchangedunsignedbounds, closeexactASMroute as intakeINCONCLUSIVE. Onlyother_minus_zero would support a separate prospective serialization question, never same-cycle repair/retry. Othergrammar violations remain separately counted. No learning/transfer/economics/scoring claim. Anyfixture/intake/binding failure stops unstarted scope.',
 'process_cap_seconds':60,'closing_allowance_seconds':90,'B_wallet_at_freeze':wallet,'parent_bindings':{n:sha256_file(root/n) for n in names},
 'forbidden':['coordinate/token/name emission','int/float conversion','geometry or nativeparser or normalizer invocation','new nativefile/sample','intake continuation','NPZ','fit/EXP/registration','model/geometry/grid/gate/code repair','retry','WT8-9','futurewriters','externalmodels/API','schedulechange','protected7tickets/47000s spending'],
 'full_goal_status':'ACTIVE, INCOMPLETE','prior_turn_classification':'PROGRESS:74exactnativecomparisons and1171validconversions; exactrequiredintake failed and preserved, narrowing nextdiagnostic to already-exposed17:74'}
atomic_write_json(path,plan)
append_jsonl(root/'research/events.jsonl',{'event':'maintenance_preparation_preregistered','created_at':utc_now(),'cycle':333,'plan_id':identity,'plan_sha256':sha256_file(path),'before_classifier_implementation_and_knownfile_read':True})
auxiliary_reserve(root,identity,300)
print({'plan_sha256':sha256_file(path),'reserved':300,'new_native_samples':0},flush=True)
