from pathlib import Path
import copy,importlib.util,json
from nextai_autoresearch.research_program import _study_scope
from nextai_autoresearch.utils import atomic_write_json,sha256_file,sha256_json
b=Path.cwd();root=b/'research/reviews/PVM01-TRANSPORT-analyzer-fixture-V3/fake-root';study=copy.deepcopy(json.loads((b/'research/plans/PVM01-TRANSPORT-COMPRESSION-ADVERSE-V2.json').read_text()));study['recipe'].update(alignment_steps=2,dense_set_steps=2)
relative='research/plans/fixed-statistical-fixture.json';atomic_write_json(root/relative,study)
addon_relative='research/plans/PVM01-TRANSPORT-CLASSICAL-ECONOMICS-V1.json'; addon=json.loads((b/addon_relative).read_text()); addon['parent_study_sha256']=sha256_file(root/relative); atomic_write_json(root/addon_relative,addon)
plan=copy.deepcopy(json.loads((b/'research/plans/EXP-20261004-0008.json').read_text()));plan.update(experiment_id='EXP-20990101-9801',candidates=study['candidates'],benchmark=study['cohort']);plan['research_program_protocol'].update(_study_scope(study),study_path=relative,study_sha256=sha256_file(root/relative));plan['research_program_protocol']['classical_economic_contract_sha256']=sha256_file(root/addon_relative);atomic_write_json(root/'research/plans/EXP-20990101-9801.json',plan)
report={'initial_parameters_sha256':'init','final_encoder_sha256':'trained','alignment_losses':[.1,.05],'optimizer_steps':2,'final_decoder_sha256':'decoder','dense_set_losses':[.2,.1],'pca_projection_sha256':'PCA','pca_grid':[{'rank':16}],'pca_choice':{'rank':16},'fp32_ridge_weights_sha256':'ridge','train_pairs_sha256':'T','training_validation_sha256':'Tv','calibration_sha256':'Tc','training_sets_sha256':{'32':'s32','128':'s128'},'fit_policy_snapshot':{'deterministic':True,'warn_only':False,'math_sdp':True,'efficient_sdp':False,'flash_sdp':False,'cudnn_sdp':False}}
pred={'answer':7,'top_handle':1,'top_value':7,'truth':7,'target_handle':1,'stratum':'retained','decision_score':.99}
outcomes=[]
for name,role in study['roles'].items():
 arm=role['arm'];r=copy.deepcopy(report)
 if arm=='transport_pca_untrained':r.update(final_encoder_sha256='init',alignment_losses=[],optimizer_steps=0)
 rows=[]
 for noise in (.02,.04):
  for k in (32,128,512):
   for updates in (0,1,4):
    rows.append({'observation_noise':noise,'knowledge_size':k,'update_rounds':updates,'fit_report_sha256':sha256_json(r),'dev_sha256':f'D{noise}/{k}/{updates}','truth_pair_sha256':f'truth{k}/{updates}','accuracy':.5 if 'untrained' in arm or 'shuffled' in arm else .99,'dense_unknown_rejection':.99,'known_false_abstention':0.,'retained_known_accuracy':.99,'updated_known_accuracy':.99,'latency_samples_us':[10. if arm.startswith('transport') else 30.]*320,'state_bytes':100 if arm.startswith('transport') else 50 if arm.startswith('ridge') else 1000,'full_workload_seconds':.1 if arm.startswith('transport') else .01 if arm.startswith('ridge') else 1.,'measurements':[{'predictions':[pred]*320}] if arm.startswith('dense') else []})
 rows[0]['fit_report']=r
 outcomes.append({'candidate':name,'status':'complete','trials':rows,'execution':{'supervised_fit_seconds':0.,'research_compute_seconds':0.,'wall_seconds':0.,'peak_rss_bytes':1000}})
