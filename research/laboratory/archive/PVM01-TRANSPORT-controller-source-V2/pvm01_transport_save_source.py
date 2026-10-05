from pathlib import Path
import json,shutil
from nextai_autoresearch.utils import sha256_file,atomic_write_json,utc_now
b=Path.cwd();manifest=json.loads((b/"research/eval_manifest.json").read_text());out=b/"research/laboratory/archive/PVM01-TRANSPORT-full-source-V3";assert not out.exists()
for name,digest in manifest["files"].items():
 assert sha256_file(b/name)==digest,name
 target=out/("root.gitattributes.raw" if name==".gitattributes" else name);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(b/name,target);assert sha256_file(target)==digest
for name in ["research/eval_manifest.json","research/laboratory/preflight_certificate.json"]:
 target=out/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(b/name,target)
helper=b/"research/laboratory/archive/PVM01-TRANSPORT-controller-source-V1";helper.mkdir(parents=True,exist_ok=False)
for p in sorted((b/"research/tmp").glob("pvm01_transport*.py")):
 shutil.copyfile(p,helper/p.name)
atomic_write_json(helper/"raw-source-hashes.json",{"created_at":utc_now(),"files":{p.name:sha256_file(p) for p in sorted(helper.glob("*.py"))},"public_fixtures_not_research_fit":True})
print("Evaluated1250 source files and all maintenance/failed-fixture/controllers preserved as raw bytes")
