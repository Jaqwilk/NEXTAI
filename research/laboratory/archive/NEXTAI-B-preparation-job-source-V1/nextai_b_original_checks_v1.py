from pathlib import Path
import os,subprocess
from nextai_autoresearch.utils import atomic_write_json,sha256_file,utc_now
clone=Path(__file__).resolve().parents[2]
original=clone.parent/'NEXTAI'
env=os.environ.copy();env.update(PYTHONPATH=str(original/'src'),NEXTAI_PROJECT_ROOT=str(original),PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
commands=[['uv','run','--no-sync','python',str(clone/'scripts/check_transfer_preparation.py'),'--original'],['uv','run','--no-sync','nextai','doctor'],['uv','run','--no-sync','nextai','lab','status'],['uv','run','--no-sync','pytest','-q','tests/test_muc01_activation.py','tests/test_transfer_program_authority.py','tests/test_source_metadata.py','tests/test_research_continuation.py','tests/test_muc03_program.py','tests/test_integrity_and_schemas.py::test_repository_documents_validate','tests/test_protocol_v2.py::test_checked_in_research_lifecycle_is_consistent','--junitxml='+str(clone/'research/reviews/NEXTAI-B-original-gates-V1.xml')]]
for command in commands:subprocess.run(command,cwd=original,env=env,check=True)
assert not subprocess.check_output(['git','status','--porcelain'],cwd=original)
print('Original doctor/lab,history,source states and59 authority/schema/lifecycle tests passed',flush=True)
