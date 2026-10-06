from pathlib import Path
from copy import deepcopy
import json,re
from nextai_autoresearch.utils import sha256_file
root=Path.cwd();schema_path=root/'schemas/experiment_plan.schema.json';doc=json.loads(schema_path.read_text(encoding='utf-8'));old=[node for node in doc['allOf'] if node.get('if',{}).get('properties',{}).get('benchmark',{}).get('const')=='har01_native_memory_v1'];assert len(old)==1
study='research/plans/HAR01-INDEPENDENT-REPLICATION-V1.json';task='research/plans/HAR01-REPLICATION-TASK-V1.json'
changes={'har01_native_memory_v1':'har01_native_memory_v2','research/plans/HAR01-FROZEN-SOURCE-SCREEN-V1.json':study,'9ec218451704762a128415204a1b4f7aa6e016bac4a56122368e975f6d9013eb':sha256_file(root/study),'research/plans/HAR01-NATIVE-TASK-CONTRACT-V1.json':task,'73a28822fe3ea49a007d919350190415a67186ac402427bbd2367f902abe8672':sha256_file(root/task)}
def substitute(value):
 if isinstance(value,str):return changes.get(value,value)
 if isinstance(value,list):return [substitute(v) for v in value]
 if isinstance(value,dict):return {k:substitute(v) for k,v in value.items()}
 return value
new=substitute(deepcopy(old[0]));props=new['then']['properties']['research_program_protocol']['properties'];props['fit_seconds_total_cap']['const']=3600;props['data']['const']=json.loads((root/study).read_text())['data'] if 'const' in props['data'] else props['data'].get('const')
# Original data object uses nested exact properties, not a whole-object const.
if props['data'].get('const') is None:props['data'].pop('const',None)
if 'properties' in props['data'] and 'screen_subjects' in props['data']['properties']:props['data']['properties']['screen_subjects']={'const':json.loads((root/study).read_text())['data']['screen_subjects']}
doc['allOf'].append(new)
for values in (doc.get('properties',{}).get('benchmark',{}).get('enum',[]),):
 if 'har01_native_memory_v1' in values and 'har01_native_memory_v2' not in values:values.append('har01_native_memory_v2')
schema_path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
runner=root/'src/nextai_autoresearch/runner.py';text=runner.read_text(encoding='utf-8');text=text.replace('"har01_native_memory_v1", "asm01_native_memory_v2"','"har01_native_memory_v1", "har01_native_memory_v2", "asm01_native_memory_v2"');text=text.replace('if private_prefix == "asm01":','if private_prefix == "asm01" or plan["benchmark"] == "har01_native_memory_v2":');runner.write_text(text,encoding='utf-8',newline='\n')
audit=root/'src/nextai_autoresearch/audit.py';text=audit.read_text(encoding='utf-8').replace('"nextai_autoresearch.har01_task",','"nextai_autoresearch.har01_task",\n    "nextai_autoresearch.har01_task_v2",');audit.write_text(text,encoding='utf-8',newline='\n')
integrity=root/'src/nextai_autoresearch/integrity.py';text=integrity.read_text(encoding='utf-8').replace('FIXED_PROTECTED_FILES = (','FIXED_PROTECTED_FILES = (\n    "research/plans/HAR01-INDEPENDENT-REPLICATION-V1.json",\n    "research/plans/HAR01-REPLICATION-TASK-V1.json",\n    "research/laboratory/HAR01-REPLICATION-PREPARATION-AUTHORITY-V1.json",\n    "research/data_manifests/HAR01-REPLICATION-ACQUISITION-V1.json",\n    "scripts/acquire_har01_replication.py",\n    "scripts/check_har01_replication_readiness.py",\n    "scripts/run_har01_replication_experiment.py",\n    "scripts/analyze_har01_replication.py",');integrity.write_text(text,encoding='utf-8',newline='\n')
config=root/'config/research.toml';text=config.read_text(encoding='utf-8').replace('benchmark_version = "asm01_native_memory_v3"','benchmark_version = "har01_native_memory_v2"').replace('study_path = "research/plans/ASM01-FULL-SCREEN-GRAMMAR-INVENTORY-V3.json"',f'study_path = "{study}"');assert 'benchmark_status = "maintenance"' in text;config.write_text(text,encoding='utf-8',newline='\n')
print({'new_schema_branch':len(doc['allOf'])-1,'subject_binding':props['data'],'source_changes':'dispatch/schema/privacy/protection/config only'},flush=True)
