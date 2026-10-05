from pathlib import Path
import json, subprocess
from nextai_autoresearch.integrity import freeze_manifest
from nextai_autoresearch.baseline_semantics import write_preflight_certificate
from nextai_autoresearch.utils import sha256_file
b=Path.cwd();p=b/"schemas/experiment_plan.schema.json";s=json.loads(p.read_text());props=s["properties"]["research_program_protocol"]["properties"]
props["classical_economic_contract_path"]={"type":"string","const":"research/plans/PVM01-TRANSPORT-CLASSICAL-ECONOMICS-V1.json"}
props["classical_economic_contract_sha256"]={"type":"string","const":"06688b5c493c08d701a236fedcfb549e27489ec7596715c73535b8d04fe7a512"}
names=["classical_economic_contract_path","classical_economic_contract_sha256"]
s["allOf"].append({"if":{"properties":{"benchmark":{"const":"paired_view_mutable_memory_v6"}},"required":["benchmark"]},"then":{"properties":{"research_program_protocol":{"required":names}}},"else":{"properties":{"research_program_protocol":{"not":{"anyOf":[{"required":[n]} for n in names]}}}}})
p.write_text(json.dumps(s,ensure_ascii=False)+"\n",encoding="utf-8",newline="\n")
p=b/"tests/test_pvm01_transport_compression.py";raw=p.read_text();needle='    validate_document("experiment_plan", plan, ROOT)\n';assert raw.count(needle)==1
addition='''    from jsonschema.exceptions import ValidationError
    broken = json.loads(json.dumps(plan))
    broken["research_program_protocol"].pop("classical_economic_contract_sha256")
    with pytest.raises(ValidationError, match="classical_economic_contract_sha256"):
        validate_document("experiment_plan", broken, ROOT)
    old = json.loads((ROOT / "research/plans/EXP-20261004-0008.json").read_text())
    validate_document("experiment_plan", old, ROOT)
    old["research_program_protocol"]["classical_economic_contract_path"] = "research/plans/PVM01-TRANSPORT-CLASSICAL-ECONOMICS-V1.json"
    with pytest.raises(ValidationError, match="research_program_protocol"):
        validate_document("experiment_plan", old, ROOT)
'''
raw=raw.replace(needle,needle+addition);p.write_text(raw,encoding="utf-8",newline="\n")
p=b/"config/baseline_semantics.json";raw=p.read_text();before=json.loads(raw);after=json.loads(raw);digest=sha256_file(b/"tests/test_pvm01_transport_compression.py")
for name,record in after["baselines"].items():
 if name.startswith("pvm01_tc_"):
  for test in record["conformance_tests"]:
   if test["path"]=="tests/test_pvm01_transport_compression.py":test["sha256"]=digest
 else:assert record==before["baselines"][name]
oldhash=before["baselines"]["pvm01_tc_transport_pca_s0"]["conformance_tests"][0]["sha256"];raw=raw.replace(oldhash,digest);assert json.loads(raw)==after;p.write_text(raw,encoding="utf-8",newline="\n")
freeze_manifest(b,overwrite=True);write_preflight_certificate(b)
result=subprocess.run(["uv","run","--no-sync","pytest","-q","tests/test_pvm01_transport_compression.py","tests/test_integrity_and_schemas.py","tests/test_muc03_program.py","--junitxml=research/checks/PVM01-TRANSPORT-schema-conformance-V1.xml"],cwd=b)
raise SystemExit(result.returncode)
