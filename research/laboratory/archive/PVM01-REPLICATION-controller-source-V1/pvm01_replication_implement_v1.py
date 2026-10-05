from pathlib import Path
import copy,json,subprocess
from nextai_autoresearch.utils import sha256_file
b=Path.cwd();study=json.loads((b/'research/plans/PVM01-INDEPENDENT-REPLICATION-V1.json').read_text())
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()=='430e4e45a249ce0ec69e335bb04adda7f81ff913'
addon_rel='research/plans/PVM01-REPLICATION-CLASSICAL-ECONOMICS-V1.json'
addon_hash=sha256_file(b/addon_rel)
p=b/'src/nextai_autoresearch/research_program.py';t=p.read_text()
old='''        extra.update(classical_economic_contract_path="research/plans/PVM01-TRANSPORT-CLASSICAL-ECONOMICS-V1.json",
                     classical_economic_contract_sha256="06688b5c493c08d701a236fedcfb549e27489ec7596715c73535b8d04fe7a512")'''
new=f'''        replication = study["cohort"] == "paired_view_mutable_memory_v7"
        extra.update(classical_economic_contract_path="{addon_rel}" if replication else "research/plans/PVM01-TRANSPORT-CLASSICAL-ECONOMICS-V1.json",
                     classical_economic_contract_sha256="{addon_hash}" if replication else "06688b5c493c08d701a236fedcfb549e27489ec7596715c73535b8d04fe7a512")'''
assert t.count(old)==1;t=t.replace(old,new)
old='def verify_pvm01_fresh_realization(base, seeds, nonces, *, include_latest=False):'
assert t.count(old)==1;t=t.replace(old,old.replace('include_latest=False','include_latest=False, include_transport=False'))
old='''    for identity, relative in previous.items():'''
new='''    if include_transport:
        if not include_latest:
            raise ValueError("Transport history requires capacity-exposure history")
        previous["EXP-20261005-0001"] = "research/laboratory/archive/EXP-20261005-0001-runtime/research/tmp/EXP-20261005-0001"
    for identity, relative in previous.items():'''
assert t.count(old)==1;t=t.replace(old,new)
old='"paired_view_mutable_memory_v6")'
assert t.count(old)==1;t=t.replace(old,'"paired_view_mutable_memory_v6", "paired_view_mutable_memory_v7")')
p.write_text(t,encoding='utf-8',newline='\n')
p=b/'src/nextai_autoresearch/runner.py';t=p.read_text()
assert t.count('"paired_view_mutable_memory_v6")')==1
t=t.replace('"paired_view_mutable_memory_v6")','"paired_view_mutable_memory_v6", "paired_view_mutable_memory_v7")')
assert t.count('"paired_view_mutable_memory_v6"}')==2
t=t.replace('"paired_view_mutable_memory_v6"}','"paired_view_mutable_memory_v6", "paired_view_mutable_memory_v7"}')
old='''                    if plan["benchmark"] == "paired_view_mutable_memory_v6":
                        verify_pvm01_fresh_realization(base, evaluation_matrix["seeds"], unit_nonces, include_latest=True)'''
new='''                    if plan["benchmark"] == "paired_view_mutable_memory_v7":
                        verify_pvm01_fresh_realization(base, evaluation_matrix["seeds"], unit_nonces, include_latest=True, include_transport=True)
                    elif plan["benchmark"] == "paired_view_mutable_memory_v6":
                        verify_pvm01_fresh_realization(base, evaluation_matrix["seeds"], unit_nonces, include_latest=True)'''
assert t.count(old)==1;t=t.replace(old,new)
p.write_text(t,encoding='utf-8',newline='\n')
p=b/'src/nextai_autoresearch/benchmarks/paired_view_mutable_memory_v7.py'
assert not p.exists()
p.write_text('''"""Independent replica: unchanged scientific v6 suite, fresh audited v7 realization."""
from . import paired_view_mutable_memory_v6 as selected

BENCHMARK_VERSION = "paired_view_mutable_memory_v7"


def run_suite(candidate_name, plan, trial_sink=None, phase_sink=None, fit_sink=None, data_sink=None):
    if plan.get("benchmark") != BENCHMARK_VERSION:
        raise ValueError("Replication cohort binding mismatch")
    return selected.run_suite(candidate_name, plan, trial_sink, phase_sink, fit_sink, data_sink)
''',encoding='utf-8',newline='\n')
p=b/'config/baseline_semantics.json';raw=p.read_bytes()
old=b'"paired_view_mutable_memory_v6"],'
assert raw.count(old)==1
p.write_bytes(raw.replace(old,b'"paired_view_mutable_memory_v6", "paired_view_mutable_memory_v7"],'))
p=b/'schemas/experiment_plan.schema.json';s=json.loads(p.read_text())
props=s['properties']['research_program_protocol']['properties']
old_path=props['classical_economic_contract_path']['const'];old_hash=props['classical_economic_contract_sha256']['const']
props['classical_economic_contract_path']={'type':'string','enum':[old_path,addon_rel]}
props['classical_economic_contract_sha256']={'type':'string','enum':[old_hash,addon_hash]}
s['allOf'][64]['if']['properties']['benchmark']['enum'].append('paired_view_mutable_memory_v7')
s['allOf'][65]['if']['properties']['benchmark']={'enum':['paired_view_mutable_memory_v6','paired_view_mutable_memory_v7']}
for version,path,digest in [('paired_view_mutable_memory_v6',old_path,old_hash),('paired_view_mutable_memory_v7',addon_rel,addon_hash)]:
 s['allOf'].append({'if':{'properties':{'benchmark':{'const':version}},'required':['benchmark']},
 'then':{'properties':{'research_program_protocol':{'properties':{
 'classical_economic_contract_path':{'const':path},'classical_economic_contract_sha256':{'const':digest}}}}}})
p.write_text(json.dumps(s,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
wrapper=(b/'scripts/run_pvm01_transport_check.py').read_text()
wrapper=wrapper.replace('immutable cycle312 contract','immutable cycle313 replication contract')
wrapper=wrapper.replace('PVM01-TRANSPORT-COMPRESSION-ADVERSE-V2.json','PVM01-INDEPENDENT-REPLICATION-V1.json').replace('PVM01-TRANSPORT-','PVM01-REPLICATION-')
(b/'scripts/run_pvm01_replication_check.py').write_text(wrapper,encoding='utf-8',newline='\n')
for rel,digest in study['independent_replication']['scientific_source_sha256_unchanged'].items():assert sha256_file(b/rel)==digest,rel
print('Minimal v7 integration implemented; all80 scientific source files unchanged',flush=True)
