"""Prospective metadata-only intake correction; no coordinate/fit outcome is available."""
from copy import deepcopy
from pathlib import Path
import json

from nextai_autoresearch.ledger import append_jsonl
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now

root=Path(__file__).resolve().parents[1]
old_study='research/plans/ASM01-FROZEN-SOURCE-SCREEN-V1.json'
old_task='research/plans/ASM01-PROSPECTIVE-NATIVE-TASK-V1.json'
task_path='research/plans/ASM01-CANONICAL-NATIVE-TASK-V2.json'
study_path='research/plans/ASM01-FROZEN-SOURCE-SCREEN-V2.json'
assert not (root/task_path).exists() and not (root/study_path).exists()
evidence='research/reviews/ASM01-DUPLICATE-LOCATION-METADATA-V1.json'
proof=json.loads((root/evidence).read_text(encoding='utf-8'))
assert proof['native_coordinate_files_parsed']==0 and proof['publisher_sha256']=='d6ad543e65269d53e38fdac6a32dd20bcd942e7616891a6cf95986894b454a4d'
exception='Online Handwritten Assamese Characters Dataset/W6/15.5.TXT'
assert proof['duplicates']==[{'writer':5,'character':15,'files':[
    {'path':'Online Handwritten Assamese Characters Dataset/W5/15.5.TXT','bytes':5572},
    {'path':exception,'bytes':9459}]}]
for w in range(1,46):
    expected={str(w):183}
    if w==6:
        expected['5']=1
    assert proof['folder_writer_counts'][f'Online Handwritten Assamese Characters Dataset/W{w}']==expected
task=deepcopy(json.loads((root/old_task).read_text(encoding='utf-8')))
task.update(id='ASM01-CANONICAL-NATIVE-TASK-V2',created_at=utc_now(),cohort='asm01_native_memory_v2',
            metadata_correction_evidence_path=evidence,metadata_correction_evidence_sha256=sha256_file(root/evidence),
            original_task_path=old_task,original_task_sha256=sha256_file(root/old_task),
            revision_reason='Exactly one foreign filename within W6; all45 canonical Wn folders contain183 matching M.n files. Original V1 intake is invalid and preserved. No coordinates, model fit, scoring or paid registration seen; replace only the prospective native archive-membership rule, never scientific metrics/recipe/budgets.')
task['independent_units']['archive_identity_gate']='Require exactly45 Wn native writer folders, each with183 distinct M.n.txt entries whose filename writer n agrees with folder Wn, total8235. No missing/duplicate canonical sample allowed. Exactly one publisher foreign member W6/15.5.TXT (9459bytes) is excluded from the legal membership map, preserved in archive, never numerically read. No other exception or sample/writer substitution.'
task['intake'].update(publisher_sha256=proof['publisher_sha256'],reuse_preserved_archive_without_new_download=True,
                      excluded_foreign_member=dict(path=exception,bytes=9459),new_coordinate_access_before_preregistration=False)
atomic_write_json(root/task_path,task)
study=deepcopy(json.loads((root/old_study).read_text(encoding='utf-8')))
study.update(id='ASM01-FROZEN-SOURCE-SCREEN-V2',created_at=utc_now(),cohort='asm01_native_memory_v2',
             task_contract_path=task_path,task_contract_sha256=sha256_file(root/task_path),
             invalid_parent_study_path=old_study,invalid_parent_study_sha256=sha256_file(root/old_study),
             metadata_only_intake_revision='Only canonical Wn/M.n membership before any coordinate content; V1 failure remains immutable. Not a model/dev rescue or paid retry. Shared original180min deadline,3600s auxiliary and9000s fullworker caps include all V1 failures.')
study['data']['acquisition']=task['intake'];study['data']['independent_units']=task['independent_units']
study['native_parser']['filename_identity']=task['independent_units']['archive_identity_gate']
atomic_write_json(root/study_path,study)
for key in ('candidates','roles','matrix','resources','recipe','diagnostics','diagnosis_gates','reference_gates','source_evidence','cost_boundary'):
    assert study[key]==json.loads((root/old_study).read_text(encoding='utf-8'))[key],key
append_jsonl(root/'research/events.jsonl',dict(event='research_study_preimplementation_intake_invalidated',created_at=utc_now(),cycle=321,
             program_id='NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1',study_path=old_study,study_sha256=sha256_file(root/old_study),
             reason='Extra conflicting filename in publisher W6 directory; zero coordinate parsing, fit, registration or scoring.',
             evidence_path=evidence,evidence_sha256=sha256_file(root/evidence)))
append_jsonl(root/'research/events.jsonl',dict(event='research_study_preregistered',created_at=utc_now(),cycle=321,
             program_id='NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1',study_path=study_path,study_sha256=sha256_file(root/study_path),
             before_implementation=True,before_native_coordinate_content=True,preserves_invalid_parent=True))
print(json.dumps(dict(study_path=study_path,study_sha256=sha256_file(root/study_path),task_sha256=sha256_file(root/task_path),
                      all_scientific_recipes_metrics_gates_and_shared_caps_unchanged=True,new_paid_registrations=0)))