result={'plan_sha256':sha256_json(plan),'candidates':outcomes};path=root/'research/results/EXP-20990101-9801.json';atomic_write_json(path,result,compact=True)
spec=importlib.util.spec_from_file_location('transport_analysis_fixture',b/'scripts/analyze_pvm01_transport.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
a=module.analyze(root,'EXP-20990101-9801');assert a['valid_comparison'] and a['decision'].startswith('KEEP') and all(a['primary_gates'].values());assert not a['economic_screen_qualified'] and a['descriptive_classical_dominators']
# Separate fixture identity retains the good input bytes; tiny exact loss drift must invalidate.
badplan=copy.deepcopy(plan);badplan['experiment_id']='EXP-20990101-9802';atomic_write_json(root/'research/plans/EXP-20990101-9802.json',badplan)
bad=copy.deepcopy(result);bad['plan_sha256']=sha256_json(badplan)
for item in bad['candidates']:
 if 'dense_cached_cpu_s0' in item['candidate']:
  r=item['trials'][0]['fit_report'];r['dense_set_losses'][1]+=1e-8
  for row in item['trials']:row['fit_report_sha256']=sha256_json(r)
atomic_write_json(root/'research/results/EXP-20990101-9802.json',bad,compact=True);v=module.analyze(root,'EXP-20990101-9802');assert not v['valid_comparison'] and v['decision']=='INCONCLUSIVE comparison'
atomic_write_json(b/'research/reviews/PVM01-TRANSPORT-analyzer-fixture-V3.json',{'statistical_fixture_only':True,'private_arrays_fit_registration':False,'good_valid_keep':True,'classical_dominance_prevents_economic_qualification':True,'tiny_exact_decoder_loss_drift_invalidates':True,'synthetic_inputs_sha256':{p.name:sha256_file(p) for p in (path,root/'research/results/EXP-20990101-9802.json')}});print('Stored analyzer end-to-end valid/null/dominance/exact drift: PASS; no models/data fit')

# A tiny quality difference within the original2pp margin cannot hide classical cost dominance.
near=copy.deepcopy(result); nearplan=copy.deepcopy(plan);nearplan['experiment_id']='EXP-20990101-9803';near['plan_sha256']=sha256_json(nearplan)
for outcome in near['candidates']:
 if outcome['candidate'].split('pvm01_tc_')[1].rsplit('_s',1)[0] in addon['controls']:
  for row in outcome['trials']:row['accuracy']=.989
atomic_write_json(root/'research/plans/EXP-20990101-9803.json',nearplan);atomic_write_json(root/'research/results/EXP-20990101-9803.json',near,compact=True)
x=module.analyze(root,'EXP-20990101-9803');assert not x['descriptive_classical_dominators'] and x['matched_quality_classical_dominators'] and not x['economic_screen_qualified']
# Remove domination, then make one K's absence quality fail while the overall mean still passes.
free=copy.deepcopy(near);freeplan=copy.deepcopy(plan);freeplan['experiment_id']='EXP-20990101-9804';free['plan_sha256']=sha256_json(freeplan)
for outcome in free['candidates']:
 if outcome['candidate'].split('pvm01_tc_')[1].rsplit('_s',1)[0] in addon['controls']:
  for row in outcome['trials']:row['state_bytes']=10000;row['full_workload_seconds']=2.
atomic_write_json(root/'research/plans/EXP-20990101-9804.json',freeplan);atomic_write_json(root/'research/results/EXP-20990101-9804.json',free,compact=True)
x=module.analyze(root,'EXP-20990101-9804');assert x['economic_screen_qualified']
weak=copy.deepcopy(free);weakplan=copy.deepcopy(plan);weakplan['experiment_id']='EXP-20990101-9805';weak['plan_sha256']=sha256_json(weakplan)
for outcome in weak['candidates']:
 if 'transport_pca_s' in outcome['candidate']:
  for row in outcome['trials']:
   if row['observation_noise']==.04 and row['knowledge_size']==32:row['dense_unknown_rejection']=.90
atomic_write_json(root/'research/plans/EXP-20990101-9805.json',weakplan);atomic_write_json(root/'research/results/EXP-20990101-9805.json',weak,compact=True)
x=module.analyze(root,'EXP-20990101-9805');assert x['valid_comparison'] and x['decision'].startswith('KEEP') and not x['economic_screen_qualified'] and not x['economic_quality_guards']['0.04:K32:transport_pca']
atomic_write_json(b/'research/reviews/PVM01-TRANSPORT-classical-economic-conformance-V2.json',{'fixture_only':True,'models_fit_private_data_registration':False,'tiny_point_quality_difference_does_not_hide_classical_dominance':True,'per_K_unknown_failure_rejects_economics_despite_overall_competence':True,'exact_loss_drift_remains_invalid':True});print('New preregistered classical/per-K economic controls: PASS')
