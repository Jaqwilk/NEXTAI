from pathlib import Path
import copy,json,subprocess
from nextai_autoresearch.utils import sha256_file
b=Path.cwd();study=json.loads((b/'research/plans/PVM01-DENSE-NOISE-ROBUSTNESS-V1.json').read_text())
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()=='e2342788c37e9bcb7d80db9331e9c2e825c695cf'
addon_rel='research/plans/PVM01-ROBUSTNESS-CLASSICAL-ECONOMICS-V1.json';addon_hash=sha256_file(b/addon_rel)
p=b/'src/nextai_autoresearch/research_program.py';t=p.read_text()
needle='    return {**extra, **{key: study[key] for key in'
assert t.count(needle)==1
t=t.replace(needle,f'''    if study.get("study_kind") == "paired_view_dense_noise_robustness":
        extra.update(classical_economic_contract_path="{addon_rel}",
                     classical_economic_contract_sha256="{addon_hash}")
'''+needle)
needle='def verify_pvm01_fresh_realization(base, seeds, nonces, *, include_latest=False, include_transport=False):'
assert t.count(needle)==1;t=t.replace(needle,needle.replace('include_transport=False','include_transport=False, include_replication=False'))
needle='    for identity, relative in previous.items():'
assert t.count(needle)==1;t=t.replace(needle,'''    if include_replication:
        if not include_latest or not include_transport:
            raise ValueError("Replication history requires all earlier PVM histories")
        previous["EXP-20261005-0002"] = "research/laboratory/archive/EXP-20261005-0002-runtime/research/tmp/EXP-20261005-0002"
'''+needle)
assert t.count('"paired_view_mutable_memory_v7")')==1;t=t.replace('"paired_view_mutable_memory_v7")','"paired_view_mutable_memory_v7", "paired_view_mutable_memory_v8")')
p.write_text(t,encoding='utf8',newline='\n')
p=b/'src/nextai_autoresearch/runner.py';t=p.read_text()
assert t.count('"paired_view_mutable_memory_v7")')==1;t=t.replace('"paired_view_mutable_memory_v7")','"paired_view_mutable_memory_v7", "paired_view_mutable_memory_v8")')
assert t.count('"paired_view_mutable_memory_v7"}')==2;t=t.replace('"paired_view_mutable_memory_v7"}','"paired_view_mutable_memory_v7", "paired_view_mutable_memory_v8"}')
needle='                    if plan["benchmark"] == "paired_view_mutable_memory_v7":'
assert t.count(needle)==1;t=t.replace(needle,'''                    if plan["benchmark"] == "paired_view_mutable_memory_v8":
                        verify_pvm01_fresh_realization(base, evaluation_matrix["seeds"], unit_nonces, include_latest=True, include_transport=True, include_replication=True)
                    elif plan["benchmark"] == "paired_view_mutable_memory_v7":''')
p.write_text(t,encoding='utf8',newline='\n')
for name,role in study['roles'].items():
 if role['arm'].endswith('_mixed'):
  p=b/f'src/nextai_autoresearch/candidates/{name}.py';assert not p.exists()
  p.write_text('from .pvm01_dense_noise_core import Candidate as Reference\n\n\nclass Candidate(Reference):\n    pass\n',encoding='utf8',newline='\n')
p=b/'schemas/experiment_plan.schema.json';s=json.loads(p.read_text());props=s['properties']['research_program_protocol']['properties']
props['classical_economic_contract_path']['enum'].append(addon_rel);props['classical_economic_contract_sha256']['enum'].append(addon_hash)
s['allOf'][64]['if']['properties']['benchmark']['enum'].append('paired_view_mutable_memory_v8')
s['allOf'][65]['if']['properties']['benchmark']['enum'].append('paired_view_mutable_memory_v8')
s['allOf'].append({'if':{'properties':{'benchmark':{'const':'paired_view_mutable_memory_v8'}},'required':['benchmark']},'then':{'properties':{'research_program_protocol':{'properties':{'classical_economic_contract_path':{'const':addon_rel},'classical_economic_contract_sha256':{'const':addon_hash}}}}}})
p.write_text(json.dumps(s,ensure_ascii=False)+'\n',encoding='utf8',newline='\n')
wrapper=(b/'scripts/run_pvm01_replication_check.py').read_text().replace('immutable cycle313 replication contract','immutable cycle314 dense-noise contract').replace('PVM01-INDEPENDENT-REPLICATION-V1.json','PVM01-DENSE-NOISE-ROBUSTNESS-V1.json').replace('PVM01-REPLICATION-','PVM01-ROBUSTNESS-')
(b/'scripts/run_pvm01_dense_noise_check.py').write_text(wrapper,encoding='utf8',newline='\n')
p=b/'src/nextai_autoresearch/integrity.py';t=p.read_text();needle='FIXED_PROTECTED_FILES = (';assert t.count(needle)==1
t=t.replace(needle,needle+'\n    "scripts/analyze_pvm01_replication.py",\n    "scripts/run_pvm01_replication_check.py",\n    "scripts/analyze_pvm01_dense_noise.py",\n    "scripts/run_pvm01_dense_noise_check.py",')
p.write_text(t,encoding='utf8',newline='\n')
for rel,digest in study['parent_evidence']['scientific_source_sha256_unchanged'].items():assert sha256_file(b/rel)==digest,rel
print('Implemented minimal training-noise wrapper and audited v8 integration; original80 scientific sources unchanged',flush=True)
