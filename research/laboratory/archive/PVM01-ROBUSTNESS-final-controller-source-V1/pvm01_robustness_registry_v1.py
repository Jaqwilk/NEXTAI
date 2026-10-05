from pathlib import Path
import copy,json
from nextai_autoresearch.utils import sha256_file
b=Path.cwd();p=b/'config/baseline_semantics.json';registry=json.loads(p.read_text())
assert 'paired_view_mutable_memory_v8' not in registry['cohorts']
registry['cohorts'].append('paired_view_mutable_memory_v8')
study=json.loads((b/'research/plans/PVM01-DENSE-NOISE-ROBUSTNESS-V1.json').read_text())
test='tests/test_pvm01_dense_noise.py'
nodes=['test_augmentation_preserves_labels_shapes_inputs_and_noise_law','test_augmentation_is_seeded_independent_and_does_not_touch_torch_rng','test_mixed_dense_cache_fit_is_exact_and_alignment_is_unchanged','test_all85_roles_audited_and_analyzers_protected_before_data']
for name,role in study['roles'].items():
 if not role['arm'].endswith('_mixed'):continue
 oldname=f'pvm01_tc_{role["arm"].removesuffix("_mixed")}_s{role["seed_index"]}'
 record=copy.deepcopy(registry['baselines'][oldname]);record['baseline_id']=name
 old_alias=f'src/nextai_autoresearch/candidates/{oldname}.py'
 record['implementation_files'].pop(old_alias)
 for rel in [f'src/nextai_autoresearch/candidates/{name}.py','src/nextai_autoresearch/candidates/pvm01_dense_noise_core.py']:
  record['implementation_files'][rel]=sha256_file(b/rel)
 record['conformance_tests'].extend({'path':test,'node_id':test+'::'+node,'sha256':sha256_file(b/test)} for node in nodes)
 assert name not in registry['baselines'];registry['baselines'][name]=record
p.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
old=json.loads((b/'research/laboratory/archive/PVM01-ROBUSTNESS-previous-source-V1/config/baseline_semantics.json').read_text())
assert all(registry['baselines'][k]==v for k,v in old['baselines'].items())
print('Registered15 new semantic baselines; all historical records unchanged',flush=True)
