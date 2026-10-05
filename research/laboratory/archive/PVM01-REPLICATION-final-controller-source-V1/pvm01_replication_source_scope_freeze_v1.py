from pathlib import Path
import json
from nextai_autoresearch.integrity import freeze_manifest
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.report import write_report
b=Path.cwd()
old=json.loads((b/'research/laboratory/archive/PVM01-SOURCE-SCOPE-METADATA-REPAIR-V1-before/schemas/source.schema.json').read_text())
new=json.loads((b/'schemas/source.schema.json').read_text())
declared=new['properties'].pop('checked_scope')
assert old==new and declared=={'type':'string','minLength':1,'maxLength':1024,'pattern':r'\S'}
assert new['additionalProperties'] is False
freeze_manifest(b,overwrite=True);write_preflight_certificate(b);write_report(b)
print('Exactly one optional typed scope field; strict source validation unchanged')
