from pathlib import Path
import json,subprocess
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
from nextai_autoresearch.report import write_report
b=Path.cwd()
subprocess.run(['uv','run','--no-sync','python','research/tmp/pvm01_confirmation_history_v1.py'],check=True)
write_report(b)
paths=[x for x in subprocess.check_output(['git','ls-files','-m','-o','--exclude-standard','-z']).decode().split('\0') if x]
allowed=('research/REPORT','research/events.jsonl','research/eval_manifest.json','research/checks/PVM01-CONFIRMATION-','research/reviews/PVM01-CONFIRMATION-','research/plans/PVM01-CONFIRMATION-','research/laboratory/PVM01-','research/laboratory/archive/PVM01-CONFIRMATION-','research/laboratory/preflight_certificate','research/laboratory/archive/preflight','research/laboratory/certificates/','research/manifests/')
exact={'config/research.toml','schemas/experiment_plan.schema.json','src/nextai_autoresearch/research_program.py','src/nextai_autoresearch/runner.py','src/nextai_autoresearch/integrity.py','src/nextai_autoresearch/worker_resources.py','src/nextai_autoresearch/worker_resource_peaks.py','src/nextai_autoresearch/benchmarks/paired_view_mutable_memory_v9.py','tests/test_pvm01_confirmation.py','scripts/analyze_pvm01_confirmation.py','scripts/run_pvm01_confirmation_check.py'}
for rel in paths:
    assert rel in exact or rel.startswith(allowed),rel
    assert (b/rel).stat().st_size<99_000_000,rel
for i in range(0,len(paths),100): subprocess.run(['git','add','--',*paths[i:i+100]],check=True)
files=('research/checks/PVM01-CONFIRMATION-targeted-V1.xml','research/checks/PVM01-CONFIRMATION-full-V2.xml','schemas/experiment_plan.schema.json','src/nextai_autoresearch/worker_resource_peaks.py','tests/test_pvm01_confirmation.py')
proof={}
for policy in ('false','true'):
    checkout=b/f'research/tmp/PVM01-CONFIRMATION-native-checkout-{policy}-V1'; assert not checkout.exists(); checkout.mkdir()
    subprocess.run(['git','-c','core.autocrlf='+policy,'checkout-index','--prefix='+checkout.as_posix()+'/', '--',*files],check=True)
    proof[policy]={name:sha256_file(checkout/name) for name in files}
    assert all(proof[policy][name]==sha256_file(b/name) for name in files)
atomic_write_json(b/'research/checks/PVM01-CONFIRMATION-native-checkout-V1.json',{'created_at':utc_now(),'files':proof,'same_native_bytes_under_both_autocrlf_policies':True,'old_records_unchanged':True})
subprocess.run(['git','add','--','research/checks/PVM01-CONFIRMATION-native-checkout-V1.json'],check=True)
subprocess.run(['git','-c','core.whitespace=-blank-at-eof,cr-at-eol','diff','--cached','--check'],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['git','commit','-q','-m','Validate independent confirmation with unchanged recipes and trusted CUDA/RSS evidence'],check=True)
print('Validated source',subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),flush=True)
