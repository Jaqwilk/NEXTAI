from pathlib import Path
import json
from nextai_autoresearch.utils import sha256_file
b=Path.cwd();prereg=json.loads((b/'research/tmp/PVM01-FRESH-FINAL-preregistration-V1.json').read_text())
assert prereg['preregistration_git_commit']=='fe5c89cf05eda4c1c8c0a84971bebf7861fe3fba'
study=json.loads((b/'research/plans/PVM01-FRESH-FINAL-V1.json').read_text())
assert sha256_file(b/prereg['study_path'])==prereg['study_sha256']
for rel,digest in study['parent_evidence']['scientific_source_sha256_unchanged'].items():assert sha256_file(b/rel)==digest,rel
p=b/'src/nextai_autoresearch/research_program.py';s=p.read_text();needle='    return {**extra, **{key: study[key]';assert s.count(needle)==1
block='''    if study.get("study_kind") == "paired_view_frozen_fresh_final":
        extra.update(classical_economic_contract_path="research/plans/PVM01-FRESH-FINAL-CLASSICAL-ECONOMICS-V1.json",
                     classical_economic_contract_sha256="5f6565713391799b8aeb2f1a54e9a0faa976d6bde5ec1645618284aabd8cc5fb",
                     resource_measurement_version="cumulative_cuda_phase_peaks_v1",
                     evaluation_data_role="frozen_fresh_final_v1")
'''
s=s.replace(needle,block+needle,1)
s=s.replace('include_confirmation=False):','include_confirmation=False, include_base_reference=False):',1)
needle='    for identity, relative in previous.items():';assert s.count(needle)==1
block='''    if include_base_reference:
        if not all((include_latest, include_transport, include_replication, include_dense_noise, include_confirmation)):
            raise ValueError("Frozen fresh final requires all earlier PVM histories")
        previous["EXP-20261005-0005"] = "research/laboratory/archive/EXP-20261005-0005-runtime/research/tmp/EXP-20261005-0005"
'''
s=s.replace(needle,block+needle,1);s=s.replace('"paired_view_mutable_memory_v10")','"paired_view_mutable_memory_v10", "paired_view_mutable_memory_v11")')
p.write_text(s,encoding='utf-8',newline='\n')
p=b/'src/nextai_autoresearch/runner.py';s=p.read_text();s=s.replace('"paired_view_mutable_memory_v10")','"paired_view_mutable_memory_v10", "paired_view_mutable_memory_v11")').replace('"paired_view_mutable_memory_v10"}', '"paired_view_mutable_memory_v10", "paired_view_mutable_memory_v11"}')
needle='                    if plan["benchmark"] == "paired_view_mutable_memory_v10":';assert s.count(needle)==1
s=s.replace(needle,'''                    if plan["benchmark"] == "paired_view_mutable_memory_v11":
                        verify_pvm01_fresh_realization(base, evaluation_matrix["seeds"], unit_nonces, include_latest=True, include_transport=True, include_replication=True, include_dense_noise=True, include_confirmation=True, include_base_reference=True)
                    elif plan["benchmark"] == "paired_view_mutable_memory_v10":''',1)
p.write_text(s,encoding='utf-8',newline='\n')
p=b/'src/nextai_autoresearch/integrity.py';s=p.read_text();needle='    "scripts/analyze_pvm01_base_reference.py",';assert s.count(needle)==1
s=s.replace(needle,'    "scripts/analyze_pvm01_fresh_final.py",\n    "scripts/run_pvm01_fresh_final_check.py",\n'+needle,1);p.write_text(s,encoding='utf-8',newline='\n')
p=b/'schemas/experiment_plan.schema.json';s=json.loads(p.read_text())
props=s['properties']['research_program_protocol']['properties']
props['evaluation_data_role']={'const':'frozen_fresh_final_v1'}
props['classical_economic_contract_path']['enum'].append('research/plans/PVM01-FRESH-FINAL-CLASSICAL-ECONOMICS-V1.json')
# Preserve every older clause while extending its complete version inventory.
for item in s['allOf']:
    version=item.get('if',{}).get('properties',{}).get('benchmark',{})
    if 'paired_view_mutable_memory_v10' in version.get('enum',[]):version['enum'].append('paired_view_mutable_memory_v11')
    if version.get('const')=='paired_view_mutable_memory_v9':
        item['else']['if']['properties']['benchmark']['not']={'enum':['paired_view_mutable_memory_v10','paired_view_mutable_memory_v11']}
s['allOf'].append({'if':{'properties':{'benchmark':{'const':'paired_view_mutable_memory_v11'}},'required':['benchmark']},'then':{'properties':{'research_program_protocol':{'required':['resource_measurement_version','evaluation_data_role'],'properties':{'classical_economic_contract_path':{'const':'research/plans/PVM01-FRESH-FINAL-CLASSICAL-ECONOMICS-V1.json'},'classical_economic_contract_sha256':{'const':'5f6565713391799b8aeb2f1a54e9a0faa976d6bde5ec1645618284aabd8cc5fb'},'resource_measurement_version':{'const':'cumulative_cuda_phase_peaks_v1'},'evaluation_data_role':{'const':'frozen_fresh_final_v1'}}}},},'else':{'properties':{'research_program_protocol':{'properties':{'evaluation_data_role':False}}}}})
p.write_text(json.dumps(s,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
s=(b/'scripts/run_pvm01_base_reference_check.py').read_text().replace('cycle316 base-reference comparison','cycle317 frozen fresh final').replace('PVM01-BASE-REFERENCE-CONFIRMATION-V1','PVM01-FRESH-FINAL-V1').replace('PVM01-BASE-REFERENCE-','PVM01-FRESH-FINAL-')
(b/'scripts/run_pvm01_fresh_final_check.py').write_text(s,encoding='utf-8',newline='\n')
print('Prospectively frozen v11 scope/schema/dispatch integrated;112 scientific bytes unchanged')