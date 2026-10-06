"""Fresh-cohort dispatch/schema guards; no native payload or research fitting."""
import ast
import copy
import json
from pathlib import Path
import pytest
from jsonschema.exceptions import ValidationError
from nextai_autoresearch.utils import project_root,load_json,sha256_file
from nextai_autoresearch.research_program import _study_scope
from nextai_autoresearch.schemas import validate_document
from nextai_autoresearch.config import load_config
from nextai_autoresearch.audit import audit_candidate
ROOT=project_root()
STUDY_PATH='research/plans/HAR01-INDEPENDENT-REPLICATION-V1.json'

def replication_plan():
 study=load_json(ROOT/STUDY_PATH)
 plan=load_json(ROOT/'research/plans/EXP-20261005-0006.json')
 plan.update(benchmark=study['cohort'],candidates=study['candidates'],matrix=study['matrix'])
 plan['research_program_protocol']={'authority_path':'research/laboratory/NEXTAI-TRANSFER-PROTOTYPE-PROGRAM-20261005-V1.json','program_contract_path':study['program_contract_path'],'program_contract_sha256':study['program_contract_sha256'],'study_path':STUDY_PATH,'study_sha256':sha256_file(ROOT/STUDY_PATH),'registration_ticket':2,**_study_scope(study)}
 return plan

def test_exact_replication_schema_rejects_recipe_gate_subject_and_cost_changes():
 plan=replication_plan();validate_document('experiment_plan',plan,ROOT)
 mutations=[('recipe','alignment_steps',8192),('recipe','dense_set_steps',2048),('data','train_pairs',2048),('reference_gates','known_false_abstention_maximum',.2)]
 for section,key,value in mutations:
  bad=copy.deepcopy(plan);bad['research_program_protocol'][section][key]=value
  with pytest.raises(ValidationError):validate_document('experiment_plan',bad,ROOT)
 for key,value in [('study_path','research/plans/HAR01-FROZEN-SOURCE-SCREEN-V1.json'),('fit_seconds_total_cap',9000),('task_contract_sha256','0'*64)]:
  bad=copy.deepcopy(plan);bad['research_program_protocol'][key]=value
  with pytest.raises(ValidationError):validate_document('experiment_plan',bad,ROOT)
 bad=copy.deepcopy(plan);bad['research_program_protocol']['data']['screen_subjects'][0]['dev_subject']=26
 with pytest.raises(ValidationError):validate_document('experiment_plan',bad,ROOT)
 bad=copy.deepcopy(plan);bad['matrix']['knowledge_sizes'][-1]=128
 with pytest.raises(ValidationError):validate_document('experiment_plan',bad,ROOT)

def test_models_and_old_science_bytes_unchanged_and_exact_45_audits():
 study=load_json(ROOT/STUDY_PATH);parent=load_json(ROOT/study['parent_study_path'])
 for key in ('recipe','diagnostics','diagnosis_gates','reference_gates','roles','candidates','decision_policy'):
  assert study[key]==parent[key]
 for path,digest in study['parent_bindings'].items():assert sha256_file(ROOT/path)==digest
 assert len(study['candidates'])==45 and len(study['roles'])==45
 for candidate in study['candidates']:assert audit_candidate(candidate,load_config(ROOT),ROOT).ok

def test_new_private_loader_forbidden_to_candidates(tmp_path):
 directory=tmp_path/'src/nextai_autoresearch/candidates';directory.mkdir(parents=True)
 (directory/'fresh_native_leak.py').write_text('from nextai_autoresearch.har01_task_v2 import load_unit\nclass Candidate: pass\n',encoding='utf-8')
 assert not audit_candidate('fresh_native_leak',load_config(ROOT),tmp_path).ok

def test_new_dispatch_excludes_consumed_har_seeds_and_nonces_before_scoring():
 text=(ROOT/'src/nextai_autoresearch/runner.py').read_text(encoding='utf-8');tree=ast.parse(text)
 branches=[n for n in ast.walk(tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='private_prefix == \'asm01\' or plan[\'benchmark\'] == \'har01_native_memory_v2\'']
 assert len(branches)==1
 body=ast.unparse(branches[0]);assert 'Consumed native seed/data collision; no replacement' in body
 assert 'native_plan' in body and 'native_private' in body and 'unit_nonces' in body
 native=[n for n in ast.walk(tree) if isinstance(n,ast.If) and 'har01_native_memory_v1' in ast.unparse(n.test) and 'har01_native_memory_v2' in ast.unparse(n.test)]
 assert native
 assert text.index('Consumed native seed/data collision; no replacement') < text.index('"event": "experiment_scoring_started"')

def test_independent_clone_package_provenance():
 import nextai_autoresearch
 assert ROOT.name=='NEXTAI-VALIDATION-20261002'
 assert Path(nextai_autoresearch.__file__).resolve().is_relative_to(ROOT/'src')
