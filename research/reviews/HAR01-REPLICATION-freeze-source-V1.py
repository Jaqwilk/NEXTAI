from pathlib import Path
import subprocess
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
root=Path.cwd();paths=subprocess.check_output(['git','diff','--name-only'],text=True).splitlines()+subprocess.check_output(['git','ls-files','--others','--exclude-standard'],text=True).splitlines()
paths=[p for p in paths if p.endswith(('.py','.json','.toml'))]
for p in paths:
 path=root/p;data=path.read_text(encoding='utf-8-sig').replace('\r\n','\n');path.write_text(data,encoding='utf-8',newline='\n')
paths+=['src/nextai_autoresearch/har01_task.py','src/nextai_autoresearch/candidates/har01_core.py','src/nextai_autoresearch/benchmarks/har01_native_memory_v1.py','src/nextai_autoresearch/har01_analysis.py','tests/test_har01_native_transfer.py','tests/test_har01_intake.py','tests/test_har01_analysis_contract.py','tests/test_transfer_program_authority.py','tests/test_process_supervision.py']
atomic_write_json(root/'research/reviews/HAR01-REPLICATION-SOURCE-BINDING-V1.json',{'created_at':utc_now(),'study_sha256':'d5567973e85b444d95ac13a70db9fe24b87c0ab3b672932e8322862c336ad12a','before_only_conformance_and_fresh_intake':True,'files':{p:sha256_file(root/p) for p in sorted(set(paths))}})
print({'files':len(set(paths))},flush=True)
