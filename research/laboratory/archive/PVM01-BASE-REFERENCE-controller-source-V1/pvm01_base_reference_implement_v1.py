from pathlib import Path
import json,subprocess
from nextai_autoresearch.utils import sha256_file
b=Path.cwd();r=json.loads((b/'research/tmp/PVM01-BASE-REFERENCE-preregistration-V1.json').read_text(encoding='utf-8'))
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==r['preregistration_git_commit']
s=json.loads((b/r['study_path']).read_text(encoding='utf-8'));assert sha256_file(b/r['study_path'])==r['study_sha256']
addon='research/plans/PVM01-BASE-REFERENCE-CLASSICAL-ECONOMICS-V1.json';digest=sha256_file(b/addon)
def edit(rel,changes):
    p=b/rel;t=p.read_text(encoding='utf-8')
    for old,new,count in changes:
        assert t.count(old)==count,(rel,old,t.count(old));t=t.replace(old,new)
    p.write_text(t,encoding='utf-8',newline='\n')
edit('src/nextai_autoresearch/research_program.py',[
    ('    return {**extra, **{key: study[key] for key in',f'''    if study.get("study_kind") == "paired_view_unaugmented_reference_confirmation":
        extra.update(classical_economic_contract_path="{addon}",
                     classical_economic_contract_sha256="{digest}",
                     resource_measurement_version="cumulative_cuda_phase_peaks_v1")
    return {{**extra, **{{key: study[key] for key in''',1),
    ('include_dense_noise=False):','include_dense_noise=False, include_confirmation=False):',1),
    ('    for identity, relative in previous.items():','''    if include_confirmation:
        if not all((include_latest, include_transport, include_replication, include_dense_noise)):
            raise ValueError("Base-reference comparison requires all earlier PVM histories")
        previous["EXP-20261005-0004"] = "research/laboratory/archive/EXP-20261005-0004-runtime/research/tmp/EXP-20261005-0004"
    for identity, relative in previous.items():''',1),
    ('"paired_view_mutable_memory_v9")','"paired_view_mutable_memory_v9", "paired_view_mutable_memory_v10")',1)])
edit('src/nextai_autoresearch/runner.py',[
    ('"paired_view_mutable_memory_v9")','"paired_view_mutable_memory_v9", "paired_view_mutable_memory_v10")',1),
    ('"paired_view_mutable_memory_v9"}','"paired_view_mutable_memory_v9", "paired_view_mutable_memory_v10"}',2),
    ('                    if plan["benchmark"] == "paired_view_mutable_memory_v9":','''                    if plan["benchmark"] == "paired_view_mutable_memory_v10":
                        verify_pvm01_fresh_realization(base, evaluation_matrix["seeds"], unit_nonces, include_latest=True, include_transport=True, include_replication=True, include_dense_noise=True, include_confirmation=True)
                    elif plan["benchmark"] == "paired_view_mutable_memory_v9":''',1)])
edit('src/nextai_autoresearch/integrity.py',[
    ('FIXED_PROTECTED_FILES = (','FIXED_PROTECTED_FILES = (\n    "scripts/analyze_pvm01_base_reference.py",\n    "scripts/run_pvm01_base_reference_check.py",',1)])
wrapper=(b/'src/nextai_autoresearch/benchmarks/paired_view_mutable_memory_v9.py').read_text(encoding='utf-8').replace('Independent new units; frozen models/task and service measurement law.','Distinct prospective reference question; unchanged scientific worker law.').replace('paired_view_mutable_memory_v8 as selected','paired_view_mutable_memory_v9 as selected').replace('BENCHMARK_VERSION = "paired_view_mutable_memory_v9"','BENCHMARK_VERSION = "paired_view_mutable_memory_v10"').replace('Independent confirmation cohort binding mismatch','Base-reference cohort binding mismatch')
p=b/'src/nextai_autoresearch/benchmarks/paired_view_mutable_memory_v10.py';assert not p.exists();p.write_text(wrapper,encoding='utf-8',newline='\n')
wrapper=(b/'scripts/run_pvm01_confirmation_check.py').read_text(encoding='utf-8').replace('cycle315 independent confirmation','cycle316 base-reference comparison').replace('PVM01-DENSE-NOISE-CONFIRMATION-V1.json','PVM01-BASE-REFERENCE-CONFIRMATION-V1.json').replace('PVM01-CONFIRMATION-','PVM01-BASE-REFERENCE-')
p=b/'scripts/run_pvm01_base_reference_check.py';assert not p.exists();p.write_text(wrapper,encoding='utf-8',newline='\n')
p=b/'schemas/experiment_plan.schema.json';schema=json.loads(p.read_text(encoding='utf-8'));props=schema['properties']['research_program_protocol']['properties']
props['classical_economic_contract_path']['enum'].append(addon);props['classical_economic_contract_sha256']['enum'].append(digest)
for clause in schema['allOf']:
    benchmark=clause.get('if',{}).get('properties',{}).get('benchmark',{})
    if 'paired_view_mutable_memory_v9' in benchmark.get('enum',[]):benchmark['enum'].append('paired_view_mutable_memory_v10')
    if benchmark.get('const')=='paired_view_mutable_memory_v9':
        assert clause['else']=={'properties':{'research_program_protocol':{'properties':{'resource_measurement_version':False}}}}
        clause['else']={'if':{'properties':{'benchmark':{'not':{'const':'paired_view_mutable_memory_v10'}}},'required':['benchmark']},'then':clause['else']}
schema['allOf'].append({'if':{'properties':{'benchmark':{'const':'paired_view_mutable_memory_v10'}},'required':['benchmark']},'then':{'properties':{'research_program_protocol':{'required':['resource_measurement_version'],'properties':{'classical_economic_contract_path':{'const':addon},'classical_economic_contract_sha256':{'const':digest},'resource_measurement_version':{'const':'cumulative_cuda_phase_peaks_v1'}}}}}})
p.write_text(json.dumps(schema,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
# Preserve the observed native startup JSON, including the initial CRLF bytes.
p=b/'.gitattributes';p.write_bytes(p.read_bytes()+b'\n# Startup observation is hash-bound to native Windows bytes.\nresearch/reviews/PVM01-BASE-REFERENCE-startup*.json -text\n')
subprocess.run(['git','add','--renormalize','--','research/reviews/PVM01-BASE-REFERENCE-startup-observation-V1.json'],check=True)
for rel,digest in s['parent_evidence']['scientific_source_sha256_unchanged'].items():assert sha256_file(b/rel)==digest,rel
print('Audited v10 dispatch/schema/freshness; all107 selected scientific source bytes unchanged',flush=True)